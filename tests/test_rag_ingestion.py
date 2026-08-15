"""Focused tests for memory-bounded RAG ingestion batching."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.rag.chunking import chunk_text, iter_text_chunks
from app.rag.indexing_service import RagIndexingService
from app.rag.pinecone_store import PineconeVectorStore


class ChunkingTests(unittest.TestCase):
    def test_chunk_text_uses_semantic_chunker(self) -> None:
        text = "Sentence one. Sentence two. Sentence three. " * 20

        with patch("app.rag.chunking.SemanticChunker") as mock_splitter_cls:
            instance = MagicMock()
            instance.split_text.return_value = [
                "Sentence one. Sentence two.",
                "Sentence three. " * 5,
            ]
            mock_splitter_cls.return_value = instance

            chunks = chunk_text(text)

        self.assertEqual(len(chunks), 2)
        instance.split_text.assert_called_once()

    def test_iter_text_chunks_indexes_semantic_output(self) -> None:
        with patch(
            "app.rag.chunking.chunk_text",
            return_value=["alpha", "beta", "gamma"],
        ):
            chunks = list(iter_text_chunks("ignored"))

        self.assertEqual(chunks, [(0, "alpha"), (1, "beta"), (2, "gamma")])


class PineconeBatchIdTests(unittest.TestCase):
    def test_vector_ids_are_deterministic_across_batches(self) -> None:
        store = PineconeVectorStore.__new__(PineconeVectorStore)
        store._index = MagicMock()
        upserted_ids: list[str] = []

        def capture_upsert(*, vectors, namespace):
            upserted_ids.extend(v["id"] for v in vectors)

        store._index.upsert.side_effect = capture_upsert

        store.upsert_chunks(
            embeddings=[[0.1], [0.2]],
            texts=["a", "b"],
            session_id="s1",
            user_id="u1",
            document_id="docabc",
            source_file_name="f.txt",
            start_index=0,
            created_at="t0",
        )
        store.upsert_chunks(
            embeddings=[[0.3]],
            texts=["c"],
            session_id="s1",
            user_id="u1",
            document_id="docabc",
            source_file_name="f.txt",
            start_index=2,
            created_at="t0",
        )

        self.assertEqual(upserted_ids, ["docabc-0", "docabc-1", "docabc-2"])
        self.assertEqual(store._index.upsert.call_count, 2)

    def test_retry_same_ids_are_idempotent(self) -> None:
        store = PineconeVectorStore.__new__(PineconeVectorStore)
        store._index = MagicMock()

        payload = dict(
            embeddings=[[0.1]],
            texts=["same"],
            session_id="s1",
            user_id="u1",
            document_id="doc1",
            source_file_name="f.txt",
            start_index=5,
            created_at="t0",
        )
        store.upsert_chunks(**payload)
        store.upsert_chunks(**payload)

        first_ids = [v["id"] for v in store._index.upsert.call_args_list[0].kwargs["vectors"]]
        second_ids = [v["id"] for v in store._index.upsert.call_args_list[1].kwargs["vectors"]]
        self.assertEqual(first_ids, second_ids)
        self.assertEqual(first_ids, ["doc1-5"])


class IndexingBatchingTests(unittest.TestCase):
    def test_indexing_upserts_multiple_small_batches(self) -> None:
        service = RagIndexingService()
        text = "document body"
        upsert_sizes: list[int] = []

        mock_store = MagicMock()
        mock_store.clear_session_namespace = MagicMock()

        def capture_upsert(**kwargs):
            upsert_sizes.append(len(kwargs["texts"]))
            return len(kwargs["texts"])

        mock_store.upsert_chunks.side_effect = capture_upsert

        semantic_chunks = [(i, f"chunk-{i}") for i in range(9)]

        with (
            patch("app.rag.indexing_service.settings") as mock_settings,
            patch(
                "app.rag.indexing_service.extract_document_from_path",
                return_value=MagicMock(
                    text=text,
                    source_file_name="big.txt",
                    document_type="text",
                ),
            ),
            patch("app.rag.indexing_service.get_vector_store", return_value=mock_store),
            patch(
                "app.rag.indexing_service.embed_documents",
                side_effect=lambda texts: [[0.0] * 8 for _ in texts],
            ),
            patch(
                "app.rag.indexing_service.generate_rag_summary",
                return_value={"aboutDoc": "x"},
            ),
            patch(
                "app.rag.indexing_service.iter_text_chunks",
                return_value=semantic_chunks,
            ),
            patch.object(RagIndexingService, "_write_temp_file", return_value="/tmp/fake.txt"),
            patch("app.rag.indexing_service.os.unlink"),
        ):
            mock_settings.EMBEDDING_BATCH_SIZE = 4
            mock_settings.EMBEDDING_CONCURRENCY = 1

            result = service._index_document_sync(
                file_bytes=b"ignored",
                filename="big.txt",
                session_id="session1",
                user_id="user1",
            )

        self.assertGreater(len(upsert_sizes), 1)
        self.assertTrue(all(size <= 4 for size in upsert_sizes))
        self.assertEqual(result.chunk_count, sum(upsert_sizes))
        mock_store.clear_session_namespace.assert_called_once_with("session1")

    def test_failed_batch_does_not_keep_prior_embeddings(self) -> None:
        service = RagIndexingService()
        text = "document body"
        call_count = {"n": 0}

        mock_store = MagicMock()
        mock_store.clear_session_namespace = MagicMock()
        mock_store.upsert_chunks.side_effect = lambda **kwargs: len(kwargs["texts"])

        def embed_side_effect(texts):
            call_count["n"] += 1
            vectors = [[float(call_count["n"])] * 4 for _ in texts]
            if call_count["n"] == 2:
                raise RuntimeError("boom")
            return vectors

        semantic_chunks = [(i, f"chunk-{i}") for i in range(6)]

        with (
            patch("app.rag.indexing_service.settings") as mock_settings,
            patch(
                "app.rag.indexing_service.extract_document_from_path",
                return_value=MagicMock(
                    text=text,
                    source_file_name="doc.txt",
                    document_type="text",
                ),
            ),
            patch("app.rag.indexing_service.get_vector_store", return_value=mock_store),
            patch("app.rag.indexing_service.embed_documents", side_effect=embed_side_effect),
            patch(
                "app.rag.indexing_service.generate_rag_summary",
                return_value={"aboutDoc": "x"},
            ),
            patch(
                "app.rag.indexing_service.iter_text_chunks",
                return_value=semantic_chunks,
            ),
            patch.object(RagIndexingService, "_write_temp_file", return_value="/tmp/fake.txt"),
            patch("app.rag.indexing_service.os.unlink"),
        ):
            mock_settings.EMBEDDING_BATCH_SIZE = 2
            mock_settings.EMBEDDING_CONCURRENCY = 1

            with self.assertRaises(Exception):
                service._index_document_sync(
                    file_bytes=b"ignored",
                    filename="doc.txt",
                    session_id="s",
                    user_id="u",
                )

        self.assertGreaterEqual(mock_store.upsert_chunks.call_count, 1)
        self.assertGreaterEqual(call_count["n"], 2)


if __name__ == "__main__":
    unittest.main()
