from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..docking.docking_service import (
    PRESET_TARGETS,
    execute_docking,
    prepare_receptor_pdbqt,
    RECEPTOR_CACHE_DIR,
)

router = APIRouter(prefix="/dock", tags=["Protein & Docking Engine"])


class DockingRequest(BaseModel):
    smiles: str = Field(..., description="Ligand SMILES string to dock", json_schema_extra={"example": "CC(=O)Oc1ccccc1C(=O)O"})
    target: str = Field("6LU7", description="Target PDB ID (preset or RCSB ID)", json_schema_extra={"example": "6LU7"})
    center_x: Optional[float] = Field(None, description="Grid center X coordinate (defaults to target active site)")
    center_y: Optional[float] = Field(None, description="Grid center Y coordinate (defaults to target active site)")
    center_z: Optional[float] = Field(None, description="Grid center Z coordinate (defaults to target active site)")
    size_x: Optional[float] = Field(None, description="Grid box size X in Angstroms", json_schema_extra={"example": 20.0})
    size_y: Optional[float] = Field(None, description="Grid box size Y in Angstroms", json_schema_extra={"example": 20.0})
    size_z: Optional[float] = Field(None, description="Grid box size Z in Angstroms", json_schema_extra={"example": 20.0})
    exhaustiveness: int = Field(4, ge=1, le=32, description="Vina search exhaustiveness (4=fast, 8=standard, 16=thorough)")
    num_modes: int = Field(9, ge=1, le=20, description="Maximum number of binding modes to generate")


class TargetPrepRequest(BaseModel):
    pdb_id: str = Field(..., description="4-letter RCSB Protein Data Bank accession code", json_schema_extra={"example": "1IEP"})


@router.get("/targets", summary="List pre-configured therapeutic protein targets")
def list_preset_targets():
    """Return all curated therapeutic targets with their active site center coordinates and indications."""
    return list(PRESET_TARGETS.values())


@router.post("/prepare_target", summary="Fetch and prepare receptor from RCSB PDB")
def prepare_target_endpoint(req: TargetPrepRequest):
    """Fetch target PDB from RCSB, clean waters, assign charges, and prepare rigid PDBQT."""
    try:
        pdbqt_path, center, box_size = prepare_receptor_pdbqt(req.pdb_id)
        return {
            "status": "prepared",
            "pdb_id": req.pdb_id.upper(),
            "pdbqt_path": pdbqt_path,
            "center": center,
            "box_size": box_size,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run", summary="Run AutoDock Vina molecular docking simulation")
def run_docking_endpoint(req: DockingRequest):
    """
    Perform local AutoDock Vina docking simulation:
    - Prepares ligand with 3D conformer embedding and Gasteiger charges.
    - Prepares protein receptor PDBQT.
    - Runs multithreaded docking across CPU cores.
    - Returns predicted binding affinity (kcal/mol), RMSDs, and docked poses.
    """
    try:
        center = None
        if req.center_x is not None and req.center_y is not None and req.center_z is not None:
            center = {"x": req.center_x, "y": req.center_y, "z": req.center_z}

        box_size = None
        if req.size_x is not None and req.size_y is not None and req.size_z is not None:
            box_size = {"x": req.size_x, "y": req.size_y, "z": req.size_z}

        result = execute_docking(
            smiles=req.smiles,
            target=req.target,
            center=center,
            box_size=box_size,
            exhaustiveness=req.exhaustiveness,
            num_modes=req.num_modes,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run_gnina", summary="Run dual AutoDock Vina + GNINA 3D-CNN molecular docking")
def run_gnina_docking_endpoint(req: DockingRequest):
    """
    Perform dual molecular docking:
    1. AutoDock Vina conformational exploration across CPU cores.
    2. Deep learning 3D-CNN rescoring on NVIDIA RTX 3060 CUDA.
    3. Returns CNNscore, CNNaffinity (pKd), Vina affinity (kcal/mol), and CompositeScore.
    """
    try:
        from ..docking.gnina_service import GNINAService
        center = None
        if req.center_x is not None and req.center_y is not None and req.center_z is not None:
            center = {"x": req.center_x, "y": req.center_y, "z": req.center_z}

        box_size = None
        if req.size_x is not None and req.size_y is not None and req.size_z is not None:
            box_size = {"x": req.size_x, "y": req.size_y, "z": req.size_z}

        result = GNINAService.run_gnina_docking(
            smiles=req.smiles,
            target=req.target,
            center=center,
            box_size=box_size,
            exhaustiveness=req.exhaustiveness,
            num_modes=req.num_modes,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/receptor_pdb/{pdb_id}", response_class=PlainTextResponse, summary="Download clean receptor PDB for 3D visualization")
def get_receptor_pdb(pdb_id: str):
    """Return raw cleaned PDB string of target protein for client-side 3D rendering."""
    pdb_path = RECEPTOR_CACHE_DIR / f"{pdb_id.upper()}_clean.pdb"
    if not pdb_path.exists():
        # Attempt preparation
        try:
            prepare_receptor_pdbqt(pdb_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Receptor '{pdb_id}' could not be prepared: {e}")

    if pdb_path.exists():
        return pdb_path.read_text(encoding="utf-8", errors="ignore")
    raise HTTPException(status_code=404, detail=f"Receptor PDB '{pdb_id}' not found.")
