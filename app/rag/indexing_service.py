"""Document injection (indexing) pipeline for RAG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.core.exceptions import EmptyDocumentException, RagIndexingException
from app.core.logger import logger
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_documents
from app.rag.extractors import extract_document
from app.rag.pinecone_store import get_vector_store
from app.rag.summary import generate_rag_summary


@dataclass
class IndexingResult:
    document_id: str
    chunk_count: int
    rag_summary: dict[str, Any]
    source_file_name: str
    excerpt: str


class RagIndexingService:
    """
    Indexing pipeline:

    extract → semantic chunk → embed → Pinecone upsert → RAGSummary
    """

    async def index_document(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        session_id: str,
        user_id: str,
    ) -> IndexingResult:
        try:
            extracted = extract_document(file_bytes, filename)
            logger.info(f"[rag.indexing] | filename: {filename} | Extracted text")
        except Exception as exc:
            # UnsupportedFileTypeException and others bubble as-is when typed.
            if hasattr(exc, "message"):
                raise
            raise RagIndexingException(f"Failed to read document: {exc}") from exc

        if not extracted.text.strip():
            raise EmptyDocumentException()

        chunks = chunk_text(extracted.text)
        logger.info(f"[rag.indexing] | filename: {filename} | Chunks: {len(chunks)}")
        if not chunks:
            raise EmptyDocumentException()

        try:
            embeddings = embed_documents(chunks)
            logger.info(f"[rag.indexing] | filename: {filename} | Embeddings: {embeddings}")
        except Exception as exc:
            raise RagIndexingException(f"Failed to embed document chunks: {exc}") from exc

        document_id = uuid4().hex

        try:
            store = get_vector_store()
            store.upsert_chunks(
                embeddings=embeddings,
                texts=chunks,
                session_id=session_id,
                user_id=user_id,
                document_id=document_id,
                source_file_name=extracted.source_file_name,
            )
        except Exception as exc:
            raise RagIndexingException(f"Failed to store vectors in Pinecone: {exc}") from exc

        rag_summary = generate_rag_summary(
            document_text=extracted.text,
            source_file_name=extracted.source_file_name,
        )

        logger.info(
            "[rag.indexing] complete | session=%s | document=%s | chunks=%s",
            session_id,
            document_id,
            len(chunks),
        )

        return IndexingResult(
            document_id=document_id,
            chunk_count=len(chunks),
            rag_summary=rag_summary,
            source_file_name=extracted.source_file_name,
            excerpt=extracted.text[:1500],
        )
