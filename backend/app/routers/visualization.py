"""
FastAPI Router for Project GENESIS Molecular Visualisation Engine (PyMOL Integration).
Provides REST endpoints for high-resolution 3D rendering, session export (.pse),
binding pocket residue highlighting, and geometric contact distance measurements.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..visualization.pymol_service import execute_pymol_job, VIZ_CACHE_DIR
from ..docking.docking_service import PRESET_TARGETS

router = APIRouter(prefix="/viz", tags=["Molecular Visualisation Engine (PyMOL)"])


class VizRenderRequest(BaseModel):
    target: str = Field(..., description="Target PDB ID (e.g. 6LU7, 1ERE, 1IEP, 1M17, 1CX2)", json_schema_extra={"example": "6LU7"})
    smiles: Optional[str] = Field(None, description="Ligand SMILES string (for conformer overlay)", json_schema_extra={"example": "CC(=O)Oc1ccccc1C(=O)O"})
    docked_pdbqt: Optional[str] = Field(None, description="Docked PDBQT multi-model string from AutoDock Vina")
    pose_mode: int = Field(1, ge=1, le=20, description="Binding mode / pose number to visualize")
    style: str = Field("cartoon", description="Visual representation style: cartoon, surface, ribbon, sticks", json_schema_extra={"example": "cartoon"})
    pocket_radius: float = Field(4.5, ge=2.0, le=12.0, description="Radius around ligand to select binding pocket residues (Angstroms)")
    contact_cutoff: float = Field(3.5, ge=2.0, le=6.0, description="Maximum distance to detect geometric contacts (Angstroms)")
    width: int = Field(1200, ge=400, le=3840, description="Image render width in pixels")
    height: int = Field(900, ge=300, le=2160, description="Image render height in pixels")
    dpi: int = Field(150, ge=72, le=300, description="Rendering resolution (DPI)")
    ray_trace: bool = Field(True, description="Enable high-quality ray tracing")


class ContactAnalysisRequest(BaseModel):
    target: str = Field(..., description="Target PDB ID", json_schema_extra={"example": "6LU7"})
    smiles: Optional[str] = Field(None, description="Ligand SMILES")
    docked_pdbqt: Optional[str] = Field(None, description="Docked PDBQT string")
    contact_cutoff: float = Field(3.5, ge=2.0, le=6.0, description="Cutoff distance in Angstroms")


@router.get("/targets", summary="List pre-configured targets available for visualization")
def get_viz_targets():
    """Return all pre-configured protein targets with active site and indication metadata."""
    return list(PRESET_TARGETS.values())


@router.post("/render", summary="Generate high-resolution PyMOL rendering and .pse session")
def render_molecular_scene(req: VizRenderRequest):
    """
    Render 3D molecular visualization using Schrödinger PyMOL Open-Source 3.1.0:
    - Prepares protein structure and ligand / docking pose.
    - Applies secondary-structure coloring (marine alpha helices, salmon beta sheets).
    - Identifies and highlights binding pocket residues within specified radius.
    - Measures geometric inter-atomic distances (< 3.5 Å) and creates 3D dashed distance lines.
    - Generates high-resolution ray-traced PNG and reusable PyMOL session file (.pse).
    - Returns base64 image preview, geometric contact table, and session download link.
    """
    try:
        result = execute_pymol_job(
            target_pdb_id=req.target,
            smiles=req.smiles,
            docked_pdbqt=req.docked_pdbqt,
            pose_mode=req.pose_mode,
            style=req.style,
            pocket_radius=req.pocket_radius,
            contact_cutoff=req.contact_cutoff,
            width=req.width,
            height=req.height,
            dpi=req.dpi,
            ray_trace=req.ray_trace,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/image/{filename}", summary="Download or view generated PyMOL PNG image")
def get_rendered_image(filename: str):
    """Serve high-resolution PNG image produced by PyMOL rendering engine."""
    # Find file recursively in VIZ_CACHE_DIR
    matches = list(VIZ_CACHE_DIR.rglob(filename))
    if not matches or not matches[0].exists():
        raise HTTPException(status_code=404, detail=f"Image file '{filename}' not found.")
    return FileResponse(matches[0], media_type="image/png", filename=filename)


@router.get("/session/{filename}", summary="Download reusable PyMOL session (.pse)")
def get_session_file(filename: str):
    """Serve saved PyMOL session file (.pse) for desktop PyMOL visualization and editing."""
    matches = list(VIZ_CACHE_DIR.rglob(filename))
    if not matches or not matches[0].exists():
        raise HTTPException(status_code=404, detail=f"PyMOL session file '{filename}' not found.")
    return FileResponse(
        matches[0],
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/contacts", summary="Compute geometric contacts and distances between ligand and pocket")
def compute_contacts_endpoint(req: ContactAnalysisRequest):
    """
    Perform geometric contact distance analysis between ligand and pocket residues.
    Note: Distinguishes geometrically detected contacts from chemically validated bonds.
    """
    try:
        # Run lightweight fast render to extract contact table
        result = execute_pymol_job(
            target_pdb_id=req.target,
            smiles=req.smiles,
            docked_pdbqt=req.docked_pdbqt,
            contact_cutoff=req.contact_cutoff,
            width=400,
            height=300,
            dpi=72,
            ray_trace=False,
        )
        return {
            "target": req.target.upper(),
            "contact_cutoff_angstrom": req.contact_cutoff,
            "geometric_contacts_count": result.get("geometric_contacts_count", 0),
            "geometric_contacts": result.get("geometric_contacts", []),
            "pocket_residues": result.get("pocket_residues", []),
            "note": "Geometrically detected spatial proximity (< 3.5 Å). Does not imply experimentally validated chemical bonding."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
