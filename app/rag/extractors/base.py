from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractedDocument:
    text: str
    source_file_name: str
    document_type: str


class BaseDocumentExtractor(ABC):
    """Pluggable text extractor — add DOCX/MD/CSV by subclassing."""

    extensions: frozenset[str] = frozenset()

    @abstractmethod
    def extract(self, data: bytes, filename: str) -> ExtractedDocument:
        """Return plain text extracted from the uploaded file bytes."""
