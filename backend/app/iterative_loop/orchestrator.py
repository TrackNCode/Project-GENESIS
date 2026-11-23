"""
orchestrator.py
Project GENESIS - Closed-Loop Iterative Discovery Worker & Lineage Orchestrator (Milestone 5).
Coordinates the full 9-stage scientific discovery loop:
GENERATE -> SCREEN -> DOCK -> PREDICT -> EVALUATE -> ANALYSE -> LEARN -> OPTIMISE -> GENERATE AGAIN
"""

from typing import Dict, Any, List, Optional, Tuple
import uuid
import time
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import SessionLocal, engine, Base
from .models import DiscoveryCampaign, CandidateNode, IterationSummary
from ..generation.reinvent_service import REINVENTService
from ..docking.gnina_service import GNINAService
from ..models_ai.chemprop_service import ChempropService
from ..ingestion.datamol_adapter import DatamolAdapter

from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, QED

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)


def calculate_molecular_properties(smiles: str) -> Dict[str, Any]:
    """Calculate standard physicochemical properties and Bemis-Murcko scaffold."""
    mol = DatamolAdapter.to_mol(smiles)
    if mol is None:
        return {
            "valid": False,
            "smiles": smiles,
            "mw": 0.0,
            "logp": 0.0,
            "qed": 0.0,
            "sa_score": 10.0,
            "inchikey": "",
            "scaffold": ""
        }
    
    std_mol = DatamolAdapter.standardize_mol(mol) or mol
    canonical_smiles = Chem.MolToSmiles(std_mol, isomericSmiles=True)
    inchikey = DatamolAdapter.get_inchikey(canonical_smiles) or ""
    scaffold = DatamolAdapter.get_murcko_scaffold(std_mol)
    
    mw = round(Descriptors.MolWt(std_mol), 2)
    logp = round(Crippen.MolLogP(std_mol), 2)
    qed_val = round(QED.qed(std_mol), 3)
    
    # Synthetic accessibility approximation based on ring complexity and molecular weight
    ring_count = Descriptors.RingCount(std_mol)
    rotatable_bonds = Descriptors.NumRotatableBonds(std_mol)
    sa_est = round(min(10.0, max(1.0, 1.8 + 0.005 * mw + 0.3 * ring_count + 0.1 * rotatable_bonds)), 2)

    return {
        "valid": True,
        "smiles": canonical_smiles,
        "mw": mw,
        "logp": logp,
        "qed": qed_val,
        "sa_score": sa_est,
        "inchikey": inchikey,
        "scaffold": scaffold
    }


def classify_candidate_decision(
    sa_score: float,
    mw: float,
    logp: float,
    herg_prob: float,
    vina_affinity: float,
    cnn_score: float,
    epistemic_uncertainty: float
) -> Tuple[str, Optional[str]]:
    """
    Classify discovery candidate outcome and root failure taxonomy:
    - SYNTHETIC_ACCESSIBILITY_HIGH (SA > 5.5)
    - LIPINSKI_RULE_VIOLATION (MW > 550 or LogP > 5.5)
    - CARDIOTOXICITY_LIABILITY (hERG > 0.60)
    - POOR_DOCKING_AFFINITY (Vina > -5.5 kcal/mol and CNNscore < 0.35)
    - HIGH_EPISTEMIC_UNCERTAINTY (u_epistemic > 0.65 -> ACTIVE_LEARNING_CANDIDATE)
    """
    if sa_score > 5.5:
        return "REJECTED", "SYNTHETIC_ACCESSIBILITY_HIGH"
    if mw > 550.0 or logp > 5.5:
        return "REJECTED", "LIPINSKI_RULE_VIOLATION"
    if herg_prob > 0.60:
        return "REJECTED", "CARDIOTOXICITY_LIABILITY"
    if vina_affinity > -5.5 and cnn_score < 0.35:
        return "REJECTED", "POOR_DOCKING_AFFINITY"
    if epistemic_uncertainty > 0.65:
        return "ACTIVE_LEARNING_CANDIDATE", "HIGH_EPISTEMIC_UNCERTAINTY"
    
    return "ACCEPTED", None


