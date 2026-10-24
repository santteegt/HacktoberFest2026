"""Board reads and writes against the shared schema (sloth/core/schema.sql).

Kept links come from the Curator's tables: `links.status = 'kept'` (Curator statuses:
new → enriched → kept | reading | valhalla | unsure; `reading` never becomes a card) with the
latest triage row per link, minus links in Valhalla (unless restored) and links on a live card.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from ..core.models import Card, Column

# A card that is archived or killed releases its links for a new card.
LIVE_COLUMNS = ("backlog", "today", "building", "built")


@dataclass
class KeptLink:
    link_id: int
    url: str
    title: str | None
    saved_at: datetime | None
    folder_path: str | None
    topic: str
    vertical: str
    kind: str
    buildable: int
    one_line_idea: str | None
    reason: str | None = None


def current_schema(conn) -> str:
    return conn.execute("SELECT current_schema() AS s").fetchone()["s"]


def kept_links(conn) -> list[KeptLink]:
    rows = conn.execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (link_id) * FROM triage ORDER BY link_id, created_at DESC
        )
        SELECT l.id AS link_id, l.url, l.title, l.saved_at, l.folder_path,
               t.topic, t.vertical, t.kind, t.buildable, t.one_line_idea, t.reason
        FROM latest t JOIN links l ON l.id = t.link_id
        LEFT JOIN valhalla v ON v.link_id = l.id AND v.status <> 'restored'
        WHERE l.status = 'kept' AND t.buildable >= 2 AND v.link_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM cards c WHERE c."column" = ANY(%s) AND l.id = ANY(c.link_ids))
        ORDER BY l.id
        """,
        (list(LIVE_COLUMNS),),
    ).fetchall()
    return [KeptLink(**r) for r in rows]


def links_by_id(conn, ids: list[int]) -> dict[int, dict]:
    if not ids:
        return {}
    rows = conn.execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (link_id) * FROM triage WHERE link_id = ANY(%s)
            ORDER BY link_id, created_at DESC
        )
        SELECT l.id, l.url, l.title, l.saved_at, t.topic, t.one_line_idea, t.buildable
        FROM links l LEFT JOIN latest t ON t.link_id = l.id WHERE l.id = ANY(%s)
        """,
        (ids, ids),
    ).fetchall()
    return {r["id"]: r for r in rows}


def card_ids(conn) -> set[str]:
    return {r["id"] for r in conn.execute("SELECT id FROM cards").fetchall()}


def insert_card(conn, card: Card) -> None:
    conn.execute(
        """
        INSERT INTO cards (id, title, vertical, learning_goal, hypothesis, done_means,
                           box_minutes, link_ids, kill_criteria, "column", picked_on)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (card.id, card.title, card.vertical.value, card.learning_goal, card.hypothesis,
         card.done_means, card.box_minutes, card.link_ids, card.kill_criteria,
         card.column.value, card.picked_on),
    )


def get_card(conn, card_id: str) -> dict | None:
    return conn.execute("SELECT * FROM cards WHERE id = %s", (card_id,)).fetchone()


def all_cards(conn, columns: tuple[str, ...] | None = None) -> list[dict]:
    if columns:
        return conn.execute(
            'SELECT * FROM cards WHERE "column" = ANY(%s) ORDER BY created_at, id',
            (list(columns),)).fetchall()
    return conn.execute("SELECT * FROM cards ORDER BY created_at, id").fetchall()


def move_card(conn, card_id: str, column: Column, *, picked_on: date | None = None) -> None:
    if picked_on is not None:
        conn.execute(
            'UPDATE cards SET "column" = %s, moved_at = now(), picked_on = %s WHERE id = %s',
            (column.value, picked_on, card_id))
    else:
        conn.execute('UPDATE cards SET "column" = %s, moved_at = now() WHERE id = %s',
                     (column.value, card_id))


def latest_runs(conn) -> dict[str, dict]:
    """Latest run per card (the Builder writes these; see LANES.md L3 → L2)."""
    rows = conn.execute(
        "SELECT DISTINCT ON (card_id) * FROM runs ORDER BY card_id, started_at DESC, id DESC"
    ).fetchall()
    return {r["card_id"]: r for r in rows}


def runs_for(conn, card_id: str) -> list[dict]:
    return conn.execute("SELECT * FROM runs WHERE card_id = %s ORDER BY started_at, id",
                        (card_id,)).fetchall()


def link_counts(conn) -> dict[str, int]:
    """Reading List totals for the Project README status block."""
    row = conn.execute(
        """
        SELECT
          (SELECT count(*) FROM links) AS collected,
          (SELECT count(*) FROM links WHERE status = 'kept') AS kept,
          (SELECT count(*) FROM valhalla WHERE status <> 'restored') AS valhalla,
          (SELECT count(*) FROM valhalla WHERE status = 'confirmed') AS valhalla_confirmed,
          (SELECT count(*) FROM links WHERE status IN ('new', 'enriched')) AS untriaged,
          (SELECT count(*) FROM links WHERE status = 'reading') AS reading,
          (SELECT count(*) FROM links WHERE status = 'unsure') AS unsure
        """
    ).fetchone()
    return dict(row)


def last_touched(conn) -> dict[str, date]:
    """Most recent day each vertical had a card picked."""
    rows = conn.execute(
        "SELECT vertical, max(picked_on) AS d FROM cards WHERE picked_on IS NOT NULL GROUP BY vertical"
    ).fetchall()
    return {r["vertical"]: r["d"] for r in rows}
