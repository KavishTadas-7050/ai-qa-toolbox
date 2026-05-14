# AI QA Toolbox

AI-powered QA automation tooling experiments.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

On Linux CI or headless servers, install Playwright system dependencies too:

```bash
python -m playwright install --with-deps chromium
```

## Configuration

Set `OPENAI_API_KEY` before using the LLM client. `OPENAI_MODEL` is optional and defaults to `gpt-5-mini`.

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "gpt-5-mini"
```

## Test

```powershell
python -m pytest
```

---

## Day 3 – AI Agents

### Log Classifier Agent
Reads a Playwright failure log and uses the LLM to classify the root cause, failure category, confidence, recommended action, and flakiness.

```powershell
# Run individually
python -m agents.log_classifier.main

# Or directly
python agents/log_classifier/main.py
```

### Selector Healer Agent
Takes 3 broken Playwright locators and asks the LLM to suggest robust CSS and Playwright-native replacements.

```powershell
python -m agents.selector_healer.main
```

### Run both agents together
```powershell
python agents/run_all_agents.py
```

---

## Day 4 – Agentic UI Auditor Pipeline

### What it does
Captures a screenshot of any URL using Playwright, sends it to a vision LLM (GPT-4o), and produces a structured JSON report of UX issues including severity, category, location, and recommended fix.

### Run the auditor (CLI)

```powershell
# Audit the default page (example.com)
python agentic-ui-auditor/auditor.py

# Audit any URL
python agentic-ui-auditor/auditor.py --url https://your-site.com
```

### Run the FastAPI server (optional)

```powershell
cd agentic-ui-auditor
python api.py
# Server runs at http://localhost:8000

# Audit a URL via API
curl -X POST http://localhost:8000/audit/url \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://example.com\"}"

# Audit an uploaded screenshot
curl -X POST http://localhost:8000/audit/upload \
  -F "file=@screenshot.png"
```

### Pipeline steps
1. Playwright captures a full-page screenshot
2. Screenshot bytes sent to vision LLM with UX audit prompt
3. LLM returns structured JSON array of issues
4. Report printed to terminal or returned via API
