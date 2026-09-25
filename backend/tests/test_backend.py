"""
Backend tests for FastAPI app, discovery, analysis, linking, and reconstruction endpoints.
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
    assert "Not legally admissible" in data["disclaimer"]


def test_deferred_stages_return_501():
    """Verify export endpoints scheduled for Phase 7 return HTTP 501."""
    stages = [
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


def test_pipeline_stages_live():
    """Test full Phase 1-5 pipeline through API client."""
    # 1. Register sample dataset
    r_disc = client.post("/api/v1/discovery/sample")
    assert r_disc.status_code in (200, 201)
    ev_id = r_disc.json()["id"]

    # 2. Analyze fragments
    r_ana = client.post("/api/v1/analysis/fragments", json={"evidence_id": ev_id})
    assert r_ana.status_code == 200
    ana_data = r_ana.json()
    assert ana_data["fragment_count"] > 0

    # 3. Generate candidate chains
    r_cand = client.post("/api/v1/reconstruction/candidates", json={"evidence_id": ev_id})
    assert r_cand.status_code == 200
    candidates = r_cand.json()
    assert len(candidates) > 0

    # 4. Check candidates list
    r_list = client.get(f"/api/v1/reconstruction/candidates?evidence_id={ev_id}")
    assert r_list.status_code == 200
    assert r_list.json()["total"] > 0
