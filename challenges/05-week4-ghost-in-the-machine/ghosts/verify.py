"""Deterministic grounding checker for model-written sentences.

The facts (facts.json, plus verdict.json, wounds.json and code-derived values) are flattened into leaves. A sentence is
`grounded` when every checkable token in it appears in those leaves:

- every 4-digit year, every date (month + day, month + year, ISO), every month name;
- every number with more than one digit (also number words such as "twenty-one"), every ETH amount (any size);
- every capitalized multi-word name ("Kieran Elby", "King of the Ether Throne"), every camelCase or `call()` identifier,
  every 0x hex string, every version string (0.4.18), every quoted phrase.

Numbers match when rounding the fact to the precision the sentence shows gives the same value (83.0 matches 83.001304,
"19,000" matches 19461 because it shows two significant digits, "2.4 billion" matches 2425858453), or when the sentence
shows a whole number equal to the fact's floor (10 years for 10.7). The check is lexical: it proves the checkable parts of a
sentence came from the facts, not that the sentence is true.
"""
from __future__ import annotations
import math
import re
import unicodedata
from dataclasses import dataclass, field

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
_MON_ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}
MONTH_NUM = {m: i + 1 for i, m in enumerate(MONTHS)} | _MON_ABBR
_MON_RE = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\.?"
_WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}

# Phrases the storyteller may always use: the project's own frame, not facts about the ghost.
ALLOW_NAMES = {"día de los muertos", "dia de los muertos", "day of the dead", "all souls", "ethereum history", "internet archive",
               "wayback machine", "ghost buster", "ghost busters", "solidity", "ethereum"}

_HEX = re.compile(r"0x[0-9a-fA-F]{4,}")
_SHORT_HEX = re.compile(r"(0x[0-9a-fA-F]{2,})(?:…|\.\.\.)([0-9a-fA-F]{2,})\b")
_VERSION = re.compile(r"\bv?\d+\.\d+\.\d+(?:[-+][\w.]+)?\b")
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})")
_WAYBACK = re.compile(r"^(\d{4})(\d{2})(\d{2})\d{6}$")
_DATE_MDY = re.compile(rf"\b({_MON_RE})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*[–-]\s*(\d{{1,2}}))?(?:,?\s+(\d{{4}}))?\b")
_DATE_DMY = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MON_RE})(?:,?\s+(\d{{4}}))?\b")
_DATE_MY = re.compile(rf"\b({_MON_RE})(?:\s+of)?,?\s+(\d{{4}})\b")
_MONTH_ALONE = re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b")
_NUM = re.compile(r"(?<![\w.])(\$)?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?:st|nd|rd|th)?(\s*(?:%|percent))?"
                  r"(?:\s+(thousand|million|billion)|([kKMB])\b)?(?:\s*(ETH|Ether|ether|finney|gwei|wei)\b)?(?![\w])")
_QUOTED = re.compile(r"\"([^\"]{2,200})\"|“([^”]{2,200})”|(?<![\w])‘((?:[^’\n]|’(?=\w)){2,200}?)’(?![\w])|(?<![\w])'((?:[^'\n]|'(?=\w)){3,200}?)'(?![\w])")
_CODE_TICK = re.compile(r"`([^`]{1,120})`")
_IDENT = re.compile(r"\b(?:[a-z]+[A-Z]\w*|[A-Z][a-z0-9]+[A-Z]\w*|\w+\(\))")
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][\wÀ-ÖØ-öø-ÿ'’.&-]*")
_CONNECTORS = {"of", "the", "de", "los", "la", "del", "von", "van", "da"}
_STARTERS = {"the", "a", "an", "in", "on", "at", "for", "but", "and", "then", "when", "once", "it", "its", "this", "that", "there",
             "here", "now", "so", "yet", "still", "after", "before", "by", "from", "with", "as", "while", "since", "every",
             "each", "no", "some", "his", "her", "their", "our", "my", "your", "today", "tonight", "long", "years", "one", "only",
             "because", "though", "although", "if", "where", "what", "who", "why", "how", "until", "even", "not", "nor", "or",
             "i", "we", "you", "he", "she", "they", "these", "those", "all", "few", "many", "more", "most", "once", "twice",
             "o", "oh", "ah", "listen", "look", "come", "behold", "remember", "beware", "hush", "see", "now,"}
_SMALL = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
          "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
          "eighteen": 18, "nineteen": 19}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_SCALES = {"hundred": 100, "thousand": 1000, "million": 10**6, "billion": 10**9}
