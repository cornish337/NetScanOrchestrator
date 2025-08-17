import pytest
from unittest.mock import patch

def test_health_check(client_with_db):
    response = client_with_db.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("web_api.app.asyncio.create_task")
def test_start_scan(mock_create_task, client_with_db):
    response = client_with_db.post(
        "/api/scans",
        json={"targets": ["127.0.0.1"], "nmap_options": "-sT"},
    )
    assert response.status_code == 202
    assert "scan_id" in response.json()
    mock_create_task.assert_called_once()

def test_get_scan_status_not_found(client_with_db):
    response = client_with_db.get("/api/scans/999")
    assert response.status_code == 404
