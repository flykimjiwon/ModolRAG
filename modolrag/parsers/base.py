"""Base parser interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    """Result of parsing a document."""
    text: str
    metadata: dict = field(default_factory=dict)
    pages: list[str] = field(default_factory=list)


class ParserBase(ABC):
    """Abstract base for document parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document file and return a ParsedDocument."""
        ...

    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        """Return list of MIME types this parser supports."""
        ...
