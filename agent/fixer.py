"""LangChain-based fix suggester with retrieval-augmented generation.

Retrieves similar past failures from ChromaDB before generating a fix,
giving the LLM concrete historical context to improve suggestion quality.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from agent.llm_backend import get_llm
from agent.memory_store import retrieve_similar_failures


class FixSuggestion(BaseModel):
    """Structured fix suggestion from the LLM."""
    fix_title: str = Field(description="Short title for the fix, under 60 chars")
    fix_description: str = Field(description="2-3 sentence explanation of what to change and why")
    fix_steps: list[str] = Field(description="List of concrete steps to apply the fix")
    file_to_change: str | None = Field(description="Relative path to file that needs changing, or null")
    code_suggestion: str | None = Field(description="Exact lines to change or add, or null")
    confidence: str = Field(description="high, medium, or low")


parser = JsonOutputParser(pydantic_object=FixSuggestion)

PROMPT = PromptTemplate(
    template="""You are a CI repair engineer. A GitHub Actions workflow failed.
{format_instructions}

Failure category: {category}
Root cause: {root_cause}

Similar past failures and their fixes (use these as examples):
{memory_context}

Raw log tail:
{log_tail}

Based on the patterns above, suggest a concrete fix.
Respond ONLY with valid JSON matching the schema. No markdown, no fences.""",
    input_variables=["category", "root_cause", "memory_context", "log_tail"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


def suggest_fix(log_content: str, classification: dict) -> dict:
    """Generate a structured fix suggestion using RAG from ChromaDB."""
    root_cause = classification.get("root_cause", "unknown failure")

    # Retrieve similar past failures from vector store
    similar = retrieve_similar_failures(root_cause, n=3)
    memory_context = (
        "\n".join(f"- {m}" for m in similar)
        if similar
        else "No prior examples found."
    )

    llm = get_llm()
    chain = PROMPT | llm | parser
    return chain.invoke({
        "category": classification.get("category", "unknown"),
        "root_cause": root_cause,
        "memory_context": memory_context,
        "log_tail": log_content[-1500:],
    })


if __name__ == "__main__":
    import json
    from pathlib import Path
    from agent.classifier import classify

    sample = Path("agents/log_classifier/sample_log.txt").read_text(encoding="utf-8")
    classification = classify(sample)
    fix = suggest_fix(sample, classification)
    print("=== FIX SUGGESTION (with memory) ===")
    print(json.dumps(fix, indent=2))
