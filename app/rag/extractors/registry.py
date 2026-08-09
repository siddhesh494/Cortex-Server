from pathlib import Path

from app.core.exceptions import UnsupportedFileTypeException
from app.rag.extractors.base import BaseDocumentExtractor, ExtractedDocument
from app.rag.extractors.pdf_extractor import PdfExtractor
from app.rag.extractors.txt_extractor import TxtExtractor

_EXTRACTORS: list[BaseDocumentExtractor] = [
    PdfExtractor(),
    TxtExtractor(),
]

_BY_EXTENSION: dict[str, BaseDocumentExtractor] = {
    ext: extractor
    for extractor in _EXTRACTORS
    for ext in extractor.extensions
}


def supported_extensions() -> list[str]:
    return sorted(_BY_EXTENSION.keys())


def extract_document(data: bytes, filename: str) -> ExtractedDocument:
    extension = Path(filename or "").suffix.lower()
    extractor = _BY_EXTENSION.get(extension)

    if extractor is None:
        raise UnsupportedFileTypeException(filename)

    return extractor.extract(data, filename)
