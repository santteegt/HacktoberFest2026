"""DeFiHackLabs incidents (2021-2023) parsed into data/incidents/<year>.json.

Each README entry looks like (the format drifts between years, the parser is tolerant):

    ### 20211221 Visor Finance - Reentrancy
    #### Lost: $8.2 million
    forge test --contracts ./src/test/2021-12/Visor_exp.sol -vv
    #### Contract
    [Visor_exp.sol](../../src/test/2021-12/Visor_exp.sol)
    #### Link reference
    https://...

The PoC `.sol` names the victim contracts as address constants or interface instances; we pull every
0x…40 address out of it. Nothing here is asserted by a model; a vulnerability is only "confirmed" later,
by Lane A, when a catalog entry (this file) documents the incident with a reference.
"""
from __future__ import annotations
import json, re
import typer
from pathlib import Path
from . import config
from .http import get_text
from .sources import blockscout

README_URL = "https://raw.githubusercontent.com/SunWeb3Sec/DeFiHackLabs/main/past/{year}/README.md"
RAW_BASE = "https://raw.githubusercontent.com/SunWeb3Sec/DeFiHackLabs/main/"
BLOB_BASE = "https://github.com/SunWeb3Sec/DeFiHackLabs/blob/main/"
INCIDENTS_DIR = config.DATA / "incidents"
YEARS = (2021, 2022, 2023)                    # pages fetched
ALL_YEARS = (2017, 2018, 2020, 2021, 2022, 2023)  # year files produced (the 2021 page also lists 2017, 2018, 2020)

