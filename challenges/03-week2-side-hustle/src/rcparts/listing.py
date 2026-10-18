"""Validation and normalization of the listing JSON the model produces."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

KINDS = ("HAVE", "NEED")
CONDITIONS = {"new": "new", "nuevo": "new", "nueva": "new", "used": "used", "usado": "used", "usada": "used"}
_PART_STRIP = re.compile(r"[\s\-_]+")
# "TT-02" and "TT02" must index as the same word, or full-text search misses them.
# Dash only: joining on spaces would glue "gear 68T" into one word.
_MODEL_CODE = re.compile(r"\b([A-Za-z]{1,5})-(?=\d)")


def normalize_part_number(value) -> str:
    """`TAM 54500`, `tam-54500` -> `TAM54500`."""
    return _PART_STRIP.sub("", str(value or "")).upper()


def join_model_codes(value: str | None) -> str | None:
    return _MODEL_CODE.sub(r"\1", value) if value else value


def normalize_phone(value) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _text(value, lower: bool = False, limit: int = 300) -> str | None:
    if value is None:
        return None
    s = " ".join(str(value).split())[:limit]
    if lower:
        s = s.lower()
    return s or None


@dataclass
class Validation:
    ok: bool
    listing: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_listing(raw) -> Validation:
    """Unknown keys are ignored. `missing` is ordered: the first entry is the one question to ask."""
    if not isinstance(raw, dict):
        return Validation(ok=False, missing=["listing"])
    warnings: list[str] = []
    kind = str(raw.get("kind") or "").strip().upper()
    listing = {
        "kind": kind if kind in KINDS else None,
        "brand": _text(raw.get("brand"), lower=True, limit=60),
        "chassis": join_model_codes(_text(raw.get("chassis"), lower=True, limit=60)),
        "part_number": normalize_part_number(raw.get("part_number")) or None,
        "description": join_model_codes(_text(raw.get("description"))),
        "condition": None,
        "price_usd": None,
        "qty": 1,
    }

    if listing["kind"] == "HAVE":
        cond = str(raw.get("condition") or "").strip().lower()
        listing["condition"] = CONDITIONS.get(cond, "unknown")
        if raw.get("price_usd") not in (None, ""):
            try:
                price = Decimal(str(raw["price_usd"]).replace("$", "").strip())
                if price < 0 or price > 100000:
                    raise InvalidOperation
                listing["price_usd"] = price.quantize(Decimal("0.01"))
            except (InvalidOperation, ValueError):
                warnings.append("price_usd ignored: not a valid amount")

    if raw.get("qty") not in (None, ""):
        try:
            qty = int(str(raw["qty"]).strip())
            if not 1 <= qty <= 999:
                raise ValueError
            listing["qty"] = qty
        except ValueError:
            warnings.append("qty ignored: not a whole number between 1 and 999")

    missing = []
    if listing["kind"] is None:
        missing.append("kind")
    if not listing["part_number"]:
        has_vehicle = bool(listing["brand"] or listing["chassis"])
        if not has_vehicle and not listing["description"]:
            missing.append("part_number")
        elif not listing["description"]:
            missing.append("description")
        elif not has_vehicle:
            missing.append("brand_or_chassis")
    return Validation(ok=not missing, listing=listing, missing=missing, warnings=warnings)
