"""Lane A: taxonomy precedence and thresholds (offline)."""
import copy, json
from pathlib import Path
from ghosts import classify as C
from ghosts import activity as A

FX = Path(__file__).parent / "fixtures" / "a"
KOTE, DAO, RUBIXI, SB = ("0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0", "0xbb9bc244d798123fde783fcc1c72d3bb8c189413",
                         "0xe82719202e5965cf5d9b6673b7503a3b92de20be", "0x2af47a65da8cd66729b4209c22017d6a5c2d2400")
NOW = A.parse_ts("2026-10-29T05:00:00Z")
SERIOUS = {"findings": [{"check": "reentrancy-eth", "impact": "High", "confidence": "Medium", "confirmed": True, "title": "x"}], "incident": None}
SUSPECTED = {"findings": [{"check": "unchecked-send", "impact": "Medium", "confidence": "Low", "confirmed": False, "title": "x"}], "incident": None}
INCIDENT = {"findings": [], "incident": {"name": "The DAO hack", "date": "2016-06-17"}}


def facts(addr):
    return json.loads((FX / addr / "facts.json").read_text())


def kind(f, w=None):
    return C.decide(f, w, NOW)[0]


def test_friendly_kote_without_wounds():
    assert kind(facts(KOTE)) == "friendly"
    assert kind(facts(KOTE), SUSPECTED) == "friendly"   # suspected wounds alone do not make a bad ghost


def test_bad_beats_alive_and_friendly():
    assert kind(facts(KOTE), SERIOUS) == "bad"
    assert kind(facts(DAO)) == "alive"                   # 223 calls in 12 months
    assert kind(facts(DAO), INCIDENT) == "bad"


def test_low_confidence_or_low_impact_is_not_bad():
    for imp, conf in (("High", "Low"), ("Low", "High"), ("Informational", "High")):
        w = {"findings": [{"impact": imp, "confidence": conf, "confirmed": True}], "incident": None}
        assert kind(facts(KOTE), w) == "friendly"


def test_banished_beats_everything():
    f = facts(DAO)
    f["chain"]["code_present"] = False
    assert kind(f, INCIDENT) == "banished"
    f["chain"] = {"error": "rpc down"}                   # unknown is not banished
    assert kind(f, INCIDENT) == "bad"


def test_alive_by_share_and_lingering():
    f = facts(RUBIXI)                                    # 75 of 712 = 10.5 % -> alive
    assert kind(f) == "alive"
    f["life"]["last_12m_txs"] = 30                       # 4.2 %, no site -> lingering
    v = C.decide(f, None, NOW)
    assert v[0] == "lingering" and "no site known" in v[1]


def test_lingering_fallback_when_site_answers():
    f = facts(SB)                                        # 27 calls, bounties.network captured in 2026
    k, reasons = C.decide(f, None, NOW)
    assert k == "lingering" and any("fallback" in r for r in reasons)


def test_verdict_schema():
    v = C.verdict(facts(KOTE), SUSPECTED, NOW)
    assert set(v) == {"address", "kind", "reasons", "activity", "wounds", "labels", "decided_at"}
    assert set(v["activity"]) == {"lifetime_txs", "last_tx", "last_12m_txs", "last_12m_capped", "silent_years"}
    assert v["activity"] == {"lifetime_txs": 21, "last_tx": "2016-02-19T21:51:14Z", "last_12m_txs": 0,
                             "last_12m_capped": False, "silent_years": 10.7}
    assert v["wounds"] == {"count": 1, "confirmed": 0, "worst_impact": "Medium", "scars": 0, "fatal": 0}
    assert v["labels"] == {"historian_story": True, "verified_source": True, "site_known": True}


SCARRED = {"findings": [{"check": "reentrancy-no-eth", "impact": "Medium", "confidence": "Medium", "confirmed": True, "title": "x"},
                        {"check": "incorrect-equality", "impact": "Medium", "confidence": "High", "confirmed": True, "title": "y"},
                        {"check": "unchecked-send", "impact": "Medium", "confidence": "Low", "confirmed": False, "title": "z"}],
           "incident": None}


def test_medium_wounds_are_scars_not_bad():
    k, reasons = C.decide(facts(KOTE), SCARRED, NOW)
    assert k == "friendly" and "2 scars (reentrancy-no-eth, incorrect-equality), none fatal" in reasons
    assert C.wound_summary(SCARRED) == {"count": 3, "confirmed": 2, "worst_impact": "Medium", "scars": 2, "fatal": 0}


def test_high_impact_needs_confirmation_and_confidence():
    w = {"findings": [{"impact": "High", "confidence": "Medium", "confirmed": False}], "incident": None}
    assert kind(facts(KOTE), w) == "friendly"            # suspected (regex) High is not fatal
    w["findings"][0]["confirmed"] = True
    assert kind(facts(KOTE), w) == "bad" and C.wound_summary(w)["fatal"] == 1


def test_standardbounties_lingers_with_scars():
    k, reasons = C.decide(facts(SB), SCARRED, NOW)
    assert k == "lingering" and any("scars" in r for r in reasons)


def test_incident_with_only_scars_is_bad():
    w = {**SCARRED, "incident": {"name": "KotET", "date": "2016-02-06"}}
    k, reasons = C.decide(facts(KOTE), w, NOW)
    assert k == "bad" and reasons[1].endswith("none fatal")
