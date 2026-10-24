"""Code rules for Valhalla. They run before the model and win over it: the model never sees these links."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .collect import dedupe_key

STALE_AFTER = timedelta(days=4 * 365)


@dataclass(frozen=True)
class Verdict:
    rule: str      # dead | parked | archived | stale | duplicate
    reason: str    # shown in #sk-valhalla, max ~120 chars


def _keys(row: dict) -> set[str]:
    keys = {dedupe_key(row["canonical_url"])}
    if row.get("final_url"):
        keys.add(dedupe_key(row["final_url"]))
    return keys


def _order(row: dict) -> tuple[datetime, int]:
    return (row.get("saved_at") or datetime.max.replace(tzinfo=UTC), row["id"])


class DupeIndex:
    """Loose key (post-redirect URL counts) → the earliest-saved link with that key."""

    def __init__(self, everyone: list[dict]):
        self.first: dict[str, dict] = {}
        for row in everyone:
            for k in _keys(row):
                if k not in self.first or _order(row) < _order(self.first[k]):
                    self.first[k] = row

    def duplicate_of(self, link: dict) -> dict | None:
        best = None
        for k in _keys(link):
            other = self.first.get(k)
            if other and other["id"] != link["id"] and _order(other) < _order(link):
                if best is None or _order(other) < _order(best):
                    best = other
        return best


def judge(link: dict, enr: dict | None, dupes: DupeIndex, *, now: datetime | None = None) -> Verdict | None:
    """A Valhalla verdict from facts alone, or None to let the model decide."""
    now = now or datetime.now(UTC)
    if dup := dupes.duplicate_of({**link, "final_url": (enr or {}).get("final_url")}):
        return Verdict("duplicate", f"duplicate of #{dup['id']} (saved earlier)")
    if not enr:
        return None
    err = enr.get("error") or ""
    status = enr.get("http_status")
    if status in (404, 410):
        what = "repo" if enr.get("content_kind") == "github" else "page"
        return Verdict("dead", f"dead link: {what} returns HTTP {status} (checked twice)")
    if err.startswith("dns"):
        return Verdict("dead", "dead link: the domain no longer resolves (checked twice)")
    if err == "parked domain":
        return Verdict("parked", "dead link: the domain is parked or for sale")
    if enr.get("github_archived"):
        return Verdict("archived", f"archived repo ({enr.get('github_stars') or 0} stars); the author stopped it")
    pushed = enr.get("github_pushed_at")
    if pushed and now - pushed > STALE_AFTER:
        return Verdict("stale", f"stale repo: last push {pushed:%Y-%m-%d}, over 4 years ago")
    return None
