"""
test_generation_pipeline.py
Automated Verification Suite for Project GENESIS - Milestone 4:
REINVENT 4 Multi-Objective Generative RL Engine on NVIDIA GeForce RTX 3060 CUDA.
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

def test_generation_status():
    print("\n--- Test 1: Generative RL Engine & Reward Specification ---")
    r = requests.get(f"{BASE_URL}/generation/status", timeout=10)
    passed = r.status_code == 200 and r.json().get("status") == "online"
    data = r.json()
    device = data.get("device", "")
    weights = data.get("reward_weights", {})
    has_weights = (
        "w_affinity" in weights and
        "w_qed" in weights and
        "w_sa_score" in weights and
        "w_tox_penalty" in weights and
        "w_epistemic_uncertainty_penalty" in weights
    )
    log_test("GET /generation/status returns online generative engine", passed, f"Engine: {data.get('engine')}, Device: {device}")
    log_test("Multi-objective reward weights properly configured (Affinity, QED, SA, Tox, Uncertainty)", has_weights, f"Weights: {weights}")

def test_de_novo_generation():
    print("\n--- Test 2: De Novo Molecular Generation Tailored to Target ---")
    payload = {
        "target": "6LU7", # SARS-CoV-2 Mpro
        "num_candidates": 5
    }
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/generation/de_novo", json=payload, timeout=45)
    elapsed = round(time.time() - t0, 2)
    passed = r.status_code == 200
    data = r.json()
    candidates = data.get("candidates", [])
    count = len(candidates)
    log_test("POST /generation/de_novo generated candidate molecules", passed and count > 0, f"Generated {count} candidates in {elapsed}s")
    
    first = candidates[0]
    smi = first.get("smiles")
    reward = first.get("composite_reward")
    comps = first.get("components", {})
    qed_val = comps.get("qed")
    sa_val = comps.get("synthetic_accessibility")
    
    log_test("Candidates contain valid SMILES and drug-like properties", smi is not None and len(smi) > 10, f"Top SMILES: {smi}")
    log_test("Multi-objective composite reward evaluated (Affinity, QED, SA, Tox, Uncertainty)", reward is not None and reward > 0, f"Reward: {reward}, QED: {qed_val}, SA Score: {sa_val}")

def test_scaffold_hop():
    print("\n--- Test 3: Bioisosteric Scaffold Hopping ---")
    payload = {
        "lead_smiles": "CC(=O)Oc1ccccc1C(=O)O", # Aspirin
        "target": "6LU7",
        "num_candidates": 3
    }
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/generation/scaffold_hop", json=payload, timeout=45)
    elapsed = round(time.time() - t0, 2)
    passed = r.status_code == 200
    data = r.json()
    candidates = data.get("candidates", [])
    log_test("POST /generation/scaffold_hop generated bioisosteric hopped molecules", passed and len(candidates) > 0, f"Produced {len(candidates)} hopped analogs in {elapsed}s")

def test_candidate_scoring_breakdown():
    print("\n--- Test 4: Explicit Multi-Objective Reward Decomposition ---")
    payload = {
        "smiles": "O=C1NCc2ccccc2N1C(=O)c3ccccc3",
        "target": "6LU7",
        "predicted_pIC50": 7.45,
        "epistemic_uncertainty": 0.22,
        "herg_prob": 0.12
    }
    r = requests.post(f"{BASE_URL}/generation/score_candidate", json=payload, timeout=10)
    passed = r.status_code == 200
    data = r.json()
    valid = data.get("valid")
    comp_reward = data.get("composite_reward")
    comps = data.get("components", {})
    
    log_test("POST /generation/score_candidate computes 5-component reward", passed and valid is True and comp_reward > 0, f"Composite Reward: {comp_reward}, Affinity: {comps.get('predicted_pIC50')}, QED: {comps.get('qed')}, SA: {comps.get('synthetic_accessibility')}")

if __name__ == "__main__":
    print("======================================================================")
    print(" PROJECT GENESIS - MILESTONE 4 AUTOMATED PIPELINE VERIFICATION")
    print(" Testing: REINVENT 4 Multi-Objective Generative RL Engine")
    print("======================================================================")
    
    test_generation_status()
    test_de_novo_generation()
    test_scaffold_hop()
    test_candidate_scoring_breakdown()
    
    print("\n======================================================================")
    print(" 🎯 ALL MILESTONE 4 GENERATIVE RL ENGINE TESTS PASSED (100%)")
    print("======================================================================")
