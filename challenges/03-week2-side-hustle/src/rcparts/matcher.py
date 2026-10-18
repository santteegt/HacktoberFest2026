"""Club matching in SQL, no model: exact part number first, then full-text over the listing words."""

from __future__ import annotations

import re

from . import glossary
from .db import LISTING_COLS, has_extension, scope_club_ids
from .listing import join_model_codes, normalize_part_number

MAX_RESULTS = 5
# The index is language-neutral ('simple'), so filler words are dropped from the query here.
STOPWORDS = set(
    "a an and the for of to with in on my i have has need want looking any some who anyone someone does is "
    "de del la el los las un una unos unas para por con en y o mi mis tengo busco necesito quiero algun alguien "
    "alguno quien tiene hay im looking for pieza piezas repuesto repuestos part parts spare".split()
)
_WORD = re.compile(r"\w+", re.UNICODE)
_LOOKS_LIKE_PART = re.compile(r"(?=.*[A-Z])(?=.*\d)[A-Z0-9]{5,}")


def query_terms(*texts: str | None) -> list[str]:
    seen: dict[str, None] = {}
    for text in texts:
        for w in _WORD.findall(join_model_codes(text or "").lower()):
            if len(w) >= 2 and w not in STOPWORDS:
                seen.setdefault(w, None)
    return list(seen)


def stem(word: str) -> str:
    return glossary.stem(word)


_FOLDED_STOPWORDS = {glossary.fold(w) for w in STOPWORDS}


def _folded_words(*texts: str | None) -> list[str]:
    out = []
    for text in texts:
        out += [w for w in glossary.words(join_model_codes(text or ""))
                if len(w) >= 2 and w not in _FOLDED_STOPWORDS]
    return out


def query_concepts(*texts: str | None) -> list[str]:
    """Concepts of the query words: glossary synonyms collapse to one concept ("shocks" and
    "amortiguadores" are both `shock`); any other word is its own concept (its stem)."""
    return glossary.concepts(_folded_words(*texts))


class Profile:
    """A listing's words (folded) and concepts, to count which query concepts it covers."""

    def __init__(self, row: dict):
        self.words = _folded_words(row.get("brand"), row.get("chassis"), row.get("part_number"),
                                   row.get("description"))
        self.concepts = set(glossary.concepts(self.words))

    def covers(self, concept: str) -> bool:
        if glossary.is_glossary(concept):
            return concept in self.concepts
        # A word outside the glossary matches as a prefix, so "amortig" style stems still find plurals.
        return any(w.startswith(concept) for w in self.words)

    def overlap(self, concepts: list[str]) -> int:
        return sum(1 for c in concepts if self.covers(c))


def _tsquery(concepts: list[str], raw_text: str) -> str:
    """OR over every synonym of every concept, as prefixes; phrases are ANDed. The index keeps accents as
    written, so glossary synonyms go in both accented and folded, and so do the member's own words."""
    alts: dict[str, None] = {}
    for c in concepts:
        for form in glossary.synonym_prefixes(c):
            alts.setdefault(" & ".join(f"{w}:*" for w in form) if len(form) == 1 else
                            "(" + " & ".join(f"{w}:*" for w in form) + ")", None)
    for w in re.findall(r"[^\W_]+", join_model_codes(raw_text or "").lower()):
        if len(w) >= 2 and glossary.fold(w) not in _FOLDED_STOPWORDS:
            alts.setdefault(f"{stem(w)}:*", None)
    return " | ".join(alts)


_FOLDED_VECTOR = ("to_tsvector('simple', unaccent(coalesce(l.brand, '') || ' ' || coalesce(l.chassis, '') || ' ' || "
                  "coalesce(l.part_number, '') || ' ' || coalesce(l.description, '')))")


