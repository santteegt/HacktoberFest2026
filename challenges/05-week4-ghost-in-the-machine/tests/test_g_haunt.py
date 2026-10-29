"""Lane G: the haunt step chain, every step mocked. No network, no model."""
import json
from pathlib import Path

import pytest

from ghosts import config, haunt as H

FIX = Path(__file__).parent / "fixtures" / "g"
A1 = "0x" + "11" * 20
A2 = "0x" + "22" * 20
A3 = "0x" + "33" * 20


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    monkeypatch.setattr(config, "GHOSTS_DIR", tmp_path / "data" / "ghosts")
    (tmp_path / "data" / "ghosts").mkdir(parents=True)
    calls: list[tuple] = []
    state = {"kinds": {}, "fail": None}

    def put(path: Path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj))

    def make(name):
        def run(ctx):
            a = ctx["address"]
            calls.append((name, a))
            gd = H.ghost_dir(a)
            if state["fail"] == name:
                raise RuntimeError(f"{name} blew up")
            if name == "summon":
                put(gd / "facts.json", {"address": a, "name": "Mock"})
            elif name == "wounds":
                put(gd / "wounds.json", {"tier": "none", "findings": [], "entry": ctx.get("catalog_entry")})
            elif name == "classify":
                put(gd / "verdict.json", {"kind": state["kinds"].get(a, "friendly"), "reasons": ["r"]})
            elif name == "face":
                put(gd / "shots" / "index.json", [])
            elif name == "story":
                put(gd / "story.json", {"title": "A Title", "name": "Mock", "kind": "friendly"})
            elif name == "render":
                H.page_path(a).parent.mkdir(parents=True, exist_ok=True)
                H.page_path(a).write_text("<html>")
            elif name == "og":
                (H.page_path(a).parent / "og.png").write_bytes(b"png")
            return f"{name} done"
        return run

    for n in H.STEP_NAMES:
        monkeypatch.setitem(H.IMPL, n, make(n))
    picks = []

    def fake_pick(source, year, seed, attempt, max_blocks=None):
        calls.append(("pick", attempt))
        p = picks[attempt]
        if isinstance(p, Exception):
            raise p
        return p

    monkeypatch.setattr(H, "pick_one", fake_pick)
    return type("E", (), {"calls": calls, "state": state, "picks": picks, "tmp": tmp_path})


def names(env):
    return [c[0] for c in env.calls]


def test_order_and_record(env):
    rec = H.haunt(A1, log=lambda *a: None)
    assert names(env) == ["summon", "wounds", "classify", "face", "story", "render", "og", "gallery"]
    assert rec["ok"] and rec["kind"] == "friendly" and rec["title"] == "A Title"
    assert rec["gallery_path"] == f"web/ghosts/{A1}/"
    saved = json.loads((H.ghost_dir(A1) / "haunt.json").read_text())
    assert [s["name"] for s in saved["steps"]] == names(env)
    assert all({"name", "ok", "seconds", "note"} <= set(s) for s in saved["steps"])
    assert saved["started_at"] and saved["finished_at"]
    assert "FAILED" not in H.summary_line(saved) and "A Title" in H.summary_line(saved)


def test_deploy_only_when_asked(env):
    H.haunt(A1, log=lambda *a: None)
    assert "deploy" not in names(env)
    env.calls.clear()
    H.haunt(A1, deploy=True, log=lambda *a: None)
    assert names(env) == ["gallery", "deploy"]


def test_resume_skips_existing_outputs_and_keeps_old_timing(env):
    H.haunt(A1, log=lambda *a: None)
    env.calls.clear()
    rec = H.haunt(A1, log=lambda *a: None)
    assert names(env) == ["gallery"]  # the gallery index is rebuilt every time, it is cheap
    skipped = [s["name"] for s in rec["steps"] if s.get("skipped")]
    assert skipped == ["summon", "wounds", "classify", "face", "story", "render", "og"]
    assert "output exists" in rec["steps"][0]["note"]


