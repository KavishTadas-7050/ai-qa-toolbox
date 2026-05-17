"""Pydantic models for structured LLM outputs."""

from pydantic import BaseModel, Field


class FailureClassification(BaseModel):
    """Structured output from the log classifier."""
    category: str = Field(
        description="One of: FLAKY, BUG, ENVIRONMENT, CONFIG"
    )
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0"
    )
    root_cause: str = Field(
        description="One sentence explaining the root cause"
    )
    fix_hint: str = Field(
        description="One sentence on what to change to fix this"
    )


class SelectorFix(BaseModel):
    """Structured output from the selector healer."""
    original_locator: str = Field(description="The failing locator")
    suggested_css: str = Field(description="A more robust CSS selector")
    suggested_playwright: str = Field(
        description="Playwright-native locator using getByRole/getByText/getByLabel"
    )
    reason_original_failed: str = Field(
        description="One sentence explaining why the original failed"
    )
    confidence: str = Field(description="high, medium, or low")
