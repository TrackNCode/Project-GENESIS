"""
AutoDock Vina Docking Engine & Molecular Preparation Service.
Handles receptor fetching/cleaning, ligand PDBQT preparation, grid configuration,
multithreaded docking execution, and binding affinity pose extraction.
"""

import os
import re
import sys
import shutil
import urllib.request
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy

# Root directories and binary paths
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent.parent
BIN_DIR = BACKEND_DIR / "bin"
VINA_EXE = BIN_DIR / "vina.exe"
RECEPTOR_CACHE_DIR = BACKEND_DIR / "data" / "receptors"

# Fallback conda Scripts directory for mk_prepare_receptor
CONDA_SCRIPTS = Path(sys.executable).parent / "Scripts"
MK_PREPARE_RECEPTOR_EXE = CONDA_SCRIPTS / "mk_prepare_receptor.exe"

# Standard Pre-configured Therapeutic Targets
PRESET_TARGETS: Dict[str, Dict[str, Any]] = {
    "6LU7": {
        "pdb_id": "6LU7",
        "name": "SARS-CoV-2 Main Protease (Mpro)",
        "organism": "SARS-CoV-2",
        "indication": "COVID-19 Antiviral Target",
        "description": "Catalytic Cys145-His41 dyad substrate-binding pocket complexed with inhibitor N3",
        "resolution_angstrom": 2.16,
        "chain": "A",
        "center": {"x": -10.46, "y": 4.10, "z": 73.01},
        "box_size": {"x": 22.0, "y": 22.0, "z": 22.0},
        "co_ligand": "02J",
    },
    "1IEP": {
        "pdb_id": "1IEP",
        "name": "Abl Tyrosine Kinase Domain",
        "organism": "Homo sapiens",
        "indication": "Chronic Myeloid Leukemia (CML)",
        "description": "Inactive conformation binding ATP-pocket complexed with Gleevec / Imatinib",
        "resolution_angstrom": 2.10,
        "chain": "A",
        "center": {"x": 15.61, "y": 53.38, "z": 15.45},
        "box_size": {"x": 20.0, "y": 20.0, "z": 20.0},
        "co_ligand": "STI",
    },
    "1M17": {
        "pdb_id": "1M17",
        "name": "EGFR Kinase Domain",
        "organism": "Homo sapiens",
        "indication": "Non-Small Cell Lung Cancer (NSCLC)",
        "description": "Epidermal Growth Factor Receptor kinase catalytic domain complexed with Erlotinib (Tarceva)",
        "resolution_angstrom": 2.60,
        "chain": "A",
        "center": {"x": 22.01, "y": 0.25, "z": 52.79},
        "box_size": {"x": 20.0, "y": 20.0, "z": 20.0},
        "co_ligand": "AQ4",
    },
    "1CX2": {
        "pdb_id": "1CX2",
        "name": "Cyclooxygenase-2 (COX-2)",
        "organism": "Mus musculus / Homo sapiens homolog",
        "indication": "Inflammation & Pain Management",
        "description": "Prostaglandin endoperoxide synthase-2 complexed with SC-558 selective inhibitor",
        "resolution_angstrom": 3.00,
        "chain": "A",
        "center": {"x": 24.26, "y": 21.53, "z": 16.50},
        "box_size": {"x": 22.0, "y": 22.0, "z": 22.0},
        "co_ligand": "SC5",
    },
    "1ERE": {
        "pdb_id": "1ERE",
        "name": "Estrogen Receptor Alpha (ERα)",
        "organism": "Homo sapiens",
        "indication": "Breast Cancer / Oncology",
        "description": "Nuclear hormone receptor ligand-binding domain complexed with 17β-estradiol",
        "resolution_angstrom": 3.10,
        "chain": "A",
        "center": {"x": 9.27, "y": 46.29, "z": 131.21},
        "box_size": {"x": 20.0, "y": 20.0, "z": 20.0},
        "co_ligand": "EST",
    },
}


