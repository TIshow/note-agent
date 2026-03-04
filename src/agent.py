"""Orchestration loop: read inbox → generate → save draft → move to processed."""

from __future__ import annotations

import asyncio
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

    def __init__(self, settings: Settings, web_search: bool = True) -> None:
        self._settings = settings
        self._generator = ArticleGenerator(
            client=anthropic.Anthropic(api_key=settings.anthropic_api_key),
            web_search=web_search,
        )

    def _make_note_client(self, headless: bool) -> NoteClient:
        return NoteClient(
            session_path=Path("session/auth.json"),
            headless=headless,
            email=self._settings.note_user_email,
            password=self._settings.note_user_password,
        )

    def run(
        self,
        *,
        dry_run: bool = False,
        save_to_note: bool = False,
        style: WritingStyle = WritingStyle.general,
        headless: bool = True,
    ) -> list[ArticleDraft]:
        """Process all inbox files. Returns list of drafts.

        When save_to_note=True, note.com login is verified BEFORE article
        generation so no API credits are spent if the session cannot be established.
        """
        docs = _load_inbox(self._settings.inbox_dir, style)
        if not docs:
            logger.info("Inbox is empty — nothing to process")
            return []

        # ── Step 1: verify / establish note.com session before spending API credits ──
        if save_to_note and not dry_run:
            asyncio.run(self._ensure_note_session(headless=headless))

        # ── Step 2: generate articles ──
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

        # ── Step 3: upload to note.com ──
        if save_to_note and not dry_run:
            asyncio.run(self._upload_drafts(drafts, headless=headless))

        return drafts

    async def _ensure_note_session(self, *, headless: bool) -> None:
        """Navigate to the note.com editor to verify login. Auto-login if needed.

        Raises on failure so the pipeline aborts before generating articles.
        """
        logger.info("Verifying note.com session before article generation...")
        async with self._make_note_client(headless) as client:
            await client.ensure_logged_in()
        logger.info("note.com session OK")

    async def _upload_drafts(self, drafts: list[ArticleDraft], *, headless: bool) -> None:
        async with self._make_note_client(headless) as client:
            for draft in drafts:
                if draft.status == DraftStatus.generated:
                    await client.save_draft(draft)
