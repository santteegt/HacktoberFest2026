"""Lane 1 CLI: `sloth curate`, `sloth valhalla {show,restore,empty}`, `sloth curator <stage>`."""

from __future__ import annotations

import asyncio
import re
import time
from typing import Annotated

import typer
from rich import print

curator_app = typer.Typer(no_args_is_help=True, help="Curator stages, one at a time (debugging and measurements).")
valhalla_app = typer.Typer(no_args_is_help=True, help="The removal bucket. Nothing here touches Chrome's Bookmarks file.")


def _conn():
    from ..core.db import connect
    return connect()


@curator_app.command("collect")
def collect_cmd() -> None:
    """Read the Reading List folder (read-only) and upsert new links."""
    from ..curator.pipeline import run_collect
    with _conn() as conn:
        print(run_collect(conn))


@curator_app.command("enrich")
def enrich_cmd(limit: Annotated[int, typer.Option(help="How many un-enriched links (0 = all).")] = 0,
               browser: Annotated[bool, typer.Option(help="Use the Lane 3 browser for unreadable pages.")] = True) -> None:
    """HTTP + GitHub (+ browser) enrichment for links that have none yet."""
    from ..curator.pipeline import run_enrich
    with _conn() as conn:
        conn.autocommit = True
        t0 = time.monotonic()
        stats = asyncio.run(run_enrich(conn, limit=limit or None, use_browser=browser))
        print({**stats, "seconds": round(time.monotonic() - t0, 1)})


@curator_app.command("stats")
def stats_cmd() -> None:
    """Link counts by status, enrichment outcome and decision source."""
    from ..curator.pipeline import stats
    with _conn() as conn:
        print(stats(conn))


def curate(batch: Annotated[int, typer.Option("--batch", "-n", help="Links to triage in this batch.")] = 200,
           source: Annotated[str, typer.Option(help="Link source.")] = "reading-list",
           browser: Annotated[bool, typer.Option(help="Use the Lane 3 browser for unreadable pages.")] = True,
           post: Annotated[bool, typer.Option(help="Post the summary and Valhalla list via notify.")] = True) -> None:
    """Collect → enrich → rules → model triage for the next N links; prints the batch summary."""
    from ..curator.pipeline import run_batch
    with _conn() as conn:
        conn.autocommit = True
        result = run_batch(conn, batch, source=source, use_browser=browser)
    from ..core import notify
    from ..curator.report import batch_summary, log_line, valhalla_messages
    print(batch_summary(result))
    if post:
        notify.post("curator", batch_summary(result))
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
        print(measure.run(conn, n, label_n, seed=seed))
    print(f"label file: {measure.OUT / 'labels.md'}")


@curator_app.command("m02-score")
def m02_score_cmd(results: str = "results.json") -> None:
    """Agreement between the author's labels and the model on the M0.2 sample."""
    from ..curator import measure
    print(measure.score(results_name=results))


@curator_app.command("m02-rerun")
def m02_rerun_cmd(tag: str) -> None:
    """Re-label the author-labelled links with the current prompt and score them."""
    from ..curator import measure
    with _conn() as conn:
        print(measure.rerun_labelled(conn, tag))


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
        print(measure.compute_bench(conn, n))


@curator_app.command("reading")
def reading_cmd() -> None:
    """The reading bucket: still worth reading, nothing to prototype. Grouped by vertical."""
    from ..curator import store
    from ..curator.report import reading_messages
    with _conn() as conn:
        rows = store.reading_rows(conn)
    for msg in reading_messages(rows):
        print(msg)
