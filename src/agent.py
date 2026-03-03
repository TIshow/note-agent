"""Orchestration loop: read inbox → generate → save draft → move to processed."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import anthropic

from .article_generator import ArticleGenerator
from .config import Settings
from .models import ArticleDraft, DraftStatus, InputDocument, WritingStyle
from .note_client import NoteClient

logger = logging.getLogger(__name__)


def _load_inbox(inbox_dir: Path, style: WritingStyle) -> list[InputDocument]:
    docs = []
    for path in sorted(inbox_dir.glob("*.txt")):
        content = path.read_text(encoding="utf-8").strip()
        if content:
            docs.append(InputDocument(path=path, content=content, style=style))
        else:
            logger.warning("Skipping empty file: %s", path.name)
    return docs


def _save_article(draft: ArticleDraft, articles_dir: Path) -> Path:
    slug = draft.title[:60].replace(" ", "-").lower()
    out_path = articles_dir / f"{slug}.md"
    out_path.write_text(draft.to_markdown(), encoding="utf-8")
    return out_path


def _move_to_processed(doc: InputDocument, processed_dir: Path) -> None:
    dest = processed_dir / doc.path.name
    shutil.move(str(doc.path), dest)
    logger.info("Moved %s → %s", doc.path.name, processed_dir)


class Agent:
    """Runs the full pipeline for all files in the inbox."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._generator = ArticleGenerator(
            client=anthropic.Anthropic(api_key=settings.anthropic_api_key)
        )

    def run(
        self,
        *,
        dry_run: bool = False,
        save_to_note: bool = False,
        style: WritingStyle = WritingStyle.general,
        headless: bool = True,
    ) -> list[ArticleDraft]:
        """Process all inbox files. Returns list of drafts."""
        docs = _load_inbox(self._settings.inbox_dir, style)
        if not docs:
            logger.info("Inbox is empty — nothing to process")
            return []

        drafts: list[ArticleDraft] = []
        for doc in docs:
            try:
                draft = self._generator.generate(doc)
                out_path = _save_article(draft, self._settings.articles_dir)
                logger.info("Article written: %s", out_path)
                drafts.append(draft)

                if not dry_run:
                    _move_to_processed(doc, self._settings.processed_dir)
            except Exception as e:
                logger.error("Failed on %s: %s", doc.path.name, e)

        if save_to_note:
            import asyncio

            session = Path("session/auth.json")
            if not session.exists():
                logger.warning("session/auth.json not found — skipping note.com upload")
            else:
                asyncio.run(self._upload_drafts(drafts, session, headless=headless))

        return drafts

    async def _upload_drafts(
        self, drafts: list[ArticleDraft], session: Path, *, headless: bool = True
    ) -> None:
        async with NoteClient(session_path=session, headless=headless) as client:
            for draft in drafts:
                if draft.status == DraftStatus.generated:
                    await client.save_draft(draft)
