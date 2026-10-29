"""Lane B: fix recipes and the solc 0.8.38 compile gate."""
import re

import pytest

from ghosts.fixes import RECIPES, recipe_for, compile_solidity
from ghosts.fixes import compile as C

REQUIRED = ["reentrancy-eth", "unchecked-send", "unchecked-lowlevel", "suicidal", "controlled-delegatecall", "tx-origin",
            "uninitialized-storage", "weak-prng", "constructor-name-mismatch", "locked-ether"]


@pytest.mark.parametrize("check", REQUIRED)
def test_required_checks_have_recipes(check):
    assert recipe_for(check) is not None


@pytest.mark.parametrize("key", sorted(RECIPES))
def test_recipe_shape(key):
    r = RECIPES[key]
    assert re.search(r"pragma solidity \^?0\.8\.38;", r["code"])
    assert "SPDX-License-Identifier" in r["code"]
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", r["explain"].strip()) if s]
    assert len(sentences) == 2, key


def test_lookup_by_swc_and_keywords():
    assert recipe_for(swc="SWC-107")["check"] == "reentrancy-eth"
    assert recipe_for(text="The DAO hack: a reentrancy in splitDAO")["check"] == "reentrancy-eth"
    assert recipe_for(text="constructor name typo")["check"] == "constructor-name"
    assert recipe_for("no-such-check") is None


def test_compile_gate_mocked(monkeypatch):
    class R:
        returncode, stdout, stderr = 1, "", "Fix.sol:3:1: ParserError: Expected pragma"
    monkeypatch.setattr(C, "solc_path", lambda: ["solc"])
    monkeypatch.setattr(C.subprocess, "run", lambda *a, **k: R())
    ok, out = compile_solidity("garbage")
    assert not ok and "ParserError" in out

    class G:
        returncode, stderr = 0, ""
        stdout = "\n======= Fix.sol:Vault =======\nBinary:\n6080604052\n"
    monkeypatch.setattr(C.subprocess, "run", lambda *a, **k: G())
    ok, out = compile_solidity("contract Vault {}")
    assert ok and "Vault 5 bytes" in out


def test_compile_gate_without_solc(monkeypatch):
    monkeypatch.setattr(C, "solc_path", lambda: None)
    ok, out = compile_solidity("x")
    assert not ok and "not found" in out


@pytest.mark.skipif(not (C.Path.home() / ".solc-select/artifacts/solc-0.8.38/solc-0.8.38").exists(), reason="solc 0.8.38 not installed")
@pytest.mark.parametrize("key", sorted(RECIPES))
def test_recipes_really_compile(key):
    ok, out = compile_solidity(RECIPES[key]["code"])
    assert ok, out
