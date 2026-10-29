"""`ghosts haunt`: the whole pipeline for one ghost, resumable, safe to run from a cron.

    pick -> summon -> wounds -> classify -> (alive? skip a picked one) -> face -> story -> render -> og -> gallery -> deploy

Every step is skipped when its output file already exists (unless --force). Each step's seconds and outcome go to
data/ghosts/<address>/haunt.json. A failure stops the chain and leaves the partial files; face failures never stop it.
A picked ghost that classifies as alive is moved to data/skipped/<address>/ (with its haunt.json) and the picker is
asked again, up to 3 tries. An address given by hand is never skipped for being alive.
"""
from __future__ import annotations
import contextlib
import datetime as dt
import fcntl
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import typer

from . import config

MAX_TRIES = 3
STEP_NAMES = ["summon", "wounds", "classify", "face", "story", "render", "og", "gallery", "deploy"]
STORY_LOCK_WAIT = 45 * 60  # seconds to wait for the single Ollama slot


# ----------------------------------------------------------------------------- paths (read config at call time)


def ghost_dir(address: str) -> Path:
    return config.GHOSTS_DIR / address.lower()


def skipped_dir() -> Path:
    return config.DATA / "skipped"


def page_path(address: str) -> Path:
    return config.ROOT / "web" / "ghosts" / address.lower() / "index.html"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


# ----------------------------------------------------------------------------- locks


