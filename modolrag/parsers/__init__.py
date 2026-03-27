"""Document parsers."""
from modolrag.parsers.base import ParserBase, ParsedDocument

_MIME_MAP: dict[str, type[ParserBase]] = {}


def _register() -> None:
    from modolrag.parsers.pdf import PdfParser
    from modolrag.parsers.docx import DocxParser
    from modolrag.parsers.xlsx import XlsxParser
    from modolrag.parsers.pptx import PptxParser
    from modolrag.parsers.markdown import MarkdownParser
    from modolrag.parsers.text import TextParser

    for cls in [PdfParser, DocxParser, XlsxParser, PptxParser, MarkdownParser, TextParser]:
        for mime in cls().supported_mime_types():
            _MIME_MAP[mime] = cls


def get_parser(mime_type: str) -> ParserBase:
    """Return a parser instance for the given MIME type.

    Falls back to TextParser for unknown MIME types.
    """
    if not _MIME_MAP:
        _register()
    parser_cls = _MIME_MAP.get(mime_type)
    if parser_cls is None:
        from modolrag.parsers.text import TextParser
        return TextParser()
    return parser_cls()


_EXT_TO_MIME: dict[str, str] = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def mime_from_extension(filename: str) -> str:
    """Infer MIME type from file extension. Returns 'application/octet-stream' for unknown."""
    import os
    ext = os.path.splitext(filename)[1].lower()
    return _EXT_TO_MIME.get(ext, "application/octet-stream")


__all__ = ["ParserBase", "ParsedDocument", "get_parser", "mime_from_extension"]
