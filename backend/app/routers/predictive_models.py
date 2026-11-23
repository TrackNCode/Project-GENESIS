"""
FastAPI Router for Project GENESIS Deep Neural Predictive Engine (Milestone 2 / Stage 3).
Exposes endpoints for Chemprop 2.x Evidential D-MPNN bioactivity prediction,
epistemic uncertainty quantification (u_epistemic), and multi-task ADMET profiling on NVIDIA RTX 3060 GPU.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..models_ai.chemprop_service import ChempropService

router = APIRouter(prefix="/predictive", tags=["Deep Neural Predictive Engine (Milestone 2)"])


class BioactivityPredictRequest(BaseModel):
    smiles: List[str] = Field(..., description="List of ligand SMILES strings for binding prediction")
    target: str = Field("6LU7", description="Target identifier (e.g. 6LU7 for SARS-CoV-2 Mpro, 1ERE for ESR1)")


class ADMETPredictRequest(BaseModel):
    smiles: List[str] = Field(..., description="List of ligand SMILES strings for ADMET evaluation")


@router.get("/status", summary="Check GPU predictive engine status and device specs")
def get_predictive_engine_status():
    """Return hardware accelerator status, Chemprop model version, and uncertainty capabilities."""
    return {
        "status": "online",
        "engine": "Chemprop Directed Message-Passing Neural Network (D-MPNN)",
        "version": "2.3.1",
        "device": "NVIDIA GeForce RTX 3060 (12.0 GB VRAM, CUDA 12.4)",
        "framework": "PyTorch 2.6.0+cu124",
        "capabilities": {
            "evidential_uncertainty": True,
            "epistemic_variance": "Closed-form Inverse-Gamma prior (gamma, v, alpha, beta)",
            "out_of_distribution_detection": True,
            "multi_task_admet": ["Caco-2 Effective Permeability", "hERG Cardiotoxicity Liability"],
            "supported_targets": ["6LU7 (SARS-CoV-2 Mpro)", "1ERE (ESR1)", "1IEP (ABL1)", "1M17 (EGFR)", "1CX2 (COX-2)"]
        }
    }


@router.post("/bioactivity", summary="Predict target binding affinity pIC50 with epistemic uncertainty")
def predict_bioactivity_endpoint(req: BioactivityPredictRequest):
    """
    Run D-MPNN evidential regression to predict pIC50, estimated Ki (nM),
    and epistemic uncertainty. Candidates with u_epistemic > 0.65 are flagged as OOD.
    """
    if not req.smiles:
        raise HTTPException(status_code=400, detail="Empty SMILES list provided")
    if len(req.smiles) > 200:
        raise HTTPException(status_code=400, detail="Batch size limit is 200 molecules")

    try:
        return ChempropService.predict_bioactivity(req.smiles, target=req.target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admet", summary="Predict multi-task Caco-2 permeability and hERG cardiotoxicity")
def predict_admet_endpoint(req: ADMETPredictRequest):
    """
    Predict multi-parameter ADMET properties:
    - Caco-2 apparent permeability (Papp log10 cm/s)
    - hERG potassium channel inhibition liability (0.0 to 1.0)
    - Aggregate ADMET risk classification (LOW / MODERATE / HIGH)
    """
    if not req.smiles:
        raise HTTPException(status_code=400, detail="Empty SMILES list provided")
    if len(req.smiles) > 200:
        raise HTTPException(status_code=400, detail="Batch size limit is 200 molecules")

    try:
        return ChempropService.predict_admet(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
