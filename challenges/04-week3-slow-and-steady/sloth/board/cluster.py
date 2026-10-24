"""Group kept links into card-sized clusters. Pure code: no model, no database.

A card needs 2-5 links, each with buildable >= 2, from one vertical. Inside a vertical,
links join the cluster whose topic words they share most (Jaccard over topic + idea words);
leftover singletons of a vertical are grouped together so nothing buildable is stranded
unless it is alone in its vertical (it waits for the next batch).
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import UTC, datetime

from .store import KeptLink

MIN_LINKS, MAX_LINKS, MIN_BUILDABLE = 2, 5, 2
SIMILAR = 0.2  # Jaccard threshold to join a topic cluster

_STOP = {
    "a", "an", "and", "the", "of", "for", "to", "in", "on", "with", "by", "from", "how", "using",
    "build", "building", "tiny", "demo", "small", "simple", "your", "you", "is", "are", "it",
    "topic", "into", "via", "vs", "at", "as", "that", "this", "what", "why", "new",
}


def words(link: KeptLink) -> set[str]:
    text = f"{link.topic} {link.one_line_idea or ''}".lower()
    return {w for w in re.findall(r"[a-z0-9][a-z0-9+#.-]*", text)
            if w not in _STOP and not w.isdigit() and not w.startswith("#") and len(w) > 1}


def topic_words(link: KeptLink) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9+#.-]*", link.topic.lower())
            if w not in _STOP and len(w) > 1} or words(link)


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _rank(link: KeptLink) -> tuple:
    saved = link.saved_at or datetime(1970, 1, 1, tzinfo=UTC)
    return (-link.buildable, -saved.timestamp(), link.link_id)


def cluster(links: list[KeptLink]) -> list[list[KeptLink]]:
    """Return clusters of 2-5 links, deterministic for the same input."""
    by_vertical: dict[str, list[KeptLink]] = defaultdict(list)
    for link in links:
        if link.buildable >= MIN_BUILDABLE:
            by_vertical[link.vertical].append(link)
    out: list[list[KeptLink]] = []
    for vertical in sorted(by_vertical):
        pool = sorted(by_vertical[vertical], key=_rank)
        groups: list[list[KeptLink]] = []
        while pool:
            seed = pool.pop(0)
            group, seed_words = [seed], topic_words(seed)
            # take the most similar first, so a group is tight before it is full
            scored = sorted(((jaccard(seed_words, topic_words(o)), i) for i, o in enumerate(pool)),
                            key=lambda x: (-x[0], x[1]))
            take = [i for score, i in scored if score >= SIMILAR][: MAX_LINKS - 1]
            group += [pool[i] for i in take]
            pool = [o for i, o in enumerate(pool) if i not in set(take)]
            groups.append(group)
        full = [g for g in groups if len(g) >= MIN_LINKS]
        leftovers = sorted((g[0] for g in groups if len(g) < MIN_LINKS), key=_rank)
        for i in range(0, len(leftovers), MAX_LINKS):
            chunk = leftovers[i:i + MAX_LINKS]
            if len(chunk) >= MIN_LINKS:
                full.append(chunk)
            elif full and len(full[-1]) < MAX_LINKS:
                full[-1].append(chunk[0])
        out += full
    return out


def card_id(link_ids: list[int], taken: set[str]) -> str:
    """Short stable id from the link set, e.g. `k7f3a`; lengthened on a collision."""
    digest = hashlib.sha1(",".join(map(str, sorted(link_ids))).encode()).hexdigest()
    for n in range(4, len(digest)):
        cid = f"k{digest[:n]}"
        if cid not in taken:
            return cid
    raise ValueError("card id space exhausted")
