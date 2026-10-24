"""Curator reads and writes in Postgres (tables from sloth/core/schema.sql). Every function takes a conn."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from sloth.core.models import Enrichment, Link, Triage

# links.status values the Curator writes: new → enriched → kept | reading | valhalla | unsure.
# kept = build candidate (buildable >= 2); reading = worth reading, nothing to prototype.


def upsert_links(conn, links: Iterable[Link]) -> int:
    """Insert new links; existing canonical URLs keep their status. Returns how many were new."""
    before = conn.execute("SELECT count(*) AS n FROM links").fetchone()["n"]
    with conn.cursor() as cur:  # executemany pipelines the round trips (Tiger is ~90 ms away)
        cur.executemany(
            """INSERT INTO links (url, canonical_url, title, folder_path, saved_at, source)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (canonical_url) DO UPDATE
                 SET title = EXCLUDED.title, folder_path = EXCLUDED.folder_path""",
            [(link.url, link.canonical_url, link.title, link.folder_path, link.saved_at, link.source)
             for link in links],
        )
    return conn.execute("SELECT count(*) AS n FROM links").fetchone()["n"] - before


def next_batch(conn, n: int, *, statuses: tuple[str, ...] = ("new", "enriched"),
               source: str | None = None) -> list[dict]:
    """The next n links to work on, newest saves first (2026 before 2025)."""
    return conn.execute(
        """SELECT * FROM links WHERE status = ANY(%s) AND (%s::text IS NULL OR source = %s)
           ORDER BY saved_at DESC NULLS LAST, id LIMIT %s""",
        (list(statuses), source, source, n),
    ).fetchall()


def links_by_ids(conn, ids: list[int]) -> list[dict]:
    return conn.execute("SELECT * FROM links WHERE id = ANY(%s) ORDER BY id", (ids,)).fetchall()


def save_enrichment(conn, e: Enrichment) -> None:
    cols = list(Enrichment.model_fields)
    vals = [getattr(e, c) for c in cols]
    vals[cols.index("fetched_with")] = str(e.fetched_with)
    sets = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "link_id")
    conn.execute(
        f"""INSERT INTO enrichment ({", ".join(cols)}, fetched_at) VALUES ({", ".join(["%s"] * len(cols))}, now())
            ON CONFLICT (link_id) DO UPDATE SET {sets}, fetched_at = now()""",
        vals,
    )
    conn.execute("UPDATE links SET status = 'enriched' WHERE id = %s AND status = 'new'", (e.link_id,))


def enrichment_for(conn, ids: list[int]) -> dict[int, dict]:
    rows = conn.execute("SELECT * FROM enrichment WHERE link_id = ANY(%s)", (ids,)).fetchall()
    return {r["link_id"]: r for r in rows}


def all_links_with_final_url(conn) -> list[dict]:
    """Every link with its post-redirect URL, for duplicate detection across batches."""
    return conn.execute(
        """SELECT l.id, l.canonical_url, l.saved_at, l.status, e.final_url
           FROM links l LEFT JOIN enrichment e ON e.link_id = l.id"""
    ).fetchall()


def save_triage(conn, link_id: int, t: Triage, *, decided_by: str, model: str | None = None,
                tokens_in: int | None = None, tokens_out: int | None = None, ms: int | None = None) -> None:
    conn.execute(
        """INSERT INTO triage (link_id, model, topic, vertical, kind, still_relevant, reason, buildable,
                               one_line_idea, decided_by, tokens_in, tokens_out, ms)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (link_id, model, t.topic, str(t.vertical), str(t.kind), t.still_relevant, t.reason, t.buildable,
         t.one_line_idea, decided_by, tokens_in, tokens_out, ms),
    )


def set_status(conn, link_id: int, status: str, batch_id: str | None = None) -> None:
    conn.execute("UPDATE links SET status = %s, batch_id = COALESCE(%s, batch_id) WHERE id = %s",
                 (status, batch_id, link_id))


