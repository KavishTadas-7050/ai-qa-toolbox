"""Seed the ChromaDB vector store from existing fix_attempts.jsonl.

Run once to bootstrap the knowledge base from Day 8 fix history:
    python scripts/seed_memory.py
"""

import json
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.memory_store import store_failure

LOG_PATH = Path("logs/fix_attempts.jsonl")


def seed() -> int:
    """Seed memory store from JSONL log. Returns number of entries stored."""
    if not LOG_PATH.exists():
        print(f"No log file found at {LOG_PATH}. Nothing to seed.")
        return 0

    count = 0
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping malformed line: {line[:60]}")
                continue

            classification = {
                "category": entry.get("category", "unknown"),
                "confidence": entry.get("confidence", 0.8),
                "root_cause": entry.get("root_cause", "unknown failure"),
                "fix_hint": "",
            }
            fix = {"fix_title": entry.get("fix_title", "") or "unknown"}
            run_id = entry.get("run_id", f"unknown_{count}")
            sandbox_passed = entry.get("sandbox_passed", False)

            store_failure(run_id, classification, fix, sandbox_passed)
            print(f"Stored run_{run_id} ({classification['category']})")
            count += 1

    print(f"\nSeeded {count} entries into ChromaDB.")
    return count


if __name__ == "__main__":
    seed()
