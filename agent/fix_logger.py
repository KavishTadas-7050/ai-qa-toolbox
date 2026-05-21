"""Fix attempt logger — records every sandbox validation result to JSONL.

The resulting logs/fix_attempts.jsonl becomes training data for future
prompt tuning: patterns of failed fixes inform better fix generation.
"""

import datetime
import json
from pathlib import Path

LOG_PATH = Path("logs/fix_attempts.jsonl")


def log_attempt(
    run_id: int | str,
    classification: dict,
    fix: dict,
    sandbox_passed: bool,
    pr_url: str | None = None,
) -> None:
    """Append one fix attempt record to the JSONL log file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "run_id": str(run_id),
        "category": classification.get("category", "unknown"),
        "confidence": classification.get("confidence", 0.0),
        "fix_title": fix.get("fix_title", ""),
        "sandbox_passed": sandbox_passed,
        "pr_url": pr_url,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_attempts() -> list[dict]:
    """Return all logged fix attempts as a list of dicts."""
    if not LOG_PATH.exists():
        return []
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


if __name__ == "__main__":
    # Quick smoke test
    log_attempt(
        run_id=12345,
        classification={"category": "BUG", "confidence": 0.9},
        fix={"fix_title": "Fix assertion in test_checkout"},
        sandbox_passed=True,
        pr_url="https://github.com/example/repo/pull/1",
    )
    print("Logged. Current attempts:")
    for attempt in read_attempts():
        print(json.dumps(attempt, indent=2))
