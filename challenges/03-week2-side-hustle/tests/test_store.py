import os
from decimal import Decimal

import pytest

from rcparts.store import StoreClient, absolute_url, parse_product, parse_search, pick_best


def test_parse_single_search(load_fixture):
    hits = parse_search(load_fixture("search_tam54500.json"))
    assert len(hits) == 1
    h = hits[0]
    assert h.code == "TAM54500" and h.sku == "TAM54500"
    assert h.price_usd == Decimal("13")
    assert h.available is True
    assert h.brand == "Tamiya"
    assert h.url == "https://www.michaelsrchobbies.com/tam54500-rc-tt02-high-speed-gear-set-68t-tcs.html"
    assert "  " not in h.title


def test_parse_multi_search_keeps_store_order(load_fixture):
    hits = parse_search(load_fixture("search_tt02_gear.json"))
    assert len(hits) == 7
    assert hits[0].code == "YEA-TT02-013BU"
    assert any(not h.available for h in hits)


def test_empty_search_is_false():
    # The store returns `"products": false` when nothing matches (seen 2026-10-17).
    assert parse_search({"collection": {"count": 0, "products": False}}) == []


def test_pick_best_prefers_exact_code(load_fixture):
    hits = parse_search(load_fixture("search_tt02_gear.json"))
    assert pick_best(hits, "tam 54500").code == "TAM54500"
    assert pick_best(hits, "spur TAM-54500 please").code == "TAM54500"
    assert pick_best(hits, "tt02 gear").code == "YEA-TT02-013BU"  # top result fallback
    assert pick_best([], "anything") is None


def test_parse_product(load_fixture):
    p = parse_product(load_fixture("product_tam54500.json"))
    assert p.code == "TAM54500"
    assert p.weight == Decimal("113")
    assert p.price_usd == Decimal("13")
    assert p.available and p.on_stock
    assert p.stock_level == 1
    assert p.delivery == "Ships within 24hrs"
    assert p.fulltitle.startswith("Tamiya TAM54500")
    assert p.url.startswith("https://www.michaelsrchobbies.com/")


def test_parse_product_without_weight():
    p = parse_product({"product": {"code": "X", "price": {"price": 5}, "weight": 0, "stock": {}}})
    assert p.weight is None and not p.available


def test_absolute_url():
    assert absolute_url("/a.html") == "https://www.michaelsrchobbies.com/a.html"
    assert absolute_url("https://x.test/a") == "https://x.test/a"


@pytest.mark.skipif(os.environ.get("RCPARTS_LIVE") != "1", reason="live store call; set RCPARTS_LIVE=1")
def test_live_tam54500():
    client = StoreClient(crawl_delay_s=2)
    best = pick_best(client.search("TAM54500"), "TAM54500")
    assert best and best.code == "TAM54500"
    p = client.product(best.url)
    assert p.weight is not None and p.price_usd > 0
