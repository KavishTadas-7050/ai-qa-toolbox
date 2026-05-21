"""LangChain-based fix suggester.

Given a classified failure log, generates a structured fix suggestion
with a file target and code change. Uses the same LangChain chain
pattern as classifier.py.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from agent.llm_backend import get_llm


class FixSuggestion(BaseModel):
    """Structured fix suggestion from the LLM."""
    fix_title: str = Field(description="Short title for the fix (used as PR title)")
    fix_description: str = Field(description="One paragraph explaining what to change and why")
    file_to_change: str = Field(description="Relative path to the file that needs changing")
    code_suggestion: str = Field(description="The actual code change or addition to make")
    confidence: str = Field(description="high, medium, or low")


parser = JsonOutputParser(pydantic_object=FixSuggestion)

PROMPT = PromptTemplate(
    template="""You are a senior software engineer reviewing a CI failure.
{format_instructions}

The failure has been classified as: {category}
Root cause: {root_cause}

Based on this failure log, suggest a concrete fix:
{log_content}

Respond ONLY with valid JSON matching the schema. No markdown, no fences.""",
    input_variables=["category", "root_cause", "log_content"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


def suggest_fix(log_content: str, classification: dict) -> dict:
    """Generate a structured fix suggestion for a classified failure."""
    llm = get_llm()
    chain = PROMPT | llm | parser
    return chain.invoke({
        "category": classification.get("category", "unknown"),
        "root_cause": classification.get("root_cause", "unknown"),
        "log_content": log_content[-3000:],
    })


if __name__ == "__main__":
    import json
    from pathlib import Path
    from agent.classifier import classify

    sample = Path("agents/log_classifier/sample_log.txt").read_text(encoding="utf-8")
    classification = classify(sample)
    fix = suggest_fix(sample, classification)
    print("=== FIX SUGGESTION ===")
    print(json.dumps(fix, indent=2))
