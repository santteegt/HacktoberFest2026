"""Lane A: activity thresholds and the facts.py fixes (offline)."""
import copy, json
from pathlib import Path
import pytest
from ghosts import activity as A
from ghosts import facts as F
from ghosts.sources import blockscout as B

FX = Path(__file__).parent / "fixtures" / "a"
KOTE, DAO, RUBIXI, SB = ("0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0", "0xbb9bc244d798123fde783fcc1c72d3bb8c189413",
                         "0xe82719202e5965cf5d9b6673b7503a3b92de20be", "0x2af47a65da8cd66729b4209c22017d6a5c2d2400")
NOW = A.parse_ts("2026-10-29T05:00:00Z")


def facts(addr):
    return json.loads((FX / addr / "facts.json").read_text())


def test_parse_ts_iso_and_wayback():
    assert A.parse_ts("2016-02-19T21:51:14.000000Z") == A.parse_ts("20160219215114")
    assert A.parse_ts(None) is None and A.parse_ts("garbage") is None
    assert A.iso(A.parse_ts("2016-02-19T21:51:14.000000Z")) == "2016-02-19T21:51:14Z"


def test_silent_years_kote():
    assert A.silent_years(facts(KOTE), NOW) == pytest.approx(10.69, abs=0.01)


@pytest.mark.parametrize("k12,lifetime,alive", [(99, 100000, False), (100, 100000, True), (4, 100, False),
                                                (5, 100, True), (0, 0, False), (0, 10, False)])
def test_alive_threshold(k12, lifetime, alive):
    f = {"life": {"tx_count": lifetime, "last_12m_txs": k12}}
    assert A.is_alive(f) is alive


def test_long_silent_two_years():
    f = {"life": {"tx_count": 3, "last_12m_txs": 0, "last_tx": {"timestamp": "2024-10-30T05:00:00Z"}}}
    assert not A.is_long_silent(f, NOW)          # 1.99 years
    f["life"]["last_tx"]["timestamp"] = "2024-10-27T05:00:00Z"
    assert A.is_long_silent(f, NOW)              # 2.0+ years


def test_site_dead():
    assert A.site_dead({"sites": []}, NOW)
    assert A.site_dead({"sites": [{"host": "x", "last_ok": "20231001000000"}]}, NOW)
    assert not A.site_dead({"sites": [{"host": "x", "last_ok": "20251001000000"}]}, NOW)
    assert A.site_dead({"sites": [{"host": "x", "error": "timeout"}]}, NOW)


def test_clean_name_and_pick_name_thedao():
    assert F.clean_name("\u0001") is None and F.clean_name("  ") is None and F.clean_name(" Rubixi ") == "Rubixi"
    f = facts(DAO)
    f["name"], f["blockscout"]["name"] = "\u0001", "\u0001"
    assert F.pick_name(f) == "TheDAO"
    f["eh"]["name"] = ""
    assert F.pick_name(f) == "The DAO"           # falls through to the token name
    f["eh"]["token"]["token_name"] = None
    assert F.pick_name(f) == DAO


def test_safe_relpath_keeps_dirs():
    assert F.safe_relpath("contracts/lib/A.sol").as_posix() == "contracts/lib/A.sol"
    assert F.safe_relpath("/home/x/../A.sol").as_posix() == "home/x/A.sol"
    assert F.safe_relpath("../../etc/passwd").as_posix() == "etc/passwd"


def _pages(n_pages, ts_of):
    """Fake Blockscout pages: page i has 50 txs with timestamps ts_of(i, j)."""
    calls = []

    def get_json(url, params=None, **kw):
        i = int((params or {}).get("page", 0))
        calls.append(i)
        items = [{"timestamp": ts_of(i, j), "status": "ok" if j % 10 else "error"} for j in range(50)]
        return {"items": items, "next_page_params": {"page": i + 1} if i + 1 < n_pages else None}
    return get_json, calls


def test_recent_activity_stops_at_window(monkeypatch):
    # page 0 recent, page 1 half old
    fake, calls = _pages(5, lambda i, j: "2026-06-01T00:00:00Z" if (i == 0 or j < 25) else "2024-01-01T00:00:00Z")
    monkeypatch.setattr(B, "get_json", fake)
    r = B.recent_activity("0xabc", now=NOW)
    assert calls == [0, 1] and r["seen"] == 75 and r["ok"] == 45 + 22 and not r["capped"]


def test_recent_activity_caps_at_ten_pages(monkeypatch):
    fake, calls = _pages(50, lambda i, j: "2026-10-01T00:00:00Z")
    monkeypatch.setattr(B, "get_json", fake)
    r = B.recent_activity("0xabc", now=NOW)
    assert len(calls) == 10 and r["seen"] == 500 and r["capped"]


