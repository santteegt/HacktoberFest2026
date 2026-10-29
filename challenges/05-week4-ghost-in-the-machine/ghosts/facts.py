"""Assemble facts.json for one contract. Every value here comes from a source, never from a model."""
from __future__ import annotations
import json, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from . import config
from .hardforks import age_of
from .sources import eh, sourcify, blockscout, rpc, wayback

WEI = 10**18


def clean_name(v) -> str | None:
    """A display name, or None when it is empty after dropping control/non-printable chars and whitespace.

    Blockscout returns "\u0001" as TheDAO's name; that is not a name."""
    if not isinstance(v, str):
        return None
    v = "".join(ch for ch in v if ch.isprintable()).strip()
    return v or None


GENERIC_NAMES = {n.lower() for n in (
    "MyToken", "Token", "Contract", "Vyper_contract", "AdminUpgradeabilityProxy", "TransparentUpgradeableProxy",
    "Proxy", "ERC20", "StandardToken", "HumanStandardToken", "Crowdsale", "TemplateCrowdsale", "greeter")}


def is_generic(name: str | None) -> bool:
    """Template or framework names (MyToken, Vyper_contract, AdminUpgradeabilityProxy...) that say nothing about the contract."""
    return (name or "").strip().lower() in GENERIC_NAMES


def name_candidates(f: dict) -> list[dict]:
    """Every name a source gives, in display priority: archive, then Blockscout, then the verified source."""
    eh_ = f.get("eh") or {}
    src = f.get("source") or {}
    out = []
    for v, where in ((eh_.get("name"), "ethereumhistory"),
                     ((eh_.get("token") or {}).get("token_name"), "ethereumhistory:token_name"),
                     ((f.get("blockscout") or {}).get("name"), "blockscout"),
                     (src.get("name"), f"source:{src.get('provider') or 'unknown'}")):
        n = clean_name(v)
        if n:
            out.append({"name": n, "source": where, "generic": is_generic(n)})
    return out


def pick_name(f: dict) -> str:
    """First non-generic name (archive -> Blockscout -> verified source), else any name, else the address."""
    c = name_candidates(f)
    for x in c:
        if not x["generic"]:
            return x["name"]
    return c[0]["name"] if c else (f.get("address") or "")


def is_proxy(f: dict) -> bool:
    if ((f.get("eh") or {}).get("heuristics") or {}).get("is_proxy"):
        return True
    return any("proxy" in x["name"].lower() for x in name_candidates(f))


def set_names(f: dict) -> bool:
    """facts.name, facts.names, facts.proxy. Returns True when anything changed."""
    new = {"name": pick_name(f), "names": [{"name": x["name"], "source": x["source"]} for x in name_candidates(f)],
           "proxy": is_proxy(f)}
    changed = any(f.get(k) != v for k, v in new.items())
    f.update(new)
    return changed


def safe_relpath(name: str) -> Path:
    """Keep a source path relative (Sourcify keys like 'contracts/A.sol' or '/home/x/A.sol'); never escape src/."""
    parts = [p for p in Path(name.replace("\\", "/")).parts if p not in ("", ".", "..", "/") and not p.endswith(":")]
    return Path(*parts) if parts else Path("Contract.sol")


REFERENCE_HOSTS = ("wikipedia.org", "coindesk.com", "blog.ethereum.org", "ethereum.org", "x.com", "twitter.com",
                   "medium.com", "reddit.com", "github.com", "github.io", "etherscan.io", "ethereumhistory.com",
                   "youtube.com", "youtu.be", "archive.org")


def host_of(url: str) -> str:
    """Lowercase host without 'www.' and port ('http://www.KingOfTheEther.com/x' -> 'kingoftheether.com')."""
    h = (urlparse(url if "://" in url else f"http://{url}").hostname or url).lower()
    return h[4:] if h.startswith("www.") else h


def is_reference(url: str) -> bool:
    """A link about the contract (encyclopedia, news, social, code host), not the dapp's own site."""
    h = host_of(url)
    return any(h == r or h.endswith("." + r) for r in REFERENCE_HOSTS)


