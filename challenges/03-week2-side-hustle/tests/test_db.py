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
    assert set(check["extensions"]) == {"vector", "pg_trgm", "pg_textsearch", "timescaledb", "unaccent"}

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
    qid = q["quote"]["id"]
    acc = run(capsys, "quote", "accept", "--phone", b, "--quote", qid)
    assert acc["ok"] and "$17.39" in acc["reply"] and f"RC-Q{qid}" in acc["reply"]
    assert acc["quote"]["status"] == "awaiting_deposit"
    again = run(capsys, "quote", "accept", "--phone", b, "--quote", qid)
    assert again["ok"] is False
    assert run(capsys, "orders", "daily", "--dry-run")["orders"] == []  # not paid yet

    # Deposit: a mismatching receipt is accepted but flagged; the maintainer rejects, then a good one is confirmed.
    bad_pdf = run(capsys, "demo", "receipt", "--quote", qid, "--amount", "15")["file"]
    stranger_submit = run(capsys, "deposit", "submit", "--phone", a, "--quote", qid, "--file", bad_pdf)
    assert stranger_submit["error"] == "quote_not_awaiting_deposit"
    sub = run(capsys, "deposit", "submit", "--phone", b, "--file", bad_pdf)  # --quote inferred
    assert sub["ok"] and sub["quote_id"] == qid and sub["maintainer_notified"]
    assert sub["deposit"]["checks"]["amount_ok"] is False and sub["deposit"]["checks"]["reference_ok"] is True
    assert "MEDIA:/" in sub["maintainer_message"] and "NO coincide" not in sub["maintainer_message"]  # en
    assert "DOES NOT match" in sub["maintainer_message"]
    assert run(capsys, "deposit", "confirm", "--phone", b, "--quote", qid)["error"] == "not_maintainer"
    rej = run(capsys, "deposit", "reject", "--phone", a, "--quote", qid, "--reason", "amount differs")
    assert rej["ok"] and rej["status"] == "awaiting_deposit" and rej["member_notified"]
    good_pdf = run(capsys, "demo", "receipt", "--quote", qid)["file"]
    sub2 = run(capsys, "deposit", "submit", "--phone", b, "--quote", qid, "--file", good_pdf)
    assert sub2["deposit"]["checks"]["amount_ok"] and sub2["deposit"]["amount_usd"] == "17.39"
    conf = run(capsys, "deposit", "confirm", "--phone", a, "--quote", qid)
    assert conf["ok"] and conf["status"] == "paid"
    listed = run(capsys, "deposit", "list", "--phone", a)
    assert [d["status"] for d in listed["deposits"]] == ["confirmed", "rejected"]

    preview = run(capsys, "orders", "daily", "--dry-run")
    assert preview["orders"][0]["grand_total_usd"] == "17.39"
    order = run(capsys, "orders", "daily")
    assert order["orders"][0]["order_id"] and not order["sent"]
    assert run(capsys, "orders", "daily")["orders"] == []
    assert "in an order" in run(capsys, "quote", "list", "--phone", b)["reply"]

    closed = run(capsys, "listing", "close", "--id", have["listing"]["id"], "--phone", b)
    assert closed["ok"] is False  # not the owner
    by_id = run(capsys, "listing", "close", "--id", have["listing"]["id"], "--phone", a, "--no-notify")
    assert by_id["ok"] and by_id["reason"] == "sold"
    assert [n["listing_id"] for n in by_id["notified"]] == [need["listing"]["id"]]

    # Close by text: one hit (and the matched NEED's owner is told), ambiguous, none.
    ok = run(capsys, "listing", "close", "--phone", a, "--text", "ya vendí los amortiguadores CVA")
    assert ok["ok"] and ok["listing_id"] == have2["listing"]["id"] and ok["notified"][0]["sent"]
    run(capsys, "listing", "add", "--phone", a, "--no-notify", "--json",
        '{"kind":"HAVE","brand":"tamiya","chassis":"tt02","description":"rear upright"}')
    run(capsys, "listing", "add", "--phone", a, "--no-notify", "--json",
        '{"kind":"HAVE","brand":"tamiya","chassis":"tt02","description":"front upright"}')
    amb = run(capsys, "listing", "close", "--phone", a, "--text", "sold the upright")
    assert amb["ok"] is False and amb["error"] == "ambiguous" and len(amb["candidates"]) == 2
    none = run(capsys, "listing", "close", "--phone", a, "--text", "sold the motor")
    assert none["ok"] is False and none["error"] == "not_found" and len(none["open_listings"]) == 2