_NUMWORD_RE = re.compile(r"\b(?:(?:" + "|".join(list(_SMALL) + list(_TENS) + list(_SCALES)) + r")(?:[\s-]+(?:and[\s-]+)?)?)+", re.I)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def flatten(obj, prefix: str = "") -> list[tuple[str, object]]:
    """Leaves of a JSON-like object as (dotted.path, value). Lists use [i]."""
    out: list[tuple[str, object]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += flatten(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            out += flatten(v, f"{prefix}[{i}]")
    elif obj is not None and obj != "":
        out.append((prefix, obj))
    return out


def _month(tok: str) -> int:
    return MONTH_NUM[tok.lower().rstrip(".")]


def dates_in_text(text: str) -> tuple[set, set, set]:
    """(full dates (y,m,d) and partial (None,m,d)), (y,m), months found in free text."""
    full, ym, months = set(), set(), set()
    for y, m, d in _ISO_DATE.findall(text):
        full.add((int(y), int(m), int(d))); ym.add((int(y), int(m))); months.add(int(m))
    for mon, d1, d2, y in _DATE_MDY.findall(text):
        m = _month(mon)
        for d in filter(None, (d1, d2)):
            full.add((int(y) if y else None, m, int(d)))
        if y:
            ym.add((int(y), m))
        months.add(m)
    for d, mon, y in _DATE_DMY.findall(text):
        m = _month(mon)
        full.add((int(y) if y else None, m, int(d))); months.add(m)
        if y:
            ym.add((int(y), m))
    for mon, y in _DATE_MY.findall(text):
        ym.add((int(y), _month(mon))); months.add(_month(mon))
    for mon in _MONTH_ALONE.findall(text):
        months.add(_month(mon))
    return full, ym, months


def _words_to_numbers(text: str) -> list[tuple[str, int]]:
    out = []
    for m in _NUMWORD_RE.finditer(text):
        words = [w for w in re.split(r"[\s-]+", m.group(0).lower()) if w and w != "and"]
        if not words or all(w in _SCALES for w in words):
            continue
        total, cur = 0, 0
        for w in words:
            if w in _SMALL:
                cur += _SMALL[w]
            elif w in _TENS:
                cur += _TENS[w]
            elif w == "hundred":
                cur = (cur or 1) * 100
            else:
                total += (cur or 1) * _SCALES[w]; cur = 0
        out.append((m.group(0).strip(), total + cur))
    return out


@dataclass
class FactIndex:
    leaves: list[tuple[str, object]] = field(default_factory=list)
    text: str = ""
    numbers: list[tuple[float, str]] = field(default_factory=list)
    dates: dict = field(default_factory=dict)      # (y,m,d) -> path ; (None,m,d) too
    year_months: dict = field(default_factory=dict)
    months: dict = field(default_factory=dict)
    strings: list[tuple[str, str]] = field(default_factory=list)  # (path, normalized string)

    @classmethod
    def build(cls, **docs) -> "FactIndex":
        """docs: name -> JSON-like object (facts=..., verdict=..., wounds=..., derived=..., extra=[str, ...])."""
        ix = cls()
        for name, doc in docs.items():
            if doc is None:
                continue
            ix.leaves += flatten(doc, name)
        parts, text_numbers = [], []
        for path, v in ix.leaves:
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                ix.numbers.append((float(v), path))
                continue
            s = str(v)
            ix.strings.append((path, norm(s)))
            parts.append(norm(s))
            w = _WAYBACK.match(s)
            if w:
                y, m, d = map(int, w.groups())
                ix._add_date(y, m, d, path)
                ix.numbers.append((float(y), path))
                continue
            if _HEX.fullmatch(s.strip()):
                # "a wallet ending in 7645": the visible ends of an address may be quoted on their own
                for part in (s.strip()[2:6], s.strip()[-4:]):
                    if part.isdigit():
                        text_numbers.append((float(part), path))
                continue
            if not re.search(r"\s", s.strip()):
                # one token: a pure number ("2022") counts; timestamps give dates only; hosts, paths, ids give nothing
                if re.fullmatch(r"-?\d+(?:\.\d+)?", s.strip()):
                    text_numbers.append((float(s), path))
                for (y, m, d) in dates_in_text(s)[0]:
                    ix._add_date(y, m, d, path)
                continue
            full, ym, months = dates_in_text(s)
            for (y, m, d) in full:
                ix._add_date(y, m, d, path)
            for (y, m) in ym:
                ix.year_months.setdefault((y, m), path); ix.months.setdefault(m, path)
            for m in months:
                ix.months.setdefault(m, path)
            scrubbed = _VERSION.sub(" ", _HEX.sub(" ", re.sub(r"\d{4}-\d{2}-\d{2}T[\d:.]+Z?", " ", s)))
            scrubbed = re.sub(r"\S+[/@]\S+", " ", scrubbed)  # urls and paths
            for _, val, unit in _scan_numbers(scrubbed):
                text_numbers.append((val, path))
            for _, val in _words_to_numbers(scrubbed):
                text_numbers.append((float(val), path))
        ix.numbers += text_numbers
        ix.text = " | ".join(parts)
        return ix

    def _add_date(self, y, m, d, path):
        self.dates.setdefault((y, m, d), path)
        self.dates.setdefault((None, m, d), path)
        if y:
            self.year_months.setdefault((y, m), path)
            self.numbers.append((float(y), path))
        self.months.setdefault(m, path)

    def has_text(self, phrase: str) -> str | None:
        p = norm(phrase).strip(" .,;:!?\"'")
        if not p:
            return ""
        for path, s in self.strings:
            if p in s:
                return path
        return None

    def match_number(self, value: float, decimals: int, unit: float, exact: bool) -> str | None:
        """Exact value first (best citation), then rounding to the shown precision, then the floor of a whole number."""
        for f, path in self.numbers:
            if abs(f - value) < 1e-9:
                return path
        if exact:
            return None
        for f, path in self.numbers:
            if round(f / unit) == round(value / unit) and abs(f - value) <= unit:
                return path
        if decimals == 0 and unit == 1:
            for f, path in self.numbers:
                if math.floor(f) == value:
                    return path
        return None


def _scan_numbers(text: str):
    """Yield (token, value, meta) for each number in text. meta = dict(decimals, unit, eth, money, raw_digits, scale)."""
    for m in _NUM.finditer(text):
        dollar, whole, frac, pct, scale, short, eth = m.groups()
        val = float(whole.replace(",", "") + ("." + frac if frac else ""))
        mult = _SCALES.get((scale or "").lower(), 1)
        if short:
            mult = {"k": 1000, "m": 10**6, "b": 10**9}[short.lower()]
        yield m.group(0).strip(), val * mult, {"decimals": len(frac or ""), "scale": mult, "eth": bool(eth),
                                               "whole": whole.replace(",", ""), "frac": frac or "", "start": m.start(), "end": m.end()}


@dataclass
class Check:
    ok: bool
    problems: list[dict]
    cited: list[str]


def _name_runs(sentence: str) -> list[tuple[str, bool]]:
    """Capitalized multi-word runs, with a flag for 'starts the sentence'."""
    toks = [(m.group(0).rstrip(".'’,"), m.start(), m.end()) for m in _WORD.finditer(sentence)]
    runs, cur = [], []
    prev_end = 0
    for i, (w, pos, end) in enumerate(toks):
        # punctuation between two words ends the run: "Multichain (Anyswap)" is two names, not "Multichain Anyswap"
        if cur and re.search(r"[^\s]", sentence[prev_end:pos]):
            runs.append(cur); cur = []
        prev_end = end
        base = re.sub(r"['’]s$", "", w)
        is_cap = (base[:1].isupper() and base.lower().rstrip(".") not in MONTH_NUM and base.lower() not in _WEEKDAYS
                  and base not in ("I", "I'm", "I've", "I'll", "I'd"))
        if is_cap:
            cur.append((base, pos))
        elif cur and base.lower() in _CONNECTORS and i + 1 < len(toks) and toks[i + 1][0][:1].isupper():
            cur.append((base, pos))
        else:
            if cur:
                runs.append(cur)
            cur = []
        # punctuation after a word ends the run ("Elby, King ..." is two runs)
        tail = sentence[end - 1:end + 1]
        if cur and re.search(r"[,;:!?\"”()]|\.$|\.\s", tail):
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    out = []
    for r in runs:
        while r and r[-1][0].lower() in _CONNECTORS:
            r = r[:-1]
        caps = [w for w, _ in r if w[:1].isupper()]
        if len(caps) >= 2:
            first_pos = r[0][1]
            at_start = not sentence[:first_pos].strip(" \"“‘'(—-")
            out.append((" ".join(w for w, _ in r), at_start))
    return out


def check_sentence(sentence: str, ix: FactIndex, names: bool = True) -> Check:
    """Check one sentence against the fact index. names=False skips the multi-word-name rule (used for Title Case titles)."""
    problems, cited = [], []
    s = sentence

    def need(kind, token, path):
        if path is None:
            problems.append({"kind": kind, "token": token})
        elif path:
            cited.append(path)

    # quoted phrases and code ticks: must appear verbatim (normalized)
    for m in _QUOTED.finditer(s):
        q = next(g for g in m.groups() if g)
        need("quote", q, ix.has_text(q))
    for q in _CODE_TICK.findall(s):
        need("code", q, ix.has_text(q.rstrip("()")))
    # shortened hex ("0xbfdb…7645"): some real hex fact must start and end with those parts
    for pre, suf in _SHORT_HEX.findall(s):
        pre_l, suf_l = pre.lower(), suf.lower()
        path = next((pth for pth, v in ix.strings if v.startswith(pre_l) and v.endswith(suf_l) and len(v) > len(pre_l) + len(suf_l)), None)
        need("hex", f"{pre}…{suf}", path)
    s = _SHORT_HEX.sub(" ", s)
    # hex strings and version strings
    for h in _HEX.findall(s):
        need("hex", h, ix.has_text(h.rstrip(".…")))
    rest = _HEX.sub(" ", s)
    for v in _VERSION.findall(rest):
        need("version", v, ix.has_text(v.lstrip("v")))
    rest = _VERSION.sub(" ", rest)
    # identifiers (camelCase, PascalCase with inner capitals, call())
    for idf in set(_IDENT.findall(rest)):
        need("identifier", idf, ix.has_text(idf.rstrip("()")))
    # dates first, then strip them so their digits are not re-checked as numbers
    spans = []
    for m in _DATE_MDY.finditer(rest):
        mon, d1, d2, y = m.groups()
        mo = _month(mon)
        for d in filter(None, (d1, d2)):
            need("date", m.group(0), ix.dates.get((int(y) if y else None, mo, int(d))))
        spans.append(m.span())
    for m in _DATE_DMY.finditer(rest):
        if any(a <= m.start() < b for a, b in spans):
            continue
        d, mon, y = m.groups()
        need("date", m.group(0), ix.dates.get((int(y) if y else None, _month(mon), int(d))))
        spans.append(m.span())
    for m in _DATE_MY.finditer(rest):
        if any(a <= m.start() < b for a, b in spans):
            continue
        mon, y = m.groups()
        need("date", m.group(0), ix.year_months.get((int(y), _month(mon))))
        spans.append(m.span())
    for m in _ISO_DATE.finditer(rest):
        y, mo, d = map(int, m.groups())
        need("date", m.group(0), ix.dates.get((y, mo, d)))
        spans.append(m.span())
    for m in _MONTH_ALONE.finditer(rest):
        if any(a <= m.start() < b for a, b in spans):
            continue
        if m.start() == 0 and m.group(0) in ("May", "March"):  # sentence-initial modal/verb
            continue
        need("month", m.group(0), ix.months.get(_month(m.group(0))))
    chars = list(rest)
    for a, b in spans:
        chars[a:b] = [" "] * (b - a)
    rest = "".join(chars)
    # numbers
    for tok, val, meta in _scan_numbers(rest):
        digits = len(meta["whole"].lstrip("0")) + len(meta["frac"])
        if digits < 2 and not meta["eth"] and meta["scale"] == 1:
            continue
        is_year = meta["scale"] == 1 and not meta["frac"] and len(meta["whole"]) == 4 and 1900 <= val <= 2100 and "," not in tok
        if is_year:
            need("year", tok, ix.match_number(val, 0, 1, exact=True))
            continue
        unit = (10 ** -meta["decimals"]) * meta["scale"]
        if meta["decimals"] == 0 and meta["scale"] == 1:
            w = meta["whole"]
            tz = len(w) - len(w.rstrip("0"))
            sig = len(w) - tz
            if tz and sig >= 2:          # "19,000" shows two significant digits
                unit = 10 ** tz
        need("eth" if meta["eth"] else "number", tok, ix.match_number(val, meta["decimals"], unit, exact=False))
    for tok, val in _words_to_numbers(rest):
        if val >= 10:
            need("number", tok, ix.match_number(float(val), 0, 1, exact=False))
    # capitalized multi-word names
    if names:
        for run, at_start in _name_runs(rest):
            words = run.split(" ")
            # drop leading sentence words ("Then Kieran Elby" -> "Kieran Elby", "The DAO" -> "DAO")
            while words and words[0].lower() in _STARTERS | _CONNECTORS:
                words = words[1:]
            caps = [w for w in words if w[:1].isupper()]
            if not caps:
                continue
            name = " ".join(words)
            if norm(name) in ALLOW_NAMES or norm(run) in ALLOW_NAMES:
                continue
            if len(caps) < 2:
                # one word left: still a name when it is an acronym ("The DAO"), else ordinary capitalization
                if not (len(words) == 1 and re.fullmatch(r"[A-Z]{2,}", words[0]) and words[0] not in ("ETH", "OK")):
                    continue
            p = ix.has_text(run) if ix.has_text(run) is not None else ix.has_text(name)
            if p is None and at_start and len(words) > 1:
                # the first word of a sentence is capitalized anyway ("During the Turbulent Age" -> "Turbulent Age")
                rest_w = words[1:]
                while rest_w and rest_w[0].lower() in _STARTERS | _CONNECTORS:
                    rest_w = rest_w[1:]
                rest_caps = [w for w in rest_w if w[:1].isupper()]
                if len(rest_caps) >= 2 and ix.has_text(" ".join(rest_w)) is not None:
                    name, p = " ".join(rest_w), ix.has_text(" ".join(rest_w))
                elif len(rest_w) == 1 and (norm(rest_w[0]) in ALLOW_NAMES or ix.has_text(rest_w[0]) is not None):
                    continue  # "Modern Solidity": an ordinary first word before a known single name
                # else: "Vitalik Buterin" stays a two-word name and stays unproven
            need("name", name, p)
    return Check(ok=not problems, problems=problems, cited=sorted(set(c for c in cited if c)))


_ABBR = re.compile(r"(?:\b(?:Mr|Mrs|Ms|Dr|St|No|vs|etc|e\.g|i\.e|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|approx)\.)$")


def split_sentences(paragraph: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])([\"”’)]?)\s+(?=[\"“‘(]?[A-Z0-9ÁÉÍÓÚÑ])", paragraph.strip())
    # re.split with one group returns [text, closer, text, closer, ...]
    sents, buf = [], ""
    for i in range(0, len(parts), 2):
        piece = parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")
        buf = f"{buf} {piece}".strip() if buf else piece
        if not _ABBR.search(buf):
            sents.append(buf); buf = ""
    if buf:
        sents.append(buf)
    return [s for s in (x.strip() for x in sents) if s]


def problems_text(problems: list[dict]) -> str:
    return "; ".join(f"{p['kind']} '{p['token']}' is not in the facts" for p in problems)
