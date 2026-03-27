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


class TestRecursiveChunkerValidation:
    def test_zero_chunk_size_raises(self):
        try:
            RecursiveChunker(chunk_size=0)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "chunk_size" in str(e)

    def test_negative_overlap_raises(self):
        try:
            RecursiveChunker(chunk_size=100, chunk_overlap=-1)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "chunk_overlap" in str(e)

    def test_overlap_clamped_to_chunk_size(self):
        """Overlap >= chunk_size should be clamped, not error."""
        c = RecursiveChunker(chunk_size=50, chunk_overlap=100)
        assert c.chunk_overlap == 49  # clamped to chunk_size - 1

    def test_valid_params_ok(self):
        c = RecursiveChunker(chunk_size=1, chunk_overlap=0)
        assert c.chunk_size == 1
        assert c.chunk_overlap == 0


class TestRecursiveChunkerEdgeCases:
    def test_unicode_text(self):
        c = RecursiveChunker(chunk_size=100)
        text = "한국어 텍스트입니다.\n\n두 번째 문단입니다.\n\n세 번째 문단."
        chunks = c.chunk(text)
        assert len(chunks) >= 1
        assert all(isinstance(ch, Chunk) for ch in chunks)
        combined = " ".join(ch.content for ch in chunks)
        assert "한국어" in combined

    def test_single_long_word(self):
        """A single word longer than chunk_size must still be split."""
        c = RecursiveChunker(chunk_size=20, chunk_overlap=0)
        text = "A" * 100
        chunks = c.chunk(text)
        assert len(chunks) >= 2
        combined = "".join(ch.content for ch in chunks)
        assert len(combined) >= 100

    def test_overlap_preserves_content(self):
        """With overlap, no content should be lost."""
        c = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        text = "Word " * 60
        chunks = c.chunk(text)
        assert len(chunks) >= 2
        # Every chunk should have content
        for ch in chunks:
            assert len(ch.content.strip()) > 0

    def test_only_whitespace_separators(self):
        c = RecursiveChunker(chunk_size=30, chunk_overlap=0)
        text = "   \n\n   \n   "
        assert c.chunk(text) == []

    def test_newline_only_text(self):
        c = RecursiveChunker(chunk_size=50)
        text = "\n" * 100
        assert c.chunk(text) == []


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
