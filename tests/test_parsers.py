"""Test document parsers — 6 formats."""
import os
import tempfile
from modolrag.parsers import get_parser, ParsedDocument, mime_from_extension
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


class TestMarkdownFrontmatter:
    def test_frontmatter_extracted(self):
        from modolrag.parsers.markdown import _parse_frontmatter
        content = "---\ntitle: Test\nauthor: Me\n---\n\n# Hello"
        fm, body = _parse_frontmatter(content)
        assert "title" in fm
        assert fm["title"] == "Test" or fm["title"] == "Test"
        assert "Hello" in body

    def test_no_frontmatter(self):
        from modolrag.parsers.markdown import _parse_frontmatter
        content = "# No frontmatter here"
        fm, body = _parse_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_empty_frontmatter(self):
        from modolrag.parsers.markdown import _parse_frontmatter
        content = "---\n---\n\nBody text"
        fm, body = _parse_frontmatter(content)
        assert fm == {}
        assert "Body text" in body

    def test_metadata_contains_frontmatter(self):
        md = "---\ntitle: Hello\ntags: test\n---\n\nContent here."
        path = _write_tmp(md, ".md")
        p = get_parser("text/markdown")
        result = p.parse(path)
        assert "frontmatter" in result.metadata
        fm = result.metadata["frontmatter"]
        assert fm.get("title") == "Hello"
        os.unlink(path)

    def test_markdown_h2_split(self):
        md = "# Title\n\nIntro.\n\n## Section A\n\nContent A.\n\n## Section B\n\nContent B."
        path = _write_tmp(md, ".md")
        p = get_parser("text/markdown")
        result = p.parse(path)
        assert len(result.pages) >= 2
        os.unlink(path)


class TestMarkdownEncodingFallback:
    def test_latin1_file(self):
        """Markdown parser should fall back to latin-1 for non-UTF8 files."""
        f = tempfile.NamedTemporaryFile(mode='wb', suffix=".md", delete=False)
        # \xe9 is é in latin-1 but invalid continuation byte in UTF-8
        f.write(b"# H\xe9llo\n\nCaf\xe9 content.")
        f.close()
        p = get_parser("text/markdown")
        result = p.parse(f.name)
        assert "content" in result.text.lower()
        os.unlink(f.name)

    def test_nonexistent_file(self):
        p = get_parser("text/markdown")
        result = p.parse("/tmp/nonexistent_modolrag_test_file.md")
        assert "error" in result.metadata


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


class TestParsedDocument:
    def test_basic_creation(self):
        doc = ParsedDocument(text="hello")
        assert doc.text == "hello"
        assert doc.metadata == {}
        assert doc.pages == []

    def test_with_pages(self):
        doc = ParsedDocument(text="full text", pages=["page 1", "page 2"])
        assert len(doc.pages) == 2

    def test_with_metadata(self):
        doc = ParsedDocument(text="x", metadata={"author": "test", "page_count": 5})
        assert doc.metadata["author"] == "test"
        assert doc.metadata["page_count"] == 5


class TestMimeFromExtension:
    def test_known_extensions(self):
        assert mime_from_extension("doc.pdf") == "application/pdf"
        assert mime_from_extension("notes.md") == "text/markdown"
        assert mime_from_extension("data.xlsx") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert mime_from_extension("readme.txt") == "text/plain"
        assert mime_from_extension("slides.pptx") == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        assert mime_from_extension("report.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_case_insensitive(self):
        assert mime_from_extension("FILE.PDF") == "application/pdf"
        assert mime_from_extension("NOTE.MD") == "text/markdown"

    def test_unknown_extension(self):
        assert mime_from_extension("file.xyz") == "application/octet-stream"
        assert mime_from_extension("noext") == "application/octet-stream"

    def test_markdown_alias(self):
        assert mime_from_extension("doc.markdown") == "text/markdown"


class TestTextParserEdgeCases:
    def test_unicode_korean(self):
        """Text parser must handle Korean UTF-8 without mangling."""
        path = _write_tmp("안녕하세요.\n두 번째 줄.", ".txt")
        p = get_parser("text/plain")
        result = p.parse(path)
        assert "안녕하세요" in result.text
        os.unlink(path)

    def test_nonexistent_file(self):
        """Nonexistent file should return error in metadata, not raise."""
        p = get_parser("text/plain")
        result = p.parse("/tmp/nonexistent_modolrag_xyz_test.txt")
        assert "error" in result.metadata

    def test_multiline_content(self):
        """All lines should be present in parsed text."""
        lines = [f"Line {i}" for i in range(50)]
        path = _write_tmp("\n".join(lines), ".txt")
        p = get_parser("text/plain")
        result = p.parse(path)
        assert "Line 0" in result.text
        assert "Line 49" in result.text
        os.unlink(path)


class TestParsedDocumentEdgeCases:
    def test_pages_default_empty_list(self):
        doc = ParsedDocument(text="hello")
        assert doc.pages == []
        assert isinstance(doc.pages, list)

    def test_metadata_default_empty_dict(self):
        doc = ParsedDocument(text="x")
        assert doc.metadata == {}
        assert isinstance(doc.metadata, dict)

    def test_independent_metadata_instances(self):
        """Two ParsedDocuments should not share the same metadata dict."""
        doc1 = ParsedDocument(text="a")
        doc2 = ParsedDocument(text="b")
        doc1.metadata["key"] = "val"
        assert "key" not in doc2.metadata

    def test_independent_pages_instances(self):
        """Two ParsedDocuments should not share the same pages list."""
        doc1 = ParsedDocument(text="a")
        doc2 = ParsedDocument(text="b")
        doc1.pages.append("page1")
        assert doc2.pages == []