def get_vina_path() -> str:
    """Return the absolute path to the local vina.exe executable."""
    if VINA_EXE.exists():
        return str(VINA_EXE)
    vina_in_path = shutil.which("vina.exe") or shutil.which("vina")
    if vina_in_path:
        return vina_in_path
    raise FileNotFoundError(
        f"AutoDock Vina executable not found at '{VINA_EXE}' or in system PATH. "
        "Ensure vina.exe is downloaded into backend/bin/."
    )


def prepare_ligand_pdbqt(smiles: str) -> str:
    """
    Generate 3D coordinates using RDKit (ETKDG + MMFF) and convert to
    AutoDock Vina PDBQT string with partial charges and rotatable bonds via Meeko.
    """
    if not smiles or not isinstance(smiles, str):
        raise ValueError("Valid SMILES string required.")

    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None:
        raise ValueError(f"Invalid SMILES string: '{smiles}'")

    mol = Chem.AddHs(mol)
    res = AllChem.EmbedMolecule(mol, randomSeed=42)
    if res != 0:
        AllChem.EmbedMolecule(mol, useRandomCoords=True, randomSeed=42)

    try:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
    except Exception:
        AllChem.UFFOptimizeMolecule(mol, maxIters=500)

    preparator = MoleculePreparation()
    mol_setups = preparator.prepare(mol)
    if not mol_setups:
        raise RuntimeError("Meeko failed to prepare ligand structure.")

    pdbqt_string = PDBQTWriterLegacy.write_string(mol_setups[0])[0]
    return pdbqt_string


