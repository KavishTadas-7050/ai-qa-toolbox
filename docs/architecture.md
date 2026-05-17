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

## Day 7 — LangChain ReAct Agent

```mermaid
flowchart TD
    A([Task: Analyze failure log]) --> B[ReAct Agent\nagent/react_agent.py]
    B -->|Thought: list logs| C[list_sample_logs tool]
    C -->|Observation: paths| B
    B -->|Thought: classify log| D[classify_log_file tool]
    D --> E[LangChain Chain\nPromptTemplate | LLM | JsonOutputParser]
    E --> F[AiQaToolboxLLM\nagent/llm_backend.py]
    F --> G[ask_llm\nai_qa_toolbox/core/llm/client.py]
    G -->|Gemini/OpenAI/Mock| H([LLM Response])
    H --> E
    E -->|Structured JSON| D
    D -->|Observation: classification| B
    B -->|Final Answer| I([category, confidence,\nroot_cause, fix_hint])
```

| Component | Location | Purpose |
|---|---|---|
| LLM Backend | `agent/llm_backend.py` | LangChain BaseLLM wrapping `ask_llm()` |
| Pydantic Models | `agent/models.py` | Schema for classifier and selector outputs |
| Classifier Chain | `agent/classifier.py` | PromptTemplate + LLM + JsonOutputParser |
| LangChain Tools | `agent/tools.py` | `@tool` wrappers callable by the ReAct agent |
| ReAct Agent | `agent/react_agent.py` | Reason+Act loop with Thought/Action/Observation |
