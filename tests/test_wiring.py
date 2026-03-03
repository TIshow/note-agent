"""Smoke tests — verifies the project structure is importable and wired correctly."""

from __future__ import annotations


def test_models_importable() -> None:
    from src.models import ArticleDraft, DraftStatus, InputDocument  # noqa: F401


def test_config_importable() -> None:
    from src.config import get_settings  # noqa: F401


def test_article_generator_importable() -> None:
    from src.article_generator import ArticleGenerator  # noqa: F401


def test_note_client_importable() -> None:
    from src.note_client import NoteClient  # noqa: F401


def test_agent_importable() -> None:
    from src.agent import Agent  # noqa: F401


def test_cli_importable() -> None:
    from src.cli import main  # noqa: F401
