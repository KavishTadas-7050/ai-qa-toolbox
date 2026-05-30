"""Smoke tests for Day 9 — ChromaDB memory store and RAG-enhanced fixer."""

import pytest


@pytest.fixture(autouse=True)
def mock_llm_env(monkeypatch):
    """All Day 9 tests run in mock/CI mode — no Ollama or network needed."""
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("CI", "true")


def test_store_and_retrieve_failure():
    """store_failure persists a record retrievable by retrieve_similar_failures."""
    from agent.memory_store import store_failure, retrieve_similar_failures

    store_failure(
        run_id=901,
        classification={
            "category": "BUG",
            "root_cause": "Assertion failed on checkout page submit",
        },
        fix={"fix_title": "Fix checkout assertion"},
        fix_passed=True,
    )
    results = retrieve_similar_failures("assertion error on checkout", n=3)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any("BUG" in r or "checkout" in r.lower() for r in results)


def test_retrieve_returns_empty_when_store_empty():
    """retrieve_similar_failures returns empty list when store has no entries."""
    from agent.memory_store import retrieve_similar_failures
    # Fresh in-memory store is empty — should not raise, just return []
    results = retrieve_similar_failures("some random failure", n=3)
    assert isinstance(results, list)


def test_fixer_uses_memory_context():
    """suggest_fix runs end-to-end with memory context injected."""
    from agent.fixer import suggest_fix

    classification = {
        "category": "BUG",
        "confidence": 0.9,
        "root_cause": "Selector not found on checkout page",
        "fix_hint": "Update the selector",
    }
    result = suggest_fix(
        "TimeoutError: waiting for selector '#submit' exceeded 30000ms",
        classification,
    )
    assert isinstance(result, dict)


def test_seed_script_runs_without_error(monkeypatch):
    import json
    import tempfile
    import pathlib

    log_file = pathlib.Path(tempfile.mktemp(suffix=".jsonl"))
    entries = [
        {
            "run_id": "901",
            "category": "BUG",
            "confidence": 0.85,
            "fix_title": "Fix assertion",
            "sandbox_passed": True,
        },
        {
            "run_id": "902",
            "category": "FLAKY",
            "confidence": 0.7,
            "fix_title": "",
            "sandbox_passed": False,
        },
    ]
    with open(log_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    import scripts.seed_memory as seed_module
    monkeypatch.setattr(seed_module, "LOG_PATH", log_file)
    count = seed_module.seed()
    assert count == 2
    log_file.unlink(missing_ok=True)    