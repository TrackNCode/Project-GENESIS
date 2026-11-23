"""
Project GENESIS - Predictive Toxicity & Safety Profiling Engine (Phase 6).
Evaluates hERG cardiac safety, Ames mutagenicity, Drug-Induced Liver Injury (DILI),
acute oral LD50, GHS hazard classification, and structural toxicophores.
"""

import math
from typing import Dict, Any, List, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen

from .descriptor_extractor import MolecularDescriptorExtractor


# Known toxicophoric alert SMARTS patterns (mutagenic, reactive, and organotoxic motifs)
TOXICOPHORE_SMARTS = {
    "Aromatic Nitro": "[$(c[N+](=O)[O-])]",
    "Aromatic Amine (Primary)": "[$(c[NH2])]",
    "Aliphatic Halide / Alkylating": "[CX4][Cl,Br,I]",
    "Epoxide / Aziridine": "[C,N]1[C,N]O1",
    "Hydrazine": "[NX3][NX3]",
    "Michael Acceptor (alpha,beta-unsaturated)": "[CX3]=[CX3][CX3](=[O,S])",
    "Acyl Halide": "[CX3](=[O,S])[Cl,Br,I]",
    "Isocyanate / Isothiocyanate": "[N,C]=[C,N]=[O,S]",
    "Quinone / Reactive Conjugated Dione": "O=C1C=CC(=O)C=C1",
    "Thiocarbonyl": "[CX3]=[SX1]",
}


