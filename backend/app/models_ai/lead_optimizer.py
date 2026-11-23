"""
Project GENESIS - Lead Optimisation & Bioisostere Generation Engine (Phase 6).
Provides automated matched molecular pair (MMP) bioisosteric modifications,
multi-property objective (MPO) desirability scoring, and structured optimization roadmaps.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Crippen

from .descriptor_extractor import MolecularDescriptorExtractor
from .qsar_engine import qsar_engine
from .adme_engine import ADMEEngine
from .toxicity_engine import ToxicityEngine


# Standard medicinal chemistry bioisosteric transformation rules (SMIRKS / SMARTS pairs)
BIOISOSTERIC_RULES = [
    {
        "name": "Carboxylic Acid -> Tetrazole Bioisostere",
        "description": "Replaces carboxylic acid with tetrazole to improve membrane permeability while preserving planar acidic H-bond donor",
        "pattern": "[CX3](=O)[OX2H1]",
        "replacement": "c1nnn[nH]1",
        "hypothesis": "Maintains acidic bioactivity while enhancing lipophilicity and oral bioavailability"
    },
    {
        "name": "Carboxylic Acid -> Acylsulfonamide",
        "description": "Replaces carboxylic acid with acylsulfonamide bioisostere",
        "pattern": "[CX3](=O)[OX2H1]",
        "replacement": "C(=O)NS(=O)(=O)C",
        "hypothesis": "Acidic bioisostere with modulated pKa and improved cellular uptake"
    },
    {
        "name": "Phenol -> Indole NH Bioisostere",
        "description": "Substitutes phenolic -OH with indole/benzimidazole NH",
        "pattern": "c1cc(O)ccc1",
        "replacement": "c1cc2[nH]ccc2cc1",
        "hypothesis": "H-bond donor bioisostere with resistance against Phase-II glucuronidation"
    },
    {
        "name": "Aromatic Phenyl -> Pyridine (Nitrogen Walk)",
        "description": "Inserts ring nitrogen into phenyl ring",
        "pattern": "c1ccccc1",
        "replacement": "c1cccnc1",
        "hypothesis": "Reduces lipophilicity (cLogP ~ -1.0) and improves aqueous solubility and clearance"
    },
    {
        "name": "Aromatic Phenyl -> 4-Fluorophenyl (Metabolic Block)",
        "description": "Fluorinates para-position of aromatic ring",
        "pattern": "c1ccccc1",
        "replacement": "c1ccc(F)cc1",
        "hypothesis": "Blocks cytochrome P450 aromatic hydroxylation at vulnerable metabolic hot spots"
    },
    {
        "name": "Aromatic Methyl -> Trifluoromethyl (-CF3)",
        "description": "Replaces metabolic methyl with trifluoromethyl group",
        "pattern": "c1ccc(C)cc1",
        "replacement": "c1ccc(C(F)(F)F)cc1",
        "hypothesis": "Enhances binding in hydrophobic pockets and prevents CYP aliphatic oxidation"
    },
    {
        "name": "Secondary Amide -> 1,2,4-Oxadiazole Isostere",
        "description": "Heterocyclic bioisostere of amide peptide bond",
        "pattern": "[CX3](=O)[NH1][c,C]",
        "replacement": "c1nc(no1)C",
        "hypothesis": "Eliminates proteolytically labile amide bond; improves plasma stability"
    },
    {
        "name": "Solubilizing Tail Addition (Morpholine)",
        "description": "Appends morpholine solubilizing moiety to terminal phenyl/alkyl site",
        "pattern": "c1ccc(C)cc1",
        "replacement": "c1ccc(CN2CCOCC2)cc1",
        "hypothesis": "Increases aqueous solubility, optimizes pKa, and improves formulation potential"
    }
]


class LeadOptimizer:
    """Generates bioisosteres, evaluates MPO desirability, and suggests lead optimization steps."""

    @staticmethod
    def calculate_mpo_desirability(
        pIC50: float,
        logp: float,
        tpsa: float,
        herg_prob: float,
        ames_mutagenic: bool,
        adme_score: float
    ) -> Dict[str, Any]:
        """
        Calculate Multi-Property Objective (MPO) desirability score (0.0 - 1.0)
        across Potency, Lipophilicity, Polar Surface Area, Safety, and ADME.
        """
        # 1. Potency Desirability (d_potency): 1.0 for pIC50 >= 8.0, 0.0 for pIC50 <= 5.0
        if pIC50 >= 8.0:
            d_potency = 1.0
        elif pIC50 <= 5.0:
            d_potency = 0.05
        else:
            d_potency = (pIC50 - 5.0) / 3.0

        # 2. Lipophilicity Desirability (d_logp): Optimal in [1.5, 3.5]
        if 1.5 <= logp <= 3.5:
            d_logp = 1.0
        elif logp < 1.5:
            d_logp = max(0.1, 1.0 - ((1.5 - logp) / 2.5))
        else:  # logp > 3.5
            d_logp = max(0.05, 1.0 - ((logp - 3.5) / 2.5))

        # 3. TPSA Desirability (d_tpsa): Optimal in [40, 120]
        if 40.0 <= tpsa <= 120.0:
            d_tpsa = 1.0
        elif tpsa < 40.0:
            d_tpsa = 0.7
        else:
            d_tpsa = max(0.1, 1.0 - ((tpsa - 120.0) / 60.0))

        # 4. Safety Desirability (d_safety): Penalize high hERG risk and Ames mutagenicity
        d_safety = 1.0 - (herg_prob * 0.5)
        if ames_mutagenic:
            d_safety *= 0.3
        d_safety = max(0.05, min(1.0, d_safety))

        # 5. ADME Desirability (d_adme): Normalized 0-100 score
        d_adme = max(0.1, min(1.0, adme_score / 100.0))

        # Geometric Mean Composite MPO Score
        mpo_composite = round(math.pow(d_potency * d_logp * d_tpsa * d_safety * d_adme, 1.0 / 5.0), 3)

        return {
            "mpo_score": mpo_composite,
            "potency_desirability": round(d_potency, 3),
            "lipophilicity_desirability": round(d_logp, 3),
            "polar_surface_desirability": round(d_tpsa, 3),
            "safety_desirability": round(d_safety, 3),
            "adme_desirability": round(d_adme, 3),
            "rating": "Exceptional" if mpo_composite >= 0.75 else ("Good Lead" if mpo_composite >= 0.55 else ("Moderate" if mpo_composite >= 0.40 else "Sub-optimal")),
        }

    @classmethod
    def generate_bioisosteres(cls, smiles: str, target: str = "6LU7", max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """
        Scan lead molecule for modifiable motifs, apply bioisosteric transformations,
        and evaluate predicted potency, ADME, and toxicity improvements.
        """
        mol = MolecularDescriptorExtractor.get_mol(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: '{smiles}'")

        # Baseline predictions for original lead
        baseline_qsar = qsar_engine.predict_pIC50(smiles, target_id=target)
        baseline_adme = ADMEEngine.profile_adme(smiles)
        baseline_tox = ToxicityEngine.profile_toxicity(smiles)
        baseline_mpo = cls.calculate_mpo_desirability(
            pIC50=baseline_qsar["predicted_pIC50"],
            logp=baseline_adme["physicochemical_basis"]["logp"],
            tpsa=baseline_adme["physicochemical_basis"]["tpsa"],
            herg_prob=baseline_tox["cardiac_herg"]["herg_inhibition_probability"],
            ames_mutagenic=baseline_tox["mutagenicity_ames"]["ames_mutagenic"],
            adme_score=baseline_adme["adme_score"]
        )

        suggestions = []
        seen_smiles = {Chem.CanonSmiles(smiles)}

        for rule in BIOISOSTERIC_RULES:
            patt = Chem.MolFromSmarts(rule["pattern"])
            if patt and mol.HasSubstructMatch(patt):
                rep_mol = Chem.MolFromSmiles(rule["replacement"])
                if not rep_mol:
                    continue

                try:
                    # Apply chemical transformation via RDKit ReplaceSubstructs
                    new_mols = AllChem.ReplaceSubstructs(mol, patt, rep_mol, replaceAll=False)
                    for new_m in new_mols:
                        try:
                            Chem.SanitizeMol(new_m)
                            cand_smiles = Chem.MolToSmiles(new_m)
                            canon = Chem.CanonSmiles(cand_smiles)

                            if canon in seen_smiles or len(canon) < 5:
                                continue
                            seen_smiles.add(canon)

                            # Evaluate new analog
                            cand_qsar = qsar_engine.predict_pIC50(canon, target_id=target)
                            cand_adme = ADMEEngine.profile_adme(canon)
                            cand_tox = ToxicityEngine.profile_toxicity(canon)
                            cand_mpo = cls.calculate_mpo_desirability(
                                pIC50=cand_qsar["predicted_pIC50"],
                                logp=cand_adme["physicochemical_basis"]["logp"],
                                tpsa=cand_adme["physicochemical_basis"]["tpsa"],
                                herg_prob=cand_tox["cardiac_herg"]["herg_inhibition_probability"],
                                ames_mutagenic=cand_tox["mutagenicity_ames"]["ames_mutagenic"],
                                adme_score=cand_adme["adme_score"]
                            )

                            delta_pIC50 = round(cand_qsar["predicted_pIC50"] - baseline_qsar["predicted_pIC50"], 2)
                            delta_logp = round(cand_adme["physicochemical_basis"]["logp"] - baseline_adme["physicochemical_basis"]["logp"], 2)
                            delta_mpo = round(cand_mpo["mpo_score"] - baseline_mpo["mpo_score"], 3)

                            suggestions.append({
                                "rule_name": rule["name"],
                                "hypothesis": rule["hypothesis"],
                                "description": rule["description"],
                                "analog_smiles": canon,
                                "predicted_pIC50": cand_qsar["predicted_pIC50"],
                                "delta_pIC50": delta_pIC50,
                                "predicted_logp": cand_adme["physicochemical_basis"]["logp"],
                                "delta_logp": delta_logp,
                                "mpo_score": cand_mpo["mpo_score"],
                                "delta_mpo": delta_mpo,
                                "adme_score": cand_adme["adme_score"],
                                "safety_score": cand_tox["safety_score"],
                                "herg_prob": cand_tox["cardiac_herg"]["herg_inhibition_probability"],
                                "recommendation": "Advance to Synthesis/Docking" if delta_mpo >= 0 and delta_pIC50 >= -0.2 else "Secondary Analog",
                            })
                        except Exception:
                            continue
                except Exception:
                    continue

        # Sort suggestions by MPO desirability improvement descending
        suggestions.sort(key=lambda x: x["mpo_score"], reverse=True)
        return suggestions[:max_suggestions]

    @classmethod
    def get_full_lead_profile(cls, smiles: str, target: str = "6LU7") -> Dict[str, Any]:
        """
        Generate integrated 360-degree lead profiling report combining
        QSAR bioactivity, ADME pharmacokinetics, toxicity safety, MPO, and bioisosteres.
        """
        qsar = qsar_engine.predict_pIC50(smiles, target_id=target)
        multi_target = qsar_engine.predict_multi_target_profile(smiles)
        adme = ADMEEngine.profile_adme(smiles)
        tox = ToxicityEngine.profile_toxicity(smiles)

        mpo = cls.calculate_mpo_desirability(
            pIC50=qsar["predicted_pIC50"],
            logp=adme["physicochemical_basis"]["logp"],
            tpsa=adme["physicochemical_basis"]["tpsa"],
            herg_prob=tox["cardiac_herg"]["herg_inhibition_probability"],
            ames_mutagenic=tox["mutagenicity_ames"]["ames_mutagenic"],
            adme_score=adme["adme_score"]
        )

        bioisosteres = cls.generate_bioisosteres(smiles, target=target, max_suggestions=4)

        return {
            "smiles": smiles,
            "target": target,
            "qsar": qsar,
            "multi_target_profile": multi_target,
            "adme": adme,
            "toxicity": tox,
            "mpo_desirability": mpo,
            "bioisosteric_optimizations": bioisosteres,
        }
