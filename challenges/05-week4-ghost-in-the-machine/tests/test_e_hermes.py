"""Lane E: the Hermes profile distribution and its haunt script. Offline: `uv` and `hermes` are stubs on PATH."""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERMES = ROOT / "hermes"
ADDR = "0x2af47a65da8cd66729b4209c22017d6a5c2d2400"

UV_STUB = r'''#!/usr/bin/env bash
echo "uv $*" >> "$STUB_LOG"
[ "$1" = run ] && shift; [ "$1" = ghosts ] && shift
cmd="$1"; shift
A=__ADDR__
[ "${STUB_FAIL:-}" = "$cmd" ] && [ "$1" != --help ] && { [ "$cmd" = haunt ] && echo '{"address": null, "ok": false, "error": "no ghost after 3 tries"}'; exit 1; }
write_story() { mkdir -p data/ghosts/$A; echo '{"name":"Stub","kind":"friendly","title":"A stub ghost","tagline":"quiet","address":"'$A'"}' > data/ghosts/$A/story.json; echo '{"age":{"hardfork":"Byzantium"}}' > data/ghosts/$A/facts.json; }
case "$cmd" in
  haunt) [ "${STUB_HAVE_HAUNT:-0}" = 1 ] || exit 2
         [ "$1" = --help ] && exit 0
         write_story; echo '{"address": "'$A'", "ok": true}' ;;
  pick) echo $A ;;
  story) write_story ;;
  face) [ "${STUB_FACE_FAIL:-0}" = 1 ] && exit 1 ;;
esac
exit 0
'''.replace("__ADDR__", ADDR)
HERMES_STUB = '#!/usr/bin/env bash\necho "hermes $*" >> "$STUB_LOG"\n'


@pytest.fixture
def sandbox(tmp_path):
    proj = tmp_path / "proj"
    scripts = proj / "hermes" / "scripts"
    scripts.mkdir(parents=True)
    (proj / "scripts").mkdir()
    (proj / "data" / "ghosts").mkdir(parents=True)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for f in (HERMES / "scripts").glob("*.sh"):
        text = f.read_text().replace('EXTRA_PATH="__EXTRA_PATH__"', f'EXTRA_PATH="{bindir}"')
        (scripts / f.name).write_text(text)
    (bindir / "uv").write_text(UV_STUB)
    (bindir / "hermes").write_text(HERMES_STUB)
    (proj / "scripts" / "deploy.sh").write_text("#!/usr/bin/env bash\necho deployed: stub\n")
    for p in list(bindir.iterdir()):
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "calls.log"
    log.write_text("")

    def run(*args, script="haunt.sh", env=None, discord=False):
        if discord:
            (proj / "hermes" / ".env").write_text("DISCORD_BOT_TOKEN=x\nDISCORD_HOME_CHANNEL=1\n")
        e = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(tmp_path), "STUB_LOG": str(log), **(env or {})}
        return subprocess.run(["bash", str(scripts / script), *args], capture_output=True, text=True, env=e, cwd=str(tmp_path), timeout=60)

    run.proj, run.log = proj, log
    return run


def calls(sandbox):
    return [ln for ln in sandbox.log.read_text().splitlines() if ln]


def test_dry_run_prints_plan_and_runs_nothing(sandbox):
    r = sandbox("--dry-run", "--source", "archive", "--seed", "daily", "--deploy")
    assert r.returncode == 0
    assert "+ uv run ghosts haunt --source archive --seed daily --deploy --json" in r.stdout
    for step in ("pick --source archive --seed daily --dry-run", "summon", "wounds", "classify", "face", "story", "render", "bash scripts/deploy.sh"):
        assert step in r.stdout
    assert calls(sandbox) == []


def test_dry_run_with_address_and_sites(sandbox):
    r = sandbox("--dry-run", "--address", ADDR.upper().replace("0X", "0x"), "--site", "bounties.network")
    assert r.returncode == 0
    assert f"uv run ghosts haunt {ADDR} --site bounties.network --json" in r.stdout
    assert "gallery build" in r.stdout


