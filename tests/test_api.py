from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_job_generates_certificates_and_can_download():
    response = client.post("/jobs", json={
        "event_name": "Test Workshop",
        "recipients": [
            {"name": "Anu", "email": "anu@example.com"},
            {"name": "Ravi", "email": "ravi@example.com"}
        ]
    })
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job_response = client.get(f"/jobs/{job_id}")
    assert job_response.status_code == 200
    data = job_response.json()
    assert data["total_count"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0
    assert data["status"] == "completed"
    assert all(r["status"] == "success" for r in data["recipients"])

    certificate_id = data["recipients"][0]["id"]
    download = client.get(f"/certificates/{certificate_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")

def test_invalid_email_is_rejected():
    response = client.post("/jobs", json={
        "event_name": "Test Workshop",
        "recipients": [{"name": "Anu", "email": "not-an-email"}]
    })
    assert response.status_code == 422

def test_job_not_found():
    response = client.get("/jobs/999999")
    assert response.status_code == 404

def test_empty_recipients_are_rejected():
    response = client.post("/jobs", json={
        "event_name": "Test Workshop",
        "recipients": []
    })
    assert response.status_code == 422


def test_individual_certificate_failure_does_not_stop_job(monkeypatch):
    import app.main as main_module

    original_generator = main_module.generate_certificate

    def fail_for_ravi(name, event_name, certificate_id):
        if name == "Ravi":
            raise RuntimeError("Simulated PDF generation failure")
        return original_generator(name, event_name, certificate_id)

    monkeypatch.setattr(main_module, "generate_certificate", fail_for_ravi)
    response = client.post("/jobs", json={
        "event_name": "Failure Handling Workshop",
        "recipients": [
            {"name": "Anu", "email": "anu@example.com"},
            {"name": "Ravi", "email": "ravi@example.com"}
        ]
    })
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    result = client.get(f"/jobs/{job_id}").json()
    assert result["status"] == "completed_with_errors"
    assert result["success_count"] == 1
    assert result["failure_count"] == 1
    statuses = {r["name"]: r["status"] for r in result["recipients"]}
    assert statuses["Anu"] == "success"
    assert statuses["Ravi"] == "failed"
