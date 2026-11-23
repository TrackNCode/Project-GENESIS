"""
Project GENESIS Chemistry API Full Test Suite.
Verifies all chemistry endpoints against live running FastAPI backend.
"""

import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 60)
    print(" PROJECT GENESIS - CHEMISTRY API COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    passed = 0
    total = 0

    def assert_test(name: str, condition: bool, extra: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f" [PASS] {name} {extra}")
        else:
            print(f" [FAIL] {name} {extra}")

    # 1. Health check
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert_test("Backend /health check", r.status_code == 200 and r.json().get("status") == "ok")
    except Exception as e:
        print(f" [FAIL] Backend is not reachable at {BASE_URL}: {e}")
        return 1

    # 2. Presets endpoint
    try:
        r = requests.get(f"{BASE_URL}/chem/presets", timeout=5)
        presets = r.json()
        assert_test("GET /chem/presets", r.status_code == 200 and len(presets) >= 5, f"({len(presets)} presets found)")
    except Exception as e:
        assert_test("GET /chem/presets", False, str(e))

    # 3. Ethanol Molecular Weight
    try:
        r = requests.post(f"{BASE_URL}/chem/weight", json={"smiles": "CCO"}, timeout=5)
        data = r.json()
        weight = data.get("weight", 0.0)
        expected = 46.0419
        diff = abs(weight - expected)
        assert_test("POST /chem/weight (Ethanol CCO)", r.status_code == 200 and diff < 0.01, f"(MW = {weight:.4f} g/mol, diff = {diff:.6f})")
    except Exception as e:
        assert_test("POST /chem/weight (Ethanol CCO)", False, str(e))

    # 4. Ethanol Formula
    try:
        r = requests.post(f"{BASE_URL}/chem/formula", json={"smiles": "CCO"}, timeout=5)
        data = r.json()
        formula = data.get("formula", "")
        assert_test("POST /chem/formula (Ethanol CCO)", r.status_code == 200 and formula == "C2H6O", f"(Formula = '{formula}')")
    except Exception as e:
        assert_test("POST /chem/formula (Ethanol CCO)", False, str(e))

    # 5. Ethanol LogP
    try:
        r = requests.post(f"{BASE_URL}/chem/logp", json={"smiles": "CCO"}, timeout=5)
        data = r.json()
        logp = data.get("logp", 999.0)
        assert_test("POST /chem/logp (Ethanol CCO)", r.status_code == 200 and abs(logp - (-0.0014)) < 0.05, f"(LogP = {logp})")
    except Exception as e:
        assert_test("POST /chem/logp (Ethanol CCO)", False, str(e))

    # 6. Aspirin Properties & Lipinski Profile
    try:
        aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
        r = requests.post(f"{BASE_URL}/chem/properties", json={"smiles": aspirin_smiles}, timeout=5)
        data = r.json()
        mw = data.get("molecular_weight", 0)
        lipinski = data.get("lipinski_pass", False)
        formula = data.get("formula", "")
        condition = (r.status_code == 200 and abs(mw - 180.0423) < 0.05 and lipinski is True and formula == "C9H8O4")
        assert_test("POST /chem/properties (Aspirin)", condition, f"(MW={mw}, Formula={formula}, LipinskiPass={lipinski})")
    except Exception as e:
        assert_test("POST /chem/properties (Aspirin)", False, str(e))

    # 7. 3D Conformer Generation
    try:
        r = requests.post(f"{BASE_URL}/chem/conformer_3d", json={"smiles": "CCO", "optimize": True}, timeout=8)
        data = r.json()
        atoms = data.get("atoms", [])
        energy = data.get("energy_kcal_mol")
        mol_block = data.get("mol_block", "")
        condition = (r.status_code == 200 and len(atoms) == 9 and len(mol_block) > 50)
        assert_test("POST /chem/conformer_3d (Ethanol 3D Embed)", condition, f"({len(atoms)} atoms embedded, Energy = {energy} kcal/mol)")
    except Exception as e:
        assert_test("POST /chem/conformer_3d (Ethanol 3D Embed)", False, str(e))

    # 8. 2D Structure SVG Rendering
    try:
        r = requests.post(f"{BASE_URL}/chem/structure_2d", json={"smiles": "CCO"}, timeout=5)
        is_svg = ("<svg" in r.text and "</svg>" in r.text)
        assert_test("POST /chem/structure_2d (SVG Depiction)", r.status_code == 200 and is_svg, f"(Content-Length = {len(r.text)} bytes)")
    except Exception as e:
        assert_test("POST /chem/structure_2d (SVG Depiction)", False, str(e))

    # 9. Invalid SMILES Validation
    try:
        r = requests.post(f"{BASE_URL}/chem/weight", json={"smiles": "INVALID_NOT_A_SMILES_STRING"}, timeout=5)
        assert_test("POST /chem/weight (Invalid SMILES rejection)", r.status_code == 400, f"(HTTP {r.status_code} properly returned)")
    except Exception as e:
        assert_test("POST /chem/weight (Invalid SMILES rejection)", False, str(e))

    # 10. Docking Targets
    try:
        r = requests.get(f"{BASE_URL}/dock/targets", timeout=5)
        targets = r.json()
        assert_test("GET /dock/targets (Phase 4 Docking Targets)", r.status_code == 200 and len(targets) >= 5, f"({len(targets)} targets available)")
    except Exception as e:
        assert_test("GET /dock/targets (Phase 4 Docking Targets)", False, str(e))

    # 11. Live Vina Docking Simulation (6LU7)
    try:
        dock_payload = {
            "smiles": "CC(=O)Oc1ccccc1C(=O)O",
            "target": "6LU7",
            "exhaustiveness": 4,
            "num_modes": 3
        }
        r = requests.post(f"{BASE_URL}/dock/run", json=dock_payload, timeout=45)
        data = r.json()
        affinity = data.get("best_affinity_kcal_mol")
        poses = data.get("poses", [])
        condition = (r.status_code == 200 and affinity is not None and affinity < 0.0 and len(poses) >= 1)
        assert_test("POST /dock/run (6LU7 Mpro Docking)", condition, f"(Best affinity = {affinity} kcal/mol, {len(poses)} poses)")
    except Exception as e:
        assert_test("POST /dock/run (6LU7 Mpro Docking)", False, str(e))

    # 12. Live Vina Docking Simulation (1ERE Estrogen Receptor Alpha)
    try:
        dock_payload = {
            "smiles": "CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O",  # 17b-estradiol
            "target": "1ERE",
            "exhaustiveness": 4,
            "num_modes": 3
        }
        r = requests.post(f"{BASE_URL}/dock/run", json=dock_payload, timeout=45)
        data = r.json()
        affinity = data.get("best_affinity_kcal_mol")
        poses = data.get("poses", [])
        condition = (r.status_code == 200 and affinity is not None and affinity < -8.0 and len(poses) >= 1)
        assert_test("POST /dock/run (1ERE ERa Docking)", condition, f"(Best affinity = {affinity} kcal/mol, {len(poses)} poses)")
    except Exception as e:
        assert_test("POST /dock/run (1ERE ERa Docking)", False, str(e))

    print("-" * 60)
    print(f" RESULTS: {passed} / {total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(run_tests())
