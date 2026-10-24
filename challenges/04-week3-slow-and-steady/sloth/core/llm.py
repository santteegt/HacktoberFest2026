"""Local model calls. One model alias and one num_ctx for everybody, so Ollama never reloads.

local_json() asks Gemma for JSON that matches a pydantic model. Ollama's `format` schema
guarantees valid JSON but the model never sees the schema, so callers must describe the
fields and allowed values in the prompt; the result is validated here and retried once.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .config import settings

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResult[M]:
    value: M
    model: str
    tokens_in: int
    tokens_out: int
    ms: int


def local_json(prompt: str, schema: type[T], *, system: str | None = None,
               retries: int = 1, timeout_s: float = 180) -> LLMResult[T]:
    s = settings()
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}]
    last_error: Exception | None = None
    for _ in range(retries + 1):
        t0 = time.monotonic()
        r = httpx.post(f"{s.ollama_url}/api/chat", timeout=timeout_s, json={
            "model": s.ollama_model, "messages": messages, "stream": False, "think": False,
            "format": schema.model_json_schema(), "options": {"num_ctx": s.ollama_num_ctx},
        })
        r.raise_for_status()
        body = r.json()
        try:
            value = schema.model_validate_json(body["message"]["content"])
        except ValidationError as e:
            last_error = e
            messages = messages + [
                {"role": "assistant", "content": body["message"]["content"]},
                {"role": "user", "content": f"That JSON was invalid: {e.errors()[:3]}. Answer again, valid JSON only."},
            ]
            continue
        return LLMResult(value, s.ollama_model, body.get("prompt_eval_count", 0),
                         body.get("eval_count", 0), int((time.monotonic() - t0) * 1000))
    raise ValueError(f"model output failed validation after {retries + 1} tries: {last_error}")
