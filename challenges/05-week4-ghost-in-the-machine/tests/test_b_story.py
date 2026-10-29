"""Lane B: ghosts.story with a fake model that tells exactly one lie per chapter (offline).

The tests watch the verifier catch each lie: repaired when the fake model's rewrite is clean, dropped when it lies again.
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ghosts import story as S

FIX = Path(__file__).parent / "fixtures" / "b"
RUBIXI = "0xe82719202e5965cf5d9b6673b7503a3b92de20be"
KOTE = "0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0"
NOW = datetime(2026, 10, 29, 6, 0, tzinfo=timezone.utc)

# one lie per chapter, marked LIE
CHAPTERS = {
    "of its birth": ["Rubixi was born on March 14, 2016, in the Homestead era.",
                     "It came into the Homestead era. Vitalik Buterin blessed it on March 15, 2016."],          # LIE: name + date
    "of its life": ["People called it 712 times. It once held 777 ETH."],                                     # LIE: 777 ETH
    "haunting": ["I was born under a borrowed name, DynamicPyramid.", "They call it 'the owner's curse' in the taverns."],  # LIE: quote
    "ghost-buster": ["The ghost buster speaks of the `constructor` keyword. Since 1999 the cure has been known."],  # LIE: year
    "of its silence": ["Its last call came on February 19, 2016. Then 42 years of silence followed."],           # LIE: 42
    "knocking": ["It still holds about 83 ETH. Someone knocked in 1987."],                                       # LIE: 1987
}
REPAIRS = {  # rewrite of each lie: clean -> repaired, still lying -> dropped
    "Vitalik Buterin blessed it on March 15, 2016.": "It was born on March 14, 2016.",
    "It once held 777 ETH.": "It once held 778 ETH.",
    "They call it 'the owner's curse' in the taverns.": "They call it 'the owner's curse' still.",
    "Since 1999 the cure has been known.": "Since 0.4.22 the cure has been known.",
    "Then 42 years of silence followed.": "Then years of silence followed.",
    "Someone knocked in 1987.": "Someone knocked in 2026.",
}
GOOD_RENAMES = [{"from": "Pyramid", "to": "Rubixi"}, {"from": "collectFees", "to": "collectAllFees"}]


class FakeModel:
    def __init__(self, rename_replies=None, chapters=None, repairs=None):
        self.calls = []
        self.rename_replies = list(rename_replies or [GOOD_RENAMES])
        self.chapters = chapters or CHAPTERS
        self.repairs = repairs or REPAIRS

    def __call__(self, messages, schema=None, think=False, temperature=0.6):
        self.calls.append({"messages": messages, "think": think})
        user = messages[-1]["content"]
        usage = {"calls": 1, "seconds": 1.0, "wall_seconds": 1.0, "prompt_tokens": 100, "output_tokens": 50}
        if "Rewrite it in the same voice" in user:
            bad = user.split("):\n", 1)[1].split("\n\nRewrite", 1)[0]
            return {"sentence": self.repairs.get(bad, bad)}, usage
        if '{"renames"' in user:
            return {"renames": self.rename_replies.pop(0) if len(self.rename_replies) > 1 else self.rename_replies[0]}, usage
        if "Write a title" in user:
            return {"title": "The pyramid that kept its old name", "tagline": "A small program still waits on the chain."}, usage
        for key, paras in self.chapters.items():
            if key in user:
                return {"heading": "a heading", "paragraphs": paras}, usage
        raise AssertionError("unexpected prompt: " + user[-200:])


def ghost_root(tmp_path, address):
    shutil.copytree(FIX / address, tmp_path / address)
    return tmp_path


def compile_ok(code):
    return True, "solc 0.8.38 --bin: OK (mock)"


def test_bad_ghost_catches_one_lie_per_chapter(tmp_path):
    root = ghost_root(tmp_path, RUBIXI)
    fake = FakeModel()
    st = S.tell(RUBIXI, chat=fake, compile_fn=compile_ok, now=NOW, root=root, log=lambda *a: None)
    assert (root / RUBIXI / "story.json").exists()
    assert st["kind"] == "bad" and st["kind_source"] == "verdict.json"
    assert [c["id"] for c in st["chapters"]] == ["birth", "life", "haunting", "buster"]
    v = st["verifier"]
    # 4 chapters x 1 lie: birth repaired, life dropped, haunting dropped, buster repaired
    assert v["repaired"] == 2 and v["dropped"] == 2
    assert "It once held 777 ETH." in v["dropped_text"]
    assert "They call it 'the owner's curse' in the taverns." in v["dropped_text"]
    text = json.dumps(st["chapters"])
    assert "Vitalik" not in text and "777" not in text and "1999" not in text and "owner's curse" not in text
    assert "It was born on March 14, 2016." in st["chapters"][0]["paragraphs"][1]
    assert v["sentences"] == v["grounded"] + v["repaired"] + v["dropped"]
    # snippet copied verbatim from wounds.json, never from the model
    wounds = json.loads((root / RUBIXI / "wounds.json").read_text())
    assert st["scary"]["snippet"]["code"] == wounds["findings"][0]["snippet"]
    assert st["scary"]["snippet"]["lines"] == [13, 15]
    fix = st["buster"]["fix"]
    assert fix["compiled"] and fix["adapted"] and fix["recipe"] == "constructor-name"
    assert fix["renames"] == {"Pyramid": "Rubixi", "collectFees": "collectAllFees"}
    assert "contract Rubixi" in fix["code"] and "function collectAllFees() external onlyOwner" in fix["code"]
    assert "constructor()" in fix["code"] and "DynamicPyramid" not in fix["code"]
    assert all(c["think"] is False for c in fake.calls)
    assert st["model"]["calls"] == len(fake.calls) and st["model"]["prompt_tokens"] == 100 * len(fake.calls)


def test_haunting_is_first_person_others_are_not(tmp_path):
    fake = FakeModel()
    S.tell(RUBIXI, chat=fake, compile_fn=compile_ok, now=NOW, root=ghost_root(tmp_path, RUBIXI), write=False, log=lambda *a: None)
    systems = {c["messages"][-1]["content"].split("\n\n")[-1][:40]: c["messages"][0]["content"] for c in fake.calls if c["messages"][0]["role"] == "system"}
    haunt = [s for k, s in systems.items() if "haunting" in k]
    assert haunt and "first person" in haunt[0]
    assert all("third person" in s for k, s in systems.items() if "haunting" not in k and "Write a title" not in k and "RULES" not in s and "Rules" in s)


def test_fix_never_brings_back_the_old_constructor(tmp_path):
    # the model keeps trying to name a function after the misnamed constructor: refused twice, generic recipe used
    bad = [{"from": "collectFees", "to": "DynamicPyramid"}]
    fake = FakeModel(rename_replies=[bad, bad])
    seen = []

    def compile_fn(code):
        seen.append(code)
        return True, "OK"
    st = S.tell(RUBIXI, chat=fake, compile_fn=compile_fn, now=NOW, root=ghost_root(tmp_path, RUBIXI), write=False, log=lambda *a: None)
    fix = st["buster"]["fix"]
    assert not fix["adapted"] and "generic" in fix["note"] and fix["compiled"]
    assert fix["code"] == S.recipe_for("constructor-name")["code"] and "DynamicPyramid" not in fix["code"]
    assert all("old misnamed constructor" in " ".join(a["rename_problems"]) for a in fix["failed_attempts"])


def test_fix_rejects_names_not_in_the_old_source_and_compile_errors(tmp_path):
    replies = [[{"from": "Pyramid", "to": "Rubixi"}, {"from": "collectFees", "to": "notInSource"}], GOOD_RENAMES]
    fake = FakeModel(rename_replies=replies)
    calls = []

    def compile_fn(code):
        calls.append(code)
        return (len(calls) > 1), ("OK" if len(calls) > 1 else "Error: something")
    st = S.tell(RUBIXI, chat=fake, compile_fn=compile_fn, now=NOW, root=ghost_root(tmp_path, RUBIXI), write=False, log=lambda *a: None)
    fix = st["buster"]["fix"]
    assert fix["adapted"] and fix["attempts"] == 2 and fix["renames"]["collectFees"] == "collectAllFees"
    assert "notInSource does not appear in the old contract" in fix["failed_attempts"][0]["rename_problems"]


def test_style_gate_rewrites_raw_identifiers(tmp_path):
    chapters = dict(CHAPTERS)
    chapters["of its birth"] = ["Rubixi was born on March 14, 2016, in block 1150481.",
                                "Its deployer was 0xdd68da49b2a0c46eb508bd4f18044b5c6268ad60. It was written in 0.2.1+commit.91a6b35f."]
    repairs = dict(REPAIRS)
    repairs["Rubixi was born on March 14, 2016, in block 1150481."] = "Rubixi was born on March 14, 2016."
    repairs["Its deployer was 0xdd68da49b2a0c46eb508bd4f18044b5c6268ad60."] = "Its deployer was the wallet 0xdd68…ad60."
    st = S.tell(RUBIXI, chat=FakeModel(chapters=chapters, repairs=repairs), compile_fn=compile_ok, now=NOW,
                root=ghost_root(tmp_path, RUBIXI), write=False, log=lambda *a: None)
    birth = " ".join(st["chapters"][0]["paragraphs"])
    assert "1150481" not in birth and "+commit" not in birth and "0xdd68da49b2a0" not in birth
    assert "0xdd68…ad60" in birth
    v = st["verifier"]
    assert v["style"]["rewritten"] == 2 and v["style"]["dropped"] == 1      # the commit sentence is rewritten as itself: dropped
    assert "It was written in 0.2.1+commit.91a6b35f." not in v["dropped_text"]   # style drops are not silenced lies


def test_style_problems():
    assert S.style_problems("Born in 2017, busy in 2022, 2023 and 2024.")
    assert not S.style_problems("Born in 2017, busy every year since 2022.")
    assert S.style_problems("It sits in block 4,756,336.", 4756336)
    assert not S.style_problems("It sits in a block of its own.", 4756336)


def test_labels():
    assert S.short_hex("0xbfdb50dc66c8df9fd9688d8fe5a0c34126427645") == "0xbfdb…7645"
    assert S.compiler_label("0.4.18+commit.9cf6e910") == "Solidity 0.4.18"
    assert S.activity_label(["2022", "2023", "2024", "2025", "2026"], NOW) == "active every year since 2022"
    assert S.activity_label(["2016"], NOW) == "last busy in 2016"


def test_friendly_without_verdict_uses_heuristic(tmp_path):
    root = ghost_root(tmp_path, KOTE)
    st = S.tell(KOTE, chat=FakeModel(), compile_fn=compile_ok, now=NOW, root=root, write=False, log=lambda *a: None)
    assert st["kind"] == "friendly" and st["kind_source"].startswith("heuristic")
    assert any("verdict.json missing" in n for n in st["notes"])
    assert [c["id"] for c in st["chapters"]] == ["birth", "life", "silence"]
    assert st["scary"] is None and st["buster"] is None
    assert "Then 42 years of silence followed." not in json.dumps(st["chapters"])
    assert st["verifier"]["repaired"] >= 1


def test_lingering_gets_the_knocking(tmp_path):
    sb = "0x2af47a65da8cd66729b4209c22017d6a5c2d2400"
    st = S.tell(sb, chat=FakeModel(), compile_fn=compile_ok, now=NOW, root=ghost_root(tmp_path, sb), write=False, log=lambda *a: None)
    assert st["kind"] == "lingering"
    sil = st["chapters"][-1]
    assert sil["id"] == "silence" and sil["variant"] == "the knocking"
    assert "Someone knocked in 2026." in sil["paragraphs"][0]          # repaired with a year from the facts


def test_derive_and_heuristic():
    facts = json.loads((FIX / KOTE / "facts.json").read_text())
    d = S.derive(facts, None, NOW)
    assert d["born_on"] == "February 6, 2016" and d["last_seen_on"] == "February 19, 2016"
    assert d["age_years_whole"] == 10 and d["active_days"] == 13
    assert S.heuristic_kind(facts, None, NOW) == "friendly"
    assert S.heuristic_kind(facts | {"chain": {"code_present": False}}, None, NOW) == "banished"
    w = {"findings": [{"impact": "High", "confidence": "Medium"}], "incident": None}
    assert S.heuristic_kind(facts, w, NOW) == "bad"


def test_incident_only_bad_ghost(tmp_path):
    dao = "0xbb9bc244d798123fde783fcc1c72d3bb8c189413"
    st = S.tell(dao, chat=FakeModel(), compile_fn=compile_ok, now=NOW, root=ghost_root(tmp_path, dao), write=False, log=lambda *a: None)
    assert st["kind"] == "bad"
    assert st["scary"]["snippet"] is None and st["scary"]["incident"]["name"] == "The DAO hack"
    assert st["buster"]["fix"]["recipe"] == "reentrancy-eth"            # chosen from the incident summary
    assert any("incident keywords" in n for n in st["notes"])


def test_reference_sites_are_not_the_dapps_face():
    facts = json.loads((FIX / "0xbb9bc244d798123fde783fcc1c72d3bb8c189413" / "facts.json").read_text())
    assert S.dapp_sites(facts) == []                       # wikipedia, coindesk, blog, x.com: references, not the dapp
    kote = json.loads((FIX / KOTE / "facts.json").read_text())
    assert [s["host"] for s in S.dapp_sites(kote)] == ["http://www.kingoftheether.com/postmortem.html"]


def test_renames_keep_roles_and_existing_names():
    r = S.recipe_for("constructor-name")
    from ghosts.fixes.recipes import roles
    old = ("contract Rubixi {\n    uint private collectedFees = 0;\n    function collectAllFees() onlyowner {\n"
           "        uint feesToCollect = 1;\n    }\n    function changeOwner(address _owner) {}\n}")
    known = set(__import__("re").findall(r"[A-Za-z_]\w*", old))
    code, problems = S.apply_renames(r, {"collectFees": "feesToCollect", "changeOwner": "collectAllFees", "Pyramid": "Rubixi"}, known, set(), roles(old))
    assert any("is a variable in the old contract but collectFees is a function" in p for p in problems)
    assert any("changeOwner already exists" in p for p in problems)
    assert "contract Rubixi" in code and "function changeOwner" in code


def test_same_job_names():
    from ghosts.fixes.recipes import same_job
    assert same_job("collectFees", "collectAllFees") and same_job("withdraw", "payOut") and same_job("owed", "compensation")
    assert not same_job("credit", "sweepCommission") and not same_job("owed", "valuePaid") and not same_job("changeOwner", "changeFeePercentage")


def test_function_renames_keep_their_arguments():
    from ghosts.fixes.recipes import roles, arity
    r = S.recipe_for("unchecked-send")
    old = "contract KingOfTheEtherThrone {\n    function claimThrone(string name) {\n    }\n}"
    known = {"KingOfTheEtherThrone", "claimThrone"}
    code, problems = S.apply_renames(r, {"Payouts": "KingOfTheEtherThrone", "claim": "claimThrone"}, known, set(), roles(old), arity(old))
    assert any("takes 1 argument(s)" in p for p in problems)
    assert "function claim()" in code and "contract KingOfTheEtherThrone" in code


BEAN = "0xdc59ac4fefa32293a95889dc396682858d52e5db"
GREETER = "0xfcb0818c0b79a98686b2f56d4623d0b6c0243c55"


class GenericModel(FakeModel):
    """Answers every chapter with one grounded sentence, and records which ask each chapter got."""
    def __init__(self, line):
        super().__init__()
        self.line, self.asks = line, []

    def __call__(self, messages, schema=None, think=False, temperature=0.6):
        user = messages[-1]["content"]
        usage = {"calls": 1, "seconds": 1.0, "wall_seconds": 1.0, "prompt_tokens": 1, "output_tokens": 1}
        if "Write a title" in user:
            return {"title": "A quiet ghost", "tagline": "A small program waits."}, usage
        if "Rewrite it in the same voice" in user:
            return {"sentence": "Nobody ever knocked."}, usage
        if '{"renames"' in user:
            return {"renames": []}, usage
        self.asks.append(user)
        return {"heading": "a heading", "paragraphs": [self.line]}, usage


def test_never_called_ghost_has_no_life_and_no_last_call(tmp_path):
    fake = GenericModel("Its last call came long ago.")
    st = S.tell(GREETER, chat=fake, compile_fn=compile_ok, now=NOW, root=ghost_root(tmp_path, GREETER), write=False, log=lambda *a: None)
    ids = [c["id"] for c in st["chapters"]]
    assert "life" not in ids and ids[-1] == "silence" and st["chapters"][-1]["variant"] == "never called"
    assert "last_seen_on" not in st["derived"] and st["derived"]["never_called"] is True
    assert "nobody ever called it" in fake.asks[-1] and "Never speak of a last call" in fake.asks[-1]
    text = json.dumps(st["chapters"])
    assert "last call" not in text                                   # the style gate rewrote every "last call"
    assert any("never called" in n for n in st["notes"])


def test_incident_pick_without_recipe_gets_an_honest_buster(tmp_path):
    fake = GenericModel("The record names it.")
    st = S.tell(BEAN, chat=fake, compile_fn=compile_ok, now=NOW, root=ghost_root(tmp_path, BEAN), write=False, log=lambda *a: None)
    assert st["kind"] == "bad"
    b = st["buster"]
    assert b["fix"] is None and "No compiler version fixes this wound" in b["fix_reason"] and b["recipe"] is None
    assert b["mitigation"]["flaw_kind"] == "governance"                # cause "DAO + Flashloan"
    buster_ask = fake.asks[-1]
    assert "no compiler version" in buster_ask and "general_mitigation" in buster_ask
    haunt_ask = next(a for a in fake.asks if "Tell the haunting" in a)
    assert "DeFiHackLabs record of the BeanstalkFarms incident" in haunt_ask and "a token" in haunt_ask
    assert "not to me alone" in haunt_ask


def test_still_in_use_and_flaw_kinds():
    assert S.still_in_use({"activity": {"last_12m_txs": 223, "lifetime_txs": 175183}}) == {"calls_in_last_12_months": 223, "calls_in_its_life": 175183}
    assert S.still_in_use({"activity": {"last_12m_txs": 75, "lifetime_txs": 712}})       # 10.5 % of its life
    assert S.still_in_use({"activity": {"last_12m_txs": 35, "lifetime_txs": 5093}}) is None
    assert S.flaw_of({"cause": "Price Manipulation"})[0] == "price oracle"
    assert S.flaw_of({"cause": "Insufficient Token Validation"})[0] == "input validation"
    assert S.flaw_of({"cause": "Sandwich attack"})[0] == "trade ordering"
    assert S.flaw_of({"cause": "business logic flaw"})[0] == "economic logic"
    assert S.style_problems("Its last call came in 2016.", never_called=True)
    assert not S.style_problems("Its last call came in 2016.")


def test_title_words_must_be_english_or_facts():
    from ghosts.verify import FactIndex
    ix = FactIndex.build(facts={"name": "greeter", "age": {"hardfork": "DAO Fork"}})
    if not S.Path("/usr/share/dict/words").exists():
        return
    assert S.title_unknown_words("The Silent Greeting of Blokur", ix) == ["Blokur"]
    assert S.title_unknown_words("The Silent Greeting of the DAO Fork", ix) == []
