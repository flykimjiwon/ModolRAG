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


__all__ = ["ParserBase", "ParsedDocument", "get_parser"]
