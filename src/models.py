"""Data models. No I/O here — pure pydantic structures."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class DraftStatus(str, Enum):
    pending = "pending"
    generated = "generated"
    saved = "saved"
    failed = "failed"


class WritingStyle(str, Enum):
    """Controls which prompt template and writing voice is used."""

    general = "general"           # General-audience note.com article
    quantamental = "quantamental" # Investor + quantamental analyst perspective


class InputDocument(BaseModel):
    """A raw text file waiting to be processed."""

    path: Path
    content: str
    style: WritingStyle = WritingStyle.general
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class ArticleDraft(BaseModel):
    """A generated note.com article draft."""

    title: str
    body: str  # Markdown
    source_path: Path
    style: WritingStyle = WritingStyle.general
    status: DraftStatus = DraftStatus.pending
    draft_url: str | None = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        return f"# {self.title}\n\n{self.body}\n"
