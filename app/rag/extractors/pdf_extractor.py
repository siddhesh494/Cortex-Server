from io import BytesIO

from pypdf import PdfReader

from app.rag.extractors.base import BaseDocumentExtractor, ExtractedDocument


class PdfExtractor(BaseDocumentExtractor):
    extensions = frozenset({".pdf"})

    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        reader = PdfReader(BytesIO(data))
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
