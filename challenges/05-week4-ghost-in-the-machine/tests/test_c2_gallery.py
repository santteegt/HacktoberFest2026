import json
import os
import shutil
from pathlib import Path

import pytest

from ghosts import config, gallery

FIX = Path(__file__).parent / "fixtures" / "c2"
KING = "0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0"
NOPAGE = "0xe82719202e5965cf5d9b6673b7503a3b92de20be"
BOUNTIES = "0x2af47a65da8cd66729b4209c22017d6a5c2d2400"
NOSTORY = "0xbb9bc244d798123fde783fcc1c72d3bb8c189413"
KEYS = {"address", "name", "unnamed", "kind", "age", "born", "last_seen", "never_called", "proxy", "calls", "scars", "balance_eth", "historian", "path", "cover", "title", "tagline"}


@pytest.fixture()
def home(tmp_path, monkeypatch):
    ghosts = tmp_path / "data" / "ghosts"
    shutil.copytree(FIX, ghosts)
    # a ghost with data but no rendered page must be left out
    (ghosts / NOPAGE).mkdir()
    shutil.copy(FIX / KING / "facts.json", ghosts / NOPAGE / "facts.json")
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "GHOSTS_DIR", ghosts)
    web = tmp_path / "web" / "ghosts"
    for addr in (KING, BOUNTIES, NOSTORY):
        (web / addr).mkdir(parents=True)
        (web / addr / "index.html").write_text("<html></html>")
    (web / KING / "cover.png").write_bytes(b"png")
    os.utime(web / NOSTORY / "index.html", (0, 0))  # oldest, no story.json -> mtime fallback
    return tmp_path


def read(home):
    return json.loads((home / "web" / "ghosts" / "index.json").read_text())


def test_schema_and_filtering(home):
    out = gallery.build()
    assert out == home / "web" / "ghosts" / "index.json"
    rows = read(home)
    assert all(set(r) == KEYS for r in rows)
    assert {r["address"] for r in rows} == {KING, BOUNTIES, NOSTORY}  # page-less ghost excluded
    king = next(r for r in rows if r["address"] == KING)
    assert king["name"] == "KingOfTheEtherThrone" and king["unnamed"] is False
    assert king["kind"] == "friendly"
    assert king["age"] == "Frontier Thawing"
    assert king["born"] == "2016-02-06"
    assert king["last_seen"] == "2016-02-19"
    assert king["balance_eth"] == 0.0
    assert king["never_called"] is False and king["proxy"] is True
    assert king["calls"] == 21 and king["scars"] == 2
    assert king["historian"] is True
    assert king["path"] == f"ghosts/{KING}/"
    assert king["cover"] == f"ghosts/{KING}/cover.png"
    assert king["title"] == "The throne that fell silent"
    assert king["tagline"] == "A fake tagline for tests."


def test_order_newest_story_first_and_fallbacks(home):
    gallery.build()
    rows = read(home)
    assert [r["address"] for r in rows] == [BOUNTIES, KING, NOSTORY]
    nostory = rows[-1]
    assert nostory["kind"] == "unknown"  # no verdict, no story
    assert nostory["cover"] is None
    assert nostory["never_called"] is True and nostory["last_seen"] is None
    assert nostory["proxy"] is False and nostory["calls"] == 0 and nostory["scars"] == 0
    assert nostory["name"]  # never blank, falls back to a short address
    assert nostory["historian"] is True  # from facts.eh when no verdict
    bounties = rows[0]
    assert bounties["kind"] == "alive" and bounties["historian"] is False


def test_sitemap_and_idempotent(home):
    gallery.build()
    files = ("ghosts/index.json", "sitemap.txt", "ghosts/featured.json")
    first = tuple((home / "web" / f).read_text() for f in files)
    gallery.build()
    second = tuple((home / "web" / f).read_text() for f in files)
    assert first == second
    lines = first[1].splitlines()
    assert lines[0] == "https://eth-ghosts.decentraminds.tech/"
    assert f"https://eth-ghosts.decentraminds.tech/ghosts/{KING}/" in lines
    assert len(lines) == 4


def test_unnamed_when_the_name_is_the_address(home):
    ghosts = home / "data" / "ghosts"
    for name in (KING.upper().replace("0X", "0x"), ""):  # the address in any case, or nothing at all
        for f in ("facts.json", "story.json"):
            data = json.loads((ghosts / KING / f).read_text())
            data["name"] = name
            if f == "facts.json":
                data["eh"] = dict(data.get("eh") or {}, name=None)
            (ghosts / KING / f).write_text(json.dumps(data))
        gallery.build()
        king = next(r for r in read(home) if r["address"] == KING)
        assert king["unnamed"] is True, name
        assert king["name"].lower() in (KING, KING[:6] + "…" + KING[-4:])


def test_featured_is_newest_story(home):
    gallery.build()
    rows = read(home)
    featured = json.loads((home / "web" / "ghosts" / "featured.json").read_text())
    assert isinstance(rows, list)  # index.json stays a plain array (the contract)
    assert set(featured) == KEYS | {"generated_at"}
    assert featured["address"] == BOUNTIES == rows[0]["address"]
    assert featured["generated_at"] == "2026-10-30T10:00:00Z"
    assert {k: featured[k] for k in KEYS} == rows[0]
    assert "cover" in featured and featured["cover"] is None


def test_featured_follows_a_newer_story(home):
    story = home / "data" / "ghosts" / KING / "story.json"
    data = json.loads(story.read_text())
    data["generated_at"] = "2026-11-01T00:00:00Z"
    story.write_text(json.dumps(data))
    gallery.build()
    featured = json.loads((home / "web" / "ghosts" / "featured.json").read_text())
    assert featured["address"] == KING
    assert featured["cover"] == f"ghosts/{KING}/cover.png"
    assert read(home)[0]["address"] == KING


def test_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "GHOSTS_DIR", tmp_path / "nothing")
    gallery.build()
    assert json.loads((tmp_path / "web" / "ghosts" / "index.json").read_text()) == []
    assert json.loads((tmp_path / "web" / "ghosts" / "featured.json").read_text()) is None


def test_site_url_from_env(home, monkeypatch):
    monkeypatch.setenv("GHOSTS_SITE_URL", "https://preview.example.test/")
    gallery.build()
    lines = (home / "web" / "sitemap.txt").read_text().splitlines()
    assert lines[0] == "https://preview.example.test/"
    assert f"https://preview.example.test/ghosts/{KING}/" in lines


def test_og_index_skips_without_playwright(tmp_path, monkeypatch, capsys):
    import builtins
    monkeypatch.setattr(config, "ROOT", tmp_path)
    real = builtins.__import__

    def fake(name, *a, **k):
        if name.startswith("playwright"):
            raise ImportError(name)
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    assert gallery.og_index() is None
    assert "skipped" in capsys.readouterr().err
    assert not (tmp_path / "web" / "assets" / "og.png").exists()
