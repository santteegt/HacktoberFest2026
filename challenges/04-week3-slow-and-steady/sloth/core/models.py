"""Shared types between lanes. Changing a field is a contract change: ask the coordinator."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Vertical(StrEnum):
    ai_agents = "ai-agents"
    llms = "llms"
    ai_engineering = "ai-engineering"
    decentralized_ai = "decentralized-ai"
    blockchain = "blockchain"
    web3_data = "web3-data"
    cryptography = "cryptography"
    security_privacy = "security-privacy"
    rust = "rust"
    dev_tools = "dev-tools"
    data_science = "data-science"
    hardware = "hardware"
    productivity = "productivity"
    other = "other"


class Kind(StrEnum):
    tutorial = "tutorial"
    tool = "tool"
    library = "library"
    paper = "paper"
    dataset = "dataset"
    course = "course"
    article = "article"
    thread = "thread"
    news = "news"
    other = "other"


class Column(StrEnum):
    backlog = "backlog"
    today = "today"
    building = "building"
    built = "built"
    killed = "killed"
    archived = "archived"


class FetchedWith(StrEnum):
    http = "http"
    github = "github"
    stagehand = "stagehand"
    failed = "failed"


class Outcome(StrEnum):
    building = "building"
    done = "done"
    boxed_out = "boxed_out"
    killed = "killed"


class Link(BaseModel):
    id: int | None = None
    url: str
    canonical_url: str
    title: str | None = None
    folder_path: str | None = None
    saved_at: datetime | None = None
    source: str = "reading-list"


class BrowserExtract(BaseModel):
    """Lane 3 → Lane 1: what a real browser could read when plain HTTP could not."""
    title: str | None = None
    author: str | None = None
    published: str | None = None
    summary_text: str = ""
    outbound_links: list[str] = Field(default_factory=list)
    seconds: float = 0.0
    model: str | None = None


class Enrichment(BaseModel):
    link_id: int
    http_status: int | None = None
    final_url: str | None = None
    content_kind: str | None = None
    readable_text: str | None = None
    readable_chars: int = 0
    published_at: datetime | None = None
    github_stars: int | None = None
    github_archived: bool | None = None
    github_pushed_at: datetime | None = None
    fetched_with: FetchedWith
    browser_seconds: float | None = None
    error: str | None = None


class Triage(BaseModel):
    """What the model (or a code rule) says about one link."""
    topic: str
    vertical: Vertical
    kind: Kind
    still_relevant: bool
    reason: str = Field(max_length=240)
    buildable: int = Field(ge=0, le=3)
    one_line_idea: str | None = Field(default=None, max_length=200)


class Card(BaseModel):
    id: str
    title: str
    vertical: Vertical
    learning_goal: str
    hypothesis: str
    done_means: str
    box_minutes: int = 120
    link_ids: list[int]
    kill_criteria: str
    column: Column = Column.backlog
    picked_on: date | None = None


class PickOption(BaseModel):
    card_id: str
    label: str = Field(max_length=80)
    why: str = Field(max_length=200)


class Run(BaseModel):
    id: int | None = None
    card_id: str
    model_id: str | None = None
    outcome: Outcome = Outcome.building
    cost_usd: float | None = None
    approved: bool = False
    repo_url: str | None = None
    repo_dir: str | None = None
    notes_path: str | None = None
