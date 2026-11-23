"""
Project GENESIS - Phase 6 AI Prediction Models & Lead Optimisation Automated Test Suite
Tests:
  1. Target-Specific QSAR Bioactivity Prediction (SARS-CoV-2 Mpro / Nirmatrelvir)
  2. Kinase QSAR Bioactivity Prediction (Abl Kinase / Imatinib)
  3. Multi-Target Profiling & Selectivity Evaluation
  4. Comprehensive ADME Pharmacokinetics Profiling (HIA, Caco-2, BBB, PPB, Clearance)
  5. Cytochrome P450 Metabolism Matrix (5 Isoforms)
  6. Predictive Toxicity & Cardiac Safety Profiling (hERG, Ames, DILI, LD50)
  7. Mutagenic Toxicophore Alert Detection
  8. Bioisosteric Lead Optimization Suggestions (MMP & MPO Desirability)
  9. 360-Degree Comprehensive Lead Profiling Report
  10. Candidate Database Scoring & Automated Qualification
"""

import sys
import requests

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "PASS": "\033[92m",
        "FAIL": "\033[91m",
        "WARN": "\033[93m",
        "RESET": "\033[0m"
    }
    c = colors.get(status, colors["INFO"])
    print(f"{c}[{status}] {msg}{colors['RESET']}")

