"""Thin client for the local open-weight model (Gemma 4 12B through Ollama's /api/chat).

One model name and one context size everywhere, so Ollama never reloads the model between calls.
`think` is off by default: with thinking on, Gemma spent ~1,000 tokens thinking before a one-sentence answer.
"""
from __future__ import annotations
import json
import os
import time
from typing import Any

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("GHOSTS_MODEL", "gemma4:12b-it-qat")
NUM_CTX = int(os.environ.get("GHOSTS_NUM_CTX", "8192"))  # one size for every caller; <= 16384
TIMEOUT = float(os.environ.get("GHOSTS_LLM_TIMEOUT", "600"))


class LLMError(RuntimeError):
    pass


def new_usage() -> dict:
    return {"calls": 0, "seconds": 0.0, "wall_seconds": 0.0, "prompt_tokens": 0, "output_tokens": 0}


def add_usage(total: dict, u: dict) -> dict:
    for k in ("calls", "seconds", "wall_seconds", "prompt_tokens", "output_tokens"):
        total[k] = round(total.get(k, 0) + u.get(k, 0), 3) if isinstance(u.get(k, 0), float) else total.get(k, 0) + u.get(k, 0)
    return total


def _post(body: dict) -> dict:
    r = httpx.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _parse_json(text: str) -> Any:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        t = t[t.find("\n") + 1:] if "\n" in t else t
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        a, b = t.find("{"), t.rfind("}")
        if a >= 0 and b > a:
            return json.loads(t[a:b + 1])
        raise


def chat(messages: list[dict], schema: dict | None = None, think: bool = False, temperature: float = 0.6,
         num_ctx: int = NUM_CTX, model: str = MODEL, post=None) -> tuple[Any, dict]:
    """Non-streaming chat. Returns (parsed JSON when `schema` is given, else text; usage).

    usage = {calls, seconds (Ollama total_duration), wall_seconds, prompt_tokens, output_tokens}.
    With a schema, a reply that does not parse as JSON is retried once; the second failure raises LLMError.
    `post` lets tests inject a fake transport.
    """
    post = post or _post
    body: dict = {"model": model, "messages": messages, "stream": False, "think": think,
                  "options": {"temperature": temperature, "num_ctx": min(num_ctx, 16384)}}
    if schema is not None:
        body["format"] = schema
    usage = new_usage()
    attempts = 2 if schema is not None else 1
    last_err = None
    for _ in range(attempts):
        t0 = time.monotonic()
        resp = post(body)
        usage["calls"] += 1
        usage["wall_seconds"] = round(usage["wall_seconds"] + time.monotonic() - t0, 3)
        usage["seconds"] = round(usage["seconds"] + (resp.get("total_duration") or 0) / 1e9, 3)
        usage["prompt_tokens"] += int(resp.get("prompt_eval_count") or 0)
        usage["output_tokens"] += int(resp.get("eval_count") or 0)
        text = ((resp.get("message") or {}).get("content") or "").strip()
        if schema is None:
            return text, usage
        try:
            return _parse_json(text), usage
        except (json.JSONDecodeError, ValueError) as ex:
            last_err = ex
    raise LLMError(f"model returned malformed JSON twice: {last_err}")
