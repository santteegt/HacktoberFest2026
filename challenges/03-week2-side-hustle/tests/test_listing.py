from decimal import Decimal

from rcparts.listing import normalize_part_number, normalize_phone, validate_listing


def test_part_number_normalized():
    assert normalize_part_number("TAM 54500") == "TAM54500"
    assert normalize_part_number(" tam-54500 ") == "TAM54500"
    assert normalize_part_number(None) == ""


def test_phone_digits_only():
    assert normalize_phone("+593 99-123 4567") == "593991234567"


def test_have_with_part_number_ok_and_normalized():
    v = validate_listing({"kind": "have", "part_number": "tam 54500", "brand": "  Tamiya ", "chassis": "TT-02",
                          "condition": "Usado", "price_usd": "10", "qty": "2", "color": "ignored"})
    assert v.ok and v.missing == []
    assert v.listing["kind"] == "HAVE"
    assert v.listing["part_number"] == "TAM54500"
    assert v.listing["brand"] == "tamiya"
    assert v.listing["chassis"] == "tt02"
    assert v.listing["condition"] == "used"
    assert v.listing["price_usd"] == Decimal("10.00")
    assert v.listing["qty"] == 2
    assert "color" not in v.listing


def test_need_without_part_number_needs_vehicle_and_description():
    v = validate_listing({"kind": "NEED", "brand": "tamiya", "chassis": "tt02", "description": "68T spur gear"})
    assert v.ok
    assert v.listing["condition"] is None and v.listing["price_usd"] is None


def test_missing_kind_is_first_question():
    v = validate_listing({"part_number": "TAM54500"})
    assert not v.ok and v.missing == ["kind"]


def test_missing_identity():
    assert validate_listing({"kind": "NEED"}).missing == ["part_number"]
    assert validate_listing({"kind": "NEED", "chassis": "tt02"}).missing == ["description"]
    assert validate_listing({"kind": "NEED", "description": "spur gear"}).missing == ["brand_or_chassis"]


def test_bad_price_and_qty_become_warnings():
    v = validate_listing({"kind": "HAVE", "part_number": "X1", "price_usd": "cheap", "qty": 0})
    assert v.ok
    assert v.listing["price_usd"] is None and v.listing["qty"] == 1
    assert len(v.warnings) == 2


def test_condition_unknown_default_and_need_has_no_condition():
    assert validate_listing({"kind": "HAVE", "part_number": "X1"}).listing["condition"] == "unknown"
    assert validate_listing({"kind": "NEED", "part_number": "X1", "condition": "new"}).listing["condition"] is None


def test_not_an_object():
    assert validate_listing(["HAVE"]).missing == ["listing"]
