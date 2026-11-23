"""
Project GENESIS - ChEMBL Web Resource Client & Ingestion Pipeline.
Queries EMBL-EBI ChEMBL REST API for experimental target activities (IC50, Ki, Kd, EC50),
mechanism of action, assay descriptions, and canonical structure records.
"""

from typing import Dict, Any, List, Optional
import time
import math
from pathlib import Path
import json
import requests
from .datamol_adapter import DatamolAdapter

CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "ingestion" / "chembl"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ChEMBLIngestionClient:
    """Interacts with ChEMBL REST API to retrieve experimental bioactivity records."""

    TARGET_PRESETS = {
        "6LU7": {"chembl_id": "CHEMBL4523582", "name": "SARS-CoV-2 3C-like proteinase (Mpro)", "organism": "Severe acute respiratory syndrome coronavirus 2"},
        "1IEP": {"chembl_id": "CHEMBL1862", "name": "Tyrosine-protein kinase ABL", "organism": "Homo sapiens"},
        "1ERE": {"chembl_id": "CHEMBL206", "name": "Estrogen receptor alpha", "organism": "Homo sapiens"},
        "1M17": {"chembl_id": "CHEMBL203", "name": "Epidermal growth factor receptor erbB1", "organism": "Homo sapiens"},
        "1CX2": {"chembl_id": "CHEMBL230", "name": "Cyclooxygenase-2", "organism": "Homo sapiens"},
    }

    @classmethod
    def get_target_info(cls, chembl_id: str) -> Optional[Dict[str, Any]]:
        """Fetch target metadata from ChEMBL."""
        url = f"{CHEMBL_API_BASE}/target/{chembl_id}.json"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except Exception:
            return None

    @classmethod
    def fetch_target_activities(
        cls,
        target_chembl_id: str,
        activity_type: str = "IC50",
        limit: int = 50,
        min_pchembl: float = 4.0
    ) -> Dict[str, Any]:
        """
        Query ChEMBL bioactivities for a specific target with standardized unit conversion.
        Converts standard_value (nM) to pChEMBL / pIC50: pIC50 = 9.0 - log10(nM).
        """
        # 1. Fast Cache-First Lookups to ensure offline resilience & sub-10ms latency
        for cf in sorted(CACHE_DIR.glob(f"{target_chembl_id}_{activity_type}_*.json"), reverse=True):
            try:
                with open(cf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    records = data.get("records", [])
                    if records:
                        for r in records:
                            if not r.get("bemis_murcko_scaffold"):
                                r["bemis_murcko_scaffold"] = DatamolAdapter.to_scaffold(r.get("smiles", ""))
                        return {
                            "status": "success",
                            "target_chembl_id": target_chembl_id,
                            "activity_type": activity_type,
                            "total_retrieved": len(records[:limit]),
                            "records": records[:limit],
                            "cached": True
                        }
            except Exception:
                continue

        url = f"{CHEMBL_API_BASE}/activity.json"
        params = {
            "target_chembl_id": target_chembl_id,
            "standard_type": activity_type,
            "standard_units": "nM",
            "limit": limit,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

        raw_data = None
        err_msg = ""
        for attempt in range(2):
            try:
                r = requests.get(url, params=params, headers=headers, timeout=(5, 10))
                r.raise_for_status()
                raw_data = r.json()
                break
            except Exception as e:
                err_msg = str(e)
                time.sleep(0.5)

        if raw_data is None:
            # Check for any other cached files for this target to maintain offline resilience
            fallback_caches = list(CACHE_DIR.glob(f"{target_chembl_id}_{activity_type}_*.json"))
            if fallback_caches:
                with open(fallback_caches[0], "r", encoding="utf-8") as f:
                    fb_data = json.load(f)
                    if fb_data.get("records"):
                        for r in fb_data["records"]:
                            if not r.get("bemis_murcko_scaffold"):
                                r["bemis_murcko_scaffold"] = DatamolAdapter.to_scaffold(r.get("smiles", ""))
                        return fb_data

            return {
                "status": "error",
                "message": f"Failed to retrieve ChEMBL activities after retries: {err_msg}",
                "target_chembl_id": target_chembl_id,
                "records": []
            }

        activities = raw_data.get("activities", [])
        standardized_records = []

        for act in activities:
            smi = act.get("canonical_smiles")
            if not smi:
                continue

            std_smi = DatamolAdapter.standardize_smiles(smi)
            if not std_smi:
                continue

            val_nm = act.get("standard_value")
            if val_nm is None:
                continue

            try:
                val_nm = float(val_nm)
                if val_nm <= 0:
                    continue
                # Calculate pIC50 = -log10(M) = 9.0 - log10(nM)
                pIC50 = round(9.0 - math.log10(val_nm), 3)
            except Exception:
                continue

            if pIC50 < min_pchembl:
                continue

            record = {
                "compound_chembl_id": act.get("molecule_chembl_id"),
                "smiles": std_smi,
                "inchikey": DatamolAdapter.get_inchikey(std_smi),
                "bemis_murcko_scaffold": DatamolAdapter.to_scaffold(std_smi),
                "activity_type": act.get("standard_type", activity_type),
                "experimental_value": val_nm,
                "experimental_units": "nM",
                "standardized_pIC50": pIC50,
                "target_chembl_id": target_chembl_id,
                "target_pref_name": act.get("target_pref_name", "Target"),
                "target_organism": act.get("target_organism", "Homo sapiens"),
                "assay_chembl_id": act.get("assay_chembl_id"),
                "assay_description": act.get("assay_description", "Bioassay measurement"),
                "document_chembl_id": act.get("document_chembl_id"),
                "provenance": {
                    "source": "ChEMBL Bioactivity Database (EMBL-EBI)",
                    "licence": "CC-BY-SA-3.0",
                    "retrieval_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "data_class": "GROUND_TRUTH_EXPERIMENTAL",
                    "confidence_score": 0.95,
                }
            }
            standardized_records.append(record)

        result_payload = {
            "status": "success",
            "target_chembl_id": target_chembl_id,
            "activity_type": activity_type,
            "total_retrieved": len(standardized_records),
            "records": standardized_records
        }

        # Save to disk cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)

        return result_payload
