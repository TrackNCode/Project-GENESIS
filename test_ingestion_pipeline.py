"""
test_ingestion_pipeline.py
Automated Verification Suite for Project GENESIS — Milestone 1:
Scientific Data Foundation & Governance Subsystem (TDC, ChEMBL, Open Targets, Datamol).
"""

import sys
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def log_test(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if detail:
        print(f"       -> {detail}")
    if not passed:
        sys.exit(1)

def test_sources_endpoint():
    print("\n--- Test 1: Ingestion Sources Catalog ---")
    r = requests.get(f"{BASE_URL}/ingestion/sources", timeout=10)
    passed = r.status_code == 200 and r.json().get("status") == "online"
    sources = [s["id"] for s in r.json().get("sources", [])]
    has_all = "chembl" in sources and "opentargets" in sources and "tdc" in sources
    log_test("GET /ingestion/sources returns registered scientific providers", passed and has_all, f"Found sources: {sources}")

def test_chembl_ingestion():
    print("\n--- Test 2: ChEMBL Live Bioactivity Ingestion & Standardization ---")
    payload = {
        "target_chembl_id": "CHEMBL4523582",  # SARS-CoV-2 Mpro
        "activity_type": "IC50",
        "limit": 10
    }
    r = requests.post(f"{BASE_URL}/ingestion/chembl/query_target", json=payload, timeout=25)
    passed = r.status_code == 200
    data = r.json()
    records = data.get("records", [])
    count = len(records)
    log_test("ChEMBL bioactivities queried and standardized to pIC50", passed and count > 0, f"Retrieved {count} records for CHEMBL4523582")
    
    # Check first record structure
    first = records[0]
    pIC50 = first.get("standardized_pIC50")
    scaffold = first.get("bemis_murcko_scaffold")
    provenance = first.get("provenance", {})
    passed_provenance = provenance.get("data_class") == "GROUND_TRUTH_EXPERIMENTAL"
    log_test("First record contains standardized pIC50 and Datamol Bemis-Murcko scaffold", pIC50 is not None and scaffold is not None, f"pIC50: {pIC50}, Scaffold: {scaffold}")
    log_test("Strict provenance metadata attached to ChEMBL record", passed_provenance, f"Source: {provenance.get('source')}, Licence: {provenance.get('licence')}")

def test_opentargets_tractability():
    print("\n--- Test 3: Open Targets Target Tractability & Association ---")
    payload = {
        "ensembl_id": "ENSG00000091831"  # ESR1 (Estrogen Receptor 1)
    }
    r = requests.post(f"{BASE_URL}/ingestion/opentargets/target_tractability", json=payload, timeout=25)
    passed = r.status_code == 200
    data = r.json()
    approved = data.get("has_approved_drugs")
    buckets = data.get("tractability_buckets", [])
    top_diseases = len(data.get("top_associated_diseases", []))
    log_test("Open Targets GraphQL returns target tractability and disease associations", passed and approved is True, f"ESR1 Approved Drugs: {approved}, Buckets: {buckets}, Diseases: {top_diseases}")

def test_tdc_benchmark_leak_free_splits():
    print("\n--- Test 4: TDC Benchmark Feed & Scaffold Partitioning ---")
    payload = {
        "dataset_id": "caco2_wang",
        "split_type": "scaffold"
    }
    r = requests.post(f"{BASE_URL}/ingestion/tdc/load_benchmark", json=payload, timeout=10)
    passed = r.status_code == 200
    data = r.json()
    splits = data.get("splits", {})
    train_n = len(splits.get("train", []))
    val_n = len(splits.get("val", []))
    test_n = len(splits.get("test", []))
    leak_audit = data.get("leak_free_audit", {})
    leak_free = leak_audit.get("leak_free", False)
    log_test("TDC Caco-2 benchmark loaded with scaffold-based splits", passed and train_n > 0, f"Train: {train_n}, Val: {val_n}, Test: {test_n}")
    log_test("Zero data leakage verified across train/val/test scaffold partitions", leak_free is True, f"Leak-free verified: {leak_free}, Metric: {leak_audit.get('train_test_scaffold_overlap')}")

def test_data_governance_enforcement():
    print("\n--- Test 5: Scientific Data Governance & Pseudo-Label Protection ---")
    
    # 5a. Valid experimental record
    valid_rec = {
        "molecule_id": "TEST_001",
        "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "activity_value": 7.45,
        "activity_unit": "pIC50",
        "provenance": {
            "source": "ChEMBL",
            "dataset_id": "CHEMBL4523582",
            "licence": "CC-BY-SA-3.0",
            "data_class": "GROUND_TRUTH_EXPERIMENTAL",
            "retrieval_timestamp": "2026-11-20T12:00:00Z"
        }
    }
    r = requests.post(f"{BASE_URL}/ingestion/audit/validate_record", json={"record": valid_rec}, timeout=10)
    data = r.json()
    valid_pass = r.status_code == 200 and data.get("compliant") is True and data.get("is_ground_truth") is True
    log_test("Data Governance accepts valid ground-truth experimental record", valid_pass, f"Compliant: {data.get('compliant')}, InChIKey: {data.get('inchikey')}")
    
    # 5b. Pseudo-label protection: In silico prediction must NOT be flagged as ground truth
    pred_rec = {
        "molecule_id": "LEAK_001",
        "smiles": "c1ccccc1",
        "provenance": {
            "source": "chemprop_dmpnn_v1",
            "dataset_id": "IN_SILICO_01",
            "licence": "Internal",
            "data_class": "MODEL_PREDICTION",
            "retrieval_timestamp": "2026-11-20T12:00:00Z"
        }
    }
    r = requests.post(f"{BASE_URL}/ingestion/audit/validate_record", json={"record": pred_rec}, timeout=10)
    data = r.json()
    # MODEL_PREDICTION must have is_ground_truth = False so training pipelines cannot ingest it as ground-truth
    pred_pass = r.status_code == 200 and data.get("is_ground_truth") is False
    log_test("Data Governance prevents model prediction from masquerading as experimental ground truth", pred_pass, f"data_class: {data.get('data_class')}, is_ground_truth: {data.get('is_ground_truth')}")
    
    # 5c. Invalid chemical structure
    bad_chem = {
        "molecule_id": "BAD_001",
        "smiles": "INVALID_SMILES_STRING_NOT_A_MOLECULE",
        "provenance": {
            "source": "ChEMBL",
            "dataset_id": "BAD_SET",
            "licence": "CC-BY-SA-3.0",
            "data_class": "GROUND_TRUTH_EXPERIMENTAL",
            "retrieval_timestamp": "2026-11-20T12:00:00Z"
        }
    }
    r = requests.post(f"{BASE_URL}/ingestion/audit/validate_record", json={"record": bad_chem}, timeout=10)
    data = r.json()
    bad_chem_pass = r.status_code == 200 and data.get("compliant") is False
    log_test("Data Governance REJECTS invalid chemical structures", bad_chem_pass, f"Issues: {data.get('issues')}")

if __name__ == "__main__":
    print("======================================================================")
    print(" PROJECT GENESIS — MILESTONE 1 AUTOMATED PIPELINE VERIFICATION")
    print(" Testing: TDC, ChEMBL Client, Open Targets, Datamol, Data Governance")
    print("======================================================================")
    
    test_sources_endpoint()
    test_chembl_ingestion()
    test_opentargets_tractability()
    test_tdc_benchmark_leak_free_splits()
    test_data_governance_enforcement()
    
    print("\n======================================================================")
    print(" 🎯 ALL MILESTONE 1 SCIENTIFIC DATA FOUNDATION TESTS PASSED (100%)")
    print("======================================================================")
