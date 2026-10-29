"""Regenerate the favicon set from web/favicon.svg.

Run from the project folder:  uv run python scripts/make_icons.py

Renders the SVG with Playwright's Chromium, then writes web/favicon.ico (16+32+48),
web/icons/apple-touch-icon.png (180, opaque #1b0b2b), icon-192.png and icon-512.png.
Needs Pillow (dev dependency).
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

WEB = Path(__file__).resolve().parent.parent / "web"
BG = "#1b0b2b"


def render(page, svg: str, size: int, opaque: bool) -> Image.Image:
    bg = BG if opaque else "transparent"
    page.set_viewport_size({"width": size, "height": size})
    page.set_content(
        f"<style>html,body{{margin:0;background:{bg}}}svg{{display:block;width:{size}px;height:{size}px}}</style>{svg}"
    )
    png = page.screenshot(omit_background=not opaque, clip={"x": 0, "y": 0, "width": size, "height": size})
    return Image.open(io.BytesIO(png)).convert("RGBA")


def main() -> None:
    svg = (WEB / "favicon.svg").read_text(encoding="utf-8")
    (WEB / "icons").mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        for size, name in ((180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")):
            img = render(page, svg, size, opaque=name.startswith("apple"))
            if name.startswith("apple"):
                img = img.convert("RGB")
            img.save(WEB / "icons" / name)
        big = render(page, svg, 256, opaque=False)
        big.save(WEB / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
        b.close()
    print("icons written")


if __name__ == "__main__":
    main()
