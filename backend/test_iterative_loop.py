"""
test_iterative_loop.py
Milestone 5 Verification Test Suite: Closed-Loop Iterative Discovery Worker & Lineage System.
Validates the full 9-stage scientific discovery loop:
GENERATE -> SCREEN -> DOCK -> PREDICT -> EVALUATE -> ANALYSE -> LEARN -> OPTIMISE -> GENERATE AGAIN
"""

import sys
import os
import time

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.iterative_loop.models import DiscoveryCampaign, CandidateNode, IterationSummary
from app.iterative_loop.orchestrator import (
    IterativeLoopOrchestrator,
    calculate_molecular_properties,
    classify_candidate_decision,
    compute_pareto_front
)


def run_tests():
    print("=" * 70)
    print("PROJECT GENESIS - MILESTONE 5 VERIFICATION SUITE")
    print("Closed-Loop Iterative Discovery Worker & Lineage System")
    print("=" * 70)
    
    passed = 0
    total = 5
    
    # ----------------------------------------------------
    # TEST 1: Molecular Property & Bemis-Murcko Calculation
    # ----------------------------------------------------
    print("\n[TEST 1/5] Testing Molecular Properties & Bemis-Murcko Scaffolding...")
    test_smiles = "Cc1cc(nc(n1)N)C(=O)NCc2ccccc2"
    props = calculate_molecular_properties(test_smiles)
    
    assert props["valid"] is True, "Failed: Molecule marked invalid"
    assert props["mw"] > 100.0, f"Failed: Invalid MW {props['mw']}"
    assert 0.0 < props["qed"] <= 1.0, f"Failed: Invalid QED {props['qed']}"
    assert 1.0 <= props["sa_score"] <= 10.0, f"Failed: Invalid SA score {props['sa_score']}"
    assert len(props["inchikey"]) == 27, f"Failed: Invalid InChIKey {props['inchikey']}"
    assert len(props["scaffold"]) > 0, "Failed: Empty Bemis-Murcko scaffold"
    print(f"  [OK] Validated {test_smiles}")
    print(f"       MW={props['mw']}, LogP={props['logp']}, QED={props['qed']}, SA={props['sa_score']}")
    print(f"       InChIKey={props['inchikey']}")
    print(f"       Bemis-Murcko Scaffold={props['scaffold']}")
    passed += 1

    # ----------------------------------------------------
    # TEST 2: Failure Taxonomy & Active Learning Rules
    # ----------------------------------------------------
    print("\n[TEST 2/5] Testing Failure Classification Taxonomy & Active Learning Criteria...")
    # Case A: High SA
    d_sa, r_sa = classify_candidate_decision(sa_score=6.2, mw=350, logp=2.5, herg_prob=0.1, vina_affinity=-7.5, cnn_score=0.8, epistemic_uncertainty=0.2)
    assert d_sa == "REJECTED" and r_sa == "SYNTHETIC_ACCESSIBILITY_HIGH", f"Failed Case A: {d_sa}, {r_sa}"
    
    # Case B: Lipinski MW
    d_mw, r_mw = classify_candidate_decision(sa_score=3.0, mw=620, logp=2.5, herg_prob=0.1, vina_affinity=-7.5, cnn_score=0.8, epistemic_uncertainty=0.2)
    assert d_mw == "REJECTED" and r_mw == "LIPINSKI_RULE_VIOLATION", f"Failed Case B: {d_mw}, {r_mw}"
    
    # Case C: hERG Cardiotoxicity
    d_tox, r_tox = classify_candidate_decision(sa_score=3.0, mw=350, logp=2.5, herg_prob=0.85, vina_affinity=-7.5, cnn_score=0.8, epistemic_uncertainty=0.2)
    assert d_tox == "REJECTED" and r_tox == "CARDIOTOXICITY_LIABILITY", f"Failed Case C: {d_tox}, {r_tox}"
    
    # Case D: Poor Docking
    d_dock, r_dock = classify_candidate_decision(sa_score=3.0, mw=350, logp=2.5, herg_prob=0.1, vina_affinity=-4.0, cnn_score=0.20, epistemic_uncertainty=0.2)
    assert d_dock == "REJECTED" and r_dock == "POOR_DOCKING_AFFINITY", f"Failed Case D: {d_dock}, {r_dock}"
    
    # Case E: High Epistemic Uncertainty (Active Learning Flag)
    d_al, r_al = classify_candidate_decision(sa_score=3.0, mw=350, logp=2.5, herg_prob=0.1, vina_affinity=-7.5, cnn_score=0.8, epistemic_uncertainty=0.78)
    assert d_al == "ACTIVE_LEARNING_CANDIDATE" and r_al == "HIGH_EPISTEMIC_UNCERTAINTY", f"Failed Case E: {d_al}, {r_al}"
    
    # Case F: Accepted Drug Candidate
    d_ok, r_ok = classify_candidate_decision(sa_score=2.8, mw=380, logp=2.8, herg_prob=0.15, vina_affinity=-8.2, cnn_score=0.85, epistemic_uncertainty=0.25)
    assert d_ok == "ACCEPTED" and r_ok is None, f"Failed Case F: {d_ok}, {r_ok}"
    print("  [OK] Successfully validated all 6 failure taxonomy & active learning branches.")
    passed += 1

    # ----------------------------------------------------
    # TEST 3: Multi-Objective Pareto Frontier Extraction
    # ----------------------------------------------------
    print("\n[TEST 3/5] Testing Multi-Objective Pareto Front Computation...")
    candidates = [
        {"id": "cand-1", "composite_docking_score": 8.5, "qed": 0.85, "sa_score": 2.5, "decision": "ACCEPTED"}, # Dominant
        {"id": "cand-2", "composite_docking_score": 6.0, "qed": 0.60, "sa_score": 4.5, "decision": "ACCEPTED"}, # Dominated by cand-1
        {"id": "cand-3", "composite_docking_score": 9.0, "qed": 0.50, "sa_score": 2.2, "decision": "ACCEPTED"}, # Non-dominated (higher affinity)
        {"id": "cand-4", "composite_docking_score": 9.5, "qed": 0.90, "sa_score": 6.5, "decision": "REJECTED"}, # High SA rejected
    ]
    pareto_ids = compute_pareto_front(candidates)
    assert "cand-1" in pareto_ids, "Failed: cand-1 must be on Pareto frontier"
    assert "cand-3" in pareto_ids, "Failed: cand-3 must be on Pareto frontier"
    assert "cand-2" not in pareto_ids, "Failed: cand-2 is dominated and should not be on frontier"
    assert "cand-4" not in pareto_ids, "Failed: cand-4 was rejected and should not be on frontier"
    print(f"  [OK] Pareto Frontier correctly isolated non-dominated candidates: {pareto_ids}")
    passed += 1

    # ----------------------------------------------------
    # TEST 4: Live 2-Iteration Closed-Loop Campaign Execution
    # ----------------------------------------------------
    print("\n[TEST 4/5] Executing Live 2-Iteration Closed-Loop Discovery Campaign (Target: SARS-CoV-2 Mpro 6LU7)...")
    db = SessionLocal()
    start_t = time.time()
    try:
        campaign_res = IterativeLoopOrchestrator.run_campaign(
            campaign_name="Mpro Milestone 5 Verification Campaign",
            target="6LU7",
            total_iterations=2,
            candidates_per_iter=2,
            initial_lead_smiles="Cc1cc(nc(n1)N)C(=O)NCc2ccccc2",
            db=db
        )
        assert campaign_res["status"] == "success", f"Campaign failed: {campaign_res}"
        campaign_id = campaign_res["campaign_id"]
        
        # Verify Iteration summaries in DB
        summaries = db.query(IterationSummary).filter(IterationSummary.campaign_id == campaign_id).order_by(IterationSummary.iteration.asc()).all()
        assert len(summaries) == 2, f"Expected 2 iteration summaries, got {len(summaries)}"
        
        # Verify Candidate lineage
        all_cands = db.query(CandidateNode).filter(CandidateNode.campaign_id == campaign_id).all()
        assert len(all_cands) >= 4, f"Expected >= 4 candidates generated, got {len(all_cands)}"
        
        iter2_cands = [c for c in all_cands if c.iteration == 2]
        assert len(iter2_cands) > 0, "No candidates found for iteration 2"
        # Verify that iteration 2 candidates have parent_id linked to an iteration 1 candidate
        iter1_ids = {c.id for c in all_cands if c.iteration == 1}
        has_parent_link = any(c.parent_id in iter1_ids for c in iter2_cands)
        assert has_parent_link, "Failed: Iteration 2 candidates do not contain parent_id from iteration 1"

        print(f"  [OK] Campaign completed successfully in {round(time.time() - start_t, 2)}s!")
        print(f"       Campaign ID: {campaign_id}")
        print(f"       Total Candidates: {len(all_cands)} across 2 iterations")
        print(f"       Iteration 1 Mean Reward: {summaries[0].mean_reward}, Best: {summaries[0].best_reward}")
        print(f"       Iteration 2 Mean Reward: {summaries[1].mean_reward}, Best: {summaries[1].best_reward}")
        print(f"       Parent-Child Lineage Verified: {len(iter2_cands)} children derived from Iteration 1 parents")
        passed += 1

    finally:
        db.close()

    # ----------------------------------------------------
    # TEST 5: Lineage DAG & Failure Taxonomy Inspection
    # ----------------------------------------------------
    print("\n[TEST 5/5] Testing Lineage DAG Structure & System Failure Taxonomy...")
    db = SessionLocal()
    try:
        from app.routers.iterative_loop import get_campaign_lineage, get_failure_taxonomy
        lineage_data = get_campaign_lineage(campaign_id, db=db)
        assert lineage_data["total_nodes"] > 0, "Lineage graph has 0 nodes"
        assert len(lineage_data["edges"]) > 0, "Lineage graph has 0 edges (no evolutionary connections)"
        
        taxonomy_data = get_failure_taxonomy(db=db)
        assert taxonomy_data["totals"]["evaluated_total"] > 0, "No evaluated candidates in taxonomy"
        print(f"  [OK] Lineage Graph Verified: {lineage_data['total_nodes']} nodes, {len(lineage_data['edges'])} edges")
        print(f"  [OK] Failure Taxonomy Verified: {taxonomy_data['totals']}")
        passed += 1
    finally:
        db.close()

    print("\n" + "=" * 70)
    print(f"MILESTONE 5 RESULT: {passed}/{total} TESTS PASSED (100%)")
    print("Closed-Loop Iterative Discovery Worker & Lineage System Fully Verified!")
    print("=" * 70)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_tests())
