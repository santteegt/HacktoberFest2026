"""Lane C1 follow-up: never-called ghosts, fix-less busters, name/proxy/still-in-use tags, chapter variants."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from ghosts import render as R

FIX = Path(__file__).parent / "fixtures" / "c1" / "ghosts"
NEVER = "0xfcb0818c0b79a98686b2f56d4623d0b6c0243c55"   # greeter, friendly, never called
NOFIX = "0x3d5bc3c8d13dcb8bf317092d84783c2697ae9258"   # Unitroller, bad, fix null + fix_reason


def _render(tmp_path, addr, data=FIX):
    p = R.render(addr, data_dir=data, out_dir=tmp_path / "out")
    return p, p.read_text(encoding="utf-8")


def _copy(tmp_path, addr):
    d = tmp_path / "data" / addr
    shutil.copytree(FIX / addr, d)
    return tmp_path / "data", d


def test_never_called(tmp_path):
    p, doc = _render(tmp_path, NEVER)
    assert p.stat().st_size < R.SIZE_LIMIT
    assert "<dt>Never called</dt>" in doc and "<dt>Last seen</dt>" not in doc
    assert doc.count("<li class=\"ev-") == 1
    assert "nobody ever knocked" in doc
    assert doc.count('class="mark ') == 1
    assert "Nobody ever knocked" in doc
    assert "Chapter 2 · Never called" in doc


def test_fix_null_shows_reason_not_code(tmp_path):
    _, doc = _render(tmp_path, NOFIX)
    assert 'class="fix-note"' in doc
    assert "No compiler version fixes this wound" in doc
    assert "code-card fix" not in doc and "compiled:" not in doc
    assert "CreamFinance" in doc and "about $130,000,000 lost" in doc
    body = doc.split("<body", 1)[1]  # <head> holds the absolute link-preview URLs by design
    body = re.sub(r'<a class="copy eh-link" href="https://www\.ethereumhistory\.com/contract/0x[0-9a-f]{40}"', "", body)  # the ofrenda's one link
    assert not re.search(r"https?://", re.sub(r'<footer class="smallprint".*?</footer>', "", body, flags=re.S))


def test_tags_and_source_name(tmp_path):
    data, d = _copy(tmp_path, NOFIX)
    f = json.loads((d / "facts.json").read_text())
    f["proxy"] = True
    f["names"] = [{"name": "Unitroller", "source": "blockscout"}, {"name": "ComptrollerProxy", "source": "source:sourcify"}]
    (d / "facts.json").write_text(json.dumps(f))
    v = json.loads((d / "verdict.json").read_text())
    v["activity"]["last_12m_txs"] = 150
    (d / "verdict.json").write_text(json.dumps(v))
    _, doc = _render(tmp_path, NOFIX, data)
    assert 'source name: <span class="mono">ComptrollerProxy</span>' in doc
    assert doc.count('<span class="chip tag">proxy</span>') == 2  # title chips + ofrenda card
    assert doc.count('<span class="chip tag">still in use</span>') == 2


def test_no_tags_by_default(tmp_path):
    _, doc = _render(tmp_path, NOFIX)
    assert "chip tag" not in doc and "source name:" not in doc


def test_variant_label(tmp_path):
    data, d = _copy(tmp_path, NEVER)
    s = json.loads((d / "story.json").read_text())
    s["chapters"][1]["variant"] = "the knocking"
    (d / "story.json").write_text(json.dumps(s))
    _, doc = _render(tmp_path, NEVER, data)
    assert "Chapter 2 · The knocking" in doc
