"""Smoke tests for Day 12 — async pipeline and retry decorator."""

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")


def test_retry_decorator_succeeds_on_first_attempt():
    """retry_with_backoff passes through normal return values unchanged."""
    from agent.classifier import retry_with_backoff

    call_count = 0

    @retry_with_backoff(max_attempts=3, base_delay=0.01)
    def always_succeeds():
        nonlocal call_count
        call_count += 1
        return {"category": "BUG", "confidence": 0.9}

    result = always_succeeds()
    assert result["category"] == "BUG"
    assert call_count == 1


def test_retry_decorator_retries_on_json_error():
    """retry_with_backoff retries on JSONDecodeError and returns on success."""
    import json
    from agent.classifier import retry_with_backoff

    call_count = 0

    @retry_with_backoff(max_attempts=3, base_delay=0.01)
    def fails_twice_then_succeeds():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise json.JSONDecodeError("bad json", "", 0)
        return {"category": "FLAKY", "confidence": 0.5}

    result = fails_twice_then_succeeds()
    assert result["category"] == "FLAKY"
    assert call_count == 3


def test_retry_decorator_raises_after_max_attempts():
    """retry_with_backoff raises the last exception after max_attempts."""
    import json
    from agent.classifier import retry_with_backoff

    @retry_with_backoff(max_attempts=2, base_delay=0.01)
    def always_fails():
        raise json.JSONDecodeError("always bad", "", 0)

    with pytest.raises(json.JSONDecodeError):
        always_fails()


def test_async_webhook_returns_200():
    """Async webhook handler returns 200 for watched repo failure."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    payload = {
        "action": "completed",
        "workflow_run": {
            "conclusion": "failure",
            "id": 1201,
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


def test_classify_is_resilient_to_empty_input():
    """classify() does not raise on empty string in mock mode."""
    from agent.classifier import classify
    result = classify("")
    assert isinstance(result, dict)
    assert "category" in result
