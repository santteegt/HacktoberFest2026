"""Lane C3: static checks on the gallery page (no browser, no network)."""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
HTML = (WEB / "index.html").read_text()
JS = (WEB / "assets" / "site.js").read_text()
CSS = (WEB / "assets" / "site.css").read_text()
NAME = "Ghosts in the Decentralized World Computer"


def test_title_and_kicker():
    assert re.search(r"<title>\s*" + NAME + r"\s*</title>", HTML)
    assert f'<p class="eyebrow">{NAME}</p>' in HTML


def test_papel_picado_strip_like_the_story_pages():
    picado = (WEB.parent / "template" / "characters" / "papel-picado.svg").read_text().strip()
    assert picado.replace("$uid", "index") in HTML
    assert "bunting" not in HTML and ".bunting" not in CSS


def test_no_closed_model_mention_but_honesty_lines_stay():
    text = (HTML + JS).lower()
    for gone in ("claude", "closed model", "designed once"):
        assert gone not in text
    for kept in ("Gemma 4", "Ethereum History", "Blockscout", "Sourcify", "Internet Archive",
                 "The model is local; the sources are not", "no historian prose", "suspected",
                 "Día de los Muertos", "MIT license"):
        assert kept in HTML


def test_toggles_legend_and_featured_slot():
    for bid in ("lights", "motion"):
        assert re.search(rf'<button type="button" class="switch" id="{bid}" aria-pressed="true">', HTML)
    assert 'id="featured"' in HTML and HTML.index('id="featured"') < HTML.index('class="controls"')
    legend = HTML[HTML.index('<aside class="legend"'):HTML.index("</aside>")]
    for tag in ("friendly", "lingering", "bad", "banished", "alive", "scarred", "never called"):
        assert f">{tag}</span>" in legend
    assert "kind-legend" not in HTML  # moved out of the About footer
    hjs = (WEB.parent / "template" / "header.js").read_text()  # the switches moved to the shared header
    assert hjs in HTML  # inlined by `ghosts gallery build`
    assert "ghosts/featured.json" in JS and "localStorage" in hjs
    assert hjs.count("try {") >= 2  # storage access is guarded
    assert "prefers-reduced-motion" in hjs and "prefers-reduced-motion" in CSS


def test_self_contained_and_text_only_dom():
    assert not re.search(r'<script[^>]+src="(https?:)?//', HTML)
    links = re.findall(r"<link [^>]*>", HTML)
    assert all('rel="canonical"' in l for l in links if re.search(r'href="(https?:)?//', l))
    assert "@import" not in CSS and "url(http" not in CSS
    assert "innerHTML" not in JS and "insertAdjacentHTML" not in JS


def test_unnamed_ghosts_get_a_label_and_a_short_address():
    assert '"Unknown ghost soul"' in JS and "g.unnamed" in JS
    assert "shortAddress(g.address)" in JS
    assert "g.address" in JS[JS.index("function haystack"):JS.index("function silentYears")]  # search keeps the full address


SITE = "https://eth-ghosts.decentraminds.tech"


def meta(attr, key):
    m = re.search(rf'<meta {attr}="{re.escape(key)}" content="([^"]*)">', HTML)
    assert m, key
    return m.group(1)


def test_link_preview_tags():
    assert meta("property", "og:type") == "website"
    assert meta("property", "og:site_name") == meta("property", "og:title") == NAME
    desc = meta("name", "description")
    assert desc == meta("property", "og:description") == meta("name", "twitter:description")
    assert desc.count(". ") == 0 and desc.endswith(".")  # one sentence
    assert meta("property", "og:url") == SITE + "/"
    assert meta("property", "og:image") == meta("name", "twitter:image") == SITE + "/assets/og.png"
    assert meta("property", "og:image:width") == "1200" and meta("property", "og:image:height") == "630"
    assert meta("property", "og:image:alt") and meta("name", "twitter:image:alt")
    assert meta("name", "twitter:card") == "summary_large_image"
    assert f'<link rel="canonical" href="{SITE}/">' in HTML
    assert '<link rel="icon" type="image/svg+xml" href="/favicon.svg">' in HTML


def test_og_image_and_its_source():
    png = (WEB / "assets" / "og.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")
    assert (w, h) == (1200, 630)
    src = (WEB / "assets" / "og-index.html").read_text()
    assert NAME in src and 'class="picado"' in src and 'class="ghost"' in src
    assert not re.search(r'(src|href)="(https?:)?//', src) and "url(http" not in src
