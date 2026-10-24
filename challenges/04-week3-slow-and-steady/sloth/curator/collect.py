"""Collect: Chrome Bookmarks JSON (read-only) → Link rows, deduped by canonical URL."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sloth.core.models import Link

# Chrome stores times as microseconds since 1601-01-01 UTC (Windows FILETIME / 10).
_CHROME_EPOCH = datetime(1601, 1, 1, tzinfo=UTC)

# Query params that only track the click; dropping them never changes the page.
_TRACKING = {
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "igshid", "ref_src", "ref_url",
    "_hsenc", "_hsmi", "mkt_tok", "si", "source", "sk", "cmpid",
}
_TRACKING_PREFIXES = ("utm_",)
# Per-host share params (x.com adds ?s=20&t=..., medium adds ?source=...).
_HOST_TRACKING = {"x.com": {"s", "t"}, "medium.com": {"sk"}, "youtube.com": {"feature", "pp"}}
_HOST_ALIASES = {"twitter.com": "x.com", "mobile.twitter.com": "x.com", "mobile.x.com": "x.com",
                 "m.youtube.com": "youtube.com", "youtu.be": "youtu.be"}


def chrome_time(value: str | int | None) -> datetime | None:
    """Chrome `date_added` (µs since 1601) → aware UTC datetime; 0/empty → None."""
    if not value or int(value) == 0:
        return None
    return _CHROME_EPOCH + timedelta(microseconds=int(value))


def canonical_url(url: str) -> str:
    """Stable identity for a URL: lowercase host, no tracking params, no fragment, no trailing slash.

    Hash-routed fragments (`#/route`, `#!/route`) are kept because they select the page.
    """
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    host = (parts.hostname or "").lower()
    host = _HOST_ALIASES.get(host, host)
    bare = host.removeprefix("www.")
    port = parts.port
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    drop = _HOST_TRACKING.get(bare, set())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in _TRACKING and k.lower() not in drop
             and not k.lower().startswith(_TRACKING_PREFIXES)]
    path = parts.path or "/"
    if bare == "github.com":
        # Owner and repo names are case-insensitive on GitHub.
        segs = path.split("/")
        path = "/".join(s.lower() if i in (1, 2) else s for i, s in enumerate(segs))
    if len(path) > 1:
        path = path.rstrip("/")
    frag = parts.fragment if parts.fragment.startswith(("/", "!")) else ""
    out = urlunsplit((scheme, netloc, path, urlencode(sorted(query)), frag))
    return out.rstrip("/") if path == "/" and not query and not frag else out


def dedupe_key(url: str) -> str:
    """Looser key for near-duplicates: scheme-less, no `www.`, GitHub repo root/branch/README → owner/repo."""
    c = urlsplit(canonical_url(url))
    host = (c.hostname or "").removeprefix("www.")
    path = c.path
    if host == "github.com":
        segs = [s for s in path.split("/") if s]
        if len(segs) >= 2 and segs[0] not in GITHUB_NON_REPO:
            repo = f"github.com/{segs[0]}/{segs[1].removesuffix('.git')}"
            rest = segs[2:]
            # The repo page, a branch root or its README are the same thing; a file deeper inside is not.
            if (not rest or (rest[0] == "tree" and len(rest) <= 2)
                    or (rest[0] == "blob" and len(rest) == 3 and rest[2].lower().startswith("readme"))):
                return repo
            return f"{repo}/{'/'.join(rest)}"
    q = f"?{c.query}" if c.query else ""
    return f"{host}{path.rstrip('/')}{q}"


# First path segments on github.com that are not an owner.
GITHUB_NON_REPO = {"orgs", "topics", "settings", "marketplace", "features", "sponsors", "collections",
                   "trending", "explore", "search", "apps", "about", "pricing", "login", "notifications",
                   "users", "enterprise", "events", "readme", "site", "security", "codespaces"}


def github_repo(url: str) -> tuple[str, str] | None:
    """(owner, repo) for a github.com repo URL (any sub-path), else None."""
    parts = urlsplit(url)
    if (parts.hostname or "").removeprefix("www.").lower() != "github.com":
        return None
    segs = [s for s in parts.path.split("/") if s]
    if len(segs) < 2 or segs[0].lower() in GITHUB_NON_REPO:
        return None
    return segs[0], segs[1].removesuffix(".git")


@dataclass
class Collected:
    links: list[Link]
    exact_duplicates: list[Link] = field(default_factory=list)  # extra Chrome entries, same canonical URL
    folder_found: bool = True


def find_folder(roots: dict, name: str) -> dict | None:
    """The `name` folder directly under the bookmarks bar (where the author keeps it)."""
    for child in roots.get("bookmark_bar", {}).get("children", []):
        if child.get("type") == "folder" and child.get("name") == name:
            return child
    return None


def collect(bookmarks_path: Path, folder: str = "Reading List", source: str = "reading-list") -> Collected:
    data = json.loads(Path(bookmarks_path).read_text())
    node = find_folder(data.get("roots", {}), folder)
    if node is None:
        return Collected(links=[], folder_found=False)
    seen: dict[str, Link] = {}
    dupes: list[Link] = []

    def walk(n: dict, path: list[str]) -> None:
        for c in n.get("children", []):
            if c.get("type") == "folder":
                walk(c, path + [c.get("name", "")])
            elif c.get("type") == "url" and c.get("url", "").startswith(("http://", "https://")):
                link = Link(url=c["url"], canonical_url=canonical_url(c["url"]),
                            title=(c.get("name") or "").strip() or None,
                            folder_path="/".join(path), saved_at=chrome_time(c.get("date_added")),
                            source=source)
                prev = seen.get(link.canonical_url)
                if prev is None:
                    seen[link.canonical_url] = link
                elif (link.saved_at or datetime.max.replace(tzinfo=UTC)) < (
                        prev.saved_at or datetime.max.replace(tzinfo=UTC)):
                    seen[link.canonical_url] = link  # keep the earliest save
                    dupes.append(prev)
                else:
                    dupes.append(link)

    walk(node, [folder])
    return Collected(links=list(seen.values()), exact_duplicates=dupes)
