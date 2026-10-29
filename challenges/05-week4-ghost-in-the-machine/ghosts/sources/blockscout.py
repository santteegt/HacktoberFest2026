"""Blockscout (eth.blockscout.com, keyless): the contract's life and death on chain."""
from __future__ import annotations
from .. import config
from ..http import get_json


def address(addr: str) -> dict | None:
    return get_json(f"{config.BLOCKSCOUT_BASE}/addresses/{addr}", ttl=86400)


def counters(addr: str) -> dict | None:
    return get_json(f"{config.BLOCKSCOUT_BASE}/addresses/{addr}/counters", ttl=86400)


def newest_transactions(addr: str, limit: int = 50) -> list[dict]:
    d = get_json(f"{config.BLOCKSCOUT_BASE}/addresses/{addr}/transactions", params={"filter": "to"}, ttl=86400)
    return ((d or {}).get("items") or [])[:limit]


def transaction(tx_hash: str) -> dict | None:
    return get_json(f"{config.BLOCKSCOUT_BASE}/transactions/{tx_hash}", ttl=None)


def smart_contract(addr: str) -> dict | None:
    """Verified source as Blockscout holds it (a second source when Sourcify has none)."""
    return get_json(f"{config.BLOCKSCOUT_BASE}/smart-contracts/{addr}", ttl=None)


def _ts(s: str | None) -> float | None:
    """Blockscout ISO timestamp -> epoch seconds (None when missing or malformed)."""
    if not s:
        return None
    from datetime import datetime
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def recent_activity(addr: str, *, days: int = 365, max_pages: int = 10, now: float | None = None, skip=None) -> dict:
    """Count successful calls *to* the contract in the last `days`, newest first.

    Follows next_page_params; stops at the first tx older than the window, or after `max_pages`
    pages (50 txs each), in which case `capped` is true and the count is a floor.
    `skip(tx)` drops txs that are not calls (the creation tx, which Blockscout lists under filter=to).
    """
    import time as _time
    now = _time.time() if now is None else now
    cutoff = now - days * 86400
    params: dict = {"filter": "to"}
    ok = seen = pages = 0
    capped = False
    while True:
        d = get_json(f"{config.BLOCKSCOUT_BASE}/addresses/{addr}/transactions", params=params, ttl=86400) or {}
        pages += 1
        items = d.get("items") or []
        older = False
        for t in items:
            ts = _ts(t.get("timestamp"))
            if ts is not None and ts < cutoff:
                older = True
                break
            if skip and skip(t):
                continue
            seen += 1
            if t.get("status") == "ok":
                ok += 1
        nxt = d.get("next_page_params")
        if older or not nxt or not items:
            break
        if pages >= max_pages:
            capped = True
            break
        params = {**nxt, "filter": "to"}
    return {"ok": ok, "seen": seen, "pages": pages, "capped": capped}


def newest_page(addr: str) -> dict:
    """First page (50, newest first) of txs to the contract, with next_page_params (same cache as newest_transactions)."""
    return get_json(f"{config.BLOCKSCOUT_BASE}/addresses/{addr}/transactions", params={"filter": "to"}, ttl=86400) or {}


def first_transaction(addr: str, skip=None) -> dict | None:
    """Oldest tx to the contract that `skip` does not drop (one call: Blockscout sorts by block_number ascending)."""
    d = get_json(f"{config.BLOCKSCOUT_BASE}/addresses/{addr}/transactions",
                 params={"filter": "to", "sort": "block_number", "order": "asc"}, ttl=None)
    for t in (d or {}).get("items") or []:
        if not (skip and skip(t)):
            return t
    return None


def count_calls(addr: str, *, skip=None, max_pages: int = 20) -> dict:
    """Count every tx to the contract (newest first) when the counters endpoint cannot be trusted.

    Returns {calls, ok, newest_ok, pages, capped}; capped means the count is a floor (max_pages x 50)."""
    params: dict = {"filter": "to"}
    calls = ok = pages = 0
    newest_ok = None
    while True:
        d = get_json(f"{config.BLOCKSCOUT_BASE}/addresses/{addr}/transactions", params=params, ttl=86400) or {}
        pages += 1
        items = d.get("items") or []
        for t in items:
            if skip and skip(t):
                continue
            calls += 1
            if t.get("status") == "ok":
                ok += 1
                newest_ok = newest_ok or t
        nxt = d.get("next_page_params")
        if not nxt or not items:
            return {"calls": calls, "ok": ok, "newest_ok": newest_ok, "pages": pages, "capped": False}
        if pages >= max_pages:
            return {"calls": calls, "ok": ok, "newest_ok": newest_ok, "pages": pages, "capped": True}
        params = {**nxt, "filter": "to"}
