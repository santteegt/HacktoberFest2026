"""Integration tests against a real Postgres. Skipped unless DATABASE_URL is set.

They run inside a throwaway schema (`rcparts_test`, via PGOPTIONS) that is dropped afterwards.
"""

import json
import os

import pytest

from rcparts import cli, db
from rcparts.store import parse_product, parse_search

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
SCHEMA = "rcparts_test"


@pytest.fixture(scope="module", autouse=True)
def test_schema():
    url = os.environ["DATABASE_URL"]
    with db.connect(url) as conn:
        conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        conn.execute(f"CREATE SCHEMA {SCHEMA}")
        conn.commit()
    old = os.environ.get("PGOPTIONS")
    os.environ["PGOPTIONS"] = f"-c search_path={SCHEMA},public"
    yield
    if old is None:
        os.environ.pop("PGOPTIONS", None)
    else:
        os.environ["PGOPTIONS"] = old
    with db.connect(url) as conn:
        conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        conn.commit()


def run(capsys, *argv):
    code = cli.main([str(a) for a in argv])
    out = json.loads(capsys.readouterr().out)
    assert code == 0, out
    return out


def test_end_to_end(capsys, monkeypatch, load_fixture):
    monkeypatch.setenv("REPLY_LANG", "en")
    monkeypatch.setenv("US_ADDRESS", "Test address, Miami FL")
    assert run(capsys, "db", "init")["ok"]
    assert run(capsys, "db", "init")["ok"]  # idempotent
    check = run(capsys, "db", "check")
    assert set(check["extensions"]) == {"vector", "pg_trgm", "pg_textsearch", "timescaledb"}

    club = run(capsys, "club", "add", "--name", "Test RC", "--country", "EC", "--city", "Quito")["club"]
    a, b = "593990000001", "593990000002"
    run(capsys, "member", "add", "--club", club["id"], "--phone", a, "--name", "Ana")
    run(capsys, "member", "add", "--club", club["id"], "--phone", b, "--name", "Beto", "--brands", "tamiya,xray")
    assert run(capsys, "member", "add", "--club", club["id"], "--phone", b, "--name", "B")["created"] is False

    stranger = run(capsys, "listing", "add", "--phone", "1999", "--json", '{"kind":"NEED","part_number":"x1"}')
    assert stranger["ok"] is False and stranger["error"] == "not_member"

    ask = run(capsys, "listing", "add", "--phone", a, "--json", '{"kind":"NEED","chassis":"tt02"}')
    assert ask["ok"] is False and ask["missing"] == ["description"]

    have = run(capsys, "listing", "add", "--phone", a, "--no-notify", "--json",
               '{"kind":"HAVE","part_number":"TAM 54500","brand":"Tamiya","chassis":"TT-02",'
               '"description":"68T high speed gear set","condition":"new","price_usd":12}')
    assert have["ok"] and have["matches"] == []
    need = run(capsys, "listing", "add", "--phone", b, "--no-notify", "--json",
               '{"kind":"NEED","part_number":"tam-54500"}')
    assert [m["method"] for m in need["matches"]] == ["part_number"]
    assert need["matches"][0]["listing"]["id"] == have["listing"]["id"]

    # Text path: no part number, same chassis and words.
    have2 = run(capsys, "listing", "add", "--phone", a, "--no-notify", "--json",
                '{"kind":"HAVE","brand":"tamiya","chassis":"tt-02","description":"front shock set CVA"}')
    need2 = run(capsys, "listing", "add", "--phone", b, "--no-notify", "--json",
                '{"kind":"NEED","brand":"tamiya","chassis":"TT02","description":"CVA shocks front"}')
    assert need2["matches"] and need2["matches"][0]["listing"]["id"] == have2["listing"]["id"]
    # Different chassis must not match even with the same words.
    need3 = run(capsys, "listing", "add", "--phone", b, "--no-notify", "--json",
                '{"kind":"NEED","brand":"tamiya","chassis":"ta08","description":"front shock set CVA"}')
    assert need3["matches"] == []

    found = run(capsys, "search", "--club", club["id"], "--text", "who has TAM54500?")
    assert found["results"][0]["part_number"] == "TAM54500"

    class FakeStore:
        def __init__(self, *_a, **_k):
            pass

        def search(self, q):
            return parse_search(load_fixture("search_tam54500.json"))

        def product(self, url):
            return parse_product(load_fixture("product_tam54500.json"))

    monkeypatch.setattr(cli, "StoreClient", FakeStore)
    q = run(capsys, "quote", "--phone", b, "--query", "TAM54500")
    assert q["ok"] and q["exact_match"]
    assert "$17.39" in q["reply"] and "$15.83" in q["reply"]
    acc = run(capsys, "quote", "accept", "--phone", b, "--quote", q["quote"]["id"])
    assert acc["ok"] and "$17.39" in acc["reply"]
    again = run(capsys, "quote", "accept", "--phone", b, "--quote", q["quote"]["id"])
    assert again["ok"] is False

    preview = run(capsys, "orders", "daily", "--dry-run")
    assert preview["orders"][0]["grand_total_usd"] == "17.39"
    order = run(capsys, "orders", "daily")
    assert order["orders"][0]["order_id"] and not order["sent"]
    assert run(capsys, "orders", "daily")["orders"] == []
    assert "in an order" in run(capsys, "quote", "list", "--phone", b)["reply"]

    closed = run(capsys, "listing", "close", "--id", have["listing"]["id"], "--phone", b)
    assert closed["ok"] is False  # not the owner
    assert run(capsys, "listing", "close", "--id", have["listing"]["id"], "--phone", a)["ok"]
