"""Weekly focus: the author's answer becomes weights on verticals.

Code first: a glossary maps the author's words (and the tapped button labels) to verticals at
weight 1.0. The model only maps free text the glossary missed. Weights are stored in the
`focus` table as `vertical:weight` strings in `verticals` (no schema change needed).
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from pydantic import BaseModel, Field

from ..core.llm import local_json
from ..core.models import Vertical

NAMES = {
    "ai-agents": "AI agents", "llms": "LLMs", "ai-engineering": "AI engineering",
    "decentralized-ai": "Decentralized AI", "blockchain": "Blockchain", "web3-data": "Web3 data",
    "cryptography": "Cryptography", "security-privacy": "Security and privacy", "rust": "Rust",
    "dev-tools": "Dev tools", "data-science": "Data science", "hardware": "Hardware",
    "productivity": "Productivity", "other": "Other",
}
GLOSSARY = {
    "ai-agents": ["agent", "agents", "agentic", "mcp", "tool use", "multi-agent"],
    "llms": ["llm", "llms", "language model", "retrieval", "embeddings", "fine-tune", "fine-tuning", "finetuning", "inference", "rag", "gemma", "llama"],
    "ai-engineering": ["ai engineering", "evals", "eval", "prompt", "observability", "mlops"],
    "decentralized-ai": ["decentralized ai", "federated", "depin"],
    "blockchain": ["blockchain", "solidity", "ethereum", "smart contract", "smart contracts", "evm", "web3"],
    "web3-data": ["web3 data", "indexer", "subgraph", "onchain data", "on-chain data"],
    "cryptography": ["cryptography", "crypto primitives", "zk", "zero knowledge", "zero-knowledge", "fhe", "mpc"],
    "security-privacy": ["security", "privacy", "auth", "pentest"],
    "rust": ["rust", "cargo", "wasm"],
    "dev-tools": ["dev tools", "devtools", "cli", "tooling", "editor", "developer tools"],
    "data-science": ["data science", "pandas", "notebook", "analytics", "statistics", "ml"],
    "hardware": ["hardware", "arduino", "embedded", "iot", "robot", "robotics"],
    "productivity": ["productivity", "notes", "workflow", "automation"],
}
SURPRISE = "Surprise me (no focus this week)"
BUTTON = re.compile(r".+ \(\d+ cards?\)")


class FocusPick(BaseModel):
    vertical: Vertical
    weight: float = Field(ge=0, le=1)


class FocusWeights(BaseModel):
    verticals: list[FocusPick] = Field(max_length=4)


def week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def glossary_weights(text: str) -> dict[str, float]:
    low = f" {text.lower()} "
    out = {}
    for v, name in NAMES.items():
        if v != "other" and (name.lower() in low or v in low):
            out[v] = 1.0
    for v, terms in GLOSSARY.items():
        if any(re.search(rf"(?<![a-z]){re.escape(t)}(?![a-z])", low) for t in terms):
            out[v] = 1.0
    return out


def parse_weights(spec: str) -> dict[str, float]:
    out = {}
    for part in filter(None, (p.strip() for p in spec.split(","))):
        name, _, w = part.partition("=")
        Vertical(name.strip())  # raises on an unknown vertical
        out[name.strip()] = max(0.0, min(1.0, float(w or 1)))
    return out


def model_weights(text: str) -> dict[str, float]:
    menu = "\n".join(f"- {v}: {NAMES[v]} (e.g. {', '.join(GLOSSARY.get(v, [])[:4]) or 'anything else'})"
                     for v in NAMES)
    prompt = (f'The author answered "what do you care about this week?" with:\n"{text}"\n\n'
              f"Map the answer to at most 4 verticals from this list:\n{menu}\n\n"
              'Return {"verticals": [{"vertical": <id from the list>, "weight": <0..1>}]}. '
              "Weight 1.0 = named directly, 0.5 = closely related. Return an empty list if nothing fits.")
    res = local_json(prompt, FocusWeights)
    # "other" carries no signal for scoring; the model reaches for it when unsure
    return {p.vertical.value: round(p.weight, 2) for p in res.value.verticals
            if p.weight > 0 and p.vertical != Vertical.other}


def encode(weights: dict[str, float]) -> list[str]:
    return [f"{v}:{w:g}" for v, w in sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))]


def decode(items: list[str]) -> dict[str, float]:
    out = {}
    for item in items or []:
        v, _, w = item.partition(":")
        out[v] = float(w) if w else 1.0
    return out


def current_focus(conn, today: date | None = None) -> dict | None:
    """Latest focus answered in the last 14 days, else None (no weighting)."""
    today = today or datetime.now().astimezone().date()
    row = conn.execute(
        "SELECT * FROM focus WHERE week_start >= %s ORDER BY created_at DESC LIMIT 1",
        (week_start(today) - timedelta(days=7),)).fetchone()
    if not row:
        return None
    return {"text": row["text"], "weights": decode(row["verticals"]), "week_start": row["week_start"]}


def describe(focus: dict | None) -> str:
    if not focus or not focus["weights"]:
        return "not set (all verticals weigh the same)"
    parts = ", ".join(f"{NAMES.get(v, v)} {w:g}" for v, w in focus["weights"].items())
    return f'"{focus["text"]}" → {parts}'


def set_focus(conn, *, text: str | None, weights: str | None, use_model: bool = True,
              today: date | None = None) -> dict:
    today = today or datetime.now().astimezone().date()
    if weights:
        w, how = parse_weights(weights), "weights"
    elif text and text.strip().lower().startswith("surprise me"):
        w, how = {}, "surprise"
    else:
        # A tapped button ("AI agents (3 cards)") is exact; typed text also goes to the model,
        # which may add related verticals. Glossary hits always keep weight 1.0.
        w, how = glossary_weights(text or ""), "glossary"
        if use_model and not BUTTON.fullmatch((text or "").strip()):
            try:
                extra = model_weights(text or "")
            except Exception as e:  # noqa: BLE001 - the glossary answer stands
                extra, how = {}, f"glossary (model failed: {type(e).__name__})"
            if extra.keys() - w.keys():
                how = "glossary+model" if w else "model"
            w = {**extra, **w}
    text = text or ", ".join(f"{v}={x:g}" for v, x in w.items())
    conn.execute("INSERT INTO focus (text, verticals, week_start) VALUES (%s, %s, %s)",
                 (text, encode(w), week_start(today)))
    conn.commit()
    focus = {"text": text, "weights": w, "week_start": week_start(today)}
    from ..core import notify
    notify.log("coordinator", "focus", f"weekly focus: {describe(focus)}", {"weights": w, "how": how})
    return {"ok": True, "weights": w, "how": how, "reply": focus_saved_text(focus),
            "action": "Send `reply` as is. Nothing else to run."}


def show_payload(conn) -> dict:
    focus = current_focus(conn)
    return {"ok": True, "focus": focus, "reply": f"This week's focus: {describe(focus)}"}


# ------------------------------------------------------------------ Discord texts (pure)

def focus_question(backlog_by_vertical: dict[str, int]) -> dict:
    """The weekly question with up to 4 buttons: the 3 biggest verticals + 'surprise me'."""
    top = sorted(((n, v) for v, n in backlog_by_vertical.items() if n), key=lambda x: (-x[0], x[1]))[:3]
    choices = [f"{NAMES.get(v, v)} ({n} card{'s' if n != 1 else ''})" for n, v in top] + [SURPRISE]
    question = ("New week on the skunkworks board. What do you care about this week? "
                "Tap one, or type your own answer (\"rust and anything with agents\").")
    return {"question": question, "choices": choices}


def focus_saved_text(focus: dict) -> str:
    if not focus["weights"]:
        return "Got it: no focus this week. Daily picks will favour fresh links and verticals you haven't touched."
    names = ", ".join(NAMES.get(v, v) for v in focus["weights"])
    return f"Got it. This week leans toward {names}. The daily pick will favour those cards."


def question_payload(conn) -> dict:
    rows = conn.execute(
        """SELECT vertical, count(*) AS n FROM cards WHERE "column" = 'backlog' GROUP BY vertical"""
    ).fetchall()
    q = focus_question({r["vertical"]: r["n"] for r in rows})
    return {"ok": True, **q, "reply": q["question"],
            "action": ("Call clarify with `question` and `choices` exactly as given. When the author "
                       "answers (a tapped choice or typed text), run "
                       "`uv run sloth focus --json \"<their answer, verbatim>\"` and send its `reply`.")}
