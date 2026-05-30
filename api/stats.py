"""Stats loader — parses fix_attempts.jsonl into a summary dict.

Powers both the /stats JSON endpoint and the /dashboard HTML page.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

LOG_PATH = Path("logs/fix_attempts.jsonl")


def load_stats() -> dict:
    """Parse fix_attempts.jsonl and return a summary dict."""
    if not LOG_PATH.exists():
        return {
            "total": 0,
            "by_category": {},
            "pass_rate": 0.0,
            "recent": [],
        }

    lines = [
        raw_line.strip()
        for raw_line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if raw_line.strip()
    ]
    if not lines:
        return {
            "total": 0,
            "by_category": {},
            "pass_rate": 0.0,
            "recent": [],
        }

    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    categories = Counter(e.get("category", "unknown") for e in entries)
    passed = sum(1 for e in entries if e.get("sandbox_passed"))
    pass_rate = round(passed / len(entries) * 100, 1) if entries else 0.0

    return {
        "total": len(entries),
        "by_category": dict(categories),
        "pass_rate": pass_rate,
        "recent": list(reversed(entries[-10:])),
    }
