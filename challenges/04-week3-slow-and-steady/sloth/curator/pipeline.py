"""The Curator's batch: collect → enrich → code rules → model triage → kept / Valhalla / unsure."""

from __future__ import annotations

import asyncio
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from sloth.core.config import settings
from sloth.core.models import Kind, Triage, Vertical

from . import store
from .collect import collect
from .enrich import enrich_many


def run_collect(conn) -> dict:
    s = settings()
    c = collect(s.bookmarks_path, s.bookmarks_folder)
    if not c.folder_found:
        raise SystemExit(f"folder {s.bookmarks_folder!r} not found under the bookmarks bar")
    new = store.upsert_links(conn, c.links)
    return {"in_folder": len(c.links) + len(c.exact_duplicates), "unique": len(c.links),
            "exact_duplicates": len(c.exact_duplicates), "new": new}


async def run_enrich(conn, *, limit: int | None = None, ids: list[int] | None = None) -> dict:
    if ids is not None:
        links = store.links_by_ids(conn, ids)
    else:
        links = conn.execute(
            """SELECT l.* FROM links l LEFT JOIN enrichment e ON e.link_id = l.id
               WHERE e.link_id IS NULL ORDER BY l.saved_at DESC NULLS LAST, l.id LIMIT %s""",
            (limit,)).fetchall()
    results = await enrich_many(links, on_done=lambda e: store.save_enrichment(conn, e))
    return {"enriched": len(results), "by": dict(Counter(str(e.fetched_with) for e in results))}


def stats(conn) -> dict:
    return {
        "links": store.status_counts(conn),
        "enrichment": {r["fetched_with"]: r["n"] for r in conn.execute(
            "SELECT fetched_with, count(*) AS n FROM enrichment GROUP BY 1").fetchall()},
        "triage": {f"{r['decided_by']}": r["n"] for r in conn.execute(
            "SELECT decided_by, count(DISTINCT link_id) AS n FROM triage GROUP BY 1").fetchall()},
        "valhalla": {r["status"]: r["n"] for r in conn.execute(
            "SELECT status, count(*) AS n FROM valhalla GROUP BY 1").fetchall()},
    }


@dataclass
class Item:
    link_id: int
    title: str
    url: str
    outcome: str                 # kept | valhalla | unsure
    reason: str
    decided_by: str              # code | model
    rule: str | None = None      # code rule name, when decided_by == code
    buildable: int = 0
    one_line_idea: str | None = None
    vertical: str | None = None


@dataclass
class BatchResult:
    batch_id: str
    items: list[Item] = field(default_factory=list)
    seconds: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    model_seconds: float = 0.0       # wall time spent waiting on the model (includes queueing)
    compute_seconds: float = 0.0     # Ollama's own compute time
    model: str | None = None
    enriched: dict = field(default_factory=dict)
    collected_new: int = 0

    def by(self, outcome: str) -> list[Item]:
        return [i for i in self.items if i.outcome == outcome]

    @property
    def valhalla(self) -> list[dict]:
        """Valhalla items in the row shape report.valhalla_messages() takes."""
        return [{"link_id": i.link_id, "title": i.title, "url": i.url, "reason": i.reason,
                 "decided_by": i.decided_by} for i in self.by("valhalla")]

    def as_event(self) -> dict:
        d = asdict(self)
        d["items"] = len(self.items)
        d["counts"] = dict(Counter(i.outcome for i in self.items))
        d["rules"] = dict(Counter(i.rule for i in self.items if i.rule))
        return d


def new_batch_id(now: datetime | None = None) -> str:
    return f"b{(now or datetime.now(UTC)):%Y%m%d-%H%M}"


