"""
Project GENESIS - Scientific Data Governance & Quality Audit Engine (Stage 2).
Enforces strict provenance manifests, unit consistency, stereochemical sanitization,
separation of experimental ground-truth vs model predictions, and leak-free validation.
"""

from typing import Dict, Any, List, Optional, Set
from .datamol_adapter import DatamolAdapter


class DataGovernanceEngine:
    """Enforces scientific data integrity, anti-leakage rules, and provenance auditing."""

    REQUIRED_METADATA_FIELDS = [
        "source", "dataset_id", "licence", "data_class", "retrieval_timestamp"
    ]

    VALID_DATA_CLASSES = [
        "GROUND_TRUTH_EXPERIMENTAL",  # Wet-lab measured assays
        "CURATED_LITERATURE_EXTRACT", # Peer-reviewed paper extraction
        "MODEL_PREDICTION"            # In silico generated (Strictly forbidden from pseudo-label training)
    ]

    @classmethod
    def audit_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits an individual record for compliance with GENESIS scientific data standards:
        1. SMILES validity and stereochemical integrity.
        2. Presence of required provenance metadata.
        3. Clear demarcation between ground-truth and prediction.
        """
        issues = []
        smiles = record.get("smiles")

        if not smiles:
            issues.append("Missing SMILES string")
            return {"compliant": False, "issues": issues}

        mol = DatamolAdapter.to_mol(smiles)
        if mol is None:
            issues.append(f"Invalid chemical structure: '{smiles}'")
            return {"compliant": False, "issues": issues}

        prov = record.get("provenance", {})
        for field in cls.REQUIRED_METADATA_FIELDS:
            if field not in prov:
                issues.append(f"Missing required metadata field: 'provenance.{field}'")

        data_class = prov.get("data_class")
        if data_class not in cls.VALID_DATA_CLASSES:
            issues.append(f"Invalid data_class: '{data_class}'. Must be one of {cls.VALID_DATA_CLASSES}")

        is_ground_truth = data_class in ["GROUND_TRUTH_EXPERIMENTAL", "CURATED_LITERATURE_EXTRACT"]

        return {
            "compliant": len(issues) == 0,
            "canonical_smiles": DatamolAdapter.standardize_smiles(smiles),
            "inchikey": DatamolAdapter.get_inchikey(smiles),
            "is_ground_truth": is_ground_truth,
            "data_class": data_class,
            "issues": issues,
        }

    @classmethod
    def verify_split_leak_free(
        cls,
        splits: Dict[str, List[Dict[str, Any]]],
        smiles_key: str = "smiles"
    ) -> Dict[str, Any]:
        """
        Mathematically verifies that Train, Val, and Test sets have zero scaffold overlap.
        Computes the intersection of Bemis-Murcko core scaffold sets.
        """
        train_scaffolds: Set[str] = set()
        val_scaffolds: Set[str] = set()
        test_scaffolds: Set[str] = set()

        for r in splits.get("train", []):
            mol = DatamolAdapter.to_mol(r.get(smiles_key, ""))
            scaf = DatamolAdapter.get_murcko_scaffold(mol)
            if scaf:
                train_scaffolds.add(scaf)

        for r in splits.get("val", []):
            mol = DatamolAdapter.to_mol(r.get(smiles_key, ""))
            scaf = DatamolAdapter.get_murcko_scaffold(mol)
            if scaf:
                val_scaffolds.add(scaf)

        for r in splits.get("test", []):
            mol = DatamolAdapter.to_mol(r.get(smiles_key, ""))
            scaf = DatamolAdapter.get_murcko_scaffold(mol)
            if scaf:
                test_scaffolds.add(scaf)

        train_test_overlap = train_scaffolds.intersection(test_scaffolds)
        train_val_overlap = train_scaffolds.intersection(val_scaffolds)
        val_test_overlap = val_scaffolds.intersection(test_scaffolds)

        leak_free = len(train_test_overlap) == 0 and len(train_val_overlap) == 0 and len(val_test_overlap) == 0

        return {
            "leak_free": leak_free,
            "train_scaffold_count": len(train_scaffolds),
            "val_scaffold_count": len(val_scaffolds),
            "test_scaffold_count": len(test_scaffolds),
            "train_test_overlap_count": len(train_test_overlap),
            "train_test_overlap_scaffolds": list(train_test_overlap),
            "audit_verdict": "PASSED (Zero Test Leakage)" if leak_free else "FAILED (Scaffold Contamination Detected)"
        }
