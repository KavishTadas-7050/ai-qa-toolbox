# Architecture

## Week 2 — Full Self-Healing CI Pipeline

```mermaid
flowchart TD
    A([GHA Workflow Fails]) --> B[GitHub Webhook]
    B --> C[FastAPI /webhook\napi/main.py async]
    C --> D{Repo watched?}
    D -->|No| E([Ignored])
    D -->|Yes| F[_fetch_log\nstub / GitHub API]
    F --> G[LangChain Chain\nagent/classifier.py]
    G --> H[retry_with_backoff\n3 attempts + backoff]
    H --> I[AiQaToolboxLLM\nGemini / OpenAI / Mock]
    I --> J{Category?}
    J -->|FLAKY| K[log_attempt\nSlack alert only]
    J -->|BUG / ENV / CONFIG| L[ChromaDB\nRetrieve similar fixes\nagent/memory_store.py]
    L --> M[agent/fixer.py\nRAG-enhanced suggestion]
    M --> N[sandbox_runner.py\nDocker python:3.12-slim]
    N -->|Tests pass| O[Open fix PR\nplaceholder / GitHub API]
    N -->|Tests fail| P[log_attempt\nfix_validated=false]
    O --> Q[log_attempt + store_failure\nfix_attempts.jsonl + ChromaDB]
    P --> Q
    Q --> R[Slack Block Kit alert\nnotifications/slack_notifier.py]
    R --> S([Dashboard /dashboard\nChart.js + Jinja2])
```

## Week 1 — Core Infrastructure (Days 1–6)

```mermaid
flowchart TD
    A([Developer / CI]) -->|runs| B[pytest + agents]
    B --> C{Failure?}
    C -->|yes| D[Log Classifier Agent\nagents/log_classifier/main.py]
    C -->|yes| E[Selector Healer Agent\nagents/selector_healer/main.py]
    D -->|ask_llm| F[LLM Client\nai_qa_toolbox/core/llm/client.py]
    E -->|ask_llm| F
    F -->|Gemini / OpenAI / Mock| G([Structured JSON Result])
    H([URL]) --> I[Screenshot Service\nPlaywright + Chromium]
    I --> J[ask_llm_with_image]
    J --> F
    F --> K([UX Audit Report])
```

## Component Map

| Component | Location | Day | Purpose |
|---|---|---|---|
| LLM Client | `ai_qa_toolbox/core/llm/client.py` | 2 | `ask_llm` + `ask_llm_with_image`, Gemini/OpenAI/Mock |
| Screenshot Service | `ai_qa_toolbox/ui_auditor/screenshot.py` | 2 | Playwright URL capture |
| Log Classifier Agent | `agents/log_classifier/main.py` | 3 | Standalone failure classifier |
| Selector Healer Agent | `agents/selector_healer/main.py` | 3 | Broken locator fixer |
| UI Auditor CLI | `agentic-ui-auditor/auditor.py` | 4 | Vision LLM UX audit pipeline |
| UI Auditor API | `agentic-ui-auditor/api.py` | 4 | FastAPI UX audit endpoint |
| LangChain LLM Wrapper | `agent/llm_backend.py` | 7 | BaseLLM wrapping `ask_llm()` |
| LangChain Classifier | `agent/classifier.py` | 7/12 | PromptTemplate + JsonOutputParser + retry |
| LangChain Fixer | `agent/fixer.py` | 8/9 | RAG-enhanced fix suggestion |
| ReAct Agent | `agent/react_agent.py` | 7 | Thought→Action→Observation loop |
| Sandbox Runner | `agent/sandbox_runner.py` | 8 | Docker test validation gate |
| Fix Logger | `agent/fix_logger.py` | 8 | JSONL fix attempt audit trail |
| ChromaDB Memory | `agent/memory_store.py` | 9 | Vector store for past failures |
| Seed Script | `scripts/seed_memory.py` | 9 | Bootstrap ChromaDB from JSONL |
| Repo Config | `config/loader.py` | 10 | Multi-repo watched list routing |
| Slack Notifier | `notifications/slack_notifier.py` | 10 | Block Kit CI failure alerts |
| Stats Loader | `api/stats.py` | 11 | Parses JSONL for dashboard |
| Webhook API | `api/main.py` | 8–12 | Async FastAPI pipeline orchestrator |
| Dashboard | `templates/dashboard.html` | 11 | Chart.js + activity table |
| CI Pipeline | `.github/workflows/ci.yml` | 5 | test + lint + docker-build |
| Demo GIF Workflow | `.github/workflows/demo-gif.yml` | 6 | Auto-generate demo.gif on push |
