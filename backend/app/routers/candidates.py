from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime

router = APIRouter(prefix="/candidates", tags=["Candidates"])

class CandidateCreate(BaseModel):
    project_id: int
    smiles: str
    status: Optional[str] = "REVIEW"

class CandidateRead(BaseModel):
    id: int
    project_id: int
    smiles: str
    status: str
    docking_score: Optional[float] = None
    qsar_score: Optional[float] = None
    adme_score: Optional[float] = None
    toxicity_score: Optional[float] = None
    created_at: Union[datetime, str]

    class Config:
        from_attributes = True
        orm_mode = True

@router.post("/", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db)):
    # Ensure project exists
    proj = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    cand = models.Candidate(
        project_id=payload.project_id,
        smiles=payload.smiles,
        status=payload.status,
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)
    return cand

@router.get("/", response_model=List[CandidateRead])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(models.Candidate).all()

@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    cand = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand
