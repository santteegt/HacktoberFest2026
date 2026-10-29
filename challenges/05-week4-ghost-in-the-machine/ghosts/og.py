"""Link-preview images: web/ghosts/<address>/og.png, 1200x630, one per ghost.

template/og.html is filled from the same facts / verdict / story as the page (ghosts.render), with the same
palette and inline SVG characters, then screenshotted in headless Chromium (Playwright, as ghosts/face.py does).
No network: the card is loaded with set_content and has no external assets. When Playwright or its browser is
missing, nothing is written, a note goes to stderr, and the pipeline carries on.
"""
from __future__ import annotations

import sys
from pathlib import Path
from string import Template

import typer

from . import config
from . import render as R

WIDTH, HEIGHT = 1200, 630
OG_TEMPLATE = R.TEMPLATE_DIR / "og.html"


def _page(address: str, data_dir: Path | str | None, out_dir: Path | str | None) -> R._Page:
    data_dir = Path(data_dir) if data_dir else config.GHOSTS_DIR
    out_root = Path(out_dir) if out_dir else R.DEFAULT_OUT
    addr = address.strip().lower()
    folder = data_dir / addr
    if not (folder / "facts.json").is_file():
        raise FileNotFoundError(f"no facts.json for {address} in {data_dir}")
    return R._Page(R._Tpl(), folder, out_root / addr)


def html_for(address: str, data_dir: Path | str | None = None, out_dir: Path | str | None = None) -> str:
    """The filled og.html for one ghost (pure: no browser, no files written)."""
    p = _page(address, data_dir, out_dir)
    m = p.meta()
    e = R.e
    stage = p.svg("storyteller")
    if p.kind == "banished":
        stage += p.svg("gravestone")
    stage += p.svg("contract") if p.kind == "alive" else p.svg("ghost")
    chips = f'<span class="chip">Born {m["born"].year}</span>' if m["born"] else ""
    name = p.display_name
    name_line = name if name.startswith("Unknown ghost soul") else f"{name} · {R._short(p.addr)}"
    return Template(OG_TEMPLATE.read_text(encoding="utf-8")).substitute(
        kind=p.kind,
        badge=e(R.KINDS[p.kind]),
        age=e(m["age"]),
        extra_chips=chips,
        title=e(m["title"]),
        title_class="long" if len(m["title"]) > 44 else "",
        tagline=e(m["description"]),
        name=e(name_line),
        site=e(R.SITE_NAME),
        picado=p.svg("papel-picado"),
        stage=stage,
    )


def _screenshot(jobs: list[tuple[str, Path]]) -> list[Path]:
    """Render each (html, dest) at exactly WIDTH x HEIGHT. Returns the files written; [] if no browser."""
    if not jobs:
        return []
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # playwright not installed
        print(f"og: skipped, Playwright unavailable ({type(exc).__name__}: {exc})", file=sys.stderr)
        return []
    done: list[Path] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
            page = ctx.new_page()
            for html_doc, dest in jobs:
                try:
                    page.set_content(html_doc, wait_until="load")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(dest), clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT})
                    done.append(dest)
                except Exception as exc:
                    print(f"og: {dest.parent.name} failed: {type(exc).__name__}: {str(exc)[:160]}", file=sys.stderr)
            browser.close()
    except Exception as exc:  # browser binary missing, launch failure
        first = str(exc).strip().splitlines()[0][:200] if str(exc).strip() else ""
        print(f"og: skipped, Chromium could not start ({type(exc).__name__}: {first})", file=sys.stderr)
    return done


def make(address: str, data_dir: Path | str | None = None, out_dir: Path | str | None = None) -> Path | None:
    """Write <out_dir>/<address>/og.png. Returns its path, or None when it was skipped."""
    p = _page(address, data_dir, out_dir)
    dest = p.out / "og.png"
    written = _screenshot([(html_for(address, data_dir, out_dir), dest)])
    return written[0] if written else None


def make_all(data_dir: Path | str | None = None, out_dir: Path | str | None = None) -> list[Path]:
    """og.png for every ghost folder with a facts.json, with one browser for all of them."""
    data_dir = Path(data_dir) if data_dir else config.GHOSTS_DIR
    out_root = Path(out_dir) if out_dir else R.DEFAULT_OUT
    jobs = []
    for folder in sorted(d for d in data_dir.iterdir() if (d / "facts.json").is_file()):
        try:
            jobs.append((html_for(folder.name, data_dir, out_root), out_root / folder.name.lower() / "og.png"))
        except Exception as exc:
            print(f"og: {folder.name} skipped: {exc}", file=sys.stderr)
    return _screenshot(jobs)


# ----------------------------------------------------------------------------- CLI (wired by the coordinator)

def og_cmd(address: str = typer.Argument(..., help="ghost address (facts.json must exist)")):
    """Make the 1200x630 link-preview image web/ghosts/<address>/og.png."""
    path = make(address)
    typer.echo(path if path else "og: skipped (no browser); the page still renders")


def og_all_cmd():
    """Make og.png for every ghost in data/ghosts."""
    for path in make_all():
        typer.echo(path)