_HEAD = re.compile(r"^### (\d{8}) (.+?)\s*$", re.M)
_ADDR = re.compile(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")
_URL = re.compile(r"https?://[^\s)<>\"']+")
_POC_LINK = re.compile(r"\]\((?:\.\./)*(src/test/[^)\s]+?\.sol)\)")
_POC_FORGE = re.compile(r"(?:\./)?(src/test/[\w\-./]+?\.sol)")

# Addresses that show up in nearly every PoC and are never "the victim": the Foundry cheatcode
# address, WETH, major stablecoins, WBTC, the big routers/factories/vaults. Everything else is kept.
WELL_KNOWN = {a.lower(): n for a, n in {
    "0x7109709ECfa91a80626fF3989D68f67F5b1DD12D": "foundry cheatcodes (HEVM)",
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": "DAI",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "WBTC",
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": "UNI",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": "LINK",
    "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84": "stETH",
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": "Uniswap V2 router",
    "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f": "Uniswap V2 factory",
    "0xE592427A0AEce92De3Edee1F18E0157C05861564": "Uniswap V3 router",
    "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45": "Uniswap V3 router 02",
    "0x1F98431c8aD98523631AE4a59f267346ea31F984": "Uniswap V3 factory",
    "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F": "SushiSwap router",
    "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac": "SushiSwap factory",
    "0xBA12222222228d8Ba445958a75a0704d566BF2C8": "Balancer vault",
    "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9": "Aave V2 pool",
    "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2": "Aave V3 pool",
    "0x000000000022D473030F116dDEE9F6B43aC78BA3": "Permit2",
    "0xcA11bde05977b3631167028862bE2a173976CA11": "Multicall3",
    "0x0000000000000000000000000000000000000000": "zero address",
    "0x000000000000000000000000000000000000dEaD": "dead address",
}.items()}

# createSelectFork("bsc"), createFork(vm.rpcUrl("polygon")) ... map alias -> canonical chain
_FORK = re.compile(r"(?:createSelectFork|createFork|rpcUrl|rpc_url)\s*\(\s*(?:vm\.rpcUrl\s*\(\s*)?\"([\w\-]+)\"", re.I)
_CHAIN_ALIAS = {"mainnet": "mainnet", "eth": "mainnet", "ethereum": "mainnet", "main": "mainnet",
                "bsc": "bsc", "binance": "bsc", "bnb": "bsc", "polygon": "polygon", "matic": "polygon",
                "arbitrum": "arbitrum", "arb": "arbitrum", "optimism": "optimism", "avalanche": "avalanche",
                "avax": "avalanche", "fantom": "fantom", "ftm": "fantom", "base": "base", "linea": "linea",
                "celo": "celo", "gnosis": "gnosis", "moonriver": "moonriver", "moonbeam": "moonbeam",
                "cronos": "cronos", "harmony": "harmony", "blast": "blast", "mantle": "mantle", "zksync": "zksync",
                "scroll": "scroll", "sepolia": "sepolia", "goerli": "goerli", "heco": "heco", "okc": "okc"}
_OTHER_EXPLORERS = ("bscscan.com", "polygonscan.com", "arbiscan.io", "optimistic.etherscan", "snowtrace.io",
                    "ftmscan.com", "basescan.org", "lineascan.build", "gnosisscan.io", "celoscan.io",
                    "/explorer/tx/bsc/", "/explorer/tx/polygon/", "/explorer/tx/arbitrum/", "/explorer/tx/optimism/",
                    "/explorer/tx/avalanche/", "/explorer/tx/fantom/", "/explorer/tx/base/", "bscscan")

# ----------------------------------------------------------------------------- parsing


def parse_loss(text: str | None) -> int | None:
    """USD figure from a 'Lost:' value. Only amounts tied to a dollar sign / US$ / USD / USDC / USDT / BUSD / DAI,
    or a bare number with K/M/B suffix (these pages write '365K', '11M'), count. '390 ETH' alone is null."""
    if not text:
        return None
    t = text.replace(" ", " ")
    mult = {"k": 1e3, "m": 1e6, "mm": 1e6, "b": 1e9, "thousand": 1e3, "million": 1e6, "billion": 1e9, "bn": 1e9}
    num = r"(\d[\d,\.]*|\.\d+)(?![\d,\.])\s*(thousand|million|billion|bn|mm|k|m|b)?\b"

    def val(n: str, suf: str | None) -> int | None:
        n = n.rstrip(".,")
        if n.startswith("."):
            n = "0" + n
        if "," in n and "." not in n and re.fullmatch(r"\d+,\d{1,2}", n):  # '1,24M' european decimal
            n = n.replace(",", ".")
        else:
            n = n.replace(",", "")
        try:
            v = float(n)
        except ValueError:
            return None
        return int(round(v * mult.get((suf or "").lower(), 1)))

    # explicit dollar forms first: "$8.2 million", "~$4.4K", "(~$30M)", "152M US$", "20M USD"
    coin = r"(?!\s*(?:ETH|BNB|WBNB|WETH|BTC|WBTC|MATIC|AVAX|CAKE)\b)"
    m = re.search(r"\$\s*" + num + coin, t, re.I)
    if m:
        return val(m.group(1), m.group(2))
    m = re.search(num + r"\s*(?:US\$|USD\b|\$)", t, re.I)
    if m:
        return val(m.group(1), m.group(2))
    m = re.search(num + r"\s*\$?\s*(?:USDT|USDC|BUSD|DAI|TUSD)\b", t, re.I)
    if m:
        return val(m.group(1), m.group(2))
    m = re.search(r"(?:USDT|USDC|BUSD|DAI)\s*" + num, t, re.I)
    if m:
        return val(m.group(1), m.group(2))
    # bare '365K' / '11M' / '~320K' / '76k' with a suffix and no other coin named
    if not re.search(r"\b(ETH|BNB|WBNB|WETH|BTC|MATIC|AVAX|CAKE|NFT|tokens?)\b", t, re.I):
        m = re.search(r"~?\s*(\d[\d,\.]*)\s*(thousand|million|billion|bn|mm|k|m|b)\b", t, re.I)
        if m:
            return val(m.group(1), m.group(2))
        m = re.fullmatch(r"\s*~?\s*\$?(\d[\d,]*)\s*", t, re.I)  # '$1450'
        if m:
            return val(m.group(1), None)
    return None


def _split_name_cause(title: str) -> tuple[str, str | None]:
    title = re.sub(r"^[\-\u2013:\s]+", "", title)
    if " - " in title:
        n, c = title.split(" - ", 1)
        return n.strip(), c.strip() or None
    return title.strip(), None


def parse_readme(text: str, year: int | None) -> list[dict]:
    """Entries of one DeFiHackLabs yearly page, in page order (newest first); year=None keeps every date. No network."""
    heads = list(_HEAD.finditer(text))
    out = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[h.end():end]
        d = h.group(1)
        name, cause = _split_name_cause(h.group(2))
        lm = re.search(r"^#{3,4}\s*Lost:?[ \t]*(.*)$", block, re.M | re.I)
        lost_text = (lm.group(1).strip() if lm else "") or None
        pocs = []
        for m in _POC_LINK.finditer(block):
            if m.group(1) not in pocs:
                pocs.append(m.group(1))
        if not pocs:
            for m in _POC_FORGE.finditer(block):
                if m.group(1) not in pocs:
                    pocs.append(m.group(1))
        ref_zone = block.split("Link reference", 1)[1] if "Link reference" in block else block
        refs = []
        for u in _URL.findall(ref_zone):
            u = u.rstrip(".,;")
            if u not in refs and "SunWeb3Sec" not in u:
                refs.append(u)
        out.append({
            "date": f"{d[:4]}-{d[4:6]}-{d[6:]}", "name": name, "cause": cause,
            "loss_usd": parse_loss(lost_text), "loss_text": lost_text,
            "poc_path": pocs[0] if pocs else None,
            "poc_url": (BLOB_BASE + pocs[0]) if pocs else None,
            "extra_pocs": [BLOB_BASE + p for p in pocs[1:]],
            "references": refs,
        })
    return [e for e in out if year is None or e["date"].startswith(str(year))]


def detect_chains(poc_source: str) -> list[str]:
    """Chains the PoC forks (canonical names). Empty list means the PoC names none."""
    found = []
    for m in _FORK.finditer(poc_source):
        c = _CHAIN_ALIAS.get(m.group(1).lower(), m.group(1).lower())
        if c not in found:
            found.append(c)
    return found


def parse_poc(source: str) -> dict:
    """victim_addresses (dedup, order of appearance, lowercase), primary (first non well-known), chains."""
    seen, addrs = set(), []
    for m in _ADDR.finditer(source):
        a = m.group(0).lower()
        if a not in seen:
            seen.add(a)
            addrs.append(a)
    cands = [a for a in addrs if a not in WELL_KNOWN]
    return {"victim_addresses": cands, "ignored_well_known": [a for a in addrs if a in WELL_KNOWN],
            "primary": cands[0] if cands else None, "chains": detect_chains(source)}


def keep_chain(chains: list[str], references: list[str]) -> bool:
    """Keep when the PoC forks mainnet (alone or with nothing else), or names no chain and the
    references do not point at another chain's explorer."""
    if chains:
        return set(chains) == {"mainnet"}
    return not any(x in u.lower() for u in references for x in _OTHER_EXPLORERS)


# ----------------------------------------------------------------------------- fetch


def fetch(year: int, *, write: bool = True, verify: bool = False) -> list[dict]:
    """Download (cached) the year page and every PoC, parse, keep mainnet-only entries.
    Writes data/incidents/<year>.json (kept) and <year>.dropped.json (date, name, why). The 2021 page also
    lists a few older incidents (2017, 2018, 2020); they are written to their own year files."""
    text = get_text(README_URL.format(year=year))
    if not text:
        raise RuntimeError(f"no DeFiHackLabs page for {year}")
    kept: dict[int, list[dict]] = {year: []}
    dropped: dict[int, list[dict]] = {year: []}
    for e in parse_readme(text, None):
        y = int(e["date"][:4])
        kept.setdefault(y, [])
        dropped.setdefault(y, [])
        if not e["poc_path"]:
            dropped[y].append({"date": e["date"], "name": e["name"], "why": "no PoC link"})
            continue
        src = get_text(RAW_BASE + e["poc_path"])
        if not src:
            dropped[y].append({"date": e["date"], "name": e["name"], "why": "PoC not found"})
            continue
        p = parse_poc(src)
        if not keep_chain(p["chains"], e["references"]):
            dropped[y].append({"date": e["date"], "name": e["name"], "why": "not mainnet", "chains": p["chains"]})
            continue
        e.update(p)
        e["chain"] = "mainnet" if p["chains"] else "unspecified"
        e["source"] = "DeFiHackLabs"
        e["page"] = BLOB_BASE + f"past/{year}/README.md"
        kept[y].append(e)
    if write:
        INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
        for y in kept:
            (INCIDENTS_DIR / f"{y}.json").write_text(json.dumps(kept[y], indent=1))
            (INCIDENTS_DIR / f"{y}.dropped.json").write_text(json.dumps(dropped[y], indent=1))
            if verify and kept[y]:
                verify_primary(y)
        if verify:
            return load(year)
    return kept[year]


def verify_primary(year: int, *, max_candidates: int = 3) -> dict:
    """Ask Blockscout whether an entry's primary victim is a verified contract. Tries up to `max_candidates`
    non-well-known addresses and promotes the first verified one to `primary`. Fills `primary_verified`
    and `primary_name` in data/incidents/<year>.json. Returns counts."""
    path = INCIDENTS_DIR / f"{year}.json"
    entries = json.loads(path.read_text())
    n_ok = 0
    for e in entries:
        e["primary_verified"], e["primary_name"] = False, None
        for a in (e.get("victim_addresses") or [])[:max_candidates]:
            b = blockscout.address(a)
            if b and b.get("is_contract") and b.get("is_verified") and b.get("name"):
                e["primary"], e["primary_verified"], e["primary_name"] = a, True, b["name"]
                break
        n_ok += e["primary_verified"]
    path.write_text(json.dumps(entries, indent=1))
    return {"year": year, "kept": len(entries), "verified_primary": n_ok}


def load(year: int) -> list[dict]:
    p = INCIDENTS_DIR / f"{year}.json"
    return json.loads(p.read_text()) if p.exists() else []


# ----------------------------------------------------------------------------- CLI (wired by the coordinator)

app = typer.Typer(help="DeFiHackLabs incidents 2021-2023 -> data/incidents/<year>.json")


@app.command("fetch")
def fetch_cmd(year: int = typer.Option(None, "--year", "-y", help="one year; omit for 2021, 2022 and 2023"),
              verify: bool = typer.Option(True, "--verify/--no-verify", help="ask Blockscout whether the primary victim is verified")):
    """Download and parse the incident pages (cached), keep mainnet-only entries."""
    for y in ([year] if year else list(YEARS)):
        kept = fetch(y, verify=verify)
        ok = sum(1 for e in kept if e.get("primary_verified"))
        typer.echo(f"{y}: kept {len(kept)} mainnet entries, {ok} with a verified primary victim -> data/incidents/{y}.json")
