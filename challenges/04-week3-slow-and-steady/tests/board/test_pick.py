from datetime import UTC, date, datetime, timedelta

from sloth.board import brain, focus, pick
from sloth.core.models import PickOption

TODAY = date(2026, 10, 24)


def card(cid, vertical, title="A card title"):
    return {"id": cid, "vertical": vertical, "title": title, "learning_goal": "Learn x.",
            "box_minutes": 120, "done_means": "tests pass", "link_ids": [1], "column": "backlog"}


def test_glossary_maps_buttons_and_words():
    assert focus.glossary_weights("AI agents (3 cards)") == {"ai-agents": 1.0}
    assert focus.glossary_weights("rust and anything with agents") == {"rust": 1.0, "ai-agents": 1.0}
    assert focus.glossary_weights("zero-knowledge proofs") == {"cryptography": 1.0}
    assert focus.glossary_weights("html templates") == {}  # "ml" must not match inside a word
    assert focus.BUTTON.fullmatch("Security and privacy (1 card)")


def test_weights_encode_roundtrip_and_parse():
    w = {"rust": 0.5, "ai-agents": 1.0}
    assert focus.encode(w) == ["ai-agents:1", "rust:0.5"]
    assert focus.decode(focus.encode(w)) == w
    assert focus.parse_weights("ai-agents=1, rust=0.5") == w
    try:
        focus.parse_weights("nope=1")
        raise AssertionError("unknown vertical accepted")
    except ValueError:
        pass


def test_focus_question_has_at_most_four_choices():
    q = focus.focus_question({"rust": 1, "llms": 5, "ai-agents": 3, "hardware": 2, "other": 0})
    assert q["choices"] == ["LLMs (5 cards)", "AI agents (3 cards)", "Hardware (2 cards)", focus.SURPRISE]
    assert focus.week_start(TODAY) == date(2026, 10, 19)


def test_scoring_prefers_focus_then_freshness_then_novelty():
    w = {"rust": 1.0}
    fresh = TODAY - timedelta(days=5)
    old = TODAY - timedelta(days=400)
    a = pick.score_card(card("ka", "rust"), old, w, None, TODAY)
    b = pick.score_card(card("kb", "llms"), fresh, w, None, TODAY)
    assert a.score > b.score  # focus outweighs freshness
    c = pick.score_card(card("kc", "llms"), fresh, None, TODAY - timedelta(days=1), TODAY)
    d = pick.score_card(card("kd", "llms"), fresh, None, None, TODAY)
    assert d.score > c.score  # a vertical picked yesterday loses to an untouched one
    assert "never picked" in d.reasons() and "matches this week's focus" in a.reasons()


def test_select_spreads_verticals_then_fills():
    scored = [pick.score_card(card(f"k{i}", v), TODAY, {"rust": 1.0}, None, TODAY)
              for i, v in enumerate(["rust", "rust", "rust", "llms"])]
    chosen = pick.select(scored, 3)
    assert len(chosen) == 3
    assert {s.card["vertical"] for s in chosen} == {"rust", "llms"}
    assert pick.select(scored, 4)[-1].card["vertical"] == "llms"  # lowest score last


def test_wording_fallback_is_code():
    s = [pick.score_card(card("ka", "rust", "x" * 90), TODAY, None, None, TODAY)]
    opts, trace = pick.word_options(s, use_model=False)
    assert trace["fallback"] and len(opts[0].label) <= 60 and opts[0].card_id == "ka"


def test_recommended_suffix_is_stripped():
    assert pick.RECOMMENDED.sub("", "Build a ledger (Recommended)") == "Build a ledger"


def test_discord_texts():
    opts = [PickOption(card_id="ka", label="Build a ledger", why="Fresh links.")]
    text = pick.pick_text(opts)
    assert "1. **Build a ledger** (`ka`): Fresh links." in text and pick.QUESTION in text
    c = card("ka", "rust", "Ledger")
    assert "120-minute box" in pick.picked_text(c)
    assert pick.worker_ping_text(c) == "Card `ka` is today's pick. Reply `go` here to start the 120-minute box."
    saved = focus.focus_saved_text({"weights": {"rust": 1.0}})
    assert "Rust" in saved
    assert "no focus" in focus.focus_saved_text({"weights": {}})


def test_brain_card_page_reads_notes(tmp_path):
    (tmp_path / "NOTES.md").write_text("# NOTES\n\n## Learned\nThings.\n")
    run = {"outcome": "done", "approved": True, "model_id": "m/x", "cost_usd": 0.05,
           "repo_url": "https://github.com/u/r", "repo_dir": str(tmp_path), "notes_path": "NOTES.md",
           "started_at": datetime(2026, 10, 24, 14, tzinfo=UTC), "ended_at": datetime(2026, 10, 24, 15, 30, tzinfo=UTC)}
    c = {**card("ka", "rust", "Ledger"), "column": "built", "kill_criteria": "k", "hypothesis": "I can.",
         "picked_on": TODAY}
    page = brain.card_page(c, {}, run, [run], "2026-10-24T00:00:00Z")
    assert page.startswith("---\ntype: prototype\n")
    assert "### Learned" in page and "90 min, $0.05" in page and "Total cost: $0.05" in page
    assert brain.notes_for(None) == (None, None)
