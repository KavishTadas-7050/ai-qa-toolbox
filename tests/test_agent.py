"""Smoke tests for the Day 7 LangChain agent components."""

import json
import pytest


@pytest.fixture(autouse=True)
def mock_llm_env(monkeypatch):
    """Ensure all agent tests run in mock mode — no API key needed."""
    monkeypatch.setenv("MOCK_LLM", "true")


def test_classifier_returns_valid_schema():
    """classify() returns a dict with all required fields."""
    from agent.classifier import classify

    sample_log = "TimeoutError: waiting for selector '#submit-btn' exceeded 30000ms"
    result = classify(sample_log)

    assert isinstance(result, dict)
    assert "category" in result
    assert "confidence" in result
    assert "root_cause" in result
    assert "fix_hint" in result


def test_classify_log_file_tool():
    """classify_log_file tool reads and classifies a real sample log."""
    from agent.tools import classify_log_file

    result_str = classify_log_file.invoke(
        "agents/log_classifier/sample_log.txt"
    )
    result = json.loads(result_str)
    assert "category" in result


def test_list_sample_logs_tool():
    """list_sample_logs tool returns a list containing at least one file."""
    from agent.tools import list_sample_logs

    result_str = list_sample_logs.invoke("")
    result = json.loads(result_str)
    assert isinstance(result, list)
    assert len(result) >= 1


def test_llm_backend_wraps_ask_llm():
    """AiQaToolboxLLM._call() delegates to ask_llm correctly."""
    from agent.llm_backend import AiQaToolboxLLM

    llm = AiQaToolboxLLM()
    response = llm._call("classify this: TimeoutError waiting for selector")
    assert isinstance(response, str)
    assert len(response) > 0
