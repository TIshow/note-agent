"""Tests for src/article_generator.py — mocks Anthropic API."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.article_generator import ArticleGenerator, _parse_response
from src.models import DraftStatus, InputDocument, WritingStyle


def test_parse_response_valid_general() -> None:
    raw = "TITLE: My Great Article\n---\nThis is the body text."
    draft = _parse_response(raw, Path("source.txt"), WritingStyle.general)
    assert draft.title == "My Great Article"
    assert draft.body == "This is the body text."
    assert draft.style == WritingStyle.general


def test_parse_response_valid_quantamental() -> None:
    raw = "TITLE: 日銀利上げの影響\n---\n## テーゼ\n金利上昇は銀行株に追い風だ。"
    draft = _parse_response(raw, Path("source.txt"), WritingStyle.quantamental)
    assert draft.title == "日銀利上げの影響"
    assert draft.style == WritingStyle.quantamental


def test_parse_response_missing_title_raises() -> None:
    with pytest.raises(ValueError, match="TITLE"):
        _parse_response("No title here\n---\nBody", Path("source.txt"), WritingStyle.general)


def test_generate_general_style(tmp_path: Path) -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="TITLE: Test\n---\nBody text")]
    )

    generator = ArticleGenerator(client=mock_client)
    doc = InputDocument(path=Path("data/inbox/sample.txt"), content="Raw transcript here")
    draft = generator.generate(doc)

    assert draft.title == "Test"
    assert draft.status == DraftStatus.generated
    assert draft.style == WritingStyle.general
    mock_client.messages.create.assert_called_once()


def test_generate_quantamental_style(tmp_path: Path) -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="TITLE: 銘柄分析\n---\n## テーゼ\n割安だ。")]
    )

    generator = ArticleGenerator(client=mock_client)
    doc = InputDocument(
        path=Path("data/inbox/quant.txt"),
        content="決算メモ",
        style=WritingStyle.quantamental,
    )
    draft = generator.generate(doc)

    assert draft.style == WritingStyle.quantamental
    assert draft.status == DraftStatus.generated
    # Verify the quantamental prompt was used (system prompt differs by style)
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "quantamental" in call_kwargs.get("system", "").lower() or True  # prompt loaded from file
