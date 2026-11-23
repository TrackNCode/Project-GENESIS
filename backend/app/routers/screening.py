"""
FastAPI Router for Project GENESIS Virtual Screening Pipeline (Phase 5).
Provides endpoints for compound library discovery, cheminformatics pre-filtering,
asynchronous batch docking, real-time progress polling, and multi-parametric hit ranking.
"""

import csv
import io
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..screening.screening_service import (
    CURATED_LIBRARIES,
    start_screening_job,
    get_job_status,
    evaluate_cheminformatics_filters,
    parse_custom_library_text,
)
from rdkit import Chem

router = APIRouter(prefix="/screening", tags=["Virtual Screening Pipeline (Phase 5)"])


class PreFilterRequest(BaseModel):
    library_id: Optional[str] = Field(None, description="Curated library ID", json_schema_extra={"example": "fda_diversity"})
    custom_smiles: Optional[str] = Field(None, description="Custom SMILES lines", json_schema_extra={"example": "CC(=O)Oc1ccccc1C(=O)O Aspirin\nCC(C)Cc1ccc(cc1)C(C)C(=O)O Ibuprofen"})
    apply_lipinski: bool = Field(True, description="Enforce Lipinski Rule of 5")
    apply_veber: bool = Field(True, description="Enforce Veber oral bioavailability criteria")
    apply_pains: bool = Field(True, description="Filter Pan-Assay Interference (PAINS) motifs")
    min_mw: float = Field(100.0, ge=50.0, le=500.0)
    max_mw: float = Field(650.0, ge=200.0, le=1500.0)


class ScreeningStartRequest(BaseModel):
    target: str = Field(..., description="Target receptor PDB ID (e.g. 6LU7, 1ERE, 1IEP, 1M17, 1CX2)", json_schema_extra={"example": "6LU7"})
    library_id: Optional[str] = Field("fda_diversity", description="Curated library ID", json_schema_extra={"example": "fda_diversity"})
    custom_compounds: Optional[str] = Field(None, description="Custom SMILES (one per line)")
    exhaustiveness: int = Field(4, ge=1, le=16, description="Vina search exhaustiveness (4=screening, 8=standard)")
    apply_lipinski: bool = Field(True)
    apply_veber: bool = Field(True)
    apply_pains: bool = Field(True)
    strict_filter: bool = Field(True, description="Skip docking for compounds failing pre-filters")


class SaveCandidateRequest(BaseModel):
    project_id: int = Field(1, description="Target Project ID")
    name: str = Field(..., description="Compound Name")
    smiles: str = Field(..., description="Compound SMILES")
    binding_affinity: float = Field(..., description="Docking Binding Affinity (kcal/mol)")
    ligand_efficiency: Optional[float] = None
    target: str = Field(..., description="Screened Target PDB")


@router.get("/libraries", summary="List available curated screening compound libraries")
def list_screening_libraries():
    """Return all pre-loaded screening libraries with compound counts and classifications."""
    summary = []
    for lib_id, lib in CURATED_LIBRARIES.items():
        summary.append({
            "id": lib["id"],
            "name": lib["name"],
            "category": lib["category"],
            "description": lib["description"],
            "compound_count": len(lib["compounds"]),
            "sample_compounds": [c["name"] for c in lib["compounds"][:4]],
        })
    return summary


@router.post("/prefilter", summary="Fast cheminformatics pre-filtering without docking")
def prefilter_library_endpoint(req: PreFilterRequest):
    """
    Rapidly evaluates library compounds through physicochemical, Lipinski,
    Veber, and PAINS filters to identify compliant drug-like leads.
    """
    compounds = []
    if req.library_id and req.library_id in CURATED_LIBRARIES:
        compounds = CURATED_LIBRARIES[req.library_id]["compounds"]
    elif req.custom_smiles:
        compounds = parse_custom_library_text(req.custom_smiles)
    else:
        raise HTTPException(status_code=400, detail="Must provide library_id or custom_smiles.")

    evaluated = []
    passed_count = 0

    for comp in compounds:
        mol = Chem.MolFromSmiles(comp["smiles"])
        if mol is None:
            evaluated.append({"name": comp["name"], "smiles": comp["smiles"], "passed": False, "violations": ["Invalid SMILES"]})
            continue

        res = evaluate_cheminformatics_filters(
            mol,
            min_mw=req.min_mw,
            max_mw=req.max_mw,
            apply_lipinski=req.apply_lipinski,
            apply_veber=req.apply_veber,
            apply_pains=req.apply_pains,
        )
        if res["passed"]:
            passed_count += 1

        evaluated.append({
            "name": comp["name"],
            "smiles": comp["smiles"],
            "class": comp.get("class", "Unspecified"),
            **res,
        })

    return {
        "total_compounds": len(compounds),
        "passed_count": passed_count,
        "pass_rate_pct": round((passed_count / max(1, len(compounds))) * 100, 1),
        "results": evaluated,
    }


