"""Simple RAG retrieval: embed query → Pinecone similarity search."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.logger import logger
from app.rag.embeddings import embed_query
from app.rag.pinecone_store import get_vector_store


class RagRetrievalService:
    def retrieve(
        self,
        *,
        query: str,
        session_id: str,
        user_id: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        cleaned = (query or "").strip()
        if not cleaned:
            return []

        embedding = embed_query(cleaned)
        store = get_vector_store()
        chunks = store.query(
            embedding=embedding,
            session_id=session_id,
            user_id=user_id,
            top_k=top_k or settings.RAG_TOP_K,
        )

        logger.info(
            "[rag.retrieval] query done | session=%s | hits=%s",
            session_id,
            len(chunks),
        )
        return chunks
