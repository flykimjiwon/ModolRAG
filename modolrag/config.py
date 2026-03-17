"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ModolRAG configuration via environment variables."""

    # Database
    POSTGRES_URI: str = "postgresql://localhost:5432/modolrag"

    # API Authentication
    API_KEYS: str = ""  # Comma-separated list of valid API keys

    # Embedding
    EMBEDDING_PROVIDER: str = "ollama"  # "ollama" or "openai"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSIONS: int = 768
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""

    # Chunking
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 51

    # Search
    SIMILARITY_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    model_config = {"env_prefix": "MODOLRAG_", "env_file": ".env", "extra": "ignore"}

    @property
    def parsed_api_keys(self) -> list[str]:
        """Parse comma-separated API keys and strip whitespace."""
        return [k.strip() for k in self.API_KEYS.split(",") if k.strip()]


def get_settings() -> Settings:
    return Settings()
