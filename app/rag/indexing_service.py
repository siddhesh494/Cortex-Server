"""Document injection (indexing) pipeline for RAG.

Memory strategy (Render Free ~512 MB):
  extract text → semantic chunk → embed small batches → Pinecone upsert
  → drop batch refs → next batch

Never holds all embeddings or all Pinecone vectors for a document at once.
"""

from __future__ import annotations

import asyncio
import gc
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import settings
from app.core.exceptions import EmptyDocumentException, RagIndexingException
from app.core.logger import logger
from app.rag.chunking import iter_text_chunks
from app.rag.embeddings import embed_documents
from app.rag.extractors import extract_document, extract_document_from_path
from app.rag.pinecone_store import get_vector_store
from app.rag.summary import generate_rag_summary

# Only one heavy ingestion at a time on a small Render instance.
_ingestion_semaphore = asyncio.Semaphore(1)


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

    extract → semantic chunk → embed (batched) → Pinecone upsert → RAGSummary
    """

    async def index_document(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        session_id: str,
        user_id: str,
    ) -> IndexingResult:
        async with _ingestion_semaphore:
            return await asyncio.to_thread(
                self._index_document_sync,
                file_bytes,
                filename,
                session_id,
                user_id,
            )

    def _index_document_sync(
        self,
        file_bytes: bytes,
        filename: str,
        session_id: str,
        user_id: str,
    ) -> IndexingResult:
        size_mb = len(file_bytes) / (1024 * 1024)
        batch_size = max(1, int(settings.EMBEDDING_BATCH_SIZE))
        concurrency = max(1, int(settings.EMBEDDING_CONCURRENCY))

        logger.info(
            "[rag.indexing] started | filename=%s | size_mb=%.2f | "
            "batch_size=%s | concurrency=%s",
            filename,
            size_mb,
            batch_size,
            concurrency,
        )

        if concurrency != 1:
            logger.info(
                "[rag.indexing] EMBEDDING_CONCURRENCY=%s requested; "
                "using serial batches (concurrency=1) for low memory",
                concurrency,
            )

        temp_path: str | None = None
        try:
            temp_path = self._write_temp_file(file_bytes, filename)
            # Release upload bytes as soon as they are on disk.
            file_bytes = b""

            try:
                extracted = extract_document_from_path(temp_path, filename)
            except Exception as exc:
                if hasattr(exc, "message"):
                    raise
                raise RagIndexingException(f"Failed to read document: {exc}") from exc
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        if not extracted.text.strip():
            raise EmptyDocumentException()

        source_file_name = extracted.source_file_name
        excerpt = extracted.text[:1500]
        # Summary only needs a bounded excerpt — avoid passing the full doc later.
        summary_excerpt = extracted.text[:6000]
        document_text = extracted.text
        del extracted

        document_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()

        try:
            store = get_vector_store()
            # Idempotent re-try: clear orphans from a previous crashed ingest.
            store.clear_session_namespace(session_id)

            chunk_count = 0
            batch_texts: list[str] = []
            batch_start_index = 0
            batch_number = 0

            for chunk_index, chunk in iter_text_chunks(document_text):
                if not batch_texts:
                    batch_start_index = chunk_index
                batch_texts.append(chunk)

                if len(batch_texts) >= batch_size:
                    batch_number += 1
                    self._embed_and_upsert_batch(
                        store=store,
                        batch_texts=batch_texts,
                        batch_number=batch_number,
                        start_index=batch_start_index,
                        session_id=session_id,
                        user_id=user_id,
                        document_id=document_id,
                        source_file_name=source_file_name,
                        created_at=created_at,
                    )
                    chunk_count += len(batch_texts)
                    batch_texts = []
                    # Reclaim batch + embedding memory between large steps.
                    gc.collect()

            if batch_texts:
                batch_number += 1
                self._embed_and_upsert_batch(
                    store=store,
                    batch_texts=batch_texts,
                    batch_number=batch_number,
                    start_index=batch_start_index,
                    session_id=session_id,
                    user_id=user_id,
                    document_id=document_id,
                    source_file_name=source_file_name,
                    created_at=created_at,
                )
                chunk_count += len(batch_texts)
                batch_texts = []
                gc.collect()

        except RagIndexingException:
            raise
        except Exception as exc:
            raise RagIndexingException(
                f"Failed to embed/store document chunks: {exc}"
            ) from exc
        finally:
            # Full document text is no longer needed after chunk streaming.
            document_text = ""

        if chunk_count == 0:
            raise EmptyDocumentException()

        rag_summary = generate_rag_summary(
            document_text=summary_excerpt,
            source_file_name=source_file_name,
        )

        logger.info(
            "[rag.indexing] completed | session=%s | document=%s | chunks=%s | batches=%s",
            session_id,
            document_id,
            chunk_count,
            batch_number,
        )

        return IndexingResult(
            document_id=document_id,
            chunk_count=chunk_count,
            rag_summary=rag_summary,
            source_file_name=source_file_name,
            excerpt=excerpt,
        )

    def _embed_and_upsert_batch(
        self,
        *,
        store: Any,
        batch_texts: list[str],
        batch_number: int,
        start_index: int,
        session_id: str,
        user_id: str,
        document_id: str,
        source_file_name: str,
        created_at: str,
    ) -> None:
        logger.info(
            "[rag.indexing] batch %s embedding | size=%s | start_index=%s",
            batch_number,
            len(batch_texts),
            start_index,
        )
        try:
            embeddings = embed_documents(batch_texts)
        except Exception as exc:
            raise RagIndexingException(
                f"Failed to embed document batch {batch_number}: {exc}"
            ) from exc

        logger.info(
            "[rag.indexing] batch %s embedded | size=%s",
            batch_number,
            len(embeddings),
        )

        try:
            store.upsert_chunks(
                embeddings=embeddings,
                texts=batch_texts,
                session_id=session_id,
                user_id=user_id,
                document_id=document_id,
                source_file_name=source_file_name,
                start_index=start_index,
                created_at=created_at,
            )
        except Exception as exc:
            raise RagIndexingException(
                f"Failed to upsert document batch {batch_number} to Pinecone: {exc}"
            ) from exc

        logger.info(
            "[rag.indexing] batch %s upserted to Pinecone | size=%s",
            batch_number,
            len(batch_texts),
        )
        # Explicitly drop large refs before caller clears the list.
        del embeddings

    @staticmethod
    def _write_temp_file(file_bytes: bytes, filename: str) -> str:
        suffix = Path(filename or "").suffix.lower() or ".bin"
        fd, path = tempfile.mkstemp(prefix="cortex_rag_", suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(file_bytes)
        except Exception:
            try:
                os.unlink(path)
            except OSError:
                pass
            raise
        return path
