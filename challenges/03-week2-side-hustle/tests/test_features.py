"""Offline tests for match scope, close-by-text, deposits, maintainer-only commands and the order batch."""

import json
import os
import time
from decimal import Decimal

import pytest

from rcparts import cli, db
from rcparts.config import Settings
from rcparts.deposit import (amount_candidates, check_receipt_text, make_test_receipt, newest_cached_pdf,
                             parse_amount, parse_date, parse_reference, pdf_text)
from rcparts.matcher import infer_close_kind, pick_listings_to_close, text_match_ok
from rcparts.replies import eligible_for_order

D = Decimal


def run(capsys, *argv):
    code = cli.main([str(a) for a in argv])
    return code, json.loads(capsys.readouterr().out)


# --- scope -----------------------------------------------------------------------------

def test_match_scope_setting():
    assert Settings.from_env({}).match_scope == "city"
    assert Settings.from_env({"MATCH_SCOPE": "Country"}).match_scope == "country"
    assert Settings.from_env({"MATCH_SCOPE": "planet"}).match_scope == "city"


class FakeConn:
    def __init__(self, rows):
        self.rows, self.sql = rows, []

    def execute(self, sql, params=None):
        self.sql.append(sql)
        rows = self.rows
        return type("Cur", (), {"fetchall": lambda _self: rows})()


def test_scope_club_ids():
    conn = FakeConn([{"id": 1}, {"id": 2}])
    assert db.scope_club_ids(conn, 1, "club") == [1] and conn.sql == []
    assert db.scope_club_ids(conn, 1, "city") == [1, 2]
    assert "o.city" in conn.sql[-1] and "o.country" in conn.sql[-1]
    db.scope_club_ids(conn, 1, "country")
    assert "o.city" not in conn.sql[-1]
    assert db.scope_club_ids(FakeConn([]), 7, "city") == [7]  # unknown club: never widen to nothing


def test_club_suffix_only_across_clubs():
    row = {"club_id": 2, "club_name": "Cuenca Touring"}
    assert cli._club_suffix("es", row, 2) == ""
    assert cli._club_suffix("es", row, 1) == " (de Cuenca Touring)"
    assert cli._club_suffix("en", row, 1) == " (from Cuenca Touring)"


def test_text_match_needs_same_part_words():
    need = {"brand": "xray", "chassis": "x4", "part_number": "XRA303843", "description": "barra estabilizadora trasera"}
    other_part = {"brand": "xray", "chassis": "x4", "part_number": "XRA302842",
                  "description": "barra estabilizadora delantera"}
    assert not text_match_ok(need, other_part)  # different part numbers
    only_chassis = {"brand": "xray", "chassis": "x4", "part_number": None, "description": "mangueta de aluminio"}
    assert not text_match_ok({**need, "part_number": None}, only_chassis)  # only "xray x4" in common
    same = {"brand": "xray", "chassis": "x1", "part_number": None, "description": "pletina portacarrocería aluminio"}
    assert text_match_ok({"brand": None, "chassis": "x1", "part_number": None,
                          "description": "pletina portacarrocería de aluminio"}, same)


# --- close by text --------------------------------------------------------------------------

OWN = [
    {"id": 10, "kind": "HAVE", "brand": "xray", "chassis": "x1", "part_number": "XRA371203K",
     "description": "alerón delantero negro"},
    {"id": 11, "kind": "HAVE", "brand": "xray", "chassis": "x1", "part_number": "XRA378102",
     "description": "amortiguador central"},
    {"id": 12, "kind": "HAVE", "brand": "xray", "chassis": "x4", "part_number": "XRA303187H",
     "description": "brazo inferior trasero duro izquierdo"},
    {"id": 13, "kind": "NEED", "brand": "xray", "chassis": "x4", "part_number": "XRA302185M",
     "description": "brazo inferior delantero corto medio izquierdo"},
]


def test_close_pick_one():
    assert [l["id"] for l in pick_listings_to_close(OWN, "ya vendí el alerón delantero del X1", "HAVE")] == [10]
    assert [l["id"] for l in pick_listings_to_close(OWN, "ya no tengo el XRA-378102")] == [11]
    assert [l["id"] for l in pick_listings_to_close(OWN, "ya conseguí el brazo delantero", "NEED")] == [13]


def test_close_pick_ambiguous_and_none():
    assert {l["id"] for l in pick_listings_to_close(OWN, "ya vendí lo del X1", "HAVE")} == {10, 11}
    assert pick_listings_to_close(OWN, "ya vendí el piñón de la TT-02", "HAVE") == []
    assert pick_listings_to_close(OWN, "ya lo vendí", "HAVE") == []
    assert pick_listings_to_close([], "alerón") == []


def test_infer_close_kind():
    assert infer_close_kind("ya vendí el alerón") == "HAVE"
    assert infer_close_kind("I sold the wing") == "HAVE"
    assert infer_close_kind("ya conseguí el brazo") == "NEED"
    assert infer_close_kind("ya no lo necesito") == "NEED"
    assert infer_close_kind("cierra el #3") is None


def test_close_needs_id_or_text(capsys):
    code, out = run(capsys, "listing", "close", "--phone", "593990000002")
    assert code == 2 and out["error"] == "usage"


# --- deposit parsing ---------------------------------------------------------------------

