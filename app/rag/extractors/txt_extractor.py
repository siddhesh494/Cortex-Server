from pathlib import Path

from app.rag.extractors.base import BaseDocumentExtractor, ExtractedDocument


class TxtExtractor(BaseDocumentExtractor):
    extensions = frozenset({".txt"})

    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        return ExtractedDocument(
            text=self._decode(data),
            source_file_name=filename,
            document_type="text",
        )

    def extract_from_path(self, path: str, filename: str) -> ExtractedDocument:
        raw = Path(path).read_bytes()
        return self.extract(raw, filename)

    @staticmethod
    def _decode(data: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return data.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace").strip()
