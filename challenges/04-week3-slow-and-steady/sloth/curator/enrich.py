"""Enrich: plain HTTP + trafilatura first, GitHub API for repos, a real browser (Lane 3) last.

Concurrency is bounded (8 HTTP, 4 `gh`, 1 browser) and every request has a 10 s timeout and a
polite User-Agent. Nothing here decides Valhalla; it only records what it saw.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable, Iterable
from datetime import datetime
from urllib.parse import urlsplit

import httpx
import trafilatura

from sloth.core.models import BrowserExtract, Enrichment, FetchedWith

from .collect import github_repo

try:  # Lane 3: one local headful Chrome + Stagehand session reused for many URLs
    from sloth.builder.browser import extract_with_reason as browser_extract_with_reason
    from sloth.builder.browser import session as browser_session
except ImportError:  # without Lane 3 the browser pass reads nothing
    browser_session = browser_extract_with_reason = None

USER_AGENT = "Mozilla/5.0 (compatible; SkunkworksSloth/0.1; personal reading-list triage, one fetch per link)"
TIMEOUT_S = 10
HTTP_CONCURRENCY = 8
GH_CONCURRENCY = 4
MAX_TEXT = 20_000
MIN_READABLE = 200
# Hosts where plain HTTP returns a login wall or a JS shell: go straight to the browser.
BROWSER_HOSTS = {"x.com", "twitter.com", "facebook.com", "instagram.com", "linkedin.com", "threads.net"}
DEAD_STATUSES = {404, 410}
PARKED_MARKERS = ("domain is for sale", "buy this domain", "this domain may be for sale",
                  "domain has expired", "parked free", "parkingcrew", "sedoparking")


def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def content_kind(url: str, content_type: str) -> str:
    h = host_of(url)
    if h in {"youtube.com", "youtu.be", "vimeo.com"}:
        return "video"
    if "pdf" in content_type or urlsplit(url).path.lower().endswith(".pdf"):
        return "pdf"
    if "html" in content_type or "xml" in content_type:
        return "html"
    return "other"


def readable(html: str, url: str) -> tuple[str, datetime | None, str | None]:
    """(text, published date, page title) from HTML; empty text when nothing readable."""
    text = trafilatura.extract(html, url=url, include_comments=False, include_tables=False) or ""
    published, title = None, None
    try:
        meta = trafilatura.extract_metadata(html, default_url=url)
        if meta is not None:
            title = meta.title
            if meta.date:
                published = datetime.fromisoformat(meta.date)
    except Exception:  # noqa: BLE001 - metadata is a bonus, never a failure
        pass
    return text[:MAX_TEXT], published, title


def is_parked(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in PARKED_MARKERS)


def _dns_failure(e: Exception) -> bool:
    msg = str(e).lower()
    return isinstance(e, httpx.ConnectError) and any(
        s in msg for s in ("nodename nor servname", "name or service not known", "getaddrinfo",
                           "no address associated", "name resolution"))


async def fetch_http(client: httpx.AsyncClient, link_id: int, url: str) -> Enrichment:
    """GET once, retry once on a dead-looking answer (404/410/DNS) before calling it dead."""
    last: Enrichment | None = None
    for attempt in range(2):
        try:
            r = await client.get(url)
        except Exception as e:  # noqa: BLE001 - every failure becomes data
            dead = _dns_failure(e)
            last = Enrichment(link_id=link_id, fetched_with=FetchedWith.failed,
                              error=f"{'dns' if dead else type(e).__name__}: {str(e)[:200]}")
            if dead and attempt == 0:
                await asyncio.sleep(2)
                continue
            return last
        ctype = r.headers.get("content-type", "")
        kind = content_kind(str(r.url), ctype)
        e = Enrichment(link_id=link_id, http_status=r.status_code, final_url=str(r.url), content_kind=kind,
                       fetched_with=FetchedWith.http)
        if r.status_code in DEAD_STATUSES and attempt == 0:
            await asyncio.sleep(2)
            last = e
            continue
        if r.status_code >= 400:
            e.fetched_with, e.error = FetchedWith.failed, f"http {r.status_code}"
            return e
        if kind == "html":
            text, published, _ = await asyncio.to_thread(readable, r.text, str(r.url))
            e.readable_text, e.readable_chars, e.published_at = text or None, len(text), published
            if is_parked(text or r.text[:5000]):
                e.error = "parked domain"
        return e
    return last  # type: ignore[return-value]


async def _gh(args: list[str]) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        "gh", "api", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=30)
    except TimeoutError:
        proc.kill()
        return 1, "timeout"
    return proc.returncode or 0, (out or err).decode(errors="replace")


async def fetch_github(link_id: int, owner: str, repo: str) -> Enrichment:
    """Repo metadata + README through `gh api` (keyring login, 5,000 req/h)."""
    code, out = await _gh([f"repos/{owner}/{repo}"])
    if code != 0:
        status = 404 if "Not Found" in out or "404" in out else None
        return Enrichment(link_id=link_id, http_status=status, content_kind="github",
                          fetched_with=FetchedWith.failed, error=f"gh: {out.strip()[:200]}")
    meta = json.loads(out)
    code, readme = await _gh([f"repos/{owner}/{repo}/readme", "-H", "Accept: application/vnd.github.raw"])
    parts = [meta.get("description") or "",
             ("Topics: " + ", ".join(meta.get("topics") or [])) if meta.get("topics") else "",
             f"Language: {meta['language']}" if meta.get("language") else "",
             readme if code == 0 else ""]
    text = "\n".join(p for p in parts if p)[:MAX_TEXT]
    pushed = meta.get("pushed_at")
    return Enrichment(
        link_id=link_id, http_status=200, final_url=meta.get("html_url"), content_kind="github",
        readable_text=text or None, readable_chars=len(text),
        github_stars=meta.get("stargazers_count"), github_archived=meta.get("archived"),
        github_pushed_at=datetime.fromisoformat(pushed.replace("Z", "+00:00")) if pushed else None,
        fetched_with=FetchedWith.github,
    )


def _from_browser(base: Enrichment, x: BrowserExtract) -> Enrichment:
    text = "\n".join(p for p in (x.title, x.author, x.published, x.summary_text) if p)[:MAX_TEXT]
    return base.model_copy(update={
        "readable_text": text or base.readable_text, "readable_chars": len(text),
        "fetched_with": FetchedWith.stagehand, "browser_seconds": x.seconds, "error": None,
        "content_kind": base.content_kind or "html"})


async def enrich_one(client, link: dict, sems: dict[str, asyncio.Semaphore]) -> Enrichment:
    """GitHub API for repos, plain HTTP for the rest. The browser runs later, as its own pass."""
    url = link["url"]
    if gh := github_repo(link["canonical_url"]):
        async with sems["gh"]:
            e = await fetch_github(link["id"], *gh)
        if e.fetched_with != FetchedWith.failed or e.http_status == 404:
            return e
    if host_of(url) in BROWSER_HOSTS:
        return Enrichment(link_id=link["id"], final_url=url, content_kind="html", fetched_with=FetchedWith.failed,
                          error="browser-only host")
    async with sems["http"]:
        return await fetch_http(client, link["id"], url)


async def enrich_many(links: Iterable[dict], *,
                      on_done: Callable[[Enrichment], None] | None = None) -> list[Enrichment]:
    sems = {"http": asyncio.Semaphore(HTTP_CONCURRENCY), "gh": asyncio.Semaphore(GH_CONCURRENCY)}
    async with httpx.AsyncClient(timeout=TIMEOUT_S, follow_redirects=True, max_redirects=8,
                                 headers={"User-Agent": USER_AGENT, "Accept-Language": "en"}) as client:
        async def run(link: dict) -> Enrichment:
            e = await enrich_one(client, link, sems)
            if on_done:
                on_done(e)
            return e
        return list(await asyncio.gather(*(run(link) for link in links)))


def browser_timeout(url: str) -> int:
    """Lane 3's M0.3: x.com posts finish in 10-20 s scoped; JS-only pages need up to 90 s."""
    return 45 if host_of(url) in BROWSER_HOSTS else 90


