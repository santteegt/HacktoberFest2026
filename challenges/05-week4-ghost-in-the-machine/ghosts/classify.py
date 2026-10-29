"""Decide what kind of ghost a contract is. Precedence: banished > bad > alive > lingering > friendly.

Rules (docs/LANES.md, ghost taxonomy):
  banished  chain.code_present is false (selfdestructed)
  bad       a documented catalog incident, or a confirmed wound with impact High and confidence >= Medium
            (fatal). Confirmed Medium-impact wounds are scars: counted, kind unchanged.
  alive     last-12-month successful calls >= 100, or >= 5 % of lifetime txs
  lingering some calls in the last 12 months (below the alive bar) while the dapp's site is dead
  friendly  no successful call for >= 2 years, no fatal wounds (scars allowed);
            also any contract never called after its birth (code still present), whatever its age
Anything the table leaves uncovered (called recently while the site still answers; or silent for 1-2 years)
falls back to lingering, and the reasons say which rule did not fit.
"""
from __future__ import annotations
import json, time
from . import activity as A
from . import facts as F

IMPACT_RANK = {"High": 4, "Medium": 3, "Low": 2, "Informational": 1, "Optimization": 0}
CONF_RANK = {"High": 3, "Medium": 2, "Low": 1}


def fatal(w: dict) -> bool:
    """Confirmed, impact High, confidence >= Medium: enough on its own to make a bad ghost."""
    return bool(w.get("confirmed")) and w.get("impact") == "High" and CONF_RANK.get(w.get("confidence"), 0) >= 2


def scar(w: dict) -> bool:
    """Confirmed Medium+ wound that is not fatal: the ghost keeps its kind and carries the scar."""
    return bool(w.get("confirmed")) and IMPACT_RANK.get(w.get("impact"), 0) >= 3 and not fatal(w)


def wound_summary(wounds: dict | None) -> dict:
    fs = (wounds or {}).get("findings") or []
    worst = max(fs, key=lambda w: IMPACT_RANK.get(w.get("impact"), 0), default=None)
    return {"count": len(fs), "confirmed": sum(1 for w in fs if w.get("confirmed")),
            "worst_impact": worst.get("impact") if worst else None,
            "scars": sum(1 for w in fs if scar(w)), "fatal": sum(1 for w in fs if fatal(w))}


def scars_line(wounds: dict | None) -> str | None:
    fs = (wounds or {}).get("findings") or []
    sc = [w for w in fs if scar(w)]
    if not sc:
        return None
    nf = sum(1 for w in fs if fatal(w))
    checks = ", ".join(dict.fromkeys(str(w.get("check") or "unnamed") for w in sc))
    return f"{len(sc)} scar{'s' if len(sc) != 1 else ''} ({checks}), {'none' if not nf else nf} fatal"


def decide(f: dict, wounds: dict | None, now: float | None = None) -> tuple[str, list[str]]:
    """Pure: facts + wounds -> (kind, reasons)."""
    reasons: list[str] = []
    life = f.get("life") or {}
    k12, n = A.last_12m(f), A.lifetime_txs(f)
    sy = A.silent_years(f, now)
    lt = (life.get("last_tx") or {}).get("timestamp")
    last_s = (f"last successful call {str(lt)[:10]}, {sy:.1f} years ago" if sy is not None
              else "never called after its birth" if A.never_called(f) else "no successful call found")
    capped = " (at least; count capped at 500)" if life.get("last_12m_capped") else ""
    calls = f"{k12}{capped} successful calls in the last 12 months out of {n} lifetime txs ({A.last_12m_share(f):.1%})"
    ws = wound_summary(wounds)
    inc = (wounds or {}).get("incident")
    bad_w = [w for w in (wounds or {}).get("findings") or [] if fatal(w)]
    sl = scars_line(wounds)

    if (f.get("chain") or {}).get("code_present") is False:
        return "banished", ["the code is gone from the chain (selfdestructed)", last_s]
    if inc or bad_w:
        if inc:
            reasons.append(f"documented incident: {inc.get('name')} ({inc.get('date')})")
        if bad_w:
            top = bad_w[0]
            reasons.append(f"{len(bad_w)} fatal wound(s) (confirmed, High impact, Medium+ confidence); first: {top.get('check')} ({top.get('impact')}/{top.get('confidence')}) {top.get('title')}")
        if sl:
            reasons.append(sl)
        reasons.append(calls)
        return "bad", reasons
    if A.is_alive(f):
        return "alive", [calls, f"meets the alive bar (>= {A.ALIVE_MIN_CALLS} calls or >= {A.ALIVE_MIN_SHARE:.0%} of lifetime)"] + ([sl] if sl else [])
    if A.never_called(f):
        yb = A.years_since_birth(f, now)
        born = f"{yb:.1f} years ago" if yb is not None else "at an unknown date"
        return "friendly", [f"never called after its birth {born}", sl or ("no wounds" if ws["count"] == 0 else f"{ws['count']} suspected wound(s), none confirmed at Medium+")]
    wtxt = sl or ("no wounds" if ws["count"] == 0 else f"{ws['count']} suspected wound(s), none confirmed at Medium+")
    if A.is_knocked(f):
        if A.site_dead(f, now):
            site = "no site known" if not f.get("sites") else "every known site's last good capture is over 2 years old"
            return "lingering", [calls, site, last_s, wtxt]
        return "lingering", [calls, f"fallback: a site still answers ({', '.join(map(str, A.live_sites(f, now)))}), so the dapp may not be gone", last_s, wtxt]
    if A.is_long_silent(f, now):
        return "friendly", [last_s, wtxt]
    return "lingering", [last_s, f"fallback: silent for under {A.FRIENDLY_SILENT_YEARS:.0f} years, too recent to be friendly", wtxt]


def verdict(f: dict, wounds: dict | None, now: float | None = None) -> dict:
    kind, reasons = decide(f, wounds, now)
    life = f.get("life") or {}
    sy = A.silent_years(f, now)
    eh = f.get("eh") or {}
    return {
        "address": f["address"], "kind": kind, "reasons": reasons,
        "activity": {"lifetime_txs": A.lifetime_txs(f), "last_tx": A.iso(A.last_call_ts(f)),
                     "last_12m_txs": A.last_12m(f), "last_12m_capped": bool(life.get("last_12m_capped")),
                     "silent_years": None if sy is None else round(sy, 1)},
        "wounds": wound_summary(wounds),
        "labels": {"historian_story": bool(eh.get("short_description") or eh.get("description")),
                   "verified_source": bool(f.get("source")),
                   "site_known": any(s.get("host") and not s.get("error") for s in f.get("sites") or [])},
        "decided_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now) if now else time.gmtime()),
    }


def classify(address: str, *, rerun_wounds: bool = False) -> dict:
    address = address.lower()
    f = F.summon(address)
    gd = F.ghost_dir(address)
    wp = gd / "wounds.json"
    if rerun_wounds or not wp.exists():
        from .wounds import analyze
        wounds = analyze(address)
    else:
        wounds = json.loads(wp.read_text())
    v = verdict(f, wounds)
    (gd / "verdict.json").write_text(json.dumps(v, indent=1))
    return v
