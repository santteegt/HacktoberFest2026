"""Lane A: snippet cutting, regex tier, catalog lookup, Slither parsing (offline)."""
import json, shutil
from pathlib import Path
import pytest
from ghosts import wounds as W
from ghosts import facts as F

FX = Path(__file__).parent / "fixtures" / "a"
KOTE, DAO, RUBIXI, SB = ("0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0", "0xbb9bc244d798123fde783fcc1c72d3bb8c189413",
                         "0xe82719202e5965cf5d9b6673b7503a3b92de20be", "0x2af47a65da8cd66729b4209c22017d6a5c2d2400")


def src(addr, name):
    return (FX / addr / "src" / name).read_text()


def test_cut_snippet_is_verbatim_and_inclusive():
    t = "a\r\nb\nc\nd\n"
    assert W.cut_snippet(t, 2, 3) == "b\nc"
    assert W.cut_snippet(t, 0, 1) == "a" and W.cut_snippet(t, 4, 99) == "d\n"
    text = src(RUBIXI, "Rubixi.sol")
    assert W.cut_snippet(text, 13, 15).splitlines()[0].strip() == "function DynamicPyramid() {"


def test_strip_comments_keeps_lines_and_strings():
    s = 'a // x.send(1);\n/* suicide(\n */ b = "http://x";\n'
    out = W.strip_comments(s)
    assert out.count("\n") == s.count("\n") and "send" not in out and "suicide" not in out and '"http://x"' in out


def test_parse_version():
    assert W.parse_version("0.4.18+commit.9cf6e910") == (0, 4, 18) and W.plain_version("v0.2.1+c") == "0.2.1"
    assert W.parse_version(None) is None


def test_regex_rubixi_constructor_name_and_sends():
    fs = W.regex_findings({"Rubixi.sol": src(RUBIXI, "Rubixi.sol")})
    ctor = [w for w in fs if w["check"] == "constructor-name"]
    assert len(ctor) == 1 and ctor[0]["lines"] == [13, 15] and "creator = msg.sender" in ctor[0]["snippet"]
    assert ctor[0]["swc"] == "SWC-118" and ctor[0]["confirmed"] is False
    assert {w["lines"][0] for w in fs if w["check"] == "unchecked-send"} and all(not w["confirmed"] for w in fs)


def test_regex_ignores_checked_send_and_comments():
    code = "contract C {\n function f() {\n  if (!a.send(1)) throw;\n  // b.send(2);\n  bool ok = c.send(3);\n  d.send(4);\n }\n}\n"
    fs = W.regex_findings({"C.sol": code})
    assert [w["check"] for w in fs] == ["unchecked-send"] and "d.send(4)" in fs[0]["snippet"]


def test_regex_kote_constructor_matches_contract_name():
    fs = W.regex_findings({"K.sol": src(KOTE, "KingOfTheEtherThrone.sol")})
    assert not [w for w in fs if w["check"] == "constructor-name"]
    assert len([w for w in fs if w["check"] == "unchecked-send"]) == 4


def test_catalog_has_required_entries_with_references():
    cat = W.load_catalog()
    ids = {e["id"] for e in cat}
    for need in ("thedao-2016", "kotet-v030-2016", "kotet-v040-2016", "rubixi-2016", "governmental-2016",
                 "parity-multisig-1-2017", "parity-multisig-2-2017", "fomo3d-round1-2018", "spankchain-2018", "lendfme-2020"):
        assert need in ids
    for e in cat:
        assert e["references"] and all(u.startswith("http") for u in e["references"])
        assert e["date"][:4] in {"2016", "2017", "2018", "2019", "2020"}


def test_catalog_lookup_case_insensitive():
    assert W.catalog_entry(DAO.upper().replace("0X", "0x"))["id"] == "thedao-2016"
    assert W.catalog_entry(SB) is None
    assert W.incident_of(W.catalog_entry("0xa9d160e32ad37ac6f2b8231e4efe14d35abb576e")) is None   # weakness, no incident


def test_catalog_confirms_only_guilty_function():
    files = {"K.sol": src(KOTE, "KingOfTheEtherThrone.sol")}
    fs = W.apply_catalog(W.regex_findings(files), W.catalog_entry(KOTE), files)
    conf = {w["title"]: w["confirmed"] for w in fs}
    assert conf["Unchecked send() in claimThrone()"] is True
    assert conf["Unchecked send() in sweepCommission()"] is False


def test_catalog_adds_finding_at_function_hint_dao():
    text = (FX / DAO / "source.eh.sol").read_text()
    files = {"source.eh.sol": text}
    fs = W.apply_catalog(W.regex_findings(files), W.catalog_entry(DAO), files)
    w = fs[0]
    assert w["check"] == "catalog" and w["confirmed"] and "withdrawRewardFor(msg.sender)" in w["snippet"]
    a, b = w["lines"]
    assert w["snippet"] == W.cut_snippet(text, a, b) and b - a + 1 <= W.SNIPPET_MAX


def test_slither_findings_shortlist_and_snippets():
    d = json.loads((FX / SB / "slither.json").read_text())
    fs = W.slither_findings(d, FX / SB / "src")
    checks = {w["check"] for w in fs}
    assert checks <= set(W.SHORTLIST) and "naming-convention" not in checks and "reentrancy-no-eth" in checks
    text = src(SB, "StandardBounties.sol")
    for w in fs:
        a, b = w["lines"]
        assert w["snippet"] == W.cut_snippet(text, a, b) and w["confirmed"] and b - a + 1 <= W.SNIPPET_MAX
    eq = next(w for w in fs if w["check"] == "incorrect-equality")
    assert eq["lines"] == [226, 239] and "uses a dangerous strict equality" in eq["title"]


@pytest.fixture
def ghost_home(tmp_path, monkeypatch):
    def setup(addr):
        gd = tmp_path / addr
        shutil.copytree(FX / addr, gd)
        f = json.loads((gd / "facts.json").read_text())
        if f.get("source"):
            f["source"]["dir"] = str(gd / "src")
        monkeypatch.setattr(F, "summon", lambda a, *k, **kw: f)
        monkeypatch.setattr(F, "ghost_dir", lambda a: gd)
        return gd
    return setup


def test_analyze_offline_rubixi(ghost_home):
    gd = ghost_home(RUBIXI)
    w = W.analyze(RUBIXI)
    assert w["tier"] == "catalog" and w["incident"]["date"] == "2016-04-02" and w["slither_raw"] is None
    assert w["findings"][0]["check"] == "constructor-name" and w["findings"][0]["confirmed"]
    assert [x["id"] for x in w["findings"]] == [f"w{i}" for i in range(1, len(w["findings"]) + 1)]
    assert json.loads((gd / "wounds.json").read_text())["tier"] == "catalog"


def test_analyze_offline_slither_tier(ghost_home, monkeypatch):
    gd = ghost_home(SB)
    raw = json.loads((FX / SB / "slither.json").read_text())
    monkeypatch.setattr(W, "run_slither", lambda *a, **k: (raw, {"method": "solc-json", "errors": []}))
    monkeypatch.setattr(W, "tool_version", lambda cmd: "0.11.6")
    monkeypatch.setattr(W.config, "ROOT", gd.parent)
    w = W.analyze(SB)
    assert w["tier"] == "slither" and w["incident"] is None and w["compiler_version"].startswith("0.4.18")
    assert all(x["confirmed"] for x in w["findings"]) and w["run"]["tools"]["solc"] == "0.4.18"
