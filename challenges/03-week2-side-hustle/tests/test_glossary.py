"""Offline tests: bilingual concepts in the matcher, store query fallbacks, quote accept parsing, delivery."""

import datetime as dt
from decimal import Decimal

import pytest

from rcparts import cli, glossary
from rcparts.matcher import query_concepts, rank_text_hits, text_match_ok
from rcparts.store import StoreHit, query_variants, search_with_fallbacks

X4_ARM = {"id": 1, "brand": "xray", "chassis": "x4", "part_number": "XRA303187H",
          "description": "brazo inferior trasero duro izquierdo"}
X4_SHOCKS = {"id": 2, "brand": "xray", "chassis": "x4", "part_number": "XRA308329",
             "description": "cuerpos de amortiguador XLP2 de aluminio (2)"}
X1_WING = {"id": 3, "brand": "xray", "chassis": "x1", "part_number": "XRA371203K",
           "description": "alerón delantero negro"}
X1_SHOCK = {"id": 4, "brand": "xray", "chassis": "x1", "part_number": "XRA378102",
            "description": "amortiguador central"}
X4_FRONT_BAR = {"id": 5, "brand": "xray", "chassis": "x4", "part_number": "XRA302842",
                "description": "barra estabilizadora delantera 1.2 mm"}
ALL = [X4_ARM, X4_SHOCKS, X1_WING, X1_SHOCK, X4_FRONT_BAR]


def ids(text):
    return [h["id"] for h in rank_text_hits(query_concepts(text), ALL)]


def test_fold_and_concepts():
    assert glossary.fold("Alerón Piñón") == "aleron pinon"
    assert glossary.concept_of("alerones") == glossary.concept_of("aleron") == "wing"
    assert glossary.concept_of("resortes") == "spring"
    assert glossary.concept_of("shocks") == glossary.concept_of("amortiguadores") == "shock"
    assert query_concepts("barras estabilizadoras") == ["anti_roll_bar"]
    assert query_concepts("sway bar") == ["anti_roll_bar"]
    assert query_concepts("rear lower arm") == ["rear", "lower", "arm"]
    assert query_concepts("I'm looking for a rear lower arm for the Xray X4") == ["rear", "lower", "arm", "xray", "x4"]


def test_rear_lower_arm_matches_spanish_listing():
    need = {"kind": "NEED", "brand": "xray", "chassis": "x4", "part_number": None, "description": "rear lower arm"}
    hits = rank_text_hits(query_concepts("xray", "x4", "rear lower arm"), [X4_ARM])
    assert [h["id"] for h in hits] == [1] and hits[0]["overlap"] == 5
    assert text_match_ok(need, X4_ARM)
    assert ids("I'm looking for a rear lower arm for the Xray X4")[0] == 1


def test_front_vs_rear_vetoes():
    need = {"kind": "NEED", "brand": "xray", "chassis": "x4", "part_number": None, "description": "front lower arm"}
    assert rank_text_hits(query_concepts("xray", "x4", "front lower arm"), [X4_ARM]) == []
    assert not text_match_ok(need, X4_ARM)
    assert not glossary.opposite_conflict({"left", "rear"}, {"left", "rear", "lower"})
    assert glossary.opposite_conflict({"upper"}, {"lower"})
    assert glossary.opposite_conflict({"right"}, {"left"})


def test_spanish_and_english_queries():
    assert ids("amortiguadores del X4") == [2]
    assert ids("shocks x4") == [2]
    assert ids("alerones x1") == [3]
    assert ids("aleron x1") == [3]


def test_seeded_no_match_stays_no_match():
    need = {"kind": "NEED", "brand": "xray", "chassis": "x4", "part_number": "XRA303843",
            "description": "barra estabilizadora trasera"}
    assert not text_match_ok(need, X4_FRONT_BAR)  # part numbers differ
    assert not text_match_ok({**need, "part_number": None}, X4_FRONT_BAR)  # rear vs front
    assert rank_text_hits(query_concepts("xray", "x4", None, "barra estabilizadora trasera"), [X4_FRONT_BAR]) == []


def test_tsquery_has_accented_and_folded_synonyms():
    from rcparts.matcher import _tsquery
    q = _tsquery(query_concepts("alerones x1"), "alerones x1")
    assert "alerón:*" in q and "aleron:*" in q and "spoiler:*" in q and "x1:*" in q
    assert "(barra:* & estabilizadora:*)" in _tsquery(["anti_roll_bar"], "")


# --- store fallbacks --------------------------------------------------------------------------

def _hit(code, title):
    return StoreHit(store_id=None, code=code, sku=code, ean="", title=title, brand="Xray", url=f"/{code}.html",
                    price_usd=Decimal("1"), available=True)