def _exact(conn, club_ids, part_numbers, kind, exclude_member, exclude_listing) -> list[dict]:
    if not part_numbers:
        return []
    rows = conn.execute(
        f"""SELECT {LISTING_COLS} FROM listings l JOIN members m ON m.id = l.member_id
            WHERE l.club_id = ANY(%(clubs)s) AND l.part_number = ANY(%(parts)s)
              AND l.status IN ('open', 'matched')
              AND (%(kind)s::text IS NULL OR l.kind = %(kind)s)
              AND (%(xm)s::bigint IS NULL OR l.member_id <> %(xm)s)
              AND (%(xl)s::bigint IS NULL OR l.id <> %(xl)s)
            ORDER BY l.created_at DESC LIMIT %(lim)s""",
        {"clubs": club_ids, "parts": part_numbers, "kind": kind, "xm": exclude_member, "xl": exclude_listing,
         "lim": MAX_RESULTS},
    ).fetchall()
    return [{**r, "method": "part_number", "score": 1.0} for r in rows]


def rank_text_hits(concepts: list[str], rows: list[dict]) -> list[dict]:
    """Concept overlap in code: at least two concepts in common (or all, for a one-concept query), and
    never opposite positions (front vs rear, left vs right, upper vs lower)."""
    need = min(2, len(concepts))
    qset = set(concepts)
    out = []
    for r in rows:
        prof = Profile(r)
        if glossary.opposite_conflict(qset, prof.concepts):
            continue
        overlap = prof.overlap(concepts)
        if overlap < need:
            continue
        # The query names a part ("arm"): the listing must be that part, not just share "front" and "x4".
        named = glossary.part_concepts(concepts)
        if named and not any(prof.covers(c) for c in named):
            continue
        score = round(overlap / len(concepts) + float(r.get("rank") or 0) * 0.1 + float(r.get("sim") or 0) * 0.01, 4)
        out.append({**r, "overlap": overlap, "method": "text", "score": score})
    out.sort(key=lambda h: (-h["overlap"], -h["score"]))
    return out


def _text(conn, club_ids, concepts, raw_text, description, kind, exclude_member, exclude_listing) -> list[dict]:
    if not concepts:
        return []
    sim = "similarity(coalesce(l.description, ''), %(desc)s)" if has_extension(conn, "pg_trgm") else "0.0"
    folded = f" OR {_FOLDED_VECTOR} @@ q.tsq" if has_extension(conn, "unaccent") else ""
    rows = conn.execute(
        f"""WITH q AS (SELECT to_tsquery('simple', %(q)s) AS tsq)
            SELECT {LISTING_COLS}, ts_rank(l.search, q.tsq) AS rank, {sim} AS sim
            FROM listings l JOIN members m ON m.id = l.member_id, q
            WHERE l.club_id = ANY(%(clubs)s) AND l.status IN ('open', 'matched')
              AND (l.search @@ q.tsq{folded})
              AND (%(kind)s::text IS NULL OR l.kind = %(kind)s)
              AND (%(xm)s::bigint IS NULL OR l.member_id <> %(xm)s)
              AND (%(xl)s::bigint IS NULL OR l.id <> %(xl)s)
            ORDER BY rank DESC, sim DESC, l.created_at DESC
            LIMIT 200""",
        {"q": _tsquery(concepts, raw_text), "desc": description or "", "clubs": club_ids, "kind": kind,
         "xm": exclude_member, "xl": exclude_listing},
    ).fetchall()
    return rank_text_hits(concepts, rows)


def _conflicts(a: dict, b: dict) -> bool:
    """Different brand, chassis or part number on both sides means a different part, however
    similar the words (two X4 parts share "xray x4" but are not the same part)."""
    return any(a.get(k) and b.get(k) and a[k] != b[k] for k in ("brand", "chassis", "part_number"))


def _shares_description(listing: dict, hit: dict) -> bool:
    """A text match needs at least one concept of the part itself in common, not only brand and chassis."""
    desc = [c for c in query_concepts(listing.get("description"))
            if c not in set(query_concepts(listing.get("brand"), listing.get("chassis")))]
    # Modifiers alone ("front", "aluminio") are not the part; they count only if nothing else is said.
    desc = [c for c in desc if c not in glossary.MODIFIERS] or desc
    if not desc:
        return True
    return Profile(hit).overlap(desc) > 0


