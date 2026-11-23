"""
Molecular Descriptor and Structural Fingerprint Extractor for Project GENESIS (Phase 6).
Generates standardized Morgan (ECFP4), MACCS, and 24 RDKit physicochemical descriptors
for machine learning model input and applicability domain assessment.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, MACCSkeys, DataStructs


class MolecularDescriptorExtractor:
    """Extracts fingerprint and physicochemical features for QSAR/ADME/Tox models."""

    DESCRIPTOR_NAMES = [
        "MolWt", "MolLogP", "TPSA", "NumHDonors", "NumHAcceptors",
        "NumRotatableBonds", "HeavyAtomCount", "NumAromaticRings",
        "NumAliphaticRings", "NumSaturatedRings", "FractionCSP3",
        "MolMR", "LabuteASA", "BalabanJ", "BertzCT",
        "Chi0v", "Chi1v", "Chi2v", "Kappa1", "Kappa2", "Kappa3",
        "RingCount", "NumHeteroatoms", "NumValenceElectrons"
    ]

    @staticmethod
    def get_mol(smiles: str) -> Optional[Chem.Mol]:
        """Convert SMILES to clean RDKit Mol object."""
        if not smiles or not isinstance(smiles, str):
            return None
        return Chem.MolFromSmiles(smiles.strip())

    @classmethod
    def extract_physicochemical_dict(cls, mol: Chem.Mol) -> Dict[str, float]:
        """Extract a structured dictionary of 24 2D physicochemical descriptors."""
        return {
            "MolWt": round(float(Descriptors.MolWt(mol)), 4),
            "MolLogP": round(float(Descriptors.MolLogP(mol)), 4),
            "TPSA": round(float(Descriptors.TPSA(mol)), 2),
            "NumHDonors": int(Descriptors.NumHDonors(mol)),
            "NumHAcceptors": int(Descriptors.NumHAcceptors(mol)),
            "NumRotatableBonds": int(Descriptors.NumRotatableBonds(mol)),
            "HeavyAtomCount": int(Descriptors.HeavyAtomCount(mol)),
            "NumAromaticRings": int(Descriptors.NumAromaticRings(mol)),
            "NumAliphaticRings": int(Descriptors.NumAliphaticRings(mol)),
            "NumSaturatedRings": int(Descriptors.NumSaturatedRings(mol)),
            "FractionCSP3": round(float(Descriptors.FractionCSP3(mol)), 4),
            "MolMR": round(float(Descriptors.MolMR(mol)), 4),
            "LabuteASA": round(float(Descriptors.LabuteASA(mol)), 4),
            "BalabanJ": round(float(Descriptors.BalabanJ(mol)), 4),
            "BertzCT": round(float(Descriptors.BertzCT(mol)), 4),
            "Chi0v": round(float(Descriptors.Chi0v(mol)), 4),
            "Chi1v": round(float(Descriptors.Chi1v(mol)), 4),
            "Chi2v": round(float(Descriptors.Chi2v(mol)), 4),
            "Kappa1": round(float(Descriptors.Kappa1(mol)), 4),
            "Kappa2": round(float(Descriptors.Kappa2(mol)), 4),
            "Kappa3": round(float(Descriptors.Kappa3(mol)), 4),
            "RingCount": int(Descriptors.RingCount(mol)),
            "NumHeteroatoms": int(Descriptors.NumHeteroatoms(mol)),
            "NumValenceElectrons": int(Descriptors.NumValenceElectrons(mol)),
        }

    @classmethod
    def get_physicochemical_vector(cls, mol: Chem.Mol) -> np.ndarray:
        """Return 24 physicochemical descriptors as a 1D NumPy float array."""
        desc_dict = cls.extract_physicochemical_dict(mol)
        return np.array([desc_dict[name] for name in cls.DESCRIPTOR_NAMES], dtype=np.float32)

    @staticmethod
    def get_morgan_fingerprint(mol: Chem.Mol, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
        """Return Morgan (ECFP4) bit vector as 1D binary NumPy array."""
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros((n_bits,), dtype=np.int8)
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr

    @staticmethod
    def get_morgan_bitvect(mol: Chem.Mol, radius: int = 2, n_bits: int = 2048):
        """Return raw RDKit ExplicitBitVect for fast Tanimoto similarity comparisons."""
        return AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)

    @staticmethod
    def get_maccs_keys(mol: Chem.Mol) -> np.ndarray:
        """Return 166-bit MACCS structural key vector as 1D binary NumPy array."""
        fp = MACCSkeys.GenMACCSKeys(mol)
        arr = np.zeros((167,), dtype=np.int8)
        DataStructs.ConvertToNumpyArray(fp, arr)
        # MACCS keys in RDKit are 1-indexed (length 167 with index 0 unused)
        return arr[1:]

    @classmethod
    def get_composite_feature_vector(cls, mol: Chem.Mol, n_morgan_bits: int = 512) -> np.ndarray:
        """
        Concatenates condensed Morgan fingerprint (512 bits) + MACCS keys (166 bits)
        + 24 physicochemical descriptors for machine learning models.
        Total dimensions: 512 + 166 + 24 = 702 features.
        """
        morgan = cls.get_morgan_fingerprint(mol, radius=2, n_bits=n_morgan_bits)
        maccs = cls.get_maccs_keys(mol)
        physchem = cls.get_physicochemical_vector(mol)
        return np.concatenate([morgan, maccs, physchem])

    @staticmethod
    def compute_tanimoto_similarity(mol_a: Chem.Mol, mol_b: Chem.Mol, radius: int = 2, n_bits: int = 2048) -> float:
        """Calculate Tanimoto coefficient between two molecules using ECFP4 fingerprints."""
        fp_a = AllChem.GetMorganFingerprintAsBitVect(mol_a, radius, nBits=n_bits)
        fp_b = AllChem.GetMorganFingerprintAsBitVect(mol_b, radius, nBits=n_bits)
        return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))
