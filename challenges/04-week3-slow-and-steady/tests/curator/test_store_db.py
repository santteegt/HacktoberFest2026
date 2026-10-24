"""Store + Valhalla flow against real Postgres, in a throwaway schema (never `public`).

Runs only with SLOTH_DB_TESTS=1 (needs the Tiger service from .sloth/config.toml).
"""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sloth.core.models import Enrichment, FetchedWith, Kind, Link, Triage, Vertical

pytestmark = pytest.mark.skipif(os.environ.get("SLOTH_DB_TESTS") != "1", reason="set SLOTH_DB_TESTS=1")

SCHEMA = "curator_test"


@pytest.fixture
def conn():
    from sloth.core.db import SCHEMA as DDL
    from sloth.core.db import connect
    with connect() as c:
        c.autocommit = True
        c.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        c.execute(f"CREATE SCHEMA {SCHEMA}")
        c.execute(f"SET search_path TO {SCHEMA}")
        c.execute(DDL.read_text())
        yield c
        c.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")


def _t(buildable):
    return Triage(topic="t", vertical=Vertical.llms, kind=Kind.library, still_relevant=True,
                  reason="r", buildable=buildable)


def test_valhalla_flow(conn, tmp_path: Path):
    from sloth.curator import report, store
    links = [Link(url=f"https://e.com/{i}", canonical_url=f"https://e.com/{i}", title=f"T{i}",
                  saved_at=datetime(2026, 1, i + 1, tzinfo=UTC)) for i in range(4)]
    assert store.upsert_links(conn, links) == 4
    assert store.upsert_links(conn, links) == 0
    ids = [r["id"] for r in store.next_batch(conn, 10)]
    assert len(ids) == 4
    store.save_enrichment(conn, Enrichment(link_id=ids[0], http_status=404, fetched_with=FetchedWith.failed))
    assert store.status_counts(conn)["enriched"] == 1
    store.save_triage(conn, ids[0], _t(3), decided_by="model")
    store.save_triage(conn, ids[1], _t(0), decided_by="model")
    for i in ids[:3]:
        store.propose_valhalla(conn, i, "dead", decided_by="code", batch_id="b1")
    assert [r["link_id"] for r in store.valhalla_rows(conn)] == ids[:3]  # in proposal order
    assert sorted(store.restore(conn, [ids[0], ids[1], 9999])) == sorted(ids[:2])
    st = {r["id"]: r["status"] for r in conn.execute("SELECT id, status FROM links").fetchall()}
    assert st[ids[0]] == "kept" and st[ids[1]] == "reading"  # rescued by their latest label
    rows = store.confirm_all(conn)
    assert [r["link_id"] for r in rows] == [ids[2]]
    path = report.write_export(rows, out_dir=tmp_path)
    assert rows[0]["url"] in path.read_text()
    assert store.valhalla_rows(conn) == []
    store.set_status(conn, ids[3], "unsure")
    assert store.resolve_unsure(conn, [ids[3]], keep=False) == [ids[3]]
    assert store.valhalla_rows(conn)[0]["decided_by"] == "author"
