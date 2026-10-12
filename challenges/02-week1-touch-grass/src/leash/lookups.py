"""Find explicit search requests in a voice note (plain code, no model).

Only a note that *starts* with a search phrase counts, so an idea that merely mentions searching
("we could search the archive for ...") is left alone. The rest of the first sentence is the query.
"""
import re

_FILLER = r"(?:(?:okay|ok|hey|so|um|uh|and|also|please|now)[,.]?\s+)*"
_ASK = r"(?:(?:can|could|would)\s+you\s+(?:please\s+)?|i\s+want\s+you\s+to\s+|remind\s+me\s+to\s+|remember\s+to\s+|please\s+)?"
_WEB = r"(?:the\s+)?(?:web|internet|online)"
_VERB = (r"(?:search\s+(?:" + _WEB + r"\s+)?(?:for|about|on)"
         r"|do\s+(?:a|an)\s+(?:(?:web|online|internet)\s+)?search\s+(?:for|about|on)"
         r"|(?:web|online|internet)\s+search(?:\s+(?:for|about|on))?"
         r"|look\s+up)")
_PATTERN = re.compile(r"^\s*" + _FILLER + _ASK + _VERB + r"\s+(?P<q>.+)$", re.I | re.S)
MAX_QUERY = 120


def extract_query(text):
    """The search query a note asks for, or None."""
    t = " ".join((text or "").split())
    m = _PATTERN.match(t)
    if not m:
        return None
    q = re.split(r"(?<=[.?!])\s", m.group("q"), maxsplit=1)[0]      # first sentence only
    q = q.strip().strip("\"'“”‘’").rstrip(".?!,;: ").strip()
    q = re.sub(r"^(?:(?:the\s+)?(?:web|internet|online)\s+)?(?:about|for|on)\s+", "", q, flags=re.I)   # "search on the web about X"
    q = re.sub(r"\s+(?:please|for me|thanks|thank you)$", "", q, flags=re.I)
    if len(q) < 3 or len(q.split()) > 20:
        return None
    return q[:MAX_QUERY]
