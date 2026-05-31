"""FastAPI webhook handler — async self-healing CI pipeline.

All blocking LLM, sandbox, and notification calls run in a thread pool
via run_in_executor so they never block the FastAPI event loop.

Pipeline:
  check watched list → fetch log → classify → suggest fix
  → sandbox validate → log attempt → store memory → notify Slack
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from agent.classifier import classify
from agent.fixer import suggest_fix
from agent.fix_logger import log_attempt
from agent.sandbox_runner import run_fix_in_sandbox, run_fix_in_sandbox_mock
from api.stats import load_stats
from config.loader import is_watched, should_notify_slack
from notifications.slack_notifier import notify_slack

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Self-Healing CI Webhook", version="3.0.0")
templates = Jinja2Templates(directory="templates")

MOCK_MODE = os.getenv("MOCK_LLM") == "true"


def _fetch_log(owner: str, repo: str, run_id: int) -> str:
    """Stub log fetcher — returns sample log in mock mode."""
    if MOCK_MODE:
        sample = Path("agents/log_classifier/sample_log.txt")
        if sample.exists():
            return sample.read_text(encoding="utf-8")
        return "TimeoutError: waiting for selector '#submit-btn' exceeded 30000ms"
    raise NotImplementedError(
        "Set MOCK_LLM=true or implement GitHub API log fetching."
    )


def _open_pr(owner: str, repo: str, run_id: int, fix: dict, sha: str) -> str:
    """Stub PR opener — returns a placeholder URL."""
    return f"https://github.com/{owner}/{repo}/pull/new/{sha[:7]}-fix-run-{run_id}"


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mock_mode": MOCK_MODE}


@app.get("/stats")
def get_stats() -> dict:
    """Return fix attempt statistics as JSON."""
    return load_stats()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    """Render the observability dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"stats": load_stats()},
    )


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    """Return Prometheus-compatible metrics."""
    s = load_stats()
    return (
        "# HELP ci_agent_total_runs Total CI runs analysed\n"
        "# TYPE ci_agent_total_runs counter\n"
        f"ci_agent_total_runs {s['total']}\n\n"
        "# HELP ci_agent_fix_pass_rate Fix sandbox pass rate percent\n"
        "# TYPE ci_agent_fix_pass_rate gauge\n"
        f"ci_agent_fix_pass_rate {s['pass_rate']}\n"
    )


@app.post("/webhook")
async def handle_webhook(request: Request) -> JSONResponse:
    payload = await request.json()
    run = payload.get("workflow_run", {})

    owner = payload.get("repository", {}).get("owner", {}).get("login", "")
    repo = payload.get("repository", {}).get("name", "")

    # Step 0: check watched list
    if not is_watched(owner, repo):
        return JSONResponse({"status": "ignored", "reason": "repo not in watched list"})

    if payload.get("action") != "completed" or run.get("conclusion") != "failure":
        return JSONResponse({"status": "ignored"})

    run_id = run["id"]
    repo_url = payload["repository"].get("clone_url", "")
    branch = run.get("head_branch", "main")
    sha = run.get("head_sha", "unknown")

    loop = asyncio.get_event_loop()

    # Step 1: fetch log (async — non-blocking)
    log = await loop.run_in_executor(None, _fetch_log, owner, repo, run_id)

    # Step 2: classify (async — LLM call off event loop)
    classification = await loop.run_in_executor(None, classify, log)
    logger.info("Classification: %s", classification)

    # Step 3: skip PRs for flaky tests
    if classification.get("category") == "FLAKY":
        await loop.run_in_executor(
            None, log_attempt, run_id, classification, {}, False, None
        )
        if should_notify_slack(owner, repo):
            await loop.run_in_executor(
                None, notify_slack, owner, repo, run_id, classification, None
            )
        return JSONResponse({"classification": classification, "action": "logged_only"})

    # Step 4: generate fix suggestion (async)
    fix = await loop.run_in_executor(None, suggest_fix, log, classification)
    logger.info("Fix suggestion: %s", fix.get("fix_title"))

    # Step 5: validate fix in sandbox (async)
    if MOCK_MODE:
        sandbox_result = await loop.run_in_executor(
            None, run_fix_in_sandbox_mock, fix
        )
    else:
        sandbox_result = await loop.run_in_executor(
            None, run_fix_in_sandbox, repo_url, branch, fix
        )

    sandbox_passed = sandbox_result["passed"]
    logger.info("Sandbox passed: %s", sandbox_passed)

    # Step 6: open PR only if sandbox passed
    pr_url = None
    if sandbox_passed:
        pr_url = await loop.run_in_executor(
            None, _open_pr, owner, repo, run_id, fix, sha
        )

    # Step 7: log the attempt (async)
    await loop.run_in_executor(
        None, log_attempt, run_id, classification, fix, sandbox_passed, pr_url
    )

    # Step 8: store in vector memory (async, non-fatal)
    try:
        from agent.memory_store import store_failure
        await loop.run_in_executor(
            None, store_failure, run_id, classification, fix, sandbox_passed
        )
    except Exception as mem_exc:
        logger.warning("Memory store failed (non-fatal): %s", mem_exc)

    # Step 9: send Slack notification (async)
    if should_notify_slack(owner, repo):
        await loop.run_in_executor(
            None, notify_slack, owner, repo, run_id, classification, pr_url
        )

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
