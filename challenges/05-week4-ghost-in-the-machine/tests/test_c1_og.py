"""Lane C1: link-preview meta tags and og.png (the browser is mocked)."""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from ghosts import og
from ghosts import render as R

FIX = Path(__file__).parent / "fixtures" / "c1" / "ghosts"
FRIENDLY = "0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0"
BAD = "0xe82719202e5965cf5d9b6673b7503a3b92de20be"
BASE = "https://eth-ghosts.decentraminds.tech"


def _meta(doc: str, key: str) -> str:
    m = re.search(rf'<meta (?:property|name)="{re.escape(key)}" content="([^"]*)">', doc)
    assert m, key
    return m[1]


def test_meta_tags_on_fixtures(tmp_path, monkeypatch):
    monkeypatch.delenv("GHOSTS_SITE_URL", raising=False)
    for addr, title in ((FRIENDLY, "The throne that fell silent"), (BAD, "The pyramid that forgot its own name")):
        doc = R.render(addr, FIX, tmp_path).read_text()
        assert _meta(doc, "og:type") == "article"
        assert _meta(doc, "og:site_name") == "Ghosts in the Decentralized World Computer"
        assert _meta(doc, "og:title") == title == _meta(doc, "twitter:title")
        assert _meta(doc, "og:url") == f"{BASE}/ghosts/{addr}/"
        assert _meta(doc, "og:image") == f"{BASE}/ghosts/{addr}/og.png" == _meta(doc, "twitter:image")
        assert _meta(doc, "og:image:width") == "1200" and _meta(doc, "og:image:height") == "630"
        assert _meta(doc, "og:image:alt")
        assert _meta(doc, "twitter:card") == "summary_large_image"
        assert _meta(doc, "og:description") == _meta(doc, "twitter:description") == _meta(doc, "description")
        assert f'<link rel="canonical" href="{BASE}/ghosts/{addr}/">' in doc


def test_meta_escaped_and_site_url_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GHOSTS_SITE_URL", "https://preview.example.test/")
    d = tmp_path / "data" / BAD
    shutil.copytree(FIX / BAD, d)
    s = json.loads((d / "story.json").read_text())
    s["title"] = 'Boo "quoted" <b>&'
    s["tagline"] = "<script>x</script>"
    (d / "story.json").write_text(json.dumps(s))
    doc = R.render(BAD, tmp_path / "data", tmp_path / "out").read_text()
    assert _meta(doc, "og:title") == "Boo &quot;quoted&quot; &lt;b&gt;&amp;"
    assert _meta(doc, "og:description") == "&lt;script&gt;x&lt;/script&gt;"
    assert _meta(doc, "og:image") == f"https://preview.example.test/ghosts/{BAD}/og.png"


def test_description_fallback_without_story(tmp_path):
    d = tmp_path / "data" / FRIENDLY
    d.mkdir(parents=True)
    shutil.copy(FIX / FRIENDLY / "facts.json", d / "facts.json")
    doc = R.render(FRIENDLY, tmp_path / "data", tmp_path / "out").read_text()
    assert _meta(doc, "og:title") == "KingOfTheEtherThrone"
    desc = _meta(doc, "og:description")
    assert "Unclassified" in desc and "Frontier Thawing age" in desc and "born 6 Feb 2016" in desc


def test_og_html_renders_from_fixture():
    doc = og.html_for(BAD, FIX)
    assert '<body data-kind="bad">' in doc
    assert "The pyramid that forgot its own name" in doc
    assert "Bad ghost" in doc and "Age: Homestead" in doc
    assert "Rubixi · 0xe827…20be" in doc
    assert "Ghosts in the Decentralized World Computer" in doc
    assert 'class="ghost"' in doc and 'class="teller"' in doc
    assert not re.search(r"\$[a-z_]+", re.sub(r"<style>.*?</style>", "", doc, flags=re.S))
    assert not re.search(r"https?://", doc)  # no external assets on the card


def test_og_unknown_soul_name(tmp_path):
    d = tmp_path / "data" / BAD
    d.mkdir(parents=True)
    f = json.loads((FIX / BAD / "facts.json").read_text())
    f["name"] = BAD
    f["eh"]["name"] = None
    f["blockscout"]["name"] = None
    f["source"]["name"] = None
    (d / "facts.json").write_text(json.dumps(f))
    doc = og.html_for(BAD, tmp_path / "data")
    assert "Unknown ghost soul 0xe827…20be" in doc


def test_make_writes_png_with_mocked_browser(tmp_path, monkeypatch):
    seen = []

    def fake(jobs):
        for html_doc, dest in jobs:
            seen.append(html_doc)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"\x89PNG fake")
        return [dest for _, dest in jobs]

    monkeypatch.setattr(og, "_screenshot", fake)
    p = og.make(FRIENDLY, FIX, tmp_path)
    assert p == tmp_path / FRIENDLY / "og.png" and p.read_bytes().startswith(b"\x89PNG")
    assert "The throne that fell silent" in seen[0]
    paths = og.make_all(FIX, tmp_path)
    assert {x.parent.name for x in paths} >= {FRIENDLY, BAD}


def test_make_skips_without_playwright(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)  # import raises ImportError
    assert og.make(FRIENDLY, FIX, tmp_path) is None
    assert not (tmp_path / FRIENDLY / "og.png").exists()
    assert "og: skipped" in capsys.readouterr().err
