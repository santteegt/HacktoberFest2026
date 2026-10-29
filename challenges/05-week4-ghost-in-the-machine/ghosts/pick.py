"""Three ways to find a ghost, 2015-2023. A pick never summons: it only names an address and says why.

    pick("archive",  year, seed)   a documented Ethereum History contract (historian story exists)
    pick("incident", year, seed)   a DeFiHackLabs incident whose primary victim is a verified contract
    pick("random",   year, seed)   a verified, named contract found by sampling random blocks (dRPC)

`seed`: None = truly random; "daily" = the UTC date (deterministic daily choice); anything else = that string.
Returns {"address", "source", "reason", "name", "year", "extra"}.
"""
from __future__ import annotations
import datetime as dt, json, random
import typer
from .sources import eh, blockscout, rpc
from . import incidents as inc

SOURCES = ("archive", "incident", "random")
DOCUMENTED_YEARS = (2015, 2016, 2017)   # where the historians wrote most of their stories
ARCHIVE_WINDOWS = 10                     # EH windows (200 rows each, 3.2 s apart) tried before the fallback
RANDOM_MAX_BLOCKS = 120

# first block of each UTC year, checked against dRPC block timestamps on 2026-10-29 (end of 2023 kept inside the year)
YEAR_START_BLOCK = {2015: 1, 2016: 778_483, 2017: 2_912_407, 2018: 4_832_686, 2019: 6_988_615,
                    2020: 9_193_266, 2021: 11_565_019, 2022: 13_916_166, 2023: 16_308_190}
YEAR_END_BLOCK = {**{y: YEAR_START_BLOCK[y + 1] - 1 for y in range(2015, 2023)}, 2023: 18_908_300}


def utc_date() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def make_rng(seed: str | None, salt: str = "") -> random.Random:
    if seed is None:
        return random.Random()
    s = utc_date() if seed == "daily" else seed
    return random.Random(f"{s}|{salt}")


def _result(address: str, source: str, reason: str, name: str | None, year: int | None, extra: dict) -> dict:
    return {"address": address.lower(), "source": source, "reason": reason, "name": name, "year": year, "extra": extra}


# ----------------------------------------------------------------------------- archive


def choose_documented(rows: list[dict], rng: random.Random) -> dict | None:
    """Pure: one of the rows that carry a short description (the historians wrote about it)."""
    docs = sorted((r for r in rows if r.get("has_short_description")), key=lambda r: r["address"])
    return rng.choice(docs) if docs else None


