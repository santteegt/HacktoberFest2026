"""Sourcify: verified source code and compiler settings (keyless)."""
from __future__ import annotations
from .. import config
from ..http import get_json


def verified(address: str, chain_id: int = 1) -> dict | None:
    d = get_json(f"{config.SOURCIFY_BASE}/v2/contract/{chain_id}/{address}",
                 params={"fields": "sources,compilation,abi"}, ttl=None)
    if not isinstance(d, dict) or not d.get("match"):
        return None
    comp = d.get("compilation") or {}
    sources = {name: (s.get("content") if isinstance(s, dict) else s) for name, s in (d.get("sources") or {}).items()}
    return {
        "match": d.get("match"),
        "name": comp.get("name"),
        "compiler_version": comp.get("compilerVersion"),
        "language": comp.get("language"),
        "sources": sources,
        "abi": d.get("abi"),
    }