def propose_valhalla(conn, link_id: int, reason: str, *, decided_by: str, batch_id: str) -> None:
    conn.execute(
        """INSERT INTO valhalla (link_id, reason, decided_by, batch_id) VALUES (%s, %s, %s, %s)
           ON CONFLICT (link_id) DO UPDATE SET reason = EXCLUDED.reason, decided_by = EXCLUDED.decided_by,
             batch_id = EXCLUDED.batch_id, status = 'proposed', resolved_at = NULL, created_at = now()""",
        (link_id, reason, decided_by, batch_id),
    )
    set_status(conn, link_id, "valhalla", batch_id)


def valhalla_rows(conn, status: str = "proposed", batch_id: str | None = None) -> list[dict]:
    return conn.execute(
        """SELECT v.*, l.url, l.canonical_url, l.title, l.folder_path, l.saved_at
           FROM valhalla v JOIN links l ON l.id = v.link_id
           WHERE v.status = %s AND (%s::text IS NULL OR v.batch_id = %s)
           ORDER BY v.created_at, v.link_id""",
        (status, batch_id, batch_id),
    ).fetchall()


def restore(conn, link_ids: list[int]) -> list[int]:
    """Proposed → restored, link back to kept. Returns the ids that were actually restored."""
    rows = conn.execute(
        """UPDATE valhalla SET status = 'restored', resolved_at = %s
           WHERE link_id = ANY(%s) AND status = 'proposed' RETURNING link_id""",
        (datetime.now(UTC), link_ids),
    ).fetchall()
    done = [r["link_id"] for r in rows]
    if done:
        conn.execute(_BACK_FROM_LIMBO, (done,))
    return done


# A link the author rescues goes to kept if its latest label says buildable >= 2, else to reading.
_BACK_FROM_LIMBO = """
    UPDATE links l SET status = CASE WHEN coalesce((SELECT t.buildable FROM triage t WHERE t.link_id = l.id
                                                   ORDER BY t.created_at DESC LIMIT 1), 0) >= 2
                                     THEN 'kept' ELSE 'reading' END
    WHERE l.id = ANY(%s)"""


def confirm_all(conn) -> list[dict]:
    """Proposed → confirmed (the author said `empty`). Returns the confirmed rows for the export list."""
    rows = valhalla_rows(conn, "proposed")
    if rows:
        conn.execute("UPDATE valhalla SET status = 'confirmed', resolved_at = %s WHERE status = 'proposed'",
                     (datetime.now(UTC),))
    return rows


def status_counts(conn) -> dict[str, int]:
    return {r["status"]: r["n"] for r in conn.execute(
        "SELECT status, count(*) AS n FROM links GROUP BY status").fetchall()}


def unsure_rows(conn) -> list[dict]:
    return conn.execute(
        """SELECT l.id AS link_id, l.title, l.url, t.reason FROM links l
           LEFT JOIN LATERAL (SELECT reason FROM triage WHERE link_id = l.id ORDER BY created_at DESC LIMIT 1) t
             ON true
           WHERE l.status = 'unsure' ORDER BY l.id""").fetchall()


def resolve_unsure(conn, link_ids: list[int], *, keep: bool, batch_id: str = "author") -> list[int]:
    """The author's answer to an unsure link: keep it, or send it to Valhalla (decided_by author)."""
    rows = conn.execute("SELECT id FROM links WHERE id = ANY(%s) AND status = 'unsure'", (link_ids,)).fetchall()
    done = [r["id"] for r in rows]
    if keep and done:
        conn.execute(_BACK_FROM_LIMBO, (done,))
    for i in done:
        if not keep:
            propose_valhalla(conn, i, "the author sent it to Valhalla", decided_by="author", batch_id=batch_id)
    return done


def reading_rows(conn) -> list[dict]:
    return conn.execute(
        """SELECT l.id AS link_id, l.title, l.url, t.vertical, t.topic FROM links l
           LEFT JOIN LATERAL (SELECT vertical, topic FROM triage WHERE link_id = l.id
                              ORDER BY created_at DESC LIMIT 1) t ON true
           WHERE l.status = 'reading' ORDER BY t.vertical, l.saved_at DESC""").fetchall()
