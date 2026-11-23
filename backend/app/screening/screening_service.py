"""
Virtual Screening Pipeline Service for Project GENESIS (Phase 5).
Manages compound libraries, cheminformatics pre-filtering (Lipinski, Veber, PAINS),
multithreaded batch docking execution with AutoDock Vina, and multi-parametric hit ranking.
"""

import os
import sys
import json
import time
import uuid
import math
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdMolDescriptors

from ..docking.docking_service import execute_docking, PRESET_TARGETS

# Storage paths
CURRENT_DIR = Path(__file__).resolve().parent
APP_DIR = CURRENT_DIR.parent
BACKEND_DIR = APP_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
SCREENING_DATA_DIR = DATA_DIR / "screening"
SCREENING_DATA_DIR.mkdir(parents=True, exist_ok=True)

# In-memory screening job store with persistent JSON backups
SCREENING_JOBS: Dict[str, Dict[str, Any]] = {}

# Standard Curated Compound Libraries
CURATED_LIBRARIES: Dict[str, Dict[str, Any]] = {
    "fda_diversity": {
        "id": "fda_diversity",
        "name": "FDA-Approved Diverse Drug Set",
        "category": "Approved Therapeutics",
        "description": "Diverse collection of clinically validated FDA therapeutics across distinct structural classes",
        "compounds": [
            {"name": "Aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O", "class": "NSAID"},
            {"name": "Ibuprofen", "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O", "class": "NSAID"},
            {"name": "Acetaminophen", "smiles": "CC(=O)Nc1ccc(O)cc1", "class": "Analgesic"},
            {"name": "Ciprofloxacin", "smiles": "C1CC1N2C=C(C(=O)c3cc(c(cc32)N4CCNCC4)F)C(=O)O", "class": "Fluoroquinolone Antibiotic"},
            {"name": "Metformin", "smiles": "CN(C)C(=N)NC(=N)N", "class": "Biguanide Antidiabetic"},
            {"name": "Omeprazole", "smiles": "COc1ccc2[nH]c(nc2c1)S(=O)Cc3ncc(c(c3C)OC)C", "class": "Proton Pump Inhibitor"},
            {"name": "Atorvastatin", "smiles": "CC(C)c1c(c(c(n1CCC(CC(CC(=O)O)O)O)c2ccc(cc2)F)c3ccccc3)C(=O)Nc4ccccc4", "class": "Statin"},
            {"name": "Dexamethasone", "smiles": "CC1CC2C3CCC4=CC(=O)C=CC4(C3(C(CC2(C1(C(=O)CO)O)C)O)F)C", "class": "Corticosteroid"},
            {"name": "Sildenafil", "smiles": "CCCC1=NN(C2=C1N=C(NC2=O)C3=C(C=CC(=C3)S(=O)(=O)N4CCN(CC4)C)OCC)C", "class": "PDE5 Inhibitor"},
            {"name": "Warfarin", "smiles": "CC(=O)CC(c1ccccc1)c2c(c3ccccc3oc2=O)O", "class": "Anticoagulant"},
            {"name": "Metoprolol", "smiles": "COCCc1ccc(cc1)OCC(CNC(C)C)O", "class": "Beta-Blocker"},
            {"name": "Amoxicillin", "smiles": "CC1(C(N2C(S1)C(C2=O)NC(=O)C(c3ccc(cc3)O)N)C(=O)O)C", "class": "Beta-Lactam Antibiotic"},
        ]
    },
    "antiviral_protease": {
        "id": "antiviral_protease",
        "name": "Antiviral & Protease Inhibitor Focus Set",
        "category": "Infectious Disease",
        "description": "Clinical and investigational antiviral peptidomimetic and small-molecule protease inhibitors",
        "compounds": [
            {"name": "Ritonavir", "smiles": "CC(C)c1nc(cn1C)NC(=O)N(C)Cc2ccc(cc2)NC(=O)C(C(C)C)NC(=O)OCC3=CN=CS3", "class": "HIV/SARS-CoV-2 Protease Inhibitor"},
            {"name": "Nirmatrelvir Core", "smiles": "CC1(C2C1C(N(C2)C(=O)C(C(C)(C)C)NC(=O)C(F)(F)F)C(=O)NC(CC3CCNC3=O)C#N)C", "class": "Mpro Inhibitor (Paxlovid)"},
            {"name": "Boceprevir Core", "smiles": "CC(C)(C)NC(=O)NC(C(=O)N1CC2CC1C2(C)C)C(=O)NC(CC3CCCC3)C(=O)C(=O)N", "class": "HCV/Coronavirus Protease"},
            {"name": "Favipiravir", "smiles": "c1c(c(nc(n1)C(=O)N)O)F", "class": "RdRp Inhibitor"},
            {"name": "Ribavirin", "smiles": "c1nc(nn1C2C(C(C(O2)CO)O)O)C(=O)N", "class": "Guanosine Analog"},
            {"name": "Remdesivir Metabolite", "smiles": "C1=CC(=C2C(=N1)N(C=N2)C3C(C(C(O3)CO)O)F)N", "class": "Nucleoside Analog"},
            {"name": "Lopinavir Core", "smiles": "Cc1cccc(c1C)OCC(=O)NC(Cc2ccccc2)C(CC(Cc3ccccc3)NC(=O)C4CCCN4C(=O)N)O", "class": "HIV Protease Inhibitor"},
            {"name": "Saquinavir Core", "smiles": "CC(C)(C)NC(=O)C1CC2CCCCC2CN1CC(C(Cc3ccccc3)NC(=O)c4nc5ccccc5cc4)O", "class": "HIV Protease Inhibitor"},
        ]
    },
    "kinase_oncology": {
        "id": "kinase_oncology",
        "name": "Kinase & Oncology Targeted Library",
        "category": "Oncology",
        "description": "Type-I and Type-II kinase domain ATP-competitive inhibitors and oncology therapeutic leads",
        "compounds": [
            {"name": "Imatinib (Gleevec)", "smiles": "CN1CCN(CC1)Cc2ccc(cc2)C(=O)Nc3ccc(c(c3)C)Nc4nccc(n4)c5cccnc5", "class": "Bcr-Abl / c-Kit Inhibitor"},
            {"name": "Erlotinib (Tarceva)", "smiles": "COCCOc1cc2c(cc1OCCOC)ncnc2Nc3cccc(c3)C#C", "class": "EGFR Kinase Inhibitor"},
            {"name": "Gefitinib (Iressa)", "smiles": "COc1cc2ncnc(c2cc1OCCCN3CCOCC3)Nc4ccc(c(c4)Cl)F", "class": "EGFR Kinase Inhibitor"},
            {"name": "Dasatinib (Sprycel)", "smiles": "Cc1cccc(c1Cl)NC(=O)c2cnc(s2)Nc3cc(nc(n3)C)N4CCN(CC4)CCO", "class": "Multi-Kinase Inhibitor"},
            {"name": "Sorafenib (Nexavar)", "smiles": "CNC(=O)c1ccnc(c1)Oc2ccc(cc2)NC(=O)Nc3ccc(c(c3)Cl)C(F)(F)F", "class": "Raf / VEGFR Inhibitor"},
            {"name": "Lapatinib (Tykerb)", "smiles": "CS(=O)(=O)CCNCC1=CC=C(O1)C2=CC3=C(C=C2)N=CN=C3NC4=CC(=C(C=C4)OCC5=CC(=CC=C5)F)Cl", "class": "EGFR / HER2 Inhibitor"},
            {"name": "Sunifinib (Sutent)", "smiles": "CCN(CC)CCNC(=O)c1c(c(c([nH]1)C)/C=C/2\\c3cc(ccc3NC2=O)F)C", "class": "Multi-Targeted RTK"},
            {"name": "Crizotinib (Xalkori)", "smiles": "Cc1c(c(nn1)c2cc(ccc2N)Cl)Oc3cc(ncc3Cl)C(C)c4c(ccc(c4Cl)F)Cl", "class": "ALK / ROS1 Inhibitor"},
        ]
    },
    "natural_products": {
        "id": "natural_products",
        "name": "Bioactive Natural Products & Phenolics",
        "category": "Natural Leads",
        "description": "Polyphenols, flavonoids, and bioactive secondary metabolites with broad disease modulation",
        "compounds": [
            {"name": "Resveratrol", "smiles": "c1cc(ccc1/C=C/c2cc(cc(c2)O)O)O", "class": "Stilbenoid Antioxidant"},
            {"name": "Quercetin", "smiles": "c1cc(c(cc1c2c(c(=O)c3c(cc(cc3o2)O)O)O)O)O", "class": "Flavonoid Antioxidant"},
            {"name": "Curcumin", "smiles": "COC1=C(C=CC(=C1)/C=C/C(=O)CC(=O)/C=C/C2=CC(=C(C=C2)O)OC)O", "class": "Diarylheptanoid"},
            {"name": "Baicalein", "smiles": "c1ccc(cc1)c2cc(=O)c3c(o2)c(c(cc3O)O)O", "class": "Flavone"},
            {"name": "EGCG", "smiles": "c1cc(c(c(c1)O)O)C(=O)OC2CC(Oc3cc(cc(c32)O)O)c4cc(c(c(c4)O)O)O", "class": "Green Tea Catechin"},
            {"name": "Thymol", "smiles": "Cc1ccc(c(c1)O)C(C)C", "class": "Monoterpene"},
            {"name": "Caffeine", "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C", "class": "Purine Alkaloid"},
            {"name": "Genistein", "smiles": "c1cc(ccc1c2coc3cc(cc(c3c2=O)O)O)O", "class": "Isoflavone"},
        ]
    }
}

