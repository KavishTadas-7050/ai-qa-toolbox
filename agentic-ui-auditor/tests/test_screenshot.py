from pathlib import Path

import pytest

from ai_qa_toolbox.ui_auditor.screenshot import take_screenshot


class FakePlaywright:
    def __init__(self, page=None):
        self.page = page or FakePage()
        self.browser = FakeBrowser(self.page)
        self.chromium = FakeChromium(self.browser)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser

    def launch(self):
        return self.browser


class FakeBrowser:
    def __init__(self, page):
        self.page = page
        self.closed = False

    def new_page(self):
        return self.page

    def close(self):
        self.closed = True


class FakePage:
    def __init__(self, goto_error=None):
        self.goto_error = goto_error
        self.url = None
        self.screenshot_path = None

    def goto(self, url):
        if self.goto_error is not None:
            raise self.goto_error

        self.url = url

    def screenshot(self, path):
        self.screenshot_path = path


def test_take_screenshot_uses_playwright():
    fake = FakePlaywright()
    output_path = Path("example.png")

    result = take_screenshot(
        "https://example.com",
        output_path,
        playwright_factory=lambda: fake,
    )

    assert result == output_path
    assert fake.page.url == "https://example.com"
    assert fake.page.screenshot_path == str(output_path)
    assert fake.browser.closed


def test_take_screenshot_closes_browser_when_capture_fails():
    error = RuntimeError("navigation failed")
    fake = FakePlaywright(page=FakePage(goto_error=error))

    with pytest.raises(RuntimeError, match="navigation failed"):
        take_screenshot(
            "https://example.com",
            Path("example.png"),
            playwright_factory=lambda: fake,
        )

    assert fake.browser.closed