class ToxicityEngine:
    """Predicts cardiac safety, mutagenicity, hepatotoxicity, and acute oral toxicity."""

    _compiled_toxicophores = None

    @classmethod
    def _get_toxicophores(cls):
        if cls._compiled_toxicophores is None:
            cls._compiled_toxicophores = {}
            for name, smarts in TOXICOPHORE_SMARTS.items():
                patt = Chem.MolFromSmarts(smarts)
                if patt:
                    cls._compiled_toxicophores[name] = patt
        return cls._compiled_toxicophores

    @classmethod
    def profile_toxicity(cls, smiles: str) -> Dict[str, Any]:
        """Generate comprehensive safety and toxicity report for a compound."""
        mol = MolecularDescriptorExtractor.get_mol(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: '{smiles}'")

        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        aromatic_rings = Descriptors.NumAromaticRings(mol)

        # Detect structural toxicophore alerts
        toxicophores = cls._get_toxicophores()
        detected_alerts = []
        for name, patt in toxicophores.items():
            if mol.HasSubstructMatch(patt):
                detected_alerts.append(name)

        # -------------------------------------------------------------
        # 1. hERG Cardiac Safety (IKr channel block risk)
        # -------------------------------------------------------------
        # High logP (>3), MW > 350, low TPSA (<70), and basic centers drive hERG block
        has_basic_nitrogen = any(atom.GetSymbol() == "N" and atom.GetTotalNumHs() > 0 for atom in mol.GetAtoms())
        herg_score = 0.15 + (0.12 * max(0.0, logp - 1.5)) + (0.25 if has_basic_nitrogen else 0.0) + (0.08 * aromatic_rings) - (0.002 * tpsa)
        herg_prob = round(max(0.05, min(0.95, herg_score)), 2)

        if herg_prob >= 0.60:
            herg_class = "High Risk (Potential QT Prolongation)"
            herg_flag = True
        elif herg_prob >= 0.35:
            herg_class = "Moderate Risk (Monitor ECG)"
            herg_flag = False
        else:
            herg_class = "Low Risk (Cardiosafe)"
            herg_flag = False

        # -------------------------------------------------------------
        # 2. Ames Mutagenicity (DNA Reactivity & Carcinogenicity)
        # -------------------------------------------------------------
        # Driven by presence of mutagenic structural alerts (nitro, amines, alkylators)
        mutagenic_alerts = [a for a in detected_alerts if a in ["Aromatic Nitro", "Aromatic Amine (Primary)", "Aliphatic Halide / Alkylating", "Epoxide / Aziridine", "Hydrazine"]]
        ames_prob = 0.08 + (0.35 * len(mutagenic_alerts)) + (0.05 * aromatic_rings)
        ames_prob = round(max(0.05, min(0.95, ames_prob)), 2)
        ames_mutagenic = ames_prob >= 0.50 or len(mutagenic_alerts) > 0

        # -------------------------------------------------------------
        # 3. Drug-Induced Liver Injury (DILI)
        # -------------------------------------------------------------
        # Reactive metabolites, Michael acceptors, quinones, and high lipophilicity
        dili_score = 0.20 + (0.10 * logp) + (0.25 if "Michael Acceptor (alpha,beta-unsaturated)" in detected_alerts or "Quinone / Reactive Conjugated Dione" in detected_alerts else 0.0)
        dili_prob = round(max(0.05, min(0.95, dili_score)), 2)
        if dili_prob >= 0.60:
            dili_class = "High Hepatotoxicity Concern"
        elif dili_prob >= 0.35:
            dili_class = "Moderate Concern"
        else:
            dili_class = "Low Hepatotoxicity Risk"

        # -------------------------------------------------------------
        # 4. Acute Oral Toxicity (Rat LD50 in mg/kg) & GHS Hazard Category
        # -------------------------------------------------------------
        # Log10(LD50_mol_kg) empirical QSAR estimation
        base_ld50 = 3.4 - (0.15 * logp) - (0.0008 * mw) - (0.35 * len(detected_alerts))
        ld50_mg_kg = round(math.pow(10, base_ld50) * mw, 0)
        ld50_mg_kg = max(25.0, min(15000.0, ld50_mg_kg))

        # GHS Hazard Classification
        if ld50_mg_kg <= 50.0:
            ghs_category = "Category I: Fatal if Swallowed"
            ghs_code = "GHS06 (Danger)"
        elif ld50_mg_kg <= 300.0:
            ghs_category = "Category II: Fatal if Swallowed"
            ghs_code = "GHS06 (Danger)"
        elif ld50_mg_kg <= 2000.0:
            ghs_category = "Category III: Toxic if Swallowed"
            ghs_code = "GHS06 (Toxic)"
        elif ld50_mg_kg <= 5000.0:
            ghs_category = "Category IV: Harmful if Swallowed"
            ghs_code = "GHS07 (Warning)"
        else:
            ghs_category = "Category V: Low Acute Toxicity"
            ghs_code = "Non-hazardous"

        # -------------------------------------------------------------
        # 5. Composite Safety Index (0 - 100)
        # -------------------------------------------------------------
        safety_score = 100.0
        safety_score -= (herg_prob * 35.0)
        safety_score -= (ames_prob * 35.0)
        safety_score -= (dili_prob * 20.0)
        safety_score -= (len(detected_alerts) * 10.0)
        safety_score = round(max(5.0, min(99.0, safety_score)), 1)

        return {
            "smiles": smiles,
            "safety_score": safety_score,
            "cardiac_herg": {
                "herg_inhibition_probability": herg_prob,
                "herg_risk_class": herg_class,
                "herg_positive_alert": herg_flag,
            },
            "mutagenicity_ames": {
                "ames_mutagenic": ames_mutagenic,
                "ames_probability": ames_prob,
                "mutagenic_alerts": mutagenic_alerts,
            },
            "hepatotoxicity_dili": {
                "dili_probability": dili_prob,
                "dili_risk_class": dili_class,
            },
            "acute_oral_toxicity": {
                "estimated_ld50_mg_kg": ld50_mg_kg,
                "ghs_hazard_category": ghs_category,
                "ghs_symbol": ghs_code,
            },
            "structural_toxicophores": {
                "alert_count": len(detected_alerts),
                "alerts": detected_alerts,
                "has_reactive_metabolite_motif": any(a in detected_alerts for a in ["Michael Acceptor (alpha,beta-unsaturated)", "Quinone / Reactive Conjugated Dione"]),
            }
        }
