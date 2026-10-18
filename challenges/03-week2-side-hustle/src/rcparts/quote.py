"""Import quote math. Every number a member sees comes from here, never from the model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal

from .config import WEIGHT_UNITS

CENT = Decimal("0.01")


def cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def to_grams(weight: Decimal | float | int, unit: str) -> Decimal:
    return (Decimal(str(weight)) * WEIGHT_UNITS[unit]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class QuoteMath:
    qty: int
    unit_price_usd: Decimal
    store_price_usd: Decimal  # unit price x qty
    weight_g: Decimal  # total for qty
    fee_per_kg_usd: Decimal
    fee_usd: Decimal
    processing_pct: Decimal
    processing_usd: Decimal
    total_usd: Decimal
    total_with_processing_usd: Decimal

    def as_json(self) -> dict:
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in asdict(self).items()}


def compute_quote(
    unit_price_usd: Decimal | float | str,
    unit_weight_g: Decimal | float | str,
    fee_per_kg_usd: Decimal,
    processing_pct: Decimal,
    qty: int = 1,
) -> QuoteMath:
    """Each component is rounded to cents first and the totals are sums of rounded parts,
    so the lines in the reply always add up to the total shown."""
    if qty < 1:
        raise ValueError("qty must be >= 1")
    unit_price = cents(Decimal(str(unit_price_usd)))
    store_price = cents(unit_price * qty)
    weight_g = Decimal(str(unit_weight_g)) * qty
    fee = cents(weight_g / Decimal(1000) * fee_per_kg_usd)
    processing = cents(store_price * processing_pct / Decimal(100))
    total = store_price + fee
    return QuoteMath(
        qty=qty,
        unit_price_usd=unit_price,
        store_price_usd=store_price,
        weight_g=weight_g,
        fee_per_kg_usd=fee_per_kg_usd,
        fee_usd=fee,
        processing_pct=processing_pct,
        processing_usd=processing,
        total_usd=total,
        total_with_processing_usd=total + processing,
    )
