"""Text chunking strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modolrag.core.embedder import EmbedderBase


@dataclass
class Chunk:
    """A text chunk with metadata."""

    content: str
    chunk_index: int
    chunk_level: int = 0  # 0=leaf, 1=parent
    parent_index: int | None = None
    metadata: dict = field(default_factory=dict)


class ChunkerBase(ABC):
    @abstractmethod
    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        ...


class RecursiveChunker(ChunkerBase):
    """Split text recursively using separator hierarchy."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 51):
        if chunk_size < 1:
            raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be >= 0, got {chunk_overlap}")
        self.chunk_size = chunk_size
        # Clamp overlap to be strictly less than chunk_size
        self.chunk_overlap = min(chunk_overlap, chunk_size - 1)
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        raw_chunks = self._split_recursive(text, self.separators)
        # Create parent-child structure
        chunks = []
        for i, content in enumerate(raw_chunks):
            chunks.append(Chunk(content=content, chunk_index=i, chunk_level=0))
        return chunks

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        # Find the best separator
        separator = separators[-1] if separators else ""
        for sep in separators:
            if sep in text:
                separator = sep
                break

        # Split by separator
        if separator:
            parts = text.split(separator)
        else:
            # Character-level split
            parts = [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
            ]
            return [p.strip() for p in parts if p.strip()]

        # Merge small parts into chunks
        chunks: list[str] = []
        current = ""
        for part in parts:
            candidate = (current + separator + part).strip() if current else part.strip()
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # If single part exceeds chunk_size, recurse with next separator
                if len(part.strip()) > self.chunk_size:
                    next_seps = (
                        separators[separators.index(separator) + 1 :]
                        if separator in separators
                        else separators[1:]
                    )
                    chunks.extend(self._split_recursive(part, next_seps))
                    current = ""
                else:
                    current = part.strip()
        if current:
            chunks.append(current)

        # Add overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks)

        return [c for c in chunks if c.strip()]

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            overlap_text = prev[-self.chunk_overlap :] if len(prev) > self.chunk_overlap else prev
            # Find word boundary in overlap
            space_idx = overlap_text.find(" ")
            if space_idx > 0:
                overlap_text = overlap_text[space_idx + 1 :]
            result.append(overlap_text + " " + chunks[i])
        return result


class PageChunker(ChunkerBase):
    """Split by pages (from ParsedDocument.pages)."""

    def chunk(self, text: str, pages: list[str] | None = None, **kwargs) -> list[Chunk]:
        if pages:
            return [Chunk(content=p, chunk_index=i) for i, p in enumerate(pages) if p.strip()]
        # Fallback: split by form feed or double newline
        parts = text.split("\f") if "\f" in text else text.split("\n\n\n")
        return [Chunk(content=p.strip(), chunk_index=i) for i, p in enumerate(parts) if p.strip()]


class SemanticChunker(ChunkerBase):
    """Split by semantic similarity between sentences."""

    def __init__(self, embedder: EmbedderBase, threshold: float = 0.5):
        self.embedder = embedder
        self.threshold = threshold

    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        # Split into sentences
        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
        if len(sentences) <= 1:
            return [Chunk(content=text, chunk_index=0)] if text.strip() else []

        # Synchronous fallback — real semantic chunking uses embed_and_chunk()
        chunks: list[Chunk] = []
        current = sentences[0]
        idx = 0
        for s in sentences[1:]:
            if len(current) + len(s) < 512:
                current += ". " + s
            else:
                chunks.append(Chunk(content=current + ".", chunk_index=idx))
                current = s
                idx += 1
        if current:
            chunks.append(
                Chunk(content=current + "." if not current.endswith(".") else current, chunk_index=idx)
            )
        return chunks

    async def embed_and_chunk(self, text: str) -> list[Chunk]:
        """Async version that uses embeddings for semantic splitting."""
        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
        if len(sentences) <= 1:
            return [Chunk(content=text, chunk_index=0)] if text.strip() else []

        embeddings = await self.embedder.embed_batch(sentences)

        # Compute cosine similarity between consecutive sentences
        chunks: list[Chunk] = []
        current_group = [sentences[0]]
        idx = 0

        for i in range(1, len(sentences)):
            sim = self._cosine_similarity(embeddings[i - 1], embeddings[i])
            if sim < self.threshold:
                # Split here
                chunks.append(Chunk(content=". ".join(current_group) + ".", chunk_index=idx))
                current_group = [sentences[i]]
                idx += 1
            else:
                current_group.append(sentences[i])

        if current_group:
            chunks.append(Chunk(content=". ".join(current_group) + ".", chunk_index=idx))

        return chunks

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        import math

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


def get_chunker(strategy: str = "recursive", **kwargs) -> ChunkerBase:
    """Factory function."""
    if strategy == "recursive":
        return RecursiveChunker(
            chunk_size=kwargs.get("chunk_size", 512),
            chunk_overlap=kwargs.get("chunk_overlap", 51),
        )
    elif strategy == "page":
        return PageChunker()
    elif strategy == "semantic":
        embedder = kwargs.get("embedder")
        if embedder is None:
            raise ValueError("embedder is required for semantic chunking")
        return SemanticChunker(embedder=embedder, threshold=kwargs.get("threshold", 0.5))
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
