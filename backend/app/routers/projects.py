from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Union[datetime, str]
    class Config:
        from_attributes = True
        orm_mode = True

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    new_proj = models.Project(name=payload.name, description=payload.description)
    db.add(new_proj)
    db.commit()
    db.refresh(new_proj)
    return new_proj

@router.get("/", response_model=List[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()
