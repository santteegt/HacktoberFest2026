from decimal import Decimal

import pytest

from rcparts.quote import cents, compute_quote, to_grams

D = Decimal


def test_reference_quote_tam54500():
    m = compute_quote(13, 113, D("25"), D("12"))
    assert m.store_price_usd == D("13.00")
    assert m.fee_usd == D("2.83")  # 0.113 kg * 25 = 2.825 -> half-up
    assert m.processing_usd == D("1.56")
    assert m.total_usd == D("15.83")
    assert m.total_with_processing_usd == D("17.39")


def test_totals_are_sums_of_rounded_parts():
    m = compute_quote("19.99", "333", D("25"), D("12"))
    assert m.fee_usd == D("8.33")  # 8.325
    assert m.processing_usd == D("2.40")  # 2.3988
    assert m.total_usd == m.store_price_usd + m.fee_usd
    assert m.total_with_processing_usd == m.total_usd + m.processing_usd
    assert m.total_with_processing_usd.as_tuple().exponent == -2


def test_qty_multiplies_price_and_weight():
    m = compute_quote(13, 113, D("25"), D("12"), qty=2)
    assert m.store_price_usd == D("26.00")
    assert m.weight_g == D("226")
    assert m.fee_usd == D("5.65")
    assert m.total_with_processing_usd == D("26.00") + D("5.65") + D("3.12")


def test_rejects_zero_qty():
    with pytest.raises(ValueError):
        compute_quote(1, 1, D("25"), D("12"), qty=0)


def test_cents_half_up():
    assert cents(D("0.005")) == D("0.01")
    assert cents(D("2.825")) == D("2.83")


def test_to_grams_units():
    assert to_grams(113, "g") == D("113.0")
    assert to_grams("0.25", "lb") == D("113.4")
    assert to_grams(4, "oz") == D("113.4")
    assert to_grams("0.113", "kg") == D("113.0")


def test_per_pound_rate_converts_to_per_kg(monkeypatch):
    from rcparts.config import Settings
    s = Settings.from_env({"FEE_PER_POUND_USD": "10"})
    assert s.fee_basis == "lb" and s.fee_rate_usd == D("10")
    m = compute_quote(13, 113, s.fee_per_kg_usd, D("12"))
    assert m.fee_usd == D("2.49")  # 113 g = 0.249 lb x 10 USD/lb


def test_db_url_alias():
    from rcparts.config import Settings
    assert Settings.from_env({"TIGER_DATA_DB_URL": "postgresql://x"}).database_url == "postgresql://x"
