"""Client helpers for LLM calls — supports OpenAI and Google Gemini."""

import os
import base64

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------
# Set LLM_PROVIDER=gemini to use Google Gemini (free tier).
# Defaults to openai if OPENAI_API_KEY is set, gemini if GEMINI_API_KEY is set.

def _detect_provider() -> str:
    explicit = os.getenv("LLM_PROVIDER", "").lower()
    if explicit in ("gemini", "openai"):
        return explicit
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return "openai"


# ---------------------------------------------------------------------------
# Default models per provider
# ---------------------------------------------------------------------------

_DEFAULT_MODELS = {
    "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "gemini": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
}

DEFAULT_MODEL = _DEFAULT_MODELS.get(_detect_provider(), "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Client builders
# ---------------------------------------------------------------------------

def _build_openai_client():
    if OpenAI is None:
        raise RuntimeError(
            "The openai package is required. "
            "Install with `pip install -e .[dev]`."
        )
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_ADMIN_KEY"):
        raise RuntimeError(
            "OpenAI credentials are required. "
            "Set OPENAI_API_KEY before calling ask_llm."
        )
    return OpenAI()


def _build_gemini_client():
    if OpenAI is None:
        raise RuntimeError(
            "The openai package is required even for Gemini (used as HTTP client). "
            "Install with `pip install -e .[dev]`."
        )
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GEMINI_API_KEY before calling ask_llm with LLM_PROVIDER=gemini."
        )
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


def _build_client(provider: str):
    if provider == "gemini":
        return _build_gemini_client()
    return _build_openai_client()


# ---------------------------------------------------------------------------
# Mock responses (no API key needed)
# ---------------------------------------------------------------------------

def _mock_response(prompt: str) -> str:
    """Return realistic hardcoded JSON for demo/CI use when MOCK_LLM=true."""
    import json
    prompt_lower = prompt.lower()

    if "ci failure analyst" in prompt_lower or "fix_hint" in prompt_lower:
        return json.dumps({
            "category": "FLAKY",
            "confidence": 0.92,
            "root_cause": "The test timed out waiting for a selector to become visible and enabled.",
            "fix_hint": "Add a robust wait for the UI state or fix the selector readiness condition."
        }, indent=2)

    if "failure_category" in prompt_lower:
        return json.dumps({
            "root_cause": "Element '#checkout-submit-btn' not found in DOM within timeout",
            "failure_category": "selector_failure",
            "confidence": "high",
            "recommended_action": "Verify the selector exists after page load; consider waiting for network idle before asserting.",
            "is_flaky": True
        }, indent=2)

    if "suggested_css" in prompt_lower:
        return json.dumps({
            "original_locator": "#checkout-submit-btn",
            "suggested_css": "button[data-testid='checkout-submit']",
            "suggested_playwright": "page.getByRole('button', { name: 'Submit' })",
            "reason_original_failed": "The ID was dynamically generated and changed after a frontend refactor.",
            "confidence": "high"
        }, indent=2)

    if "ux" in prompt_lower or "screenshot" in prompt_lower or "severity" in prompt_lower:
        return json.dumps([
            {
                "issue": "Insufficient color contrast on primary CTA button",
                "category": "color_contrast",
                "severity": "High",
                "location": "hero section",
                "recommendation": "Increase button text contrast ratio to at least 4.5:1 per WCAG AA."
            },
            {
                "issue": "Missing alt text on logo image",
                "category": "accessibility",
                "severity": "Medium",
                "location": "top navigation",
                "recommendation": "Add descriptive alt attribute to the <img> tag for screen reader support."
            },
            {
                "issue": "Body text font size below 16px on mobile viewport",
                "category": "text_legibility",
                "severity": "Low",
                "location": "footer",
                "recommendation": "Set minimum font size to 16px for paragraph text to improve readability."
            }
        ], indent=2)

    return json.dumps({"result": "mock response", "status": "ok"}, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ask_llm(prompt: str, *, model: str | None = None, client=None) -> str:
    """Send a text prompt to the configured LLM and return the response."""
    if os.getenv("MOCK_LLM") == "true":
        return _mock_response(prompt)

    provider = _detect_provider()
    client = client or _build_client(provider)
    effective_model = model or _DEFAULT_MODELS[provider]

    if provider == "gemini":
        response = client.chat.completions.create(
            model=effective_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    # OpenAI Responses API
    response = client.responses.create(
        model=effective_model,
        input=prompt,
    )
    return response.output_text


def ask_llm_with_image(
    prompt: str,
    image_bytes: bytes,
    *,
    model: str | None = None,
    client=None,
) -> str:
    """Send a prompt + image to the configured vision LLM and return the response."""
    if os.getenv("MOCK_LLM") == "true":
        return _mock_response(prompt)

    provider = _detect_provider()
    client = client or _build_client(provider)
    effective_model = model or _DEFAULT_MODELS[provider]
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    if provider == "gemini":
        response = client.chat.completions.create(
            model=effective_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"},
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content

    # OpenAI Responses API
    response = client.responses.create(
        model=effective_model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{b64}",
                    },
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )
    return response.output_text


__all__ = ["ask_llm", "ask_llm_with_image"]
