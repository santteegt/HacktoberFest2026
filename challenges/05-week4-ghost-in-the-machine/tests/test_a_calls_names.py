"""Lane A follow-up 2: calls vs transactions, never-called ghosts, generic names (offline)."""
import json
from pathlib import Path
import pytest
from ghosts import activity as A
from ghosts import classify as C
from ghosts import facts as F
from ghosts.sources import blockscout as B

FX = Path(__file__).parent / "fixtures" / "a"
NOW = A.parse_ts("2026-10-29T05:00:00Z")


def extra(prefix):
    return json.loads(next((FX / "extra").glob(prefix + "*.json")).read_text())


def tx(h, ts, status="ok", method="m", to="0xc", created=None):
    return {"hash": h, "timestamp": ts, "status": status, "method": method,
            "to": {"hash": to} if to else None, "created_contract": {"hash": created} if created else None}


def base(addr="0xc"):
    return {"address": addr, "birth": {"tx": "0xbirth", "timestamp": "2016-09-07T00:00:00Z"}, "life": {}}


def test_creation_tx_is_not_a_call():
    f = base()
    assert F.is_creation(tx("0xBIRTH", "x"), f)
    assert F.is_creation(tx("0xother", "x", to=None, created="0xC"), f)
    assert not F.is_creation(tx("0xother", "x"), f)


def test_only_creation_means_never_called():
    f = base()
    F.set_calls(f, {"transactions_count": "0"}, {"items": [tx("0xbirth", "2016-09-07T00:00:00Z", to=None, created="0xc")],
                                                 "next_page_params": None})
    life = f["life"]
    assert life["tx_count"] == life["calls"] == 0 and life["never_called"] and life["last_tx"] is None
    assert life["recent_methods"] == [] and life["first_call_timestamp"] is None


def test_zero_counter_is_checked_against_the_list():
    f = base()
    items = [tx("0x2", "2019-07-31T10:00:00Z", method="transfer"), tx("0x1", "2019-07-31T09:00:00Z", status="error"),
             tx("0xbirth", "2019-07-31T08:00:00Z", to=None, created="0xc")]
    F.set_calls(f, {"transactions_count": "0"}, {"items": items, "next_page_params": None})
    life = f["life"]
    assert life["calls"] == 2 and life["calls_source"] == "blockscout-txlist" and not life["never_called"]
    assert life["last_tx"]["hash"] == "0x2" and life["first_call_timestamp"] == "2019-07-31T09:00:00Z"


def test_failed_calls_only_leave_last_tx_null():
    f = base()
    F.set_calls(f, {"transactions_count": "1"}, {"items": [tx("0x1", "2019-07-31T09:00:00Z", status="error")]})
    assert f["life"]["calls"] == 1 and f["life"]["last_tx"] is None and f["life"]["never_called"] is False


def test_counter_wins_when_positive(monkeypatch):
    f = base()
    monkeypatch.setattr(B, "first_transaction", lambda a, skip=None: {"timestamp": "2016-02-06T16:28:43Z"})
    F.set_calls(f, {"transactions_count": "21"}, {"items": [tx("0x9", "2016-02-19T21:51:14Z")], "next_page_params": {"p": 1}})
    assert f["life"]["calls"] == 21 and f["life"]["calls_source"] == "blockscout-counters"
    assert f["life"]["first_call_timestamp"] == "2016-02-06T16:28:43Z"


def test_zero_counter_with_more_pages_counts_them(monkeypatch):
    pages = {0: [tx(f"0x{i}", "2022-10-21T00:00:00Z") for i in range(50)],
             1: [tx("0xa", "2022-10-06T00:00:00Z"), tx("0xbirth", "2022-09-16T00:00:00Z", to=None, created="0xc")]}
    monkeypatch.setattr(B, "get_json", lambda url, params=None, **kw: {
        "items": pages[int(params.get("page", 0))], "next_page_params": {"page": 1} if int(params.get("page", 0)) == 0 else None})
    monkeypatch.setattr(B, "first_transaction", lambda a, skip=None: {"timestamp": "2022-10-06T00:00:00Z"})
    f = base()
    F.set_calls(f, {"transactions_count": "0"}, {"items": pages[0], "next_page_params": {"page": 1}})
    assert f["life"]["calls"] == 51 and not f["life"]["calls_capped"]


def test_never_called_is_friendly_not_lingering():
    f = extra("0xfcb0818c")
    assert f["life"]["never_called"] and f["life"]["last_tx"] is None
    k, reasons = C.decide(f, {"findings": [], "incident": None}, NOW)
    assert k == "friendly" and reasons[0].startswith("never called after its birth 10.1 years ago")
    young = json.loads(json.dumps(f))
    young["birth"]["timestamp"] = "2026-09-01T00:00:00Z"
    assert C.decide(young, None, NOW)[0] == "friendly"
    bad = {"findings": [{"impact": "High", "confidence": "High", "confirmed": True, "check": "suicidal"}], "incident": None}
    assert C.decide(f, bad, NOW)[0] == "bad"


@pytest.mark.parametrize("prefix,name,proxy", [("0xf4eced2f", "MistCoin", False), ("0x8f5e7888", "stakedXYM", True),
                                               ("0xafe6851c", "DigitalCommunityShare", False), ("0xfcb0818c", "greeter", False)])
def test_display_names_skip_generic(prefix, name, proxy):
    f = extra(prefix)
    assert F.pick_name(f) == name and F.is_proxy(f) is proxy
    assert f["name"] == name and f["proxy"] is proxy
    assert all({"name", "source"} <= set(x) for x in f["names"])


def test_names_record_every_candidate():
    f = extra("0xf4eced2f")
    srcs = {x["source"]: x["name"] for x in f["names"]}
    assert srcs["ethereumhistory"] == "MistCoin" and srcs["blockscout"] == "MyToken"
    assert F.is_generic("vyper_contract") and F.is_generic(" Token ") and not F.is_generic("TheDAO")
    assert F.pick_name({"address": "0xabc"}) == "0xabc"
    assert F.pick_name({"address": "0xabc", "blockscout": {"name": "Proxy"}}) == "Proxy"
