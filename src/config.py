"""Settings loaded from environment variables. No side effects at import time."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    note_user_id: str = Field("", alias="NOTE_USER_ID")
    note_user_email: str = Field("", alias="NOTE_USER_EMAIL")
    note_user_password: str = Field("", alias="NOTE_USER_PASSWORD")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    inbox_dir: Path = Field(Path("data/inbox"), alias="INBOX_DIR")
    articles_dir: Path = Field(Path("data/articles"), alias="ARTICLES_DIR")
    processed_dir: Path = Field(Path("data/processed"), alias="PROCESSED_DIR")

    @field_validator("inbox_dir", "articles_dir", "processed_dir", mode="after")
    @classmethod
    def ensure_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


def get_settings() -> Settings:
    """Return a Settings instance. Call this at runtime, not at module level."""
    return Settings()  # type: ignore[call-arg]
