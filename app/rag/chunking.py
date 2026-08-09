"""Semantic chunking via LangChain SemanticChunker."""

from __future__ import annotations

from langchain_experimental.text_splitter import SemanticChunker

from app.core.logger import logger
from app.rag.embeddings import NomicEmbeddings

# Fallback when semantic chunking yields a single huge blob or empty result.
_FALLBACK_MAX_CHARS = 2000
_FALLBACK_OVERLAP = 200


def chunk_text(text: str) -> list[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    try:
        splitter = SemanticChunker(
            embeddings=NomicEmbeddings(),
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95,
        )
        chunks = [
            chunk.strip()
            for chunk in splitter.split_text(cleaned)
            if chunk and chunk.strip()
        ]
    except Exception as exc:
        logger.warning(
            "[rag.chunking] semantic chunking failed; using fallback | error=%s",
            exc,
        )
        chunks = []

    if not chunks:
        chunks = _fixed_size_chunks(cleaned)

    # Guard against oversized chunks for embedding/metadata limits.
    normalized: list[str] = []
    for chunk in chunks:
        if len(chunk) <= _FALLBACK_MAX_CHARS:
            normalized.append(chunk)
        else:
            normalized.extend(_fixed_size_chunks(chunk))

    logger.info("[rag.chunking] produced %s chunks", len(normalized))
    return normalized


def _fixed_size_chunks(text: str) -> list[str]:
    # if the text is less than the fallback max characters then return the text as it is
    if len(text) <= _FALLBACK_MAX_CHARS:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + _FALLBACK_MAX_CHARS, len(text))
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - _FALLBACK_OVERLAP)
    return [c for c in chunks if c]
