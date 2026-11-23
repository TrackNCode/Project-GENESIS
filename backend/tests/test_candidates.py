import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.database import SessionLocal, engine

@pytest.fixture(scope="function")
def db_session():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    # create a project to associate candidate
    session = SessionLocal()
    proj = models.Project(name="Proj1", description="test")
    session.add(proj)
    session.commit()
    session.refresh(proj)
    yield session, proj.id
    session.close()

client = TestClient(app)

def test_create_and_get_candidate(db_session):
    session, proj_id = db_session
    # create candidate
    payload = {"project_id": proj_id, "smiles": "CCO", "status": "REVIEW"}
    response = client.post("/candidates/", json=payload)
    assert response.status_code == 201
    cand = response.json()
    assert cand["smiles"] == "CCO"
    cand_id = cand["id"]

    # get candidate
    response = client.get(f"/candidates/{cand_id}")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["id"] == cand_id
    assert fetched["project_id"] == proj_id

def test_list_candidates(db_session):
    session, proj_id = db_session
    # create two candidates
    client.post("/candidates/", json={"project_id": proj_id, "smiles": "CCO"})
    client.post("/candidates/", json={"project_id": proj_id, "smiles": "CCC"})
    response = client.get("/candidates/")
    assert response.status_code == 200
    lst = response.json()
    assert len(lst) >= 2
