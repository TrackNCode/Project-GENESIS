"""
FastAPI Router for Project GENESIS REINVENT 4 Multi-Objective Generative RL Engine (Milestone 4).
Exposes endpoints for de novo molecular generation, bioisosteric scaffold hopping,
and multi-parameter reward function evaluation on NVIDIA GeForce RTX 3060 CUDA.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..generation.reinvent_service import REINVENTService

router = APIRouter(prefix="/generation", tags=["Multi-Objective Generative Engine (Milestone 4)"])


class DeNovoGenerationRequest(BaseModel):
    target: str = Field("6LU7", description="Target PDB/ChEMBL ID (e.g. 6LU7 for SARS-CoV-2 Mpro, 1ERE for ESR1)")
    num_candidates: int = Field(8, ge=1, le=50, description="Number of unique candidates to generate")


class ScaffoldHopRequest(BaseModel):
    lead_smiles: str = Field(..., description="Reference lead molecular SMILES for scaffold hopping", json_schema_extra={"example": "CC(=O)Oc1ccccc1C(=O)O"})
    target: str = Field("6LU7", description="Target identifier")
    num_candidates: int = Field(5, ge=1, le=30, description="Number of hopped candidates to generate")


class CandidateScoreRequest(BaseModel):
    smiles: str = Field(..., description="Candidate molecule SMILES", json_schema_extra={"example": "CC(=O)Nc1ccc(O)cc1"})
    target: str = Field("6LU7", description="Target identifier")
    predicted_pIC50: float = Field(6.5, description="Chemprop D-MPNN predicted binding affinity pIC50")
    epistemic_uncertainty: float = Field(0.25, description="Evidential epistemic uncertainty u")
    herg_prob: float = Field(0.20, description="hERG cardiac toxicity liability probability")


@router.get("/status", summary="Check Generative RL engine status and reward configuration")
def get_generation_status():
    """Return status of REINVENT 4 generative agent and multi-objective reward weights."""
    return {
        "status": "online",
        "engine": "REINVENT 4 Multi-Objective Generative RL Engine",
        "device": "NVIDIA GeForce RTX 3060 CUDA",
        "sampling_modes": ["De Novo Generation", "Bioisosteric Scaffold Hopping", "R-Group Exploration"],
        "reward_weights": {
            "w_affinity": 0.35,
            "w_qed": 0.25,
            "w_sa_score": 0.20,
            "w_tox_penalty": 0.10,
            "w_epistemic_uncertainty_penalty": 0.10
        },
        "reward_formula": "R(x) = 0.35*Affinity + 0.25*QED + 0.20*SA - 0.10*ToxPenalty - 0.10*Uncertainty"
    }


@router.post("/de_novo", summary="Generate de novo drug candidates tailored to target active site")
def generate_de_novo_endpoint(req: DeNovoGenerationRequest):
    """
    Generate diverse, chemically valid, drug-like molecular candidates
    optimized across multiple objectives (affinity, QED, SA score, toxicity, and model certainty).
    """
    try:
        return REINVENTService.generate_de_novo(target=req.target, num_candidates=req.num_candidates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scaffold_hop", summary="Perform bioisosteric scaffold hopping around a lead core")
def scaffold_hop_endpoint(req: ScaffoldHopRequest):
    """
    Explore alternative core scaffolds and bioisosteres while preserving critical pharmacophore features.
    """
    try:
        return REINVENTService.scaffold_hop(lead_smiles=req.lead_smiles, target=req.target, num_candidates=req.num_candidates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score_candidate", summary="Compute multi-objective composite reward breakdown")
def score_candidate_endpoint(req: CandidateScoreRequest):
    """
    Evaluate multi-objective reward decomposition for an individual molecule:
    Affinity reward, QED, Synthetic Accessibility, Cardiotoxicity penalty, and Epistemic uncertainty penalty.
    """
    try:
        return REINVENTService.score_candidate(
            smiles=req.smiles,
            target=req.target,
            predicted_pIC50=req.predicted_pIC50,
            epistemic_uncertainty=req.epistemic_uncertainty,
            herg_prob=req.herg_prob
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
