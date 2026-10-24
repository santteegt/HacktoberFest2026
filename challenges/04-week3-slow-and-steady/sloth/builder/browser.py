"""Stagehand v4 on a local, throwaway Chrome, with the local Gemma alias as its LLM.

Lane 3 → Lane 1 contract: `extract(url, *, timeout_s=45) -> BrowserExtract | None`.
None means the browser could not read the page (timeout, login wall, empty page, model
failure); the Curator then records `fetched_with='failed'`.

Stagehand v4 has no base-URL option for self-hosted models, so the model goes through its
bring-your-own-LLM callback: `_gemma_generate` calls Ollama's OpenAI-compatible endpoint
with the same alias as `sloth.core.llm` (num_ctx is baked into the alias, so Ollama never
reloads). The browser is a fresh temporary profile, never the author's Chrome profile.
"""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any

from pydantic import AnyUrl, BaseModel, Field

from ..core.config import settings
from ..core.models import BrowserExtract

# Pages that only render for a logged-in user say so in their text; treat them as unread.
LOGIN_WALL_MARKERS = (
    "sign in to x", "log in to x", "don't miss what's happening", "join x today",
    "log in to facebook", "you must log in", "sign up to see",
    "access to x.com was denied", "http error 403",
)
SETTLE_S = 8          # max seconds to wait for client-side rendering after DOMContentLoaded
MIN_TEXT_CHARS = 80   # below this the page did not render anything worth extracting

INSTRUCTION = (
    "Extract the main content of this page: its title, the author (person or account), "
    "the publication date as written on the page, a plain-text summary of what the page says "
    "in at most 5 sentences (use only facts visible on the page), and up to 10 outbound links "
    "that the main content points to (absolute URLs). Use null for anything not on the page."
)


class _PageText(BaseModel):
    """Fallback schema without links: used when the model picks a link id Stagehand cannot map."""
    title: str | None = Field(description="Title of the page or post")
    author: str | None = Field(description="Author name or account handle, null if not shown")
    published: str | None = Field(description="Publication date as written on the page, null if not shown")
    summary_text: str = Field(description="2-5 plain sentences on what the page says, only facts visible on it")


class _PageContent(_PageText):
    """What we ask the model for; seconds and model are filled in by code."""
    outbound_links: list[AnyUrl] = Field(description="Up to 10 links the main content points to")


def _content_text(content: Any) -> str:
    blocks = content if isinstance(content, list) else [content]
    parts = []
    for block in blocks:
        b = getattr(block, "root", block)
        if getattr(b, "type", None) == "text":
            parts.append(b.text)
    return "\n".join(parts)


def _openai_client():
    from openai import AsyncOpenAI
    return AsyncOpenAI(base_url=f"{settings().ollama_url}/v1", api_key="ollama")


async def _gemma_generate(params: Any) -> Any:
    """Stagehand LLM callback → local Gemma via Ollama's OpenAI-compatible API."""
    from stagehand import LLMStructuredGenerateResult
    from stagehand._generated.models import LLMMessageGenerateResult

    s = settings()
    messages = ([{"role": "system", "content": params.system_prompt}] if params.system_prompt else [])
    messages += [{"role": m.role.value, "content": _content_text(m.content)} for m in params.messages]
    fmt = params.response_format
    structured = fmt is not None and getattr(fmt, "type", None) == "json_schema"
    kwargs: dict[str, Any] = {}
    if structured:
        schema = fmt.schema_.model_dump() if fmt.schema_ is not None else {"type": "object"}
        kwargs["response_format"] = {"type": "json_schema", "json_schema": {
            "name": fmt.name, "schema": schema, "strict": True}}
    resp = await _openai_client().chat.completions.create(
        model=s.ollama_model, messages=messages, temperature=params.temperature or 0.1,
        reasoning_effort="none", **kwargs)
    text = resp.choices[0].message.content or ""
    usage = None
    if resp.usage:
        usage = {"input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens,
                 "total_tokens": resp.usage.total_tokens}
    if structured:
        return LLMStructuredGenerateResult.model_validate({
            "role": "assistant", "content": {"type": "text", "text": text}, "usage": usage,
            "output_format": "json_schema", "structured_content": json.loads(text)})
    return LLMMessageGenerateResult.model_validate({
        "role": "assistant", "content": {"type": "text", "text": text}, "usage": usage,
        "output_format": "text"})


