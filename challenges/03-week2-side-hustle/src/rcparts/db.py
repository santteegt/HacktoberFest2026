"""Postgres access (Tiger Cloud). Plain SQL, one short transaction per command."""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
from psycopg import sql
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


def schema_tables() -> list[str]:
    """Tables created by sql/schema.sql, in creation order (the only tables `db reset` may drop)."""
    return re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", SCHEMA_FILE.read_text(encoding="utf-8"))


def reset_schema(conn: psycopg.Connection) -> dict:
    """Drop exactly the rcparts tables (reverse creation order, so foreign keys go first), then recreate.
    No CASCADE: if anything outside rcparts depends on these tables the drop fails loudly instead."""
    tables = schema_tables()
    schema = conn.execute("SELECT current_schema() AS s").fetchone()["s"]
    existing = {r["tablename"] for r in conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = %s", (schema,)).fetchall()}
    dropped = []
    for name in reversed(tables):
        if name in existing:  # schema-qualified: never resolves to a same-named table elsewhere
            conn.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(schema, name)))
            dropped.append(f"{schema}.{name}")
    conn.commit()
    return {"dropped": dropped, **init_schema(conn)}


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
                  l.condition, l.price_usd, l.qty, l.status, l.closed_reason, l.created_at,
                  m.display_name AS member_name, m.phone AS member_phone,
                  (SELECT c.name FROM clubs c WHERE c.id = l.club_id) AS club_name"""


def scope_club_ids(conn, club_id: int, scope: str) -> list[int]:
    """Clubs whose listings a member of `club_id` can match: own club, same city or same country."""
    if scope == "club":
        return [club_id]
    same_city = "AND lower(trim(o.city)) = lower(trim(c.city))" if scope == "city" else ""
    rows = conn.execute(
        f"""SELECT o.id FROM clubs c JOIN clubs o ON lower(trim(o.country)) = lower(trim(c.country)) {same_city}
            WHERE c.id = %s ORDER BY o.id""",
        (club_id,),
    ).fetchall()
    return [r["id"] for r in rows] or [club_id]


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


def close_listing(conn, listing_id: int, member_id: int | None, reason: str | None = None) -> dict | None:
    """Closes an open or matched listing (owner only when member_id is given); returns it, or None."""
    sql_ = """UPDATE listings SET status = 'closed', closed_reason = %s, closed_at = now()
              WHERE id = %s AND status <> 'closed'"""
    params: list = [reason, listing_id]
    if member_id is not None:
        sql_ += " AND member_id = %s"
        params.append(member_id)
    row = conn.execute(sql_ + " RETURNING id", params).fetchone()
    conn.commit()
    return get_listing(conn, listing_id) if row else None


def active_listings_for_member(conn, member_id: int) -> list[dict]:
    return conn.execute(
        f"""SELECT {LISTING_COLS} FROM listings l JOIN members m ON m.id = l.member_id
            WHERE l.member_id = %s AND l.status IN ('open', 'matched') ORDER BY l.id""",
        (member_id,),
    ).fetchall()


def match_counterparts(conn, listing_id: int) -> list[dict]:
    """The other side of every match this listing is in, while that other listing is still active."""
    return conn.execute(
        f"""SELECT {LISTING_COLS}, x.id AS match_id FROM matches x
            JOIN listings l ON l.id = CASE WHEN x.need_id = %(id)s THEN x.have_id ELSE x.need_id END
            JOIN members m ON m.id = l.member_id
            WHERE (x.need_id = %(id)s OR x.have_id = %(id)s) AND l.status IN ('open', 'matched')
            ORDER BY x.id""",
        {"id": listing_id},
    ).fetchall()


def reopen_unmatched(conn, listing_ids: list[int]) -> None:
    """A 'matched' listing whose every counterpart is now closed goes back to 'open'."""
    conn.execute(
        """UPDATE listings l SET status = 'open' WHERE l.id = ANY(%s) AND l.status = 'matched'
           AND NOT EXISTS (SELECT 1 FROM matches x JOIN listings o
                             ON o.id = CASE WHEN x.need_id = l.id THEN x.have_id ELSE x.need_id END
                           WHERE (x.need_id = l.id OR x.have_id = l.id) AND o.status <> 'closed')""",
        (listing_ids,),
    )
    conn.commit()


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
    """We order it -> awaiting_deposit (the member pays first); self-order -> accepted (fee only)."""
    row = conn.execute(
        """UPDATE quotes SET status = %s, with_processing = %s, accepted_at = now()
           WHERE id = %s AND member_id = %s AND status = 'quoted' RETURNING *""",
        ("awaiting_deposit" if with_processing else "accepted", with_processing, quote_id, member_id),
    ).fetchone()
    conn.commit()
    return row


QUOTE_COLS = "q.*, m.phone AS member_phone, m.display_name AS member_name, m.club_id AS member_club_id"


def get_quote(conn, quote_id: int) -> dict | None:
    return conn.execute(
        f"SELECT {QUOTE_COLS} FROM quotes q JOIN members m ON m.id = q.member_id WHERE q.id = %s", (quote_id,)
    ).fetchone()


def member_quotes_with_status(conn, member_id: int, statuses: list[str]) -> list[dict]:
    return conn.execute(
        f"""SELECT {QUOTE_COLS} FROM quotes q JOIN members m ON m.id = q.member_id
            WHERE q.member_id = %s AND q.status = ANY(%s) ORDER BY q.id""",
        (member_id, statuses),
    ).fetchall()


def set_quote_status(conn, quote_id: int, from_statuses: list[str], to: str) -> dict | None:
    row = conn.execute(
        "UPDATE quotes SET status = %s WHERE id = %s AND status = ANY(%s) RETURNING *",
        (to, quote_id, from_statuses),
    ).fetchone()
    return row


# --- deposits ---------------------------------------------------------------------

def insert_deposit(conn, d: dict) -> dict:
    d = {**d, "checks": Jsonb(d["checks"])}
    cols = list(d)
    return conn.execute(
        f"INSERT INTO deposits ({', '.join(cols)}) VALUES ({', '.join('%(' + c + ')s' for c in cols)}) RETURNING *",
        d,
    ).fetchone()


def latest_deposit(conn, quote_id: int, status: str | None = "submitted") -> dict | None:
    return conn.execute(
        """SELECT * FROM deposits WHERE quote_id = %s AND (%s::text IS NULL OR status = %s)
           ORDER BY id DESC LIMIT 1""",
        (quote_id, status, status),
    ).fetchone()


def review_deposit(conn, deposit_id: int, status: str, reason: str | None) -> dict:
    return conn.execute(
        "UPDATE deposits SET status = %s, reject_reason = %s, reviewed_at = now() WHERE id = %s RETURNING *",
        (status, reason, deposit_id),
    ).fetchone()


def list_deposits(conn, status: str | None) -> list[dict]:
    return conn.execute(
        """SELECT d.*, q.status AS quote_status, q.store_title, m.display_name AS member_name
           FROM deposits d JOIN quotes q ON q.id = d.quote_id JOIN members m ON m.id = d.member_id
           WHERE (%s::text IS NULL OR d.status = %s) ORDER BY d.id DESC LIMIT 50""",
        (status, status),
    ).fetchall()


def list_quotes(conn, member_id: int) -> list[dict]:
    return conn.execute(
        "SELECT * FROM quotes WHERE member_id = %s ORDER BY id DESC LIMIT 50", (member_id,)
    ).fetchall()


def pending_order_quotes(conn) -> list[dict]:
    return conn.execute(
        """SELECT q.*, m.phone AS member_phone, m.display_name AS member_name
           FROM quotes q JOIN members m ON m.id = q.member_id
           WHERE q.order_id IS NULL
             AND (q.status = 'paid' OR (q.status = 'accepted' AND q.with_processing IS FALSE))
           ORDER BY q.store, q.id"""
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
