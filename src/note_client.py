"""note.com browser automation — draft creation only. Never publishes."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .models import ArticleDraft, DraftStatus

logger = logging.getLogger(__name__)

# note.com Markdown features not supported in the editor paste flow
_UNSUPPORTED_MD = [
    r"```",  # code blocks
    r"<.*?>",  # raw HTML
    r"\|.*\|",  # Markdown tables (pipe-delimited rows)
]

def _strip_unsupported(text: str) -> str:
    """Remove Markdown syntax unsupported by note.com's editor."""
    lines = []
    for line in text.splitlines():
        if any(re.search(pat, line) for pat in _UNSUPPORTED_MD):
            continue
        lines.append(line)
    return "\n".join(lines)


NOTE_EDITOR_URL = "https://note.com/notes/new"
NOTE_LOGIN_URL = "https://note.com/login"
DRAFT_SAVE_LABEL = "下書き保存"  # "Save as draft" button text

# Timeout for waiting for the editor to appear after navigation (ms)
_EDITOR_LOAD_TIMEOUT = 15_000


class NoteClient:
    """Thin Playwright wrapper for note.com draft creation.

    Usage:
        async with NoteClient(session_path=Path("session/auth.json")) as client:
            draft = await client.save_draft(article)
    """

    def __init__(
        self,
        session_path: Path,
        headless: bool = True,
        email: str = "",
        password: str = "",
    ) -> None:
        self._session_path = session_path
        self._headless = headless
        self._email = email
        self._password = password
        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> NoteClient:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            storage_state=str(self._session_path) if self._session_path.exists() else None,
            locale="ja-JP",
            permissions=["clipboard-read", "clipboard-write"],
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def ensure_logged_in(self) -> None:
        """Verify session by navigating to the editor. Auto-login if needed.

        Called once before article generation so we fail fast if login is broken.
        """
        if not self._context:
            raise RuntimeError("NoteClient must be used as async context manager")
        page: Page = await self._context.new_page()
        try:
            await self._navigate_to_editor(page)
        finally:
            await page.close()

    async def _navigate_to_editor(self, page: Page) -> None:
        """Go to editor URL, auto-login if session expired, then wait for title input."""
        await page.goto(NOTE_EDITOR_URL, wait_until="domcontentloaded")
        if not await self._is_logged_in(page):
            await self._login(page)
            await page.goto(NOTE_EDITOR_URL, wait_until="domcontentloaded")
            await page.get_by_placeholder("記事タイトル").wait_for(state="visible", timeout=30_000)

    async def _is_logged_in(self, page: Page) -> bool:
        """Return True if the editor title input is visible within a short timeout."""
        try:
            await page.get_by_placeholder("記事タイトル").wait_for(
                state="visible", timeout=_EDITOR_LOAD_TIMEOUT
            )
            return True
        except PlaywrightTimeoutError:
            return False
        except Exception:
            logger.warning("Unexpected error while checking login state", exc_info=True)
            return False

    async def _login(self, page: Page) -> None:
        """Log in using email/password and persist the new session to disk."""
        if not self._email or not self._password:
            raise RuntimeError(
                "Session expired and no credentials available. "
                "Set NOTE_USER_EMAIL and NOTE_USER_PASSWORD in .env, "
                "or refresh session/auth.json manually."
            )
        logger.info("Session expired — logging in automatically")
        await page.goto(NOTE_LOGIN_URL, wait_until="networkidle")

        # note.com login form selectors (confirmed 2026-03):
        # email input has no type attr; password is type='password'
        email_input = page.locator("input:not([type='password'])")
        await email_input.wait_for(state="visible", timeout=15_000)
        await email_input.fill(self._email)
        await page.locator("input[type='password']").fill(self._password)
        await page.get_by_role("button", name="ログイン").click()
        # Wait until we navigate away from the login page.
        # "https://note.com/**" also matches /login itself, so we use a predicate.
        await page.wait_for_url(lambda url: "/login" not in url, timeout=30_000)

        # Persist refreshed session
        assert self._context is not None
        await self._context.storage_state(path=str(self._session_path))
        logger.info("Session refreshed and saved to %s", self._session_path)

    async def save_draft(self, draft: ArticleDraft) -> ArticleDraft:
        """Fill editor and save as draft. Returns draft with updated status and URL."""
        if not self._context:
            raise RuntimeError("NoteClient must be used as async context manager")

        page: Page = await self._context.new_page()
        try:
            await self._navigate_to_editor(page)

            await page.get_by_placeholder("記事タイトル").fill(draft.title)
            await asyncio.sleep(1)

            body_area = page.locator(".ProseMirror")
            await body_area.click()
            body = _strip_unsupported(draft.body)
            await page.evaluate("(text) => navigator.clipboard.writeText(text)", body)
            await page.keyboard.press("Meta+v")
            await asyncio.sleep(1)

            await page.get_by_role("button", name=DRAFT_SAVE_LABEL).click()
            await asyncio.sleep(2)

            draft_url = page.url
            if "/notes/" not in draft_url:
                logger.warning(
                    "Unexpected URL after save: %s — draft may not have saved", draft_url
                )

            draft.draft_url = draft_url
            draft.status = DraftStatus.saved
            logger.info("Draft saved: %s", draft_url)
            return draft
        except Exception as e:
            draft.status = DraftStatus.failed
            logger.error("Failed to save draft '%s': %s", draft.title, e)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = Path("data/logs") / f"debug_{ts}.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            logger.info("Screenshot saved to %s", screenshot_path)
            raise
        finally:
            await page.close()
