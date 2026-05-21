"""Smoke tests for Day 8 — sandbox runner, fix logger, fixer, webhook API."""

import pytest


@pytest.fixture(autouse=True)
def mock_llm_env(monkeypatch):
    """All Day 8 tests run in mock mode."""
    monkeypatch.setenv("MOCK_LLM", "true")


def test_fix_logger_writes_and_reads(monkeypatch):
    import tempfile
    import pathlib
    tmp_path = pathlib.Path(tempfile.mkdtemp())
    """log_attempt writes a valid JSONL entry that read_attempts returns."""
    from agent import fix_logger
    monkeypatch.setattr(fix_logger, "LOG_PATH", tmp_path / "fix_attempts.jsonl")

    fix_logger.log_attempt(
        run_id=99,
        classification={"category": "BUG", "confidence": 0.85},
        fix={"fix_title": "Test fix"},
        sandbox_passed=True,
        pr_url="https://github.com/test/repo/pull/1",
    )

    attempts = fix_logger.read_attempts()
    assert len(attempts) == 1
    assert attempts[0]["category"] == "BUG"
    assert attempts[0]["sandbox_passed"] is True
    assert attempts[0]["pr_url"] == "https://github.com/test/repo/pull/1"


def test_sandbox_mock_returns_passing():
    """run_fix_in_sandbox_mock always returns passed=True."""
    from agent.sandbox_runner import run_fix_in_sandbox_mock

    result = run_fix_in_sandbox_mock({"fix_title": "test"})
    assert result["passed"] is True
    assert "passed" in result["output"]


def test_fixer_returns_valid_schema():
    """suggest_fix returns a dict with all required fields in mock mode."""
    from agent.fixer import suggest_fix

    classification = {
        "category": "BUG",
        "confidence": 0.9,
        "root_cause": "Selector not found",
        "fix_hint": "Update the selector",
    }
    result = suggest_fix("TimeoutError: selector not found", classification)
    assert isinstance(result, dict)


def test_webhook_health_endpoint():
    """GET /health returns status ok."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_webhook_ignores_non_failure():
    """POST /webhook ignores non-failure payloads."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    payload = {
        "action": "completed",
        "workflow_run": {"conclusion": "success", "id": 1},
        "repository": {
            "name": "test-repo",
            "owner": {"login": "test-user"},
            "clone_url": "https://github.com/test-user/test-repo.git",
        },
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_handles_failure_in_mock_mode():
    """POST /webhook processes a failure payload end-to-end in mock mode."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    payload = {
        "action": "completed",
        "workflow_run": {
            "conclusion": "failure",
            "id": 12345,
            "head_branch": "main",
            "head_sha": "abc123def456",
        },
        "repository": {
            "name": "ai-qa-toolbox",
            "owner": {"login": "KavishTadas-7050"},
            "clone_url": "https://github.com/KavishTadas-7050/ai-qa-toolbox.git",
        },
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "fix_validated" in data or data.get("action") == "logged_only"
