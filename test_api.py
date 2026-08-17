import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database import init_db

# Initialize database before testing
init_db()
client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_list_opportunities():
    resp = client.get("/api/opportunities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 6

def test_filter_opportunities_by_federal():
    resp = client.get("/api/opportunities?source_type=FEDERAL")
    assert resp.status_code == 200
    data = resp.json()
    assert all(o["source_type"] == "FEDERAL" for o in data)

def test_filter_opportunities_by_sled():
    resp = client.get("/api/opportunities?source_type=SLED")
    assert resp.status_code == 200
    data = resp.json()
    assert all(o["source_type"] == "SLED" for o in data)

def test_opportunity_stats():
    resp = client.get("/api/opportunities/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_rfps" in stats
    assert "federal_rfps" in stats
    assert "sled_rfps" in stats
    assert "avg_fit_score" in stats

def test_profiles_endpoints():
    # List all profiles
    resp = client.get("/api/profile/all")
    assert resp.status_code == 200
    profiles = resp.json()
    assert len(profiles) >= 2

    # Switch to PIScaleX
    resp_switch = client.post("/api/profile/switch/profile_piscalex")
    assert resp_switch.status_code == 200
    assert resp_switch.json()["active_profile"]["company_name"] == "PIScaleX"

    # Switch back to A11N Holdings LLC
    resp_switch2 = client.post("/api/profile/switch/profile_a11n")
    assert resp_switch2.status_code == 200
    assert resp_switch2.json()["active_profile"]["company_name"] == "A11N Holdings LLC"

def test_opportunity_detail_and_status_update():
    opps = client.get("/api/opportunities").json()
    assert len(opps) > 0
    opp_id = opps[0]["id"]

    # Get single detail
    resp = client.get(f"/api/opportunities/{opp_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == opp_id

    # Update status to BID
    resp_status = client.patch(f"/api/opportunities/{opp_id}/status?status=BID")
    assert resp_status.status_code == 200
    assert resp_status.json()["new_status"] == "BID"

    # Check updated detail
    resp_after = client.get(f"/api/opportunities/{opp_id}")
    assert resp_after.json()["status"] == "BID"

def test_export_endpoints():
    # Test CSV export
    resp_csv = client.get("/api/opportunities/export?format=csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "Solicitation Number" in resp_csv.text

    # Test JSON export
    resp_json = client.get("/api/opportunities/export?format=json")
    assert resp_json.status_code == 200
    assert isinstance(resp_json.json(), list)

def test_ai_qa_and_reanalysis():
    opps = client.get("/api/opportunities").json()
    opp_id = opps[0]["id"]

    # Test asking a question
    resp_ask = client.post(
        f"/api/ai/ask/{opp_id}",
        json={"question": "What is the primary deadline and key requirements?"}
    )
    assert resp_ask.status_code == 200
    data = resp_ask.json()
    assert "answer" in data
    assert len(data["answer"]) > 10

    # Test re-analyzing opportunity
    resp_reanalyze = client.post(f"/api/ai/reanalyze/{opp_id}")
    assert resp_reanalyze.status_code == 200
    assert "fit_score" in resp_reanalyze.json()

def test_rescore_pipeline():
    resp = client.post("/api/profile/rescore-pipeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rescored"] >= 6

def test_capture_run_and_logs():
    # Run a capture
    resp_run = client.post(
        "/api/capture/run",
        json={"sources": ["TX_SMARTBUY"], "due_window_days": 60}
    )
    assert resp_run.status_code == 200
    assert resp_run.json()["status"] == "COMPLETED"

    # Check logs
    resp_logs = client.get("/api/capture/logs")
    assert resp_logs.status_code == 200
    assert len(resp_logs.json()) >= 1

def test_capability_deck_upload_text():
    sample_deck = """
    Apex NextGen Defense AI LLC
    Core Capabilities: Specializing in Edge Computer Vision, Autonomous UAV swarm control,
    tactical sensor fusion, and zero-trust cloud orchestration for defense agencies.
    Certifications: CMMC Level 2, Secret Facility Clearance, ISO 9001.
    Target NAICS: 541512, 541511, 541330.
    """
    resp = client.post(
        "/api/profile/upload-deck",
        data={"raw_text": sample_deck}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "profile_id" in data
    assert "Apex NextGen" in data["extracted_profile"]["company_name"] or "GovTech" in data["extracted_profile"]["company_name"] or "Uploaded" in data["extracted_profile"]["company_name"]

