"""Club matching in SQL, no model: exact part number first, then full-text over the listing words."""

from __future__ import annotations

import re

from .db import LISTING_COLS, has_extension
from .listing import join_model_codes, normalize_part_number

MAX_RESULTS = 5
# The index is language-neutral ('simple'), so filler words are dropped from the query here.
STOPWORDS = set(
    "a an and the for of to with in on my i have has need want looking any some who anyone someone does is "
    "de del la el los las un una unos unas para por con en y o mi mis tengo busco necesito quiero algun alguien "
    "alguno quien tiene hay".split()
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


def _exact(conn, club_id, part_numbers, kind, exclude_member, exclude_listing) -> list[dict]:
    if not part_numbers:
        return []
    rows = conn.execute(
        f"""SELECT {LISTING_COLS} FROM listings l JOIN members m ON m.id = l.member_id
            WHERE l.club_id = %(club)s AND l.part_number = ANY(%(parts)s)
              AND l.status IN ('open', 'matched')
              AND (%(kind)s::text IS NULL OR l.kind = %(kind)s)
              AND (%(xm)s::bigint IS NULL OR l.member_id <> %(xm)s)
              AND (%(xl)s::bigint IS NULL OR l.id <> %(xl)s)
            ORDER BY l.created_at DESC LIMIT %(lim)s""",
        {"club": club_id, "parts": part_numbers, "kind": kind, "xm": exclude_member, "xl": exclude_listing,
         "lim": MAX_RESULTS},
    ).fetchall()
    return [{**r, "method": "part_number", "score": 1.0} for r in rows]


def _text(conn, club_id, terms, description, kind, exclude_member, exclude_listing) -> list[dict]:
    if not terms:
        return []
    sim = "similarity(coalesce(l.description, ''), %(desc)s)" if has_extension(conn, "pg_trgm") else "0.0"
    rows = conn.execute(
        f"""WITH q AS (SELECT websearch_to_tsquery('simple', %(q)s) AS tsq)
            SELECT {LISTING_COLS},
                   ts_rank(l.search, q.tsq) AS rank,
                   (SELECT count(*) FROM unnest(%(terms)s::text[]) t
                     WHERE t = ANY(tsvector_to_array(l.search))) AS overlap,
                   {sim} AS sim
            FROM listings l JOIN members m ON m.id = l.member_id, q
            WHERE l.club_id = %(club)s AND l.status IN ('open', 'matched') AND l.search @@ q.tsq
              AND (%(kind)s::text IS NULL OR l.kind = %(kind)s)
              AND (%(xm)s::bigint IS NULL OR l.member_id <> %(xm)s)
              AND (%(xl)s::bigint IS NULL OR l.id <> %(xl)s)
            ORDER BY overlap DESC, rank DESC, sim DESC, l.created_at DESC
            LIMIT 25""",
        {"q": " or ".join(terms), "terms": terms, "desc": description or "", "club": club_id, "kind": kind,
         "xm": exclude_member, "xl": exclude_listing},
    ).fetchall()
    # One shared word ("tamiya") is not a match; ask for two, or all of them if the query is a single word.
    need = min(2, len(terms))
    out = []
    for r in rows:
        if r["overlap"] < need:
            continue
        score = round(r["overlap"] / len(terms) + float(r["rank"]) * 0.1 + float(r["sim"]) * 0.01, 4)
        out.append({**r, "method": "text", "score": score})
    return out


def _conflicts(a: dict, b: dict) -> bool:
    """Different brand or chassis on both sides means a different part, however similar the words."""
    return any(a.get(k) and b.get(k) and a[k] != b[k] for k in ("brand", "chassis"))


def find_matches(conn, listing: dict) -> list[dict]:
    """Opposite-kind open listings in the same club, never the member's own."""
    other = "HAVE" if listing["kind"] == "NEED" else "NEED"
    args = (listing["club_id"], other, listing["member_id"], listing["id"])
    if listing.get("part_number"):
        hits = _exact(conn, args[0], [listing["part_number"]], *args[1:])
        if hits:
            return hits
    terms = query_terms(listing.get("brand"), listing.get("chassis"), listing.get("part_number"),
                        listing.get("description"))
    hits = _text(conn, args[0], terms, listing.get("description"), *args[1:])
    return [h for h in hits if not _conflicts(listing, h)][:MAX_RESULTS]


def search(conn, club_id: int, text: str, kind: str | None = None) -> list[dict]:
    """Free-text lookup for the agent's "who has X?" questions."""
    words = re.findall(r"[\w\-]+", text)
    words += [a + b for a, b in zip(words, words[1:])]  # "TAM 54500"
    parts = sorted({p for p in map(normalize_part_number, words) if _LOOKS_LIKE_PART.fullmatch(p)})
    exact = _exact(conn, club_id, parts, kind, None, None)
    seen = {r["id"] for r in exact}
    rest = [r for r in _text(conn, club_id, query_terms(text), text, kind, None, None) if r["id"] not in seen]
    return (exact + rest)[:MAX_RESULTS]
