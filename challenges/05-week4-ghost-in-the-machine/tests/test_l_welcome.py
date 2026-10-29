"""Lane L: first-visit welcome ("Hunt the ghost" on the index, "Light the candle" on ghost pages). No network."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ghosts import render as R

FIX = Path(__file__).parent / "fixtures" / "c1" / "ghosts"
BAD = "0xe82719202e5965cf5d9b6673b7503a3b92de20be"
ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "template"
HTML = (ROOT / "web" / "index.html").read_text()
JS = (TPL / "header.js").read_text()
GEOM = re.compile(r'\b(d|cx|cy|r|rx|ry|x|y|width|height|viewBox|transform)="([^"]*)"')
# sha256 of the storyteller's geometry attributes at commit 8823457 (before lane L)
STORYTELLER_GEOMETRY = "b879397e73d84e9df1b755cea16d0e1d794eeb2b5651da8dba6b5951d236adcd"


def test_header_js_has_the_flag_and_timings():
    assert '"eg-welcomed"' in JS and '"eg-welcome-tries"' in JS
    assert "WELCOME_HINT_MS = 8000" in JS and "WELCOME_GIVE_UP_MS = 20000" in JS
    assert "navigator.webdriver" in JS  # automated visits skip the welcome
    assert ".preventDefault(" not in JS  # the welcome never swallows a click
    assert "addEventListener(\"click\", onWelcomeClick, true)" in JS


def test_ghost_page_has_the_candle(tmp_path):
    doc = R.render(BAD, data_dir=FIX, out_dir=tmp_path / "out").read_text(encoding="utf-8")
    stage = doc[doc.index('<div class="title-stage">'):]
    assert re.search(r'<button type="button" class="eg-candle" aria-label="Light the candle"[^>]*hidden>', stage)
    assert 'aria-live="polite" data-candle="Light the candle"' in stage
    assert stage.index('class="teller"') < stage.index('class="eg-candle"')
    assert 'class="flame"' in doc
    assert R.Header().js in doc


def test_index_has_the_hunt():
    fly = HTML[HTML.index('<div class="fly">'):HTML.index('</div></div></div>')]
    assert re.search(r'<button type="button" class="eg-hunt" aria-label="Hunt the ghost[^"]*"[^>]*hidden>', fly)
    assert fly.index('class="eg-hunt"') < fly.index('class="bob"')  # sibling before .bob: hover glow via ~
    assert 'class="eg-candle eg-candle-solo"' in HTML  # reduced-motion variant
    assert 'data-hunt="Hunt the ghost"' in HTML and 'data-candle="Light the candle"' in HTML
    # the welcome markup must be parsed before the header script looks for it
    assert HTML.index('id="eg-line"') < HTML.index("<!-- header:start -->")
    assert JS in HTML


def test_storyteller_keeps_its_geometry():
    svg = (TPL / "characters" / "storyteller.svg").read_text()
    assert hashlib.sha256(repr(GEOM.findall(svg)).encode()).hexdigest() == STORYTELLER_GEOMETRY
    assert svg.count('class="flame"') == 2
