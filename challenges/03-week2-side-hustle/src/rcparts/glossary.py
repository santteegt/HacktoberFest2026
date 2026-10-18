"""Bilingual (Spanish / English) RC part vocabulary, so "rear lower arm" finds "brazo inferior trasero".

Each concept groups the words members use for the same thing in either language. Matching counts
concepts, not words: "shock" and "amortiguadores" are one concept. Everything is compared accent-folded
("alerón" == "aleron") and with crude plural folding. Multi-word synonyms ("anti-roll bar",
"barra estabilizadora") are phrases: all their words must appear in order.
"""

from __future__ import annotations

import re
import unicodedata

CONCEPTS: dict[str, list[str]] = {
    "arm": ["arm", "brazo", "a-arm", "suspension arm", "wishbone", "trapecio"],
    "rear": ["rear", "trasero", "trasera", "posterior"],
    "front": ["front", "delantero", "delantera", "frontal"],
    "lower": ["lower", "inferior", "bajo", "baja", "bottom"],
    "upper": ["upper", "superior"],
    "left": ["left", "izquierdo", "izquierda", "izq", "lh"],
    "right": ["right", "derecho", "derecha", "rh"],
    "shock": ["shock", "shock absorber", "amortiguador", "damper"],
    "spring": ["spring", "resorte", "muelle"],
    "anti_roll_bar": ["anti-roll bar", "anti roll bar", "antiroll bar", "anti-roll", "antiroll", "sway bar",
                      "stabilizer", "barra estabilizadora", "estabilizadora", "estabilizador", "barra antivuelco"],
    "steering_block": ["steering block", "steering knuckle", "knuckle", "mangueta"],
    "hub_carrier": ["hub carrier", "hub", "carrier", "c-hub", "portamangueta"],
    "bumper": ["bumper", "parachoques", "paragolpes", "defensa"],
    "wing": ["wing", "alerón", "spoiler"],
    "body_post": ["body post", "body mount", "portacarrocería", "poste", "body clip"],
    "body": ["body", "carrocería", "shell"],
    "chassis": ["chassis", "chasis"],
    "plate": ["plate", "pletina", "placa", "deck"],
    "spur": ["spur gear", "spur", "corona"],
    "pinion": ["pinion", "piñón"],
    "gear": ["gear", "engranaje"],
    "diff": ["diff", "differential", "diferencial"],
    "belt": ["belt", "correa"],
    "bearing": ["bearing", "rodamiento", "balero", "rulemán"],
    "screw": ["screw", "tornillo"],
    "nut": ["nut", "tuerca"],
    "tire": ["tire", "tyre", "llanta", "neumático"],
    "wheel": ["wheel", "rin", "aro", "rim"],
    "servo": ["servo"],
    "motor": ["motor"],
    "esc": ["esc", "variador", "speed controller"],
    "battery": ["battery", "batería", "lipo"],
    "camber": ["camber", "caída"],
    "bushing": ["bushing", "buje", "bush"],
    "kit": ["kit"],
    "hard": ["hard", "duro", "dura"],
    "medium": ["medium", "medio", "media"],
    "soft": ["soft", "suave", "blando", "blanda"],
    "short": ["short", "corto", "corta"],
    "long": ["long", "largo", "larga"],
    "aluminum": ["aluminum", "aluminium", "aluminio", "alu"],
    "carbon": ["carbon", "carbono", "grafito", "graphite"],
}

# Two sides naming different values on one axis are different parts ("front arm" is not "rear arm").
OPPOSITES: tuple[frozenset[str], ...] = (
    frozenset({"front", "rear"}), frozenset({"left", "right"}), frozenset({"upper", "lower"}),
)

# Words that describe a part rather than name it. "front lower arm" and "front anti-roll bar" share
# "front" but are different parts, so a match needs a shared part concept, not only these.
MODIFIERS = frozenset({"rear", "front", "lower", "upper", "left", "right", "hard", "medium", "soft", "short", "long",
                       "aluminum", "carbon"})