@pytest.mark.parametrize("args", [
    ["--source", "bogus"], ["--year", "1999"], ["--seed", "a;rm -rf x"], ["--address", "0x12"], ["--site", "a b; ls"], ["--nope"],
])
def test_bad_arguments_are_refused(sandbox, args):
    r = sandbox(*args)
    assert r.returncode == 2
    assert calls(sandbox) == []


def test_wrappers_carry_their_arguments(sandbox):
    daily = sandbox("--dry-run", script="ghost-of-the-day.sh")
    assert "haunt --source archive --seed daily --deploy --json" in daily.stdout
    weekly = sandbox("--dry-run", script="weekly-incident.sh")
    assert re.search(r"haunt --source incident --seed week-\d{4}-\d{2} --deploy --json", weekly.stdout)


def test_fallback_chain_when_haunt_is_missing(sandbox):
    r = sandbox("--source", "archive", "--seed", "daily", "--deploy", env={"STUB_FACE_FAIL": "1"})
    assert r.returncode == 0, r.stderr
    order = [c.split()[3] if c.split()[3:4] else "" for c in calls(sandbox)]
    assert order == ["haunt", "pick", "summon", "wounds", "classify", "face", "story", "render"]  # face failure does not stop it
    assert r.stdout.strip().startswith("Ghost of the day: Stub (friendly, Byzantium era).")
    assert f"https://eth-ghosts.decentraminds.tech/ghosts/{ADDR}" in r.stdout


def test_haunt_present_uses_json_record_and_posts_to_discord(sandbox):
    r = sandbox("--source", "incident", "--seed", "week-1", env={"STUB_HAVE_HAUNT": "1"}, discord=True)
    assert r.returncode == 0, r.stderr
    log = calls(sandbox)
    assert "uv run ghosts haunt --source incident --seed week-1 --json" in log
    posts = [c for c in log if c.startswith("hermes -p ghosts send --to discord")]
    assert len(posts) == 1 and posts[0].endswith(r.stdout.strip())
    assert "Incident ghost:" in r.stdout
    assert "not published" in r.stdout  # no --deploy: the report says so, with no public link
    assert "eth-ghosts.decentraminds.tech" not in r.stdout
    assert (sandbox.proj / "data/cache/hermes/last-haunt.txt").read_text().strip().endswith(r.stdout.strip())


def test_no_discord_without_token_and_channel(sandbox):
    r = sandbox("--source", "archive", env={"STUB_HAVE_HAUNT": "1"})
    assert r.returncode == 0
    assert not any(c.startswith("hermes ") for c in calls(sandbox))


def test_failure_is_reported_in_code_and_exits_nonzero(sandbox):
    r = sandbox("--source", "archive", env={"STUB_HAVE_HAUNT": "1", "STUB_FAIL": "haunt"}, discord=True)
    assert r.returncode == 1
    assert "Haunt failed at step: haunt. no ghost after 3 tries" in r.stdout
    assert any(c.startswith("hermes -p ghosts send") and "Haunt failed" in c for c in calls(sandbox))


def test_failed_step_in_fallback_names_the_step(sandbox):
    r = sandbox("--address", ADDR, env={"STUB_FAIL": "story"})
    assert r.returncode == 1
    assert "failed at step: story" in r.stdout
    assert not any(" render " in c for c in calls(sandbox))


def test_read_only_modes(sandbox):
    web = sandbox.proj / "web" / "ghosts"
    web.mkdir(parents=True)
    (web / "index.json").write_text(json.dumps([{"address": ADDR, "name": "StandardBounties", "kind": "lingering", "age": "Byzantium"}]))
    gd = sandbox.proj / "data" / "ghosts" / ADDR
    gd.mkdir(parents=True)
    (gd / "verdict.json").write_text(json.dumps({"kind": "lingering", "reasons": ["27 calls in the last 12 months"]}))
    (gd / "wounds.json").write_text(json.dumps({"findings": [{"title": "Reentrancy in contribute", "impact": "Medium", "confidence": "Medium", "confirmed": False}]}))
    assert "StandardBounties | lingering | Byzantium" in sandbox("--list").stdout
    v = sandbox("--verdict", ADDR).stdout
    assert "kind: lingering" in v and "suspected: Reentrancy in contribute" in v
    assert "no story.json" in sandbox("--show", ADDR).stdout
    assert "no haunt has finished yet" in sandbox("--status").stdout
    assert calls(sandbox) == []


