import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from sloth.core.models import FetchedWith, Kind, Triage, Vertical
from sloth.curator import collect as col
from sloth.curator import enrich, measure, report, rules, triage
from sloth.curator.pipeline import BatchResult, Item

FIX = Path(__file__).parents[1] / "fixtures"
LINKS = json.loads((FIX / "links.json").read_text())
NOW = datetime(2026, 10, 24, tzinfo=UTC)


def to_chrome(dt: datetime) -> str:
    return str(int((dt - datetime(1601, 1, 1, tzinfo=UTC)) / timedelta(microseconds=1)))


def bookmarks_file(tmp_path: Path) -> Path:
    """A Chrome Bookmarks JSON with the fixture links under bookmark_bar → Reading List/<subfolders>."""
    folders: dict[str, list] = {}
    for x in LINKS:
        sub = x["folder_path"].removeprefix("Reading List").strip("/")
        saved = datetime.fromisoformat(x["saved_at"].replace("Z", "+00:00"))
        folders.setdefault(sub, []).append({"type": "url", "name": x["title"], "url": x["url"],
                                            "date_added": to_chrome(saved)})
    children = folders.pop("", []) + [{"type": "folder", "name": k, "children": v} for k, v in folders.items()]
    data = {"roots": {"bookmark_bar": {"children": [
        {"type": "folder", "name": "Other stuff", "children": [{"type": "url", "name": "x", "url": "https://a.b"}]},
        {"type": "folder", "name": "Reading List", "children": children}]}, "other": {"children": []}}}
    p = tmp_path / "Bookmarks"
    p.write_text(json.dumps(data))
    return p


def test_canonical_url_matches_fixture():
    for x in LINKS:
        assert col.canonical_url(x["url"]) == x["canonical_url"]


@pytest.mark.parametrize("raw,canon", [
    ("https://WWW.Example.com/a/?utm_source=x&b=2&a=1#section", "https://www.example.com/a?a=1&b=2"),
    ("https://twitter.com/u/status/1?s=20&t=abc", "https://x.com/u/status/1"),
    ("https://github.com/Owner/Repo/", "https://github.com/owner/repo"),
    ("https://app.example.com/#/route", "https://app.example.com/#/route"),
    ("https://example.com/", "https://example.com"),
])
def test_canonical_url_rules(raw, canon):
    assert col.canonical_url(raw) == canon


def test_chrome_time():
    assert col.chrome_time("13303000000000000") == datetime(2022, 7, 22, 21, 46, 40, tzinfo=UTC)  # unix 1658526400
    assert col.chrome_time(to_chrome(NOW)) == NOW
    assert col.chrome_time("0") is None


def test_collect_reads_only_the_folder_and_dedupes(tmp_path):
    c = col.collect(bookmarks_file(tmp_path))
    assert c.folder_found
    assert len(c.links) + len(c.exact_duplicates) == len(LINKS)
    assert len(c.exact_duplicates) == 1  # the #dup fragment copy
    assert all(link.folder_path.startswith("Reading List") for link in c.links)
    assert all(link.canonical_url != "https://a.b" for link in c.links)
    first = next(link for link in c.links if link.canonical_url == LINKS[0]["canonical_url"])
    assert first.saved_at == datetime(2025, 1, 10, 12, tzinfo=UTC)


def test_collect_missing_folder(tmp_path):
    assert not col.collect(bookmarks_file(tmp_path), folder="Nope").folder_found


def test_github_repo_and_dedupe_key():
    assert col.github_repo("https://github.com/o/r/blob/main/x.md") == ("o", "r")
    assert col.github_repo("https://github.com/orgs/o") is None
    assert col.github_repo("https://gitlab.com/o/r") is None
    assert col.dedupe_key("https://github.com/O/R/tree/main") == col.dedupe_key("http://www.github.com/o/r")


def _row(i, url, saved, **kw):
    return {"id": i, "url": url, "canonical_url": col.canonical_url(url), "saved_at": saved, "title": f"t{i}", **kw}


