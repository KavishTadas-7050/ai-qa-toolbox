# CI Setup

## Demo GIF generation

The `demo-gif` workflow runs entirely in mock mode — **no API key or secrets required**.

It uses `MOCK_LLM=true` to return realistic hardcoded JSON instead of
calling OpenAI, so the GIF shows real pipeline output without any cost.

## Trigger the workflow manually

1. Go to the **Actions** tab in your GitHub repository
2. Click **Generate Demo GIF** in the left sidebar
3. Click **Run workflow** → **Run workflow**

The workflow will:
- Run all three agents with mocked LLM responses
- Record the terminal session with asciinema
- Convert to `docs/demo.gif` using agg
- Auto-commit the GIF back to your repo

## Automatic triggers

The workflow also re-runs automatically on every push to `main` that
touches agent code, auditor code, or `docs/record_demo.sh`.

## When you have an OpenAI API key (optional upgrade)

Add it as a GitHub secret named `OPENAI_API_KEY` and change the
workflow env block from:
  MOCK_LLM: "true"
to:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  OPENAI_MODEL: gpt-4o-mini