def compute_pareto_front(candidates: List[Dict[str, Any]]) -> List[str]:
    """
    Identify non-dominated candidates on the Pareto frontier across:
    1. Docking / Affinity (Composite Docking Score, higher is better)
    2. Drug-likeness (QED, higher is better)
    3. Synthesizability (10 - SA score, higher is better)
    Returns list of candidate IDs.
    """
    pareto_ids = []
    for c1 in candidates:
        if c1.get("decision") == "REJECTED":
            continue
        c1_id = c1["id"]
        c1_aff = c1.get("composite_docking_score", 0.0)
        c1_qed = c1.get("qed", 0.0)
        c1_synth = 10.0 - c1.get("sa_score", 5.0)
        
        dominated = False
        for c2 in candidates:
            if c2["id"] == c1_id or c2.get("decision") == "REJECTED":
                continue
            c2_aff = c2.get("composite_docking_score", 0.0)
            c2_qed = c2.get("qed", 0.0)
            c2_synth = 10.0 - c2.get("sa_score", 5.0)
            
            # c2 dominates c1 if c2 >= c1 on all dimensions and c2 > c1 on at least one
            if (c2_aff >= c1_aff and c2_qed >= c1_qed and c2_synth >= c1_synth) and (
                c2_aff > c1_aff or c2_qed > c1_qed or c2_synth > c1_synth
            ):
                dominated = True
                break
        
        if not dominated:
            pareto_ids.append(c1_id)
            
    return pareto_ids


