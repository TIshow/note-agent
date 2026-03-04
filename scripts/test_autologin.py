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
        await client.ensure_logged_in()

    if _TEST_SESSION.exists():
        logger.info("Session saved to %s — auto-login succeeded!", _TEST_SESSION)
        _TEST_SESSION.unlink()  # clean up
    else:
        logger.warning("Session file was not created — check _login() persistence logic")


if __name__ == "__main__":
    asyncio.run(main())
