"""Screenshot capture helpers."""

from collections.abc import Callable
from pathlib import Path
from typing import Any


def take_screenshot(
    url: str,
    output_path: str | Path = "screenshot.png",
    playwright_factory: Callable[[], Any] | None = None,
) -> Path:
    """Capture a screenshot of a URL and return the output path."""
    if playwright_factory is None:
        from playwright.sync_api import sync_playwright

        playwright_factory = sync_playwright

    output_path = Path(output_path)
    with playwright_factory() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(url)
            page.screenshot(path=str(output_path))
        finally:
            browser.close()

    return output_path
