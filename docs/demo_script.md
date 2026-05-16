# Demo Script

This is the step-by-step scenario to record for the demo GIF.

## Scenario: Full AI QA Pipeline in 90 seconds

### Step 1 — Log Classifier (15 seconds)
```bash
cd ~/ai-qa-toolbox
source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
python agents/log_classifier/main.py
```
**What to show:** The classifier reads a Playwright timeout log and returns
a JSON result with root_cause, failure_category, confidence, and recommended_action.

### Step 2 — Selector Healer (20 seconds)
```bash
python agents/selector_healer/main.py
```
**What to show:** Three broken selectors go in, three AI-suggested CSS and
Playwright-native locators come out, each with a reason the original failed.

### Step 3 — UI Auditor CLI (30 seconds)
```bash
python agentic-ui-auditor/auditor.py --url https://example.com
```
**What to show:** The pipeline prints each step (screenshot → LLM → report),
then outputs a formatted list of UX issues with severity and recommendations.

### Step 4 — Docker build (25 seconds)
```bash
docker build -t ai-qa-toolbox . 2>&1 | tail -5
docker run --rm -e OPENAI_API_KEY=dummy ai-qa-toolbox \
  python -c "from ai_qa_toolbox.core.llm.client import ask_llm; print('Container OK')"
```
**What to show:** Image builds successfully and imports resolve inside the container.

## Recording Commands

### Record with asciinema
```bash
asciinema rec docs/demo.cast --title "AI QA Toolbox Demo"
# follow the steps above, then press Ctrl-D to finish
```

### Convert to GIF
```bash
agg docs/demo.cast docs/demo.gif
```

### Preview locally
```bash
# macOS
open docs/demo.gif
# Linux
xdg-open docs/demo.gif
# Windows — just open the file in a browser
```
