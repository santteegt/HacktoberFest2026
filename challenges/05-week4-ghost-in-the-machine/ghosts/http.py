"""One HTTP door for every source: user agent, cache, retries and polite rate limits."""
from __future__ import annotations
import hashlib, json, time
from typing import Any
import httpx
from . import config

_last_call: dict[str, float] = {}
# minimum seconds between calls per host (Ethereum History: 20/min anonymous)
_MIN_GAP = {"www.ethereumhistory.com": 3.2, "web.archive.org": 1.0}


def _cache_path(key: str):
    return config.CACHE / (hashlib.sha256(key.encode()).hexdigest()[:24] + ".json")


def get_json(url: str, *, params: dict | None = None, headers: dict | None = None,
             ttl: float | None = 7 * 86400, method: str = "GET", body: Any = None,
             timeout: float = 40.0) -> Any:
    """GET (or POST with a JSON body) and parse JSON, with a file cache. ttl=None means never expire."""
    key = json.dumps([method, url, params, body], sort_keys=True)
    cp = _cache_path(key)
    if cp.exists():
        age = time.time() - cp.stat().st_mtime
        if ttl is None or age < ttl:
            return json.loads(cp.read_text())
    host = httpx.URL(url).host
    gap = _MIN_GAP.get(host, 0.2)
    wait = _last_call.get(host, 0) + gap - time.time()
    if wait > 0:
        time.sleep(wait)
    h = {"User-Agent": config.UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    for attempt in range(4):
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout) as c:
                r = c.request(method, url, params=params, headers=h, json=body) if body is not None \
                    else c.request(method, url, params=params, headers=h)
            _last_call[host] = time.time()
            if r.status_code == 429:
                time.sleep(float(r.headers.get("Retry-After", "5")) + 1)
                continue
            if r.status_code == 404:
                data = None
            else:
                r.raise_for_status()
                data = r.json()
            cp.write_text(json.dumps(data))
            return data
        except (httpx.TransportError, httpx.HTTPStatusError) as e:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    return None


def get_text(url: str, *, ttl: float | None = None, timeout: float = 60.0) -> str | None:
    key = json.dumps(["TEXT", url])
    cp = _cache_path(key)
    if cp.exists() and (ttl is None or time.time() - cp.stat().st_mtime < ttl):
        return json.loads(cp.read_text())
    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": config.UA}) as c:
        r = c.get(url)
    if r.status_code == 404:
        txt = None
    else:
        r.raise_for_status()
        txt = r.text
    cp.write_text(json.dumps(txt))
    return txt
