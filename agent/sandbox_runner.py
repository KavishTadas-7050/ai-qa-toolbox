"""Sandbox test runner — validates a fix by running pytest inside Docker.

Clones the repo branch into a temp directory, optionally applies a fix,
then runs the test suite in an isolated python:3.12-slim container.
Returns pass/fail and truncated output for logging.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def _apply_fix(tmpdir: str, fix_suggestion: dict) -> None:
    """Append suggested code to the target file if both fields are present."""
    file_to_change = fix_suggestion.get("file_to_change")
    code_suggestion = fix_suggestion.get("code_suggestion")
    if not file_to_change or not code_suggestion:
        return
    target = Path(tmpdir) / file_to_change
    if target.exists():
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n" + code_suggestion)


def run_fix_in_sandbox(
    repo_url: str,
    branch: str,
    fix_suggestion: dict,
) -> dict:
    """
    Clone repo_url at branch, apply fix_suggestion, run pytest in Docker.

    Returns:
        {
            "passed": bool,
            "output": str   (last 2000 chars of combined stdout/stderr)
        }
    """
    try:
        import docker
    except ImportError:
        return {
            "passed": False,
            "output": "docker package not installed. Run: pip install docker",
        }

    client = docker.from_env()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone the failing branch
        clone_result = subprocess.run(
            [
                "git", "clone",
                "--branch", branch,
                "--depth", "1",
                repo_url,
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )
        if clone_result.returncode != 0:
            return {
                "passed": False,
                "output": f"git clone failed:\n{clone_result.stderr}",
            }

        # Apply the fix
        _apply_fix(tmpdir, fix_suggestion)

        # Run tests inside an isolated container
        try:
            output_bytes = client.containers.run(
                "python:3.12-slim",
                command=(
                    "bash -c 'pip install -r requirements.txt -q "
                    "&& pip install -e . -q "
                    "&& pytest tests/ -v --tb=short 2>&1'"
                ),
                volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                remove=True,
                stdout=True,
                stderr=True,
            )
            output = output_bytes.decode("utf-8", errors="replace")
        except Exception as exc:
            return {"passed": False, "output": f"Container error: {exc}"}

    passed = "passed" in output and "failed" not in output
    return {"passed": passed, "output": output[-2000:]}


def run_fix_in_sandbox_mock(fix_suggestion: dict) -> dict:
    """
    Mock sandbox runner for testing without Docker or network access.
    Returns a passing result with realistic output.
    """
    output = (
        "================================ test session starts ================================\n"
        "platform linux -- Python 3.12.0, pytest-9.0.3\n"
        "collected 2 items\n\n"
        "tests/test_sample.py ..                                                        [100%]\n\n"
        "================================= 2 passed in 1.07s =================================\n"
    )
    return {"passed": True, "output": output}
