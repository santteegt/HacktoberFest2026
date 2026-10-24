"""Lane 1 CLI: `sloth curate`, `sloth valhalla {show,restore,empty}`, `sloth curator <stage>`."""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Annotated

import typer

curator_app = typer.Typer(no_args_is_help=True, help="Curator stages, one at a time (debugging and measurements).")
valhalla_app = typer.Typer(no_args_is_help=True, help="The removal bucket. Nothing here touches Chrome's Bookmarks file.")


def _out(value) -> None:
    """Plain stdout (never rich: it wraps at 80 columns, which breaks Discord-ready text)."""
    print(value if isinstance(value, str) else json.dumps(value, indent=1, default=str))


def _conn():
    from ..core.db import connect
    return connect()


@curator_app.command("collect")
def collect_cmd() -> None:
    """Read the Reading List folder (read-only) and upsert new links."""
    from ..curator.pipeline import run_collect
    with _conn() as conn:
        _out(run_collect(conn))


@curator_app.command("enrich")
def enrich_cmd(limit: Annotated[int, typer.Option(help="How many un-enriched links (0 = all).")] = 0) -> None:
    """HTTP + GitHub enrichment for links that have none yet (the browser is `sloth curator browse`)."""
    from ..curator.pipeline import run_enrich
    with _conn() as conn:
        conn.autocommit = True
        t0 = time.monotonic()
        stats = asyncio.run(run_enrich(conn, limit=limit or None))
        _out({**stats, "seconds": round(time.monotonic() - t0, 1)})


@curator_app.command("stats")
def stats_cmd() -> None:
    """Link counts by status, enrichment outcome and decision source."""
    from ..curator.pipeline import stats
    with _conn() as conn:
        _out(stats(conn))


def curate(batch: Annotated[int, typer.Option("--batch", "-n", help="Links to triage in this batch.")] = 200,
           source: Annotated[str, typer.Option(help="Link source.")] = "reading-list",
           browser: Annotated[bool, typer.Option(help="Read x.com and JS-only pages with a visible local Chrome first.")] = False,
           post: Annotated[bool, typer.Option(help="Post the summary and Valhalla list via notify.")] = True) -> None:
    """Collect → enrich → rules → model triage for the next N links; prints the batch summary."""
    from ..curator.pipeline import run_batch
    with _conn() as conn:
        conn.autocommit = True
        result = run_batch(conn, batch, source=source, use_browser=browser)
    from ..core import notify
    from ..curator.report import batch_summary, chunk, log_line, valhalla_messages
    if not post:
        print(batch_summary(result))
    else:
        for msg in chunk(batch_summary(result).split("\n")):
            notify.post("curator", msg)
        for msg in valhalla_messages(result.valhalla, header=f"Valhalla, batch {result.batch_id}"):
            notify.post("valhalla", msg)
        notify.log("curator", "batch", log_line(result), result.as_event())


def _parse_ids(text: list[str]) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", " ".join(text))]


@valhalla_app.command("show")
def valhalla_show(batch: Annotated[str | None, typer.Option(help="Only this batch id.")] = None) -> None:
    """List proposed Valhalla links as numbered (by link id) Discord-ready text."""
    from ..curator import store
    from ..curator.report import valhalla_messages
    with _conn() as conn:
        rows = store.valhalla_rows(conn, "proposed", batch)
    for msg in valhalla_messages(rows, header="Valhalla (proposed)"):
        print(msg)


@valhalla_app.command("restore")
def valhalla_restore(ids: Annotated[list[str], typer.Argument(help="Link ids as listed, e.g. `3, 7` or `3 7`.")]) -> None:
    """Take links back out of Valhalla (they become kept)."""
    from ..curator import store
    wanted = _parse_ids(ids)
    with _conn() as conn:
        done = store.restore(conn, wanted)
    missing = sorted(set(wanted) - set(done))
    print(f"restored {len(done)}: {', '.join(f'#{i}' for i in done) or '-'}"
          + (f"; not in Valhalla: {', '.join(f'#{i}' for i in missing)}" if missing else ""))


@valhalla_app.command("empty")
def valhalla_empty() -> None:
    """Confirm every proposed link and write the removal list. Never edits the Bookmarks file."""
    from ..curator import store
    from ..curator.report import write_export
    with _conn() as conn:
        rows = store.confirm_all(conn)
    if not rows:
        print("Valhalla is already empty.")
        return
    path = write_export(rows)
    print(f"confirmed {len(rows)} links. Removal list for Chrome: {path}")


