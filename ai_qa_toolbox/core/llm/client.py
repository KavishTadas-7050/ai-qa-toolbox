"""Client helpers for OpenAI-backed LLM calls."""

import os
import base64

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    OpenAI = None


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")


def _build_client():
    if OpenAI is None:
        raise RuntimeError(
            "The openai package is required. Install dependencies with "
            "`pip install -e .[dev]` or `pip install -r requirements.txt`."
        )

    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_ADMIN_KEY"):
        raise RuntimeError(
            "OpenAI credentials are required. Set OPENAI_API_KEY before "
            "calling ask_llm, or pass a client explicitly for tests."
        )

    return OpenAI()


def _mock_response(prompt: str) -> str:
    """Return realistic hardcoded JSON for demo/CI use when MOCK_LLM=true."""
    import json
    prompt_lower = prompt.lower()

    if "failure_category" in prompt_lower:
        # Log classifier response
        return json.dumps({
            "root_cause": "Element '#checkout-submit-btn' not found in DOM within timeout",
            "failure_category": "selector_failure",
            "confidence": "high",
            "recommended_action": "Verify the selector exists after page load; consider waiting for network idle before asserting.",
            "is_flaky": True
        }, indent=2)

    if "suggested_css" in prompt_lower:
        # Selector healer response
        return json.dumps({
            "original_locator": "#checkout-submit-btn",
            "suggested_css": "button[data-testid='checkout-submit']",
            "suggested_playwright": "page.getByRole('button', { name: 'Submit' })",
            "reason_original_failed": "The ID was dynamically generated and changed after a frontend refactor.",
            "confidence": "high"
        }, indent=2)

    if "ux" in prompt_lower or "screenshot" in prompt_lower or "severity" in prompt_lower:
        # UI auditor response
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

    # Generic fallback
    return json.dumps({"result": "mock response", "status": "ok"}, indent=2)


def ask_llm(prompt: str, *, model: str = DEFAULT_MODEL, client=None) -> str:
    """Send a prompt to an OpenAI Responses API model and return the text output."""
    import os
    if os.getenv("MOCK_LLM") == "true":
        return _mock_response(prompt)

    client = client or _build_client()
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text


def ask_llm_with_image(prompt: str, image_bytes: bytes, *, model: str = DEFAULT_MODEL, client=None) -> str:
    import os
    if os.getenv("MOCK_LLM") == "true":
        return _mock_response(prompt)

    client = client or _build_client()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    response = client.responses.create(
        model=model,
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