def text_match_ok(listing: dict, hit: dict) -> bool:
    if _conflicts(listing, hit):
        return False
    if glossary.opposite_conflict(set(query_concepts(listing.get("description"))), Profile(hit).concepts):
        return False
    return _shares_description(listing, hit)


def find_matches(conn, listing: dict, scope: str = "club") -> list[dict]:
    """Opposite-kind open listings in the clubs within `scope` (club | city | country), never the member's own."""
    other = "HAVE" if listing["kind"] == "NEED" else "NEED"
    clubs = scope_club_ids(conn, listing["club_id"], scope)
    args = (other, listing["member_id"], listing["id"])
    if listing.get("part_number"):
        hits = _exact(conn, clubs, [listing["part_number"]], *args)
        if hits:
            return hits
    fields = (listing.get("brand"), listing.get("chassis"), listing.get("part_number"), listing.get("description"))
    hits = _text(conn, clubs, query_concepts(*fields), " ".join(f for f in fields if f), listing.get("description"),
                 *args)
    return [h for h in hits if text_match_ok(listing, h)][:MAX_RESULTS]


def part_numbers_in(text: str) -> list[str]:
    words = re.findall(r"[\w\-]+", text)
    words += [a + b for a, b in zip(words, words[1:])]  # "TAM 54500"
    return sorted({p for p in map(normalize_part_number, words) if _LOOKS_LIKE_PART.fullmatch(p)})


def search(conn, club_id: int, text: str, kind: str | None = None, scope: str = "club") -> list[dict]:
    """Free-text lookup for the agent's "who has X?" questions, across the clubs within `scope`."""
    clubs = scope_club_ids(conn, club_id, scope)
    exact = _exact(conn, clubs, part_numbers_in(text), kind, None, None)
    seen = {r["id"] for r in exact}
    rest = [r for r in _text(conn, clubs, query_concepts(text), text, text, kind, None, None) if r["id"] not in seen]
    return (exact + rest)[:MAX_RESULTS]


# --- closing a listing from what the member said ------------------------------------------

CLOSE_WORDS = set(
    "ya vendi vendí vendido vendida vendidos lo la le les me se no tengo tenía tenia mas más disponible "
    "consegui conseguí encontre encontré compre compré necesito busco hace falta sold found got bought "
    "anymore longer have need it its gone already available".split()
)
SOLD_HINT = re.compile(r"vend|sold|ya no (lo |la )?tengo|no longer have|gone", re.I)
FOUND_HINT = re.compile(r"consegu|encontr|compr[eé]|found|got (it|one)|bought|ya no (lo |la )?(busco|necesito)", re.I)


def infer_close_kind(text: str) -> str | None:
    """HAVE when the member says they sold it, NEED when they say they found it, else None."""
    sold, found = bool(SOLD_HINT.search(text)), bool(FOUND_HINT.search(text))
    return "HAVE" if sold and not found else "NEED" if found and not sold else None


def pick_listings_to_close(listings: list[dict], text: str, kind: str | None = None) -> list[dict]:
    """The member's own active listings that best fit what they said. One result = close it;
    several = ask which one; none = nothing fits. Exact part number wins over words."""
    pool = [l for l in listings if kind is None or l["kind"] == kind] or listings
    parts = set(part_numbers_in(text))
    by_part = [l for l in pool if l.get("part_number") and l["part_number"] in parts]
    if by_part:
        return by_part
    words = set(query_terms(text)) - CLOSE_WORDS
    if not words:
        return []
    scored = []
    for l in pool:
        lw = set(query_terms(l.get("brand"), l.get("chassis"), l.get("part_number"), l.get("description")))
        scored.append((len(words & lw), l))
    best = max((n for n, _ in scored), default=0)
    return [l for n, l in scored if n == best] if best else []
