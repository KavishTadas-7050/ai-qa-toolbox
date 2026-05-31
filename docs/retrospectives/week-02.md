# Week 2 Retrospective — Self-Healing CI Agent

## What was built

### Day 7 — LangChain ReAct Agent
Replaced direct `ask_llm()` calls with a LangChain chain (PromptTemplate →
AiQaToolboxLLM → JsonOutputParser). Built a ReAct agent with three tools:
`classify_log_file`, `classify_log_text`, `list_sample_logs`. The
Thought → Action → Observation loop now orchestrates tool selection.

### Day 8 — Docker Sandbox Validation
Added a sandbox runner that clones the failing branch, applies the fix,
and runs pytest inside a `python:3.12-slim` container. PRs only open when
tests pass. Every attempt logged to `logs/fix_attempts.jsonl`.

### Day 9 — ChromaDB Vector Memory
Integrated ChromaDB as a local vector store. Each classified failure is
embedded and stored. Before generating a fix, the agent retrieves the 3
most similar past failures as few-shot context — retrieval-augmented
generation applied to CI repair.

### Day 10 — Multi-Repo Routing + Slack Alerts
Added `config/repos.json` watched list so the webhook silently ignores
unregistered repos. Built a Slack Block Kit notifier that fires within
seconds of a failure detection with category badge, confidence, root
cause, and PR link.

### Day 11 — Observability Dashboard
Added `/stats` (JSON), `/dashboard` (Chart.js doughnut + activity table),
and `/metrics` (Prometheus-compatible) endpoints. The dashboard renders
live data from `fix_attempts.jsonl` with no database required.

### Day 12 — Async Pipeline + Adversarial Tests
Moved all blocking LLM/sandbox/Slack calls to `run_in_executor` so
FastAPI never blocks the event loop. Added exponential backoff retry to
the classifier. Wrote 8 adversarial tests covering empty logs, foreign
language, JSON noise, and arbitrary string inputs.

---

## What was harder than expected

- **ChromaDB in CI**: The persistent client requires a filesystem path that
  doesn't exist cleanly in GitHub Actions. Solved by detecting `CI=true`
  and switching to an in-memory client with mock embeddings.
- **Windows `tmp_path` permissions**: pytest's built-in `tmp_path` fixture
  consistently hits `PermissionError` on Windows due to stale temp dirs.
  Worked around with `tempfile.mktemp()` in affected tests.
- **Package discovery**: Each new top-level package (`agent`, `api`,
  `scripts`, `config`, `notifications`) required a manual addition to
  `pyproject.toml`'s `include` list. Easy fix but caught us multiple times.

---

## What the agent still gets wrong

- **FLAKY vs BUG accuracy**: Deterministic timeouts (selector not found,
  fixed 30s wait) are consistently classified FLAKY when they are
  reproducible BUGs. The prompt needs stronger category definitions.
- **Fix suggestions for CONFIG failures**: ~40% require manual path
  corrections because the LLM doesn't have repo structure context.
- **Sandbox clone time**: `git clone --depth 1` still takes 8–15s in CI
  for larger repos. A local cache layer would help significantly.

---

## Key architectural decisions

- **No new LLM provider**: Used the existing Gemini/OpenAI/Mock client
  rather than adding Ollama. This kept CI free and the codebase simpler.
- **JSONL over a database**: `fix_attempts.jsonl` is append-only, human-
  readable, and requires zero setup. It feeds both the dashboard and the
  ChromaDB seed script.
- **Mock-first testing**: Every new component was built with `MOCK_LLM=true`
  support first, ensuring 100% of tests pass in CI without any API key.

---

## Next: Sentinel Security Agent

Starting Phase 2 — a LangChain agent that eliminates OWASP ZAP false
positives using application crawl map reasoning. The ChromaDB memory
pattern built on Day 9 transfers directly: past vulnerability assessments
stored as embeddings, retrieved as context before triage decisions.

Week 3 goal: first live ZAP scan with LLM-powered false positive filtering.
