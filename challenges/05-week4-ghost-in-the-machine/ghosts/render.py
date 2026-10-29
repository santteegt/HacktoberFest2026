"""Render one ghost as a self-contained comic page: web/ghosts/<address>/index.html.

The template (template/ghost.html, panels.html, ghost.css, ghost.js, characters/*.svg) was designed once by a
Claude agent. Every word of story on the page comes from story.json, written at runtime by the local model.
This module only fills placeholders (string.Template) and escapes every value; it never writes prose of its own
beyond fixed labels and sentences built from facts.json / verdict.json numbers.
"""
from __future__ import annotations

import html
import itertools
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from string import Template
from urllib.parse import urlparse

from . import config

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template"
DEFAULT_OUT = config.ROOT / "web" / "ghosts"
SIZE_LIMIT = 300_000  # bytes, page without screenshots
DEFAULT_SITE_URL = "https://eth-ghosts.decentraminds.tech"  # the coordinator may move this to config.py
SITE_NAME = "Ghosts in the Decentralized World Computer"


def site_url() -> str:
    """Absolute base for canonical / Open Graph URLs: GHOSTS_SITE_URL or the default domain."""
    return (os.environ.get("GHOSTS_SITE_URL") or DEFAULT_SITE_URL).rstrip("/")

KINDS = {
    "friendly": "Friendly ghost",
    "lingering": "Lingering ghost",
    "bad": "Bad ghost",
    "banished": "Banished",
    "alive": "Not a ghost yet",
    "unknown": "Unclassified",
}
CHAPTER_NAMES = {
    "birth": "Birth", "life": "Life", "silence": "The silence", "knocking": "The knocking",
    "haunting": "The haunting", "buster": "Ghost buster",
}
ALIVE_CHAPTERS = {"birth", "life"}
ETH_GENESIS = date(2015, 7, 30)


# ---------------------------------------------------------------- small helpers

def e(x) -> str:
    return "" if x is None else html.escape(str(x), quote=True)


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"render: ignoring unreadable {path}: {exc}", file=sys.stderr)
        return None


def _d(x) -> dict:
    return x if isinstance(x, dict) else {}


def _l(x) -> list:
    return x if isinstance(x, list) else []


def _parse_date(ts) -> date | None:
    if not ts:
        return None
    s = str(ts).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s) or re.match(r"^(\d{4})(\d{2})(\d{2})\d{0,6}$", s)
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def _fmt_date(d: date | None) -> str:
    return f"{d.day} {d:%b %Y}" if d else "unknown"


def _fmt_int(n) -> str:
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "unknown"


def _fmt_eth(x) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "unknown"
    s = f"{v:,.6f}".rstrip("0").rstrip(".")
    return f"{s} ETH"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _short(addr: str | None) -> str:
    a = str(addr or "")
    return f"{a[:6]}…{a[-4:]}" if len(a) > 12 else a


def _safe_url(u) -> str | None:
    if not isinstance(u, str):
        return None
    p = urlparse(u.strip())
    return u.strip() if p.scheme in ("http", "https") and p.netloc else None


def ghost_name(f: dict) -> str:
    eh, bs, src, tok = _d(f.get("eh")), _d(f.get("blockscout")), _d(f.get("source")), _d(_d(f.get("eh")).get("token"))
    for cand in (f.get("name"), eh.get("name"), bs.get("name"), src.get("name"), tok.get("token_name")):
        if isinstance(cand, str) and cand.strip() and cand.isprintable() and len(cand.strip()) > 1:
            return cand.strip()
    return _short(f.get("address"))


class _Tpl:
    """Loads the master template, the panel fragments and the character SVGs once."""

    def __init__(self, root: Path = TEMPLATE_DIR):
        self.master = Template((root / "ghost.html").read_text(encoding="utf-8"))
        self.css = (root / "ghost.css").read_text(encoding="utf-8")
        self.js = (root / "ghost.js").read_text(encoding="utf-8")
        self.parts: dict[str, Template] = {}
        raw = (root / "panels.html").read_text(encoding="utf-8")
        for m in re.finditer(r"<!--@ (\w+) -->\n(.*?)(?=<!--@ |\Z)", raw, re.S):
            self.parts[m[1]] = Template(m[2].strip("\n"))
        self.svgs = {}
        for p in sorted((root / "characters").glob("*.svg")):
            s = p.read_text(encoding="utf-8")
            s = re.sub(r'\s+xmlns="[^"]*"', "", s, count=1).strip()
            self.svgs[p.stem] = Template(s)

    def part(self, name: str, **kw) -> str:
        return self.parts[name].substitute(**kw)