def site_life(site: str) -> dict:
    """wayback.life() shape, from captures whose original URL's host is exactly the site's host."""
    want = host_of(site)
    caps = [c for c in wayback.captures(site) if host_of(c.get("url") or "") == want]
    ok = [c for c in caps if c["status"] == "200"]
    return {"host": site, "captures": len(caps),
            "first_capture": caps[0]["ts"] if caps else None, "first_ok": ok[0]["ts"] if ok else None,
            "last_ok": ok[-1]["ts"] if ok else None, "last_capture": caps[-1]["ts"] if caps else None,
            "years_alive": sorted({c["ts"][:4] for c in ok})}


def _iso_ts(s) -> float | None:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def chain_birth_time(f: dict) -> tuple[str | None, str | None]:
    """(timestamp, source) of the birth block from the chain: Blockscout's creation tx, else the archive RPC."""
    b = f.get("birth") or {}
    tx = b.get("tx") or (f.get("blockscout") or {}).get("creation_tx")
    if tx:
        t = blockscout.transaction(tx) or {}
        if t.get("timestamp"):
            return t["timestamp"], "blockscout"
    if b.get("block"):
        blk = rpc.block(int(b["block"])) or {}
        if blk.get("timestamp"):
            ts = int(blk["timestamp"], 16)
            return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rpc"
    return None, None


def fix_birth_time(f: dict) -> bool:
    """Prefer the chain's block time for birth.timestamp; keep Ethereum History's as birth.timestamp_eh when they differ."""
    b = f.get("birth")
    if not b or b.get("timestamp_source"):
        return False
    ts, src = chain_birth_time(f)
    if not ts:
        return False
    old = b.get("timestamp")
    a, c = _iso_ts(old), _iso_ts(ts)
    if old and a is not None and c is not None and abs(a - c) >= 1:
        b["timestamp_eh"] = old
        b["note"] = f"Ethereum History says {old}; the chain ({src}) says {ts} for block {b.get('block')}; the chain wins"
    b["timestamp"], b["timestamp_source"] = ts, src
    return True


def collect_sites(f: dict, given: list[str] | None) -> None:
    """Dapp sites: the caller's --site values plus Ethereum History links on non-reference hosts."""
    sites, excluded = list(given or []), []
    for l in (f.get("eh") or {}).get("links", []):
        u = l.get("url") or ""
        if u:
            (excluded if is_reference(u) else sites).append(u)
    f["sites"], f["sites_excluded"] = [], sorted(set(excluded))
    for s_ in dict.fromkeys(sites):
        try:
            f["sites"].append(site_life(s_))
        except Exception as ex:
            f["sites"].append({"host": s_, "error": str(ex)[:200]})


def is_creation(t: dict, f: dict) -> bool:
    """The deployment itself, which Blockscout lists among the txs 'to' the contract. It is not a call."""
    bt = ((f.get("birth") or {}).get("tx") or (f.get("blockscout") or {}).get("creation_tx") or "").lower()
    if bt and (t.get("hash") or "").lower() == bt:
        return True
    cc = ((t.get("created_contract") or {}).get("hash") or "").lower()
    return t.get("to") is None and cc == (f.get("address") or "").lower()


def _tx_brief(t: dict | None) -> dict | None:
    return {"timestamp": t.get("timestamp"), "method": t.get("method"), "status": t.get("status"),
            "hash": t.get("hash")} if t else None


def set_calls(f: dict, counters: dict | None, page: dict) -> None:
    """life.tx_count / life.calls = calls to the contract (never the creation tx); last_tx = newest successful call or null.

    Blockscout's counters endpoint answers "0" for many contracts it has not counted, so a zero counter
    is checked against the tx list (paged up to 1,000 txs; calls_capped when the count is a floor)."""
    life = f["life"]
    addr = f["address"]
    skip = lambda t: is_creation(t, f)
    items = page.get("items") or []
    more = bool(page.get("next_page_params"))
    calls = [t for t in items if not skip(t)]
    ok = [t for t in calls if t.get("status") == "ok"]
    counter = int((counters or {}).get("transactions_count") or 0)
    newest_ok, capped = (ok[0] if ok else None), False
    if counter > 0:
        n, src = counter, "blockscout-counters"
    elif not more:
        n, src = len(calls), "blockscout-txlist"
    else:
        r = blockscout.count_calls(addr, skip=skip)
        n, src, capped, newest_ok = r["calls"], "blockscout-txlist", r["capped"], newest_ok or r["newest_ok"]
    life["tx_count"] = life["calls"] = n
    life["calls_source"], life["calls_capped"] = src, capped
    life["last_tx"] = _tx_brief(newest_ok)
    life["never_called"] = n == 0
    life["recent_methods"] = sorted({t.get("method") for t in calls if t.get("method")})
    life["recent_years"] = sorted({(t.get("timestamp") or "")[:4] for t in calls if t.get("timestamp")})
    if n == 0:
        life["first_call_timestamp"] = None
    elif not more:
        life["first_call_timestamp"] = calls[-1].get("timestamp")
    else:
        life["first_call_timestamp"] = (blockscout.first_transaction(addr, skip=skip) or {}).get("timestamp")


