"""Michael's RC Hobbies client: the shop's own `?format=json` views, nothing scraped from HTML."""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import httpx

from . import glossary
from .listing import join_model_codes, normalize_part_number

STORE_NAME = "michaelsrchobbies"
BASE_URL = "https://www.michaelsrchobbies.com/"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
)
# Shared across CLI invocations: every command is a new process, so the crawl delay
# (robots.txt asks for 2 s) has to be remembered on disk.
STAMP_FILE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "rcparts" / "last_store_request"


class StoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoreHit:
    store_id: int | None
    code: str
    sku: str
    ean: str
    title: str
    brand: str
    url: str
    price_usd: Decimal
    available: bool

    def as_json(self) -> dict:
        d = asdict(self)
        d["price_usd"] = str(self.price_usd)
        return d


@dataclass(frozen=True)
class StoreProduct:
    code: str
    sku: str
    title: str
    fulltitle: str
    brand: str
    url: str
    price_usd: Decimal
    weight: Decimal | None  # raw store value; the unit is not stated in the JSON
    available: bool
    on_stock: bool
    stock_level: int | None
    delivery: str

    def as_json(self) -> dict:
        d = asdict(self)
        d["price_usd"] = str(self.price_usd)
        d["weight"] = None if self.weight is None else str(self.weight)
        return d


def absolute_url(path_or_url: str) -> str:
    if urlparse(path_or_url).scheme:
        return path_or_url
    return BASE_URL + path_or_url.lstrip("/")


def _price(obj: dict | None) -> Decimal:
    price = (obj or {}).get("price")
    return Decimal(str(price)) if price is not None else Decimal("0")


def _brand(value) -> str:
    if isinstance(value, dict):
        return str(value.get("title") or "")
    return str(value or "")


def parse_search(data: dict) -> list[StoreHit]:
    """`collection.products` is a dict keyed by id in store order, or `false` when empty."""
    products = (data.get("collection") or {}).get("products") or {}
    items = products.values() if isinstance(products, dict) else products
    hits = []
    for p in items:
        hits.append(
            StoreHit(
                store_id=p.get("id"),
                code=str(p.get("code") or ""),
                sku=str(p.get("sku") or ""),
                ean=str(p.get("ean") or ""),
                title=" ".join(str(p.get("title") or "").split()),
                brand=_brand(p.get("brand")),
                url=absolute_url(str(p.get("url") or "")),
                price_usd=_price(p.get("price")),
                available=bool(p.get("available")),
            )
        )
    return hits


def parse_product(data: dict) -> StoreProduct:
    p = data.get("product")
    if not isinstance(p, dict):
        raise StoreError("product JSON has no 'product' object")
    stock = p.get("stock") or {}
    weight = p.get("weight")
    return StoreProduct(
        code=str(p.get("code") or ""),
        sku=str(p.get("sku") or ""),
        title=" ".join(str(p.get("title") or "").split()),
        fulltitle=" ".join(str(p.get("fulltitle") or "").split()),
        brand=_brand(p.get("brand")),
        url=absolute_url(str(p.get("url") or "")),
        price_usd=_price(p.get("price")),
        weight=Decimal(str(weight)) if weight not in (None, "", 0, False) else None,
        available=bool(stock.get("available")),
        on_stock=bool(stock.get("on_stock")),
        stock_level=stock.get("level"),
        delivery=str((stock.get("delivery") or {}).get("title") or ""),
    )


def _hit_codes(hit: StoreHit) -> set[str]:
    return {normalize_part_number(hit.code), normalize_part_number(hit.sku), hit.ean} - {""}


