import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_vector_search_query_params():
    # Use query parameters
    response = client.post("/knowledge/search", params={"query": "drug discovery", "k": 5})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_vector_search_json_body():
    payload = {"query": "drug discovery", "k": 5}
    response = client.post("/knowledge/search", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_ingest_documents():
    docs = [{"id": "test1", "text": "sample text", "metadata": {"source": "unit"}}]
    response = client.post("/knowledge/ingest", json=docs)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["added"] == len(docs)
