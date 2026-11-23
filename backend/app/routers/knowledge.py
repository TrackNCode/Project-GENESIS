"""Knowledge API router.
Provides endpoints to query the Neo4j graph and to perform vector similarity search.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any
from ..knowledge.neo4j_client import Neo4jClient
from ..knowledge.vector_store import VectorStore, load_store, save_store

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

class SearchRequest(BaseModel):
    query: str
    k: int = 5

class GraphQueryRequest(BaseModel):
    cypher: str
    parameters: Dict[str, Any] = {}


neo4j_client = Neo4jClient()
vector_store = load_store()

@router.post("/graph/query")
def graph_query(request: GraphQueryRequest = Body(...)) -> List[Dict[str, Any]]:
    """Execute a Cypher query against Neo4j.
    Returns a list of record dicts. If Neo4j is unavailable, returns an empty list.
    """
    try:
        result = neo4j_client.run_query(request.cypher, request.parameters or {})
        return result
    except Exception as e:
        # If driver not initialized, log and return empty list instead of 400 error
        print(f"Neo4j query failed: {e}")
        return []

def graph_query(request: GraphQueryRequest = Body(...)) -> List[Dict[str, Any]]:
    """Execute a Cypher query against Neo4j.
    Expects a JSON body with `cypher` and optional `parameters`.
    """
    try:
        result = neo4j_client.run_query(request.cypher, request.parameters or {})
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/search")
def vector_search(request: SearchRequest = Body(None), query: str = None, k: int = 5) -> List[Dict[str, Any]]:
    """Accept either JSON body or query parameters for search.
    If a JSON body is provided, its fields take precedence.
    """
    # Determine actual parameters
    if request is not None:
        q = request.query
        kk = request.k
    else:
        q = query
        kk = k
    try:
        results = vector_store.search(q, kk)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
def ingest_documents(docs: List[Dict[str, Any]]):
    """Ingest docs into vector store and Neo4j.
    Returns status and count of added documents.
    """
    try:
        # Add to vector store and persist
        vector_store.add_documents(docs)
        save_store(vector_store)
        # Create Neo4j Publication nodes
        for doc in docs:
            neo4j_client.create_publication(doc)
        return {"status": "ok", "added": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
