"""Test chunking engine — recursive, page, semantic."""
from modolrag.core.chunker import RecursiveChunker, PageChunker, Chunk, get_chunker


class TestRecursiveChunker:
    def test_short_text(self):
        c = RecursiveChunker(chunk_size=100)
        chunks = c.chunk("Short text.")
        assert len(chunks) == 1
        assert chunks[0].content == "Short text."

    def test_long_text_splits(self):
        c = RecursiveChunker(chunk_size=50, chunk_overlap=0)
        text = "A" * 200
        chunks = c.chunk(text)
        assert len(chunks) >= 2

    def test_paragraph_boundary(self):
        c = RecursiveChunker(chunk_size=100)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = c.chunk(text)
        assert len(chunks) >= 1
        assert all(isinstance(ch, Chunk) for ch in chunks)

    def test_chunk_index(self):
        c = RecursiveChunker(chunk_size=30, chunk_overlap=0)
        chunks = c.chunk("Word " * 50)
        for i, ch in enumerate(chunks):
            assert ch.chunk_index == i

    def test_empty_text(self):
        c = RecursiveChunker()
        assert c.chunk("") == []
        assert c.chunk("   ") == []


class TestPageChunker:
    def test_form_feed(self):
        c = PageChunker()
        chunks = c.chunk("Page 1\fPage 2\fPage 3")
        assert len(chunks) == 3

    def test_triple_newline(self):
        c = PageChunker()
        chunks = c.chunk("Section 1\n\n\nSection 2\n\n\nSection 3")
        assert len(chunks) == 3

    def test_pages_param(self):
        c = PageChunker()
        chunks = c.chunk("ignored", pages=["Page A", "Page B"])
        assert len(chunks) == 2
        assert chunks[0].content == "Page A"


class TestFactory:
    def test_recursive(self):
        c = get_chunker("recursive", chunk_size=100)
        assert isinstance(c, RecursiveChunker)

    def test_page(self):
        c = get_chunker("page")
        assert isinstance(c, PageChunker)

    def test_unknown_raises(self):
        try:
            get_chunker("nonexistent")
            assert False, "Should raise"
        except ValueError:
            pass
