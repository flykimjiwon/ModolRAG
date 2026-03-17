"""Test document parsers — 6 formats."""
import os
import tempfile
from modolrag.parsers import get_parser, ParsedDocument
from modolrag.parsers.base import ParserBase


def _write_tmp(content: str, suffix: str) -> str:
    f = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    f.write(content)
    f.close()
    return f.name


class TestTextParser:
    def test_parse_basic(self):
        path = _write_tmp("Hello world.\nSecond line.", ".txt")
        p = get_parser("text/plain")
        result = p.parse(path)
        assert isinstance(result, ParsedDocument)
        assert "Hello world" in result.text
        os.unlink(path)

    def test_parse_empty(self):
        path = _write_tmp("", ".txt")
        p = get_parser("text/plain")
        result = p.parse(path)
        assert result.text == "" or result.text.strip() == ""
        os.unlink(path)

    def test_supported_mime(self):
        p = get_parser("text/plain")
        assert isinstance(p, ParserBase)


class TestMarkdownParser:
    def test_parse_basic(self):
        md = "# Title\n\nSome content here.\n\n## Section 2\n\nMore content."
        path = _write_tmp(md, ".md")
        p = get_parser("text/markdown")
        result = p.parse(path)
        assert "Title" in result.text
        assert "Section 2" in result.text
        os.unlink(path)

    def test_frontmatter(self):
        md = "---\ntitle: Test\nauthor: Me\n---\n\n# Hello\n\nContent."
        path = _write_tmp(md, ".md")
        p = get_parser("text/markdown")
        result = p.parse(path)
        assert "Hello" in result.text
        os.unlink(path)


class TestParserFactory:
    def test_known_types(self):
        for mime in ["text/plain", "text/markdown", "application/pdf",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
            p = get_parser(mime)
            assert isinstance(p, ParserBase), f"No parser for {mime}"

    def test_unknown_fallback(self):
        p = get_parser("application/octet-stream")
        assert isinstance(p, ParserBase)
