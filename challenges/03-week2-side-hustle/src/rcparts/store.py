"""Michael's RC Hobbies client: the shop's own `?format=json` views, nothing scraped from HTML."""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import httpx

from .listing import normalize_part_number

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


def pick_best(hits: list[StoreHit], query: str) -> StoreHit | None:
    """Exact code/sku/ean match on the whole query or any word of it, else the store's top hit."""
    if not hits:
        return None
    wanted = {normalize_part_number(query)} | {normalize_part_number(w) for w in query.split()}
    wanted.discard("")
    for hit in hits:
        if {normalize_part_number(hit.code), normalize_part_number(hit.sku), hit.ean} & wanted:
            return hit
    return hits[0]


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
