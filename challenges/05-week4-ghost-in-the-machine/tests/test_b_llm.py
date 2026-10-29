"""Lane B: the Ollama client, with a fake transport (offline)."""
import pytest

from ghosts import llm


def resp(content, pe=10, ev=5, dur=2_000_000_000):
    return {"message": {"content": content}, "prompt_eval_count": pe, "eval_count": ev, "total_duration": dur}


def test_body_and_usage():
    seen = []

    def post(body):
        seen.append(body)
        return resp('{"a": 1}')

    out, u = llm.chat([{"role": "user", "content": "hi"}], schema={"type": "object"}, post=post, num_ctx=99999)
    assert out == {"a": 1}
    b = seen[0]
    assert b["think"] is False and b["stream"] is False and b["format"] == {"type": "object"}
    assert b["options"]["num_ctx"] == 16384 and b["model"] == llm.MODEL
    assert u["calls"] == 1 and u["prompt_tokens"] == 10 and u["output_tokens"] == 5 and u["seconds"] == 2.0


def test_retry_once_on_malformed_json():
    replies = iter([resp("not json at all"), resp('```json\n{"ok": true}\n```')])
    out, u = llm.chat([], schema={}, post=lambda b: next(replies))
    assert out == {"ok": True} and u["calls"] == 2 and u["prompt_tokens"] == 20


def test_malformed_twice_raises():
    with pytest.raises(llm.LLMError):
        llm.chat([], schema={}, post=lambda b: resp("{broken"))


def test_text_mode_no_retry():
    out, u = llm.chat([], post=lambda b: resp("  plain  "))
    assert out == "plain" and u["calls"] == 1


def test_add_usage():
    t = llm.new_usage()
    llm.add_usage(t, {"calls": 1, "seconds": 1.5, "wall_seconds": 1.6, "prompt_tokens": 3, "output_tokens": 4})
    llm.add_usage(t, {"calls": 1, "seconds": 1.0, "wall_seconds": 1.0, "prompt_tokens": 3, "output_tokens": 4})
    assert t == {"calls": 2, "seconds": 2.5, "wall_seconds": 2.6, "prompt_tokens": 6, "output_tokens": 8}