def register(app: typer.Typer) -> None:
    app.command("curate")(curate)
    app.add_typer(valhalla_app, name="valhalla")
    app.add_typer(curator_app, name="curator")


@curator_app.command("m02")
def m02_cmd(n: int = 50, label_n: int = 20, seed: int = 26) -> None:
    """M0.2: triage n random real links, measure speed, write the blind labelling file to .sloth/m02/."""
    from ..curator import measure
    with _conn() as conn:
        _out(measure.run(conn, n, label_n, seed=seed))
    print(f"label file: {measure.OUT / 'labels.md'}")


@curator_app.command("m02-score")
def m02_score_cmd(results: str = "results.json") -> None:
    """Agreement between the author's labels and the model on the M0.2 sample."""
    from ..curator import measure
    _out(measure.score(results_name=results))


@curator_app.command("m02-rerun")
def m02_rerun_cmd(tag: str) -> None:
    """Re-label the author-labelled links with the current prompt and score them."""
    from ..curator import measure
    with _conn() as conn:
        _out(measure.rerun_labelled(conn, tag))


@curator_app.command("unsure")
def unsure_cmd() -> None:
    """Links the verifier or the rules could not settle; the author answers `keep` or `valhalla`."""
    from ..curator import store
    from ..curator.report import chunk
    with _conn() as conn:
        rows = store.unsure_rows(conn)
    lines = [f"**Unsure**: {len(rows)} links. Reply `keep <ids>` or `valhalla <ids>`."] + [
        f"`#{r['link_id']}` {r['title'] or r['url']}" for r in rows]
    for msg in chunk(lines):
        print(msg)


@curator_app.command("keep")
def keep_cmd(ids: Annotated[list[str], typer.Argument(help="Unsure link ids, e.g. `12, 40`.")]) -> None:
    """Keep unsure links (to build if their label says buildable >= 2, else to the reading bucket)."""
    from ..curator import store
    with _conn() as conn:
        done = store.resolve_unsure(conn, _parse_ids(ids), keep=True)
    print(f"kept {len(done)}: {', '.join(f'#{i}' for i in done) or '-'}")


@curator_app.command("drop")
def drop_cmd(ids: Annotated[list[str], typer.Argument(help="Unsure link ids, e.g. `12, 40`.")]) -> None:
    """Send unsure links to Valhalla (proposed; `sloth valhalla empty` confirms)."""
    from ..curator import store
    with _conn() as conn:
        done = store.resolve_unsure(conn, _parse_ids(ids), keep=False)
    print(f"sent to Valhalla {len(done)}: {', '.join(f'#{i}' for i in done) or '-'}")


@curator_app.command("bench")
def bench_cmd(n: int = 15) -> None:
    """Model compute per link from Ollama's own durations (ignores queueing behind other lanes)."""
    from ..curator import measure
    with _conn() as conn:
        _out(measure.compute_bench(conn, n))


@curator_app.command("reading")
def reading_cmd() -> None:
    """The reading bucket: still worth reading, nothing to prototype. Grouped by vertical."""
    from ..curator import store
    from ..curator.report import reading_messages
    with _conn() as conn:
        rows = store.reading_rows(conn)
    for msg in reading_messages(rows):
        print(msg)


@curator_app.command("browse")
def browse_cmd(limit: Annotated[int, typer.Option(help="How many browser candidates (0 = all).")] = 0,
               retriage: Annotated[bool, typer.Option(help="Re-label links that were already triaged.")] = True) -> None:
    """Read x.com and JS-only pages with Lane 3's browser (visible local Chrome), then re-triage them.
    Prints one line per extract (host, ok, seconds) and a summary."""
    from ..curator.enrich import browser_session
    from ..curator.pipeline import run_browse
    if browser_session is None:
        raise SystemExit("sloth.builder.browser is not available")
    with _conn() as conn:
        conn.autocommit = True
        _out(run_browse(conn, limit=limit or None, retriage=retriage,
                        on_try=lambda t: print(json.dumps(t), flush=True)))


@curator_app.command("recheck")
def recheck_cmd() -> None:
    """Re-apply the code rules to proposed code verdicts (after a rule change)."""
    from ..curator.pipeline import recheck_code_verdicts
    with _conn() as conn:
        conn.autocommit = True
        _out(recheck_code_verdicts(conn))


@curator_app.command("retriage-stale")
def retriage_stale_cmd() -> None:
    """Re-label links whose enrichment changed after their last model label."""
    from ..curator.pipeline import retriage_stale
    with _conn() as conn:
        conn.autocommit = True
        _out(retriage_stale(conn))
