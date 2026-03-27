"""Test chunking engine — recursive, page, semantic."""
from unittest.mock import AsyncMock
from modolrag.core.chunker import RecursiveChunker, PageChunker, SemanticChunker, Chunk, get_chunker


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


class TestSemanticChunker:
    def _make_chunker(self):
        mock_embedder = AsyncMock()
        return SemanticChunker(embedder=mock_embedder, threshold=0.5)

    def test_short_text(self):
        c = self._make_chunker()
        chunks = c.chunk("Short text.")
        assert len(chunks) == 1

    def test_empty_text(self):
        c = self._make_chunker()
        assert c.chunk("") == []
        assert c.chunk("   ") == []

    def test_multiple_sentences(self):
        c = self._make_chunker()
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = c.chunk(text)
        assert len(chunks) >= 1
        # All content should be preserved
        combined = " ".join(ch.content for ch in chunks)
        assert "First" in combined
        assert "Fourth" in combined

    def test_chunk_indices_sequential(self):
        c = self._make_chunker()
        text = ". ".join(f"Sentence number {i}" for i in range(20))
        chunks = c.chunk(text)
        for i, ch in enumerate(chunks):
            assert ch.chunk_index == i

    def test_cosine_similarity_static(self):
        sim = SemanticChunker._cosine_similarity([1, 0, 0], [1, 0, 0])
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        sim = SemanticChunker._cosine_similarity([1, 0], [0, 1])
        assert abs(sim) < 1e-6

    def test_cosine_similarity_zero_vector(self):
        sim = SemanticChunker._cosine_similarity([0, 0], [1, 1])
        assert sim == 0.0


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

    def test_semantic_requires_embedder(self):
        try:
            get_chunker("semantic")
            assert False, "Should raise"
        except ValueError as e:
            assert "embedder" in str(e)

    def test_semantic_with_embedder(self):
        mock_embedder = AsyncMock()
        c = get_chunker("semantic", embedder=mock_embedder)
        assert isinstance(c, SemanticChunker)

    def test_recursive_custom_params(self):
        c = get_chunker("recursive", chunk_size=256, chunk_overlap=32)
        assert isinstance(c, RecursiveChunker)
        assert c.chunk_size == 256
        assert c.chunk_overlap == 32

    def test_default_is_recursive(self):
        c = get_chunker()
        assert isinstance(c, RecursiveChunker)
