from app.rag.extractors.base import BaseDocumentExtractor, ExtractedDocument


class TxtExtractor(BaseDocumentExtractor):
    extensions = frozenset({".txt"})

    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = data.decode("utf-8", errors="replace")

        return ExtractedDocument(
            text=text.strip(),
            source_file_name=filename,
            document_type="text",
        )
