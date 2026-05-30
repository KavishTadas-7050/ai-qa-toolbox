"""Multi-repo configuration loader.

Reads watched_repos from config/repos.json so the webhook handler
can route payloads and skip unregistered repositories silently.
"""

from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "repos.json"


def get_watched_repos() -> list[dict]:
    """Return the list of watched repo configs."""
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)["watched_repos"]


def is_watched(owner: str, repo: str) -> bool:
    """Return True if the owner/repo pair is in the watched list."""
    return any(
        r["owner"] == owner and r["repo"] == repo
        for r in get_watched_repos()
    )


def should_notify_slack(owner: str, repo: str) -> bool:
    """Return True if Slack notifications are enabled for this repo."""
    for r in get_watched_repos():
        if r["owner"] == owner and r["repo"] == repo:
            return r.get("notify_slack", False)
    return False
