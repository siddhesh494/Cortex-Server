"""Embedding helpers for RAG indexing and retrieval.

Uses nomic-embed-text-v1.5 via fastembed (ONNX). Groq's chat API is used for
LLMs, but embedding models are not available on all Groq accounts, so we run
the same open-source Nomic model locally for consistent vectors.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Iterable

from langchain_core.embeddings import Embeddings

from app.config import settings
from app.core.logger import logger

DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


def _hf_token() -> str:
    return (settings.HF_TOKEN or os.environ.get("HF_TOKEN") or "").strip()


def _configure_embedding_runtime() -> None:
    """Set HF + ONNX env before fastembed imports those libraries."""
    token = _hf_token()
    if token:
        os.environ["HF_TOKEN"] = token
    else:
        # Public models still download without a token; hush Hub's noisy warning.
        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    # onnxruntime probes Linux DRM sysfs for GPUs; on macOS/CPU that only
    # prints a harmless warning. Keep ORT at ERROR unless already configured.
    os.environ.setdefault("ORT_LOG_SEVERITY_LEVEL", "3")


_configure_embedding_runtime()


@lru_cache(maxsize=1)
def _get_fastembed_model():
    _configure_embedding_runtime()
    from fastembed import TextEmbedding

    model_name = settings.EMBEDDING_MODEL
    if not _hf_token():
        logger.warning(
            "[rag.embeddings] HF_TOKEN is not set. Add a read token from "
            "https://huggingface.co/settings/tokens to .env for higher Hub rate limits."
        )
    logger.info("[rag.embeddings] loading fastembed model | model=%s", model_name)
    return TextEmbedding(
        model_name=model_name,
        providers=["CPUExecutionProvider"],
        cuda=False,
    )


def _embed_raw(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = _get_fastembed_model()
    vectors = list(model.embed(texts))
    return [vector.tolist() for vector in vectors]


def embed_documents(texts: Iterable[str]) -> list[list[float]]:
    """Embed document chunks with the Nomic document task prefix."""
    prefixed = [f"{DOCUMENT_PREFIX}{text}" for text in texts]
    return _embed_raw(prefixed)


def embed_query(text: str) -> list[float]:
    """Embed a retrieval query with the Nomic query task prefix."""
    vectors = _embed_raw([f"{QUERY_PREFIX}{text}"])
    if not vectors:
        raise ValueError("Failed to embed query text.")
    return vectors[0]


class NomicEmbeddings(Embeddings):
    """LangChain Embeddings adapter used by SemanticChunker."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # SemanticChunker embeds sentences for breakpoint detection; use
        # document prefix so chunking and storage share the same space.
        return embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return embed_query(text)