class FakeClient:
    """Returns hits only for the queries in `answers`; records every request."""

    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def search(self, q):
        self.calls.append(q)
        return self.answers.get(q.lower(), [])


def test_query_variants():
    assert query_variants("kit Xray XB2D 2026") == ["kit Xray XB2D 2026", "xray xb2d 2026"]
    v = query_variants("cotízame el brazo XRA303843 del X4 de Xray")
    assert v[1] == "brazo xra303843 x4 xray" and v[2] == "xray xra303843 x4" and v[3] == "xray brazo xra303843 x4"


def test_fallback_finds_xb2d_kit():
    kit = _hit("XRA320021", "XRA320021 XRAY XB2D 2026 1/10 2WD Off-Road Car Kit - Dirt Edition")
    client = FakeClient({"xray xb2d 2026": [kit]})
    hits, used, tried = search_with_fallbacks(client, ["kit Xray XB2D 2026"])
    assert hits == [kit] and used == "xray xb2d 2026" and tried == ["kit Xray XB2D 2026", "xray xb2d 2026"]


def test_fallback_caps_requests():
    client = FakeClient({})
    hits, used, tried = search_with_fallbacks(client, ["the TT-02 spur for tamiya", "TAM54500 again"], 4)
    assert hits == [] and used is None and len(client.calls) == 4 == len(tried)


# --- quote accept from free text ------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("sí", (None, False)), ("sí 5", (5, False)), ("#5", (5, False)), ("cotización 12", (12, False)),
    ("dale", (None, False)), ("lo compro yo 5", (5, True)), ("lo compro yo", (None, True)),
    ("yes 7", (7, False)), ("I'll buy it 9", (9, True)), ("si son $17.39 dale", (None, False)),
])
def test_parse_accept_text(text, expected):
    assert cli.parse_accept_text(text) == expected


def test_pick_pending_quote():
    now = dt.datetime(2026, 10, 18, 12, tzinfo=dt.timezone.utc)
    old = {"id": 1, "created_at": now - dt.timedelta(days=5)}
    new = {"id": 2, "created_at": now - dt.timedelta(hours=1)}
    newer = {"id": 3, "created_at": now - dt.timedelta(minutes=5)}
    assert cli.pick_pending_quote([old], now) == (old, [])
    assert cli.pick_pending_quote([old, new], now) == (new, [])
    assert cli.pick_pending_quote([old, new, newer], now) == (None, [newer, new])
    old2 = {"id": 4, "created_at": now - dt.timedelta(days=3)}
    assert cli.pick_pending_quote([old, old2], now) == (None, [old2, old])


@pytest.mark.parametrize("env,group", [
    ({"HERMES_SESSION_CHAT_TYPE": "group"}, True), ({"HERMES_SESSION_CHAT_TYPE": "dm"}, False),
    ({"HERMES_SESSION_CHAT_ID": "120363000000000000@g.us"}, True), ({}, False),
    ({"HERMES_SESSION_KEY": "agent:rc-parts:whatsapp:group:120363000000000000@g.us"}, True),
])
def test_in_group_session(env, group):
    assert cli.in_group_session(env) is group


def test_orders_mine_text():
    rows = [{"id": 9, "store_title": "TAM54500 Gear", "status": "in_transit", "with_processing": False,
             "fee_usd": "2.83", "total_usd": "15.83", "total_with_processing_usd": "17.39",
             "tracking_number": "1Z999AA10123456784"},
            {"id": 8, "store_title": "XRA303843 bar", "status": "awaiting_deposit", "with_processing": True,
             "fee_usd": "1.00", "total_usd": "10.00", "total_with_processing_usd": "11.20", "tracking_number": None}]
    es = cli.orders_mine_text("es", rows)
    assert "#9 TAM54500 Gear — en camino — solo tarifa $2.83 USD (la compras tú) — tracking 1Z999AA10123456784" in es
    assert "#8 XRA303843 bar — esperando depósito — total a pagar $11.20 USD" in es
    assert "in transit" in cli.orders_mine_text("en", rows)
    assert cli.orders_mine_text("en", []).startswith("You have no active orders")


def test_shared_modifier_is_not_the_same_part():
    need = {"kind": "NEED", "brand": "xray", "chassis": "x4", "part_number": None, "description": "front lower arm"}
    assert not text_match_ok(need, X4_FRONT_BAR)  # both "front", but an arm is not an anti-roll bar
    assert rank_text_hits(query_concepts("front arm x4"), [X4_FRONT_BAR]) == []
    alu = {"kind": "NEED", "brand": None, "chassis": "x1", "part_number": None, "description": "pletina de aluminio"}
    plate = {"brand": "xray", "chassis": "x1", "part_number": None, "description": "pletina portacarrocería aluminio"}
    assert text_match_ok(alu, plate)
