"""Take a screenshot of the note.com login page and print visible input placeholders."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright

NOTE_LOGIN_URL = "https://note.com/login"
SCREENSHOT_PATH = Path("data/logs/debug_login_page.png")


async def main() -> None:
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(locale="ja-JP")

        print(f"Navigating to {NOTE_LOGIN_URL} ...")
        await page.goto(NOTE_LOGIN_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        await page.screenshot(path=str(SCREENSHOT_PATH))
        print(f"Screenshot saved: {SCREENSHOT_PATH}")

        # Print all input elements and their attributes
        inputs = await page.query_selector_all("input")
        print(f"\nFound {len(inputs)} input elements:")
        for inp in inputs:
            typ = await inp.get_attribute("type")
            name = await inp.get_attribute("name")
            placeholder = await inp.get_attribute("placeholder")
            label = await inp.get_attribute("aria-label")
            print(f"  type={typ!r:12} name={name!r:20} placeholder={placeholder!r:30} aria-label={label!r}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
