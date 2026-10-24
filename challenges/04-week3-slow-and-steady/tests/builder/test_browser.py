import asyncio

from sloth.builder import browser


def test_login_wall_detection():
    assert browser.is_login_wall("Access to x.com was denied\n\nHTTP ERROR 403")
    assert browser.is_login_wall("Don't miss what's happening. Log in. Sign up.")
    assert not browser.is_login_wall("A long article about agents. " * 100)


def test_content_text_joins_text_blocks():
    class Block:
        def __init__(self, type_, text=""):
            self.type, self.text = type_, text

    class Wrapped:
        def __init__(self, b):
            self.root = b

    assert browser._content_text([Wrapped(Block("text", "a")), Wrapped(Block("image")), Block("text", "b")]) == "a\nb"
    assert browser._content_text(Wrapped(Block("text", "solo"))) == "solo"


def test_extract_returns_none_when_browser_fails(monkeypatch):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def broken_session(**_):
        raise RuntimeError("no chrome")
        yield  # pragma: no cover

    monkeypatch.setattr(browser, "session", broken_session)
    assert browser.extract("https://example.com", timeout_s=1) is None


def test_extract_with_reason_times_out():
    class SlowContext:
        async def new_page(self):
            await asyncio.sleep(5)

    class SlowBrowser:
        context = SlowContext()

    class SlowSH:
        browser = SlowBrowser()

    result, why = asyncio.run(browser.extract_with_reason(SlowSH(), "https://example.com", timeout_s=1))
    assert result is None and why.startswith("timeout")


def test_scope_selectors_prefer_the_focal_post():
    sels = browser._scope_selectors("https://x.com/VitalikButerin/status/123?s=20")
    assert sels == ['article:has(a[href="/VitalikButerin" i]):not(:has(a[href^="/compose/post"]))',
                    'article:has(a[href="/VitalikButerin" i])', "article"]
    assert browser._scope_selectors("https://example.com/post") == []
