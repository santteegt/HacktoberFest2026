"""Pure functions over facts.json: how long a contract has been silent and how busy it still is.

No network, no clock unless the caller passes none: every function takes `now` (epoch seconds)."""
from __future__ import annotations
import time
from datetime import datetime, timezone

YEAR_S = 365.25 * 86400
ALIVE_MIN_CALLS = 100        # last-12-month successful calls that make a contract "alive"
ALIVE_MIN_SHARE = 0.05       # ... or this share of its lifetime txs
FRIENDLY_SILENT_YEARS = 2.0  # no successful call for this long -> eligible for "friendly"
SITE_DEAD_YEARS = 2.0        # a site whose last good capture is older than this is dead


def parse_ts(s: str | None) -> float | None:
    """ISO-8601 ('2016-02-19T21:51:14.000000Z') or Wayback ('20160211005112') -> epoch seconds."""
    if not s or not isinstance(s, str):
        return None
    try:
        if s.isdigit() and len(s) >= 8:
            return datetime.strptime(s[:14].ljust(14, "0"), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()
    except ValueError:
        return None


def iso(ts: float | None) -> str | None:
    return None if ts is None else datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now(now: float | None) -> float:
    return time.time() if now is None else now


def lifetime_txs(f: dict) -> int:
    return int((f.get("life") or {}).get("tx_count") or 0)


def last_12m(f: dict) -> int:
    return int((f.get("life") or {}).get("last_12m_txs") or 0)


def last_call_ts(f: dict) -> float | None:
    """Timestamp of the newest successful call (facts.life.last_tx is the newest 'ok' tx when one exists)."""
    lt = (f.get("life") or {}).get("last_tx") or {}
    return parse_ts(lt.get("timestamp"))


def silent_years(f: dict, now: float | None = None) -> float | None:
    ts = last_call_ts(f)
    return None if ts is None else max(0.0, (_now(now) - ts) / YEAR_S)


def never_called(f: dict) -> bool:
    """No call after the deployment (facts.life.never_called; older facts: no calls and no last_tx)."""
    life = f.get("life") or {}
    if "never_called" in life:
        return bool(life["never_called"])
    return lifetime_txs(f) == 0 and not life.get("last_tx")


def years_since_birth(f: dict, now: float | None = None) -> float | None:
    born = parse_ts((f.get("birth") or {}).get("timestamp"))
    return None if born is None else max(0.0, (_now(now) - born) / YEAR_S)


def last_12m_share(f: dict) -> float:
    n = lifetime_txs(f)
    return last_12m(f) / n if n else 0.0


def is_alive(f: dict) -> bool:
    k = last_12m(f)
    return k >= ALIVE_MIN_CALLS or (k > 0 and last_12m_share(f) >= ALIVE_MIN_SHARE)


def is_knocked(f: dict) -> bool:
    """Some successful calls in the last 12 months."""
    return last_12m(f) > 0


def is_long_silent(f: dict, now: float | None = None) -> bool:
    """No successful call for FRIENDLY_SILENT_YEARS (a contract never called counts as silent since birth)."""
    y = silent_years(f, now)
    if y is None:
        born = parse_ts((f.get("birth") or {}).get("timestamp"))
        y = None if born is None else (_now(now) - born) / YEAR_S
    return y is not None and y >= FRIENDLY_SILENT_YEARS and not is_knocked(f)


def live_sites(f: dict, now: float | None = None) -> list[str]:
    """Hosts whose last good Wayback capture is younger than SITE_DEAD_YEARS."""
    out = []
    for s in f.get("sites") or []:
        ts = parse_ts(s.get("last_ok"))
        if ts is not None and (_now(now) - ts) / YEAR_S < SITE_DEAD_YEARS:
            out.append(s.get("host"))
    return out


def site_dead(f: dict, now: float | None = None) -> bool:
    """True when no site is known or every known site's last good capture is older than SITE_DEAD_YEARS."""
    return not live_sites(f, now)
