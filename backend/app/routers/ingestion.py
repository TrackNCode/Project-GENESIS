"""
FastAPI Router for Project GENESIS Scientific Data Ingestion & Governance Subsystem (Stage 2).
Exposes endpoints for ChEMBL experimental activities, Open Targets tractability,
TDC benchmark ingestion, and leak-free scaffold split verification.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..ingestion.chembl_client import ChEMBLIngestionClient
from ..ingestion.opentargets_client import OpenTargetsClient
from ..ingestion.tdc_client import TDCClient
from ..ingestion.data_governance import DataGovernanceEngine
from ..ingestion.datamol_adapter import DatamolAdapter

router = APIRouter(prefix="/ingestion", tags=["Scientific Data Foundation & Governance (Stage 2)"])


class ChEMBLQueryRequest(BaseModel):
    target_chembl_id: str = Field(..., description="Target ChEMBL ID (e.g. CHEMBL4296597 for Mpro, CHEMBL1862 for ABL)", json_schema_extra={"example": "CHEMBL4296597"})
    activity_type: str = Field("IC50", description="Activity standard type: IC50, Ki, Kd, EC50")
    limit: int = Field(25, ge=5, le=100)


class OpenTargetsQueryRequest(BaseModel):
    ensembl_id: str = Field(..., description="Target Ensembl Gene ID (e.g. ENSG00000091831 for ESR1, ENSG00000148400 for ABL1)", json_schema_extra={"example": "ENSG00000091831"})


class TDCLoadRequest(BaseModel):
    dataset_id: str = Field("caco2_wang", description="TDC dataset identifier: caco2_wang, herg_karim, mpro_postera")
    split_type: str = Field("scaffold", description="Data partitioning: scaffold or random")


class AuditRecordRequest(BaseModel):
    record: Dict[str, Any] = Field(..., description="Full dataset record including SMILES and provenance")


@router.get("/sources", summary="List available scientific data sources and active connectors")
def list_scientific_sources():
    """Return available public connectors: ChEMBL REST, Open Targets GraphQL, and TDC."""
    return {
        "status": "online",
        "sources": [
            {
                "id": "chembl",
                "name": "EMBL-EBI ChEMBL Bioactivity Database",
                "protocol": "REST (ebi.ac.uk/chembl/api/data)",
                "data_class": "GROUND_TRUTH_EXPERIMENTAL",
                "default_targets": ChEMBLIngestionClient.TARGET_PRESETS,
            },
            {
                "id": "opentargets",
                "name": "Open Targets Platform",
                "protocol": "GraphQL (api.platform.opentargets.org)",
                "data_class": "GROUND_TRUTH_EXPERIMENTAL",
                "default_targets": OpenTargetsClient.ENSEMBL_TARGET_MAP,
            },
            {
                "id": "tdc",
                "name": "Therapeutics Data Commons (TDC)",
                "protocol": "Standardized ML Benchmark Feeds",
                "data_class": "GROUND_TRUTH_EXPERIMENTAL",
                "available_benchmarks": TDCClient.list_benchmarks(),
            }
        ]
    }


@router.post("/chembl/query_target", summary="Retrieve ChEMBL experimental bioactivity records")
def query_chembl_target_endpoint(req: ChEMBLQueryRequest):
    """
    Fetch experimental binding activities from ChEMBL, convert units to standard pIC50,
    and attach full provenance manifests.
    """
    try:
        return ChEMBLIngestionClient.fetch_target_activities(
            target_chembl_id=req.target_chembl_id,
            activity_type=req.activity_type,
            limit=req.limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opentargets/target_tractability", summary="Fetch Open Targets tractability & safety report")
def query_opentargets_endpoint(req: OpenTargetsQueryRequest):
    """
    Fetch target validation, small-molecule druggability categories,
    and known safety liabilities from Open Targets GraphQL API.
    """
    try:
        data = OpenTargetsClient.query_target(req.ensembl_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tdc/load_benchmark", summary="Load standardized TDC dataset with leak-free scaffold splits")
def load_tdc_benchmark_endpoint(req: TDCLoadRequest):
    """
    Loads curated TDC benchmark dataset with Bemis-Murcko scaffold partitioning
    guaranteeing zero test data contamination.
    """
    try:
        dataset = TDCClient.load_dataset(req.dataset_id, split_type=req.split_type)
        leak_audit = DataGovernanceEngine.verify_split_leak_free(dataset["splits"])
        dataset["leak_free_audit"] = leak_audit
        return dataset
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/audit/validate_record", summary="Audit dataset record for governance & provenance compliance")
def audit_record_endpoint(req: AuditRecordRequest):
    """Verify record compliance against scientific data governance rules."""
    return DataGovernanceEngine.audit_record(req.record)
