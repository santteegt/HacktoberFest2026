"""Enrich: plain HTTP + trafilatura first, GitHub API for repos, a real browser (Lane 3) last.

Concurrency is bounded (8 HTTP, 4 `gh`, 1 browser) and every request has a 10 s timeout and a
polite User-Agent. Nothing here decides Valhalla; it only records what it saw.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Iterable
from datetime import datetime
from urllib.parse import urlsplit

import httpx
import trafilatura

from sloth.core.models import BrowserExtract, Enrichment, FetchedWith

from .collect import github_repo

try:  # Lane 3 lands sloth.builder.browser.extract(url, *, timeout_s=45) -> BrowserExtract | None
    from sloth.builder.browser import extract as browser_extract
except ImportError:  # until then: a browser that can never read anything
    def browser_extract(url: str, *, timeout_s: int = 45) -> BrowserExtract | None:  # noqa: ARG001
        return None
try:  # Lane 3's batch API: one Chrome session reused for many URLs (their M0.3 advice)
    from sloth.builder.browser import extract_with as browser_extract_with
    from sloth.builder.browser import session as browser_session
except ImportError:
    browser_session = browser_extract_with = None

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


def needs_browser(url: str, readable_chars: int) -> bool:
    return host_of(url) in BROWSER_HOSTS or readable_chars < MIN_READABLE


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


async def enrich_one(client, link: dict, sems: dict[str, asyncio.Semaphore], *, use_browser: bool,
                     browser: Callable = None) -> Enrichment:  # type: ignore[assignment]
    url = link["url"]
    if gh := github_repo(link["canonical_url"]):
        async with sems["gh"]:
            e = await fetch_github(link["id"], *gh)
        if e.fetched_with != FetchedWith.failed or e.http_status == 404:
            return e
    if host_of(url) in BROWSER_HOSTS:
        e = Enrichment(link_id=link["id"], final_url=url, content_kind="html", fetched_with=FetchedWith.failed,
                       error="browser-only host")
    else:
        async with sems["http"]:
            e = await fetch_http(client, link["id"], url)
    dead = e.http_status in DEAD_STATUSES or (e.error or "").startswith("dns")
    if use_browser and not dead and e.content_kind in (None, "html") and needs_browser(url, e.readable_chars):
        async with sems["browser"]:
            try:
                x = await asyncio.to_thread(browser or browser_extract, url)
            except Exception as err:  # noqa: BLE001 - the browser is best effort
                x, e.error = None, (e.error or "") + f" | browser: {type(err).__name__}"
        if x is not None and (x.summary_text or x.title):
            e = _from_browser(e, x)
    return e


async def enrich_many(links: Iterable[dict], *, use_browser: bool = True, browser: Callable | None = None,
                      on_done: Callable[[Enrichment], None] | None = None) -> list[Enrichment]:
    sems = {"http": asyncio.Semaphore(HTTP_CONCURRENCY), "gh": asyncio.Semaphore(GH_CONCURRENCY),
            "browser": asyncio.Semaphore(1)}
    async with httpx.AsyncClient(timeout=TIMEOUT_S, follow_redirects=True, max_redirects=8,
                                 headers={"User-Agent": USER_AGENT, "Accept-Language": "en"}) as client:
        async def run(link: dict) -> Enrichment:
            e = await enrich_one(client, link, sems, use_browser=use_browser, browser=browser)
            if on_done:
                on_done(e)
            return e
        return list(await asyncio.gather(*(run(link) for link in links)))


def browser_timeout(url: str) -> int:
    """Lane 3's M0.3: x.com posts finish in 10-20 s scoped; JS-only pages need up to 90 s."""
    return 45 if host_of(url) in BROWSER_HOSTS else 90


async def browse_many(links: list[dict], enr: dict[int, dict],
                      on_done: Callable[[Enrichment], None] | None = None) -> list[Enrichment]:
    """Re-read links with the real browser, one at a time, in one session when Lane 3 offers it.
    Returns only the links the browser could read."""
    out: list[Enrichment] = []

    async def one(read, link: dict) -> None:
        base = Enrichment.model_validate({**(enr.get(link["id"]) or {}), "link_id": link["id"],
                                          "fetched_with": (enr.get(link["id"]) or {}).get("fetched_with", "failed")})
        try:
            x = await read(link["url"])
        except Exception:  # noqa: BLE001 - one bad page never stops the batch
            x = None
        if x is not None and (x.summary_text or x.title):
            e = _from_browser(base, x)
            out.append(e)
            if on_done:
                on_done(e)

    if browser_session is not None:
        async with browser_session() as sh:
            for link in links:
                await one(lambda u: browser_extract_with(sh, u, timeout_s=browser_timeout(u)), link)
    else:
        for link in links:
            await one(lambda u: asyncio.to_thread(browser_extract, u, timeout_s=browser_timeout(u)), link)
    return out