BROWSER_FAILED = "| browser: "


def browser_candidate(enr: dict | None, *, retry_failed: bool = False) -> bool:
    """Browser-only hosts and pages that answered 200 with a JS shell. Never 403/404/DNS failures:
    a real browser does not fix a blocked or dead page (coordinator ruling, CP1). A link the browser
    already failed on is skipped unless retry_failed."""
    if not enr or enr.get("content_kind") in ("github", "pdf", "video"):
        return False
    if BROWSER_FAILED in (enr.get("error") or "") and not retry_failed:
        return False
    if (enr.get("error") or "").startswith("browser-only host"):
        return True
    return enr.get("http_status") == 200 and (enr.get("readable_chars") or 0) < MIN_READABLE


def ollama_drained(max_wait_s: float = 300) -> float:
    """Block until a 1-token request to the shared model returns, i.e. requests a timed-out extract
    left running inside Ollama (one slot) have finished. Returns the seconds waited."""
    from sloth.core.config import settings
    s = settings()
    t0 = time.monotonic()
    try:
        httpx.post(f"{s.ollama_url}/api/generate", timeout=max_wait_s, json={
            "model": s.ollama_model, "prompt": "ok", "stream": False, "think": False,
            "options": {"num_ctx": s.ollama_num_ctx, "num_predict": 1}})
    except httpx.HTTPError:
        pass
    return round(time.monotonic() - t0, 1)


async def browse_many(links: list[dict], enr: dict[int, dict],
                      on_done: Callable[[Enrichment], None] | None = None,
                      on_try: Callable[[dict], None] | None = None,
                      on_fail: Callable[[int, str, float], None] | None = None) -> list[Enrichment]:
    """Re-read links with Lane 3's browser, one at a time in one session. Returns the ones it read.
    on_try gets {link_id, host, ok, seconds, reason} for every attempt (for the lane log)."""
    out: list[Enrichment] = []
    if browser_session is None:
        return out
    async with browser_session() as sh:
        for link in links:
            prev = enr.get(link["id"]) or {}
            base = Enrichment.model_validate({**prev, "link_id": link["id"],
                                              "fetched_with": prev.get("fetched_with", "failed")})
            t0 = time.monotonic()
            try:
                x, why = await browser_extract_with_reason(sh, link["url"], timeout_s=browser_timeout(link["url"]))
            except Exception as err:  # noqa: BLE001 - one bad page never stops the batch
                x, why = None, f"{type(err).__name__}: {str(err)[:120]}"
            ok = x is not None and bool(x.summary_text or x.title)
            secs = round(time.monotonic() - t0, 1)
            drained = 0.0
            if not ok and "timeout" in (why or ""):
                # The abandoned Stagehand request is still running in Ollama's single slot; wait for
                # it, or every following page queues behind it and times out too (seen 19:30-20:54Z).
                drained = await asyncio.to_thread(ollama_drained)
            if on_try:
                on_try({"link_id": link["id"], "host": host_of(link["url"]), "ok": ok,
                        "seconds": secs, "reason": why, "drain_s": drained})
            if not ok and on_fail:
                on_fail(link["id"], (why or "unknown")[:80], secs)
            if ok:
                e = _from_browser(base, x)
                out.append(e)
                if on_done:
                    on_done(e)
    return out
