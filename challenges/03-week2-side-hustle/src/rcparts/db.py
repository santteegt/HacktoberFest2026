"""Postgres access (Tiger Cloud). Plain SQL, one short transaction per command."""

from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"
EXTENSIONS = ("vector", "pg_trgm", "pg_textsearch", "timescaledb")


class ConfigError(RuntimeError):
    pass


def connect(database_url: str | None) -> psycopg.Connection:
    if not database_url:
        raise ConfigError("DATABASE_URL is not set")
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=15)


def init_schema(conn: psycopg.Connection) -> dict:
    conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.commit()
    # pg_trgm only sharpens the ranking, so a role that can't create extensions still works.
    trgm = {"pg_trgm": False, "pg_trgm_error": None}
    try:
        conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS listings_desc_trgm_idx ON listings USING gin (description gin_trgm_ops)"
        )
        conn.commit()
        trgm["pg_trgm"] = True
    except psycopg.Error as exc:
        conn.rollback()
        trgm["pg_trgm_error"] = str(exc).strip().splitlines()[0]
    return trgm


def check(conn: psycopg.Connection) -> dict:
    version = conn.execute("SHOW server_version").fetchone()["server_version"]
    rows = conn.execute(
        "SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = ANY(%s)",
        (list(EXTENSIONS),),
    ).fetchall()
    found = {r["name"]: r for r in rows}
    exts = {
        name: {
            "available": name in found,
            "installed": bool(found.get(name, {}).get("installed_version")),
            "default_version": found.get(name, {}).get("default_version"),
            "installed_version": found.get(name, {}).get("installed_version"),
        }
        for name in EXTENSIONS
    }
    return {"server_version": version, "extensions": exts}


