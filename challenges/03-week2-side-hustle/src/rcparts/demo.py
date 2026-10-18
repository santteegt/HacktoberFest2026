"""Demo data: real Xray X4 / X1 parts from Michael's RC Hobbies search, seeded for an on-camera run.

Only the two allowlisted real numbers are used (the maintainer and one member); no fictional members.
The store is hit once (6 searches, crawl delay respected) and the result is cached in data/demo_catalog.json.
"""

from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

from .listing import normalize_part_number
from .store import STORE_NAME, StoreClient

QUERIES = {
    "x4": ["xray x4", "xray x4 arm"],
    "x1": ["xray x1", "xray x1 front", "x1'25", "x1 graphite"],
}
# Distinct real products picked from those searches (seen 2026-10-18); missing ones are skipped.
PICKS = {
    "x4": ["XRA302242", "XRA308329", "XRA302842", "XRA303843", "XRA303187-H", "XRA302185-M", "XRA302145-S",
           "XRA301028", "X4-2026TDRHD-20", "OFC-UP-49-X4"],
    "x1": ["XRA371201", "XRA371203-K", "XRA378102", "XRA372326", "XRA371290", "XRA371202", "XRA372127",
           "XRA372087", "XRA373583", "XRA371082"],
}

CLUB_A = {"name": "RC Club Cuenca", "country": "EC", "city": "Cuenca"}
CLUB_B = {"name": "Cuenca Touring", "country": "EC", "city": "Cuenca"}

# Listings by part code. `price` is "store" (same as the store) or a fraction of the store price.
# A = the maintainer (Santiago, club A), B = the other member (Socio, club B).
HAVES = [
    ("A", "XRA302242", "x4", "mangueta de aluminio liviana", "new", Decimal("0.85")),
    ("A", "XRA308329", "x4", "cuerpos de amortiguador XLP2 de aluminio (2)", "used", Decimal("0.6")),
    ("A", "XRA302842", "x4", "barra estabilizadora delantera 1.2 mm", "new", "store"),
    ("A", "XRA371201", "x1", "parachoques delantero", "used", Decimal("0.65")),
    ("B", "XRA303187-H", "x4", "brazo inferior trasero duro izquierdo", "new", "store"),
    ("B", "XRA371203-K", "x1", "alerón delantero negro", "used", Decimal("0.7")),
    ("B", "XRA378102", "x1", "amortiguador central", "new", "store"),
    ("B", "XRA372326", "x1", "bujes de camber 2 puntos (2)", "used", Decimal("0.6")),
]
# (owner, code or None, chassis, description). Case (b) has no part number on purpose: the text path.
NEEDS = [
    ("A", None, "x1", "pletina portacarrocería de aluminio"),
    ("B", "XRA302185-M", "x4", "brazo inferior delantero corto medio izquierdo"),
]
CASE_A_CODE = "XRA303187-H"   # A posts a NEED; B (other club) has it -> exact part number match
CASE_C_CODE = "XRA303843"     # nobody has it -> import quote


def fetch_catalog(client: StoreClient) -> dict:
    found: dict[str, dict] = {}
    for chassis, queries in QUERIES.items():
        for q in queries:
            for h in client.search(q):
                code = normalize_part_number(h.code)
                if code and code not in found:
                    found[code] = {"code": h.code, "title": h.title, "price_usd": str(h.price_usd),
                                   "url": h.url, "available": h.available, "query": q}
    catalog = {"store": STORE_NAME, "fetched_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
               "chassis": {}}
    for chassis, codes in PICKS.items():
        items = []
        for code in codes:
            item = found.get(normalize_part_number(code))
            if item:
                items.append({**item, "chassis": chassis})
        catalog["chassis"][chassis] = items
    return catalog


def load_catalog(path: Path, refresh: bool, client_factory) -> tuple[dict, bool]:
    """Returns (catalog, fetched_now)."""
    if not refresh and path.is_file():
        return json.loads(path.read_text(encoding="utf-8")), False
    catalog = fetch_catalog(client_factory())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog, True


def by_code(catalog: dict) -> dict[str, dict]:
    return {normalize_part_number(i["code"]): i for items in catalog["chassis"].values() for i in items}


def _price(item: dict, rule) -> Decimal:
    store = Decimal(item["price_usd"])
    if rule == "store":
        return store
    return max(Decimal("1"), (store * rule).quantize(Decimal("1")))  # members round used prices


def plan_listings(catalog: dict) -> list[dict]:
    """[{owner, listing_json}] for the seed, skipping parts the store no longer lists."""
    items, out = by_code(catalog), []
    for owner, code, chassis, desc, cond, rule in HAVES:
        item = items.get(normalize_part_number(code))
        if not item:
            continue
        out.append({"owner": owner, "listing": {
            "kind": "HAVE", "brand": "xray", "chassis": chassis, "part_number": item["code"], "description": desc,
            "condition": cond, "price_usd": str(_price(item, rule)), "qty": 1},
            "store_price_usd": item["price_usd"], "store_title": item["title"]})
    for owner, code, chassis, desc in NEEDS:
        if code and normalize_part_number(code) not in items:
            continue
        listing = {"kind": "NEED", "brand": "xray", "chassis": chassis, "description": desc}
        if code:
            listing["part_number"] = items[normalize_part_number(code)]["code"]
        out.append({"owner": owner, "listing": listing})
    return out


def demo_script(catalog: dict) -> list[dict]:
    items = by_code(catalog)
    a = items.get(normalize_part_number(CASE_A_CODE), {"code": CASE_A_CODE, "title": ""})
    c = items.get(normalize_part_number(CASE_C_CODE), {"code": CASE_C_CODE, "title": ""})
    return [
        {"case": "a_exact_cross_club", "who": "Santiago (RC Club Cuenca), in the club group",
         "say": f"@bot busco el {a['code']}, brazo inferior trasero duro izquierdo del X4",
         "expect": "Exact part-number match with Socio's HAVE in Cuenca Touring; both get a DM naming the other club."},
        {"case": "b_text_match", "who": "Socio (Cuenca Touring), by DM",
         "say": "tengo una pletina portacarrocería de aluminio del Xray X1, usada, $15",
         "expect": "Text match with Santiago's NEED (no part number) in RC Club Cuenca."},
        {"case": "c_import_quote", "who": "Socio (Cuenca Touring), by DM",
         "say": f"busco la barra estabilizadora trasera {c['code']} del X4",
         "expect": "No match in Cuenca; the bot offers an import quote. Then: \"sí, cotízala\" -> quote -> \"sí\" "
                   "-> deposit instructions (RC-Q<id>) -> send the PDF made by `rcparts demo receipt --quote <id>` "
                   "(data/receipts/demo-RC-Q<id>.pdf) as a document in the same DM."},
        {"case": "d_close_by_text", "who": "Socio (DM)",
         "say": "ya vendí el alerón delantero del X1",
         "expect": "Closes Socio's X1 front wing listing (sold)."},
        {"case": "e_confirm_payment", "who": "Santiago (DM, maintainer)",
         "say": "confirmar <quote id>",
         "expect": "Quote becomes paid; Socio gets 'pago confirmado'; it enters the next order batch."},
    ]
