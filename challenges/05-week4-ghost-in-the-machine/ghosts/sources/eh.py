"""Ethereum History (ethereumhistory.com): birth, body, decompiled code and the historians' story."""
from __future__ import annotations
from .. import config
from ..http import get_json


def _headers():
    return {"x-api-key": config.EH_API_KEY} if config.EH_API_KEY else {}


def contract(address: str) -> dict | None:
    d = get_json(f"{config.EH_BASE}/api/agent/contracts/{address.lower()}", headers=_headers(), ttl=None)
    return (d or {}).get("data") if isinstance(d, dict) else None


def discover(**params) -> list[dict]:
    """Filters: era_id, featured, undocumented_only, q, from_timestamp, to_timestamp, limit, offset."""
    d = get_json(f"{config.EH_BASE}/api/agent/contracts", params=params, headers=_headers(), ttl=86400)
    return (d or {}).get("data", []) if isinstance(d, dict) else []


def abi(address: str) -> list | None:
    d = get_json(f"{config.EH_BASE}/api/contract/{address.lower()}/abi", headers=_headers(), ttl=None)
    return (d or {}).get("abi") if isinstance(d, dict) else None