def has_extension(conn: psycopg.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM pg_extension WHERE extname = %s", (name,)).fetchone() is not None


# --- clubs and members -------------------------------------------------------

def add_club(conn, name: str, country: str, city: str, jid: str | None) -> dict:
    row = conn.execute(
        "INSERT INTO clubs (name, country, city, whatsapp_group_jid) VALUES (%s, %s, %s, %s) RETURNING *",
        (name, country, city, jid),
    ).fetchone()
    conn.commit()
    return row


def list_clubs(conn) -> list[dict]:
    return conn.execute("SELECT * FROM clubs ORDER BY id").fetchall()


def get_club(conn, club_id: int) -> dict | None:
    return conn.execute("SELECT * FROM clubs WHERE id = %s", (club_id,)).fetchone()


def get_member(conn, phone: str) -> dict | None:
    return conn.execute(
        "SELECT m.*, c.name AS club_name FROM members m JOIN clubs c ON c.id = m.club_id WHERE m.phone = %s",
        (phone,),
    ).fetchone()


def add_member(conn, club_id: int, phone: str, name: str, rc_class: str | None, brands: list[str]) -> tuple[dict, bool]:
    """Returns (member, created). An existing phone is left untouched."""
    row = conn.execute(
        """INSERT INTO members (club_id, phone, display_name, rc_class, brands)
           VALUES (%s, %s, %s, %s, %s) ON CONFLICT (phone) DO NOTHING RETURNING id""",
        (club_id, phone, name, rc_class, brands),
    ).fetchone()
    conn.commit()
    return get_member(conn, phone), row is not None


def list_members(conn, club_id: int) -> list[dict]:
    return conn.execute("SELECT * FROM members WHERE club_id = %s ORDER BY id", (club_id,)).fetchall()


# --- listings ------------------------------------------------------------------

def insert_listing(conn, member: dict, listing: dict) -> dict:
    row = conn.execute(
        """INSERT INTO listings (club_id, member_id, kind, brand, chassis, part_number, description,
                                 condition, price_usd, qty)
           VALUES (%(club_id)s, %(member_id)s, %(kind)s, %(brand)s, %(chassis)s, %(part_number)s,
                   %(description)s, %(condition)s, %(price_usd)s, %(qty)s)
           RETURNING id, club_id, member_id, kind, brand, chassis, part_number, description,
                     condition, price_usd, qty, status, created_at""",
        {**listing, "club_id": member["club_id"], "member_id": member["id"]},
    ).fetchone()
    return row


LISTING_COLS = """l.id, l.club_id, l.member_id, l.kind, l.brand, l.chassis, l.part_number, l.description,
                  l.condition, l.price_usd, l.qty, l.status, l.created_at,
                  m.display_name AS member_name, m.phone AS member_phone"""


def get_listing(conn, listing_id: int) -> dict | None:
    return conn.execute(
        f"SELECT {LISTING_COLS} FROM listings l JOIN members m ON m.id = l.member_id WHERE l.id = %s",
        (listing_id,),
    ).fetchone()


def list_listings(conn, phone: str | None, club_id: int | None, kind: str | None, status: str | None) -> list[dict]:
    where, params = [], []
    if phone:
        where.append("m.phone = %s")
        params.append(phone)
    if club_id is not None:
        where.append("l.club_id = %s")
        params.append(club_id)
    if kind:
        where.append("l.kind = %s")
        params.append(kind)
    if status:
        where.append("l.status = %s")
        params.append(status)
    sql = f"SELECT {LISTING_COLS} FROM listings l JOIN members m ON m.id = l.member_id"
    if where:
        sql += " WHERE " + " AND ".join(where)
    return conn.execute(sql + " ORDER BY l.id DESC LIMIT 200", params).fetchall()


def close_listing(conn, listing_id: int, member_id: int | None) -> bool:
    sql = "UPDATE listings SET status = 'closed' WHERE id = %s"
    params: list = [listing_id]
    if member_id is not None:
        sql += " AND member_id = %s"
        params.append(member_id)
    cur = conn.execute(sql, params)
    conn.commit()
    return cur.rowcount > 0


def record_match(conn, need_id: int, have_id: int, method: str, score: float) -> int | None:
    """Returns the new match id, or None when this pair was already matched (no second DM)."""
    row = conn.execute(
        """INSERT INTO matches (need_id, have_id, method, score) VALUES (%s, %s, %s, %s)
           ON CONFLICT (need_id, have_id) DO NOTHING RETURNING id""",
        (need_id, have_id, method, score),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE listings SET status = 'matched' WHERE id IN (%s, %s) AND status = 'open'", (need_id, have_id)
        )
    return row["id"] if row else None


def mark_notified(conn, match_id: int, error: str | None) -> None:
    conn.execute(
        "UPDATE matches SET notified_at = CASE WHEN %s::text IS NULL THEN now() END, notify_error = %s WHERE id = %s",
        (error, error, match_id),
    )
    conn.commit()


# --- quotes and orders -----------------------------------------------------------

def insert_quote(conn, q: dict) -> dict:
    cols = list(q)
    row = conn.execute(
        f"INSERT INTO quotes ({', '.join(cols)}) VALUES ({', '.join('%(' + c + ')s' for c in cols)}) RETURNING *",
        q,
    ).fetchone()
    conn.commit()
    return row


def accept_quote(conn, quote_id: int, member_id: int, with_processing: bool) -> dict | None:
    row = conn.execute(
        """UPDATE quotes SET status = 'accepted', with_processing = %s, accepted_at = now()
           WHERE id = %s AND member_id = %s AND status = 'quoted' RETURNING *""",
        (with_processing, quote_id, member_id),
    ).fetchone()
    conn.commit()
    return row


def list_quotes(conn, member_id: int) -> list[dict]:
    return conn.execute(
        "SELECT * FROM quotes WHERE member_id = %s ORDER BY id DESC LIMIT 50", (member_id,)
    ).fetchall()


def pending_order_quotes(conn) -> list[dict]:
    return conn.execute(
        """SELECT q.*, m.phone AS member_phone, m.display_name AS member_name
           FROM quotes q JOIN members m ON m.id = q.member_id
           WHERE q.status = 'accepted' AND q.order_id IS NULL ORDER BY q.store, q.id"""
    ).fetchall()


def create_order(conn, store: str, quote_ids: list[int], summary: dict) -> dict:
    row = conn.execute(
        "INSERT INTO orders (store, quote_ids, summary) VALUES (%s, %s, %s) RETURNING *",
        (store, quote_ids, Jsonb(summary)),
    ).fetchone()
    conn.execute(
        "UPDATE quotes SET order_id = %s, status = 'ordered' WHERE id = ANY(%s)", (row["id"], quote_ids)
    )
    return row


def mark_order_sent(conn, order_ids: list[int]) -> None:
    conn.execute("UPDATE orders SET summary_sent_at = now() WHERE id = ANY(%s)", (order_ids,))
    conn.commit()