def fetch_and_clean_pdb(pdb_id: str, output_dir: Path, target_chain: Optional[str] = None) -> Tuple[Path, Optional[Dict[str, float]]]:
    """
    Download PDB file from RCSB, filter for the active binding chain, strip alternate
    locations and water molecules, and compute co-crystallized ligand centroid.
    """
    pdb_id = pdb_id.strip().upper()
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_pdb_path = output_dir / f"{pdb_id}_clean.pdb"

    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    raw_pdb_path = output_dir / f"{pdb_id}_raw.pdb"

    if not raw_pdb_path.exists():
        try:
            urllib.request.urlretrieve(url, raw_pdb_path)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PDB '{pdb_id}' from RCSB: {e}")

    # Inspect available chains in ATOM records
    available_chains: List[str] = []
    with open(raw_pdb_path, "r", encoding="utf-8", errors="ignore") as f_in:
        for line in f_in:
            if line.startswith("ATOM  ") and len(line) > 21:
                ch = line[21]
                if ch not in available_chains:
                    available_chains.append(ch)

    # Determine chain to extract: preference given to target_chain, then 'A', then first available
    selected_chain = None
    if target_chain and target_chain in available_chains:
        selected_chain = target_chain
    elif "A" in available_chains:
        selected_chain = "A"
    elif available_chains:
        selected_chain = available_chains[0]

    # Parse and clean PDB: keep only selected chain and default alternate location 'A' or ' '
    ligand_coords: List[Tuple[float, float, float]] = []
    fallback_ligand_coords: List[Tuple[float, float, float]] = []

    with open(raw_pdb_path, "r", encoding="utf-8", errors="ignore") as f_in, \
         open(clean_pdb_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            if line.startswith("ATOM  "):
                ch = line[21] if len(line) > 21 else ""
                altloc = line[16] if len(line) > 16 else " "
                if (selected_chain is None or ch == selected_chain) and altloc in (" ", "A"):
                    f_out.write(line)
            elif line.startswith(("TER   ", "END   ")):
                f_out.write(line)
            elif line.startswith("HETATM") and "HOH" not in line and "WAT" not in line:
                try:
                    ch = line[21] if len(line) > 21 else ""
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    if selected_chain is not None and ch == selected_chain:
                        ligand_coords.append((x, y, z))
                    else:
                        fallback_ligand_coords.append((x, y, z))
                except (ValueError, IndexError):
                    pass

    centroid = None
    coords_to_use = ligand_coords or fallback_ligand_coords
    if coords_to_use:
        avg_x = sum(c[0] for c in coords_to_use) / len(coords_to_use)
        avg_y = sum(c[1] for c in coords_to_use) / len(coords_to_use)
        avg_z = sum(c[2] for c in coords_to_use) / len(coords_to_use)
        centroid = {"x": round(avg_x, 2), "y": round(avg_y, 2), "z": round(avg_z, 2)}

    return clean_pdb_path, centroid


def prepare_receptor_pdbqt(pdb_id: str) -> Tuple[str, Dict[str, float], Dict[str, float]]:
    """
    Ensure the target receptor is fetched, cleaned, converted to PDBQT,
    and return the path to the PDBQT file along with default grid center and box size.
    """
    pdb_id = pdb_id.strip().upper()
    target_info = PRESET_TARGETS.get(pdb_id)
    target_chain = target_info.get("chain", "A") if target_info else None

    RECEPTOR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pdbqt_path = RECEPTOR_CACHE_DIR / f"{pdb_id}.pdbqt"

    if target_info:
        default_center = target_info["center"]
        default_size = target_info["box_size"]
    else:
        default_center = {"x": 0.0, "y": 0.0, "z": 0.0}
        default_size = {"x": 20.0, "y": 20.0, "z": 20.0}

    # If already prepared and cached, return existing
    if pdbqt_path.exists() and os.path.getsize(pdbqt_path) > 1000:
        return str(pdbqt_path), default_center, default_size

    # Fetch and clean with chain and altloc filtering
    clean_pdb, detected_centroid = fetch_and_clean_pdb(pdb_id, RECEPTOR_CACHE_DIR, target_chain=target_chain)
    if detected_centroid and not target_info:
        default_center = detected_centroid

    # Convert clean PDB to PDBQT using mk_prepare_receptor
    mk_exe = str(MK_PREPARE_RECEPTOR_EXE) if MK_PREPARE_RECEPTOR_EXE.exists() else "mk_prepare_receptor"
    cmd = [
        mk_exe,
        "--read_pdb", str(clean_pdb),
        "-p", str(pdbqt_path),
        "-x",  # skip bad residues instead of failing
        "--default_altloc", "A",
        "--forgive_extra_bonds",
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mk_prepare_receptor failed for {pdb_id}: {e.stderr or e.stdout}")

    if not pdbqt_path.exists():
        raise RuntimeError(f"Expected receptor PDBQT was not generated at {pdbqt_path}")

    return str(pdbqt_path), default_center, default_size


def parse_docked_pdbqt(pdbqt_content: str) -> List[Dict[str, Any]]:
    """
    Parse multi-model docked PDBQT content generated by AutoDock Vina into
    individual binding modes with affinity scores and clean PDB coordinate blocks.
    """
    poses = []
    models = pdbqt_content.split("MODEL")
    for m in models[1:]:
        lines = m.strip().splitlines()
        affinity = None
        rmsd_lb = 0.0
        rmsd_ub = 0.0
        mode_num = len(poses) + 1

        pdb_lines = []
        atom_coords = []

        for line in lines:
            if "REMARK VINA RESULT:" in line:
                parts = line.split()
                try:
                    affinity = float(parts[3])
                    rmsd_lb = float(parts[4])
                    rmsd_ub = float(parts[5])
                except (IndexError, ValueError):
                    pass
            elif line.startswith(("ATOM", "HETATM")):
                # Format standard PDB line
                pdb_line = line[:66]
                pdb_lines.append(pdb_line)
                try:
                    symbol = line[76:78].strip() or line[12:16].strip()[0]
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    atom_coords.append({"symbol": symbol, "x": x, "y": y, "z": z})
                except (ValueError, IndexError):
                    pass

        if affinity is not None:
            poses.append({
                "mode": mode_num,
                "affinity_kcal_mol": affinity,
                "rmsd_lower_bound": rmsd_lb,
                "rmsd_upper_bound": rmsd_ub,
                "atom_count": len(atom_coords),
                "pdb_block": "\n".join(pdb_lines),
                "atoms": atom_coords,
            })

    return poses


def execute_docking(
    smiles: str,
    target: str = "6LU7",
    center: Optional[Dict[str, float]] = None,
    box_size: Optional[Dict[str, float]] = None,
    exhaustiveness: int = 8,
    num_modes: int = 9,
) -> Dict[str, Any]:
    """
    Execute full AutoDock Vina molecular docking pipeline:
    1. Prepares ligand from SMILES (with 3D embedding & charges).
    2. Retrieves / prepares receptor PDBQT.
    3. Runs Vina docking in an isolated temporary workspace.
    4. Extracts binding affinities, RMSDs, and coordinates.
    """
    vina_cmd = get_vina_path()
    receptor_path, default_center, default_size = prepare_receptor_pdbqt(target)

    # Use provided coordinates or defaults
    c = center if center else default_center
    s = box_size if box_size else default_size

    with tempfile.TemporaryDirectory(prefix="genesis_dock_") as temp_dir:
        temp_path = Path(temp_dir)
        ligand_path = temp_path / "ligand.pdbqt"
        output_pdbqt_path = temp_path / "docked_output.pdbqt"

        # Prepare ligand
        ligand_pdbqt = prepare_ligand_pdbqt(smiles)
        ligand_path.write_text(ligand_pdbqt, encoding="utf-8")

        # Build Vina command
        cmd = [
            vina_cmd,
            "--receptor", receptor_path,
            "--ligand", str(ligand_path),
            "--center_x", str(c["x"]),
            "--center_y", str(c["y"]),
            "--center_z", str(c["z"]),
            "--size_x", str(s["x"]),
            "--size_y", str(s["y"]),
            "--size_z", str(s["z"]),
            "--exhaustiveness", str(max(1, exhaustiveness)),
            "--num_modes", str(max(1, num_modes)),
            "--out", str(output_pdbqt_path),
            "--cpu", "0",  # Auto-detect full 28 logical threads of i7-14700KF
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=temp_dir,
                timeout=120,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AutoDock Vina execution failed: {e.stderr or e.stdout}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("AutoDock Vina docking simulation timed out (>120s).")

        if not output_pdbqt_path.exists():
            raise RuntimeError("AutoDock Vina produced no output poses file.")

        raw_output_pdbqt = output_pdbqt_path.read_text(encoding="utf-8")
        poses = parse_docked_pdbqt(raw_output_pdbqt)

        if not poses:
            raise RuntimeError("No valid docked poses could be parsed from Vina output.")

        best_affinity = poses[0]["affinity_kcal_mol"]

        # Read protein PDB lines for co-display if available
        clean_pdb_path = RECEPTOR_CACHE_DIR / f"{target.upper()}_clean.pdb"
        protein_pdb_snippet = ""
        if clean_pdb_path.exists():
            # First 500 lines or full for light visualization
            with open(clean_pdb_path, "r", encoding="utf-8", errors="ignore") as f:
                protein_pdb_snippet = "".join([f.readline() for _ in range(500)])

        return {
            "target": target.upper(),
            "target_name": PRESET_TARGETS.get(target.upper(), {}).get("name", "Custom Target"),
            "smiles": smiles,
            "grid_center": c,
            "grid_size": s,
            "exhaustiveness": exhaustiveness,
            "total_modes": len(poses),
            "best_affinity_kcal_mol": best_affinity,
            "poses": poses,
            "docked_pdbqt": raw_output_pdbqt,
            "protein_preview": protein_pdb_snippet,
        }