# ---------------------------------------------------------------- the renderer

class _Page:
    def __init__(self, tpl: _Tpl, folder: Path, out: Path):
        self.t = tpl
        self.folder = folder
        self.out = out
        self.f = _load(folder / "facts.json") or {}
        if not self.f:
            raise FileNotFoundError(f"no facts.json in {folder}")
        self.v = _load(folder / "verdict.json")
        self.s = _load(folder / "story.json")
        self.w = _load(folder / "wounds.json")
        self.shots = _load(folder / "shots" / "index.json")
        self.addr = str(self.f.get("address") or folder.name).lower()
        self.tag = self.addr[:6]
        self.name = ghost_name(self.f)
        kind = (_d(self.v).get("kind") or _d(self.s).get("kind") or "unknown")
        self.kind = kind if kind in KINDS else "unknown"
        self._ids = itertools.count(1)
        self.extra_sources: list[tuple[str, str]] = []

    # flags from facts / verdict
    @property
    def never_called(self) -> bool:
        return bool(_d(self.f.get("life")).get("never_called"))

    def tags(self) -> str:
        out = []
        if self.f.get("proxy") is True:
            out.append('<span class="chip tag">proxy</span>')
        n12 = _d(_d(self.v).get("activity")).get("last_12m_txs")
        if n12 is None:
            n12 = _d(self.f.get("life")).get("last_12m_txs")
        if self.kind == "bad" and isinstance(n12, (int, float)) and n12 >= 100:
            out.append('<span class="chip tag">still in use</span>')
        return "".join(out)

    def source_name(self) -> str | None:
        for n in _l(self.f.get("names")):
            n = _d(n)
            nm, src = n.get("name"), str(n.get("source") or "")
            if src.startswith("source") and isinstance(nm, str) and nm.strip() and nm.isprintable() and nm.strip() != self.name:
                return nm.strip()
        return None

    # characters
    def svg(self, name: str) -> str:
        return self.t.svgs[name].substitute(uid=f"svg{next(self._ids)}", tag=e(self.tag))

    def flyer(self, chapter_id: str | None = None) -> str:
        if self.kind == "alive" or (chapter_id in ALIVE_CHAPTERS):
            return self.svg("contract")
        return self.svg("ghost")

    # sections
    def title_panel(self) -> str:
        s, f = _d(self.s), self.f
        age = _d(f.get("age")).get("hardfork") or _d(f.get("age")).get("eh_era") or "unknown age"
        born = _parse_date(_d(f.get("birth")).get("timestamp"))
        last = _parse_date(_d(_d(f.get("life")).get("last_tx")).get("timestamp"))
        chips = [f'<li class="chip badge kind-{self.kind}">{e(KINDS[self.kind])}</li>']
        chips += [f"<li>{t}</li>" for t in re.findall(r"<span[^>]*>[^<]*</span>", self.tags())]
        chips.append(f'<li class="chip">Age: {e(age)}</li>')
        if born:
            chips.append(f'<li class="chip">Born {born.year}</li>')
        if self.never_called:
            chips.append('<li class="chip">Never called</li>')
        elif last:
            chips.append(f'<li class="chip">Last seen {last.year}</li>')
        stage = self.svg("storyteller")
        if self.kind == "banished":
            stage += self.svg("gravestone")
        stage += f'<div class="flight"><div class="flyer"><div class="bob">{self.flyer()}</div></div></div>'
        return self.t.part(
            "title",
            kicker=e(f"{self.name} · {age}"),
            title=e(s.get("title") or f"The ghost of {self.name}"),
            tagline=e(s.get("tagline") or "A ghost waiting for its storyteller."),
            chips="".join(chips),
            stage=stage,
        )

    def cover_panel(self) -> str:
        shots = [x for x in _l(self.shots) if isinstance(x, dict) and x.get("role") == "cover"]
        if not shots:
            return ""
        shot = shots[-1]
        f = shot.get("file") or ""
        cands = [Path(f)] if Path(f).is_absolute() else [self.folder / "shots" / f, self.folder / f, self.folder / "shots" / Path(f).name]
        src = next((c for c in cands if c.is_file()), None)
        if not src:
            print(f"render: cover {f!r} listed but not found for {self.addr}", file=sys.stderr)
            return ""
        self.out.mkdir(parents=True, exist_ok=True)
        dest = self.out / f"cover{src.suffix.lower() or '.png'}"
        shutil.copyfile(src, dest)
        when = _fmt_date(_parse_date(shot.get("ts")))
        url = _safe_url(shot.get("url"))
        orig = url or ""
        if url and urlparse(url).netloc == "web.archive.org":
            m = re.match(r"^https?://web\.archive\.org/web/[^/]+/(.+)$", url)
            orig = m[1] if m else ""
        elif url and shot.get("ts"):
            url = f"https://web.archive.org/web/{shot['ts']}/{url}"
        site = str(shot.get("site") or orig)
        host = urlparse(site if "://" in site else "//" + site).netloc.split(":")[0]
        if url:
            self.extra_sources.append((f"Wayback capture used for the cover ({host or 'site'}, {when})", url))
        return self.t.part(
            "cover",
            src=e(dest.name),
            alt=e(f"The {self.name} website{(' at ' + host) if host else ''} as the Wayback Machine captured it on {when}"),
            caption=e(f"{host or 'The dapp site'}, captured by the Internet Archive's Wayback Machine on {when}."),
        )

    def record_panel(self) -> str:
        f = self.f
        birth, life, chain = _d(f.get("birth")), _d(f.get("life")), _d(f.get("chain"))
        src, bs, eh, age = _d(f.get("source")), _d(f.get("blockscout")), _d(f.get("eh")), _d(f.get("age"))
        last = _d(life.get("last_tx"))
        rows: list[tuple[str, str]] = []
        tok = _d(eh.get("token"))
        aka = self.source_name()
        rows.append(("Name", e(self.name) + (f' <span class="mono">({e(tok["token_symbol"])})</span>' if tok.get("token_symbol") else "")
                     + (f'<small class="aka">source name: <span class="mono">{e(aka)}</span></small>' if aka else "")))
        born = _parse_date(birth.get("timestamp"))
        rows.append(("Born", f"{e(_fmt_date(born))}, block <span class=\"mono\">{e(_fmt_int(birth.get('block')))}</span>"))
        era = age.get("hardfork") or "unknown"
        if age.get("eh_era") and age.get("eh_era") != era:
            era = f"{era} (historian era: {age['eh_era']})"
        rows.append(("Age", e(era)))
        dep = birth.get("deployer") or bs.get("creator")
        rows.append(("Deployer", f'<span class="mono" title="{e(dep)}">{e(_short(dep))}</span>' if dep else "unknown"))
        if self.never_called:
            rows.append(("Never called", "Not one call has reached it since its birth."))
        elif last:
            status = "" if last.get("status") in (None, "ok") else f", status {last.get('status')}"
            rows.append(("Last seen", f"{e(_fmt_date(_parse_date(last.get('timestamp'))))} · <span class=\"mono\">{e(last.get('method') or 'unknown method')}</span>{e(status)}"))
        else:
            rows.append(("Last seen", "unknown"))
        calls = _fmt_int(life.get("tx_count"))
        if life.get("token_transfers"):
            calls += f" · {_fmt_int(life.get('token_transfers'))} token transfers"
        rows.append(("Lifetime calls", e(calls)))
        bal = chain.get("balance_eth", life.get("balance_eth"))
        rows.append(("Balance", e(_fmt_eth(bal))))
        if chain:
            code = f"present, {_fmt_int(chain.get('code_bytes'))} bytes" if chain.get("code_present") else "gone (selfdestructed)"
            rows.append(("Code on chain", e(code)))
        verified = bool(src.get("provider")) or bool(bs.get("is_verified"))
        how = []
        if src.get("provider"):
            how.append(f"{src['provider'].capitalize()} ({src.get('match') or 'match'})")
        if bs.get("is_verified"):
            how.append("Blockscout")
        ver = f'<span class="pill {"yes" if verified else "no"}">{"yes" if verified else "no"}</span>'
        if how:
            ver += " " + e(", ".join(how))
        rows.append(("Verified source", ver))
        rows.append(("Compiler", f'<span class="mono">{e(src.get("compiler_version") or "unknown")}</span>'))
        hist = _d(_d(self.v).get("labels")).get("historian_story")
        if hist is None:
            hist = bool(eh.get("short_description") or eh.get("description"))
        rows.append(("Historian story", f'<span class="pill {"yes" if hist else "no"}">{"yes" if hist else "no"}</span>'))
        rows_html = "\n".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
        reasons = [str(r) for r in _l(_d(self.v).get("reasons")) if r]
        if self.v:
            verdict = f'<span class="chip badge kind-{self.kind}">{e(KINDS[self.kind])}</span>' + self.tags() + e(" · ".join(reasons) or "no reason recorded")
        else:
            verdict = f'<span class="chip badge kind-unknown">{e(KINDS["unknown"])}</span>' + self.tags() + e("The classifier has not judged this ghost yet.")
        return self.t.part("record", address=e(self.addr), rows=rows_html, verdict=verdict)

    def code_card(self, code: str, start: int, label: str, tag: str, fix: bool = False) -> str:
        lines = str(code).replace("\r\n", "\n").rstrip("\n").split("\n")
        body = "".join(f'<span class="line"><span class="ln">{start + i}</span>{e(ln)}</span>' for i, ln in enumerate(lines))
        cls = "code-card fix" if fix else "code-card"
        return (f'<figure class="{cls}"><figcaption><span>{e(label)}</span><span class="tag">{e(tag)}</span></figcaption>'
                f'<pre tabindex="0" aria-label="{e(label + ", " + tag)}"><code>{body}</code></pre></figure>')

    def haunting_extra(self) -> str:
        out = []
        w = _d(self.w)
        inc = _d(w.get("incident"))
        if inc:
            loss = f", about ${_fmt_int(inc['loss_usd'])} lost" if inc.get("loss_usd") else ""
            out.append(f'<p class="incident"><strong>{e(inc.get("name") or "Incident")}</strong> · '
                       f'{e(_fmt_date(_parse_date(inc.get("date"))))}{e(loss)}. {e(inc.get("summary") or "")}</p>')
            for r in _l(inc.get("references")):
                if _safe_url(r):
                    self.extra_sources.append((f"Incident reference: {inc.get('name') or 'incident'}", r))
        findings = [x for x in _l(w.get("findings")) if isinstance(x, dict)]
        if findings:
            items = []
            for x in findings[:5]:
                conf = "confirmed" if x.get("confirmed") else "suspected"
                lines = _l(x.get("lines"))
                where = f"{x.get('file') or ''}" + (f", lines {lines[0]}-{lines[-1]}" if lines else "")
                meta = " · ".join(str(p) for p in (x.get("check"), x.get("swc"), f"impact {x.get('impact')}" if x.get("impact") else None,
                                                   f"confidence {x.get('confidence')}" if x.get("confidence") else None, where or None) if p)
                items.append(f'<li class="wound"><strong>{e(x.get("title") or x.get("check") or "Wound")} '
                             f'<span class="pill {conf}">{conf}</span></strong><span class="meta">{e(meta)}</span>'
                             + (f'<br>{e(x["description"])}' if x.get("description") else "") + "</li>")
                if _safe_url(x.get("reference_url")):
                    self.extra_sources.append((f"Reference for {x.get('check') or 'wound'}", x["reference_url"]))
            tier = w.get("tier")
            out.append(f'<h3 class="visually-hidden">Wounds</h3><ul class="wounds" aria-label="Wounds found by {e(tier or "the analyzer")}">{"".join(items)}</ul>')
        snip = _d(_d(self.s).get("scary")).get("snippet")
        snip = _d(snip)
        if not snip.get("code"):
            first = next((x for x in findings if x.get("snippet")), None)
            if first:
                snip = {"file": first.get("file"), "lines": first.get("lines"), "code": first.get("snippet")}
        if snip.get("code"):
            lines = _l(snip.get("lines"))
            start = int(lines[0]) if lines and str(lines[0]).isdigit() else 1
            label = f"{snip.get('file') or 'source'}" + (f", lines {lines[0]}-{lines[-1]}" if lines else "")
            out.append(self.code_card(snip["code"], start, label, "the guilty code"))
        return "\n".join(out)

    def buster_extra(self) -> str:
        buster = _d(_d(self.s).get("buster"))
        fix = _d(buster.get("fix"))
        if not fix.get("code"):
            reason = buster.get("fix_reason")
            if isinstance(reason, str) and reason.strip():
                return f'<aside class="fix-note" role="note"><strong>Why there is no code fix</strong>{e(reason.strip())}</aside>'
            return ""
        ver = fix.get("version") or "0.8.38"
        lang = (fix.get("language") or "solidity").capitalize()
        compiled = "yes" if fix.get("compiled") else "no"
        out = self.code_card(fix["code"], 1, "the fix", f"{lang} {ver}, compiled: {compiled}", fix=True)
        if fix.get("compiler_output") and not fix.get("compiled"):
            out += f'<p class="cited">Compiler said: <code>{e(str(fix["compiler_output"])[:600])}</code></p>'
        return out

    def chapter_panel(self, i: int, cid: str, heading: str, balloons: list[tuple[str, str]], cited: list, extra: str = "",
                      variant: str | None = None) -> str:
        bl = "\n".join(f'<p class="balloon {cls}">{e(t)}</p>' for cls, t in balloons)
        if cited:
            bl += '\n<p class="cited">Grounded in: ' + ", ".join(f"<code>{e(c)}</code>" for c in cited[:8]) + "</p>"
        name = variant.strip().capitalize() if isinstance(variant, str) and variant.strip() else CHAPTER_NAMES.get(cid, cid.replace("_", " ").capitalize())
        label = f"Chapter {i} · {name}" if i else "Waiting"
        busted = cid == "buster"
        return self.t.part(
            "chapter",
            tilt="tilt-l" if i % 2 else "tilt-r",
            extra_class="busted" if busted else "",
            cid=e(f"{cid}-{i}"),
            label=e(label),
            heading=e(heading),
            beam='<div class="beam" aria-hidden="true"></div>' if busted else "",
            flyer=self.flyer(cid),
            teller=self.svg("storyteller"),
            balloons=bl,
            extra=extra,
        )

    def chapters(self) -> str:
        s = _d(self.s)
        chapters = [c for c in _l(s.get("chapters")) if isinstance(c, dict)]
        scary, buster = _d(s.get("scary")), _d(s.get("buster"))
        ids = [str(c.get("id") or "") for c in chapters]
        has_wounds = bool(_l(_d(self.w).get("findings")) or _d(self.w).get("incident"))
        if (scary or (self.kind == "bad" and has_wounds)) and "haunting" not in ids:
            chapters.append({"id": "haunting", "heading": "The haunting", "paragraphs": []})
        if buster and "buster" not in ids:
            chapters.append({"id": "buster", "heading": "Who you gonna call", "paragraphs": []})
        if not chapters:
            return self.chapter_panel(0, "waiting", "The storyteller has not spoken yet",
                                      [("whisper", "The storyteller has not spoken yet. Until the candle is lit, the chain's own record below is all this ghost will say.")], [])
        out = []
        for i, c in enumerate(chapters, 1):
            cid = str(c.get("id") or f"chapter{i}")
            paras = [p for p in _l(c.get("paragraphs")) if isinstance(p, str) and p.strip()]
            balloons = [("", p) for p in paras]
            extra = ""
            if cid == "haunting":
                balloons += [("scary", p) for p in _l(scary.get("paragraphs")) if isinstance(p, str) and p.strip() and p not in paras]
                extra = self.haunting_extra()
            elif cid == "buster":
                balloons += [("buster", p) for p in _l(buster.get("paragraphs")) if isinstance(p, str) and p.strip() and p not in paras]
                extra = self.buster_extra()
            if not balloons:
                balloons = [("whisper", "The storyteller has not spoken this part yet.")]
            heading = c.get("heading") or CHAPTER_NAMES.get(cid, cid.capitalize())
            out.append(self.chapter_panel(i, cid, heading, balloons, [str(x) for x in _l(c.get("facts_cited"))], extra, c.get("variant")))
        return "\n".join(out)

    def timeline_panel(self) -> str:
        f, v = self.f, _d(self.v)
        birth, life = _d(f.get("birth")), _d(f.get("life"))
        last = _d(life.get("last_tx"))
        born = _parse_date(birth.get("timestamp"))
        ev: list[tuple[date, str, str]] = []
        age = _d(f.get("age")).get("hardfork")
        if born:
            ev.append((born, "ev-born", f"Born in block {_fmt_int(birth.get('block'))}" + (f", {age} age" if age else "")))
        for site in [x for x in _l(f.get("sites")) if isinstance(x, dict)][:2]:
            host = str(site.get("host") or "")
            host = urlparse(host).netloc + urlparse(host).path.rstrip("/") if "://" in host else host
            fo, lo = _parse_date(site.get("first_ok")), _parse_date(site.get("last_ok"))
            if fo and fo >= ETH_GENESIS:
                ev.append((fo, "ev-site", f"{host} first archived alive"))
            if lo and lo >= ETH_GENESIS and lo != fo:
                ev.append((lo, "ev-site", f"{host} last archived alive"))
        inc = _d(_d(self.w).get("incident"))
        inc_d = _parse_date(inc.get("date"))
        if inc_d:
            ev.append((inc_d, "ev-incident", f"The haunting: {inc.get('name') or 'incident'}"))
        last_d = _parse_date(last.get("timestamp"))
        method = last.get("method") or "a call"
        if last_d:
            if self.kind in ("friendly", "banished", "unknown"):
                ev.append((last_d, "ev-ghost", f"Last call ({method}); the silence begins"))
            elif self.kind == "lingering":
                ev.append((last_d, "ev-last", f"Latest knock: {method}"))
            else:
                ev.append((last_d, "ev-last", f"Last call: {method}"))
        if self.never_called:
            ev = [(born, "ev-born", f"Born in block {_fmt_int(birth.get('block'))}; nobody ever knocked")] if born else []
        ev.sort(key=lambda x: x[0])

        act = _d(v.get("activity"))
        silent = act.get("silent_years")
        if silent is None and last_d:
            ref = _parse_date(v.get("decided_at") or f.get("fetched_at")) or date.today()
            silent = round((ref - last_d).days / 365.25, 1)
        n12 = act.get("last_12m_txs")
        capped = "+" if act.get("last_12m_capped") else ""
        if self.never_called:
            moment = f"Nobody ever knocked: not one call reached it after its birth on {_fmt_date(born)}."
        elif self.kind == "friendly":
            moment = f"It became a ghost after its last call on {_fmt_date(last_d)}. The chain has been quiet for {silent} years."
        elif self.kind == "lingering":
            knocks = f"{_fmt_int(n12)}{capped} calls in the last 12 months" if n12 is not None else "a few calls still arrive"
            moment = f"Its dapp is gone, but people still knock: {knocks}. Latest knock: {_fmt_date(last_d)}."
        elif self.kind == "bad":
            if inc_d:
                moment = f"It turned bad on {_fmt_date(inc_d)}: {inc.get('name') or 'the incident'}."
            else:
                worst = _d(v.get("wounds")).get("worst_impact")
                moment = "It carries a wound in its code" + (f" (worst impact: {worst})" if worst else "") + f". Last call: {_fmt_date(last_d)}."
        elif self.kind == "banished":
            moment = f"It was banished: its code is gone from the chain. Last call: {_fmt_date(last_d)}."
        elif self.kind == "alive":
            moment = f"Not a ghost yet: {_fmt_int(n12)}{capped} calls in the last 12 months."
        else:
            moment = f"Not classified yet. Last call: {_fmt_date(last_d)}."

        track = ""
        if len(ev) == 1:
            d, cls, label = ev[0]
            track = f'<span class="mark {cls}" style="left:0%" title="{e(label)}"></span><span class="yr first" style="left:0">{d.year}</span>'
        elif len(ev) >= 2:
            lo, hi = ev[0][0], ev[-1][0]
            span = max((hi - lo).days, 1)
            for d, cls, label in ev:
                pct = round(100 * (d - lo).days / span, 2)
                track += f'<span class="mark {cls}" style="left:{pct}%" title="{e(label)}"></span>'
            track += f'<span class="yr first" style="left:0">{lo.year}</span><span class="yr last" style="left:100%">{hi.year}</span>'
        events = "".join(f'<li class="{cls}"><time datetime="{d.isoformat()}">{e(_fmt_date(d))}</time><span>{e(label)}</span></li>' for d, cls, label in ev)
        return self.t.part("timeline", moment=e(moment), track=track, events=events)

    def closing_panel(self) -> str:
        s = _d(self.s)
        vf = _d(s.get("verifier"))
        if not s:
            return self.t.part("closing", tally="", tally_line=e("The storyteller has not spoken yet, so there is nothing to count."), dropped="")
        n = {k: int(vf.get(k) or 0) for k in ("sentences", "grounded", "repaired", "dropped")}
        tally = "".join(f"<li><b>{n[k]}</b><span>{k}</span></li>" for k in ("sentences", "grounded", "repaired", "dropped"))
        line = (f"The storyteller spoke {_plural(n['sentences'], 'sentence')}; {n['grounded']} grounded, "
                f"{n['repaired']} repaired, {n['dropped']} dropped.")
        dropped_text = [t for t in _l(vf.get("dropped_text")) if isinstance(t, str) and t.strip()]
        dropped = ""
        if dropped_text:
            dropped = ('<p>Struck from the story, because a date, number or name in it is not in the facts:</p>'
                       '<ul class="dropped">' + "".join(f"<li><s>{e(t)}</s></li>" for t in dropped_text) + "</ul>")
        return self.t.part("closing", tally=tally, tally_line=e(line), dropped=dropped)

    def sources(self) -> str:
        f, a = self.f, self.addr
        used = set(_l(f.get("sources_used")))
        src = _d(f.get("source"))
        links: list[tuple[str, str]] = []
        if "ethereumhistory" in used or f.get("eh"):
            links.append(("Ethereum History: the contract's page", f"https://www.ethereumhistory.com/contract/{a}"))
        if "blockscout" in used or f.get("blockscout"):
            links.append(("Blockscout: transactions, balance and verification", f"https://eth.blockscout.com/address/{a}"))
        if src.get("provider") == "sourcify":
            links.append(("Sourcify: verified source", f"https://repo.sourcify.dev/1/{a}"))
        for site in [x for x in _l(f.get("sites")) if isinstance(x, dict)]:
            host = str(site.get("host") or "")
            for key, word in (("first_ok", "first"), ("last_ok", "last")):
                ts = site.get(key)
                if ts and _parse_date(ts) and _parse_date(ts) >= ETH_GENESIS:
                    links.append((f"Wayback Machine, {word} live capture of {host} ({_fmt_date(_parse_date(ts))})",
                                  f"https://web.archive.org/web/{ts}/{host}"))
        for lk in _l(_d(f.get("eh")).get("links")):
            if isinstance(lk, dict) and _safe_url(lk.get("url")):
                links.append((f"Historian's link: {lk.get('title') or lk['url']}", lk["url"]))
        links += self.extra_sources
        seen, items = set(), []
        for label, url in links:
            url = _safe_url(url)
            if not url or url in seen:
                continue
            seen.add(url)
            items.append(f'<li><a href="{e(url)}" rel="noopener">{e(label)}</a></li>')
        if "rpc" in used:
            items.append("<li>A public Ethereum JSON-RPC node: is the code still there, and the balance</li>")
        return "".join(items)

    def smallprint(self) -> str:
        s = _d(self.s)
        m = _d(s.get("model"))
        mid = str(m.get("id") or "")
        fixture = mid.startswith("fixture")
        if not s:
            model_line = "No story yet: this page shows the code-verified facts only."
        elif fixture:
            model_line = "This page shows a hand-written test fixture, not model output: no model wrote these sentences."
        else:
            bits = [f"Story written by {mid or 'an unnamed model'} running locally through Ollama"]
            if m.get("think") is False:
                bits.append("thinking off")
            if m.get("seconds"):
                bits.append(f"{float(m['seconds']):.1f} s")
            if m.get("output_tokens"):
                bits.append(f"{_fmt_int(m['output_tokens'])} output tokens")
            model_line = ", ".join(bits) + "."
        if s and not fixture:
            honest = (f"The words on this page were written at runtime by {mid or 'an open-weight model'} on the author's Mac, "
                      "and code checked every date, number and name it wrote against the facts on this page; sentences that failed were repaired or dropped.")
        elif fixture:
            honest = "The words on this sample were written by hand to test the template; real pages carry the local model's story."
        else:
            honest = "No model has written about this ghost yet."
        generated = _fmt_date(_parse_date(s.get("generated_at") or _d(self.v).get("decided_at") or self.f.get("fetched_at")))
        return self.t.part("smallprint", model_line=e(model_line), honest=e(honest), sources=self.sources(),
                           generated=e(generated), address=e(self.addr), chain_id=e(self.f.get("chain_id") or 1))

    @property
    def display_name(self) -> str:
        """The name for previews: 'Unknown ghost soul 0xc820…6adf' when the only name is the address."""
        n = self.name.strip().lower()
        if n in (self.addr, _short(self.addr).lower()):
            return f"Unknown ghost soul {_short(self.addr)}"
        return self.name

    def meta(self) -> dict:
        s, f = _d(self.s), self.f
        age = _d(f.get("age")).get("hardfork") or _d(f.get("age")).get("eh_era") or "unknown age"
        born = _parse_date(_d(f.get("birth")).get("timestamp"))
        title = s.get("title") or self.display_name
        desc = s.get("tagline") or f"{KINDS[self.kind]} · {age} age · born {_fmt_date(born)}: {self.display_name}, an old Ethereum contract."
        base = site_url()
        return {
            "title": str(title), "description": str(desc), "age": str(age), "born": born,
            "url": f"{base}/ghosts/{self.addr}/", "image": f"{base}/ghosts/{self.addr}/og.png",
            "image_alt": f"{KINDS[self.kind]}: {title}. {self.display_name}, {age} age.",
        }

    def build(self) -> str:
        s = _d(self.s)
        m = self.meta()
        panels = [self.title_panel(), self.cover_panel(), self.record_panel(), self.chapters(), self.timeline_panel(), self.closing_panel()]
        title = s.get("title") or f"The ghost of {self.name}"
        return self.t.master.substitute(
            page_title=e(f"{title} · {self.name}"),
            description=e(m["description"]),
            site_name=e(SITE_NAME),
            og_title=e(m["title"]),
            og_url=e(m["url"]),
            og_image=e(m["image"]),
            og_image_alt=e(m["image_alt"]),
            model_id=e(_d(s.get("model")).get("id") or "no model yet"),
            kind=self.kind,
            css=self.t.css,
            js=self.t.js,
            picado=self.svg("papel-picado"),
            panels="\n".join(p for p in panels if p),
            smallprint=self.smallprint(),
        )


