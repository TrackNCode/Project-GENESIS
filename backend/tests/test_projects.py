import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.database import SessionLocal, engine
from sqlalchemy.orm import Session

# Ensure a fresh DB for each test run
@pytest.fixture(scope="function")
def db_session():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

client = TestClient(app)

def test_create_and_list_project(db_session: Session):
    # Create a project
    response = client.post("/projects/", json={"name": "Test Project", "description": "Demo"})
    assert response.status_code == 201
    proj = response.json()
    assert proj["name"] == "Test Project"

    # List projects
    response = client.get("/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert any(p["id"] == proj["id"] for p in projects)