def test_phase6_suite():
    passed_tests = 0
    total_tests = 10

    print("=" * 75)
    print(" PROJECT GENESIS - PHASE 6: AI PREDICTION MODELS & LEAD OPTIMISATION")
    print("=" * 75)

    # -------------------------------------------------------------
    # Test 1: Target-Specific QSAR Bioactivity (Nirmatrelvir against 6LU7)
    # -------------------------------------------------------------
    print("\n--- Test 1: QSAR Bioactivity (Nirmatrelvir / 6LU7) ---")
    try:
        nirmatrelvir_smiles = "CC1(C2C1C(N(C2)C(=O)C(C(C)(C)C)NC(=O)C(F)(F)F)C(=O)NC(CC3CCNC3=O)C#N)C"
        payload = {"smiles": nirmatrelvir_smiles, "target": "6LU7"}
        r = requests.post(f"{BASE_URL}/ai_models/qsar/predict", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["predicted_pIC50"] >= 7.0, f"Expected potent pIC50 >= 7.0, got {data['predicted_pIC50']}"
        assert data["predicted_IC50_nM"] <= 100.0, f"Expected sub-100 nM IC50, got {data['predicted_IC50_nM']}"
        assert "Potent" in data["activity_class"]
        assert data["applicability_domain"]["in_domain"] is True
        log(f"6LU7 Mpro QSAR: pIC50 = {data['predicted_pIC50']} | IC50 = {data['predicted_IC50_nM']} nM | Class: {data['activity_class']} | AD: In-Domain (Tanimoto = {data['applicability_domain']['max_tanimoto_similarity']})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 1 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 2: Kinase QSAR Bioactivity (Imatinib / 1IEP)
    # -------------------------------------------------------------
    print("\n--- Test 2: Kinase QSAR Bioactivity (Imatinib / 1IEP) ---")
    try:
        imatinib_smiles = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc4nccc(n4)c5cccnc5"
        payload = {"smiles": imatinib_smiles, "target": "1IEP"}
        r = requests.post(f"{BASE_URL}/ai_models/qsar/predict", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["predicted_pIC50"] >= 7.5, f"Expected potent pIC50 >= 7.5, got {data['predicted_pIC50']}"
        log(f"1IEP Abl Kinase QSAR: pIC50 = {data['predicted_pIC50']} | IC50 = {data['predicted_IC50_nM']} nM | Class: {data['activity_class']}", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 2 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 3: Multi-Target Profiling & Selectivity Evaluation
    # -------------------------------------------------------------
    print("\n--- Test 3: Multi-Target Profiling & Selectivity ---")
    try:
        estradiol_smiles = "CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O"
        payload = {"smiles": estradiol_smiles}
        r = requests.post(f"{BASE_URL}/ai_models/qsar/multi_target", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "targets" in data
        assert len(data["targets"]) >= 5
        assert data["primary_target"] == "1ERE", f"Expected primary target 1ERE, got {data['primary_target']}"
        er_pic50 = data["targets"]["1ERE"]["pIC50"]
        mpro_pic50 = data["targets"]["6LU7"]["pIC50"]
        assert er_pic50 > mpro_pic50, f"Expected selective binding to 1ERE ({er_pic50}) over 6LU7 ({mpro_pic50})"
        log(f"Selectivity Confirmed: Primary Target = 1ERE (pIC50 {er_pic50}) vs 6LU7 (pIC50 {mpro_pic50})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 3 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 4: Comprehensive ADME Pharmacokinetics
    # -------------------------------------------------------------
    print("\n--- Test 4: Comprehensive ADME Pharmacokinetics ---")
    try:
        cipro_smiles = "O=C(O)c1cn(C2CC2)c3cc(N4CCNCC4)c(F)cc3c1=O"
        payload = {"smiles": cipro_smiles}
        r = requests.post(f"{BASE_URL}/ai_models/adme/profile", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "absorption" in data and "distribution" in data and "metabolism" in data and "excretion" in data
        assert data["absorption"]["hia_percentage"] > 60.0
        assert data["distribution"]["bbb_penetrant"] is False  # Ciprofloxacin is BBB non-penetrant
        assert data["adme_score"] >= 60.0
        log(f"ADME Profile: Score = {data['adme_score']}/100 | HIA = {data['absorption']['hia_percentage']}% | Caco-2 = {data['absorption']['caco2_permeability_10e6_cm_s']} × 10^-6 cm/s | BBB: {data['distribution']['bbb_class']}", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 4 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 5: CYP450 Metabolism Matrix (5 Isoforms)
    # -------------------------------------------------------------
    print("\n--- Test 5: CYP450 Metabolism Matrix ---")
    try:
        payload = {"smiles": "Cc1nc(sc1)NC(=O)C2=C(O)c3ccccc3S(=O)(=O)N2C"}  # Meloxicam
        r = requests.post(f"{BASE_URL}/ai_models/adme/profile", json=payload, timeout=10)
        assert r.status_code == 200
        matrix = r.json()["metabolism"]["cyp_matrix"]
        assert all(iso in matrix for iso in ["CYP1A2", "CYP2C9", "CYP2C19", "CYP2D6", "CYP3A4"])
        log(f"CYP Matrix Verified: 5 Isoforms successfully modeled (CYP2C9 prob = {matrix['CYP2C9']['probability']})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 5 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 6: Toxicity & Cardiac Safety (Aspirin)
    # -------------------------------------------------------------
    print("\n--- Test 6: Toxicity & Cardiac Safety (Aspirin) ---")
    try:
        aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
        payload = {"smiles": aspirin_smiles}
        r = requests.post(f"{BASE_URL}/ai_models/toxicity/profile", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["safety_score"] >= 80.0, f"Expected high safety score, got {data['safety_score']}"
        assert data["cardiac_herg"]["herg_positive_alert"] is False
        assert data["mutagenicity_ames"]["ames_mutagenic"] is False
        assert data["acute_oral_toxicity"]["estimated_ld50_mg_kg"] > 500.0
        log(f"Aspirin Safety: Score = {data['safety_score']}/100 | hERG = Cardiosafe (p={data['cardiac_herg']['herg_inhibition_probability']}) | Ames = Non-Mutagenic | LD50 = {data['acute_oral_toxicity']['estimated_ld50_mg_kg']} mg/kg", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 6 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 7: Mutagenic Toxicophore Alert Detection
    # -------------------------------------------------------------
    print("\n--- Test 7: Toxicophore Alert Detection (4-Nitroaniline) ---")
    try:
        nitroaniline_smiles = "Nc1ccc(N(=O)=O)cc1"
        payload = {"smiles": nitroaniline_smiles}
        r = requests.post(f"{BASE_URL}/ai_models/toxicity/profile", json=payload, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["mutagenicity_ames"]["ames_mutagenic"] is True
        assert len(data["structural_toxicophores"]["alerts"]) >= 1
        log(f"Toxicophore Alert Detected: {data['structural_toxicophores']['alerts']} (Ames Mutagenic = {data['mutagenicity_ames']['ames_mutagenic']})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 7 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 8: Bioisosteric Lead Optimization Suggestions
    # -------------------------------------------------------------
    print("\n--- Test 8: Bioisosteric Lead Optimization Suggestions ---")
    try:
        ibuprofen_smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
        payload = {"smiles": ibuprofen_smiles, "target": "6LU7", "max_suggestions": 4}
        r = requests.post(f"{BASE_URL}/ai_models/lead_opt/suggest", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["total_suggestions"] >= 1, "Expected at least 1 bioisosteric suggestion"
        top_sug = data["suggestions"][0]
        assert "analog_smiles" in top_sug
        assert "delta_pIC50" in top_sug
        assert "mpo_score" in top_sug
        log(f"Bioisostere Engine: Generated {data['total_suggestions']} analogs | Top: {top_sug['rule_name']} (MPO = {top_sug['mpo_score']})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 8 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 9: 360-Degree Comprehensive Lead Profiling Report
    # -------------------------------------------------------------
    print("\n--- Test 9: 360-Degree Comprehensive Lead Profiling ---")
    try:
        payload = {"smiles": "Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1", "target": "1CX2"}  # Celecoxib
        r = requests.post(f"{BASE_URL}/ai_models/lead_opt/comprehensive_lead_profile", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "qsar" in data and "adme" in data and "toxicity" in data and "mpo_desirability" in data
        assert data["qsar"]["predicted_pIC50"] >= 6.5
        assert data["mpo_desirability"]["mpo_score"] > 0.4
        log(f"Comprehensive 360 Lead Report: Target 1CX2 | pIC50 = {data['qsar']['predicted_pIC50']} | MPO = {data['mpo_desirability']['mpo_score']} ({data['mpo_desirability']['rating']})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 9 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 10: Candidate Database Scoring & Qualification
    # -------------------------------------------------------------
    print("\n--- Test 10: Candidate Database Scoring & Qualification ---")
    try:
        # 1. Create or save candidate into DB
        cand_payload = {
            "project_id": 1,
            "name": "Nirmatrelvir Mpro Lead",
            "smiles": "CC1(C2C1C(N(C2)C(=O)C(C(C)(C)C)NC(=O)C(F)(F)F)C(=O)NC(CC3CCNC3=O)C#N)C",
            "binding_affinity": -8.5,
            "target": "6LU7"
        }
        r_save = requests.post(f"{BASE_URL}/screening/save_candidate", json=cand_payload, timeout=5)
        assert r_save.status_code == 200
        cand_id = r_save.json()["candidate_id"]

        # 2. Trigger evaluate_all
        r_eval = requests.post(f"{BASE_URL}/ai_models/candidates/{cand_id}/evaluate_all?target=6LU7", timeout=10)
        assert r_eval.status_code == 200, f"Expected 200, got {r_eval.status_code}: {r_eval.text}"
        eval_data = r_eval.json()
        assert eval_data["qsar_score"] is not None and eval_data["qsar_score"] >= 7.0
        assert eval_data["adme_score"] is not None
        assert eval_data["toxicity_score"] is not None
        assert eval_data["status"] == "LEAD_QUALIFIED"
        log(f"Candidate #{cand_id} Successfully Evaluated & Qualified: QSAR = {eval_data['qsar_score']} | ADME = {eval_data['adme_score']} | Safety = {eval_data['toxicity_score']} | Status: {eval_data['status']}", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 10 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    print(f" PHASE 6 TEST SUMMARY: {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)")
    print("=" * 75)

    if passed_tests == total_tests:
        print("\n>>> ALL PHASE 6 AI PREDICTION & LEAD OPTIMISATION TESTS PASSED! <<<")
        sys.exit(0)
    else:
        print(f"\n>>> {total_tests - passed_tests} TESTS FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    test_phase6_suite()