def run_batch(conn, n: int, *, source: str = "reading-list", use_browser: bool = False,
              ids: list[int] | None = None, batch_id: str | None = None,
              on_item=None) -> BatchResult:
    """One Curator batch on the next n untriaged links (or the given ids). Autocommit per link."""
    t0 = time.monotonic()
    res = BatchResult(batch_id=batch_id or new_batch_id())
    if ids is None:
        res.collected_new = run_collect(conn)["new"]
        links = store.next_batch(conn, n, source=source)
    else:
        links = store.links_by_ids(conn, ids)
    if not links:
        res.seconds = round(time.monotonic() - t0, 1)
        return res
    lids = [r["id"] for r in links]
    have = store.enrichment_for(conn, lids)
    missing = [i for i in lids if i not in have]
    if missing:
        res.enriched = asyncio.run(run_enrich(conn, ids=missing))
        have = store.enrichment_for(conn, lids)
    if use_browser:  # its own phase, one Chrome session, before any triage call (one Ollama slot)
        from .enrich import browse_many, browser_candidate
        todo = [r for r in links if browser_candidate(have.get(r["id"]))]
        if todo:
            asyncio.run(browse_many(todo, have, on_done=lambda e: store.save_enrichment(conn, e)))
            have = store.enrichment_for(conn, lids)
    from .rules import DupeIndex, judge
    from .triage import decide, label
    dupes = DupeIndex(store.all_links_with_final_url(conn))
    for link in links:
        enr = have.get(link["id"])
        title = link.get("title") or link["canonical_url"]
        if v := judge(link, enr, dupes):
            item = Item(link["id"], title, link["url"], "valhalla", v.reason, "code", rule=v.rule)
            store.save_triage(conn, link["id"], Triage(topic=v.rule, vertical=Vertical.other, kind=Kind.other,
                                                       still_relevant=False, reason=v.reason, buildable=0),
                              decided_by="code")
            store.propose_valhalla(conn, link["id"], v.reason, decided_by="code", batch_id=res.batch_id)
        else:
            lab = label(link, enr)
            outcome = decide(lab, link, enr)
            t = lab.triage
            res.tokens_in += lab.tokens_in
            res.tokens_out += lab.tokens_out
            res.model_seconds += lab.ms / 1000
            res.compute_seconds += lab.compute_ms / 1000
            res.model = lab.model
            store.save_triage(conn, link["id"], t, decided_by="model", model=lab.model,
                              tokens_in=lab.tokens_in, tokens_out=lab.tokens_out, ms=lab.ms)
            reason = t.reason if lab.verified else f"unverified label ({'; '.join(lab.problems)}): {t.reason}"
            item = Item(link["id"], title, link["url"], outcome, reason[:240], "model", buildable=t.buildable,
                        one_line_idea=t.one_line_idea, vertical=str(t.vertical))
            if outcome == "valhalla":
                store.propose_valhalla(conn, link["id"], t.reason, decided_by="model", batch_id=res.batch_id)
            else:
                store.set_status(conn, link["id"], outcome, res.batch_id)
        res.items.append(item)
        if on_item:
            on_item(item)
    res.seconds = round(time.monotonic() - t0, 1)
    res.model_seconds = round(res.model_seconds, 1)
    res.compute_seconds = round(res.compute_seconds, 1)
    return res


def unreadable_links(conn, limit: int | None = None) -> list[dict]:
    """Browser candidates (see enrich.browser_candidate) the author has not settled yet."""
    from .enrich import browser_candidate
    rows = conn.execute(
        """SELECT l.* FROM links l JOIN enrichment e ON e.link_id = l.id
           LEFT JOIN valhalla v ON v.link_id = l.id
           WHERE e.fetched_with <> 'stagehand'
             AND (l.status IN ('new', 'enriched', 'kept', 'reading', 'unsure')
                  OR (l.status = 'valhalla' AND v.status = 'proposed' AND v.decided_by = 'model'))
           ORDER BY l.saved_at DESC NULLS LAST""").fetchall()
    enr = store.enrichment_for(conn, [r["id"] for r in rows])
    picked = [r for r in rows if browser_candidate(enr.get(r["id"]))]
    return picked[:limit] if limit else picked


