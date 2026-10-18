"""Builds the multi-line replies (quotes, daily order) from stored numbers."""

from __future__ import annotations

from collections import OrderedDict
from decimal import Decimal

from .i18n import STORE_LABEL, grams, money, t
from .config import WEIGHT_UNITS


def quote_reply(lang: str, q: dict, us_address: str, exact: bool = True) -> str:
    """`q` holds the quote row fields (store_*, weight_*, fee_*, processing_*, total_*, qty, in_stock)."""
    store = STORE_LABEL.get(q["store"], q["store"])
    weight = f"{grams(q['weight_store'])} {q['weight_unit']}"
    if q["weight_unit"] != "g":
        weight += f" (≈ {grams(q['weight_g'])} g)"
    if q["qty"] > 1:
        weight += f" × {q['qty']}"
    lines = [t(lang, "quote_head", store=store), q["store_title"]]
    if not exact:
        lines.append(t(lang, "quote_check_title"))
    if q["qty"] > 1:
        unit = Decimal(str(q["store_price_usd"])) / q["qty"]
        lines.append(t(lang, "quote_qty", qty=q["qty"], unit=money(unit)))
    lines += [
        t(lang, "quote_price", price=money(q["store_price_usd"])),
        t(lang, "quote_weight", weight=weight),
        (t(lang, "quote_fee_lb", lbs=f"{Decimal(str(q['weight_g'])) / WEIGHT_UNITS['lb']:.2f}",
           per_lb=money(q["fee_rate_usd"]), fee=money(q["fee_usd"]))
         if q.get("fee_basis") == "lb" else
         t(lang, "quote_fee", grams=grams(q["weight_g"]), per_kg=money(q["fee_per_kg_usd"]), fee=money(q["fee_usd"]))),
        t(lang, "quote_total_self", address=us_address, total=money(q["total_usd"])) if us_address
        else t(lang, "quote_total_plain", total=money(q["total_usd"])),
        t(lang, "quote_total_proc", pct=grams(q["processing_pct"]), proc=money(q["processing_usd"]),
          total=money(q["total_with_processing_usd"])),
        t(lang, "quote_stock_yes", delivery=f" ({q['stock_note']})" if q.get("stock_note") else "")
        if q["in_stock"] else t(lang, "quote_stock_no"),
        q["store_url"],
        t(lang, "quote_cta", id=q["id"]),
    ]
    return "\n".join(lines)


def eligible_for_order(q: dict) -> bool:
    """Into the order batch: paid quotes (deposit confirmed by the maintainer) and self-orders whose member
    sent a tracking number (in_transit). `accepted` self-orders predate the tracking step and still count."""
    if q.get("order_id") is not None:
        return False
    if q.get("status") == "paid":
        return True
    return q.get("status") in ("in_transit", "accepted") and q.get("with_processing") is False


def order_summary(lang: str, quotes: list[dict], order_ids: dict[str, int], date: str) -> tuple[str, dict]:
    """Groups accepted quotes by store, then by store code. Returns (text, per-store summary dict)."""
    by_store: OrderedDict[str, list[dict]] = OrderedDict()
    for q in quotes:
        by_store.setdefault(q["store"], []).append(q)
    lines = [t(lang, "orders_head", date=date)]
    stores = {}
    for store, qs in by_store.items():
        items: OrderedDict[str, dict] = OrderedDict()
        for q in qs:
            self_order = q.get("with_processing") is False
            key = f"{q.get('store_code') or q['store_url']}|{self_order}"
            it = items.setdefault(key, {"code": q.get("store_code") or "", "title": q.get("store_title") or "",
                                        "url": q["store_url"], "self_order": self_order, "qty": 0,
                                        "store_price_usd": Decimal(0), "phones": [], "quote_ids": [], "tracking": []})
            it["qty"] += q["qty"]
            it["store_price_usd"] += Decimal(str(q["store_price_usd"]))
            if q["member_phone"] not in it["phones"]:
                it["phones"].append(q["member_phone"])
            it["quote_ids"].append(q["id"])
            if q.get("tracking_number"):
                it["tracking"].append(q["tracking_number"])
        # Self-order quotes: the member buys the part and ships it to the US address,
        # so only the weight fee is collected and the store price is not in the order.
        placed = [q for q in qs if q.get("with_processing") is not False]
        subtotal = sum((Decimal(str(q["store_price_usd"])) for q in placed), Decimal(0))
        fees = sum((Decimal(str(q["fee_usd"])) for q in qs), Decimal(0))
        proc = sum((Decimal(str(q["processing_usd"])) for q in placed), Decimal(0))
        summary = {"store": store, "order_id": order_ids.get(store), "items": list(items.values()),
                   "store_subtotal_usd": subtotal, "fees_usd": fees, "processing_usd": proc,
                   "grand_total_usd": subtotal + fees + proc, "quote_ids": [q["id"] for q in qs]}
        stores[store] = summary
        lines.append("")
        lines.append(t(lang, "orders_store", store=STORE_LABEL.get(store, store), id=order_ids.get(store, "-")))
        for it in items.values():
            title = it["title"] if it["code"] and it["code"] in it["title"] else f"{it['code']} {it['title']}".strip()
            line = t(lang, "orders_item", qty=it["qty"], title=title, price=money(it["store_price_usd"]),
                     phone=", +".join(it["phones"]))
            if it["self_order"]:
                line += " " + t(lang, "orders_self", tracking=", ".join(it["tracking"]) or "-")
            lines.append(line)
            lines.append(f"  {it['url']}")
        lines.append(t(lang, "orders_totals", subtotal=money(subtotal), fees=money(fees), proc=money(proc),
                       total=money(subtotal + fees + proc)))
    return "\n".join(lines), stores