def test_cross_club_scope(capsys, monkeypatch):
    monkeypatch.setenv("REPLY_LANG", "es")
    run(capsys, "db", "init")
    c1 = run(capsys, "club", "add", "--name", "Club Uno", "--country", "EC", "--city", "Loja")["club"]
    c2 = run(capsys, "club", "add", "--name", "Club Dos", "--country", "EC", "--city", "loja ")["club"]
    c3 = run(capsys, "club", "add", "--name", "Club Tres", "--country", "EC", "--city", "Ambato")["club"]
    x, y, z = "593990000011", "593990000012", "593990000013"
    run(capsys, "member", "add", "--club", c1["id"], "--phone", x, "--name", "Xavi")
    run(capsys, "member", "add", "--club", c2["id"], "--phone", y, "--name", "Yola")
    run(capsys, "member", "add", "--club", c3["id"], "--phone", z, "--name", "Zoe")
    run(capsys, "listing", "add", "--phone", y, "--no-notify", "--json",
        '{"kind":"HAVE","part_number":"XRA303187-H","brand":"xray","chassis":"x4","description":"brazo"}')
    run(capsys, "listing", "add", "--phone", z, "--no-notify", "--json",
        '{"kind":"HAVE","part_number":"XRA303187-H","brand":"xray","chassis":"x4","description":"brazo"}')
    need = run(capsys, "listing", "add", "--phone", x, "--json", '{"kind":"NEED","part_number":"XRA303187H"}')
    assert [m["listing"]["member_name"] for m in need["matches"]] == ["Yola"]  # same city only
    assert "Yola (de Club Dos)" in need["reply"] and need["matches"][0]["notified"]
    monkeypatch.setenv("MATCH_SCOPE", "club")
    assert run(capsys, "search", "--phone", x, "--text", "XRA303187H", "--kind", "HAVE")["results"] == []
    found = run(capsys, "search", "--phone", x, "--text", "XRA303187H", "--kind", "HAVE", "--scope", "country")
    assert {r["member_name"] for r in found["results"]} == {"Yola", "Zoe"}
    assert "(de Club Tres)" in found["reply"]
    by_club = run(capsys, "search", "--club", c2["id"], "--text", "XRA303187H", "--kind", "HAVE")
    assert [r["member_name"] for r in by_club["results"]] == ["Yola"]


def test_reset_drops_only_rcparts_tables(capsys):
    url = os.environ["DATABASE_URL"]
    with db.connect(url) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS sensors (id int)")
        conn.commit()
    out = run(capsys, "db", "reset", "--yes")
    assert out["ok"] and all(t.split(".")[1] in db.schema_tables() for t in out["dropped"])
    with db.connect(url) as conn:
        assert conn.execute("SELECT to_regclass('sensors') AS r").fetchone()["r"] is not None
        assert conn.execute("SELECT count(*) AS n FROM clubs").fetchone()["n"] == 0