# ----------------------------------------------------------------------------- the distribution files


def test_cron_jobs_ship_paused_and_point_at_existing_scripts():
    jobs = json.loads((HERMES / "cron" / "jobs.json").read_text())["jobs"]
    assert {j["name"] for j in jobs} == {"ghost-of-the-day", "weekly-incident"}
    assert len({j["id"] for j in jobs}) == 2
    for j in jobs:
        assert j["no_agent"] is True and j["enabled"] is False and j["state"] == "paused"
        assert (HERMES / "scripts" / j["script"]).is_file()
    daily = next(j for j in jobs if j["name"] == "ghost-of-the-day")
    assert daily["schedule"]["expr"].split()[2:] == ["*", "*", "*"]  # every day


def test_skill_description_lists_the_request_phrases():
    text = (HERMES / "skills/ghost-stories/SKILL.md").read_text()
    head = text.split("---")[1]
    for phrase in ("tell a ghost story", "haunt", "summon a contract", "today's ghost", "who is in the gallery"):
        assert phrase in head
    assert len(re.search(r'description: "(.*)"\n', head).group(1)) < 1024
    assert "haunt.sh" in text


def test_soul_has_the_skill_first_rule():
    soul = (HERMES / "SOUL.md").read_text()
    assert "hard rule" in soul and "ghost-stories" in soul and "never invent chain facts" in soul.lower()


def test_config_fragment_has_the_required_keys():
    cfg = (HERMES / "config.yaml").read_text()
    for needle in ("default: ghosts-gemma4-12b", "provider: custom", "base_url: http://localhost:11434/v1",
                   "ethereum_history:", 'url: "https://www.ethereumhistory.com/mcp"', "deny:", "- sudo", "- launchctl *", "- crontab *",
                   "- security *", "discord:", "tool_progress: 'off'", "cwd: __GHOSTS_HOME__"):
        assert needle in cfg, needle


def test_distribution_manifest_and_env_example_carry_names_only():
    manifest = (HERMES / "distribution.yaml").read_text()
    names = re.findall(r"- name: ([A-Z_]+)", manifest)
    assert names == ["DISCORD_BOT_TOKEN", "DISCORD_ALLOWED_USERS", "DISCORD_ALLOWED_CHANNELS", "DISCORD_FREE_RESPONSE_CHANNELS", "DISCORD_HOME_CHANNEL", "VERCEL_TOKEN"]
    for line in (HERMES / ".env.example").read_text().splitlines():
        if line and not line.startswith("#"):
            name, _, value = line.partition("=")
            assert name in names and value == ""


def test_no_secret_shaped_strings_in_the_distribution():
    pat = re.compile(r"(MT[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{20,}|vcp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|0x[0-9a-f]{64})")
    for f in HERMES.rglob("*"):
        if f.is_file():
            assert not pat.search(f.read_text()), f


def test_placeholders_are_only_the_three_known_ones():
    for f in HERMES.rglob("*"):
        if f.is_file() and f.name != "install.sh":
            found = set(re.findall(r"__[A-Z_]+__", f.read_text()))
            assert found <= {"__GHOSTS_HOME__", "__PROFILE_HOME__", "__EXTRA_PATH__"}, (f, found)


def test_scripts_are_executable_and_parse():
    for f in [*(HERMES / "scripts").glob("*.sh"), HERMES / "install.sh"]:
        assert os.access(f, os.X_OK), f
        assert subprocess.run(["bash", "-n", str(f)]).returncode == 0