def test_rules():
    a = _row(1, "https://github.com/o/r", NOW - timedelta(days=300))
    b = _row(2, "https://github.com/o/r/tree/main", NOW - timedelta(days=10))
    c = _row(3, "https://example.com/post", NOW - timedelta(days=5))
    d = _row(4, "https://short.ly/x", NOW - timedelta(days=1), final_url="https://example.com/post")
    idx = rules.DupeIndex([a, b, c, d])
    assert rules.judge(b, None, idx).rule == "duplicate"
    assert rules.judge(d, {"final_url": "https://example.com/post"}, idx).reason == "duplicate of #3 (saved earlier)"
    assert rules.judge(a, None, idx) is None
    assert rules.judge(c, {"http_status": 404}, idx, now=NOW).rule == "dead"
    assert rules.judge(c, {"error": "dns: nodename nor servname"}, idx, now=NOW).rule == "dead"
    assert rules.judge(c, {"http_status": 403, "error": "http 403"}, idx, now=NOW) is None  # blocked, not dead
    assert rules.judge(a, {"github_archived": True, "github_stars": 9}, idx, now=NOW).rule == "archived"
    old = {"github_archived": False, "github_pushed_at": NOW - timedelta(days=5 * 365)}
    assert rules.judge(a, old, idx, now=NOW).rule == "stale"
    fresh = {"github_archived": False, "github_pushed_at": NOW - timedelta(days=30)}
    assert rules.judge(a, fresh, idx, now=NOW) is None


def _t(**kw):
    base = dict(topic="vector search", vertical=Vertical.llms, kind=Kind.tutorial, still_relevant=True,
                reason="The title promises a pgvector tutorial with 1200 stars.", buildable=2,
                one_line_idea="Index my notes with pgvector.")
    return Triage(**{**base, **kw})


def test_verifier():
    src = "Title: Hands-on pgvector tutorial\nGitHub: 1200 stars"
    assert triage.verify(_t(), src) == []
    assert triage.verify(_t(reason="A really useful and interesting resource to learn from."), src)
    assert triage.verify(_t(one_line_idea=None), src)
    assert triage.normalize(_t(buildable=1)).one_line_idea is None


def test_link_input_hides_walls_and_cites_facts():
    link = {"url": "https://example.com/a", "title": "Hands-on pgvector", "folder_path": "Reading List/LLMs",
            "saved_at": NOW}
    wall = {"readable_text": "Sign in to continue. Create an account.", "content_kind": "html"}
    s = triage.link_input(link, wall, today=NOW)
    assert "could not read" in s and "Saved: 2026-10-24" in s and "Sign in" not in s
    gh = {"content_kind": "github", "github_stars": 42, "github_pushed_at": NOW, "readable_text": "A tiny lib."}
    assert "42 stars, last push 2026-10-24" in triage.link_input(link, gh, today=NOW)


def test_decide():
    link = {"title": "short"}
    lab = triage.Labelled(_t(still_relevant=False), True, [], "m", 1, 1, 1, 1)
    assert triage.decide(lab, link, None) == "unsure"  # no page text and a short title
    assert triage.decide(lab, {"title": "x" * 50}, None) == "valhalla"
    assert triage.decide(triage.Labelled(_t(), True, [], "m", 1, 1, 1, 1), link, None) == "kept"
    assert triage.decide(triage.Labelled(_t(buildable=1), True, [], "m", 1, 1, 1, 1), link, None) == "reading"
    assert triage.decide(triage.Labelled(_t(), False, ["x"], "m", 1, 1, 1, 2), link, None) == "unsure"


def test_read_only_kinds_are_capped():
    assert triage.normalize(_t(kind=Kind.thread, buildable=3)).buildable == 1
    assert triage.normalize(_t(kind=Kind.library, buildable=3)).buildable == 3


def _result():
    items = [Item(1, "Kept one", "u1", "kept", "r", "model", buildable=3, one_line_idea="Build a CLI"),
             Item(2, "Dead one", "u2", "valhalla", "dead link: page returns HTTP 404", "code", rule="dead"),
             Item(3, "Meh", "u3", "valhalla", "old hype", "model"),
             Item(4, "Huh", "u4", "unsure", "r", "model")]
    return BatchResult("b1", items, seconds=372, tokens_in=1000, tokens_out=200, model_seconds=60, model="g")