# PAINS and structural alert SMARTS definitions
PAINS_SMARTS = [
    ("Quinone", "[#6]1(=[O,S])[#6]=[#6][#6](=[O,S])[#6]=[#6]1"),
    ("Alkyl Halide", "[CX4][Cl,Br,I]"),
    ("Michael Acceptor", "[#6]=[#6]-[#6]=[O,S]"),
    ("Thioaldehyde/Thioketone", "[#6]=[S]"),
    ("Rhodanine", "O=C1NC(=S)SC1"),
    ("Sulfonyl Halide", "S(=O)(=O)[Cl,Br,I]"),
]
COMPILED_PAINS = [(name, Chem.MolFromSmarts(smarts)) for name, smarts in PAINS_SMARTS if Chem.MolFromSmarts(smarts) is not None]


def evaluate_cheminformatics_filters(
    mol: Chem.Mol,
    min_mw: float = 100.0,
    max_mw: float = 650.0,
    min_logp: float = -3.0,
    max_logp: float = 6.0,
    apply_lipinski: bool = True,
    apply_veber: bool = True,
    apply_pains: bool = True,
) -> Dict[str, Any]:
    """
    Evaluate molecule against multi-parametric physicochemical and medicinal chemistry filters.
    """
    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    rotb = Lipinski.NumRotatableBonds(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    heavy_atoms = mol.GetNumHeavyAtoms()

    violations: List[str] = []
    pains_alerts: List[str] = []

    # MW check
    if mw < min_mw or mw > max_mw:
        violations.append(f"MW {mw:.1f} out of bounds [{min_mw}, {max_mw}]")

    # LogP check
    if logp < min_logp or logp > max_logp:
        violations.append(f"LogP {logp:.2f} out of bounds [{min_logp}, {max_logp}]")

    # Lipinski Rule of 5
    lipinski_fails = 0
    if mw > 500: lipinski_fails += 1
    if logp > 5: lipinski_fails += 1
    if hbd > 5: lipinski_fails += 1
    if hba > 10: lipinski_fails += 1
    lipinski_pass = lipinski_fails <= 1

    if apply_lipinski and not lipinski_pass:
        violations.append(f"Failed Lipinski Rule of 5 ({lipinski_fails} criteria violated)")

    # Veber filter
    veber_pass = (rotb <= 10) and (tpsa <= 140.0)
    if apply_veber and not veber_pass:
        violations.append(f"Failed Veber filter (RotB={rotb}, TPSA={tpsa:.1f})")

    # PAINS check
    if apply_pains:
        for name, smarts_mol in COMPILED_PAINS:
            if mol.HasSubstructMatch(smarts_mol):
                pains_alerts.append(name)
        if pains_alerts:
            violations.append(f"PAINS alerts detected: {', '.join(pains_alerts)}")

    passed = len(violations) == 0

    return {
        "passed": passed,
        "mw": round(mw, 2),
        "logp": round(logp, 2),
        "hbd": hbd,
        "hba": hba,
        "rotatable_bonds": rotb,
        "tpsa": round(tpsa, 2),
        "heavy_atoms": heavy_atoms,
        "lipinski_pass": lipinski_pass,
        "veber_pass": veber_pass,
        "pains_alerts": pains_alerts,
        "violations": violations,
    }


def parse_custom_library_text(raw_text: str) -> List[Dict[str, str]]:
    """
    Parse user-provided custom compound text (SMILES per line or SMILES [TAB/SPACE] NAME).
    """
    compounds = []
    lines = raw_text.strip().splitlines()
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(None, 1)  # split on first whitespace
        smiles = parts[0].strip()
        name = parts[1].strip() if len(parts) > 1 else f"Compound_{idx + 1}"

        # Quick validation
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            compounds.append({"name": name, "smiles": smiles, "class": "Custom"})

    return compounds


def run_screening_worker(job_id: str):
    """
    Background worker thread executing batch screening, Vina docking, and scoring.
    """
    job = SCREENING_JOBS.get(job_id)
    if not job:
        return

    job["status"] = "running"
    job["start_time"] = time.time()
    save_job_backup(job_id)

    target = job["target"]
    compounds = job["compounds"]
    exhaustiveness = job.get("exhaustiveness", 4)
    filter_opts = job.get("filters", {})

    results: List[Dict[str, Any]] = []

    for idx, comp in enumerate(compounds):
        comp_name = comp["name"]
        comp_smiles = comp["smiles"]
        comp_class = comp.get("class", "Unspecified")

        job["progress"]["current"] = idx + 1
        job["progress"]["current_compound"] = comp_name
        job["progress"]["pct"] = round(((idx) / len(compounds)) * 100, 1)

        # 1. Cheminformatics Pre-Filter
        mol = Chem.MolFromSmiles(comp_smiles)
        if mol is None:
            results.append({
                "name": comp_name,
                "smiles": comp_smiles,
                "class": comp_class,
                "status": "rejected_invalid_smiles",
                "error": "Invalid SMILES structure",
            })
            continue

        filter_eval = evaluate_cheminformatics_filters(
            mol,
            apply_lipinski=filter_opts.get("lipinski", True),
            apply_veber=filter_opts.get("veber", True),
            apply_pains=filter_opts.get("pains", True),
            min_mw=filter_opts.get("min_mw", 100.0),
            max_mw=filter_opts.get("max_mw", 650.0),
        )

        if not filter_eval["passed"] and filter_opts.get("strict_filter", True):
            results.append({
                "name": comp_name,
                "smiles": comp_smiles,
                "class": comp_class,
                "status": "filtered_out",
                "filter_eval": filter_eval,
                "violations": filter_eval["violations"],
            })
            continue

        # 2. Docking Execution via AutoDock Vina
        try:
            dock_res = execute_docking(
                smiles=comp_smiles,
                target=target,
                exhaustiveness=exhaustiveness,
                num_modes=3,
            )

            affinity = dock_res["best_affinity_kcal_mol"]
            heavy_atoms = filter_eval["heavy_atoms"]

            # Ligand Efficiency (LE): kcal/mol per heavy atom
            le = round((-affinity / heavy_atoms), 3) if heavy_atoms > 0 else 0.0

            # pKi estimate and Lipophilic Ligand Efficiency (LLE)
            # pKi = -affinity / (2.303 * RT) where RT ~ 0.592 kcal/mol
            pki = round(-affinity / (2.303 * 0.592), 2)
            lle = round(pki - filter_eval["logp"], 2)

            # Composite Score: weighted combination
            # Higher affinity (more negative) gives higher score; penalize high MW / high LogP
            composite_score = round((-affinity * 1.5) + (le * 10.0) + (lle * 0.5), 2)

            results.append({
                "name": comp_name,
                "smiles": comp_smiles,
                "class": comp_class,
                "status": "docked",
                "binding_affinity_kcal_mol": affinity,
                "ligand_efficiency": le,
                "estimated_pki": pki,
                "lipophilic_efficiency_lle": lle,
                "composite_score": composite_score,
                "heavy_atoms": heavy_atoms,
                "mw": filter_eval["mw"],
                "logp": filter_eval["logp"],
                "tpsa": filter_eval["tpsa"],
                "rotatable_bonds": filter_eval["rotatable_bonds"],
                "lipinski_pass": filter_eval["lipinski_pass"],
                "pains_alerts": filter_eval["pains_alerts"],
                "docked_pdbqt": dock_res.get("docked_pdbqt", ""),
                "top_pose_pdb": dock_res.get("poses", [{}])[0].get("pdb_block", "") if dock_res.get("poses") else "",
                "docked_pdb": dock_res.get("poses", [{}])[0].get("pdb_block", "") if dock_res.get("poses") else "",
                "binding_affinity": affinity,
                "lipophilic_efficiency": lle,
                "prefilter_passed": filter_eval["lipinski_pass"],
                "total_modes": dock_res.get("total_modes", 0),
            })
        except Exception as e:
            results.append({
                "name": comp_name,
                "smiles": comp_smiles,
                "class": comp_class,
                "status": "docking_failed",
                "error": str(e),
                "filter_eval": filter_eval,
            })

    # Sort results: docked hits first by binding affinity ascending (most negative = highest affinity)
    docked_hits = [r for r in results if r["status"] == "docked"]
    other_hits = [r for r in results if r["status"] != "docked"]

    docked_hits.sort(key=lambda x: x["binding_affinity_kcal_mol"])

    # Assign rank
    for rank_idx, hit in enumerate(docked_hits):
        hit["rank"] = rank_idx + 1

    job["results"] = docked_hits + other_hits
    job["docked_count"] = len(docked_hits)
    job["filtered_count"] = len([r for r in results if r["status"] == "filtered_out"])
    job["failed_count"] = len([r for r in results if r["status"] in ("docking_failed", "rejected_invalid_smiles")])
    job["best_affinity"] = docked_hits[0]["binding_affinity_kcal_mol"] if docked_hits else None
    job["top_hit"] = docked_hits[0]["name"] if docked_hits else None

    job["status"] = "completed"
    job["end_time"] = time.time()
    job["duration_sec"] = round(job["end_time"] - job["start_time"], 1)
    job["progress"]["pct"] = 100.0

    save_job_backup(job_id)


def save_job_backup(job_id: str):
    """Write job metadata to local JSON for persistence across server restarts."""
    job = SCREENING_JOBS.get(job_id)
    if not job:
        return
    job_file = SCREENING_DATA_DIR / f"job_{job_id}.json"
    with open(job_file, "w", encoding="utf-8") as f:
        # Exclude massive raw PDBQT strings in summary backup
        safe_copy = dict(job)
        json.dump(safe_copy, f, indent=2, default=str)


def start_screening_job(
    target: str,
    library_id: Optional[str] = None,
    custom_compounds_text: Optional[str] = None,
    exhaustiveness: int = 4,
    filters: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Validate target and library, create job record, and launch background screening thread.
    """
    target = target.strip().upper()
    compounds: List[Dict[str, str]] = []

    if custom_compounds_text and len(custom_compounds_text.strip()) > 0:
        compounds = parse_custom_library_text(custom_compounds_text)
        lib_name = f"Custom Library ({len(compounds)} compounds)"
    elif library_id and library_id in CURATED_LIBRARIES:
        compounds = list(CURATED_LIBRARIES[library_id]["compounds"])
        lib_name = CURATED_LIBRARIES[library_id]["name"]
    else:
        raise ValueError("Must provide either a valid library_id or custom_compounds_text.")

    if not compounds:
        raise ValueError("No valid compound structures found in selected screening library.")

    job_id = f"screen_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    job_record = {
        "job_id": job_id,
        "target": target,
        "target_name": PRESET_TARGETS.get(target, {}).get("name", "Custom Target"),
        "library_id": library_id or "custom",
        "library_name": lib_name,
        "status": "pending",
        "progress": {
            "current": 0,
            "total": len(compounds),
            "pct": 0.0,
            "current_compound": "",
        },
        "compounds": compounds,
        "exhaustiveness": exhaustiveness,
        "filters": filters or {"lipinski": True, "veber": True, "pains": True, "strict_filter": True},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": [],
    }

    SCREENING_JOBS[job_id] = job_record

    # Launch in independent daemon thread
    worker_thread = threading.Thread(
        target=run_screening_worker,
        args=(job_id,),
        daemon=True,
        name=f"ScreeningWorker-{job_id}"
    )
    worker_thread.start()

    return job_id


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Return live status and progress of a screening job."""
    if job_id in SCREENING_JOBS:
        return SCREENING_JOBS[job_id]

    # Try loading from disk backup
    backup_file = SCREENING_DATA_DIR / f"job_{job_id}.json"
    if backup_file.exists():
        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            SCREENING_JOBS[job_id] = data
            return data

    return None
