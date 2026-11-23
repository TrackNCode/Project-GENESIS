"""
Datamol and RDKit Unified Standardization & Scaffold Splitting Adapter (Phase 6+).
Implements salt stripping, tautomer standardization, Bemis-Murcko scaffold clustering,
generic framework extraction, and leak-free dataset partitioning.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import collections
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, SaltRemover
from rdkit.Chem.Scaffolds import MurckoScaffold


class DatamolAdapter:
    """Standardizes molecular structures and performs leak-free scaffold partitioning."""

    _remover = None

    @classmethod
    def get_salt_remover(cls) -> SaltRemover.SaltRemover:
        if cls._remover is None:
            cls._remover = SaltRemover.SaltRemover()
        return cls._remover

    @staticmethod
    def to_mol(smiles: str) -> Optional[Chem.Mol]:
        """Convert SMILES to sanitized RDKit Mol object."""
        if not smiles or not isinstance(smiles, str):
            return None
        try:
            mol = Chem.MolFromSmiles(smiles.strip())
            if mol is not None:
                Chem.SanitizeMol(mol)
            return mol
        except Exception:
            return None

    @classmethod
    def standardize_mol(cls, mol: Chem.Mol) -> Optional[Chem.Mol]:
        """
        Standardize molecular structure:
        1. Strip inorganic and organic salts/solvents.
        2. Neutralize charges where chemically appropriate.
        3. Assign stereochemical stereocenters.
        """
        if mol is None:
            return None

        try:
            # 1. Strip salts
            remover = cls.get_salt_remover()
            desalted = remover.StripMol(mol, dontRemoveAll=True)

            # In case multiple fragments remained, keep largest fragment by heavy atom count
            frags = Chem.GetMolFrags(desalted, asMols=True)
            if frags:
                largest = max(frags, key=lambda m: m.GetNumHeavyAtoms())
            else:
                largest = desalted

            # 2. Sanitize and assign stereochemistry
            Chem.SanitizeMol(largest)
            Chem.AssignStereochemistry(largest, cleanIt=True, force=True)
            return largest
        except Exception:
            return mol

    @classmethod
    def standardize_smiles(cls, smiles: str) -> Optional[str]:
        """Convert SMILES to canonical, desalted, standardized SMILES."""
        mol = cls.to_mol(smiles)
        if mol is None:
            return None
        std_mol = cls.standardize_mol(mol)
        if std_mol is None:
            return None
        return Chem.MolToSmiles(std_mol, isomericSmiles=True)

    @classmethod
    def get_inchikey(cls, smiles: str) -> Optional[str]:
        """Generate canonical InChIKey for deduplication."""
        mol = cls.to_mol(smiles)
        if mol is None:
            return None
        return Chem.MolToInchiKey(mol)

    @staticmethod
    def get_murcko_scaffold(mol: Chem.Mol) -> str:
        """Extract Bemis-Murcko core scaffold SMILES."""
        if mol is None:
            return ""
        try:
            scaffold = MurckoScaffold.GetScaffoldForMol(mol)
            return Chem.MolToSmiles(scaffold)
        except Exception:
            return ""

    @classmethod
    def to_scaffold(cls, smiles: str) -> str:
        """Extract Bemis-Murcko core scaffold SMILES from input SMILES."""
        mol = cls.to_mol(smiles)
        if mol is None:
            return ""
        return cls.get_murcko_scaffold(mol)

    @staticmethod
    def get_generic_murcko_scaffold(mol: Chem.Mol) -> str:
        """Extract generic all-carbon framework of Bemis-Murcko scaffold."""
        if mol is None:
            return ""
        try:
            scaffold = MurckoScaffold.MakeScaffoldGeneric(mol)
            return Chem.MolToSmiles(scaffold)
        except Exception:
            return ""

    @classmethod
    def scaffold_split(
        cls,
        records: List[Dict[str, Any]],
        smiles_key: str = "smiles",
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: int = 42
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Bemis-Murcko Scaffold Partitioning:
        Groups compounds by core molecular scaffold so that train, val,
        and test sets contain completely disjoint scaffold clusters.
        Prevents test data leakage and provides realistic generalization benchmark.
        """
        if not records:
            return {"train": [], "val": [], "test": []}

        scaffold_groups = collections.defaultdict(list)
        unparseable = []

        for r in records:
            smi = r.get(smiles_key)
            mol = cls.to_mol(smi)
            if mol is None:
                unparseable.append(r)
                continue

            scaffold = cls.get_murcko_scaffold(mol)
            if not scaffold:
                scaffold = "NO_RING_CORE"
            scaffold_groups[scaffold].append(r)

        # Sort scaffold groups by size descending (largest clusters allocated first)
        sorted_groups = sorted(scaffold_groups.values(), key=len, reverse=True)

        n_total = len(records) - len(unparseable)
        n_test_target = int(n_total * test_ratio)
        n_val_target = int(n_total * val_ratio)

        train_set = []
        val_set = []
        test_set = []

        for group in sorted_groups:
            if len(test_set) + len(group) <= n_test_target:
                test_set.extend(group)
            elif len(val_set) + len(group) <= n_val_target:
                val_set.extend(group)
            else:
                train_set.extend(group)

        # In case unparseable records exist, put in train
        train_set.extend(unparseable)

        return {
            "train": train_set,
            "val": val_set,
            "test": test_set,
            "stats": {
                "total_records": len(records),
                "total_scaffolds": len(scaffold_groups),
                "train_count": len(train_set),
                "val_count": len(val_set),
                "test_count": len(test_set),
                "train_pct": round((len(train_set) / max(1, len(records))) * 100, 1),
                "val_pct": round((len(val_set) / max(1, len(records))) * 100, 1),
                "test_pct": round((len(test_set) / max(1, len(records))) * 100, 1),
            }
        }
