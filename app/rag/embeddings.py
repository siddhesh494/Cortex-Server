"""Embedding helpers for RAG indexing and retrieval.

Uses gemini-embedding-2 via the Google Generative Language API (external).
No local ONNX model and no Nomic Atlas / Groq embeddings.
"""

from __future__ import annotations

import json
from typing import Iterable, Literal
from urllib.parse import quote

import httpx

from app.config import settings
from app.core.logger import logger

_MAX_API_ERROR_CHARS = 1000
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

TaskType = Literal["search_document", "search_query"]


class GeminiEmbeddingError(RuntimeError):
    """Raised when the Gemini embedding API fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        api_error: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.api_error = api_error


def _format_api_error_body(response: httpx.Response) -> str:
    """Extract a readable error string from a Gemini HTTP response."""
    raw = (response.text or "").strip()
    if not raw:
        return f"empty response body (HTTP {response.status_code})"

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return raw[:_MAX_API_ERROR_CHARS]

    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            message = err.get("message") or err.get("status") or err
            return str(message)[:_MAX_API_ERROR_CHARS]
        for key in ("message", "detail", "msg"):
            value = payload.get(key)
            if value is not None:
                if isinstance(value, (dict, list)):
                    return json.dumps(value, ensure_ascii=False)[:_MAX_API_ERROR_CHARS]
                return str(value)[:_MAX_API_ERROR_CHARS]
        return json.dumps(payload, ensure_ascii=False)[:_MAX_API_ERROR_CHARS]

    return str(payload)[:_MAX_API_ERROR_CHARS]


def _prepare_text(text: str, *, task_type: TaskType) -> str:
    """gemini-embedding-2 uses prompt prefixes instead of taskType."""
    cleaned = (text or "").strip()
    if task_type == "search_query":
        return f"task: search result | query: {cleaned}"
    return f"title: none | text: {cleaned}"


def _embed_url(model: str) -> str:
    # One request per text via batchEmbedContents so each chunk gets its own vector.
    return f"{_GEMINI_BASE}/models/{quote(model, safe='')}:batchEmbedContents"


def _embed_via_gemini(
    texts: list[str],
    *,
    task_type: TaskType,
) -> list[list[float]]:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        message = (
            "GEMINI_API_KEY is not set. Add a Google AI Studio key to embed with "
            "gemini-embedding-2."
        )
        logger.error("[rag.embeddings] %s", message)
        raise GeminiEmbeddingError(message)

    model = (settings.EMBEDDING_MODEL or "gemini-embedding-2").strip()
    dimension = int(settings.EMBEDDING_DIMENSION or 768)
    url = _embed_url(model)

    requests_payload = [
        {
            "model": f"models/{model}",
            "content": {
                "parts": [{"text": _prepare_text(text, task_type=task_type)}]
            },
            "output_dimensionality": dimension,
        }
        for text in texts
    ]

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    body = {"requests": requests_payload}

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=body)
    except httpx.HTTPError as exc:
        message = f"Gemini embedding request failed: {exc}"
        logger.error("[rag.embeddings] %s", message)
        raise GeminiEmbeddingError(message, api_error=str(exc)) from exc

    if response.status_code >= 400:
        api_error = _format_api_error_body(response)
        message = f"Gemini embedding failed (HTTP {response.status_code}): {api_error}"
        logger.error(
            "[rag.embeddings] Gemini API error | status=%s | batch_size=%s | "
            "task_type=%s | model=%s | api_error=%s",
            response.status_code,
            len(texts),
            task_type,
            model,
            api_error,
        )
        raise GeminiEmbeddingError(
            message,
            status_code=response.status_code,
            api_error=api_error,
        )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        api_error = (response.text or "")[:_MAX_API_ERROR_CHARS]
        message = (
            f"Gemini returned invalid JSON (HTTP {response.status_code}): {api_error}"
        )
        logger.error("[rag.embeddings] %s", message)
        raise GeminiEmbeddingError(
            message,
            status_code=response.status_code,
            api_error=api_error,
        ) from exc

    embeddings = payload.get("embeddings") if isinstance(payload, dict) else None
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        message = (
            "Gemini returned an unexpected embedding response "
            f"(expected {len(texts)} vectors)."
        )
        logger.error(
            "[rag.embeddings] %s | response_keys=%s",
            message,
            list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__,
        )
        raise GeminiEmbeddingError(message, status_code=response.status_code)

    vectors: list[list[float]] = []
    for item in embeddings:
        values = item.get("values") if isinstance(item, dict) else None
        if not isinstance(values, list) or not values:
            raise GeminiEmbeddingError(
                "Gemini embedding item missing values.",
                status_code=response.status_code,
            )
        vectors.append([float(v) for v in values])

    return vectors


def embed_documents(texts: Iterable[str]) -> list[list[float]]:
    """Embed document chunks for storage / retrieval."""
    batch = list(texts)
    if not batch:
        return []
    return _embed_via_gemini(batch, task_type="search_document")


def embed_query(text: str) -> list[float]:
    """Embed a retrieval query."""
    vectors = _embed_via_gemini([text], task_type="search_query")
    if not vectors:
        raise GeminiEmbeddingError("Failed to embed query text: empty Gemini response.")
    return vectors[0]


class GeminiEmbeddings:
    """LangChain-compatible adapter used by SemanticChunker."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return embed_query(text)


# Backwards-compatible alias for older imports.
NomicEmbeddings = GeminiEmbeddings
