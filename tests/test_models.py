"""Tests for src/models.py"""

from __future__ import annotations

from pathlib import Path

from src.models import ArticleDraft, DraftStatus, InputDocument


def test_input_document_stores_content() -> None:
    doc = InputDocument(path=Path("data/inbox/test.txt"), content="Hello world")
    assert doc.content == "Hello world"
    assert doc.path.name == "test.txt"


def test_article_draft_default_status() -> None:
    draft = ArticleDraft(title="My Title", body="Some content", source_path=Path("test.txt"))
    assert draft.status == DraftStatus.pending
    assert draft.draft_url is None


def test_article_draft_to_markdown() -> None:
    draft = ArticleDraft(title="My Title", body="Line one\n\nLine two", source_path=Path("x.txt"))
    md = draft.to_markdown()
    assert md.startswith("# My Title")
    assert "Line one" in md
