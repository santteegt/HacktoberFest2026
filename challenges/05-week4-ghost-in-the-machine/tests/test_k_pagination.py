"""Lane K: gallery pagination markup/script and the favicon set."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
LINKS = ['href="/favicon.ico"', 'href="/favicon.svg"', 'href="/icons/apple-touch-icon.png"', 'href="/site.webmanifest"']


def test_site_js_pagination():
    js = (WEB / "assets" / "site.js").read_text()
    assert "PAGE_SIZE = 15" in js
    assert 'setAttribute("aria-current", "page")' in js
    assert "prefers-reduced-motion" in js


def test_index_has_pager_nav():
    html = (WEB / "index.html").read_text()
    assert '<nav class="pager" id="pager" aria-label="Pages"' in html
    assert 'id="count" role="status"' in html


def test_icon_links_in_both_heads():
    for p in (WEB / "index.html", ROOT / "template" / "ghost.html"):
        head = p.read_text().split("</head>")[0]
        for link in LINKS:
            assert link in head, (p, link)
        assert "data:image/svg" not in head


def test_icon_files_and_manifest():
    for f in ("favicon.ico", "favicon.svg", "icons/apple-touch-icon.png", "icons/icon-192.png", "icons/icon-512.png"):
        assert (WEB / f).stat().st_size > 100, f
    svg = (WEB / "favicon.svg").read_text()
    assert "0xB00" in svg and "$tag" not in svg and "$uid" not in svg
    m = json.loads((WEB / "site.webmanifest").read_text())
    assert m["short_name"] == "Ghosts" and m["theme_color"] == "#1b0b2b" and len(m["icons"]) == 2