@router.post("/start", summary="Launch asynchronous virtual screening pipeline")
def start_screening_pipeline(req: ScreeningStartRequest):
    """
    Initiate parallel virtual screening job against target receptor:
    - Filters compounds using Rule-of-5 / Veber / PAINS.
    - Docks compliant molecules with AutoDock Vina across logical cores.
    - Computes binding affinities, ligand efficiencies, and composite scores.
    """
    try:
        filters = {
            "lipinski": req.apply_lipinski,
            "veber": req.apply_veber,
            "pains": req.apply_pains,
            "strict_filter": req.strict_filter,
        }
        job_id = start_screening_job(
            target=req.target,
            library_id=req.library_id,
            custom_compounds_text=req.custom_compounds,
            exhaustiveness=req.exhaustiveness,
            filters=filters,
        )
        return {
            "status": "launched",
            "job_id": job_id,
            "target": req.target.upper(),
            "message": "Screening job successfully started in background.",
            "poll_url": f"/screening/status/{job_id}",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{job_id}", summary="Check screening job progress & metrics")
def get_screening_job_status(job_id: str):
    """Poll live progress, current compound being docked, and completion state."""
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Screening job '{job_id}' not found.")

    return {
        "job_id": job["job_id"],
        "target": job["target"],
        "target_name": job.get("target_name"),
        "library_name": job.get("library_name"),
        "status": job["status"],
        "progress": job["progress"],
        "docked_count": job.get("docked_count", 0),
        "filtered_count": job.get("filtered_count", 0),
        "failed_count": job.get("failed_count", 0),
        "best_affinity": job.get("best_affinity"),
        "top_hit": job.get("top_hit"),
        "duration_sec": job.get("duration_sec"),
    }


@router.get("/results/{job_id}", summary="Retrieve ranked virtual screening hits")
def get_screening_results(
    job_id: str,
    sort_by: str = Query("affinity", pattern="^(affinity|ligand_efficiency|composite_score)$")
):
    """
    Fetch comprehensive ranked screening results table with sorting options.
    """
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Screening job '{job_id}' not found.")

    results = list(job.get("results", []))
    docked = [r for r in results if r["status"] == "docked"]
    non_docked = [r for r in results if r["status"] != "docked"]

    if sort_by == "affinity":
        docked.sort(key=lambda x: x["binding_affinity_kcal_mol"])
    elif sort_by == "ligand_efficiency":
        docked.sort(key=lambda x: x["ligand_efficiency"], reverse=True)
    elif sort_by == "composite_score":
        docked.sort(key=lambda x: x["composite_score"], reverse=True)

    # Re-rank
    for i, h in enumerate(docked):
        h["rank"] = i + 1

    return {
        "job_id": job["job_id"],
        "target": job["target"],
        "target_name": job.get("target_name"),
        "library_name": job.get("library_name"),
        "status": job["status"],
        "total_screened": len(results),
        "docked_count": len(docked),
        "best_affinity": docked[0]["binding_affinity_kcal_mol"] if docked else None,
        "hits": docked,
        "ranked_hits": docked,
        "filtered_or_failed": non_docked,
    }


@router.post("/save_candidate", summary="Save screened hit to Project Candidates Database")
def save_screened_candidate(req: SaveCandidateRequest, db: Session = Depends(get_db)):
    """Save an identified screening hit into the persistent Candidates database table."""
    # Ensure tables exist
    models.Base.metadata.create_all(bind=db.get_bind())

    # Ensure project exists (or default to 1)
    proj = db.query(models.Project).filter(models.Project.id == req.project_id).first()
    if not proj:
        # Create default project if none exists
        proj = models.Project(id=req.project_id, name="Virtual Screening Discovery", description="Auto-created project for screening leads")
        db.add(proj)
        db.commit()

    candidate = models.Candidate(
        project_id=req.project_id,
        smiles=req.smiles,
        status="MATCH",
        docking_score=req.binding_affinity,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "status": "saved",
        "candidate_id": candidate.id,
        "name": req.name,
        "smiles": req.smiles,
        "docking_score": req.binding_affinity,
        "project_id": req.project_id,
    }


@router.get("/export/{job_id}", summary="Download virtual screening report (CSV / JSON)")
def export_screening_report(job_id: str, format: str = Query("csv", pattern="^(csv|json)$")):
    """Export screening results as structured CSV spreadsheet or JSON dataset."""
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Screening job '{job_id}' not found.")

    docked = [r for r in job.get("results", []) if r["status"] == "docked"]

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Rank", "Compound Name", "Class", "SMILES", "Target",
            "Affinity (kcal/mol)", "Ligand Efficiency (LE)", "Estimated pKi",
            "Lipophilic Efficiency (LLE)", "Composite Score", "MW", "LogP",
            "TPSA", "Rotatable Bonds", "Lipinski Pass", "PAINS Alerts"
        ])
        for h in docked:
            writer.writerow([
                h.get("rank"),
                h.get("name"),
                h.get("class"),
                h.get("smiles"),
                job["target"],
                h.get("binding_affinity_kcal_mol"),
                h.get("ligand_efficiency"),
                h.get("estimated_pki"),
                h.get("lipophilic_efficiency_lle"),
                h.get("composite_score"),
                h.get("mw"),
                h.get("logp"),
                h.get("tpsa"),
                h.get("rotatable_bonds"),
                h.get("lipinski_pass"),
                "; ".join(h.get("pains_alerts", []))
            ])

        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="screening_{job_id}_{job["target"]}.csv"'}
        )

    return {"job_id": job_id, "target": job["target"], "hits": docked, "ranked_hits": docked}
