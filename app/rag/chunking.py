"""Semantic chunking via LangChain SemanticChunker."""

from __future__ import annotations

from collections.abc import Iterator

from langchain_experimental.text_splitter import SemanticChunker

from app.core.logger import logger
from app.rag.embeddings import GeminiEmbeddings

# Guard when semantic chunking yields empty/oversized pieces.
_MAX_CHUNK_CHARS = 2000
_OVERLAP = 200


def chunk_text(text: str) -> list[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    try:
        splitter = SemanticChunker(
            embeddings=GeminiEmbeddings(),
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
            "[rag.chunking] semantic chunking failed; using size fallback | error=%s",
            exc,
        )
        chunks = []

    if not chunks:
        chunks = _fixed_size_chunks(cleaned)

    # Guard against oversized chunks for embedding/metadata limits.
    normalized: list[str] = []
    for chunk in chunks:
        if len(chunk) <= _MAX_CHUNK_CHARS:
            normalized.append(chunk)
        else:
            normalized.extend(_fixed_size_chunks(chunk))

    logger.info("[rag.chunking] produced %s chunks", len(normalized))
    return normalized


def iter_text_chunks(text: str) -> Iterator[tuple[int, str]]:
    """Yield ``(chunk_index, chunk_text)`` from semantic chunking."""
    for index, chunk in enumerate(chunk_text(text)):
        yield index, chunk


def _fixed_size_chunks(text: str) -> list[str]:
    if len(text) <= _MAX_CHUNK_CHARS:
        return [text] if text.strip() else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + _MAX_CHUNK_CHARS, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(0, end - _OVERLAP)
    return chunks
