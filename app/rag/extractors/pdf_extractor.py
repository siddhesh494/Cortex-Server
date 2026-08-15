from io import BytesIO

from pypdf import PdfReader

from app.rag.extractors.base import BaseDocumentExtractor, ExtractedDocument


class PdfExtractor(BaseDocumentExtractor):
    extensions = frozenset({".pdf"})

    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        return self._extract_reader(PdfReader(BytesIO(data)), filename)

    def extract_from_path(self, path: str, filename: str) -> ExtractedDocument:
        # Parse from disk so the upload byte buffer can be released earlier.
        return self._extract_reader(PdfReader(path), filename)

    @staticmethod
    def _extract_reader(reader: PdfReader, filename: str) -> ExtractedDocument:
        pages: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())

        return ExtractedDocument(
            text="\n\n".join(pages).strip(),
            source_file_name=filename,
            document_type="pdf",
        )