@asynccontextmanager
async def session(*, headless: bool = False):
    """One local Chrome + Stagehand for many extracts (Lane 1 batches reuse it).

    Headful by default: x.com answers headless Chrome with a 403, and we do not disguise
    the browser. The window is a separate throwaway profile, not the author's Chrome.
    """
    from stagehand import Stagehand, local_browser

    browser = await local_browser.launch(headless=headless, viewport_width=1280, viewport_height=900)
    try:
        sh = await Stagehand.create(browser=browser, model=_gemma_generate,
                                    logging={"level": "error"})
        try:
            yield sh
        finally:
            await sh.close()
    finally:
        await browser.close()


async def _visible_text(page) -> str:
    deadline = time.monotonic() + SETTLE_S
    text = ""
    while time.monotonic() < deadline:
        text = str(await page.evaluate("document.body ? document.body.innerText : ''") or "")
        if len(text) >= 400:
            break
        await asyncio.sleep(1)
    return text


def is_login_wall(text: str) -> bool:
    low = text.lower()
    return len(text) < 1500 and any(m in low for m in LOGIN_WALL_MARKERS)


async def extract_with_reason(sh, url: str, *, timeout_s: int = 45) -> tuple[BrowserExtract | None, str]:
    """Extract one URL with an open session; returns (result, reason). Never raises."""
    t0 = time.monotonic()

    async def run() -> tuple[BrowserExtract | None, str]:
        page = await sh.browser.context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            text = await _visible_text(page)
            if len(text) < MIN_TEXT_CHARS:
                return None, f"empty page ({len(text)} chars)"
            if is_login_wall(text):
                return None, "login wall or access denied"
            try:
                data = (await sh.extract(INSTRUCTION, _PageContent, page=page)).data
                links = [str(u) for u in data.outbound_links][:10]
            except Exception:  # noqa: BLE001 - usually an unmappable link id; retry without links
                data = (await sh.extract(INSTRUCTION, _PageText, page=page)).data
                links = []
            if not data.summary_text.strip():
                return None, "model returned no summary"
            return BrowserExtract(
                **data.model_dump(include={"title", "author", "published", "summary_text"}),
                outbound_links=links, seconds=round(time.monotonic() - t0, 1),
                model=settings().ollama_model), "ok"
        finally:
            try:
                await page.close()
            except Exception:  # noqa: BLE001 - a closed page is fine
                pass

    try:
        return await asyncio.wait_for(run(), timeout=timeout_s)
    except TimeoutError:
        return None, f"timeout after {timeout_s}s"
    except Exception as e:  # noqa: BLE001 - None is the contract for "could not read"
        return None, f"{type(e).__name__}: {str(e)[:120]}"


async def extract_with(sh, url: str, *, timeout_s: int = 45) -> BrowserExtract | None:
    return (await extract_with_reason(sh, url, timeout_s=timeout_s))[0]


async def extract_async(url: str, *, timeout_s: int = 45) -> BrowserExtract | None:
    try:
        async with session() as sh:
            return await extract_with(sh, url, timeout_s=timeout_s)
    except Exception:  # noqa: BLE001 - browser launch failure is also "could not read"
        return None


def extract(url: str, *, timeout_s: int = 45) -> BrowserExtract | None:
    """Sync entry point for Lane 1: one browser per call. Use `session()` for batches."""
    return asyncio.run(extract_async(url, timeout_s=timeout_s))
