import json
from pathlib import Path

from ai_qa_toolbox.core.llm.client import ask_llm


def main():
    log_path = Path(__file__).parent / "sample_log.txt"
    log_content = log_path.read_text(encoding="utf-8")

    prompt = f"""
You are a QA engineer analyzing a test failure log. Analyze the log below and respond ONLY with a valid JSON object \u2014 no markdown, no explanation, no code fences.

The JSON must have exactly these fields:
- "root_cause": short string (what specifically failed)
- "failure_category": one of [selector_failure, timeout, assertion_error, network_error, flaky_test, environment_issue, unknown]
- "confidence": one of [high, medium, low]
- "recommended_action": one actionable sentence for the QA engineer
- "is_flaky": boolean

LOG:
{log_content}
"""

    result = ask_llm(prompt)

    print("=== LOG CLASSIFIER RESULT ===")
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        print(result)
    else:
        print(json.dumps(parsed, indent=2))


if __name__ == "__main__":
    main()
