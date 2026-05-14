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