@contextlib.contextmanager
def file_lock(path: Path, wait: float = 0.0):
    """flock on `path`. wait=0: fail at once with BlockingIOError; wait>0: poll up to that many seconds."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+")
    deadline = time.monotonic() + wait
    try:
        while True:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(2)
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


# ----------------------------------------------------------------------------- incident hint


def incident_entry(address: str, pick: dict) -> dict | None:
    """A catalog-shaped entry built from the incident picker's hint (DeFiHackLabs text), for Lane A's wounds.analyze.
    Only when the address is one of the incident's victim addresses. `checks` is empty, so nothing in the source is
    'confirmed' by it: wounds.apply_catalog adds one catalog finding that says what the repository documents."""
    inc = ((pick or {}).get("extra") or {}).get("incident")
    if not inc:
        return None
    a = address.lower()
    if a not in [x.lower() for x in (inc.get("victim_addresses") or []) + [inc.get("primary") or ""]]:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", str(inc.get("name") or "incident").lower()).strip("-")
    loss = inc.get("loss_text")
    refs = [u for u in [inc.get("poc_url"), *(inc.get("references") or [])] if u]
    return {
        "id": f"defihacklabs-{inc.get('date')}-{slug}", "address": a, "name": inc.get("name"),
        "contract_name": (pick or {}).get("name"), "date": inc.get("date"), "cause": inc.get("cause"), "swc": None,
        "checks": [], "function_hint": None, "loss_usd": inc.get("loss_usd"), "loss_eth": None, "loss_note": loss,
        "incident": True,
        "summary": f"{inc.get('name')} ({inc.get('date')}), documented in the DeFiHackLabs repository: {inc.get('cause') or 'cause not stated'}."
                   + (f" Reported loss: {loss}." if loss else ""),
        "references": refs,
        "notes": "Victim address read from the proof-of-concept exploit by code; the repository's words, not ours.",
    }


# ----------------------------------------------------------------------------- the real steps (patched in tests)


def _summon(ctx: dict) -> str:
    from . import facts as F
    f = F.summon(ctx["address"], ctx["sites"] or None, force=ctx["force"])
    return f"{f.get('name')}; via {', '.join(f.get('sources_used') or [])}"


def _wounds(ctx: dict) -> str:
    from . import wounds as W
    entry = ctx.get("catalog_entry")
    w = W.analyze(ctx["address"], catalog=(W.load_catalog() + [entry]) if entry else None)
    return f"tier {w['tier']}, {len(w['findings'])} finding(s)" + (f", incident: {w['incident']['name']}" if w.get("incident") else "")


def _classify(ctx: dict) -> str:
    from . import classify as C
    v = C.classify(ctx["address"])
    return v["kind"]


def _face(ctx: dict) -> str:
    from . import face as Fa
    sites = list(ctx["sites"] or [])
    r = Fa.capture(ctx["address"], sites or None)
    if not r["shots"]:
        fails = [x for x in r["report"] if x.get("ok") is False]
        if fails:
            raise RuntimeError(f"no screenshots: {fails[0]}")
        return "no site known, no screenshots"  # not a failure: most 2018+ contracts have no dapp site
    return f"{len(r['shots'])} shot(s)"


def _story(ctx: dict) -> str:
    from . import story as S
    with file_lock(config.DATA / "haunt-story.lock", wait=STORY_LOCK_WAIT):
        st = S.tell(ctx["address"], log=lambda *a, **k: None)
    v = st["verifier"]
    return (f"{st['model']['seconds']} s, {st['model']['calls']} calls; verifier {v['grounded']}/{v['sentences']} grounded, "
            f"{v['repaired']} repaired, {v['dropped']} dropped")


def _render(ctx: dict) -> str:
    from . import render as R
    p = R.render(ctx["address"])
    return f"{Path(p).stat().st_size:,} bytes"


def _og(ctx: dict) -> str:
    from . import og as O
    p = O.make(ctx["address"])
    return f"{Path(p).stat().st_size:,} bytes" if p else "no og.png (skipped: browser missing)"


def _gallery(ctx: dict) -> str:
    from . import gallery as G
    p = G.build()
    return f"{len(json.loads(Path(p).read_text()))} ghost(s) in the index"


def _deploy(ctx: dict) -> str:
    script = config.ROOT / "scripts" / "deploy.sh"
    r = subprocess.run(["bash", str(script)], cwd=config.ROOT, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError(f"deploy.sh exit {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}")
    return (r.stdout.strip().splitlines() or ["deployed"])[-1]


def _out(name: str, address: str) -> Path | None:
    gd = ghost_dir(address)
    return {"summon": gd / "facts.json", "wounds": gd / "wounds.json", "classify": gd / "verdict.json",
            "face": gd / "shots" / "index.json", "story": gd / "story.json", "render": page_path(address),
            "og": page_path(address).parent / "og.png"}.get(name)


IMPL = {"summon": _summon, "wounds": _wounds, "classify": _classify, "face": _face, "story": _story,
        "render": _render, "og": _og, "gallery": _gallery, "deploy": _deploy}
NEVER_FATAL = {"face", "og"}


# ----------------------------------------------------------------------------- the chain


def read_record(address: str) -> dict:
    return _load(ghost_dir(address) / "haunt.json") or {}


def write_record(rec: dict, folder: Path | None = None) -> None:
    folder = folder or ghost_dir(rec["address"])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "haunt.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))


def summarize(rec: dict) -> dict:
    """Fill kind, title, name from the files on disk."""
    gd = ghost_dir(rec["address"])
    verdict, story, facts = _load(gd / "verdict.json") or {}, _load(gd / "story.json") or {}, _load(gd / "facts.json") or {}
    rec["kind"] = verdict.get("kind") or story.get("kind")
    rec["title"] = story.get("title")
    rec["name"] = story.get("name") or facts.get("name") or rec.get("name")
    return rec


def chain(address: str, *, sites: list[str] | None = None, force: bool = False, skip_face: bool = False, deploy: bool = False,
          picked: dict | None = None, pre_steps: list[dict] | None = None, drop_alive: bool = False, log=print) -> dict:
    """Run the steps for one address. Returns the haunt record (also written to haunt.json).
    drop_alive: if the verdict is alive, move the folder to data/skipped/ and stop with rec['alive_skipped'] True."""
    address = address.lower()
    prev = read_record(address)
    prev_steps = {s["name"]: s for s in prev.get("steps", [])}
    rec = {"address": address, "started_at": now_iso(), "finished_at": None, "kind": None, "title": None, "name": None,
           "ok": None, "error": None, "steps": list(pre_steps or []), "options": {"sites": sites or [], "force": force, "skip_face": skip_face, "deploy": deploy}}
    if not picked and prev.get("picked"):  # a re-run by address keeps how the ghost was found
        rec["picked"] = prev["picked"]
        rec["name"] = prev.get("name")
        if "pick" in prev_steps and not pre_steps:
            rec["steps"].append(prev_steps["pick"])
    if picked:
        rec["picked"] = {k: picked.get(k) for k in ("source", "reason", "name", "year")}
        rec["picked"]["hint"] = bool(((picked.get("extra") or {}).get("incident")))
        rec["name"] = picked.get("name")
    gd = ghost_dir(address)
    gd.mkdir(parents=True, exist_ok=True)
    ctx = {"address": address, "sites": list(sites or []), "force": force, "catalog_entry": incident_entry(address, picked) if picked else None}
    if ctx["catalog_entry"]:
        rec["incident_hint"] = {k: ctx["catalog_entry"][k] for k in ("id", "name", "date", "cause", "loss_note")}
    elif prev.get("incident_hint") and not picked:
        rec["incident_hint"] = prev["incident_hint"]

    def finish(ok: bool, error: str | None = None) -> dict:
        rec.update(ok=ok, error=error, finished_at=now_iso())
        summarize(rec)
        rec["gallery_path"] = f"web/ghosts/{address}/" if page_path(address).exists() else None
        write_record(rec)
        return rec

    for name in STEP_NAMES:
        if name == "deploy" and not deploy:
            continue
        if name == "face" and skip_face:
            rec["steps"].append({"name": name, "ok": True, "seconds": 0.0, "note": "skipped: --skip-face", "skipped": True})
            continue
        out = _out(name, address)
        if name != "gallery" and name != "deploy" and out is not None and out.exists() and not force:
            old = prev_steps.get(name) or {}
            rec["steps"].append({"name": name, "ok": True, "seconds": old.get("seconds", 0.0) if old.get("ok") else 0.0,
                                 "note": "skipped: output exists" + (f" ({old['note']})" if old.get("ok") and old.get("note") and not old.get("skipped") else ""),
                                 "skipped": True})
        else:
            t0 = time.monotonic()
            try:
                note = IMPL[name](ctx)
                step = {"name": name, "ok": True, "seconds": round(time.monotonic() - t0, 1), "note": str(note)[:300]}
            except Exception as e:  # noqa: BLE001  a failed step is data, not a crash
                step = {"name": name, "ok": False, "seconds": round(time.monotonic() - t0, 1), "note": f"{type(e).__name__}: {str(e)[:300]}"}
            rec["steps"].append(step)
            log(f"  {name:8} {'ok' if step['ok'] else 'FAILED'} {step['seconds']}s {step['note']}")
            write_record(rec | {"finished_at": None, "ok": None})  # partial progress is visible while running
            if not step["ok"] and name not in NEVER_FATAL:
                return finish(False, f"{name}: {step['note']}")
        if name == "classify" and drop_alive:
            v = _load(gd / "verdict.json") or {}
            if v.get("kind") == "alive":
                rec["alive_skipped"] = True
                rec["reasons"] = v.get("reasons")
                finish(True)
                dest = skipped_dir() / address
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(gd), str(dest))
                log(f"  {address} classifies as alive: moved to {dest}")
                return rec
    return finish(True)


# ----------------------------------------------------------------------------- the front door


def resolve_seed(seed: str | None) -> str | None:
    if seed == "daily":
        return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    return seed


def pick_one(source: str, year: int | None, seed: str | None, attempt: int, max_blocks: int | None = None) -> dict:
    from . import pick as P
    s = resolve_seed(seed)
    if s is not None and attempt:
        s = f"{s}#{attempt}"
    if source == "random" and max_blocks:
        return P.pick_random(year, s, max_blocks)
    return P.pick(source, year, s)


def haunt(address: str | None = None, *, source: str = "archive", year: int | None = None, seed: str | None = None,
          sites: list[str] | None = None, deploy: bool = False, force: bool = False, skip_face: bool = False,
          max_blocks: int | None = None, log=print) -> dict:
    """Run the pipeline. With an address: that ghost, whatever its verdict. Without: pick (3 tries, alive ones skipped)."""
    if address:
        address = address.lower()
        with file_lock(config.DATA / "locks" / f"{address}.lock"):
            return chain(address, sites=sites, force=force, skip_face=skip_face, deploy=deploy, log=log)

    skipped_picks: list[dict] = []
    last_error = None
    for attempt in range(MAX_TRIES):
        t0 = time.monotonic()
        try:
            p = pick_one(source, year, seed, attempt, max_blocks)
        except (LookupError, ValueError) as e:
            last_error = f"pick: {e}"
            log(f"  pick     FAILED (try {attempt + 1}) {e}")
            continue
        pick_step = {"name": "pick", "ok": True, "seconds": round(time.monotonic() - t0, 1),
                     "note": f"{source}: {p['reason']}"[:300]}
        a = p["address"].lower()
        log(f"  pick     ok {pick_step['seconds']}s {a} {p.get('name')}")
        prior = skipped_dir() / a / "haunt.json"
        if prior.exists() and not force:
            skipped_picks.append({"address": a, "name": p.get("name"), "why": "alive (skipped earlier)"})
            log(f"  {a} was skipped earlier as alive; picking again")
            continue
        extra_sites = list(sites or [])
        for s in ((p.get("extra") or {}).get("sites") or [(p.get("extra") or {}).get("site")]):
            if s and s not in extra_sites:
                extra_sites.append(s)
        try:
            with file_lock(config.DATA / "locks" / f"{a}.lock"):
                rec = chain(a, sites=extra_sites, force=force, skip_face=skip_face, deploy=deploy, picked=p,
                            pre_steps=[pick_step], drop_alive=True, log=log)
        except BlockingIOError:
            raise RuntimeError(f"another haunt is already working on {a}")
        if rec.get("alive_skipped"):
            skipped_picks.append({"address": a, "name": rec.get("name") or p.get("name"), "why": "alive", "reasons": rec.get("reasons")})
            # the moved folder carries the record; add the list of earlier skips to the final one only
            continue
        if skipped_picks:
            rec["skipped_picks"] = skipped_picks
            write_record(rec)
        return rec
    msg = f"no ghost after {MAX_TRIES} tries" + (f" ({last_error})" if last_error else "") + (f"; skipped as alive: {[s['address'] for s in skipped_picks]}" if skipped_picks else "")
    rec = {"address": None, "ok": False, "error": msg, "skipped_picks": skipped_picks, "steps": [], "kind": None, "title": None}
    return rec


def summary_line(rec: dict) -> str:
    if not rec.get("address") or not rec.get("ok"):
        return f"FAILED {rec.get('address') or '-'}: {rec.get('error')}"
    return f"{rec.get('kind')}  {rec.get('name')}  \"{rec.get('title')}\"  {rec.get('gallery_path') or '(not rendered)'}"


def haunt_cmd(
    address: str = typer.Argument(None, help="a contract address; omit to let the picker choose"),
    source: str = typer.Option("archive", "--source", "-s", help="archive | incident | random (when no address is given)"),
    year: int = typer.Option(None, "--year", "-y", help="2015-2023"),
    seed: str = typer.Option(None, "--seed", help="'daily' = UTC date; any string = deterministic; omit = random"),
    site: list[str] = typer.Option(None, "--site", help="website(s) the dapp lived at; repeat for several"),
    deploy: bool = typer.Option(False, "--deploy", help="run scripts/deploy.sh at the end"),
    force: bool = typer.Option(False, "--force", help="redo every step even when its output exists"),
    skip_face: bool = typer.Option(False, "--skip-face", help="no Wayback screenshots"),
    max_blocks: int = typer.Option(None, "--max-blocks", help="random source: blocks to sample before giving up (default 120)"),
    as_json: bool = typer.Option(False, "--json", help="print the haunt record as JSON instead of one line"),
):
    """Run the whole pipeline for one ghost: pick, summon, wounds, classify, face, story, render, gallery (deploy)."""
    log = (lambda *a, **k: print(*a, file=sys.stderr, **k)) if as_json else print
    try:
        rec = haunt(address, source=source, year=year, seed=seed, sites=list(site or []), deploy=deploy, force=force,
                    skip_face=skip_face, max_blocks=max_blocks, log=log)
    except (BlockingIOError, RuntimeError) as e:
        rec = {"address": address, "ok": False, "error": str(e), "steps": []}
    typer.echo(json.dumps(rec, indent=1, ensure_ascii=False) if as_json else summary_line(rec))
    if not rec.get("ok"):
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(haunt_cmd)
