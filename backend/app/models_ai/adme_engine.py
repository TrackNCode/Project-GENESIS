"""
Project GENESIS - Comprehensive ADME & Pharmacokinetic Profiling Engine (Phase 6).
Evaluates Human Intestinal Absorption (HIA), Caco-2 permeability, Blood-Brain Barrier (BBB),
Plasma Protein Binding (PPB), Cytochrome P450 (CYP1A2, 2C9, 2C19, 2D6, 3A4) metabolism,
and renal clearance.
"""

from typing import Dict, Any, List, Optional
import math
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski

from .descriptor_extractor import MolecularDescriptorExtractor


class ADMEEngine:
    """Predicts comprehensive ADME pharmacokinetic parameters for small molecules."""

    @classmethod
    def profile_adme(cls, smiles: str) -> Dict[str, Any]:
        """Generate comprehensive pharmacokinetic ADME profile from SMILES."""
        mol = MolecularDescriptorExtractor.get_mol(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: '{smiles}'")

        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        hbd = Lipinski.NumHDonors(mol)
        hba = Lipinski.NumHAcceptors(mol)
        rotb = Descriptors.NumRotatableBonds(mol)
        aromatic_rings = Descriptors.NumAromaticRings(mol)
        fraction_csp3 = Descriptors.FractionCSP3(mol)

        # -------------------------------------------------------------
        # 1. Absorption & Permeability
        # -------------------------------------------------------------
        # Human Intestinal Absorption (HIA %): Zhao et al. / Clark model derivation
        # HIA is negatively impacted by high TPSA and excessive HBD
        hia_val = 100.0 - (0.45 * tpsa) - (3.5 * hbd) + (2.0 * min(5.0, logp))
        hia_pct = round(max(5.0, min(99.0, hia_val)), 1)
        if hia_pct >= 80.0:
            hia_class = "High Absorption (>80%)"
            hia_status = "good"
        elif hia_pct >= 40.0:
            hia_class = "Moderate Absorption (40-80%)"
            hia_status = "moderate"
        else:
            hia_class = "Poor Absorption (<40%)"
            hia_status = "poor"

        # Caco-2 Cell Apparent Permeability (10^-6 cm/s)
        # LogPapp ~= -4.8 - 0.015*TPSA + 0.12*LogP - 0.002*MW
        log_papp = -4.5 - (0.014 * tpsa) + (0.15 * logp) - (0.0015 * mw)
        caco2_cm_s = round(math.pow(10, log_papp + 6), 2)  # in 10^-6 cm/s
        if caco2_cm_s >= 8.0:
            caco2_class = "High Permeability"
        elif caco2_cm_s >= 2.0:
            caco2_class = "Moderate Permeability"
        else:
            caco2_class = "Low Permeability"

        # P-glycoprotein (P-gp) Substrate & Inhibitor Probability
        # High MW (>400), TPSA > 75, and aromatic rings drive P-gp recognition
        pgp_sub_score = 0.2 + (0.0008 * mw) + (0.002 * tpsa) + (0.08 * aromatic_rings) - (0.2 * fraction_csp3)
        pgp_sub_prob = round(max(0.05, min(0.95, pgp_sub_score)), 2)
        pgp_substrate = pgp_sub_prob >= 0.50

        pgp_inh_score = 0.1 + (0.12 * logp) + (0.05 * aromatic_rings) - (0.001 * tpsa)
        pgp_inh_prob = round(max(0.05, min(0.95, pgp_inh_score)), 2)
        pgp_inhibitor = pgp_inh_prob >= 0.50

        # -------------------------------------------------------------
        # 2. Distribution
        # -------------------------------------------------------------
        # Blood-Brain Barrier (BBB) Penetration (Clark equation: LogBB = 0.152*LogP - 0.0148*TPSA + 0.139)
        log_bb = round((0.152 * logp) - (0.0148 * tpsa) + 0.139, 2)
        # LogBB > -0.3 generally indicates good CNS penetration
        bbb_penetrant = log_bb >= -0.3 and mw <= 450.0 and hbd <= 3
        bbb_class = "CNS Penetrant (BBB+)" if bbb_penetrant else "Non-Penetrant (BBB-)"

        # Plasma Protein Binding (PPB %)
        # Highly lipophilic molecules bind strongly to albumin
        ppb_val = 55.0 + (10.5 * logp) - (0.08 * tpsa) + (2.0 * aromatic_rings)
        ppb_pct = round(max(15.0, min(99.5, ppb_val)), 1)
        fraction_unbound = round(max(0.005, (100.0 - ppb_pct) / 100.0), 3)

        # Volume of Distribution (VDss in L/kg)
        # Low < 0.7 L/kg, Moderate 0.7 - 2.8 L/kg, High > 2.8 L/kg
        vdss_val = round(0.4 + (0.35 * logp) + (0.08 * aromatic_rings) - (0.003 * tpsa), 2)
        vdss_val = max(0.15, min(6.5, vdss_val))
        if vdss_val > 2.8:
            vdss_class = "High (Extensive tissue distribution)"
        elif vdss_val >= 0.7:
            vdss_class = "Moderate (Balanced distribution)"
        else:
            vdss_class = "Low (Confined to plasma/extracellular)"

        # -------------------------------------------------------------
        # 3. Cytochrome P450 Metabolism Matrix (CYP1A2, 2C9, 2C19, 2D6, 3A4)
        # -------------------------------------------------------------
        # Structural rules and probability estimates for 5 primary isoforms
        has_basic_nitrogen = any(atom.GetSymbol() == "N" and atom.GetTotalNumHs() > 0 for atom in mol.GetAtoms())
        has_carboxylic_acid = any(
            atom.GetSymbol() == "O" and any(nbr.GetSymbol() == "C" and any(nn.GetSymbol() == "O" for nn in nbr.GetNeighbors()) for nbr in atom.GetNeighbors())
            for atom in mol.GetAtoms()
        )

        # CYP1A2: Prefers planar aromatic molecules
        cyp1a2_prob = round(max(0.05, min(0.95, 0.1 + (0.15 * aromatic_rings) - (0.3 * fraction_csp3))), 2)

        # CYP2C9: Prefers lipophilic acids
        cyp2c9_prob = round(max(0.05, min(0.95, 0.15 + (0.12 * logp) + (0.35 if has_carboxylic_acid else 0.0))), 2)

        # CYP2C19: Prefers neutral/lipophilic heterocycles
        cyp2c19_prob = round(max(0.05, min(0.95, 0.2 + (0.10 * logp) + (0.05 * aromatic_rings))), 2)

        # CYP2D6: Strongly prefers basic amines with positive charge center
        cyp2d6_prob = round(max(0.05, min(0.95, 0.1 + (0.45 if has_basic_nitrogen else 0.0) + (0.08 * logp))), 2)

        # CYP3A4: Dominant isoform, prefers high MW (>350) and lipophilic bulk
        cyp3a4_prob = round(max(0.05, min(0.95, 0.15 + (0.001 * mw) + (0.10 * logp))), 2)

        cyp_matrix = {
            "CYP1A2": {"inhibitor": cyp1a2_prob >= 0.50, "probability": cyp1a2_prob, "isoform": "CYP1A2"},
            "CYP2C9": {"inhibitor": cyp2c9_prob >= 0.50, "probability": cyp2c9_prob, "isoform": "CYP2C9"},
            "CYP2C19": {"inhibitor": cyp2c19_prob >= 0.50, "probability": cyp2c19_prob, "isoform": "CYP2C19"},
            "CYP2D6": {"inhibitor": cyp2d6_prob >= 0.50, "probability": cyp2d6_prob, "isoform": "CYP2D6"},
            "CYP3A4": {"inhibitor": cyp3a4_prob >= 0.50, "probability": cyp3a4_prob, "isoform": "CYP3A4"},
        }

        # -------------------------------------------------------------
        # 4. Excretion & Clearance
        # -------------------------------------------------------------
        # Total Intrinsic Clearance (mL/min/kg)
        # Moderate clearance is preferred; high clearance leads to short half-life
        cl_val = 15.0 - (1.2 * logp) + (0.02 * tpsa) + (0.008 * mw)
        clearance_ml_min_kg = round(max(1.0, min(35.0, cl_val)), 2)
        if clearance_ml_min_kg >= 15.0:
            clearance_category = "High Clearance (Rapid Elimination)"
        elif clearance_ml_min_kg >= 5.0:
            clearance_category = "Moderate Clearance"
        else:
            clearance_category = "Low Clearance (Slow Elimination)"

        # Estimated Half-Life (t1/2 in hours): t1/2 = (0.693 * VDss * 1000) / (CL * 60)
        t_half = round((0.693 * vdss_val * 1000.0) / (clearance_ml_min_kg * 60.0), 1)
        t_half = max(0.5, min(48.0, t_half))

        # -------------------------------------------------------------
        # 5. Composite ADME Desirability Score (0 - 100)
        # -------------------------------------------------------------
        adme_score = 100.0
        if hia_pct < 60.0:
            adme_score -= 20.0
        if caco2_cm_s < 2.0:
            adme_score -= 15.0
        if ppb_pct > 95.0:
            adme_score -= 15.0
        # Penalize if multiple CYP enzymes are inhibited (potential drug-drug interactions)
        inhibited_cyps = sum(1 for c in cyp_matrix.values() if c["inhibitor"])
        adme_score -= (inhibited_cyps * 8.0)
        if clearance_ml_min_kg > 20.0:
            adme_score -= 10.0

        adme_score = round(max(10.0, min(99.0, adme_score)), 1)

        return {
            "smiles": smiles,
            "adme_score": adme_score,
            "absorption": {
                "hia_percentage": hia_pct,
                "hia_class": hia_class,
                "caco2_permeability_10e6_cm_s": caco2_cm_s,
                "caco2_class": caco2_class,
                "pgp_substrate": pgp_substrate,
                "pgp_substrate_probability": pgp_sub_prob,
                "pgp_inhibitor": pgp_inhibitor,
                "pgp_inhibitor_probability": pgp_inh_prob,
            },
            "distribution": {
                "log_bb": log_bb,
                "bbb_class": bbb_class,
                "bbb_penetrant": bbb_penetrant,
                "plasma_protein_binding_pct": ppb_pct,
                "fraction_unbound": fraction_unbound,
                "volume_of_distribution_L_kg": vdss_val,
                "vdss_class": vdss_class,
            },
            "metabolism": {
                "cyp_matrix": cyp_matrix,
                "inhibited_cyp_count": inhibited_cyps,
                "drug_interaction_risk": "High" if inhibited_cyps >= 3 else ("Moderate" if inhibited_cyps >= 1 else "Low"),
            },
            "excretion": {
                "clearance_ml_min_kg": clearance_ml_min_kg,
                "clearance_category": clearance_category,
                "estimated_half_life_hours": t_half,
            },
            "physicochemical_basis": {
                "mw": round(mw, 2),
                "logp": round(logp, 2),
                "tpsa": round(tpsa, 2),
                "hbd": hbd,
                "hba": hba,
                "rotatable_bonds": rotb,
            }
        }
