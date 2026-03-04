"""Tests for src/article_generator.py — mocks Anthropic API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.article_generator import ArticleGenerator, _extract_text, _parse_response
from src.models import DraftStatus, InputDocument, WritingStyle


def _text_block(text: str) -> MagicMock:
    block = MagicMock()
    block.text = text
    return block


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


def test_extract_text_single_block() -> None:
    msg = MagicMock()
    msg.content = [_text_block("TITLE: Test\n---\nBody")]
    assert _extract_text(msg) == "TITLE: Test\n---\nBody"


def test_extract_text_multiple_blocks_joins_all_text() -> None:
    """Simulates tool-use response where article text is split across multiple blocks."""
    tool_block = MagicMock(spec=[])  # no 'text' attribute
    msg = MagicMock()
    msg.content = [
        _text_block("TITLE: Final\n---\nPart one."),
        tool_block,
        _text_block("Part two."),
    ]
    assert _extract_text(msg) == "TITLE: Final\n---\nPart one.\nPart two."


def test_extract_text_no_text_block_raises() -> None:
    tool_block = MagicMock(spec=[])
    msg = MagicMock()
    msg.content = [tool_block]
    with pytest.raises(ValueError, match="No text content"):
        _extract_text(msg)


def test_generate_no_web_search(tmp_path: Path) -> None:
    """web_search=False uses client.messages.create."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[_text_block("TITLE: Test\n---\nBody text")]
    )

    generator = ArticleGenerator(client=mock_client, web_search=False)
    doc = InputDocument(path=Path("data/inbox/sample.txt"), content="Raw transcript here")
    draft = generator.generate(doc)

    assert draft.title == "Test"
    assert draft.status == DraftStatus.generated
    assert draft.style == WritingStyle.general
    mock_client.messages.create.assert_called_once()
    mock_client.beta.messages.create.assert_not_called()


def test_generate_with_web_search(tmp_path: Path) -> None:
    """web_search=True passes tools= to client.messages.create."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[_text_block("TITLE: 銘柄分析\n---\n## テーゼ\n割安だ。")]
    )

    generator = ArticleGenerator(client=mock_client, web_search=True)
    doc = InputDocument(
        path=Path("data/inbox/quant.txt"),
        content="決算メモ",
        style=WritingStyle.quantamental,
    )
    draft = generator.generate(doc)

    assert draft.style == WritingStyle.quantamental
    assert draft.status == DraftStatus.generated
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "tools" in call_kwargs
    assert call_kwargs["tools"][0]["type"] == "web_search_20260209"


def test_generate_quantamental_style(tmp_path: Path) -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[_text_block("TITLE: 銘柄分析\n---\n## テーゼ\n割安だ。")]
    )

    generator = ArticleGenerator(client=mock_client, web_search=False)
    doc = InputDocument(
        path=Path("data/inbox/quant.txt"),
        content="決算メモ",
        style=WritingStyle.quantamental,
    )
    draft = generator.generate(doc)

    assert draft.style == WritingStyle.quantamental
    assert draft.status == DraftStatus.generated
