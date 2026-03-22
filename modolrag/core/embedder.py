"""Embedding adapters for Ollama and OpenAI."""

from abc import ABC, abstractmethod

import httpx

from modolrag.config import Settings


class EmbedderBase(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        ...


class OllamaEmbedder(EmbedderBase):
    """Ollama embedding adapter."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimensions: int | None = None

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            data = response.json()
            embedding = data["embedding"]
            if self._dimensions is None:
                self._dimensions = len(embedding)
            return embedding

    async def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = []
            for text in batch:
                embedding = await self.embed(text)
                batch_results.append(embedding)
            results.extend(batch_results)
        return results

    @property
    def dimensions(self) -> int:
        return self._dimensions or 768  # nomic-embed-text default


class OpenAIEmbedder(EmbedderBase):
    """OpenAI embedding adapter."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self._dimensions: int | None = None

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": text},
            )
            response.raise_for_status()
            data = response.json()
            embedding = data["data"][0]["embedding"]
            if self._dimensions is None:
                self._dimensions = len(embedding)
            return embedding

    async def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "input": batch},
                )
                response.raise_for_status()
                data = response.json()
                batch_embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
                results.extend(batch_embeddings)
        return results

    @property
    def dimensions(self) -> int:
        return self._dimensions or 1536  # text-embedding-3-small default


class LocalEmbedder(EmbedderBase):
    """Local embedding using sentence-transformers. No external API needed.

    Install: pip install sentence-transformers
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self.model_name = model
        self._model = None
        self._dimensions: int | None = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers가 필요합니다.\n"
                    "설치: pip install sentence-transformers\n"
                    "또는 Ollama 사용: export MODOLRAG_EMBEDDING_PROVIDER=ollama"
                )
            self._model = SentenceTransformer(self.model_name)
            self._dimensions = self._model.get_sentence_embedding_dimension()

    async def embed(self, text: str) -> list[float]:
        self._load_model()
        import asyncio
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: self._model.encode(text, normalize_embeddings=True).tolist()
        )
        return embedding

    async def embed_batch(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        self._load_model()
        import asyncio
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: self._model.encode(texts, normalize_embeddings=True, batch_size=batch_size).tolist()
        )
        return embeddings

    @property
    def dimensions(self) -> int:
        self._load_model()
        return self._dimensions or 384


def get_embedder(settings: Settings | None = None) -> EmbedderBase:
    """Factory function to create the appropriate embedder.

    Providers:
        - "ollama" (default): Requires Ollama running locally
        - "openai": Requires OPENAI_API_KEY
        - "local": Uses sentence-transformers (pip install sentence-transformers)
    """
    if settings is None:
        from modolrag.config import get_settings
        settings = get_settings()

    if settings.EMBEDDING_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER is 'openai'")
        return OpenAIEmbedder(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
    elif settings.EMBEDDING_PROVIDER == "local":
        return LocalEmbedder(
            model=settings.EMBEDDING_MODEL if settings.EMBEDDING_MODEL != "nomic-embed-text" else "all-MiniLM-L6-v2",
        )
    else:
        return OllamaEmbedder(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.EMBEDDING_MODEL,
        )
