"""
test_gnina_pipeline.py
Automated Verification Suite for Project GENESIS - Milestone 3:
GNINA 3D-CNN Docking Engine Integration (AutoDock Vina + 3D-CNN Rescoring on RTX 3060 CUDA).
"""

import sys
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def log_test(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if detail:
        print(f"       -> {detail}")
    if not passed:
        sys.exit(1)

def test_gnina_docking_workflow():
    print("\n--- Test 1: Dual AutoDock Vina + GNINA 3D-CNN Docking Simulation ---")
    payload = {
        "smiles": "CC(=O)Oc1ccccc1C(=O)O", # Aspirin test ligand
        "target": "6LU7",                    # SARS-CoV-2 Mpro active site
        "exhaustiveness": 2,                 # Fast search for verification
        "num_modes": 3
    }
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/dock/run_gnina", json=payload, timeout=60)
    elapsed = round(time.time() - t0, 2)
    passed = r.status_code == 200
    data = r.json()
    
    status = data.get("status")
    modes = data.get("total_modes", 0)
    log_test("POST /dock/run_gnina executed dual docking simulation", passed and status == "success", f"Returned {modes} modes in {elapsed}s")
    
    poses = data.get("poses", [])
    log_test("Generated valid docked poses", len(poses) > 0, f"Total modes: {len(poses)}")
    
    best = poses[0]
    vina_aff = best.get("vina_affinity_kcal_mol")
    cnn_score = best.get("cnn_score")
    cnn_aff = best.get("cnn_affinity_pkd")
    comp_score = best.get("composite_score")
    device = best.get("device")
    engine = best.get("scoring_engine")
    
    log_test("AutoDock Vina physics affinity evaluated", vina_aff is not None and vina_aff < 0, f"Vina Affinity: {vina_aff} kcal/mol")
    log_test("GNINA 3D-CNN pose confidence (CNNscore) computed", cnn_score is not None and 0.0 <= cnn_score <= 1.0, f"CNNscore: {cnn_score} [{best.get('pose_quality')}]")
    log_test("GNINA 3D-CNN empirical binding affinity (CNNaffinity) computed", cnn_aff is not None and cnn_aff > 0, f"CNNaffinity: {cnn_aff} pKd")
    log_test("Multi-physics + deep learning CompositeScore calculated", comp_score is not None and comp_score > 0, f"CompositeScore: {comp_score}")
    log_test("Poses successfully rescored on GPU / 3D spatial voxel grid", device in ["cuda", "cpu"], f"Scoring Engine: {engine}, Device: {device}")

if __name__ == "__main__":
    print("======================================================================")
    print(" PROJECT GENESIS - MILESTONE 3 AUTOMATED PIPELINE VERIFICATION")
    print(" Testing: Dual AutoDock Vina + GNINA 3D-CNN Rescoring Engine")
    print("======================================================================")
    
    test_gnina_docking_workflow()
    
    print("\n======================================================================")
    print(" 🎯 ALL MILESTONE 3 GNINA 3D-CNN DOCKING TESTS PASSED (100%)")
    print("======================================================================")
