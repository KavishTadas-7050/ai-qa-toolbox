# Architecture

## System Overview

```mermaidflowchart TD
A([Developer / CI]) -->|runs| B[pytest + agents]
B --> C{Failure?}
C -->|yes| D[Log Classifier Agent\nagents/log_classifier/main.py]
C -->|yes| E[Selector Healer Agent\nagents/selector_healer/main.py]
D -->|ask_llm| F[OpenAI LLM\ngpt-4o / gpt-4o-mini]
E -->|ask_llm| F
F -->|JSON| D
F -->|JSON| E
D -->|root_cause, confidence,\nrecommended_action| G([QA Engineer])
E -->|suggested_css,\nsuggested_playwright| GH([User / CI]) -->|POST /audit/url| I[FastAPI\nagentic-ui-auditor/api.py]
I --> J[Screenshot Service\nai_qa_toolbox/ui_auditor/screenshot.py]
J -->|Playwright + Chromium| K([Target URL])
K -->|screenshot bytes| J
J --> L[ask_llm_with_image\nai_qa_toolbox/core/llm/client.py]
L -->|base64 image + prompt| F
F -->|JSON issues array| L
L --> M([Audit Report\nissue, severity, recommendation])

## Component Map

| Component | Location | Purpose |
|---|---|---|
| LLM Client | `ai_qa_toolbox/core/llm/client.py` | `ask_llm` and `ask_llm_with_image` wrappers |
| Screenshot Service | `ai_qa_toolbox/ui_auditor/screenshot.py` | Playwright-based URL capture |
| Log Classifier | `agents/log_classifier/main.py` | Classifies test failure logs via LLM |
| Selector Healer | `agents/selector_healer/main.py` | Suggests robust locators for broken selectors |
| UI Auditor CLI | `agentic-ui-auditor/auditor.py` | End-to-end UX audit pipeline |
| UI Auditor API | `agentic-ui-auditor/api.py` | FastAPI wrapper for auditor pipeline |
| CI Pipeline | `.github/workflows/ci.yml` | Test, lint, and Docker build on every push |
