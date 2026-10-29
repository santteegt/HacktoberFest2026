"""JSON-RPC against public nodes. State calls go to RPC_URL; old full blocks to ARCHIVE_RPC_URL."""
from __future__ import annotations
from .. import config
from ..http import get_json

_id = 0


def call(method: str, params: list, *, archive: bool = False, ttl: float | None = 3600):
    global _id
    _id += 1
    url = config.ARCHIVE_RPC_URL if archive else config.RPC_URL
    d = get_json(url, method="POST", body={"jsonrpc": "2.0", "id": _id, "method": method, "params": params}, ttl=ttl)
    if not isinstance(d, dict):
        return None
    if "error" in d:
        raise RuntimeError(f"rpc {method}: {d['error']}")
    return d.get("result")


def get_code(addr: str) -> str:
    return call("eth_getCode", [addr, "latest"]) or "0x"


def get_balance_wei(addr: str) -> int:
    return int(call("eth_getBalance", [addr, "latest"], ttl=3600) or "0x0", 16)


def block(number: int, full: bool = False) -> dict | None:
    # old blocks need the archive-capable node (publicnode prunes before 15,500,000)
    return call("eth_getBlockByNumber", [hex(number), full], archive=True, ttl=None)


def receipt(tx_hash: str) -> dict | None:
    return call("eth_getTransactionReceipt", [tx_hash], archive=True, ttl=None)