def test_resume_after_failure_continues_where_it_stopped(env):
    env.state["fail"] = "story"
    rec = H.haunt(A1, log=lambda *a: None)
    assert not rec["ok"] and rec["error"].startswith("story:")
    assert names(env) == ["summon", "wounds", "classify", "face", "story"]  # chain stopped: no render, no gallery
    assert (H.ghost_dir(A1) / "facts.json").exists() and not (H.ghost_dir(A1) / "story.json").exists()
    saved = json.loads((H.ghost_dir(A1) / "haunt.json").read_text())
    assert saved["ok"] is False and saved["steps"][-1]["ok"] is False
    env.state["fail"] = None
    env.calls.clear()
    rec = H.haunt(A1, log=lambda *a: None)
    assert rec["ok"] and names(env) == ["story", "render", "og", "gallery"]


def test_force_redoes_everything(env):
    H.haunt(A1, log=lambda *a: None)
    env.calls.clear()
    H.haunt(A1, force=True, log=lambda *a: None)
    assert names(env) == ["summon", "wounds", "classify", "face", "story", "render", "og", "gallery"]


def test_face_failure_is_not_fatal(env):
    env.state["fail"] = "face"
    rec = H.haunt(A1, log=lambda *a: None)
    assert rec["ok"] and names(env)[-3:] == ["render", "og", "gallery"]
    face = next(s for s in rec["steps"] if s["name"] == "face")
    assert face["ok"] is False and "blew up" in face["note"]


def test_skip_face(env):
    rec = H.haunt(A1, skip_face=True, log=lambda *a: None)
    assert "face" not in names(env) and rec["ok"]
    assert next(s for s in rec["steps"] if s["name"] == "face")["skipped"]


def test_failure_in_summon_stops_before_anything_else(env):
    env.state["fail"] = "summon"
    rec = H.haunt(A1, log=lambda *a: None)
    assert names(env) == ["summon"] and not rec["ok"]
    assert H.summary_line(rec).startswith("FAILED")


def test_explicit_alive_address_is_not_skipped(env):
    env.state["kinds"][A1] = "alive"
    rec = H.haunt(A1, log=lambda *a: None)
    assert rec["ok"] and rec["kind"] == "alive" and "render" in names(env)


def pk(a, **extra):
    return {"address": a, "source": "random", "reason": "why", "name": "N" + a[2:4], "year": 2019, "extra": extra}


def test_picked_alive_is_moved_to_skipped_and_picker_asked_again(env):
    env.picks += [pk(A1), pk(A2)]
    env.state["kinds"][A1] = "alive"
    rec = H.haunt(source="random", log=lambda *a: None)
    assert rec["address"] == A2 and rec["ok"]
    assert [c for c in env.calls if c[0] == "pick"] == [("pick", 0), ("pick", 1)]
    assert ("face", A1) not in env.calls and ("story", A1) not in env.calls  # skipped before the expensive steps
    moved = H.skipped_dir() / A1
    assert (moved / "haunt.json").exists() and (moved / "verdict.json").exists()
    assert json.loads((moved / "haunt.json").read_text())["alive_skipped"] is True
    assert not H.ghost_dir(A1).exists() and not H.page_path(A1).exists()
    assert rec["skipped_picks"][0]["address"] == A1
    assert json.loads((H.ghost_dir(A2) / "haunt.json").read_text())["skipped_picks"]
    assert rec["steps"][0]["name"] == "pick"


def test_three_alive_picks_give_up(env):
    env.picks += [pk(A1), pk(A2), pk(A3)]
    for a in (A1, A2, A3):
        env.state["kinds"][a] = "alive"
    rec = H.haunt(source="random", log=lambda *a: None)
    assert not rec["ok"] and "3 tries" in rec["error"]
    assert len(rec["skipped_picks"]) == 3
    assert len([c for c in env.calls if c[0] == "pick"]) == 3


def test_pick_error_counts_as_a_try(env):
    env.picks += [LookupError("nothing in 120 blocks"), pk(A1)]
    rec = H.haunt(source="random", log=lambda *a: None)
    assert rec["ok"] and rec["address"] == A1