# Brands members name; the store lookup keeps them when it shortens a query.
BRANDS = frozenset(
    "xray tamiya yokomo associated tlr losi kyosho traxxas arrma awesomatix mugen infinity schumacher sakura "
    "serpent hpi axial mst 3racing hobao sweep reedy hobbywing futaba sanwa".split()
)

_WORD = re.compile(r"[^\W_]+", re.UNICODE)


def fold(text: str | None) -> str:
    """Lowercase without accents: "Alerón" -> "aleron", "piñón" -> "pinon"."""
    decomposed = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def words(text: str | None) -> list[str]:
    return _WORD.findall(fold(text))


def stem(word: str) -> str:
    """Crude plural folding ("amortiguadores" -> "amortiguador", "shocks" -> "shock"). Used as a prefix,
    so over-trimming ("bujes" -> "buj") still matches."""
    if len(word) >= 6 and word.endswith("es"):
        return word[:-2]
    if len(word) >= 5 and word.endswith("s"):
        return word[:-1]
    return word


def singulars(word: str) -> list[str]:
    """Candidate singular forms of a folded word: "resortes" -> resortes, resorte, resort."""
    out = [word]
    if len(word) >= 4 and word.endswith("s"):
        out.append(word[:-1])
    if len(word) >= 5 and word.endswith("es"):
        out.append(word[:-2])
    return out


# Lookup tables built once: single folded word -> concept, and phrases (tuples of folded words).
_SINGLE: dict[str, str] = {}
_PHRASES: list[tuple[tuple[str, ...], str]] = []
for _concept, _syns in CONCEPTS.items():
    for _syn in _syns:
        _w = tuple(words(_syn))
        if len(_w) == 1:
            _SINGLE.setdefault(_w[0], _concept)
        elif _w:
            _PHRASES.append((_w, _concept))
_PHRASES.sort(key=lambda p: -len(p[0]))  # longest phrase first


def concept_of(word: str) -> str | None:
    """The glossary concept of one folded word (any plural form), or None."""
    for form in singulars(word):
        if form in _SINGLE:
            return _SINGLE[form]
    return None


def _phrase_at(ws: list[str], i: int) -> tuple[str, int] | None:
    for phrase, concept in _PHRASES:
        n = len(phrase)
        if i + n <= len(ws) and all(concept_of_form(ws[i + k], phrase[k]) for k in range(n)):
            return concept, n
    return None


def concept_of_form(word: str, target: str) -> bool:
    return target in singulars(word)


def concepts(ws: list[str]) -> list[str]:
    """Concept ids for a list of folded words, in order, deduplicated. A word outside the glossary is
    its own concept, keyed by its stem ("x4", "xra303187h", "pletina")."""
    out: dict[str, None] = {}
    i = 0
    while i < len(ws):
        hit = _phrase_at(ws, i)
        if hit:
            out.setdefault(hit[0], None)
            i += hit[1]
            continue
        out.setdefault(concept_of(ws[i]) or stem(ws[i]), None)
        i += 1
    return list(out)


def is_glossary(concept: str) -> bool:
    return concept in CONCEPTS


def part_concepts(concepts) -> list[str]:
    """The glossary concepts that name a part (arm, shock, wing...), not a modifier (front, aluminum...)."""
    return [c for c in concepts if c in CONCEPTS and c not in MODIFIERS]


def synonym_prefixes(concept: str) -> list[list[str]]:
    """The tsquery prefixes for a concept: each synonym as a list of words (a phrase is ANDed), both as
    written (the index keeps accents) and folded. A non-glossary concept is just its own stem."""
    if concept not in CONCEPTS:
        return [[concept]]
    out: dict[tuple[str, ...], None] = {}
    for syn in CONCEPTS[concept]:
        raw = tuple(_WORD.findall(syn.lower()))
        folded = tuple(words(syn))
        for form in (raw, folded):
            if form:
                out.setdefault(form, None)
    return [list(f) for f in out]


def opposite_conflict(a: set[str], b: set[str]) -> bool:
    """True when both sides name a value on the same axis and the values differ (front vs rear)."""
    for axis in OPPOSITES:
        x, y = a & axis, b & axis
        if x and y and not (x & y):
            return True
    return False
