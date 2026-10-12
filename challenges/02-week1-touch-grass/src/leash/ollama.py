"""Minimal Ollama chat client over the native API (stdlib only)."""
import json
import os
import time
import urllib.request

from .envfile import load_env


# One model, one context size for everything on this Mac. Ollama keeps a single 12B model loaded and reloads it
# whenever the name or the context size differs between requests; the Hermes agent uses this alias with a 64K
# context, so the server must ask for the same, or each hand-off between agent and server pays a reload.
DEFAULT_MODEL = "leash-gemma4-12b"   # created from agent/Modelfile.leash (gemma4:12b-it-qat, num_ctx 65536)
CTX = 65536


def chat(model, messages, schema=None, temperature=0.3, num_ctx=16384, think=False, timeout=1800):
    load_env()
    base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    body = {"model": model, "messages": messages, "stream": False, "think": think,
            "options": {"temperature": temperature, "num_ctx": max(num_ctx, CTX)}}
    if schema:
        body["format"] = schema
    req = urllib.request.Request(base + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.load(r)
    resp["_wall_s"] = time.time() - t0
    return resp
