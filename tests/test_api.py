"""
Tests — FastAPI Endpoints (integration)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_postforge.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    res = client.get("/health/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["app"] == "PostForge"


def test_list_jobs_empty(client):
    res = client.get("/jobs/")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_create_job_text(client):
    res = client.post("/jobs/", data={
        "input_type": "text",
        "input_text": "Lanzamos nuestro nuevo servicio de automatización",
        "brand_id": "confluex",
    })
    # Job creation returns 201, actual processing is async
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "pending"
    assert data["brand_id"] == "confluex"


def test_get_job_not_found(client):
    res = client.get("/jobs/nonexistent-id")
    assert res.status_code == 404


def test_list_brands_empty(client):
    res = client.get("/brands/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
