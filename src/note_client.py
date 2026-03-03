"""note.com browser automation — draft creation only. Never publishes."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright

from .models import ArticleDraft, DraftStatus

logger = logging.getLogger(__name__)

# note.com Markdown features not supported in the editor paste flow
_UNSUPPORTED_MD = [
    r"```",     # code blocks
    r"<.*?>",   # raw HTML
]

NOTE_EDITOR_URL = "https://note.com/notes/new"
DRAFT_SAVE_LABEL = "下書き保存"  # "Save as draft" button text


class NoteClient:
    """Thin Playwright wrapper for note.com draft creation.

    Usage:
        async with NoteClient(session_path=Path("session/auth.json")) as client:
            draft = await client.save_draft(article)
    """

    def __init__(self, session_path: Path, headless: bool = True) -> None:
        self._session_path = session_path
        self._headless = headless
        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> "NoteClient":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            storage_state=str(self._session_path),
            locale="ja-JP",
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def save_draft(self, draft: ArticleDraft) -> ArticleDraft:
        """Fill editor and save as draft. Returns draft with updated status and URL."""
        if not self._context:
            raise RuntimeError("NoteClient must be used as async context manager")

        page: Page = await self._context.new_page()
        try:
            await page.goto(NOTE_EDITOR_URL)
            await asyncio.sleep(2)

            await page.get_by_label("タイトル").fill(draft.title)
            await asyncio.sleep(1)

            body_area = page.get_by_role("textbox", name="本文")
            await body_area.fill(draft.body)
            await asyncio.sleep(1)

            await page.get_by_role("button", name=DRAFT_SAVE_LABEL).click()
            await asyncio.sleep(2)

            draft_url = page.url
            if "/drafts/" not in draft_url and "/notes/edit/" not in draft_url:
                logger.warning("Unexpected URL after save: %s — draft may not have saved", draft_url)

            draft.draft_url = draft_url
            draft.status = DraftStatus.saved
            logger.info("Draft saved: %s", draft_url)
            return draft
        except Exception as e:
            draft.status = DraftStatus.failed
            logger.error("Failed to save draft '%s': %s", draft.title, e)
            raise
        finally:
            await page.close()
