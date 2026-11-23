"""
Project GENESIS - Phase 5 Virtual Screening Pipeline Automated Test Suite
Tests:
  1. Discovery of curated screening libraries
  2. Cheminformatics pre-filtering (Lipinski, Veber, PAINS)
  3. Batch asynchronous virtual screening against SARS-CoV-2 Mpro (6LU7)
  4. Real-time status and progress polling
  5. Multi-parametric hit ranking (Affinity, LE, LLE, Composite Score)
  6. Sorting permutations (Affinity vs. LE vs. Composite)
  7. Candidate persistence into SQLite Project DB
  8. Streaming CSV and JSON report exports
  9. Visual verification via PyMOL rendering engine
"""

import sys
import time
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

def test_screening_suite():
    passed_tests = 0
    total_tests = 10

    print("=" * 70)
    print(" PROJECT GENESIS - PHASE 5: VIRTUAL SCREENING AUTOMATED TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # Test 1: Discover Curated Libraries
    # -------------------------------------------------------------
    print("\n--- Test 1: Discover Curated Libraries ---")
    try:
        r = requests.get(f"{BASE_URL}/screening/libraries", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        libs = r.json()
        assert len(libs) >= 4, f"Expected at least 4 libraries, got {len(libs)}"
        lib_ids = [l["id"] for l in libs]
        assert "fda_diversity" in lib_ids, "Missing fda_diversity library"
        assert "antiviral_protease" in lib_ids, "Missing antiviral_protease library"
        log(f"Found {len(libs)} curated libraries: {lib_ids}", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 1 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 2: Cheminformatics Pre-Filter (Lipinski, Veber, PAINS)
    # -------------------------------------------------------------
    print("\n--- Test 2: Cheminformatics Pre-Filter ---")
    try:
        payload = {
            "library_id": "fda_diversity",
            "apply_lipinski": True,
            "apply_veber": True,
            "apply_pains": True,
            "min_mw": 100.0,
            "max_mw": 600.0
        }
        r = requests.post(f"{BASE_URL}/screening/prefilter", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        res = r.json()
        assert "total_compounds" in res and res["total_compounds"] > 0
        assert "passed_count" in res
        assert "results" in res
        log(f"Pre-filter evaluated {res['total_compounds']} compounds: {res['passed_count']} passed ({res['pass_rate_pct']}%)", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 2 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 3: Launch Asynchronous Screening Job
    # -------------------------------------------------------------
    print("\n--- Test 3: Launch Asynchronous Screening Job (6LU7) ---")
    job_id = None
    try:
        # Mini test library for fast verification (Aspirin, Ibuprofen, Boceprevir Core)
        custom_test_cmpds = (
            "CC(=O)Oc1ccccc1C(=O)O Aspirin\n"
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O Ibuprofen\n"
            "CC(=O)Nc1ccc(O)cc1 Acetaminophen"
        )
        payload = {
            "target": "6LU7",
            "custom_compounds": custom_test_cmpds,
            "exhaustiveness": 2,  # fast test
            "apply_lipinski": True,
            "apply_veber": True,
            "apply_pains": True,
            "strict_filter": False
        }
        r = requests.post(f"{BASE_URL}/screening/start", json=payload, timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        start_res = r.json()
        job_id = start_res["job_id"]
        assert job_id.startswith("screen_"), f"Unexpected job_id format: {job_id}"
        log(f"Successfully initiated virtual screening job: {job_id}", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 3 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 4: Poll Job Progress to Completion
    # -------------------------------------------------------------
    print(f"\n--- Test 4: Polling Job Progress ({job_id}) ---")
    try:
        assert job_id is not None, "Cannot test polling without active job_id"
        completed = False
        start_time = time.time()
        while time.time() - start_time < 90:  # 90 sec timeout
            r = requests.get(f"{BASE_URL}/screening/status/{job_id}", timeout=5)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            stat = r.json()
            status_str = stat["status"].lower()
            pct = stat["progress"]["pct"]
            curr = stat["progress"].get("current_compound", "")
            current_idx = stat["progress"].get("current", 0)
            total_cmpds = stat["progress"].get("total", 0)
            print(f"  > Progress: {pct:.0f}% ({current_idx}/{total_cmpds}) | Active: {curr} | Status: {status_str}")
            if status_str == "completed":
                completed = True
                break
            elif status_str == "failed":
                raise RuntimeError(f"Screening job marked as FAILED: {stat.get('error')}")
            time.sleep(2.0)

        assert completed, "Screening job did not complete within timeout"
        log("Screening job reached 100% COMPLETED state", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 4 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 5: Fetch Results Sorted by Binding Affinity
    # -------------------------------------------------------------
    print("\n--- Test 5: Fetch Results Sorted by Binding Affinity (ΔG) ---")
    top_hit = None
    try:
        r = requests.get(f"{BASE_URL}/screening/results/{job_id}?sort_by=affinity", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        res_data = r.json()
        hits = res_data["ranked_hits"]
        assert len(hits) == 3, f"Expected 3 hits, got {len(hits)}"
        top_hit = hits[0]
        assert top_hit["binding_affinity"] < 0, f"Expected negative binding affinity, got {top_hit['binding_affinity']}"
        assert top_hit["ligand_efficiency"] > 0, f"Expected positive LE, got {top_hit['ligand_efficiency']}"
        assert "composite_score" in top_hit
        log(f"Top Hit: {top_hit['name']} | ΔG = {top_hit['binding_affinity']:.2f} kcal/mol | LE = {top_hit['ligand_efficiency']:.3f} | LLE = {top_hit['lipophilic_efficiency']:.2f}", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 5 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 6: Verify Multi-Parametric Sorting (Ligand Efficiency)
    # -------------------------------------------------------------
    print("\n--- Test 6: Verify Multi-Parametric Sorting (Ligand Efficiency) ---")
    try:
        r = requests.get(f"{BASE_URL}/screening/results/{job_id}?sort_by=ligand_efficiency", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        le_hits = r.json()["ranked_hits"]
        for i in range(len(le_hits) - 1):
            assert le_hits[i]["ligand_efficiency"] >= le_hits[i+1]["ligand_efficiency"], "LE sort ordering invalid"
        log(f"LE Ordering Valid: Top LE = {le_hits[0]['name']} ({le_hits[0]['ligand_efficiency']:.3f})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 6 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 7: Save Top Hit to Project Candidates Database
    # -------------------------------------------------------------
    print("\n--- Test 7: Persist Top Hit to Candidates Database ---")
    try:
        assert top_hit is not None, "No top hit available"
        cand_payload = {
            "project_id": 1,
            "name": top_hit["name"],
            "smiles": top_hit["smiles"],
            "binding_affinity": top_hit["binding_affinity"],
            "ligand_efficiency": top_hit["ligand_efficiency"],
            "target": "6LU7"
        }
        r = requests.post(f"{BASE_URL}/screening/save_candidate", json=cand_payload, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        save_res = r.json()
        assert save_res.get("status") in ["saved", "success"]
        log(f"Successfully saved candidate {top_hit['name']} (Candidate ID #{save_res.get('candidate_id')})", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 7 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 8: Export Screening Report as CSV
    # -------------------------------------------------------------
    print("\n--- Test 8: Export Screening Report as CSV ---")
    try:
        r = requests.get(f"{BASE_URL}/screening/export/{job_id}?format=csv", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        lines = r.text.strip().split("\n")
        assert len(lines) >= 4, f"Expected header + 3 rows, got {len(lines)}"
        assert "Rank" in lines[0] and "SMILES" in lines[0]
        log(f"Exported valid CSV report with {len(lines)-1} data rows", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 8 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 9: Export Screening Report as JSON
    # -------------------------------------------------------------
    print("\n--- Test 9: Export Screening Report as JSON ---")
    try:
        r = requests.get(f"{BASE_URL}/screening/export/{job_id}?format=json", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        json_export = r.json()
        assert "ranked_hits" in json_export
        assert len(json_export["ranked_hits"]) == 3
        log("Exported valid structured JSON screening dataset", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 9 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Test 10: PyMOL High-Res Visualization of Screened Hit
    # -------------------------------------------------------------
    print("\n--- Test 10: PyMOL High-Res Visualization of Screened Hit ---")
    try:
        assert top_hit is not None, "No top hit available"
        render_payload = {
            "target": "6LU7",
            "smiles": top_hit["smiles"],
            "style": "cartoon",
            "color_by": "chain",
            "pocket_residues_highlight": True,
            "distance_cutoff": 4.5,
            "ray_trace": True,
            "width": 800,
            "height": 600
        }
        r = requests.post(f"{BASE_URL}/viz/render", json=render_payload, timeout=30)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        render_data = r.json()
        assert "image_url" in render_data
        log(f"PyMOL rendered publication-quality scene: {render_data['image_url']}", "PASS")
        passed_tests += 1
    except Exception as e:
        log(f"Test 10 Failed: {e}", "FAIL")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f" PHASE 5 TEST SUMMARY: {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)")
    print("=" * 70)

    if passed_tests == total_tests:
        print("\n>>> ALL PHASE 5 VIRTUAL SCREENING TESTS PASSED PERFECTLY! <<<")
        sys.exit(0)
    else:
        print(f"\n>>> {total_tests - passed_tests} TESTS FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    test_screening_suite()