def test_earlier_skipped_address_is_not_worked_again(env):
    (H.skipped_dir() / A1).mkdir(parents=True)
    (H.skipped_dir() / A1 / "haunt.json").write_text("{}")
    env.picks += [pk(A1), pk(A2)]
    rec = H.haunt(source="random", log=lambda *a: None)
    assert rec["address"] == A2 and ("summon", A1) not in env.calls


def test_seed_retries_use_a_new_seed(monkeypatch):
    seen = []
    import ghosts.pick as P
    monkeypatch.setattr(P, "pick", lambda source, year, seed: seen.append(seed) or {})
    H.pick_one("archive", 2016, "daily", 0)
    H.pick_one("archive", 2016, "daily", 2)
    H.pick_one("archive", 2016, "fixed", 1)
    H.pick_one("archive", 2016, None, 1)
    assert seen[0] == H.resolve_seed("daily") and seen[1] == H.resolve_seed("daily") + "#2"
    assert seen[2] == "fixed#1" and seen[3] is None


def test_incident_hint_becomes_a_catalog_entry_and_reaches_wounds(env):
    pick = json.loads((FIX / "incident_pick.json").read_text())
    env.picks.append(pick)
    rec = H.haunt(source="incident", log=lambda *a: None)
    wounds = json.loads((H.ghost_dir(pick["address"]) / "wounds.json").read_text())
    e = wounds["entry"]
    assert e["incident"] is True and e["address"] == pick["address"] and e["checks"] == []
    assert "DeFiHackLabs" in e["summary"] and "~15.32 ETH" in e["summary"]
    assert rec["incident_hint"]["name"] == "JAY"


def test_incident_hint_ignored_for_other_addresses():
    pick = json.loads((FIX / "incident_pick.json").read_text())
    assert H.incident_entry(A1, pick) is None
    assert H.incident_entry(pick["address"], {"extra": {}}) is None


def test_same_address_cannot_run_twice_at_once(env):
    with H.file_lock(config.DATA / "locks" / f"{A1}.lock"):
        with pytest.raises(BlockingIOError):
            with H.file_lock(config.DATA / "locks" / f"{A1}.lock"):
                pass
        with pytest.raises(BlockingIOError):
            H.haunt(A1, log=lambda *a: None)


def test_face_without_a_site_is_ok_and_with_a_failure_raises(monkeypatch):
    import ghosts.face as Fa
    monkeypatch.setattr(Fa, "capture", lambda a, s: {"shots": [], "report": []})
    assert "no site" in H._face({"address": A1, "sites": []})
    monkeypatch.setattr(Fa, "capture", lambda a, s: {"shots": [], "report": [{"site": "x.com", "ok": False, "error": "cdx"}]})
    with pytest.raises(RuntimeError):
        H._face({"address": A1, "sites": ["x.com"]})


def test_rerun_by_address_keeps_pick_info(env):
    env.picks.append(pk(A1))
    H.haunt(source="random", log=lambda *a: None)
    rec = H.haunt(A1, log=lambda *a: None)
    assert rec["picked"]["source"] == "random" and rec["steps"][0]["name"] == "pick"


def test_og_none_is_ok_with_a_note_and_runs_again_next_time(monkeypatch):
    import ghosts.og as O
    monkeypatch.setattr(O, "make", lambda a: None)
    assert "no og.png" in H._og({"address": A1})
    assert H._out("og", A1).name == "og.png" and H._out("og", A1).parent == H.page_path(A1).parent


def test_og_skipped_when_png_exists(env):
    H.haunt(A1, log=lambda *a: None)
    assert (H.page_path(A1).parent / "og.png").exists()
    env.calls.clear()
    H.haunt(A1, log=lambda *a: None)
    assert "og" not in names(env)


def test_og_exception_is_not_fatal(env):
    env.state["fail"] = "og"
    rec = H.haunt(A1, log=lambda *a: None)
    assert rec["ok"] and names(env)[-1] == "gallery"