@pytest.mark.parametrize("raw,value", [
    ("17.39", "17.39"), ("17,39", "17.39"), ("1.234,56", "1234.56"), ("1,234.56", "1234.56"),
    ("1 234,56", "1234.56"), ("17", "17.00"), ("1,234", "1234.00"), ("17.5", "17.50"),
])
def test_parse_amount(raw, value):
    assert parse_amount(raw) == D(value)


@pytest.mark.parametrize("text", ["Monto: $17.39", "Valor transferido USD 17,39", "Total 17.39 USD",
                                  "Importe:\nUS$ 17.39", "Amount: $ 17.39"])
def test_amount_formats(text):
    assert amount_candidates(text)[0] == D("17.39")


def test_labeled_amount_wins_over_other_money():
    text = "Comisión $0.50\nSaldo disponible USD 120.00\nMonto: USD 17,39"
    assert amount_candidates(text)[0] == D("17.39")


def test_reference_and_date():
    assert parse_reference("Ref: rc-q 12 transferencia") == "RC-Q12"
    assert parse_reference("RCQ0007") == "RC-Q7"
    assert parse_reference("sin referencia") is None
    assert parse_date("Fecha: 18/10/2026 13:05") == "2026-10-18"
    assert parse_date("2026-10-18T10:00") == "2026-10-18"
    assert parse_date("18 de octubre de 2026") == "2026-10-18"
    assert parse_date("31/02/2026") is None


def test_check_flags_mismatch():
    chk = check_receipt_text("Monto: USD 15.00\nReferencia: RC-Q8", D("17.39"), 9)
    assert chk.amount_usd == D("15.00") and not chk.amount_ok and not chk.reference_ok
    assert check_receipt_text("", D("17.39"), 9).amount_usd is None


def test_receipt_round_trip(tmp_path):
    pdf = make_test_receipt(tmp_path / "r.pdf", 12, D("17.39"))
    text = pdf_text(pdf)
    assert "NO VÁLIDO" in text and "ficticia" in text and "XXXX-0000 (demo)" in text
    chk = check_receipt_text(text, D("17.39"), 12)
    assert chk.amount_ok and chk.reference_ok and chk.receipt_date
    bad = check_receipt_text(pdf_text(make_test_receipt(tmp_path / "b.pdf", 12, D("15"))), D("17.39"), 12)
    assert bad.amount_usd == D("15.00") and not bad.amount_ok and bad.reference_ok


def test_newest_cached_pdf(tmp_path):
    old, new = tmp_path / "doc_aaa_old.pdf", tmp_path / "doc_bbb_new.pdf"
    old.write_bytes(b"%PDF-1.4 old")
    new.write_bytes(b"%PDF-1.4 new")
    (tmp_path / "doc_ccc_x.txt").write_text("no")
    os.utime(old, (time.time() - 60, time.time() - 60))
    assert newest_cached_pdf([tmp_path, tmp_path / "missing"]) == new
    os.utime(new, (time.time() - 3600, time.time() - 3600))
    os.utime(old, (time.time() - 3600, time.time() - 3600))
    assert newest_cached_pdf([tmp_path], max_age_s=900) is None


# --- maintainer only --------------------------------------------------------------------------

@pytest.mark.parametrize("argv", [
    ["deposit", "confirm", "--quote", "1", "--phone", "593990000002"],
    ["deposit", "reject", "--quote", "1", "--phone", "593990000002", "--reason", "x"],
    ["deposit", "list", "--phone", "593990000002"],
    ["deposit", "confirm", "--quote", "1"],  # no sender at all
])
def test_maintainer_only_refused(capsys, argv):
    code, out = run(capsys, *argv)
    assert code == 0 and out["ok"] is False and out["error"] == "not_maintainer"


def test_session_sender_beats_phone_flag(capsys, monkeypatch):
    # A member's turn cannot pass the maintainer's number to confirm their own payment.
    monkeypatch.setenv("HERMES_SESSION_USER_ID", "593990000002@s.whatsapp.net")
    _, out = run(capsys, "deposit", "confirm", "--quote", "1", "--phone", "593990000001")
    assert out["error"] == "not_maintainer"
    for argv in (["db", "reset", "--yes"], ["demo", "seed"], ["demo", "receipt", "--quote", "1"]):
        _, out = run(capsys, *argv)
        assert out["error"] == "not_maintainer", argv


def test_db_reset_needs_yes(capsys):
    _, out = run(capsys, "db", "reset")
    assert out["error"] == "confirm_required"
    assert out["tables"][:3] == ["clubs", "members", "listings"] and "deposits" in out["tables"]
    assert "conditions" not in out["tables"] and "sensors" not in out["tables"]


# --- order batch ------------------------------------------------------------------------------

@pytest.mark.parametrize("status,with_processing,order_id,expected", [
    ("paid", True, None, True),
    ("accepted", False, None, True),          # self-order: fee only, no deposit step
    ("accepted", True, None, False),          # legacy accepted-with-processing without a deposit
    ("awaiting_deposit", True, None, False),
    ("deposit_submitted", True, None, False),
    ("quoted", None, None, False),
    ("paid", True, 4, False),                 # already in an order
])
def test_order_eligibility(status, with_processing, order_id, expected):
    assert eligible_for_order({"status": status, "with_processing": with_processing, "order_id": order_id}) is expected
