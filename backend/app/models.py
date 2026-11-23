"""SQLAlchemy models for GENESIS backend.
Defines core entities: User, Project, Candidate.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="projects")
    candidates = relationship("Candidate", back_populates="project")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    smiles = Column(String, nullable=False)
    status = Column(String, default="REVIEW")  # MATCH / FAIL / REVIEW
    docking_score = Column(Float)
    qsar_score = Column(Float)
    adme_score = Column(Float)
    toxicity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="candidates")
