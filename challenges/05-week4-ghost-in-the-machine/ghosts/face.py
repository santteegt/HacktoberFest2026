"""A ghost's face: Wayback Machine screenshots of the dapp's site, first life and last life.

archive.org has no screenshot API, so we pick captures from the CDX index (ghosts.sources.wayback) and
render https://web.archive.org/web/<ts>/<url> in headless Chromium (Playwright) at 1200x800 with the
Wayback toolbar hidden. Output, per LANES.md:

    data/ghosts/<address>/shots/<ts>.png
    data/ghosts/<address>/shots/index.json   [{ts, url, file, role: first|last|cover, site}]
    data/ghosts/<address>/shots/report.json  failures and timings (index.json stays a clean list)

Failures (timeouts, empty pages, no 200 capture) are recorded, never raised.
"""
from __future__ import annotations
import json, time
import typer
from . import config
from .facts import ghost_dir
from .sources import wayback

VIEWPORT = {"width": 1200, "height": 800}
HIDE_TOOLBAR = "#wm-ipp-base, #wm-ipp, #wm-ipp-print { display: none !important; }"
NAV_TIMEOUT_MS = 45_000
SETTLE_MS = 2_500
MIN_PNG_BYTES = 8_000  # smaller than this is almost surely a blank frame
RETRIES = 2            # when a render is blank, try this many neighbouring 200 captures


def _ts_from_iso(iso: str | None) -> str | None:
    """'2016-02-19T21:51:14.000000Z' -> '20160219215114'."""
    if not iso:
        return None
    digits = "".join(ch for ch in iso[:19] if ch.isdigit())
    return digits if len(digits) >= 8 else None


def select_captures(caps: list[dict], last_tx_ts: str | None) -> dict:
    """Pure choice logic. `caps` are wayback.captures() rows (oldest first). Returns
    {"first": cap|None, "last": cap|None, "note": str}. first = first 200 capture; last = the last 200
    capture whose timestamp is not after the ghost's last transaction, else the latest 200 capture."""
    ok = sorted((c for c in caps if str(c.get("status")) == "200"), key=lambda c: c["ts"])
    if not ok:
        return {"first": None, "last": None, "note": "no 200-status capture"}
    first = ok[0]
    cand = {"first": ok[:RETRIES + 1]}
    note = "last = latest 200 capture (no last transaction known)"
    last = ok[-1]
    if last_tx_ts:
        before = [c for c in ok if c["ts"] <= last_tx_ts.ljust(14, "9")[:14]]
        if before:
            last, note = before[-1], "last = last 200 capture before the ghost's last transaction"
            cand["last"] = before[::-1][:RETRIES + 1]
        else:
            note = "last = latest 200 capture (every capture is after the last transaction)"
    cand.setdefault("last", ok[::-1][:RETRIES + 1])
    return {"first": first, "last": last, "note": note, "candidates": cand}


def build_index(results: list[dict]) -> list[dict]:
    """results: [{site, role, ts, url, file}] for the shots that rendered. Adds the cover (= the first
    site's first shot) as a third role pointing at the same file."""
    out = [dict(r) for r in results]
    firsts = [r for r in results if r["role"] == "first"]
    if firsts:
        out.append({**firsts[0], "role": "cover"})
    return out


def _render(page, ts: str, url: str, dest) -> dict:
    target = wayback.snapshot_url(ts, url)
    t0 = time.time()
    try:
        page.goto(target, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        page.add_style_tag(content=HIDE_TOOLBAR)
        page.wait_for_timeout(SETTLE_MS)
        page.add_style_tag(content=HIDE_TOOLBAR)
        page.screenshot(path=str(dest), full_page=False)
        size = dest.stat().st_size
        if size < MIN_PNG_BYTES:
            return {"ok": False, "error": f"screenshot only {size} bytes (blank frame?)", "seconds": round(time.time() - t0, 1)}
        return {"ok": True, "bytes": size, "final_url": page.url, "seconds": round(time.time() - t0, 1)}
    except Exception as e:  # timeouts, net errors: record, move on
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:160]}", "seconds": round(time.time() - t0, 1)}


def capture(address: str, sites: list[str] | None = None) -> dict:
    """Screenshot the first and last live captures of each site. Returns
    {"address", "shots": index list, "report": [...], "files": {file: bytes}}."""
    address = address.lower()
    gd = ghost_dir(address)
    facts = {}
    if (gd / "facts.json").exists():
        facts = json.loads((gd / "facts.json").read_text())
    if not sites:
        sites = [s.get("host") for s in facts.get("sites", []) if s.get("host")]
    last_tx_ts = _ts_from_iso(((facts.get("life") or {}).get("last_tx") or {}).get("timestamp"))
    shots_dir = gd / "shots"
    shots_dir.mkdir(exist_ok=True)

    plan, report = [], []
    for site in sites or []:
        try:
            caps = wayback.captures(site)
        except Exception as e:
            report.append({"site": site, "ok": False, "error": f"cdx: {type(e).__name__}: {str(e)[:120]}"})
            continue
        sel = select_captures(caps, last_tx_ts)
        report.append({"site": site, "ok": bool(sel["first"]), "captures": len(caps), "note": sel["note"]})
        if not sel["first"]:
            continue
        plan.append((site, "first", sel["candidates"]["first"]))
        if sel["last"]["ts"] != sel["first"]["ts"]:
            plan.append((site, "last", sel["candidates"]["last"]))

    results = []
    if plan:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(viewport=VIEWPORT, user_agent=config.UA + " screenshot")
                page = ctx.new_page()
                for site, role, cands in plan:
                    for cap in cands:
                        dest = shots_dir / f"{cap['ts']}.png"
                        r = _render(page, cap["ts"], cap["url"], dest)
                        report.append({"site": site, "role": role, "ts": cap["ts"], **r})
                        time.sleep(1.5)  # be polite to web.archive.org
                        if r["ok"]:
                            results.append({"ts": cap["ts"], "url": wayback.snapshot_url(cap["ts"], cap["url"]),
                                            "file": str(dest.relative_to(gd)), "role": role, "site": site})
                            break
                        if dest.exists():
                            dest.unlink()
                browser.close()
        except Exception as e:
            report.append({"ok": False, "error": f"playwright: {type(e).__name__}: {str(e)[:200]}"})

    index = build_index(results)
    (shots_dir / "index.json").write_text(json.dumps(index, indent=1))
    (shots_dir / "report.json").write_text(json.dumps(report, indent=1))
    return {"address": address, "shots": index, "report": report,
            "files": {r["file"]: (gd / r["file"]).stat().st_size for r in results}}


# ----------------------------------------------------------------------------- CLI (wired by the coordinator)


def face_cmd(address: str = typer.Argument(..., help="ghost address (facts.json should exist: run summon first)"),
             site: list[str] = typer.Option(None, "--site", help="site to capture; repeat for several (default: facts.json sites)")):
    """Screenshot the first and last live Wayback captures of the ghost's site(s)."""
    r = capture(address, site or None)
    for s in r["shots"]:
        typer.echo(f"{s['role']:5} {s['ts']} {s['site']} -> {s['file']}")
    for x in r["report"]:
        if x.get("ok") is False:
            typer.echo(f"failed: {x}", err=True)
    if not r["shots"]:
        raise typer.Exit(1)
