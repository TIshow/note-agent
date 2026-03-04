"""Verify that NoteClient auto-login works when no session file exists.

Uses a throwaway session path so session/auth.json is never touched.
No articles are generated. Run with:

    uv run python scripts/test_autologin.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Allow running from project root without installing
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.note_client import NoteClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# Throwaway session — deleted before the test so auto-login is always triggered
_TEST_SESSION = Path("/tmp/note_agent_autologin_test.json")


async def main() -> None:
    settings = get_settings()

    if not settings.note_user_email or not settings.note_user_password:
        logger.error(
            "NOTE_USER_EMAIL and NOTE_USER_PASSWORD must be set in .env to test auto-login"
        )
        sys.exit(1)

    # Remove any leftover test session to guarantee we start with no stored cookies
    if _TEST_SESSION.exists():
        _TEST_SESSION.unlink()
        logger.info("Removed leftover test session file")

    logger.info("Starting auto-login test (headless=False so you can watch)")
    logger.info("Session file: %s (does not exist → auto-login will be triggered)", _TEST_SESSION)

    async with NoteClient(
        session_path=_TEST_SESSION,
        headless=False,
        email=settings.note_user_email,
        password=settings.note_user_password,
    ) as client:
        # Run ensure_logged_in and dump editor page state on failure
        from playwright.async_api import async_playwright as _ap  # noqa: F401
        assert client._context is not None
        page = await client._context.new_page()
        try:
            await client._navigate_to_editor(page)
            logger.info("Editor loaded successfully")
        except Exception as e:
            logger.error("Failed to reach editor: %s", e)
            screenshot = Path("data/logs/debug_after_login.png")
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot))
            logger.info("Screenshot: %s", screenshot)
            for tag in ("textarea", "input"):
                els = await page.query_selector_all(tag)
                logger.info("<%s> elements (%d):", tag, len(els))
                for el in els:
                    ph = await el.get_attribute("placeholder")
                    cls = await el.get_attribute("class")
                    logger.info("  placeholder=%r  class=%r", ph, str(cls)[:60])
            raise
        finally:
            await page.close()

    if _TEST_SESSION.exists():
        logger.info("Session saved to %s — auto-login succeeded!", _TEST_SESSION)
        _TEST_SESSION.unlink()  # clean up
    else:
        logger.warning("Session file was not created — check _login() persistence logic")


if __name__ == "__main__":
    asyncio.run(main())