def test_bilingual_match_group_quote_and_orders(capsys, monkeypatch, load_fixture):
    monkeypatch.setenv("REPLY_LANG", "es")
    run(capsys, "db", "init")
    club = run(capsys, "club", "add", "--name", "Club Bi", "--country", "EC", "--city", "Riobamba")["club"]
    socio, ana = "593990000021", "593990000022"
    run(capsys, "member", "add", "--club", club["id"], "--phone", socio, "--name", "Socio")
    run(capsys, "member", "add", "--club", club["id"], "--phone", ana, "--name", "Ana")
    add = lambda phone, js: run(capsys, "listing", "add", "--phone", phone, "--no-notify", "--json", js)  # noqa: E731
    arm = add(socio, '{"kind":"HAVE","brand":"xray","chassis":"x4","part_number":"XRA303187-H",'
                     '"description":"brazo inferior trasero duro izquierdo"}')["listing"]
    shocks = add(socio, '{"kind":"HAVE","brand":"xray","chassis":"x4","part_number":"XRA308329",'
                        '"description":"cuerpos de amortiguador XLP2 de aluminio (2)"}')["listing"]
    wing = add(socio, '{"kind":"HAVE","brand":"xray","chassis":"x1","part_number":"XRA371203-K",'
                      '"description":"alerón delantero negro"}')["listing"]
    add(socio, '{"kind":"HAVE","brand":"xray","chassis":"x4","part_number":"XRA302842",'
               '"description":"barra estabilizadora delantera 1.2 mm"}')

    # The live failure: English NEED, Spanish HAVE.
    need = add(ana, '{"kind":"NEED","brand":"xray","chassis":"x4","description":"rear lower arm"}')
    assert [m["listing"]["id"] for m in need["matches"]] == [arm["id"]]
    front = add(ana, '{"kind":"NEED","brand":"xray","chassis":"x4","description":"front lower arm"}')
    assert front["matches"] == []
    bar = add(ana, '{"kind":"NEED","brand":"xray","chassis":"x4","part_number":"XRA303843",'
                   '"description":"barra estabilizadora trasera"}')
    assert bar["matches"] == []

    search = lambda text: [r["id"] for r in run(capsys, "search", "--club", club["id"], "--kind", "HAVE",  # noqa: E731
                                                "--text", text)["results"]]
    assert search("amortiguadores del X4") == [shocks["id"]]
    assert search("shocks x4") == [shocks["id"]]
    assert search("alerones x1") == [wing["id"]]
    assert search("aleron x1") == [wing["id"]]
    assert search("I'm looking for a rear lower arm for the Xray X4")[0] == arm["id"]

    class FakeStore:
        def __init__(self, *_a, **_k):
            pass

        def search(self, q):
            return parse_search(load_fixture("search_tam54500.json"))

        def product(self, url):
            return parse_product(load_fixture("product_tam54500.json"))

    monkeypatch.setattr(cli, "StoreClient", FakeStore)
    # In a group the full quote goes by DM and the group gets one line.
    monkeypatch.setenv("HERMES_SESSION_CHAT_TYPE", "group")
    q1 = run(capsys, "quote", "--phone", ana, "--query", "TAM54500")
    assert q1["sent_by_dm"] and q1["reply"] == "Te envié la cotización por privado, Ana."
    assert f"«sí {q1['quote']['id']}»" in q1["quote_text"] and q1["queries_tried"] == ["TAM54500"]
    monkeypatch.setenv("HERMES_SEND_CMD", "false")  # DM fails -> the full quote comes back
    q2 = run(capsys, "quote", "--phone", ana, "--query", "TAM54500")
    assert not q2["sent_by_dm"] and q2["dm_error"] and q2["reply"] == q2["quote_text"]
    monkeypatch.delenv("HERMES_SESSION_CHAT_TYPE")
    monkeypatch.setenv("HERMES_SEND_CMD", "sh -c 'cat >/dev/null'")
    q3 = run(capsys, "quote", "--phone", ana, "--query", "TAM54500", "--deliver", "dm")
    assert q3["sent_by_dm"]

    # A bare "sí" with three fresh quotes is ambiguous; "sí <id>" and "lo compro yo <id>" work.
    amb = run(capsys, "quote", "accept", "--phone", ana, "--text", "sí")
    assert amb["error"] == "ambiguous" and amb["candidates"] == [q3["quote"]["id"], q2["quote"]["id"], q1["quote"]["id"]]
    ok1 = run(capsys, "quote", "accept", "--phone", ana, "--text", f"sí {q1['quote']['id']}")
    assert ok1["ok"] and ok1["quote"]["status"] == "awaiting_deposit"
    ok2 = run(capsys, "quote", "accept", "--phone", ana, "--text", f"lo compro yo #{q2['quote']['id']}")
    assert ok2["ok"] and ok2["quote"]["status"] == "awaiting_tracking"
    ok3 = run(capsys, "quote", "accept", "--phone", ana, "--text", "dale")  # one pending left
    assert ok3["ok"] and ok3["quote"]["id"] == q3["quote"]["id"]
    assert run(capsys, "quote", "accept", "--phone", ana)["error"] == "no_pending_quote"
    assert run(capsys, "quote", "accept", "--phone", socio, "--text", f"sí {q1['quote']['id']}")["ok"] is False

    run(capsys, "tracking", "submit", "--phone", ana, "--no-notify", "--text", "tracking 1Z999AA10123456784")
    mine = run(capsys, "orders", "mine", "--phone", ana)
    assert [o["id"] for o in mine["orders"]] == [q3["quote"]["id"], q2["quote"]["id"], q1["quote"]["id"]]
    assert "en camino" in mine["reply"] and "1Z999AA10123456784" in mine["reply"] and "solo tarifa" in mine["reply"]
    assert run(capsys, "quote", "list", "--active", "--phone", ana)["reply"] == mine["reply"]
    monkeypatch.setenv("HERMES_SESSION_CHAT_TYPE", "group")
    grp = run(capsys, "orders", "mine", "--phone", ana)
    assert grp["sent_by_dm"] and grp["reply"] == "Te envié tus pedidos por privado, Ana."
    monkeypatch.delenv("HERMES_SESSION_CHAT_TYPE")
    assert "No tienes pedidos activos" in run(capsys, "orders", "mine", "--phone", socio)["reply"]
