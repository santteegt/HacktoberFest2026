"""`sloth board seed-fixtures`: synthetic links + triage into a lane schema (never `public`)."""

from __future__ import annotations

import json
from pathlib import Path

from . import store

FIX = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def seed(conn, *, allow_public: bool = False) -> dict[str, int]:
    schema = store.current_schema(conn)
    if schema == "public" and not allow_public:
        raise RuntimeError("refusing to seed fixtures into `public` (the Curator's real data); "
                           "add ?options=-csearch_path%3Dlane_board to SLOTH_DATABASE_URL")
    links = json.loads((FIX / "links.json").read_text())
    triage = json.loads((FIX / "triage.json").read_text())
    ids: list[int] = []
    for link in links:
        row = conn.execute(
            """
            INSERT INTO links (url, canonical_url, title, folder_path, saved_at, source, status)
            VALUES (%(url)s, %(canonical_url)s, %(title)s, %(folder_path)s, %(saved_at)s,
                    %(source)s, 'new')
            ON CONFLICT (canonical_url) DO UPDATE SET title = EXCLUDED.title
            RETURNING id
            """, link).fetchone()
        ids.append(row["id"])
    conn.execute("DELETE FROM triage WHERE link_id = ANY(%s)", (ids,))
    conn.execute("DELETE FROM valhalla WHERE link_id = ANY(%s)", (ids,))
    for t in triage:
        link_id = ids[t["link_index"]]
        conn.execute(
            """
            INSERT INTO triage (link_id, model, topic, vertical, kind, still_relevant, reason,
                                buildable, one_line_idea, decided_by)
            VALUES (%s, 'fixture', %s, %s, %s, %s, %s, %s, %s, 'model')
            """,
            (link_id, t["topic"], t["vertical"], t["kind"], t["still_relevant"], t["reason"],
             t["buildable"], t["one_line_idea"]))
        status = "kept" if t["still_relevant"] else "valhalla"
        conn.execute("UPDATE links SET status = %s WHERE id = %s", (status, link_id))
        if not t["still_relevant"]:
            conn.execute(
                "INSERT INTO valhalla (link_id, reason, decided_by, batch_id) VALUES (%s, %s, 'model', 'fixture')",
                (link_id, t["reason"]))
    return {"links": len(ids), "triage": len(triage), "schema": schema}