def add_activity(f: dict, now: float | None = None) -> bool:
    """Lane A keys: life.last_12m_txs, life.last_12m_capped, life.first_tx_timestamp. Returns True if added."""
    life = f.get("life")
    if life is None or ("last_12m_txs" in life and "first_tx_timestamp" in life):
        return False
    addr = f["address"]
    if "last_12m_txs" not in life:
        r = blockscout.recent_activity(addr, now=now, skip=lambda t: is_creation(t, f))
        life["last_12m_txs"], life["last_12m_capped"] = r["ok"], r["capped"]
    if "first_tx_timestamp" not in life:
        t = blockscout.first_transaction(addr) or {}
        life["first_tx_timestamp"] = t.get("timestamp") or (f.get("birth") or {}).get("timestamp")
    return True


def upgrade(f: dict) -> bool:
    """Bring an older facts.json up to the current contract without refetching everything."""
    changed = False
    b = f.get("blockscout")
    if b is not None and b.get("name") != clean_name(b.get("name")):
        b["name"] = clean_name(b.get("name"))
        changed = True
    changed = set_names(f) or changed
    life = f.get("life")
    if life is not None and "calls_source" not in life:  # calls vs transactions (creation tx is not a call)
        try:
            set_calls(f, blockscout.counters(f["address"]), blockscout.newest_page(f["address"]))
            life.pop("last_12m_txs", None)  # recount without the creation tx
            changed = True
        except Exception:
            pass
    try:
        changed = add_activity(f) or changed
    except Exception:  # offline: keep what we have; the next load retries
        pass
    try:
        changed = fix_birth_time(f) or changed
    except Exception:
        pass
    if "sites_excluded" not in f:  # sites from before the reference-host and exact-host rules
        given = [s.get("host") for s in f.get("sites") or [] if s.get("host") and not is_reference(s["host"])]
        eh_urls = {l.get("url") for l in (f.get("eh") or {}).get("links", [])}
        try:
            collect_sites(f, [h for h in given if h not in eh_urls])
            changed = True
        except Exception:
            pass
    return changed


def ghost_dir(address: str) -> Path:
    d = config.GHOSTS_DIR / address.lower()
    d.mkdir(parents=True, exist_ok=True)
    return d


