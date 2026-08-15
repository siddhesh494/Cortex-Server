"""Pinecone vector store helpers for RAG."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from pinecone import Pinecone, ServerlessSpec

from app.config import settings
from app.core.logger import logger

# Pinecone metadata value size is limited; keep original text bounded.
_MAX_ORIGINAL_TEXT_CHARS = 35000
_UPSERT_MAX_ATTEMPTS = 3
_UPSERT_RETRY_BASE_DELAY_SEC = 0.75


class PineconeVectorStore:
    def __init__(self) -> None:
        if not settings.PINECONE_API_KEY:
            raise RuntimeError(
                "PINECONE_API_KEY is not configured. Add it to your .env file."
            )
        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._index_name = settings.PINECONE_INDEX_NAME
        self._ensure_index()
        self._index = self._pc.Index(self._index_name)

    def _ensure_index(self) -> None:
        if self._pc.has_index(self._index_name):
            logger.info(
                "[rag.pinecone] using existing index | name=%s",
                self._index_name,
            )
            return

        logger.info(
            "[rag.pinecone] creating index | name=%s | dim=%s",
            self._index_name,
            settings.EMBEDDING_DIMENSION,
        )
        self._pc.create_index(
            name=self._index_name,
            dimension=settings.EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            ),
        )

        # Wait until ready (create_index may return before ready on some SDKs).
        for _ in range(60):
            description = self._pc.describe_index(self._index_name)
            status = getattr(description, "status", None)
            ready = False
            if isinstance(status, dict):
                ready = bool(status.get("ready"))
            elif status is not None:
                ready = bool(getattr(status, "ready", False))
            if ready:
                break
            time.sleep(1)

    def clear_session_namespace(self, session_id: str) -> None:
        """Remove prior vectors for this session (safe re-index / retry)."""
        namespace = self._namespace(session_id)
        try:
            self._index.delete(delete_all=True, namespace=namespace)
            logger.info(
                "[rag.pinecone] cleared namespace before ingest | namespace=%s",
                namespace,
            )
        except Exception as exc:
            # Empty namespace delete can error on some Pinecone plans/states.
            logger.warning(
                "[rag.pinecone] namespace clear skipped | namespace=%s | error=%s",
                namespace,
                exc,
            )

    def upsert_chunks(
        self,
        *,
        embeddings: list[list[float]],
        texts: list[str],
        session_id: str,
        user_id: str,
        document_id: str,
        source_file_name: str,
        start_index: int = 0,
        created_at: str | None = None,
    ) -> int:
        """Upsert one bounded batch. Does not retain vectors after return."""
        if len(embeddings) != len(texts):
            raise ValueError("embeddings and texts length mismatch")
        if not texts:
            return 0

        created_at = created_at or datetime.now(timezone.utc).isoformat()
        namespace = self._namespace(session_id)
        vectors: list[dict[str, Any]] = []

        for offset, (embedding, text) in enumerate(zip(embeddings, texts)):
            chunk_index = start_index + offset
            vectors.append(
                {
                    "id": f"{document_id}-{chunk_index}",
                    "values": embedding,
                    "metadata": {
                        "sessionId": session_id,
                        "userId": user_id,
                        "documentId": document_id,
                        "chunkIndex": chunk_index,
                        "sourceFileName": source_file_name,
                        # Chunk text only — not the full document.
                        "originalText": text[:_MAX_ORIGINAL_TEXT_CHARS],
                        "createdAt": created_at,
                    },
                }
            )

        self._upsert_with_retry(vectors=vectors, namespace=namespace)
        upserted = len(vectors)
        # Drop local references before returning so GC can reclaim promptly.
        del vectors

        logger.info(
            "[rag.pinecone] upserted batch | count=%s | start_index=%s | session=%s",
            upserted,
            start_index,
            session_id,
        )
        return upserted

    def _upsert_with_retry(
        self,
        *,
        vectors: list[dict[str, Any]],
        namespace: str,
    ) -> None:
        last_error: Exception | None = None
        for attempt in range(1, _UPSERT_MAX_ATTEMPTS + 1):
            try:
                self._index.upsert(vectors=vectors, namespace=namespace)
                return
            except Exception as exc:
                last_error = exc
                if attempt >= _UPSERT_MAX_ATTEMPTS:
                    break
                delay = _UPSERT_RETRY_BASE_DELAY_SEC * attempt
                logger.warning(
                    "[rag.pinecone] upsert failed (attempt %s/%s); retrying in %.1fs | error=%s",
                    attempt,
                    _UPSERT_MAX_ATTEMPTS,
                    delay,
                    exc,
                )
                time.sleep(delay)
        raise RuntimeError(f"Pinecone upsert failed: {last_error}") from last_error

    def query(
        self,
        *,
        embedding: list[float],
        session_id: str,
        user_id: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        top_k = top_k or settings.RAG_TOP_K
        namespace = self._namespace(session_id)

        result = self._index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
            filter={
                "sessionId": {"$eq": session_id},
                "userId": {"$eq": user_id},
            },
        )

        matches = getattr(result, "matches", None) or result.get("matches", [])
        chunks: list[dict[str, Any]] = []

        for match in matches:
            metadata = getattr(match, "metadata", None) or match.get("metadata") or {}
            score = getattr(match, "score", None)
            if score is None and isinstance(match, dict):
                score = match.get("score")

            text = str(metadata.get("originalText") or "").strip()
            if not text:
                continue

            chunks.append(
                {
                    "content": text,
                    "score": score,
                    "chunkIndex": metadata.get("chunkIndex"),
                    "sourceFileName": metadata.get("sourceFileName"),
                    "documentId": metadata.get("documentId"),
                }
            )

        return chunks

    @staticmethod
    def _namespace(session_id: str) -> str:
        return f"session_{session_id}"


_store: PineconeVectorStore | None = None


def get_vector_store() -> PineconeVectorStore:
    global _store
    if _store is None:
        _store = PineconeVectorStore()
    return _store
