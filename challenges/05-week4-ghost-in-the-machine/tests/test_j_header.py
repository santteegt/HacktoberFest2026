"""Lane J: shared header, storyteller constant, ofrenda link, gallery labels and About. No network."""
from __future__ import annotations

import re
from pathlib import Path

from ghosts import gallery, render as R

FIX = Path(__file__).parent / "fixtures" / "c1" / "ghosts"
BAD = "0xe82719202e5965cf5d9b6673b7503a3b92de20be"
LINGERING = "0x2af47a65da8cd66729b4209c22017d6a5c2d2400"
WEB = Path(__file__).resolve().parent.parent / "web"
HTML = (WEB / "index.html").read_text()


def _doc(tmp_path, addr=BAD):
    return R.render(addr, data_dir=FIX, out_dir=tmp_path / "out").read_text(encoding="utf-8")


def test_storyteller_constant_drives_the_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "STORYTELLER_NAME", "La Catrina")
    doc = _doc(tmp_path)
    assert '<p class="speaker">La Catrina</p>' in doc
    assert "What La Catrina was allowed to say" in doc
    assert "<small>La Catrina checked facts</small>Based on a True Story" in doc
    assert "La Catrina spoke" in doc
    assert '<p class="speaker">The storyteller</p>' not in doc


def test_ghost_page_has_the_shared_header(tmp_path):
    doc = _doc(tmp_path)
    assert 'id="eg-header" data-assets="../../assets/"' in doc
    for bid, label in (("effects", "Effects"), ("lights", "Lights"), ("motion", "Animation")):
        assert re.search(rf'id="{bid}" aria-pressed="true">.*?{label}</button>', doc)
    assert "&larr; All the ghosts" in doc
    assert f'<span class="eg-brand">{R.SITE_NAME}</span>' in doc
    assert 'id="about-open"' not in doc  # About is gallery-only
    hdr = R.Header()
    assert hdr.css in doc and hdr.js in doc
    assert doc.index(hdr.js) < doc.index("Ghost page behavior")  # window.EG exists before ghost.js runs
    assert "Claude" not in doc


def test_ofrenda_link_and_true_story_card(tmp_path):
    doc = _doc(tmp_path, LINGERING)
    link = re.search(r'<a class="copy eh-link"[^>]*>', doc)[0]
    assert f'href="https://www.ethereumhistory.com/contract/{LINGERING}"' in link
    assert 'target="_blank"' in link and 'rel="noopener noreferrer"' in link
    assert 'aria-label="Open in Ethereum History"' in link and 'title="Open in Ethereum History"' in link
    assert doc.index('class="copy"') < doc.index('class="copy eh-link"')  # side by side, Copy first
    foot = re.search(r'<footer class="smallprint".*?</footer>', doc, re.S)[0]
    card = re.search(r'<section class="panel truestory".*?</section>', foot, re.S)[0]
    assert "Based on a True Story" in card and "Sources used for this ghost:" in card
    assert "test fixture" in card  # the model line moved into the card
    assert "Generated " in foot.split("</section>")[1]  # the rest stays small print


def test_gallery_header_labels_and_about():
    hdr = R.Header()
    assert hdr.index_block() in HTML  # what `ghosts gallery build` writes
    assert 'data-assets="assets/"' in HTML
    assert 'id="legend-toggle" aria-expanded="false" aria-controls="legend-list">Types</button>' in HTML
    assert re.search(r'id="motion" aria-pressed="true">.*?Animation</button>', HTML)
    assert "Ghost flies" not in HTML and ">Key<" not in HTML
    about = HTML[HTML.index('<dialog class="about-dialog"'):HTML.index("</dialog>")]
    assert HTML.index('id="about-open"') < HTML.index('id="effects"')  # About sits left of the switches
    assert "Built for the Hacktoberfest 2026 &ldquo;Ghost in the Machine&rdquo; challenge." in about
    assert "<h3>Thanks</h3>" in about and "https://www.ethereumhistory.com" in about and "MCP server" in about
    for credit in ("Music track: Haunted House by Aetheric", "https://freetouse.com/music",
                   '>Jusatti890</a> from <a href="https://pixabay.com/sound-effects//?', ">Ghostie Graves</a>"):
        assert credit in about
    lede = HTML[HTML.index('<p class="lede">'):HTML.index("</p>", HTML.index('<p class="lede">'))]
    assert "Built for" not in lede
    assert HTML.count("The model is local; the sources are not") == 1  # no duplicated About prose


def test_inject_is_idempotent(tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<body>\n<!-- header:start -->\nSTALE-HEADER\n<!-- header:end -->\n</body>\n")
    assert gallery.inject_header(page) is True
    once = page.read_text()
    assert "STALE-HEADER" not in once and 'id="eg-header"' in once
    assert gallery.inject_header(page) is False and page.read_text() == once
    plain = tmp_path / "plain.html"
    plain.write_text("<body></body>")
    assert gallery.inject_header(plain) is False