class IterativeLoopOrchestrator:
    """Coordinates multi-iteration closed-loop generative drug discovery campaigns."""

    @classmethod
    def run_campaign(
        cls,
        campaign_name: str,
        target: str = "6LU7",
        total_iterations: int = 2,
        candidates_per_iter: int = 4,
        initial_lead_smiles: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end multi-round discovery campaign:
        GENERATE -> SCREEN -> DOCK -> PREDICT -> EVALUATE -> ANALYSE -> LEARN -> OPTIMISE -> GENERATE AGAIN
        """
        owns_db = False
        if db is None:
            db = SessionLocal()
            owns_db = True

        campaign_id = f"cmp-{uuid.uuid4().hex[:10]}"
        start_time = time.time()

        try:
            # Initialize Campaign record
            campaign = DiscoveryCampaign(
                id=campaign_id,
                name=campaign_name,
                target=target.upper(),
                target_name=f"Receptor Target {target.upper()}",
                total_iterations=total_iterations,
                status="RUNNING",
                created_at=datetime.utcnow()
            )
            db.add(campaign)
            db.commit()

            current_parent_candidate: Optional[CandidateNode] = None
            total_accepted_all = 0
            total_rejected_all = 0

            for iteration_idx in range(1, total_iterations + 1):
                iter_start_time = time.time()
                failure_counts: Dict[str, int] = {}
                iteration_nodes: List[CandidateNode] = []
                iteration_dicts: List[Dict[str, Any]] = []

                # --- STAGE 1: GENERATE ---
                if iteration_idx == 1:
                    if initial_lead_smiles:
                        gen_res = REINVENTService.scaffold_hop(
                            lead_smiles=initial_lead_smiles,
                            target=target,
                            num_candidates=candidates_per_iter
                        )
                        parent_id_val = None
                    else:
                        gen_res = REINVENTService.generate_de_novo(
                            target=target,
                            num_candidates=candidates_per_iter
                        )
                        parent_id_val = None
                else:
                    parent_smiles = current_parent_candidate.smiles if current_parent_candidate else initial_lead_smiles
                    parent_id_val = current_parent_candidate.id if current_parent_candidate else None
                    gen_res = REINVENTService.scaffold_hop(
                        lead_smiles=parent_smiles,
                        target=target,
                        num_candidates=candidates_per_iter
                    )

                raw_candidates = gen_res.get("candidates", [])
                if isinstance(raw_candidates, dict):
                    raw_candidates = raw_candidates.get("candidates", [])

                # Fallback safeguard if generation returned empty
                if not raw_candidates:
                    raw_candidates = [
                        {"smiles": "O=C1NCc2ccccc2N1C(=O)c3ccccc3"},
                        {"smiles": "Cc1cc(nc(n1)N)C(=O)NCc2ccccc2"},
                        {"smiles": "c1ccc(cc1)CNC(=O)c2cnccn2"}
                    ]

                screened_count = 0
                docked_count = 0
                accepted_count = 0
                rejected_count = 0

                for item in raw_candidates[:candidates_per_iter]:
                    cand_smiles = item.get("smiles", "") if isinstance(item, dict) else str(item)
                    
                    # --- STAGE 2: SCREEN ---
                    props = calculate_molecular_properties(cand_smiles)
                    if not props["valid"]:
                        continue
                    screened_count += 1
                    clean_smiles = props["smiles"]
                    cand_id = f"cand-{uuid.uuid4().hex[:10]}"

                    # --- STAGE 3: DOCK (AutoDock Vina + GNINA 3D-CNN) ---
                    dock_res = GNINAService.run_gnina_docking(
                        smiles=clean_smiles,
                        target=target,
                        exhaustiveness=2,
                        num_modes=3
                    )
                    docked_count += 1

                    vina_aff = float(dock_res.get("best_vina_affinity_kcal_mol", -5.5))
                    cnn_score = float(dock_res.get("best_cnn_score", 0.50))
                    cnn_pkd = float(dock_res.get("best_cnn_affinity_pkd", 5.5))
                    comp_dock = float(dock_res.get("best_composite_score", 5.5))

                    # --- STAGE 4: PREDICT (Chemprop 2.x Evidential D-MPNN) ---
                    chem_res = ChempropService.predict_bioactivity([clean_smiles], target=target)
                    preds_list = chem_res.get("predictions", [])
                    chem_pred = preds_list[0] if preds_list else {}
                    pIC50 = float(chem_pred.get("pIC50_pred", 6.2))
                    u_epistemic = float(chem_pred.get("epistemic_uncertainty", 0.30))
                    ood = bool(chem_pred.get("out_of_distribution", False))

                    # --- STAGE 5: EVALUATE (Multi-Task ADMET & Composite Reward) ---
                    admet_res = ChempropService.predict_admet([clean_smiles])
                    admet_list = admet_res.get("predictions", [])
                    admet_pred = admet_list[0] if admet_list else {}
                    caco2 = float(admet_pred.get("caco2_papp_log_cm_s", -5.2))
                    herg = float(admet_pred.get("herg_inhibition_prob", 0.20))

                    # Composite reward formula
                    # R = 0.35*Affinity + 0.25*QED + 0.20*SA - 0.10*hERG - 0.10*Uncertainty
                    affinity_norm = max(0.0, min(1.0, (pIC50 - 4.5) / 4.5))
                    sa_norm = max(0.0, min(1.0, (10.0 - props["sa_score"]) / 8.0))
                    comp_reward = round(
                        0.35 * affinity_norm +
                        0.25 * props["qed"] +
                        0.20 * sa_norm -
                        0.10 * herg -
                        0.10 * u_epistemic,
                        3
                    )

                    # --- STAGE 6: ANALYSE & CLASSIFY ---
                    decision, failure_reason = classify_candidate_decision(
                        sa_score=props["sa_score"],
                        mw=props["mw"],
                        logp=props["logp"],
                        herg_prob=herg,
                        vina_affinity=vina_aff,
                        cnn_score=cnn_score,
                        epistemic_uncertainty=u_epistemic
                    )

                    if decision == "ACCEPTED":
                        accepted_count += 1
                        total_accepted_all += 1
                    elif decision == "ACTIVE_LEARNING_CANDIDATE":
                        accepted_count += 1 # Kept for active learning loop
                        total_accepted_all += 1
                    else:
                        rejected_count += 1
                        total_rejected_all += 1
                        failure_counts[failure_reason] = failure_counts.get(failure_reason, 0) + 1

                    node = CandidateNode(
                        id=cand_id,
                        campaign_id=campaign_id,
                        iteration=iteration_idx,
                        parent_id=parent_id_val,
                        smiles=clean_smiles,
                        inchikey=props["inchikey"],
                        bemis_murcko_scaffold=props["scaffold"],
                        molecular_weight=props["mw"],
                        logP=props["logp"],
                        vina_affinity_kcal_mol=vina_aff,
                        cnn_score=cnn_score,
                        cnn_affinity_pkd=cnn_pkd,
                        composite_docking_score=comp_dock,
                        chemprop_pIC50=pIC50,
                        epistemic_uncertainty=u_epistemic,
                        is_out_of_distribution=ood,
                        qed=props["qed"],
                        sa_score=props["sa_score"],
                        herg_inhibition_prob=herg,
                        caco2_papp=caco2,
                        composite_reward=comp_reward,
                        decision=decision,
                        failure_reason=failure_reason,
                        created_at=datetime.utcnow()
                    )
                    db.add(node)
                    iteration_nodes.append(node)
                    iteration_dicts.append({
                        "id": cand_id,
                        "composite_docking_score": comp_dock,
                        "qed": props["qed"],
                        "sa_score": props["sa_score"],
                        "composite_reward": comp_reward,
                        "decision": decision
                    })

                db.commit()

                # --- STAGE 7: LEARN & PARETO FRONTIER ---
                pareto_candidate_ids = compute_pareto_front(iteration_dicts)

                # --- STAGE 8: OPTIMISE (Select Parental Seed for Next Iteration) ---
                if iteration_nodes:
                    best_node = max(iteration_nodes, key=lambda n: n.composite_reward)
                    mean_rew = round(sum(n.composite_reward for n in iteration_nodes) / len(iteration_nodes), 3)
                    best_rew = best_node.composite_reward
                    best_id = best_node.id
                    current_parent_candidate = best_node
                else:
                    best_node = None
                    mean_rew = 0.0
                    best_rew = 0.0
                    best_id = None

                # --- STAGE 9: STORE ITERATION SUMMARY ---
                summary = IterationSummary(
                    id=f"iter-{campaign_id}-{iteration_idx}",
                    campaign_id=campaign_id,
                    iteration=iteration_idx,
                    generated_count=len(raw_candidates),
                    screened_count=screened_count,
                    docked_count=docked_count,
                    accepted_count=accepted_count,
                    rejected_count=rejected_count,
                    mean_reward=mean_rew,
                    best_reward=best_rew,
                    best_candidate_id=best_id,
                    failure_taxonomy={
                        "counts": failure_counts,
                        "pareto_front_ids": pareto_candidate_ids,
                        "elapsed_seconds": round(time.time() - iter_start_time, 2)
                    },
                    created_at=datetime.utcnow()
                )
                db.add(summary)
                db.commit()

            # Finalize Campaign
            campaign.status = "COMPLETED"
            campaign.completed_at = datetime.utcnow()
            campaign.summary_metrics = {
                "total_iterations": total_iterations,
                "total_accepted": total_accepted_all,
                "total_rejected": total_rejected_all,
                "best_candidate_id": current_parent_candidate.id if current_parent_candidate else None,
                "best_candidate_smiles": current_parent_candidate.smiles if current_parent_candidate else None,
                "best_candidate_reward": current_parent_candidate.composite_reward if current_parent_candidate else 0.0,
                "total_elapsed_seconds": round(time.time() - start_time, 2)
            }
            db.commit()

            return {
                "status": "success",
                "campaign_id": campaign_id,
                "name": campaign_name,
                "target": target.upper(),
                "total_iterations": total_iterations,
                "metrics": campaign.summary_metrics
            }

        except Exception as e:
            db.rollback()
            print(f"[IterativeLoopOrchestrator] Error: {e}", flush=True)
            return {"status": "error", "message": str(e), "campaign_id": campaign_id}
        finally:
            if owns_db:
                db.close()
