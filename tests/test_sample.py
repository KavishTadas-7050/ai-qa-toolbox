from unittest.mock import Mock

import pytest

from ai_qa_toolbox.core.llm.client import ask_llm


def test_ask_llm_returns_response_text():
    prompt = "What is the capital of France? Answer in one word."
    client = Mock()
    client.responses.create.return_value = Mock(output_text="Paris")

    response = ask_llm(prompt, model="test-model", client=client)

    assert response == "Paris"
    client.responses.create.assert_called_once_with(model="test-model", input=prompt)


def test_ask_llm_requires_openai_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_ADMIN_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OpenAI credentials are required"):
        ask_llm("hello")
