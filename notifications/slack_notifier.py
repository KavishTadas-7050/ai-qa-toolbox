"""Slack Block Kit notifier for CI failure alerts.

Sends a formatted Slack message when a failure is detected and classified.
Requires SLACK_WEBHOOK_URL environment variable.
Set MOCK_LLM=true to skip the HTTP call in tests/CI.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

CATEGORY_EMOJI = {
    "FLAKY": ":hourglass_flowing_sand:",
    "BUG": ":bug:",
    "ENVIRONMENT": ":package:",
    "CONFIG": ":gear:",
}


def _build_payload(
    repo: str,
    classification: dict,
    pr_url: str | None,
) -> dict:
    """Build a Slack Block Kit message payload."""
    category = classification.get("category", "UNKNOWN")
    confidence = classification.get("confidence", 0.0)
    root_cause = classification.get("root_cause", "Unknown root cause")
    emoji = CATEGORY_EMOJI.get(category, ":warning:")

    if isinstance(confidence, float):
        confidence_str = f"{confidence:.0%}"
    else:
        confidence_str = str(confidence)

    pr_text = f"<{pr_url}|View fix PR>" if pr_url else "No PR opened (FLAKY or sandbox failed)"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} CI Failure Detected — {repo}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Category:*\n{category}"},
                    {"type": "mrkdwn", "text": f"*Confidence:*\n{confidence_str}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Root cause:* {root_cause}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": pr_text},
            },
            {"type": "divider"},
        ]
    }


def notify_slack(
    owner: str,
    repo: str,
    run_id: int | str,
    classification: dict,
    pr_url: str | None = None,
) -> bool:
    """
    Send a Slack Block Kit alert for a CI failure.

    Returns True if the message was sent, False otherwise.
    Silently skips if SLACK_WEBHOOK_URL is not set or MOCK_LLM=true.
    """
    if os.getenv("MOCK_LLM") == "true":
        logger.info("Mock mode: skipping Slack notification for run %s", run_id)
        return False

    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_url:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack notification")
        return False

    import requests

    payload = _build_payload(repo, classification, pr_url)
    try:
        response = requests.post(slack_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Slack notification sent for run %s", run_id)
        return True
    except Exception as exc:
        logger.warning("Slack notification failed (non-fatal): %s", exc)
        return False
