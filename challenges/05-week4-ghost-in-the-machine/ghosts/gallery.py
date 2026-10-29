"""Lanes C2/C3: build web/ghosts/index.json, web/ghosts/featured.json and web/sitemap.txt
from data/ghosts/* and the rendered pages.

Only ghosts that have a rendered page (web/ghosts/<address>/index.html) are listed.
index.json stays a plain array (the contract in docs/LANES.md); featured.json is the
"story of the day": the newest entry (same keys, plus `generated_at`), or null when empty.
Idempotent: the same inputs always produce byte-identical output.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import typer

from . import config

SITE = "https://eth-ghosts.decentraminds.tech"  # default; GHOSTS_SITE_URL overrides (same as Lane C1)


def site_url() -> str:
    return (os.environ.get("GHOSTS_SITE_URL") or SITE).rstrip("/")
KINDS = ("friendly", "lingering", "bad", "banished", "alive")

app = typer.Typer(help="The gallery index and deploy helpers", no_args_is_help=True)


def web_dir() -> Path:
    return config.ROOT / "web"


def _load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _date(ts) -> str | None:
    return str(ts)[:10] if ts else None


def _clip(text, n: int = 200) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _entry(addr_dir: Path, page: Path) -> tuple[str, dict]:
    facts = _load(addr_dir / "facts.json") or {}
    verdict = _load(addr_dir / "verdict.json") or {}
    story = _load(addr_dir / "story.json") or {}
    address = facts.get("address") or addr_dir.name
    eh, life, chain = facts.get("eh") or {}, facts.get("life") or {}, facts.get("chain") or {}
    kind = verdict.get("kind") or story.get("kind") or "unknown"
    name = story.get("name") or facts.get("name") or eh.get("name") or (address[:6] + "…" + address[-4:])
    short = address[:6] + "…" + address[-4:]
    # no real name anywhere: the name is just the address (or its short form)
    unnamed = str(name).strip().lower() in (str(address).lower(), short.lower())
    balance = chain.get("balance_eth")
    if balance is None:
        balance = life.get("balance_eth")
    if "historian_story" in (verdict.get("labels") or {}):
        historian = bool(verdict["labels"]["historian_story"])
    else:
        historian = bool(eh.get("short_description") or eh.get("description"))
    tagline = story.get("tagline") or _clip(eh.get("short_description"))
    cover = f"ghosts/{addr_dir.name}/cover.png"
    never = bool(life.get("never_called"))
    scars = (verdict.get("wounds") or {}).get("scars") or 0
    entry = {
        "address": address,
        "name": name,
        "unnamed": unnamed,
        "kind": kind,
        "age": (facts.get("age") or {}).get("hardfork"),
        "born": _date((facts.get("birth") or {}).get("timestamp")),
        "last_seen": None if never else _date((life.get("last_tx") or {}).get("timestamp")),
        "never_called": never,
        "proxy": bool(facts.get("proxy")),
        "calls": int(life.get("calls") or 0),
        "scars": int(scars),
        "balance_eth": balance,
        "historian": historian,
        "path": f"ghosts/{addr_dir.name}/",
        "cover": cover if (page.parent / "cover.png").exists() else None,
        "title": story.get("title") or name,
        "tagline": tagline,
    }
    # newest story first: story time, else the page's own mtime (both ISO UTC strings)
    stamp = story.get("generated_at")
    if not stamp:
        stamp = datetime.fromtimestamp(page.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(stamp), entry


def build() -> Path:
    """Write web/ghosts/index.json, web/ghosts/featured.json and web/sitemap.txt; return the index path."""
    web = web_dir()
    ghosts_web = web / "ghosts"
    ghosts_web.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, dict]] = []
    if config.GHOSTS_DIR.exists():
        for addr_dir in sorted(config.GHOSTS_DIR.iterdir()):
            page = ghosts_web / addr_dir.name / "index.html"
            if addr_dir.is_dir() and page.is_file():
                rows.append(_entry(addr_dir, page))
    rows.sort(key=lambda r: (r[0], r[1]["address"]), reverse=True)
    entries = [e for _, e in rows]
    index = ghosts_web / "index.json"
    index.write_text(json.dumps(entries, indent=1, ensure_ascii=False) + "\n")
    featured = dict(rows[0][1], generated_at=rows[0][0]) if rows else None
    (ghosts_web / "featured.json").write_text(json.dumps(featured, indent=1, ensure_ascii=False) + "\n")
    site = site_url()
    urls = [site + "/"] + [f"{site}/{e['path']}" for e in entries]
    (web / "sitemap.txt").write_text("\n".join(urls) + "\n")
    return index


def og_index() -> Path | None:
    """Screenshot web/assets/og-index.html to web/assets/og.png (1200x630) with Playwright.

    Returns the PNG path, or None (with a note on stderr) when Playwright or its browser is missing.
    """
    assets = web_dir() / "assets"
    src, out = assets / "og-index.html", assets / "og.png"
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        typer.echo("og: playwright is not installed; skipped", err=True)
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
                page.goto(src.resolve().as_uri())
                page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
            finally:
                browser.close()
    except Exception as err:  # browser binary missing, sandbox refusal, ...
        typer.echo(f"og: could not render ({err.__class__.__name__}); skipped", err=True)
        return None
    return out


@app.callback()
def _root():
    """The gallery index and deploy helpers."""


@app.command("build")
def build_cmd():
    """Rebuild web/ghosts/index.json and web/sitemap.txt."""
    index = build()
    n = len(json.loads(index.read_text()))
    typer.echo(f"gallery: {n} ghost(s) -> {index}")


@app.command("og")
def og_cmd():
    """Regenerate web/assets/og.png from web/assets/og-index.html (needs Playwright's Chromium)."""
    out = og_index()
    if out:
        typer.echo(f"og: {out}")


if __name__ == "__main__":
    app()
