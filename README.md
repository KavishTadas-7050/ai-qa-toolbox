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
