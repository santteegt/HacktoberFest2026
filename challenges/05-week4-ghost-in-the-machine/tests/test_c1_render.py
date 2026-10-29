"""Lane C1: the comic page renderer. No network: fixtures only."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from ghosts import render as R

FIX = Path(__file__).parent / "fixtures" / "c1" / "ghosts"
FRIENDLY = "0xb336a86e2feb1e87a328fcb7dd4d04de3df254d0"
BAD = "0xe82719202e5965cf5d9b6673b7503a3b92de20be"
LINGERING = "0x2af47a65da8cd66729b4209c22017d6a5c2d2400"


def _render(tmp_path, addr, data=FIX):
    p = R.render(addr, data_dir=data, out_dir=tmp_path / "out")
    return p, p.read_text(encoding="utf-8")


def _outside_smallprint(doc: str) -> str:
    """The page minus the small print and the link-preview tags in <head> (absolute URLs by design)."""
    doc = re.sub(r'<footer class="smallprint".*?</footer>', "", doc, flags=re.S)
    doc = re.sub(r'<meta (property="og:|name="twitter:)[^>]*>', "", doc)
    return re.sub(r'<link rel="canonical"[^>]*>', "", doc)


@pytest.mark.parametrize("addr,kind,title", [
    (FRIENDLY, "friendly", "The throne that fell silent"),
    (BAD, "bad", "The pyramid that forgot its own name"),
    (LINGERING, "lingering", "The bounty board in the empty square"),
])
def test_fixture_renders_key_strings(tmp_path, addr, kind, title):
    p, doc = _render(tmp_path, addr)
    assert p == tmp_path / "out" / addr / "index.html"
    assert f'<body data-kind="{kind}">' in doc
    assert f">{title}</h1>" in doc
    assert addr in doc and 'data-copy="' + addr + '"' in doc
    assert R.KINDS[kind] in doc
    assert "The storyteller spoke" in doc
    assert "Claude" not in doc and "closed model" not in doc
    assert "hand-written test fixture" in doc
    assert doc.count("<svg") >= 5  # picado, title teller + ghost, one per chapter
    assert "<title id=" in doc  # SVG alt text
    markup = re.sub(r"<(style|script)>.*?</\1>", "", doc, flags=re.S)
    assert not re.search(r"\$\{?[a-z_]+", markup), "unfilled placeholder"


def test_size_and_no_external_refs(tmp_path):
    for addr in (FRIENDLY, BAD, LINGERING):
        p, doc = _render(tmp_path, addr)
        assert p.stat().st_size < R.SIZE_LIMIT
        outside = _outside_smallprint(doc)
        assert not re.search(r"https?://", outside), re.findall(r".{40}https?://.{40}", outside)[:3]
        assert not re.search(r"<script[^>]+src=", doc)
        assert not re.search(r'<link (?!rel="canonical")[^>]*href=', doc)
        assert "@import" not in doc and "url(http" not in doc
        foot = re.search(r'<footer class="smallprint".*?</footer>', doc, re.S)[0]
        assert "https://eth.blockscout.com/address/" + addr in foot
        assert "https://www.ethereumhistory.com/contract/" + addr in foot


def test_bad_ghost_panels(tmp_path):
    _, doc = _render(tmp_path, BAD)
    assert "the guilty code" in doc
    assert '<span class="ln">12</span>' in doc and '<span class="ln">15</span>' in doc
    assert "Rubixi.sol, lines 12-15" in doc
    assert "Solidity 0.8.38, compiled: no" in doc
    assert 'class="balloon scary"' in doc and 'class="balloon buster"' in doc
    assert 'pill confirmed' in doc
    assert "<s>Its creator lost 40 ether in a single night.</s>" in doc
    assert "https://swcregistry.io/docs/SWC-118" in doc
    assert re.search(r'class="panel chapter reveal tilt-[lr] busted"', doc)


def test_friendly_and_lingering_moments(tmp_path):
    _, doc = _render(tmp_path, FRIENDLY)
    assert "It became a ghost after its last call on 19 Feb 2016" in doc
    assert "10.7 years" in doc
    assert "guilty code" not in doc
    assert "Kieran Elby" in doc
    _, doc = _render(tmp_path, LINGERING)
    assert "people still knock: 7 calls in the last 12 months" in doc
    assert "The knocking" in doc
    assert "83.001304 ETH" in doc
    assert "https://web.archive.org/web/20170923162827/bounties.network" in doc


def _copy(tmp_path, addr, keep=("facts.json",)):
    d = tmp_path / "data" / addr
    d.mkdir(parents=True)
    for name in keep:
        shutil.copy(FIX / addr / name, d / name)
    return tmp_path / "data", d


def test_facts_only_degrades(tmp_path):
    data, _ = _copy(tmp_path, FRIENDLY)
    _, doc = _render(tmp_path, FRIENDLY, data)
    assert "The storyteller has not spoken yet" in doc
    assert 'data-kind="unknown"' in doc
    assert "No story yet" in doc
    assert "Not classified yet" in doc
    assert "KingOfTheEtherThrone" in doc


def test_name_fallback_skips_control_chars(tmp_path):
    data, d = _copy(tmp_path, FRIENDLY)
    f = json.loads((d / "facts.json").read_text())
    f["name"] = "\u0001"
    f["eh"]["name"] = None
    f["blockscout"]["name"] = "\u0001"
    (d / "facts.json").write_text(json.dumps(f))
    _, doc = _render(tmp_path, FRIENDLY, data)
    assert "\u0001" not in doc
    assert "KingOfTheEtherThrone" in doc  # from source.name


def test_escaping_and_unsafe_urls(tmp_path):
    data, d = _copy(tmp_path, BAD, keep=("facts.json", "verdict.json", "story.json", "wounds.json"))
    s = json.loads((d / "story.json").read_text())
    s["title"] = '<script>alert("boo")</script>'
    s["chapters"][0]["paragraphs"][0] = 'A <img src=x onerror=alert(1)> & "quotes"'
    s["scary"]["snippet"]["code"] = "if (a < b && c > d) { evil(); }"
    (d / "story.json").write_text(json.dumps(s))
    w = json.loads((d / "wounds.json").read_text())
    w["findings"][0]["reference_url"] = "javascript:alert(1)"
    w["incident"] = {"name": "Night of <b>", "date": "2016-06-17", "loss_usd": 1000, "summary": "s", "references": ["https://example.org/x"]}
    (d / "wounds.json").write_text(json.dumps(w))
    _, doc = _render(tmp_path, BAD, data)
    assert "<script>alert" not in doc
    assert "&lt;script&gt;alert(&quot;boo&quot;)&lt;/script&gt;" in doc
    assert "&lt;img src=x onerror=alert(1)&gt; &amp; &quot;quotes&quot;" in doc
    assert "a &lt; b &amp;&amp; c &gt; d" in doc
    assert "javascript:" not in doc
    assert "Night of &lt;b&gt;" in doc
    assert "about $1,000 lost" in doc
    assert 'datetime="2016-06-17"' in doc  # incident lands on the timeline
    assert "https://example.org/x" in doc


def test_cover_is_copied(tmp_path):
    data, d = _copy(tmp_path, LINGERING, keep=("facts.json", "verdict.json", "story.json"))
    (d / "shots").mkdir()
    (d / "shots" / "20171005074903.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (d / "shots" / "index.json").write_text(json.dumps([
        {"ts": "20171005074903", "url": "https://web.archive.org/web/20171005074903/https://gitcoin.co/",
         "file": "shots/20171005074903.png", "role": "cover", "site": "gitcoin.co"}]))
    p, doc = _render(tmp_path, LINGERING, data)
    assert (p.parent / "cover.png").read_bytes().startswith(b"\x89PNG")
    assert '<img src="cover.png"' in doc
    assert "5 Oct 2017" in doc and "gitcoin.co, captured by" in doc
    assert doc.count("https://web.archive.org/web/20171005074903/https://gitcoin.co/") == 1
    assert not re.search(r"https?://", _outside_smallprint(doc))


def test_render_all(tmp_path):
    paths = R.render_all(FIX, tmp_path / "out")
    assert {FRIENDLY, BAD, LINGERING} <= {p.parent.name for p in paths}
    assert len(paths) == len([d for d in FIX.iterdir() if (d / "facts.json").is_file()])


def test_reveal_has_unconditional_fallback(tmp_path):
    js = (R.TEMPLATE_DIR / "ghost.js").read_text()
    assert "setTimeout(revealAll, 1500);" in js
    # the fallback sits outside the observer branch, so it runs whatever the observer does
    tail = js[js.index("panels.forEach(function (p) { io.observe(p); });"):]
    assert tail.index("}\n") < tail.index("setTimeout(revealAll, 1500);")
    _, doc = _render(tmp_path, BAD)
    assert "setTimeout(revealAll, 1500);" in doc
    assert "<noscript><style>.reveal, .reveal .balloon { opacity: 1 !important; transform: none !important; }</style></noscript>" in doc


def test_real_story_honesty_line(tmp_path):
    shutil.copytree(FIX / FRIENDLY, tmp_path / "data" / FRIENDLY)
    sp = tmp_path / "data" / FRIENDLY / "story.json"
    s = json.loads(sp.read_text())
    s["model"] = {"id": "gemma4:12b-it-qat", "think": False, "seconds": 41.2, "prompt_tokens": 900, "output_tokens": 812}
    sp.write_text(json.dumps(s))
    _, doc = _render(tmp_path, FRIENDLY, tmp_path / "data")
    assert "The words on this page were written at runtime by gemma4:12b-it-qat on the author&#x27;s Mac, and code checked every date, number and name" in doc
    assert "41.2 s" in doc and "812 output tokens" in doc
    assert "Claude" not in doc and "closed model" not in doc
