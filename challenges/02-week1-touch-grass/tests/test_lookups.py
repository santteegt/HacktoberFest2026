"""Run: PYTHONPATH=src .venv/bin/python tests/test_lookups.py"""
import os
import sys
from pathlib import Path
for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USERS", "LEASH_NOTIFY_DRY_RUN"):
    os.environ.pop(k, None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leash import lookups, notify

q = lookups.extract_query
# the author's real notes from the 2026-10-10 dog walk
assert q("Remind me to search for Grogbot documentation.") == "Grogbot documentation"
assert q("Do a web search on interesting Ducks Hound online stores.") == "interesting Ducks Hound online stores"
assert q("Here's an idea. What about if we build a Skunkworks-like project so we can quickly iterate other ideas that "
         "we have been spoken during round table sessions on Raid Guild.") is None
# the 2026-10-10 evening note: the first version searched for "the web about bunker mode ..."
assert q("Search on the web about bunker mode around Ethereum and the threats on cryptography due to AI advancements.") == \
    "bunker mode around Ethereum and the threats on cryptography due to AI advancements"
assert q("Search about gemma context length") == "gemma context length"
# other ways of asking
assert q("Look up the Lume virtual machine tool for macOS.") == "the Lume virtual machine tool for macOS"
assert q("Okay, search the web for open source podcast transcription tools") == "open source podcast transcription tools"
assert q("Can you search for gemma 4 context length?") == "gemma 4 context length"
assert q("Web search whisper.cpp metal speed. Also save this as an idea.") == "whisper.cpp metal speed"
assert q("Please do an online search about tailscale serve certificates") == "tailscale serve certificates"
assert q("search for \"hermes agent profiles\"") == "hermes agent profiles"
# ideas that only mention searching, and empty requests, must not trigger
for text in ["We could search the archive for old episodes, that would be useful.",
             "I was thinking about how to look up names faster.",
             "The search for meaning is the whole point of walking.",
             "Search.", "Look up", "Remind me to call my brother.", "", None,
             "Search for " + "word " * 30]:
    assert q(text) is None, text

# message text: plain facts, no model; errors are stated, not hidden
walk = {"kind": "dog", "distance_m": 722, "duration_s": 1135, "untracked_s": 4}
lk = [{"n": 1, "query": "Grogbot documentation", "results": [{"title": "Grogbot docs", "link": "https://example.com/docs"},
                                                           {"title": "Grogbot GitHub", "link": "https://example.com/gh"}]},
      {"n": 3, "query": "dachshund stores", "error": "daily search limit reached (8); try again tomorrow"}]
t = notify.walk_text(walk, ["Remind me to search for Grogbot documentation."], [], None, None, lk)
assert 'Searched "Grogbot documentation":' in t and "1. Grogbot docs" in t and "https://example.com/gh" in t, t
assert 'Could not search for "dachshund stores": daily search limit reached (8); try again tomorrow.' in t, t
assert notify.lookup_lines({"query": "x y z", "results": []}) == ['Searched "x y z": no results.']
assert "Searched" not in notify.walk_text(walk, [], [], None, None, None)
print("lookup tests passed")
print("--- sample ---"); print(t)