def summon(address: str, sites: list[str] | None = None, force: bool = False) -> dict:
    address = address.lower()
    out = ghost_dir(address) / "facts.json"
    if out.exists() and not force:
        f = json.loads(out.read_text())
        if upgrade(f):
            out.write_text(json.dumps(f, indent=1))
        return f
    used = []
    f: dict = {"address": address, "chain_id": 1, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # Ethereum History: birth, body, story
    e = eh.contract(address)
    if e:
        used.append("ethereumhistory")
        era = e.get("era") or {}
        f["eh"] = {
            "layer": e.get("layer"), "era_id": e.get("era_id"), "era_name": era.get("name"),
            "name": e.get("etherscan_contract_name") or e.get("token_name"),
            "token": {k: e.get(k) for k in ("token_name", "token_symbol", "token_decimals")},
            "heuristics": e.get("heuristics"), "decompilation_success": e.get("decompilation_success"),
            "code_size_bytes": e.get("code_size_bytes"),
            "short_description": e.get("short_description"), "description": e.get("description"),
            "historical_significance": e.get("historical_significance"), "historical_context": e.get("historical_context"),
            "verification_status": e.get("verification_status"), "verification_method": e.get("verification_method"),
            "links": e.get("links") or [], "metadata": e.get("metadata") or [],
            "has_source": bool(e.get("source_code")), "has_abi": bool(e.get("abi")),
        }
        f["birth"] = {"block": e.get("deployment_block"), "timestamp": e.get("deployment_timestamp"),
                      "tx": e.get("deployment_tx_hash"), "deployer": e.get("deployer_address")}
        gd = ghost_dir(address)
        if e.get("decompiled_code"):
            (gd / "decompiled.txt").write_text(e["decompiled_code"])
        if e.get("source_code"):
            (gd / "source.eh.sol").write_text(e["source_code"])
        if e.get("abi"):
            (gd / "abi.eh.json").write_text(e["abi"] if isinstance(e["abi"], str) else json.dumps(e["abi"]))

    # Blockscout: name, verification, balance, creation, activity
    b = blockscout.address(address)
    if b:
        used.append("blockscout")
        f["blockscout"] = {"name": clean_name(b.get("name")), "is_contract": b.get("is_contract"), "is_verified": b.get("is_verified"),
                           "ens": b.get("ens_domain_name"), "creation_tx": b.get("creation_transaction_hash"),
                           "creator": b.get("creator_address_hash"), "has_logs": b.get("has_logs")}
        if "birth" not in f and b.get("creation_transaction_hash"):
            t = blockscout.transaction(b["creation_transaction_hash"]) or {}
            f["birth"] = {"block": t.get("block_number") or t.get("block"), "timestamp": t.get("timestamp"),
                          "tx": b["creation_transaction_hash"], "deployer": b.get("creator_address_hash")}
        c = blockscout.counters(address) or {}
        f["life"] = {
            "token_transfers": int(c.get("token_transfers_count") or 0),
            "gas_used": int(c.get("gas_usage_count") or 0),
            "balance_wei": int(b.get("coin_balance") or 0),
        }
        f["life"]["balance_eth"] = round(f["life"]["balance_wei"] / WEI, 6)
        set_calls(f, c, blockscout.newest_page(address))
        try:
            add_activity(f)
        except Exception as ex:
            f["life"]["activity_error"] = str(ex)[:200]

    # RPC: is the body still there, and what does the chain say the balance is now
    try:
        code = rpc.get_code(address)
        f["chain"] = {"code_present": code not in ("0x", "0x0", None), "code_bytes": max(0, (len(code) - 2) // 2),
                      "balance_wei": rpc.get_balance_wei(address)}
        f["chain"]["balance_eth"] = round(f["chain"]["balance_wei"] / WEI, 6)
        used.append("rpc")
    except Exception as ex:  # keep going; the facts say what is missing
        f["chain"] = {"error": str(ex)[:200]}

    # Sourcify: verified source
    s = sourcify.verified(address)
    if s:
        used.append("sourcify")
        gd = ghost_dir(address) / "src"
        gd.mkdir(exist_ok=True)
        for name, content in s["sources"].items():
            p = gd / safe_relpath(name)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content or "")
        f["source"] = {"provider": "sourcify", "match": s["match"], "name": s["name"],
                       "compiler_version": s["compiler_version"], "language": s["language"],
                       "files": sorted(safe_relpath(n).as_posix() for n in s["sources"]), "dir": str(gd)}
        if s.get("abi"):
            (ghost_dir(address) / "abi.json").write_text(json.dumps(s["abi"]))
    elif b and b.get("is_verified"):
        sc = blockscout.smart_contract(address) or {}
        if sc.get("source_code"):
            gd = ghost_dir(address) / "src"
            gd.mkdir(exist_ok=True)
            (gd / f"{sc.get('name') or 'Contract'}.sol").write_text(sc["source_code"])
            f["source"] = {"provider": "blockscout", "match": "verified", "name": sc.get("name"),
                           "compiler_version": sc.get("compiler_version"), "language": sc.get("language"),
                           "files": [f"{sc.get('name') or 'Contract'}.sol"], "dir": str(gd)}
            if sc.get("abi"):
                (ghost_dir(address) / "abi.json").write_text(json.dumps(sc["abi"]))

    try:
        fix_birth_time(f)
    except Exception as ex:
        (f.get("birth") or {}).setdefault("note", f"chain birth time unavailable: {str(ex)[:120]}")

    # Age by hard fork, from the birth block
    blk = (f.get("birth") or {}).get("block")
    if blk:
        f["age"] = {"hardfork": age_of(int(blk)), "eh_era": (f.get("eh") or {}).get("era_name")}

    # The face: sites, from the caller or from Ethereum History links
    collect_sites(f, sites)
    if any("error" not in s_ for s_ in f["sites"]):
        used.append("wayback")

    set_names(f)
    f["sources_used"] = sorted(set(used))
    out.write_text(json.dumps(f, indent=1))
    return f
