"""LangChain-compatible LLM backend using the existing ai_qa_toolbox client.

This wraps our existing ask_llm() function as a LangChain BaseLLM so we can
use LangChain chains, parsers, and agents without duplicating provider logic.
All provider detection (Gemini vs OpenAI vs mock) is handled by client.py.
"""

from __future__ import annotations

from typing import Any, List, Optional
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

from ai_qa_toolbox.core.llm.client import ask_llm


class AiQaToolboxLLM(LLM):
    """LangChain LLM wrapper around our existing ask_llm() function."""

    model_kwargs: dict = {}

    @property
    def _llm_type(self) -> str:
        return "ai_qa_toolbox"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        return ask_llm(prompt)

    @property
    def _identifying_params(self) -> dict:
        return {"llm_type": self._llm_type}


def get_llm() -> AiQaToolboxLLM:
    """Return a configured LangChain LLM instance."""
    return AiQaToolboxLLM()
