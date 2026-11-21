import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_frontend_root_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "html" in response.headers.get("content-type", "")

def test_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "verified_schemes_count" in data
    assert "extracted_schemes_count" in data

def test_admin_auth_endpoint():
    # Without password -> 401
    res_unauth = client.get("/api/admin/verify-auth")
    assert res_unauth.status_code == 401

    # With correct password -> 200
    res_auth = client.get(
        "/api/admin/verify-auth",
        headers={"X-Admin-Password": settings.ADMIN_PASSWORD}
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["authenticated"] is True

def test_eligibility_endpoint_with_sample_farmer():
    payload = {
        "profile": {
            "age": 35,
            "occupation": "farmer",
            "annual_income": 80000.0,
            "owns_land": True,
            "land_acres": 2.5,
            "state": "Karnataka"
        },
        "language": "en"
    }
    response = client.post("/api/eligibility", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ranked_schemes" in data
    assert "total_evaluated" in data
