"""LangChain tools for the ReAct agent.

Each @tool wraps an existing capability so the ReAct agent can decide
when and how to call them based on the task description.
"""

import json
from pathlib import Path

from langchain_core.tools import tool

from agent.classifier import classify


@tool
def classify_log_file(log_path: str) -> str:
    """
    Read a test failure log file and classify the failure.
    Returns JSON with category, confidence, root_cause, and fix_hint.
    Input: path to a .txt log file relative to the project root.
    """
    path = Path(log_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {log_path}"})
    log_content = path.read_text(encoding="utf-8")
    result = classify(log_content)
    return json.dumps(result, indent=2)


@tool
def classify_log_text(log_content: str) -> str:
    """
    Classify a test failure log provided as raw text.
    Returns JSON with category, confidence, root_cause, and fix_hint.
    Input: the raw log text as a string.
    """
    result = classify(log_content)
    return json.dumps(result, indent=2)


@tool
def list_sample_logs() -> str:
    """
    List available sample log files in the agents/log_classifier directory.
    Returns a JSON array of file paths.
    """
    log_dir = Path("agents/log_classifier")
    if not log_dir.exists():
        return json.dumps([])
    logs = [str(p) for p in log_dir.glob("*.txt")]
    return json.dumps(logs)
