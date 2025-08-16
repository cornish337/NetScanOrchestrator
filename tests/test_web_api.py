import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from web_api.app import app

def test_health_check():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("web_api.app.asyncio.create_task")
def test_start_scan(mock_create_task, test_db_session):
    client = TestClient(app)
    response = client.post(
        "/api/scans",
        json={"targets": ["127.0.0.1"], "nmap_options": "-sT"},
    )
    assert response.status_code == 202
    assert "scan_id" in response.json()
    mock_create_task.assert_called_once()

@patch("web_api.app.db_repo")
def test_get_scan_status(mock_db_repo, test_db_session):
    client = TestClient(app)
    # Mock the return values of the database functions
    mock_scan_run = MagicMock()
    mock_scan_run.status.name = "COMPLETED"
    mock_db_repo.get_scan_run.return_value = mock_scan_run
    mock_db_repo.list_jobs_for_scan_run.return_value = []

    scan_id = "1"
    response = client.get(f"/api/scans/{scan_id}")
    assert response.status_code == 200
    response_data = response.json()["data"]
    assert response_data["scan_id"] == scan_id
    assert response_data["status"] == "COMPLETED"
