"""
FastAPI Router for Project GENESIS AI Prediction Models & Lead Optimisation (Phase 6).
Provides endpoints for target-specific QSAR bioactivity, comprehensive ADME pharmacokinetics,
predictive toxicity safety profiling, bioisosteric lead optimization, and candidate scoring.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..models_ai.qsar_engine import qsar_engine
from ..models_ai.adme_engine import ADMEEngine
from ..models_ai.toxicity_engine import ToxicityEngine
from ..models_ai.lead_optimizer import LeadOptimizer

router = APIRouter(prefix="/ai_models", tags=["AI Prediction Models & Lead Optimisation (Phase 6)"])


class QSARPredictRequest(BaseModel):
    smiles: str = Field(..., description="Compound SMILES to evaluate")
    target: str = Field("6LU7", description="Target PDB ID (6LU7, 1IEP, 1ERE, 1M17, 1CX2)")


class ADMEProfileRequest(BaseModel):
    smiles: str = Field(..., description="Compound SMILES to profile")


class ToxicityProfileRequest(BaseModel):
    smiles: str = Field(..., description="Compound SMILES to profile")


class LeadOptSuggestRequest(BaseModel):
    smiles: str = Field(..., description="Lead SMILES string to optimize")
    target: str = Field("6LU7", description="Biological target for potency scoring")
    max_suggestions: int = Field(5, ge=1, le=10)


class FullProfileRequest(BaseModel):
    smiles: str = Field(..., description="Lead SMILES string")
    target: str = Field("6LU7", description="Target receptor PDB")


# -------------------------------------------------------------
# QSAR Bioactivity Endpoints
# -------------------------------------------------------------
@router.post("/qsar/predict", summary="Predict target-specific pIC50 and bioactivity class")
def predict_qsar_endpoint(req: QSARPredictRequest):
    """
    Predicts pIC50, estimated IC50 (nM), bioactivity classification,
    and applicability domain index for the specified target.
    """
    try:
        res = qsar_engine.predict_pIC50(req.smiles, target_id=req.target)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/qsar/multi_target", summary="Predict bioactivity across all benchmark targets")
def predict_multi_target_endpoint(req: ADMEProfileRequest):
    """
    Evaluates compound bioactivity across SARS-CoV-2 Mpro, Abl Kinase,
    ERalpha, EGFR, and COX-2.
    """
    try:
        return qsar_engine.predict_multi_target_profile(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# ADME Pharmacokinetics Endpoints
# -------------------------------------------------------------
@router.post("/adme/profile", summary="Predict full ADME pharmacokinetic profile")
def profile_adme_endpoint(req: ADMEProfileRequest):
    """
    Evaluates Human Intestinal Absorption (HIA), Caco-2 permeability,
    P-gp efflux, Blood-Brain Barrier (BBB), Plasma Protein Binding (PPB),
    CYP450 metabolism matrix, and clearance.
    """
    try:
        return ADMEEngine.profile_adme(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# Toxicity & Safety Profiling Endpoints
# -------------------------------------------------------------
@router.post("/toxicity/profile", summary="Predict toxicity and safety alerts")
def profile_toxicity_endpoint(req: ToxicityProfileRequest):
    """
    Predicts hERG cardiac toxicity, Ames mutagenicity, Drug-Induced
    Liver Injury (DILI), acute oral LD50, and toxicophoric alerts.
    """
    try:
        return ToxicityEngine.profile_toxicity(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# Lead Optimisation & Bioisostere Endpoints
# -------------------------------------------------------------
@router.post("/lead_opt/suggest", summary="Suggest bioisosteric modifications for lead optimization")
def suggest_lead_optimizations_endpoint(req: LeadOptSuggestRequest):
    """
    Identifies functional groups in the lead molecule and generates bioisosteric
    analogs with predicted delta pIC50, delta logP, and MPO desirability scores.
    """
    try:
        suggestions = LeadOptimizer.generate_bioisosteres(
            req.smiles,
            target=req.target,
            max_suggestions=req.max_suggestions
        )
        return {
            "lead_smiles": req.smiles,
            "target": req.target,
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lead_opt/comprehensive_lead_profile", summary="360-degree lead profiling report")
def get_comprehensive_lead_profile_endpoint(req: FullProfileRequest):
    """
    Generates integrated report combining QSAR bioactivity, multi-target selectivity,
    ADME properties, toxicity risks, MPO desirability, and bioisostere suggestions.
    """
    try:
        return LeadOptimizer.get_full_lead_profile(req.smiles, target=req.target)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# Candidate Database Evaluation Endpoint
# -------------------------------------------------------------
@router.post("/candidates/{candidate_id}/evaluate_all", summary="Evaluate and score a candidate in the SQLite DB")
def evaluate_candidate_in_db(candidate_id: int, target: str = "6LU7", db: Session = Depends(get_db)):
    """
    Retrieves candidate by ID, computes QSAR pIC50, ADME score, and Toxicity safety score,
    and updates the database record.
    """
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate ID #{candidate_id} not found")

    try:
        smiles = candidate.smiles
        qsar_res = qsar_engine.predict_pIC50(smiles, target_id=target)
        adme_res = ADMEEngine.profile_adme(smiles)
        tox_res = ToxicityEngine.profile_toxicity(smiles)

        candidate.qsar_score = qsar_res["predicted_pIC50"]
        candidate.adme_score = adme_res["adme_score"]
        candidate.toxicity_score = tox_res["safety_score"]

        # Qualify candidate if potency and safety pass thresholds
        if candidate.qsar_score >= 6.0 and candidate.toxicity_score >= 60.0:
            candidate.status = "LEAD_QUALIFIED"
        elif candidate.toxicity_score < 40.0:
            candidate.status = "TOX_FLAGGED"

        db.commit()
        db.refresh(candidate)

        return {
            "candidate_id": candidate.id,
            "smiles": candidate.smiles,
            "status": candidate.status,
            "docking_score": candidate.docking_score,
            "qsar_score": candidate.qsar_score,
            "adme_score": candidate.adme_score,
            "toxicity_score": candidate.toxicity_score,
            "target_evaluated": target,
            "activity_class": qsar_res["activity_class"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Candidate evaluation failed: {e}")
