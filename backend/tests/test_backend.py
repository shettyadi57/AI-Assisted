"""
Backend tests for FastAPI app and SQLite schema migrations.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint returns 200 OK and contains mandatory disclaimer."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["current_phase"] == 0
    assert "Not legally admissible" in data["disclaimer"]


def test_pipeline_skeletons_return_501():
    """Verify all deferred pipeline stages return HTTP 501 with phase description."""
    stages = [
        ("/api/v1/discovery/ingest", "POST", 1, "discovery"),
        ("/api/v1/discovery/evidence", "GET", 1, "discovery"),
        ("/api/v1/analysis/fragments", "POST", 2, "analysis"),
        ("/api/v1/analysis/fragments/test-frag", "GET", 2, "analysis"),
        ("/api/v1/linking/score", "POST", 3, "linking"),
        ("/api/v1/linking/relationships", "GET", 3, "linking"),
        ("/api/v1/reconstruction/candidates", "POST", 4, "reconstruction"),
        ("/api/v1/reconstruction/candidates/test-cand", "GET", 4, "reconstruction"),
        ("/api/v1/export/provenance", "POST", 7, "export"),
        ("/api/v1/export/reports/test-rep", "GET", 7, "export"),
    ]
    for endpoint, method, expected_phase, stage in stages:
        if method == "POST":
            res = client.post(endpoint)
        else:
            res = client.get(endpoint)
        assert res.status_code == 501, f"Expected 501 for {endpoint}, got {res.status_code}"
        body = res.json()
        assert body["status_code"] == 501
        assert body["stage"] == stage
        assert f"Phase {expected_phase}" in body["phase"]