def test_batch_summary_and_log_line():
    r = _result()
    s = report.batch_summary(r)
    assert "to build 1" in s and "to read 0" in s and "Valhalla 2 (1 dead, 1 by Gemma)" in s and "unsure 1" in s
    assert "#1 Kept one → Build a CLI" in s and "#4 Huh" in s
    assert report.log_line(r) == "batch b1: 4 in, 1 to build, 0 to read, 2 Valhalla, 1 unsure, 6m12s"
    assert "nothing left" in report.batch_summary(BatchResult("b2"))


def test_valhalla_messages_chunk_under_discord_limit():
    rows = [{"link_id": i, "title": "T" * 80, "reason": "R" * 150, "decided_by": "code"} for i in range(60)]
    msgs = report.valhalla_messages(rows)
    assert len(msgs) > 1 and all(len(m) <= report.DISCORD_LIMIT for m in msgs)
    assert "`#0`" in msgs[0] and "`#59`" in msgs[-1]
    assert report.valhalla_messages([])[0].endswith("empty.")


def test_write_export(tmp_path):
    p = report.write_export([{"link_id": 1, "url": "https://e.com", "title": "E", "folder_path": "RL",
                              "reason": "dead"}], now=NOW, out_dir=tmp_path)
    assert "- [ ] [E](https://e.com)" in p.read_text()
    assert json.loads(p.with_suffix(".json").read_text())[0]["link_id"] == 1


def test_fetch_http_dead_after_retry_and_blocked_is_not_dead(monkeypatch):
    real_sleep = asyncio.sleep
    monkeypatch.setattr(enrich.asyncio, "sleep", lambda s: real_sleep(0))
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if req.url.path == "/gone":
            return httpx.Response(404)
        if req.url.path == "/blocked":
            return httpx.Response(403)
        return httpx.Response(200, headers={"content-type": "text/html"},
                              html="<html><body><article><p>" + "Readable words here. " * 30 + "</p></article></body></html>")

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            return [await enrich.fetch_http(c, 1, f"https://e.com/{p}") for p in ("gone", "blocked", "ok")]

    gone, blocked, ok = asyncio.run(go())
    assert gone.http_status == 404 and calls["n"] == 4  # 404 fetched twice
    assert blocked.fetched_with == FetchedWith.failed and blocked.error == "http 403"
    assert ok.fetched_with == FetchedWith.http and ok.readable_chars > 200


def test_browser_candidates_skip_blocked_and_dead():
    assert enrich.browser_candidate({"error": "browser-only host", "content_kind": "html"})
    assert enrich.browser_candidate({"http_status": 200, "readable_chars": 40, "content_kind": "html"})
    assert not enrich.browser_candidate({"http_status": 200, "readable_chars": 4000, "content_kind": "html"})
    assert not enrich.browser_candidate({"http_status": 403, "error": "http 403"})
    assert not enrich.browser_candidate({"http_status": 404})
    assert not enrich.browser_candidate({"http_status": 200, "readable_chars": 10, "content_kind": "github"})
    assert enrich.browser_timeout("https://x.com/a/status/1") == 45
    assert enrich.browser_timeout("https://kaggle.com/learn") == 90


def test_parse_labels():
    text = ("## 1. A\n<https://a>\nid 12 · RL · saved 2026-01-01\n\nkeep: y\nbuild: 3\n\n"
            "## 2. B\n<https://b>\nid 13 · RL · saved 2026-01-01\n\nkeep: ?\nbuild: ?\n")
    assert measure.parse_labels(text) == {12: {"keep": True, "build": 3}}


def test_cli_registers():
    from typer.testing import CliRunner

    from sloth.cli import app
    out = CliRunner().invoke(app, ["--help"]).output
    assert "curate" in out and "valhalla" in out and "curator" in out
