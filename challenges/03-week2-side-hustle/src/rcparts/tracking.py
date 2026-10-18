"""Tracking numbers for self-orders: find one in a member's message, guess the carrier, build a link.

The maintainer checks the package when it reaches the US address; this only has to catch typos and
point at the right carrier page.
"""

from __future__ import annotations

import re

# Order matters: the more specific formats first (USPS 20-22 digit numbers start with 9x, FedEx's do not).
CARRIERS = [
    ("UPS", re.compile(r"^1Z[0-9A-Z]{16}$"), "https://www.ups.com/track?tracknum={n}"),
    ("USPS", re.compile(r"^(9[1-5]\d{18,20}|82\d{8}|[A-Z]{2}\d{9}US)$"), "https://tools.usps.com/go/TrackConfirmAction?tLabels={n}"),
    ("Amazon", re.compile(r"^TBA\d{12}$"), None),
    ("FedEx", re.compile(r"^(\d{12}|\d{15}|\d{20})$"), "https://www.fedex.com/fedextrack/?trknbr={n}"),
    ("DHL", re.compile(r"^\d{10}$"), "https://www.dhl.com/us-en/home/tracking/tracking-express.html?tracking-id={n}"),
]
_WORD = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")


def normalize(value: str) -> str:
    return re.sub(r"[\s\-]+", "", value or "").upper()


def carrier_for(number: str) -> tuple[str | None, str | None]:
    for name, pattern, link in CARRIERS:
        if pattern.match(number):
            return name, link.format(n=number) if link else None
    return None, None


def find_tracking(text: str) -> dict | None:
    """Return {number, carrier, link} for the best candidate in free text, or None.

    A known carrier format wins; otherwise any 8-35 character code with at least 8 digits is kept
    (carrier unknown) so the maintainer can still check it by hand.
    """
    # Members write "es 1Z999..." or "UPS 1Z 999 AA1 ...": try every run of up to 8 consecutive words
    # that starts and ends with a word containing a digit, so labels like "tracking" never get glued on.
    words = _WORD.findall(text or "")
    candidates = []
    for i in range(len(words)):
        if not any(c.isdigit() for c in words[i]):
            continue
        for j in range(i, min(i + 8, len(words))):
            if not any(c.isdigit() for c in words[j]):
                continue
            n = normalize("".join(words[i:j + 1]))
            if 8 <= len(n) <= 35 and sum(c.isdigit() for c in n) >= 8:
                candidates.append(n)
    known = [(n, *carrier_for(n)) for n in candidates if carrier_for(n)[0]]
    if known:
        n, carrier, link = max(known, key=lambda x: len(x[0]))
        return {"number": n, "carrier": carrier, "link": link}
    if candidates:
        n = max(candidates, key=len)
        return {"number": n, "carrier": None, "link": None}
    return None
