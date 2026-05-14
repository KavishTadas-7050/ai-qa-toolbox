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


def ask_llm(prompt: str, *, model: str = DEFAULT_MODEL, client=None) -> str:
    """Send a prompt to an OpenAI Responses API model and return the text output."""
    client = client or _build_client()
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text


def ask_llm_with_image(prompt: str, image_bytes: bytes, *, model: str = DEFAULT_MODEL, client=None) -> str:
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
