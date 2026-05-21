"""FastAPI webhook handler — self-healing CI pipeline.

POST /webhook  accepts a GitHub workflow_run webhook payload.
Pipeline: fetch log → classify → suggest fix → sandbox validate → log attempt.
PRs are only opened when the fix passes the sandbox test run.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agent.classifier import classify
from agent.fixer import suggest_fix
from agent.fix_logger import log_attempt
from agent.sandbox_runner import run_fix_in_sandbox, run_fix_in_sandbox_mock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Self-Healing CI Webhook", version="1.0.0")

MOCK_MODE = os.getenv("MOCK_LLM") == "true"


def _fetch_log(owner: str, repo: str, run_id: int) -> str:
    """Stub log fetcher — returns sample log in mock mode."""
    if MOCK_MODE:
        sample = Path("agents/log_classifier/sample_log.txt")
        if sample.exists():
            return sample.read_text(encoding="utf-8")
        return "TimeoutError: waiting for selector '#submit-btn' exceeded 30000ms"
    # Real implementation would call GitHub API here
    raise NotImplementedError(
        "Set MOCK_LLM=true or implement GitHub API log fetching."
    )


def _open_pr(owner: str, repo: str, run_id: int, fix: dict, sha: str) -> str:
    """Stub PR opener — returns a placeholder URL."""
    return f"https://github.com/{owner}/{repo}/pull/new/{sha[:7]}-fix-run-{run_id}"


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mock_mode": MOCK_MODE}


@app.post("/webhook")
async def handle_webhook(request: Request) -> JSONResponse:
    payload = await request.json()
    run = payload.get("workflow_run", {})

    if payload.get("action") != "completed" or run.get("conclusion") != "failure":
        return JSONResponse({"status": "ignored"})

    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    run_id = run["id"]
    repo_url = payload["repository"].get("clone_url", "")
    branch = run.get("head_branch", "main")
    sha = run.get("head_sha", "unknown")

    # Step 1: fetch and classify the failure log
    log = _fetch_log(owner, repo, run_id)
    classification = classify(log)
    logger.info("Classification: %s", classification)

    # Step 2: skip PRs for flaky tests
    if classification.get("category") == "FLAKY":
        log_attempt(run_id, classification, {}, sandbox_passed=False)
        return JSONResponse({"classification": classification, "action": "logged_only"})

    # Step 3: generate fix suggestion
    fix = suggest_fix(log, classification)
    logger.info("Fix suggestion: %s", fix.get("fix_title"))

    # Step 4: validate fix in sandbox
    if MOCK_MODE:
        sandbox_result = run_fix_in_sandbox_mock(fix)
    else:
        sandbox_result = run_fix_in_sandbox(repo_url, branch, fix)

    sandbox_passed = sandbox_result["passed"]
    logger.info("Sandbox passed: %s", sandbox_passed)

    # Step 5: open PR only if sandbox passed
    pr_url = None
    if sandbox_passed:
        pr_url = _open_pr(owner, repo, run_id, fix, sha)

    # Step 6: log the attempt
    log_attempt(run_id, classification, fix, sandbox_passed, pr_url)

    # Step 7: store in vector memory for future RAG retrieval
    try:
        from agent.memory_store import store_failure
        store_failure(run_id, classification, fix, sandbox_passed)
    except Exception as mem_exc:
        logger.warning("Memory store failed (non-fatal): %s", mem_exc)

    return JSONResponse({
        "classification": classification,
        "fix_title": fix.get("fix_title"),
        "fix_validated": sandbox_passed,
        "pr_url": pr_url,
        "sandbox_output": sandbox_result["output"] if not sandbox_passed else None,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8001, reload=True)
