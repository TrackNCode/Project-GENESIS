"""
PyMOL Visualisation Service for Project GENESIS.
Manages structure preparation, format conversion (PDB, PDBQT, SDF, MOL2, mmCIF),
subprocess orchestration of PyMOL, and asset caching for backend API and frontend viewing.
"""

import os
import re
import sys
import json
import base64
import uuid
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import AllChem

# Path configuration
CURRENT_DIR = Path(__file__).resolve().parent
APP_DIR = CURRENT_DIR.parent
BACKEND_DIR = APP_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
VIZ_CACHE_DIR = DATA_DIR / "visualizations"
RECEPTOR_CACHE_DIR = DATA_DIR / "receptors"
PYTHON_EXE = Path(sys.executable)
PYMOL_RUNNER_SCRIPT = CURRENT_DIR / "pymol_runner.py"

VIZ_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def convert_pdbqt_to_pdb(pdbqt_content: str, output_pdb_path: Path, model_index: int = 1) -> Path:
    """
    Extract a specific model from AutoDock Vina docked PDBQT string and
    format as a standard PDB file suitable for PyMOL rendering.
    """
    output_pdb_path.parent.mkdir(parents=True, exist_ok=True)

    models = pdbqt_content.split("MODEL")
    target_lines: List[str] = []

    if len(models) > 1 and model_index < len(models):
        target_model = models[model_index]
    else:
        target_model = models[0] if models else pdbqt_content

    for line in target_model.splitlines():
        if line.startswith(("ATOM  ", "HETATM")):
            # Standard PDB columns 1-66 contain coords, occupancy, and tempFactor
            # Strip trailing Vina PDBQT charge/atom-type columns (67+)
            pdb_line = line[:66].ljust(80)
            target_lines.append(pdb_line)
        elif line.startswith(("TER   ", "ENDMDL", "END   ")):
            target_lines.append(line)

    if not any(l.startswith(("ATOM", "HETATM")) for l in target_lines):
        raise ValueError("No valid ATOM or HETATM records found in PDBQT content.")

    output_pdb_path.write_text("\n".join(target_lines) + "\n", encoding="utf-8")
    return output_pdb_path


def convert_smiles_to_sdf(smiles: str, output_sdf_path: Path) -> Path:
    """
    Generate 3D coordinates from SMILES using RDKit ETKDG + MMFF and save as SDF.
    """
    output_sdf_path.parent.mkdir(parents=True, exist_ok=True)
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

    writer = Chem.SDWriter(str(output_sdf_path))
    writer.write(mol)
    writer.close()
    return output_sdf_path


def prepare_structure_files(
    target_pdb_id: str,
    smiles: Optional[str] = None,
    docked_pdbqt: Optional[str] = None,
    job_dir: Optional[Path] = None,
    pose_mode: int = 1,
) -> Tuple[Path, Optional[Path]]:
    """
    Resolve and prepare local paths for receptor and ligand/docking pose.
    """
    if job_dir is None:
        job_id = str(uuid.uuid4())[:8]
        job_dir = VIZ_CACHE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    target_id = target_pdb_id.strip().upper()
    receptor_clean = RECEPTOR_CACHE_DIR / f"{target_id}_clean.pdb"

    # If clean receptor not cached, ensure it is fetched & cleaned
    if not receptor_clean.exists():
        from ..docking.docking_service import prepare_receptor_pdbqt
        prepare_receptor_pdbqt(target_id)

    if not receptor_clean.exists():
        raise FileNotFoundError(f"Could not prepare receptor PDB for '{target_id}' at {receptor_clean}")

    ligand_path: Optional[Path] = None
    if docked_pdbqt and len(docked_pdbqt.strip()) > 50:
        # User supplied docked pose PDBQT
        ligand_path = job_dir / f"docked_pose_mode_{pose_mode}.pdb"
        convert_pdbqt_to_pdb(docked_pdbqt, ligand_path, model_index=pose_mode)
    elif smiles and len(smiles.strip()) > 0:
        # User supplied SMILES ligand
        ligand_path = job_dir / "ligand.sdf"
        convert_smiles_to_sdf(smiles, ligand_path)

    return receptor_clean, ligand_path


def execute_pymol_job(
    target_pdb_id: str,
    smiles: Optional[str] = None,
    docked_pdbqt: Optional[str] = None,
    pose_mode: int = 1,
    style: str = "cartoon",
    pocket_radius: float = 4.5,
    contact_cutoff: float = 3.5,
    width: int = 1200,
    height: int = 900,
    dpi: int = 150,
    ray_trace: bool = True,
) -> Dict[str, Any]:
    """
    Full workflow: resolve files, invoke PyMOL headless subprocess, parse results,
    encode image as base64 for instant browser rendering, and return comprehensive analysis.
    """
    job_id = f"{target_pdb_id.lower()}_{uuid.uuid4().hex[:6]}"
    job_dir = VIZ_CACHE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    receptor_path, ligand_path = prepare_structure_files(
        target_pdb_id=target_pdb_id,
        smiles=smiles,
        docked_pdbqt=docked_pdbqt,
        job_dir=job_dir,
        pose_mode=pose_mode,
    )

    output_png = job_dir / f"{job_id}_render.png"
    output_pse = job_dir / f"{job_id}_session.pse"
    config_json = job_dir / f"{job_id}_config.json"

    config_data = {
        "receptor_path": str(receptor_path),
        "ligand_path": str(ligand_path) if ligand_path else None,
        "output_png": str(output_png),
        "output_pse": str(output_pse),
        "style": style,
        "pocket_radius": pocket_radius,
        "contact_cutoff": contact_cutoff,
        "width": width,
        "height": height,
        "dpi": dpi,
        "ray_trace": ray_trace,
        "title": f"Project GENESIS - {target_pdb_id.upper()}",
    }

    with open(config_json, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    # Invoke PyMOL runner via subprocess
    cmd = [
        str(PYTHON_EXE),
        str(PYMOL_RUNNER_SCRIPT),
        "--config", str(config_json)
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(job_dir),
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"PyMOL runner failed (exit {e.returncode}): {e.stderr or e.stdout}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("PyMOL execution timed out (>120s).")

    # Extract JSON between delimiters
    raw_output = proc.stdout
    if "===PYMOL_RESULT_BEGIN===" not in raw_output or "===PYMOL_RESULT_END===" not in raw_output:
        raise RuntimeError(f"Invalid PyMOL runner output format: {raw_output}")

    json_str = raw_output.split("===PYMOL_RESULT_BEGIN===")[1].split("===PYMOL_RESULT_END===")[0].strip()
    result = json.loads(json_str)

    if result.get("status") != "success":
        raise RuntimeError(result.get("error", "Unknown PyMOL error"))

    # Encode rendered PNG as base64 for instant frontend inline display
    image_base64 = ""
    if output_png.exists():
        with open(output_png, "rb") as f_img:
            image_base64 = base64.b64encode(f_img.read()).decode("utf-8")

    result["job_id"] = job_id
    result["image_base64"] = image_base64
    result["image_url"] = f"/viz/image/{job_id}_render.png"
    result["session_url"] = f"/viz/session/{job_id}_session.pse"
    result["target"] = target_pdb_id.upper()
    result["pose_mode"] = pose_mode

    return result