def test_upgrade_adds_keys_without_renaming(monkeypatch):
    f = facts(DAO)
    for k in ("last_12m_txs", "last_12m_capped", "first_tx_timestamp"):
        f["life"].pop(k, None)
    f["name"], f["blockscout"]["name"] = "\u0001", "\u0001"
    keys = set(f) | {"life"}
    monkeypatch.setattr(B, "recent_activity", lambda a, now=None, **kw: {"ok": 7, "seen": 9, "pages": 1, "capped": False})
    monkeypatch.setattr(B, "first_transaction", lambda a, **kw: {"timestamp": "2016-04-30T01:42:58.000000Z"})
    monkeypatch.setattr(B, "transaction", lambda h: {"timestamp": "2016-04-30T01:42:58.000000Z"})
    assert F.upgrade(f)
    assert keys <= set(f) and f["name"] == "TheDAO" and f["blockscout"]["name"] is None
    assert f["life"]["last_12m_txs"] == 7 and f["life"]["last_12m_capped"] is False
    assert f["life"]["first_tx_timestamp"].startswith("2016-04-30")
    assert not F.upgrade(f)


def test_reference_hosts_and_host_of():
    assert F.host_of("http://www.KingOfTheEther.com/postmortem.html") == "kingoftheether.com"
    assert F.host_of("bounties.network") == "bounties.network"
    for u in ("https://en.wikipedia.org/wiki/The_DAO", "https://x.com/avsa/status/1", "https://blog.ethereum.org/x",
              "https://github.com/a/b", "https://medium.com/p", "https://www.reddit.com/r/ethereum", "https://youtube.com/w"):
        assert F.is_reference(u), u
    assert not F.is_reference("http://www.kingoftheether.com/postmortem.html")
    assert not F.is_reference("https://bounties.network")


def test_collect_sites_drops_reference_links_and_foreign_hosts(monkeypatch):
    f = facts(DAO)
    f["eh"]["links"].append({"url": "http://www.thedao.example/"})
    monkeypatch.setattr(F.wayback, "captures", lambda site: [
        {"ts": "19961219022100", "status": "200", "mime": "text/html", "url": "http://other.example/"},
        {"ts": "20160501000000", "status": "200", "mime": "text/html", "url": "http://thedao.example/"},
        {"ts": "20170501000000", "status": "404", "mime": "text/html", "url": "https://www.thedao.example:443/"}])
    F.collect_sites(f, ["https://daohub.example"])
    hosts = [s["host"] for s in f["sites"]]
    assert hosts == ["https://daohub.example", "http://www.thedao.example/"]
    s = f["sites"][1]
    assert s["captures"] == 2 and s["first_ok"] == "20160501000000" and s["years_alive"] == ["2016"]
    assert "https://en.wikipedia.org/wiki/The_DAO" in f["sites_excluded"]
    assert len(f["eh"]["links"]) == 9                    # eh.links untouched


def test_fix_birth_time_prefers_chain(monkeypatch):
    f = facts(DAO)
    f["birth"] = {"block": 1428757, "timestamp": "2016-04-30T05:42:58.000Z", "tx": "0xe9eb"}
    monkeypatch.setattr(B, "transaction", lambda h: {"timestamp": "2016-04-30T01:42:58.000000Z"})
    assert F.fix_birth_time(f)
    b = f["birth"]
    assert b["timestamp"].startswith("2016-04-30T01:42:58") and b["timestamp_eh"] == "2016-04-30T05:42:58.000Z"
    assert b["timestamp_source"] == "blockscout" and "chain wins" in b["note"]
    assert not F.fix_birth_time(f)                      # idempotent


def test_fix_birth_time_rpc_fallback_and_equal(monkeypatch):
    f = {"birth": {"block": 963186, "timestamp": "2016-02-06T16:12:18.000Z", "tx": None}, "blockscout": {}}
    monkeypatch.setattr(F.rpc, "block", lambda n, full=False: {"timestamp": hex(1454775138)})
    assert F.fix_birth_time(f)
    assert f["birth"]["timestamp"] == "2016-02-06T16:12:18Z" and f["birth"]["timestamp_source"] == "rpc"
    assert "timestamp_eh" not in f["birth"] and "note" not in f["birth"]


def test_fixture_birth_and_sites():
    assert facts(DAO)["birth"]["timestamp_eh"] == "2016-04-30T05:42:58.000Z"
    assert facts(DAO)["sites"] == [] and facts(KOTE)["sites"][0]["host"].startswith("http://www.kingoftheether.com")
