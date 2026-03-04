"""Inspect the note.com editor page HTML using the real session."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright

NOTE_EDITOR_URL = "https://note.com/notes/new"
SESSION_PATH = Path("session/auth.json")
SCREENSHOT_PATH = Path("data/logs/debug_editor_page.png")


async def main() -> None:
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SESSION_PATH.exists():
        print("session/auth.json not found — run note-agent login first")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state=str(SESSION_PATH),
            locale="ja-JP",
        )
        page = await context.new_page()

        print(f"Navigating to {NOTE_EDITOR_URL} ...")
        await page.goto(NOTE_EDITOR_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        await page.screenshot(path=str(SCREENSHOT_PATH))
        print(f"Screenshot saved: {SCREENSHOT_PATH}")

        # List all textarea and input elements
        for tag in ("textarea", "input"):
            elements = await page.query_selector_all(tag)
            print(f"\nFound {len(elements)} <{tag}> elements:")
            for el in elements:
                placeholder = await el.get_attribute("placeholder")
                cls = await el.get_attribute("class")
                typ = await el.get_attribute("type")
                print(f"  placeholder={placeholder!r:30} type={typ!r:10} class={str(cls)[:60]!r}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