def render(address: str, data_dir: Path | str | None = None, out_dir: Path | str | None = None) -> Path:
    """Render data/ghosts/<address>/ into <out_dir>/<address>/index.html and return that path."""
    data_dir = Path(data_dir) if data_dir else config.GHOSTS_DIR
    out_root = Path(out_dir) if out_dir else DEFAULT_OUT
    addr = address.strip().lower()
    folder = data_dir / addr
    if not folder.is_dir():
        hits = [p for p in data_dir.iterdir() if p.is_dir() and p.name.lower() == addr] if data_dir.is_dir() else []
        if not hits:
            raise FileNotFoundError(f"no ghost folder for {address} in {data_dir}")
        folder = hits[0]
    out = out_root / addr
    page = _Page(_Tpl(), folder, out)
    doc = page.build()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "index.html"
    path.write_text(doc, encoding="utf-8")
    size = len(doc.encode("utf-8"))
    if size > SIZE_LIMIT:
        print(f"render: warning, {path} is {size:,} bytes (limit {SIZE_LIMIT:,})", file=sys.stderr)
    return path


def render_all(data_dir: Path | str | None = None, out_dir: Path | str | None = None) -> list[Path]:
    """Render every data/ghosts/<address>/ that has a facts.json. Failures are reported and skipped."""
    data_dir = Path(data_dir) if data_dir else config.GHOSTS_DIR
    done = []
    for folder in sorted(p for p in data_dir.iterdir() if (p / "facts.json").is_file()):
        try:
            done.append(render(folder.name, data_dir, out_dir))
        except Exception as exc:  # keep the nightly run going
            print(f"render: {folder.name} failed: {exc}", file=sys.stderr)
    return done
