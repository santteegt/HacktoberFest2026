"""Internet Archive CDX index: when a site was alive, and the snapshots to render."""
from __future__ import annotations
from urllib.parse import urlparse
from .. import config
from ..http import get_json


def captures(site: str) -> list[dict]:
    """One capture per month for a host, oldest first: [{ts, status, mime, url}]."""
    u = urlparse(site if "://" in site else f"http://{site}")
    host = u.netloc or site
    # A bare host means "the site": look up its root page. A full URL (a tweet, a postmortem page)
    # is looked up exactly, never widened to the whole domain (a tweet link once returned x.com's 1996 captures).
    target = host + "/" if not u.path or u.path == "/" else host + u.path
    rows = get_json(config.WAYBACK_CDX, params={
        "url": target, "matchType": "exact", "output": "json", "collapse": "timestamp:6",
        "fl": "timestamp,statuscode,mimetype,original", "filter": "mimetype:text/html",
    }, ttl=7 * 86400)
    if not rows or len(rows) < 2:
        return []
    out = []
    for r in rows[1:]:
        try:
            if (urlparse(r[3]).hostname or "").lower().removeprefix("www.") != host.split(":")[0].lower().removeprefix("www."):
                continue
        except Exception:
            pass
        out.append({"ts": r[0], "status": r[1], "mime": r[2], "url": r[3]})
    return out


def life(site: str) -> dict:
    caps = captures(site)
    ok = [c for c in caps if c["status"] == "200"]
    years = sorted({c["ts"][:4] for c in ok})
    return {
        "host": site,
        "captures": len(caps),
        "first_capture": caps[0]["ts"] if caps else None,
        "first_ok": ok[0]["ts"] if ok else None,
        "last_ok": ok[-1]["ts"] if ok else None,
        "last_capture": caps[-1]["ts"] if caps else None,
        "years_alive": years,
    }


def snapshot_url(ts: str, original: str) -> str:
    return f"https://web.archive.org/web/{ts}/{original}"
