"""Group kept links into card-sized clusters. Pure code: no model, no database.

A card needs 2-5 links, each with buildable >= 2, from one vertical. Inside a vertical,
links join the cluster whose topic and title words they share most (Jaccard); leftovers pair
up only when they share a word, and a link with no partner waits for the next batch.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import UTC, datetime

from .store import KeptLink

MIN_LINKS, MAX_LINKS, MIN_BUILDABLE = 2, 5, 2
SIMILAR = 0.2  # Jaccard threshold to join a topic cluster
COMMON_SHARE = 0.25  # words in more kept links than this carry no topic signal
LEFTOVER_MAX = 3  # leftovers sharing only a word or two make small cards

_STOP = {
    "a", "an", "and", "the", "of", "for", "to", "in", "on", "with", "by", "from", "how", "using",
    "build", "building", "tiny", "demo", "small", "simple", "your", "you", "is", "are", "it",
    "topic", "into", "via", "vs", "at", "as", "that", "this", "what", "why", "new",
}


def _tok(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9+#.-]*", text.lower())
            if w not in _STOP and not w.isdigit() and not w.startswith("#") and len(w) > 1}


def words(link: KeptLink) -> set[str]:
    return _tok(f"{link.topic} {link.one_line_idea or ''}")


def topic_words(link: KeptLink) -> set[str]:
    """Topic + title words: titles carry the shared site or project name ("Aztec", "Skills")."""
    return _tok(f"{link.topic} {link.title or ''}") or words(link)


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _rank(link: KeptLink) -> tuple:
    saved = link.saved_at or datetime(1970, 1, 1, tzinfo=UTC)
    return (-link.buildable, -saved.timestamp(), link.link_id)


def _bags(links: list[KeptLink]) -> dict[int, set[str]]:
    """Topic/title words minus the ones a quarter of all kept links share ("agent", "ai").

    Frequency is across every vertical, so a project name that dominates one vertical
    ("aztec" in blockchain) still holds its cluster together.
    """
    bags = {link.link_id: topic_words(link) for link in links}
    if len(links) >= 10:
        df: dict[str, int] = defaultdict(int)
        for bag in bags.values():
            for w in bag:
                df[w] += 1
        common = {w for w, n in df.items() if n > COMMON_SHARE * len(links)}
        bags = {k: (v - common) or v for k, v in bags.items()}
    return bags


def _greedy(pool: list[KeptLink], bags: dict[int, set[str]], threshold: float,
            max_size: int) -> tuple[list[list[KeptLink]], list[KeptLink]]:
    """Seed with the best-ranked link, add the most similar ones above threshold."""
    groups, alone = [], []
    pool = list(pool)
    while pool:
        seed = pool.pop(0)
        scored = sorted(((jaccard(bags[seed.link_id], bags[o.link_id]), i) for i, o in enumerate(pool)),
                        key=lambda x: (-x[0], x[1]))
        order = [i for score, i in scored if score >= threshold and score > 0][: max_size - 1]
        group = [seed] + [pool[i] for i in order]
        pool = [o for i, o in enumerate(pool) if i not in set(order)]
        (groups if len(group) >= MIN_LINKS else alone).append(group if len(group) > 1 else seed)
    return groups, alone


def cluster(links: list[KeptLink]) -> list[list[KeptLink]]:
    """Return clusters of 2-5 links, deterministic for the same input.

    Pass 1 groups links whose topic/title words overlap (Jaccard >= SIMILAR). Pass 2 pairs the
    leftovers that share any word, at most LEFTOVER_MAX per card. A link that shares nothing
    with the rest of its vertical waits for the next batch instead of padding an unrelated card.
    """
    by_vertical: dict[str, list[KeptLink]] = defaultdict(list)
    for link in links:
        if link.buildable >= MIN_BUILDABLE:
            by_vertical[link.vertical].append(link)
    bags = _bags([link for pool in by_vertical.values() for link in pool])
    out: list[list[KeptLink]] = []
    for vertical in sorted(by_vertical):
        pool = sorted(by_vertical[vertical], key=_rank)
        groups, alone = _greedy(pool, bags, SIMILAR, MAX_LINKS)
        more, _waiting = _greedy(sorted(alone, key=_rank), bags, 0.0, LEFTOVER_MAX)
        out += groups + more
    return out


def card_id(link_ids: list[int], taken: set[str]) -> str:
    """Short stable id from the link set, e.g. `k7f3a`; lengthened on a collision."""
    digest = hashlib.sha1(",".join(map(str, sorted(link_ids))).encode()).hexdigest()
    for n in range(4, len(digest)):
        cid = f"k{digest[:n]}"
        if cid not in taken:
            return cid
    raise ValueError("card id space exhausted")