def run_browse(conn, *, limit: int | None = None, batch_id: str | None = None, retriage: bool = True,
               on_try=None) -> dict:
    """Browser pass over unreadable links, then (separately, so the two never interleave on the one
    Ollama slot) re-triage the ones it read, if they were triaged before."""
    from .enrich import browse_many
    from .triage import decide, label
    t0 = time.monotonic()
    links = unreadable_links(conn, limit)
    enr = store.enrichment_for(conn, [r["id"] for r in links])
    tries: list[dict] = []

    def record(t: dict) -> None:
        tries.append(t)
        if on_try:
            on_try(t)
    read = asyncio.run(browse_many(links, enr, on_done=lambda e: store.save_enrichment(conn, e), on_try=record))
    browse_s = round(time.monotonic() - t0, 1)
    bid = batch_id or new_batch_id() + "-browser"
    moves: Counter = Counter()
    have = store.enrichment_for(conn, [e.link_id for e in read])
    for link in store.links_by_ids(conn, [e.link_id for e in read]) if retriage else []:
        if link["status"] in ("new", "enriched"):
            continue  # never triaged: the normal batch will do it with the new text
        lab = label(link, have.get(link["id"]))
        outcome = decide(lab, link, have.get(link["id"]))
        store.save_triage(conn, link["id"], lab.triage, decided_by="model", model=lab.model,
                          tokens_in=lab.tokens_in, tokens_out=lab.tokens_out, ms=lab.ms)
        before = link["status"]
        if outcome == "valhalla":
            store.propose_valhalla(conn, link["id"], lab.triage.reason, decided_by="model", batch_id=bid)
        else:
            if before == "valhalla":  # the page says otherwise now: withdraw the model's proposal
                conn.execute("UPDATE valhalla SET status = 'restored', resolved_at = now() WHERE link_id = %s",
                             (link["id"],))
            store.set_status(conn, link["id"], outcome, bid)
        moves[f"{before}->{outcome}"] += 1
    secs = sorted(t["seconds"] for t in tries)
    ok_secs = sorted(t["seconds"] for t in tries if t["ok"])
    return {"tried": len(links), "read_by_browser": len(read), "moves": dict(moves),
            "by_host": dict(Counter(f"{t['host'] if t['host'] in ('x.com', 'facebook.com') else 'other'}:"
                                    f"{'ok' if t['ok'] else 'fail'}" for t in tries)),
            "fail_reasons": dict(Counter((t["reason"] or "")[:60] for t in tries if not t["ok"]).most_common(8)),
            "median_s_per_extract": secs[len(secs) // 2] if secs else None,
            "median_s_per_success": ok_secs[len(ok_secs) // 2] if ok_secs else None,
            "browse_seconds": browse_s, "seconds": round(time.monotonic() - t0, 1)}


def recheck_code_verdicts(conn) -> dict:
    """Re-run the code rules over proposed code verdicts after a rule change: withdraw the ones the
    rules no longer support (links go back to `enriched` for the next batch) and refresh the reason
    of the ones that now fire a different rule. The author's restores and confirms are untouched."""
    from .rules import DupeIndex, judge
    rows = conn.execute(
        """SELECT l.*, v.reason AS v_reason FROM valhalla v JOIN links l ON l.id = v.link_id
           WHERE v.status = 'proposed' AND v.decided_by = 'code'""").fetchall()
    enr = store.enrichment_for(conn, [r["id"] for r in rows])
    dupes = DupeIndex(store.all_links_with_final_url(conn))
    withdrawn, updated = [], []
    for r in rows:
        v = judge(r, enr.get(r["id"]), dupes)
        if v is None:
            withdrawn.append(r["id"])
        elif v.reason != r["v_reason"]:
            conn.execute("UPDATE valhalla SET reason = %s WHERE link_id = %s", (v.reason, r["id"]))
            updated.append(r["id"])
    if withdrawn:
        conn.execute("DELETE FROM valhalla WHERE link_id = ANY(%s) AND status = 'proposed'", (withdrawn,))
        conn.execute("UPDATE links SET status = 'enriched' WHERE id = ANY(%s)", (withdrawn,))
    return {"withdrawn": withdrawn, "reason_updated": updated}


def retriage_stale(conn, *, batch_id: str | None = None) -> dict:
    """Re-label links whose enrichment is newer than their latest label (e.g. the browser read them
    after triage, and the browser pass stopped before its own re-triage). Author-settled links
    (restored/confirmed Valhalla) and code verdicts are left alone."""
    from .triage import decide, label
    rows = conn.execute(
        """SELECT l.* FROM links l JOIN enrichment e ON e.link_id = l.id
           JOIN LATERAL (SELECT created_at, decided_by FROM triage WHERE link_id = l.id
                         ORDER BY created_at DESC LIMIT 1) t ON true
           LEFT JOIN valhalla v ON v.link_id = l.id
           WHERE e.fetched_at > t.created_at AND t.decided_by = 'model'
             AND (l.status IN ('kept', 'reading', 'unsure')
                  OR (l.status = 'valhalla' AND v.status = 'proposed' AND v.decided_by = 'model'))
           ORDER BY l.id""").fetchall()
    bid = batch_id or new_batch_id() + "-retriage"
    have = store.enrichment_for(conn, [r["id"] for r in rows])
    moves: Counter = Counter()
    compute_ms = 0
    for link in rows:
        lab = label(link, have.get(link["id"]))
        compute_ms += lab.compute_ms
        outcome = decide(lab, link, have.get(link["id"]))
        store.save_triage(conn, link["id"], lab.triage, decided_by="model", model=lab.model,
                          tokens_in=lab.tokens_in, tokens_out=lab.tokens_out, ms=lab.ms)
        before = link["status"]
        if outcome == "valhalla":
            store.propose_valhalla(conn, link["id"], lab.triage.reason, decided_by="model", batch_id=bid)
        else:
            if before == "valhalla":
                conn.execute("UPDATE valhalla SET status = 'restored', resolved_at = now() WHERE link_id = %s",
                             (link["id"],))
            store.set_status(conn, link["id"], outcome, bid)
        moves[f"{before}->{outcome}"] += 1
    return {"relabelled": len(rows), "moves": dict(moves),
            "compute_ms_per_link": round(compute_ms / len(rows)) if rows else None}
