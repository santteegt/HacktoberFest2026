from pathlib import Path
from ghosts import incidents as I

FX = Path(__file__).parent / "fixtures" / "d"


def test_parse_readme_entries():
    es = I.parse_readme((FX / "readme_2021_excerpt.md").read_text(), 2021)
    assert [e["name"] for e in es] == ["Visor Finance"]  # the other two belong to 2023 / 2022
    es_all = I.parse_readme((FX / "readme_2021_excerpt.md").read_text(), 2023) + I.parse_readme((FX / "readme_2021_excerpt.md").read_text(), 2022)
    assert {e["name"] for e in es_all} == {"Channels", "JAY"}


def test_visor_fields():
    e = I.parse_readme((FX / "readme_2021_excerpt.md").read_text(), 2021)[0]
    assert e["date"] == "2021-12-21"
    assert e["cause"] == "Reentrancy"
    assert e["loss_usd"] == 8_200_000
    assert e["poc_path"] == "src/test/2021-12/Visor_exp.sol"
    assert e["poc_url"].endswith("/blob/main/src/test/2021-12/Visor_exp.sol")
    assert len(e["references"]) == 3 and e["references"][0].startswith("https://beosin.medium.com")


def test_format_drift_and_leading_dash():
    txt = (FX / "readme_2021_excerpt.md").read_text()
    ch = [e for e in I.parse_readme(txt, 2023)][0]
    assert ch["loss_usd"] == 4400 and ch["poc_path"].endswith("Channels_exp.sol")  # '### Lost:' with three hashes
    jay = I.parse_readme(txt, 2022)[0]
    assert jay["name"] == "JAY" and jay["cause"] == "Insufficient validation + Reentrancy"
    assert jay["loss_usd"] is None and jay["loss_text"] == "~15.32 ETH"  # coin amounts are not guessed into dollars


def test_parse_loss_variants():
    cases = {"$8.2 million": 8_200_000, "$130M": 130_000_000, "365K": 365_000, "~$4.4K": 4400, "~1,24M": 1_240_000,
             "153,037 ETH (~$30M)": 30_000_000, "704 ETH (~1.08M US$)": 1_080_000, "$1450": 1450, "$.2 million": 200_000,
             "20M USD": 20_000_000, "~63k $USDT": 63_000, "$2.3 ETH": None, "390 ETH": None, "12BNB": None,
             "All funds returned": None, "": None, None: None}
    for text, want in cases.items():
        assert I.parse_loss(text) == want, text


def test_poc_addresses_and_primary():
    p = I.parse_poc((FX / "poc_visor_excerpt.sol").read_text())
    # cheatcodes and WETH are well-known noise; the victims come first, in order, lowercase, no duplicates
    assert p["victim_addresses"] == ["0xc9f27a50f82571c1c8423a42970613b8dbda14ef", "0x3a84ad5d16adbe566baa6b3dafe39db3d5e261e5"]
    assert p["primary"] == "0xc9f27a50f82571c1c8423a42970613b8dbda14ef"
    assert len(p["ignored_well_known"]) == 2
    assert p["chains"] == ["mainnet"]


def test_chain_filter():
    bsc = I.parse_poc((FX / "poc_bsc_excerpt.sol").read_text())
    assert bsc["chains"] == ["bsc"] and not I.keep_chain(bsc["chains"], [])
    assert I.keep_chain(["mainnet"], [])
    assert not I.keep_chain(["mainnet", "bsc"], [])
    assert I.keep_chain([], ["https://etherscan.io/tx/0x1"])            # no fork named, no other chain
    assert not I.keep_chain([], ["https://bscscan.com/tx/0x1"])          # no fork named, but a BSC reference
