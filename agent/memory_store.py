"""Vector memory store for past CI failures.

Uses ChromaDB as a local persistent vector database.
In mock mode (MOCK_LLM=true) or CI, uses an in-memory ChromaDB client
and fake embeddings — no Ollama or network required.
In production, uses a persistent client with real embeddings.
"""

from __future__ import annotations

import os

MOCK_MODE = os.getenv("MOCK_LLM") == "true"
CI_MODE = os.getenv("CI") == "true"
USE_MOCK_EMBEDDINGS = MOCK_MODE or CI_MODE


class MockEmbeddingFunction:
    """Deterministic local embedding function for tests and mock mode."""

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [[float(hash(text) % 1000) / 1000.0] * 384 for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    @staticmethod
    def name() -> str:
        return "mock"

    @staticmethod
    def build_from_config(config: dict) -> "MockEmbeddingFunction":
        return MockEmbeddingFunction()

    def get_config(self) -> dict:
        return {}

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    def is_legacy(self) -> bool:
        return False


def _build_embedding_function():
    """Return an embedding function appropriate for the current environment."""
    if USE_MOCK_EMBEDDINGS:
        # Simple deterministic mock — no model download needed
        return MockEmbeddingFunction()

    try:
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
        return OllamaEmbeddingFunction(
            model_name="nomic-embed-text",
            url="http://localhost:11434/api/embeddings",
        )
    except Exception:
        return MockEmbeddingFunction()


def _build_client():
    """Return a ChromaDB client — in-memory for CI/mock, persistent otherwise."""
    import chromadb
    if USE_MOCK_EMBEDDINGS:
        return chromadb.Client()
    return chromadb.PersistentClient(path="./chroma_db")


def _get_collection():
    client = _build_client()
    ef = _build_embedding_function()
    return client.get_or_create_collection(
        name="failure_memory",
        embedding_function=ef,
    )


def store_failure(
    run_id: int | str,
    classification: dict,
    fix: dict,
    fix_passed: bool,
) -> None:
    """Embed and store a failure+fix record in the vector store."""
    collection = _get_collection()
    doc = (
        f"Category: {classification.get('category', 'unknown')}. "
        f"Root cause: {classification.get('root_cause', 'unknown')}. "
        f"Fix: {fix.get('fix_title', '')}. "
        f"Passed: {fix_passed}"
    )
    doc_id = f"run_{run_id}"
    # Upsert — overwrite if same run_id already stored
    existing = collection.get(ids=[doc_id])
    if existing["ids"]:
        collection.update(
            ids=[doc_id],
            documents=[doc],
            metadatas=[{
                "category": classification.get("category", "unknown"),
                "fix_passed": fix_passed,
            }],
        )
    else:
        collection.add(
            ids=[doc_id],
            documents=[doc],
            metadatas=[{
                "category": classification.get("category", "unknown"),
                "fix_passed": fix_passed,
            }],
        )


def retrieve_similar_failures(root_cause: str, n: int = 3) -> list[str]:
    """Return the n most similar past failure descriptions."""
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []
    n_results = min(n, count)
    results = collection.query(
        query_texts=[root_cause],
        n_results=n_results,
    )
    return results["documents"][0] if results["documents"] else []


if __name__ == "__main__":
    # Quick smoke test
    store_failure(
        run_id=1,
        classification={"category": "BUG", "root_cause": "Assertion failed on checkout"},
        fix={"fix_title": "Fix checkout assertion"},
        fix_passed=True,
    )
    results = retrieve_similar_failures("assertion error in checkout flow")
    print("Retrieved:", results)