def _window(year: int, rng: random.Random) -> dict:
    start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
    secs = int(rng.random() * 364 * 86400)
    frm = start + dt.timedelta(seconds=secs)
    return {"from_timestamp": frm.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to_timestamp": f"{year}-12-31T23:59:59Z", "limit": 200}


def pick_archive(year: int | None = None, seed: str | None = None) -> dict:
    rng = make_rng(seed, f"archive|{year}")
    y = year or rng.choice(DOCUMENTED_YEARS)
    tried = []
    for i in range(ARCHIVE_WINDOWS):
        params = _window(y, rng)
        rows = eh.discover(**params)
        tried.append(params["from_timestamp"])
        row = choose_documented(rows, rng)
        if row:
            name = row.get("etherscan_contract_name") or row.get("token_name")
            return _result(row["address"], "archive",
                           f"documented on Ethereum History (deployed {row['deployment_timestamp'][:10]}, era {row.get('era_id')})",
                           name, int(row["deployment_timestamp"][:4]),
                           {"era_id": row.get("era_id"), "verification_method": row.get("verification_method"),
                            "token_name": row.get("token_name"), "deployed": row["deployment_timestamp"],
                            "windows_tried": len(tried), "rows_in_window": len(rows), "method": "random window + has_short_description"})
    # fallback: the featured set (13 rows when checked), restricted to the year when one was asked for
    rows = eh.discover(featured="true", limit=200)
    if year:
        rows = [r for r in rows if r["deployment_timestamp"].startswith(str(year))]
    row = choose_documented(rows, rng)
    if not row:
        raise LookupError(f"no documented contract found for year {year} after {len(tried)} windows")
    return _result(row["address"], "archive", "featured on Ethereum History (fallback: no documented row in the sampled windows)",
                   row.get("etherscan_contract_name") or row.get("token_name"), int(row["deployment_timestamp"][:4]),
                   {"era_id": row.get("era_id"), "windows_tried": len(tried), "method": "featured fallback"})


# ----------------------------------------------------------------------------- incident


def is_verified_named(address: str) -> dict | None:
    """Blockscout says: a contract, verified, with a name. Returns the answer row or None."""
    b = blockscout.address(address)
    if b and b.get("is_contract") and b.get("is_verified") and b.get("name"):
        return b
    return None


def choose_incident(entries: list[dict], rng: random.Random, check=is_verified_named) -> tuple[dict, str, str] | None:
    """Pure-ish: shuffle entries, return (entry, address, name) for the first whose primary victim `check` accepts.
    Entries marked primary_verified True skip the network call; False are skipped."""
    order = sorted(entries, key=lambda e: (e["date"], e["name"]))
    rng.shuffle(order)
    for e in order:
        a = e.get("primary")
        if not a or e.get("primary_verified") is False:  # False: verify_primary already asked Blockscout
            continue
        if e.get("primary_verified") is True and e.get("primary_name"):
            return e, a, e["primary_name"]
        b = check(a)
        if b:
            return e, a, b["name"]
    return None


def pick_incident(year: int | None = None, seed: str | None = None) -> dict:
    years = [year] if year else list(inc.ALL_YEARS)
    entries = [dict(e, year=y) for y in years for e in inc.load(y)]
    if not entries:
        raise LookupError(f"no incidents on disk for {years}: run `ghosts incidents fetch`")
    rng = make_rng(seed, f"incident|{year}")
    got = choose_incident(entries, rng)
    if not got:
        raise LookupError("no incident with a verified primary victim")
    e, a, name = got
    loss = f", about ${e['loss_usd']:,} lost" if e.get("loss_usd") else ""
    return _result(a, "incident", f"victim of {e['name']} ({e['date']}): {e.get('cause') or 'cause not stated'}{loss}",
                   name, int(e["date"][:4]),
                   {"incident": {k: e.get(k) for k in ("name", "date", "cause", "loss_usd", "loss_text", "poc_url", "references",
                                                       "victim_addresses", "primary", "source", "page")}})


# ----------------------------------------------------------------------------- random blocks


def creations_in_block(number: int) -> list[dict]:
    """[{tx, address, from}] for every contract creation in the block (tx.to is null)."""
    blk = rpc.block(number, True)
    out = []
    for t in (blk or {}).get("transactions", []):
        if isinstance(t, dict) and t.get("to") is None:
            r = rpc.receipt(t["hash"])
            if r and r.get("contractAddress") and r.get("status") in ("0x1", None):
                out.append({"tx": t["hash"], "address": r["contractAddress"], "from": t.get("from")})
    return out


def block_range(year: int) -> tuple[int, int]:
    if year not in YEAR_START_BLOCK:
        raise ValueError(f"random picker covers 2015-2023, not {year}")
    return YEAR_START_BLOCK[year], YEAR_END_BLOCK[year]


def pick_random(year: int | None = None, seed: str | None = None, max_blocks: int = RANDOM_MAX_BLOCKS) -> dict:
    rng = make_rng(seed, f"random|{year}")
    y = year or rng.choice(sorted(YEAR_START_BLOCK)[1:])  # 2016-2023; 2015 is the archive's territory
    lo, hi = block_range(y)
    tried, errors, creations = 0, 0, 0
    last_err = None
    while tried < max_blocks:
        n = rng.randint(lo, hi)
        tried += 1
        try:
            found = creations_in_block(n)
        except Exception as ex:  # a pruned or rate-limited block counts as tried
            errors, last_err = errors + 1, str(ex)[:160]
            continue
        creations += len(found)
        for c in found:
            b = is_verified_named(c["address"])
            if b:
                return _result(c["address"], "random", f"verified contract created in block {n} ({y}), found after {tried} random blocks",
                               b["name"], y, {"block": n, "tx": c["tx"], "deployer": c["from"], "blocks_tried": tried,
                                              "creations_seen": creations, "rpc_errors": errors, "method": "random block sampler (dRPC) + Blockscout"})
    raise LookupError(f"no verified named contract in {tried} random blocks of {y} ({creations} creations seen, "
                      f"{errors} rpc errors, last: {last_err})")


# ----------------------------------------------------------------------------- front doors


def pick(source: str, year: int | None = None, seed: str | None = None) -> dict:
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}")
    if year is not None and not 2015 <= year <= 2023:
        raise ValueError("year must be within 2015-2023")
    return {"archive": pick_archive, "incident": pick_incident, "random": pick_random}[source](year, seed)


def pick_address(source: str, year: int | None = None, seed: str | None = None) -> str:
    """Dry run: just the address (nothing is summoned or written)."""
    return pick(source, year, seed)["address"]


def pick_many(source: str, n: int, year: int | None = None, seed: str | None = None) -> list[dict]:
    """n distinct picks. With a seed, pick i uses `<seed>#i` (and a few more tries on duplicates)."""
    out, seen, i = [], set(), 0
    while len(out) < n and i < n * 4:
        s = None if seed is None else f"{seed}#{i}"
        i += 1
        try:
            p = pick(source, year, s)
        except LookupError:
            continue
        if p["address"] not in seen:
            seen.add(p["address"])
            out.append(p)
    return out


# ----------------------------------------------------------------------------- CLI (wired by the coordinator)


def pick_cmd(
    source: str = typer.Option("archive", "--source", "-s", help="archive | incident | random"),
    year: int = typer.Option(None, "--year", "-y", help="2015-2023"),
    seed: str = typer.Option(None, "--seed", help="'daily' = UTC date; any string = deterministic; omit = random"),
    n: int = typer.Option(1, "--n", help="how many distinct picks"),
    max_blocks: int = typer.Option(RANDOM_MAX_BLOCKS, "--max-blocks", help="random source: blocks to sample before giving up"),
    dry_run: bool = typer.Option(False, "--dry-run", help="print only the address(es); summon nothing"),
):
    """Find a ghost: names an address and says why. Never summons by itself."""
    try:
        if source == "random" and max_blocks != RANDOM_MAX_BLOCKS and n == 1:
            picks = [pick_random(year, seed, max_blocks)]
        else:
            picks = pick_many(source, n, year, seed) if n > 1 else [pick(source, year, seed)]
    except (LookupError, ValueError) as e:
        typer.echo(f"pick failed: {e}", err=True)
        raise typer.Exit(1)
    for p in picks:
        typer.echo(p["address"] if dry_run else json.dumps(p, indent=1))
