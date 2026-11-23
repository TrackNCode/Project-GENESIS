"""
iterative_loop.py
FastAPI router for Project GENESIS Closed-Loop Iterative Discovery & Lineage System (Milestone 5).
Exposes endpoints to launch iterative discovery campaigns, inspect lineage DAG trees,
and retrieve iteration-level failure taxonomies and Pareto frontiers.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..iterative_loop.models import DiscoveryCampaign, CandidateNode, IterationSummary
from ..iterative_loop.orchestrator import IterativeLoopOrchestrator

router = APIRouter(prefix="/iterative_loop", tags=["Iterative Discovery Loop"])


class RunCampaignRequest(BaseModel):
    campaign_name: str = Field("SARS-CoV-2 Mpro Optimization Campaign", description="Name of the discovery campaign")
    target: str = Field("6LU7", description="Target PDB identifier (e.g. 6LU7, 1ERE)")
    total_iterations: int = Field(2, ge=1, le=5, description="Number of iterative discovery rounds")
    candidates_per_iter: int = Field(4, ge=1, le=10, description="Number of candidates generated per round")
    initial_lead_smiles: Optional[str] = Field(None, description="Optional starting lead SMILES for scaffold hopping")


@router.post("/run", summary="Launch a closed-loop iterative discovery campaign")
def run_discovery_campaign(request: RunCampaignRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Executes the 9-stage closed-loop iterative discovery workflow:
    GENERATE -> SCREEN -> DOCK -> PREDICT -> EVALUATE -> ANALYSE -> LEARN -> OPTIMISE -> GENERATE AGAIN
    """
    res = IterativeLoopOrchestrator.run_campaign(
        campaign_name=request.campaign_name,
        target=request.target,
        total_iterations=request.total_iterations,
        candidates_per_iter=request.candidates_per_iter,
        initial_lead_smiles=request.initial_lead_smiles,
        db=db
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message", "Campaign execution failed"))
    return res


@router.get("/campaigns", summary="List all discovery campaigns")
def list_campaigns(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve all discovery campaigns with status and summary metrics."""
    campaigns = db.query(DiscoveryCampaign).order_by(DiscoveryCampaign.created_at.desc()).all()
    results = []
    for c in campaigns:
        results.append({
            "id": c.id,
            "name": c.name,
            "target": c.target,
            "target_name": c.target_name,
            "total_iterations": c.total_iterations,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            "summary_metrics": c.summary_metrics or {}
        })
    return results


@router.get("/campaign/{campaign_id}", summary="Get full campaign details and iteration summaries")
def get_campaign(campaign_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve campaign metadata, iteration-by-iteration summaries, and candidates."""
    campaign = db.query(DiscoveryCampaign).filter(DiscoveryCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    iterations = db.query(IterationSummary).filter(IterationSummary.campaign_id == campaign_id).order_by(IterationSummary.iteration.asc()).all()
    candidates = db.query(CandidateNode).filter(CandidateNode.campaign_id == campaign_id).order_by(CandidateNode.iteration.asc(), CandidateNode.composite_reward.desc()).all()

    return {
        "id": campaign.id,
        "name": campaign.name,
        "target": campaign.target,
        "target_name": campaign.target_name,
        "total_iterations": campaign.total_iterations,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
        "summary_metrics": campaign.summary_metrics or {},
        "iterations": [
            {
                "iteration": it.iteration,
                "generated_count": it.generated_count,
                "screened_count": it.screened_count,
                "docked_count": it.docked_count,
                "accepted_count": it.accepted_count,
                "rejected_count": it.rejected_count,
                "mean_reward": it.mean_reward,
                "best_reward": it.best_reward,
                "best_candidate_id": it.best_candidate_id,
                "failure_taxonomy": it.failure_taxonomy or {}
            }
            for it in iterations
        ],
        "candidates": [
            {
                "id": c.id,
                "iteration": c.iteration,
                "parent_id": c.parent_id,
                "smiles": c.smiles,
                "inchikey": c.inchikey,
                "bemis_murcko_scaffold": c.bemis_murcko_scaffold,
                "molecular_weight": c.molecular_weight,
                "logP": c.logP,
                "vina_affinity_kcal_mol": c.vina_affinity_kcal_mol,
                "cnn_score": c.cnn_score,
                "cnn_affinity_pkd": c.cnn_affinity_pkd,
                "composite_docking_score": c.composite_docking_score,
                "chemprop_pIC50": c.chemprop_pIC50,
                "epistemic_uncertainty": c.epistemic_uncertainty,
                "is_out_of_distribution": c.is_out_of_distribution,
                "qed": c.qed,
                "sa_score": c.sa_score,
                "herg_inhibition_prob": c.herg_inhibition_prob,
                "caco2_papp": c.caco2_papp,
                "composite_reward": c.composite_reward,
                "decision": c.decision,
                "failure_reason": c.failure_reason
            }
            for c in candidates
        ]
    }


@router.get("/campaign/{campaign_id}/lineage", summary="Get parent-child lineage DAG graph")
def get_campaign_lineage(campaign_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns graph nodes and edges representing the evolutionary lineage of candidates
    across iterations for interactive visual graph rendering.
    """
    candidates = db.query(CandidateNode).filter(CandidateNode.campaign_id == campaign_id).all()
    if not candidates:
        raise HTTPException(status_code=404, detail=f"No candidates found for campaign '{campaign_id}'")

    nodes = []
    edges = []

    for c in candidates:
        nodes.append({
            "id": c.id,
            "label": f"Iter {c.iteration}: {c.smiles[:18]}...",
            "smiles": c.smiles,
            "iteration": c.iteration,
            "composite_reward": c.composite_reward,
            "vina_affinity": c.vina_affinity_kcal_mol,
            "cnn_score": c.cnn_score,
            "chemprop_pIC50": c.chemprop_pIC50,
            "epistemic_uncertainty": c.epistemic_uncertainty,
            "decision": c.decision,
            "failure_reason": c.failure_reason,
            "qed": c.qed,
            "sa_score": c.sa_score
        })
        if c.parent_id:
            edges.append({
                "source": c.parent_id,
                "target": c.id,
                "label": "derived_from"
            })

    return {
        "campaign_id": campaign_id,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }


@router.get("/failure_taxonomy", summary="Get aggregated failure taxonomy statistics")
def get_failure_taxonomy(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve system-wide failure taxonomy counts across all evaluated candidates."""
    reasons = (
        db.query(CandidateNode.failure_reason, func.count(CandidateNode.id))
        .filter(CandidateNode.failure_reason.isnot(None))
        .group_by(CandidateNode.failure_reason)
        .all()
    )
    taxonomy_counts = {r[0]: r[1] for r in reasons if r[0]}

    total_accepted = db.query(func.count(CandidateNode.id)).filter(CandidateNode.decision == "ACCEPTED").scalar() or 0
    total_active_learning = db.query(func.count(CandidateNode.id)).filter(CandidateNode.decision == "ACTIVE_LEARNING_CANDIDATE").scalar() or 0
    total_rejected = db.query(func.count(CandidateNode.id)).filter(CandidateNode.decision == "REJECTED").scalar() or 0

    return {
        "taxonomy_breakdown": taxonomy_counts,
        "totals": {
            "accepted": total_accepted,
            "active_learning_candidates": total_active_learning,
            "rejected": total_rejected,
            "evaluated_total": total_accepted + total_active_learning + total_rejected
        }
    }
