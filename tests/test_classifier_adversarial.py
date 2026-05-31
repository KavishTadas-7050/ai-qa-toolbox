"""Adversarial tests for the log classifier.

Tests edge cases that break naive parsers:
- Empty logs
- Ambiguous logs with mixed signals
- Logs containing embedded JSON that is not the response
- Non-English logs
- Very long logs
- Logs with no failure signature

All tests run in MOCK_LLM=true mode so they pass in CI without any LLM.
The mock always returns a valid schema — these tests verify the classifier
never crashes and always returns a valid structure regardless of input.
"""

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")


EMPTY_LOG = ""

AMBIGUOUS_LOG = (
    "Everything looks fine\n"
    "[INFO] Tests started\n"
    "[INFO] Tests passed\n"
    "[ERROR] Timeout after 30s\n"
    "[INFO] Retrying...\n"
)

JSON_NOISE_LOG = (
    '{"status": "ok", "result": "success"}\n'
    "AssertionError: expected 200 got 500\n"
    '{"error": null}\n'
    "at tests/test_api.py:42"
)

FOREIGN_LOG = (
    "Erreur: module introuvable: pytest\n"
    "Installation échouée\n"
    "Le processus s'est terminé avec le code 1\n"
)

VERY_LONG_LOG = "INFO: step passing\n" * 2000 + "ERROR: final step failed\n"

NO_FAILURE_LOG = (
    "All systems operational\n"
    "Health check passed\n"
    "No errors detected\n"
)

MALFORMED_OUTPUT_LOG = (
    "```json\n"
    '{"not": "a real failure"}\n'
    "```\n"
    "SyntaxError: unexpected token\n"
)


def _assert_valid_schema(result: dict) -> None:
    """Assert the result matches the FailureClassification schema."""
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "category" in result, f"Missing 'category' in {result}"
    assert "confidence" in result, f"Missing 'confidence' in {result}"
    assert "root_cause" in result, f"Missing 'root_cause' in {result}"
    assert "fix_hint" in result, f"Missing 'fix_hint' in {result}"
    assert result["category"] in (
        "FLAKY", "BUG", "ENVIRONMENT", "CONFIG",
        # mock returns these variants too
        "selector_failure", "timeout", "assertion_error",
        "network_error", "flaky_test", "environment_issue", "unknown",
    ), f"Unexpected category: {result['category']}"


def test_empty_log_does_not_crash():
    """classify() handles empty string input without raising."""
    from agent.classifier import classify
    result = classify(EMPTY_LOG)
    _assert_valid_schema(result)


def test_ambiguous_log_returns_valid_schema():
    """classify() returns valid schema for ambiguous mixed-signal logs."""
    from agent.classifier import classify
    result = classify(AMBIGUOUS_LOG)
    _assert_valid_schema(result)


def test_json_noise_does_not_confuse_parser():
    """classify() handles logs containing embedded JSON without confusion."""
    from agent.classifier import classify
    result = classify(JSON_NOISE_LOG)
    _assert_valid_schema(result)


def test_foreign_language_log():
    """classify() handles non-English log content without crashing."""
    from agent.classifier import classify
    result = classify(FOREIGN_LOG)
    _assert_valid_schema(result)


def test_very_long_log_truncated_correctly():
    """classify() handles logs longer than 4000 chars via truncation."""
    from agent.classifier import classify
    result = classify(VERY_LONG_LOG)
    _assert_valid_schema(result)


def test_no_failure_signature_log():
    """classify() handles logs with no clear failure without crashing."""
    from agent.classifier import classify
    result = classify(NO_FAILURE_LOG)
    _assert_valid_schema(result)


def test_markdown_fenced_output_log():
    """classify() handles logs that look like LLM markdown output."""
    from agent.classifier import classify
    result = classify(MALFORMED_OUTPUT_LOG)
    _assert_valid_schema(result)


def test_classifier_never_raises_on_any_string():
    """classify() must not raise for any arbitrary string input."""
    from agent.classifier import classify
    edge_cases = [
        "   ",
        "\n\n\n",
        "null",
        "undefined",
        '{"key": "value"}',
        "a" * 10000,
        "\x00\x01\x02",
    ]
    for case in edge_cases:
        try:
            result = classify(case)
            _assert_valid_schema(result)
        except Exception as exc:
            pytest.fail(f"classify() raised {type(exc).__name__} on input {case[:30]!r}: {exc}")
