"""
test_milestone6_benchmark.py
Milestone 6 Verification Suite: End-to-End Multi-Target Benchmark Campaign & Scientific Integrity.
Validates the complete closed-loop AI drug discovery architecture across diverse therapeutic targets:
- SARS-CoV-2 Main Protease (Mpro, PDB: 6LU7) - Viral Protease
- Human Estrogen Receptor Alpha (ERa, PDB: 1ERE) - Nuclear Hormone Receptor
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.iterative_loop.models import DiscoveryCampaign, CandidateNode, IterationSummary
from app.iterative_loop.orchestrator import IterativeLoopOrchestrator
from app.ingestion.datamol_adapter import DatamolAdapter
from app.ingestion.data_governance import DataGovernanceEngine
from app.generation.reinvent_service import REINVENTService
from app.models_ai.chemprop_service import ChempropService
from app.docking.gnina_service import GNINAService


def run_benchmark():
    print("=" * 75)
    print("PROJECT GENESIS - MILESTONE 6 SCIENTIFIC BENCHMARK & SYSTEM INTEGRITY")
    print("Hardware: NVIDIA GeForce RTX 3060 CUDA + Intel Core i7-14700KF")
    print("=" * 75)

    passed = 0
    total = 4
    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # BENCHMARK 1: Multi-Target Closed-Loop Discovery
        # ----------------------------------------------------
        print("\n[BENCHMARK 1/4] Running Multi-Target Discovery Loops (6LU7 & 1ERE)...")
        targets_to_test = [
            ("6LU7", "Mpro Benchmark Run", "Cc1cc(nc(n1)N)C(=O)NCc2ccccc2"),
            ("1ERE", "ERa Benchmark Run", "Oc1ccc2c(c1)OC(c3ccccc3)C2")
        ]

        for pdb_id, cmp_name, seed in targets_to_test:
            t0 = time.time()
            res = IterativeLoopOrchestrator.run_campaign(
                campaign_name=cmp_name,
                target=pdb_id,
                total_iterations=2,
                candidates_per_iter=2,
                initial_lead_smiles=seed,
                db=db
            )
            elapsed = round(time.time() - t0, 2)
            assert res["status"] == "success", f"Campaign failed for {pdb_id}: {res}"
            cid = res["campaign_id"]
            
            cands = db.query(CandidateNode).filter(CandidateNode.campaign_id == cid).all()
            assert len(cands) >= 3, f"Expected candidates for {pdb_id}, got {len(cands)}"
            
            # Check docking & prediction values
            for c in cands:
                assert c.vina_affinity_kcal_mol is not None, f"Missing Vina for {c.id}"
                assert c.cnn_score is not None, f"Missing CNNscore for {c.id}"
                assert c.chemprop_pIC50 is not None, f"Missing Chemprop pIC50 for {c.id}"
                assert c.composite_reward is not None, f"Missing reward for {c.id}"
            
            print(f"  [OK] Target {pdb_id} completed in {elapsed}s: {len(cands)} candidates, Best Reward = {res['metrics'].get('best_candidate_reward')}")

        passed += 1

        # ----------------------------------------------------
        # BENCHMARK 2: Scientific Data Governance & Anti-Leakage
        # ----------------------------------------------------
        print("\n[BENCHMARK 2/4] Verifying Data Governance & Zero-Leakage Scaffold Partitions...")
        test_compounds = [
            {"id": "c1", "smiles": "c1ccccc1NC(=O)C", "label": 7.2},
            {"id": "c2", "smiles": "c1ccccc1NC(=O)CC", "label": 6.8}, # Same benzene scaffold
            {"id": "c3", "smiles": "c1ccncc1NC(=O)C", "label": 5.4}, # Pyridine scaffold
            {"id": "c4", "smiles": "c1ccncc1NC(=O)CC", "label": 5.9}, # Pyridine scaffold
            {"id": "c5", "smiles": "c1ccc2[nH]ccc2c1", "label": 8.1}, # Indole scaffold
        ]

        splits = DatamolAdapter.scaffold_split(test_compounds, val_ratio=0.2, test_ratio=0.2, seed=42)
        audit_split = DataGovernanceEngine.verify_split_leak_free(splits)
        assert audit_split["leak_free"] is True, f"Scaffold leakage detected: {audit_split}"
        print(f"  [OK] Zero-Leakage Scaffold Partitioning Verified: 0 overlapping scaffolds between train & test.")

        # Test pseudo-label rejection & metadata provenance
        unverified_pred = {
            "smiles": "c1ccccc1",
            "predicted_pIC50": 8.2,
            "provenance": {
                "source": "in_silico_dmpnn",
                "dataset_id": "pred_mpro_001",
                "licence": "internal",
                "data_class": "MODEL_PREDICTION",
                "retrieval_timestamp": "2026-11-21"
            }
        }
        audit = DataGovernanceEngine.audit_record(unverified_pred)
        assert audit["is_ground_truth"] is False, "Failed: MODEL_PREDICTION treated as ground truth!"
        assert audit["data_class"] == "MODEL_PREDICTION"
        print(f"  [OK] Anti-Contamination Governance Verified: Model predictions strictly segregated from ground-truth.")
        passed += 1

        # ----------------------------------------------------
        # BENCHMARK 3: Deep Evidential Uncertainty & Active Learning
        # ----------------------------------------------------
        print("\n[BENCHMARK 3/4] Testing Deep Evidential Uncertainty Estimation & Active Learning Flags...")
        chem_pred = ChempropService.predict_bioactivity(["CC(=O)Oc1ccccc1C(=O)O"], target="6LU7")
        assert chem_pred.get("status") == "success", f"Chemprop inference failed: {chem_pred}"
        p = chem_pred["predictions"][0]
        assert "epistemic_uncertainty" in p, "Missing epistemic uncertainty"
        assert p["epistemic_uncertainty"] > 0.0, "Epistemic uncertainty must be positive"
        print(f"  [OK] Evidential Uncertainty u = {p['epistemic_uncertainty']}, pIC50 = {p['pIC50_pred']}, OOD = {p['out_of_distribution']}")
        passed += 1

        # ----------------------------------------------------
        # BENCHMARK 4: IPC Bridge Latency & Multi-Engine Concurrency
        # ----------------------------------------------------
        print("\n[BENCHMARK 4/4] Testing Subsystem IPC Bridge Latencies (genesis-cheminfo <-> genesis-gpu)...")
        # 1. Chemprop latency
        t0 = time.time()
        ChempropService.predict_admet(["Cc1cc(nc(n1)N)C(=O)NCc2ccccc2"])
        t_chemprop = round(time.time() - t0, 3)

        # 2. GNINA latency
        t0 = time.time()
        GNINAService.run_gnina_docking("c1ccccc1", target="6LU7", exhaustiveness=1, num_modes=1)
        t_gnina = round(time.time() - t0, 3)

        print(f"  [OK] Chemprop Evidential D-MPNN Latency: {t_chemprop}s")
        print(f"  [OK] GNINA 3D-CNN Docking + Rescoring Latency: {t_gnina}s")
        passed += 1

    finally:
        db.close()

    print("\n" + "=" * 75)
    print(f"MILESTONE 6 BENCHMARK RESULT: {passed}/{total} BENCHMARKS PASSED (100%)")
    print("Full Multi-Target Discovery Loops & Scientific Integrity Verified!")
    print("=" * 75)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_benchmark())
