from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from ..chem.cheminfo import (
    mol_weight,
    mol_formula,
    mol_logp,
    mol_properties,
    mol_conformer_3d,
    mol_svg,
)

router = APIRouter(prefix="/chem", tags=["Chemistry"])


class SMILESRequest(BaseModel):
    smiles: str = Field(..., description="Valid SMILES string representing the chemical structure", example="CCO")


class ConformerRequest(BaseModel):
    smiles: str = Field(..., description="Valid SMILES string", example="CCO")
    optimize: bool = Field(True, description="Whether to optimize geometry using MMFF/UFF force field")


class WeightResponse(BaseModel):
    smiles: str
    weight: float


class FormulaResponse(BaseModel):
    smiles: str
    formula: str


class LogPResponse(BaseModel):
    smiles: str
    logp: float


@router.get("/presets", summary="Get standard pharmaceutical preset molecules")
def get_presets():
    """Return common drug and benchmark molecules with their SMILES and descriptions."""
    return [
        {"name": "Ethanol", "smiles": "CCO", "description": "Simple alcohol benchmark", "category": "Solvent/Reference"},
        {"name": "Aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O", "description": "Acetylsalicylic acid (NSAID)", "category": "NSAID"},
        {"name": "Caffeine", "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C", "description": "Central nervous system stimulant", "category": "Stimulant"},
        {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "description": "Acetaminophen analgesic and antipyretic", "category": "Analgesic"},
        {"name": "Ibuprofen", "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O", "description": "Nonsteroidal anti-inflammatory drug", "category": "NSAID"},
        {"name": "Nicotine", "smiles": "CN1CCC[C@H]1c2cccnc2", "description": "Nicotinic acetylcholine receptor agonist", "category": "Alkaloid"},
        {"name": "Penicillin G", "smiles": "CC1(C(N2C(S1)C(C2=O)NC(=O)Cc3ccccc3)C(=O)O)C", "description": "Beta-lactam antibiotic", "category": "Antibiotic"}
    ]


@router.post("/weight", response_model=WeightResponse, summary="Calculate exact molecular weight")
def get_molecular_weight(req: SMILESRequest):
    """Return the exact molecular weight (g/mol) for a given SMILES."""
    try:
        weight = mol_weight(req.smiles)
        return {"smiles": req.smiles, "weight": weight}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/formula", response_model=FormulaResponse, summary="Calculate Hill molecular formula")
def get_molecular_formula(req: SMILESRequest):
    """Return the Hill system molecular formula (e.g. C2H6O) for a given SMILES."""
    try:
        formula = mol_formula(req.smiles)
        return {"smiles": req.smiles, "formula": formula}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logp", response_model=LogPResponse, summary="Calculate Crippen octanol-water LogP")
def get_molecular_logp(req: SMILESRequest):
    """Return the calculated LogP octanol/water partition coefficient."""
    try:
        logp = mol_logp(req.smiles)
        return {"smiles": req.smiles, "logp": logp}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/properties", summary="Comprehensive physicochemical properties and Lipinski profile")
def get_molecular_properties(req: SMILESRequest):
    """Return MW, Formula, LogP, TPSA, HBD, HBA, Rotatable Bonds, and Lipinski Rule of 5 evaluation."""
    try:
        return mol_properties(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/conformer_3d", summary="Generate 3D conformer with coordinates and MolBlock")
def generate_3d_conformer(req: ConformerRequest):
    """Generate 3D embedded coordinates with force-field geometry optimization."""
    try:
        return mol_conformer_3d(req.smiles, optimize=req.optimize)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/structure_2d", summary="Render 2D molecule depiction SVG")
def get_2d_structure_svg(req: SMILESRequest):
    """Return raw 2D depiction as SVG graphic."""
    try:
        svg_content = mol_svg(req.smiles)
        return Response(content=svg_content, media_type="image/svg+xml")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
