"""Application configuration via environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "docpulse"

    embedding_model: str = "text-embedding-004"
    chat_model: str = "gemini-2.0-flash"
    embedding_dimensions: int = 768

    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieve_top_k: int = 4
    data_dir: Path = Path("data")


@lru_cache
def get_settings() -> Settings:
    return Settings()
