"""Smoke tests for Day 10 — multi-repo config and Slack notifier."""

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """All Day 10 tests run in mock mode."""
    monkeypatch.setenv("MOCK_LLM", "true")


def test_is_watched_known_repo():
    """is_watched returns True for repos in the watched list."""
    from config.loader import is_watched
    assert is_watched("KavishTadas-7050", "ai-qa-toolbox") is True


def test_is_watched_unknown_repo():
    """is_watched returns False for repos not in the watched list."""
    from config.loader import is_watched
    assert is_watched("some-random-user", "some-random-repo") is False


def test_should_notify_slack_known_repo():
    """should_notify_slack returns True for watched repos with notify_slack=true."""
    from config.loader import should_notify_slack
    assert should_notify_slack("KavishTadas-7050", "ai-qa-toolbox") is True


def test_slack_notifier_skips_in_mock_mode():
    """notify_slack returns False and skips HTTP call in mock mode."""
    from notifications.slack_notifier import notify_slack
    result = notify_slack(
        owner="KavishTadas-7050",
        repo="ai-qa-toolbox",
        run_id=1001,
        classification={"category": "BUG", "confidence": 0.9, "root_cause": "test"},
        pr_url="https://github.com/test/repo/pull/1",
    )
    assert result is False


def test_slack_payload_structure():
    """_build_payload returns a valid Block Kit structure."""
    from notifications.slack_notifier import _build_payload
    payload = _build_payload(
        repo="ai-qa-toolbox",
        classification={
            "category": "BUG",
            "confidence": 0.85,
            "root_cause": "Assertion failed on checkout",
        },
        pr_url="https://github.com/test/repo/pull/1",
    )
    assert "blocks" in payload
    assert len(payload["blocks"]) >= 4
    header = payload["blocks"][0]
    assert header["type"] == "header"
    assert "ai-qa-toolbox" in header["text"]["text"]


def test_webhook_ignores_unwatched_repo():
    """POST /webhook returns ignored for repos not in watched list."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    payload = {
        "action": "completed",
        "workflow_run": {"conclusion": "failure", "id": 1},
        "repository": {
            "name": "some-other-repo",
            "owner": {"login": "some-other-user"},
            "clone_url": "https://github.com/some-other-user/some-other-repo.git",
        },
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert data["reason"] == "repo not in watched list"


def test_webhook_accepts_watched_repo():
    """POST /webhook processes payload for watched repo."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    payload = {
        "action": "completed",
        "workflow_run": {
            "conclusion": "failure",
            "id": 1001,
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
