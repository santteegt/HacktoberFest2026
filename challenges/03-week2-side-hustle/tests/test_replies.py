from decimal import Decimal

import pytest

from rcparts.i18n import T, describe
from rcparts.quote import compute_quote
from rcparts.replies import order_summary, quote_reply


def _quote_row(unit="g", weight_store=Decimal("113")):
    m = compute_quote(13, 113, Decimal("25"), Decimal("12"))
    return {
        "id": 7, "store": "michaelsrchobbies", "store_url": "https://www.michaelsrchobbies.com/tam54500.html",
        "store_code": "TAM54500", "store_title": "Tamiya TAM54500 RC TT02 High Speed Gear Set, 68T (TCS)",
        "store_price_usd": m.store_price_usd, "weight_store": weight_store, "weight_unit": unit,
        "weight_g": m.weight_g, "fee_per_kg_usd": m.fee_per_kg_usd, "fee_usd": m.fee_usd,
        "processing_pct": Decimal("12.00"), "processing_usd": m.processing_usd, "total_usd": m.total_usd,
        "total_with_processing_usd": m.total_with_processing_usd, "in_stock": True,
        "stock_note": "Ships within 24hrs", "qty": 1,
    }


def test_languages_have_same_keys():
    assert set(T["es"]) == set(T["en"])


@pytest.mark.parametrize("lang,cta", [("es", "«sí 7»"), ("en", "«yes 7»")])
def test_quote_reply_has_all_numbers(lang, cta):
    text = quote_reply(lang, _quote_row(), "Miami FL 33101")
    for needle in ("$13.00", "113 g", "$25.00/kg", "$2.83", "$15.83", "12%", "$1.56", "$17.39",
                   "Miami FL 33101", "https://www.michaelsrchobbies.com/tam54500.html", cta, "#7",
                   "Ships within 24hrs"):
        assert needle in text, (lang, needle)


def test_quote_reply_without_address_and_not_exact():
    text = quote_reply("en", _quote_row(), "", exact=False)
    assert "Total with import: $15.83 USD" in text
    assert "exact code" in text


def test_quote_reply_other_unit_shows_grams():
    text = quote_reply("en", _quote_row(unit="oz", weight_store=Decimal("4")), "")
    assert "4 oz (≈ 113 g)" in text


def test_describe():
    item = {"kind": "HAVE", "part_number": "TAM54500", "brand": "tamiya", "chassis": "tt02",
            "description": "68T spur", "condition": "used", "price_usd": Decimal("10"), "qty": 2}
    assert describe("en", item) == "TAM54500 · tamiya tt02 · 68T spur (used, $10.00, x2)"
    assert describe("es", item).endswith("(usado, $10.00, x2)")


def test_order_summary_groups_and_totals():
    base = _quote_row()
    quotes = [
        {**base, "id": 1, "member_phone": "593990000001", "with_processing": True},
        {**base, "id": 2, "member_phone": "593990000002", "with_processing": True},
        {**base, "id": 3, "member_phone": "593990000003", "with_processing": False},
    ]
    text, stores = order_summary("en", quotes, {"michaelsrchobbies": 4}, "2026-10-18")
    s = stores["michaelsrchobbies"]
    assert s["store_subtotal_usd"] == Decimal("26.00")
    assert s["fees_usd"] == Decimal("8.49")
    assert s["processing_usd"] == Decimal("3.12")
    assert s["grand_total_usd"] == Decimal("37.61")
    assert len(s["items"]) == 2 and s["items"][0]["qty"] == 2
    assert "+593990000001, +593990000002" in text
    assert "$37.61" in text and "order #4" in text
    assert "only the fee" in text
