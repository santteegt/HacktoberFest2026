import random
import pytest
from ghosts import pick as P


def row(addr, doc, ts="2016-03-01T00:00:00.000Z"):
    return {"address": addr, "has_short_description": doc, "deployment_timestamp": ts, "era_id": "homestead",
            "etherscan_contract_name": "N" + addr[-2:], "token_name": None, "verification_method": None}


def test_choose_documented_only_and_deterministic():
    rows = [row("0xa1", False), row("0xb2", True), row("0xc3", True), row("0xd4", False)]
    a = P.choose_documented(rows, random.Random("2026-10-29"))
    b = P.choose_documented(list(reversed(rows)), random.Random("2026-10-29"))
    assert a == b and a["has_short_description"]
    assert P.choose_documented([row("0xa1", False)], random.Random(1)) is None


def test_daily_seed_is_the_utc_date(monkeypatch):
    monkeypatch.setattr(P, "utc_date", lambda: "2026-10-29")
    assert P.make_rng("daily", "x").random() == P.make_rng("2026-10-29", "x").random()
    assert P.make_rng("daily", "x").random() != P.make_rng("2026-10-30", "x").random()


def test_pick_archive_uses_windows_until_documented(monkeypatch):
    calls = []

    def fake_discover(**params):
        calls.append(params)
        return [row("0xa1", False)] if len(calls) < 3 else [row("0xa1", False), row("0xbeef", True)]

    monkeypatch.setattr(P.eh, "discover", fake_discover)
    r = P.pick("archive", 2016, "daily")
    assert r["address"] == "0xbeef" and r["source"] == "archive" and r["year"] == 2016
    assert r["extra"]["windows_tried"] == 3 and calls[0]["from_timestamp"].startswith("2016-")
    assert set(r) == {"address", "source", "reason", "name", "year", "extra"}


def test_pick_archive_falls_back_to_featured(monkeypatch):
    def fake(**params):
        return [row("0xfeed", True, "2016-01-01T00:00:00.000Z")] if params.get("featured") else [row("0xa1", False)]
    monkeypatch.setattr(P.eh, "discover", fake)
    r = P.pick("archive", 2016, "s")
    assert r["address"] == "0xfeed" and r["extra"]["method"] == "featured fallback"


def inc(name, primary, verified=None, date="2022-05-01"):
    e = {"date": date, "name": name, "cause": "Reentrancy", "loss_usd": 1000, "primary": primary}
    if verified is not None:
        e["primary_verified"], e["primary_name"] = verified, ("V" + name if verified else None)
    return e


def test_choose_incident_skips_unverified_and_uses_blockscout():
    entries = [inc("A", "0xaa", False), inc("B", "0xbb"), inc("C", None), inc("D", "0xdd")]
    seen = []

    def check(a):
        seen.append(a)
        return {"name": "Checked" + a} if a == "0xdd" else None

    for seed in range(10):
        e, addr, name = P.choose_incident(entries, random.Random(seed), check)
        assert addr == "0xdd" and name == "Checked0xdd"
    assert "0xaa" not in seen  # already marked unverified... never offered as verified
    e2, addr2, name2 = P.choose_incident([inc("A", "0xaa", True)], random.Random(0), lambda a: pytest.fail("no network"))
    assert (addr2, name2) == ("0xaa", "VA")


def test_pick_incident_shape(monkeypatch):
    monkeypatch.setattr(P.inc, "load", lambda y: [inc("Visor", "0xaa", True, f"{y}-03-03")])
    r = P.pick("incident", 2021, "seed")
    assert r["address"] == "0xaa" and r["year"] == 2021 and r["name"] == "VVisor"
    assert r["extra"]["incident"]["name"] == "Visor" and "Reentrancy" in r["reason"]


def test_creations_and_random_picker_counts_blocks(monkeypatch):
    blocks = {}

    def fake_block(n, full=False):
        if n % 2:
            return {"transactions": [{"hash": f"0xh{n}", "to": None, "from": "0xdep"}, {"hash": "0xother", "to": "0x1"}]}
        return {"transactions": [{"hash": "0xnone", "to": "0x1"}]}

    monkeypatch.setattr(P.rpc, "block", fake_block)
    monkeypatch.setattr(P.rpc, "receipt", lambda h: {"contractAddress": "0xc" + h[3:], "status": "0x1"})
    verified_after = {"n": 0}

    def fake_ver(a):
        verified_after["n"] += 1
        return {"name": "Named"} if verified_after["n"] >= 3 else None

    monkeypatch.setattr(P, "is_verified_named", fake_ver)
    r = P.pick("random", 2019, "s")
    assert r["name"] == "Named" and r["extra"]["blocks_tried"] >= 3
    lo, hi = P.block_range(2019)
    assert lo <= r["extra"]["block"] <= hi
    monkeypatch.setattr(P, "is_verified_named", lambda a: None)
    with pytest.raises(LookupError):
        P.pick_random(2019, "s", max_blocks=5)


def test_year_ranges_cover_years_without_overlap():
    prev = 0
    for y in range(2015, 2024):
        lo, hi = P.block_range(y)
        assert lo > prev and hi > lo
        prev = hi
    with pytest.raises(ValueError):
        P.pick("random", 2025, None)
