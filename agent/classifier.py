"""LangChain-based failure log classifier.

Uses a PromptTemplate + JsonOutputParser chain to classify CI/test failure
logs into structured output. Provider-agnostic via AiQaToolboxLLM wrapper.
"""

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

Log (last 4000 chars):
{log_content}""",
    input_variables=["log_content"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


def classify(log_content: str) -> dict:
    """Classify a failure log and return structured JSON."""
    llm = get_llm()
    chain = PROMPT | llm | parser
    return chain.invoke({"log_content": log_content[-4000:]})


if __name__ == "__main__":
    import json
    from pathlib import Path

    sample = Path("agents/log_classifier/sample_log.txt").read_text(encoding="utf-8")
    result = classify(sample)
    print("=== CLASSIFIER RESULT ===")
    print(json.dumps(result, indent=2))
