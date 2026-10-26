import pytest


def fake_namer(vertical, topics, k):
    """Two subtopics per vertical from the topic words, no model."""
    words = sorted({w for t in topics for w in t.lower().split() if len(w) > 3}) or [vertical]
    half = max(1, len(words) // 2)
    return [{"name": f"{vertical} {words[0]}", "description": f"First half of {vertical}.", "keywords": words[:half]},
            {"name": f"{vertical} {words[-1]}", "description": f"Second half of {vertical}.", "keywords": words[half:]}]


@pytest.fixture(autouse=True)
def offline_taxonomy(monkeypatch, tmp_path):
    """Board tests never call Gemma or the embedder, and never touch the real .sloth cache."""
    from sloth.board import taxonomy

    def no_embed(texts):
        raise RuntimeError("embedder disabled in tests")
    monkeypatch.setattr(taxonomy, "CACHE_PATH", tmp_path / "brain-taxonomy.json")
    monkeypatch.setattr(taxonomy, "name_subtopics", fake_namer)
    monkeypatch.setattr(taxonomy, "embed_ollama", no_embed)