def pick_best(hits: list[StoreHit], query: str, words: list[str] | None = None) -> StoreHit | None:
    """Exact code/sku/ean match on the whole query or any word of it; else the hit whose title has the
    most query words (accent-folded); else (a tie or no words in common) the store's first hit."""
    if not hits:
        return None
    wanted = {normalize_part_number(query)} | {normalize_part_number(w) for w in query.split()}
    wanted.discard("")
    for hit in hits:
        if _hit_codes(hit) & wanted:
            return hit
    qwords = set(words if words is not None else content_words(query))
    if not qwords:
        return hits[0]
    best, best_n = hits[0], 0
    for hit in hits:
        n = len(qwords & set(glossary.words(join_model_codes(hit.title))))
        if n > best_n:
            best, best_n = hit, n
    return best


# Words a member wraps around the part ("cotízame el kit ...", "how much for the ...") that the store's
# search does not index, so a literal search for them returns nothing.
FILLER = frozenset(glossary.fold(w) for w in (
    "kit set de del la el los las lo para por for the a an un una unos unas of to my me mi "
    "busco buscando quiero necesito cotiza cotizame cotízame cotizar cotización cotizacion cuanto cuánto cuesta "
    "sale vale precio traer trae traeme tráeme hay tienes tienen puedes please porfa favor "
    "price quote how much need want looking get can you i im "
    "pieza piezas repuesto repuestos parte partes part parts spare original nuevo nueva new").split())


def content_words(query: str) -> list[str]:
    return [w for w in glossary.words(join_model_codes(query)) if w not in FILLER]


def _has_code(word: str) -> bool:
    """Model / part codes: letters and digits together ("xb2d", "xra303843") or a number of 3+ digits ("2026")."""
    return any(c.isdigit() for c in word) and (any(c.isalpha() for c in word) or len(word) >= 3)


def query_variants(query: str) -> list[str]:
    """Store queries to try in order: (1) as given, (2) without filler words, (3) codes plus the brand,
    (4) the words with the brand first. Duplicates (ignoring case and accents) are dropped."""
    raw = " ".join(query.split())
    content = content_words(raw)
    brands = [w for w in content if w in glossary.BRANDS]
    codes = [w for w in content if _has_code(w)]
    others = [w for w in content if w not in brands]
    variants = [raw, " ".join(content), " ".join(brands + codes) if codes else "", " ".join(brands + others)]
    out: dict[str, str] = {}
    for v in variants:
        key = " ".join(glossary.words(v))
        if key and key not in out:
            out[key] = v
    return list(out.values())


def search_with_fallbacks(client, queries: list[str], max_requests: int = 4):
    """Tries each query and its variants until the store returns hits, at most `max_requests` searches.
    Returns (hits, query_used, queries_tried)."""
    tried: list[str] = []
    seen: set[str] = set()
    for q in queries:
        for v in query_variants(q):
            key = " ".join(glossary.words(v))
            if key in seen:
                continue
            if len(tried) >= max_requests:
                return [], None, tried
            seen.add(key)
            tried.append(v)
            hits = client.search(v)
            if hits:
                return hits, v, tried
    return [], None, tried


class StoreClient:
    def __init__(self, crawl_delay_s: float = 2.0, client: httpx.Client | None = None):
        self.crawl_delay_s = crawl_delay_s
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=20.0,
            follow_redirects=True,
        )

    def _wait(self) -> None:
        try:
            last = float(STAMP_FILE.read_text())
        except (OSError, ValueError):
            last = 0.0
        sleep_for = last + self.crawl_delay_s - time.time()
        if sleep_for > 0:
            time.sleep(sleep_for)
        try:
            STAMP_FILE.parent.mkdir(parents=True, exist_ok=True)
            STAMP_FILE.write_text(str(time.time()))
        except OSError:
            pass

    def _get_json(self, url: str) -> dict:
        self._wait()
        sep = "&" if "?" in url else "?"
        try:
            resp = self.client.get(f"{url}{sep}format=json")
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise StoreError(f"store request failed: {exc}") from exc

    def search(self, query: str) -> list[StoreHit]:
        q = quote_plus(" ".join(query.split()))
        return parse_search(self._get_json(f"{BASE_URL}search/{q}/"))

    def product(self, path_or_url: str) -> StoreProduct:
        return parse_product(self._get_json(absolute_url(path_or_url)))
