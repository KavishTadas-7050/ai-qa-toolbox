"""Smoke tests for Day 11 — stats endpoint, dashboard, and metrics."""

import json
import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")


def test_load_stats_empty(monkeypatch):
    """load_stats returns zero totals when log file does not exist."""
    from api import stats as stats_module
    from pathlib import Path
    monkeypatch.setattr(stats_module, "LOG_PATH", Path("nonexistent_file.jsonl"))
    result = stats_module.load_stats()
    assert result["total"] == 0
    assert result["pass_rate"] == 0.0
    assert result["recent"] == []


def test_load_stats_with_data(monkeypatch):
    """load_stats correctly parses JSONL entries."""
    import tempfile
    import pathlib
    from api import stats as stats_module

    log_file = pathlib.Path(tempfile.mktemp(suffix=".jsonl"))
    entries = [
        {"run_id": "1", "category": "BUG", "confidence": 0.9,
         "fix_title": "Fix A", "sandbox_passed": True, "pr_url": None},
        {"run_id": "2", "category": "FLAKY", "confidence": 0.7,
         "fix_title": "", "sandbox_passed": False, "pr_url": None},
        {"run_id": "3", "category": "BUG", "confidence": 0.8,
         "fix_title": "Fix C", "sandbox_passed": True, "pr_url": None},
    ]
    with open(log_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    monkeypatch.setattr(stats_module, "LOG_PATH", log_file)
    result = stats_module.load_stats()

    assert result["total"] == 3
    assert result["by_category"]["BUG"] == 2
    assert result["by_category"]["FLAKY"] == 1
    assert result["pass_rate"] == round(2 / 3 * 100, 1)
    assert len(result["recent"]) == 3
    log_file.unlink(missing_ok=True)


def test_stats_endpoint():
    """GET /stats returns valid JSON with expected fields."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_category" in data
    assert "pass_rate" in data
    assert "recent" in data


def test_dashboard_endpoint():
    """GET /dashboard returns 200 HTML containing expected text."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Self-Healing CI Agent" in response.text
    assert "Total Runs Analysed" in response.text


def test_metrics_endpoint():
    """GET /metrics returns Prometheus-formatted plain text."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "ci_agent_total_runs" in response.text
    assert "ci_agent_fix_pass_rate" in response.text
    assert "# HELP" in response.text
    assert "# TYPE" in response.text
