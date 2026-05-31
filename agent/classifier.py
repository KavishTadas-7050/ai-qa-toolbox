"""LangChain-based failure log classifier with retry backoff.

Uses a PromptTemplate + JsonOutputParser chain to classify CI/test failure
logs into structured output. Retries on malformed JSON up to 3 times with
exponential backoff. Provider-agnostic via AiQaToolboxLLM wrapper.
"""

import functools
import time

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from agent.models import FailureClassification
from agent.llm_backend import get_llm


parser = JsonOutputParser(pydantic_object=FailureClassification)

PROMPT = PromptTemplate(
    template="""You are a CI failure analyst. Classify this test failure log.
{format_instructions}

Categories:
- FLAKY: timing issues, race conditions, intermittent failures
- BUG: assertion errors, logic failures, wrong output
- ENVIRONMENT: missing deps, wrong runtime, infrastructure issues
- CONFIG: yaml errors, wrong paths, misconfiguration

Respond ONLY with valid JSON matching the schema above. No markdown, no fences.
If the log is empty or unclear, return low confidence with category FLAKY.

Log (last 4000 chars):
{log_content}""",
    input_variables=["log_content"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0):
    """Decorator that retries a function on JSON/key errors with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import json
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (json.JSONDecodeError, KeyError, ValueError) as exc:
                    last_exc = exc
                    if attempt == max_attempts - 1:
                        raise
                    wait = base_delay * (2 ** attempt)
                    print(f"Classify attempt {attempt + 1} failed ({exc}), retrying in {wait}s")
                    time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator


@retry_with_backoff(max_attempts=3, base_delay=0.5)
def classify(log_content: str) -> dict:
    """Classify a failure log and return structured JSON with retry on bad output."""
    llm = get_llm()
    chain = PROMPT | llm | parser
    # Treat empty logs gracefully
    content = log_content.strip() if log_content else "No log content provided."
    return chain.invoke({"log_content": content[-4000:]})


if __name__ == "__main__":
    import json
    from pathlib import Path

    sample = Path("agents/log_classifier/sample_log.txt").read_text(encoding="utf-8")
    result = classify(sample)
    print("=== CLASSIFIER RESULT ===")
    print(json.dumps(result, indent=2))
