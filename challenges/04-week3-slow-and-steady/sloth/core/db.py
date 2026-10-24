"""Postgres on Tiger Data (the skunkworks-sloth service). Schema lives in schema.sql."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from .secrets import database_url

SCHEMA = Path(__file__).with_name("schema.sql")


@contextmanager
def connect():
    with psycopg.connect(database_url(), row_factory=dict_row, connect_timeout=15) as conn:
        yield conn


def apply_schema() -> None:
    with connect() as conn:
        conn.execute(SCHEMA.read_text())
