import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

app_module = importlib.import_module("app.app")
app = app_module.app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"
    assert response.json["service"] == "Linux Network Monitor"


def test_api_report_when_report_is_missing(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        app_module, "REPORT_FILE", tmp_path / "missing_report.json"
    )

    response = client.get("/api/report")

    assert response.status_code == 200
    assert response.json["overall_status"] == "unknown"
    assert "No monitoring report found." in response.json["alerts"]


def test_api_report_reads_valid_json(client, tmp_path, monkeypatch):
    report_file = tmp_path / "monitoring_report.json"
    expected_report = {
        "overall_status": "healthy",
        "system": {"cpu_usage": 10},
        "network": {},
        "alerts": [],
    }
    report_file.write_text(json.dumps(expected_report), encoding="utf-8")
    monkeypatch.setattr(app_module, "REPORT_FILE", report_file)

    response = client.get("/api/report")

    assert response.status_code == 200
    assert response.json == expected_report


def test_refresh_report_success(client, monkeypatch):
    expected_report = {
        "overall_status": "healthy",
        "system": {},
        "network": {},
        "alerts": [],
    }
    monkeypatch.setattr(app_module, "read_report", lambda: expected_report)
    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout="", stderr=""
        ),
    )

    response = client.post("/api/refresh")

    assert response.status_code == 200
    assert response.json == expected_report


def test_refresh_report_failure(client, monkeypatch):
    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1, stdout="", stderr="Monitoring failed"
        ),
    )

    response = client.post("/api/refresh")

    assert response.status_code == 500
    assert "Monitoring failed" in response.json["error"]


def test_dashboard_loads(client):
    response = client.get("/")

    assert response.status_code == 200

