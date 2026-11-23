"""
models.py
SQLAlchemy schema for Project GENESIS Iterative Learning Engine & Lineage Tracking (Milestone 5).
Tracks candidate lineage trees, generation iterations, failure classifications, and Pareto metrics.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class DiscoveryCampaign(Base):
    __tablename__ = "discovery_campaigns"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    target = Column(String(32), nullable=False, default="6LU7")
    target_name = Column(String(128), nullable=True)
    total_iterations = Column(Integer, default=2)
    status = Column(String(32), default="RUNNING") # RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    summary_metrics = Column(JSON, nullable=True)

    candidates = relationship("CandidateNode", back_populates="campaign", cascade="all, delete-orphan")
    iterations = relationship("IterationSummary", back_populates="campaign", cascade="all, delete-orphan")


class CandidateNode(Base):
    __tablename__ = "candidate_nodes"

    id = Column(String(64), primary_key=True, index=True)
    campaign_id = Column(String(64), ForeignKey("discovery_campaigns.id"), nullable=False, index=True)
    iteration = Column(Integer, nullable=False, default=1)
    parent_id = Column(String(64), nullable=True) # Lineage parent candidate ID
    
    # Chemistry
    smiles = Column(Text, nullable=False)
    inchikey = Column(String(64), nullable=True, index=True)
    bemis_murcko_scaffold = Column(Text, nullable=True)
    molecular_weight = Column(Float, nullable=True)
    logP = Column(Float, nullable=True)
    
    # Stage 3: Docking (Vina + GNINA 3D-CNN)
    vina_affinity_kcal_mol = Column(Float, nullable=True)
    cnn_score = Column(Float, nullable=True)
    cnn_affinity_pkd = Column(Float, nullable=True)
    composite_docking_score = Column(Float, nullable=True)
    
    # Stage 4: Predict (Chemprop 2.x Evidential D-MPNN)
    chemprop_pIC50 = Column(Float, nullable=True)
    epistemic_uncertainty = Column(Float, nullable=True)
    is_out_of_distribution = Column(Boolean, default=False)
    
    # Stage 5: ADMET & Drug-likeness
    qed = Column(Float, nullable=True)
    sa_score = Column(Float, nullable=True)
    herg_inhibition_prob = Column(Float, nullable=True)
    caco2_papp = Column(Float, nullable=True)
    
    # Stage 6: Multi-Objective Evaluation
    composite_reward = Column(Float, default=0.0)
    decision = Column(String(32), default="ACCEPTED") # ACCEPTED, REJECTED, ACTIVE_LEARNING_CANDIDATE
    failure_reason = Column(String(64), nullable=True) # e.g. POOR_DOCKING, HIGH_UNCERTAINTY, CARDIOTOX
    
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("DiscoveryCampaign", back_populates="candidates")


class IterationSummary(Base):
    __tablename__ = "iteration_summaries"

    id = Column(String(64), primary_key=True, index=True)
    campaign_id = Column(String(64), ForeignKey("discovery_campaigns.id"), nullable=False, index=True)
    iteration = Column(Integer, nullable=False)
    
    generated_count = Column(Integer, default=0)
    screened_count = Column(Integer, default=0)
    docked_count = Column(Integer, default=0)
    accepted_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    
    mean_reward = Column(Float, default=0.0)
    best_reward = Column(Float, default=0.0)
    best_candidate_id = Column(String(64), nullable=True)
    failure_taxonomy = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("DiscoveryCampaign", back_populates="iterations")
