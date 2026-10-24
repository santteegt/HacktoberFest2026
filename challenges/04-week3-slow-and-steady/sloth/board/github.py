"""GitHub Project (v2) mirror of the board: `sloth board init` and `sloth board sync`.

One-way, DB → Project, idempotent by the `Card ID` field: every sync reads the Project's
items once, diffs them against the desired state and sends only the differences, in batched
GraphQL mutations through `gh api graphql` (the author's keyring login, `project` scope).
UI edits are overwritten by the next sync. Ids live in .sloth/github-project.json (gitignored).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import UTC, date, datetime
from pathlib import Path

from ..core.config import CONFIG_PATH
from ..core.models import Column, Vertical

TITLE = "Skunkworks Sloth"
IDS_PATH = Path(os.environ.get("SLOTH_GH_PROJECT_FILE", CONFIG_PATH.parent / "github-project.json"))
BATCH = 25  # mutations per GraphQL request

STATUS_OPTIONS = [  # (name, color, description), order = board columns
    ("Backlog", "GRAY", "Card waiting for a daily pick"),
    ("Today", "BLUE", "Picked for today's box"),
    ("Building", "YELLOW", "The Worker's box is running"),
    ("Built", "GREEN", "Prototype built and approved"),
    ("Killed", "RED", "Box ended without done-means"),
    ("Archived", "PURPLE", "Set aside"),
]
FIELDS = [  # (name, dataType)
    ("Vertical", "SINGLE_SELECT"), ("Card ID", "TEXT"), ("Box (min)", "NUMBER"),
    ("Picked", "DATE"), ("Cost (USD)", "NUMBER"), ("Model", "TEXT"), ("Repo URL", "TEXT"),  # "Repo" is reserved by GitHub
    ("Links", "NUMBER"),
]
_COLORS = ["BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PINK", "PURPLE", "GRAY"]


class GitHubError(RuntimeError):
    pass


_calls = 0


def gql(query: str, variables: dict | None = None) -> dict:
    global _calls
    _calls += 1
    body = json.dumps({"query": query, "variables": variables or {}})
    res = subprocess.run(["gh", "api", "graphql", "--input", "-"], input=body,
                         capture_output=True, text=True, timeout=90)
    try:
        out = json.loads(res.stdout or "{}")
    except json.JSONDecodeError as e:
        raise GitHubError(f"gh api graphql: {res.stderr.strip()[:300]}") from e
    if out.get("errors"):
        raise GitHubError(json.dumps(out["errors"])[:600])
    if res.returncode != 0:
        raise GitHubError(res.stderr.strip()[:300])
    return out["data"]


def _q(s: str) -> str:
    """GraphQL string literal."""
    return json.dumps(s, ensure_ascii=False)


def load_ids() -> dict | None:
    return json.loads(IDS_PATH.read_text()) if IDS_PATH.exists() else None


def configured() -> bool:
    return IDS_PATH.exists()


FIELDS_QUERY = """
query($id: ID!) { node(id: $id) { ... on ProjectV2 {
  id number url public title
  fields(first: 50) { nodes {
    ... on ProjectV2FieldCommon { id name dataType }
    ... on ProjectV2SingleSelectField { options { id name } } } }
  views(first: 20) { nodes { id name layout } } } } }
"""


def _ids_from(project: dict, owner: str) -> dict:
    fields = {}
    for f in project["fields"]["nodes"]:
        if not f:
            continue
        entry = {"id": f["id"], "type": f["dataType"]}
        if "options" in f:
            entry["options"] = {o["name"]: o["id"] for o in f["options"]}
        fields[f["name"]] = entry
    return {"project_id": project["id"], "number": project["number"], "url": project["url"],
            "owner": owner, "public": project["public"], "fields": fields,
            "views": {v["name"]: v["id"] for v in project["views"]["nodes"]}}


def init() -> dict:
    """Create the private Project, its fields and a Board view; store the ids. Safe to re-run."""
    ids = load_ids()
    viewer = gql("{ viewer { id login } }")["viewer"]
    if not ids:  # a run that failed half-way left a project without an ids file: reuse it
        found = gql("""query { viewer { projectsV2(first: 50) { nodes { id title closed } } } }""")
        ids = next(({"project_id": p["id"]} for p in found["viewer"]["projectsV2"]["nodes"]
                    if p["title"] == TITLE and not p["closed"]), None)
    if ids:
        project = gql(FIELDS_QUERY, {"id": ids["project_id"]})["node"]
    else:
        project = gql("""mutation($owner: ID!, $title: String!) {
            createProjectV2(input: {ownerId: $owner, title: $title}) { projectV2 { id } } }""",
                      {"owner": viewer["id"], "title": TITLE})["createProjectV2"]["projectV2"]
        project = gql(FIELDS_QUERY, {"id": project["id"]})["node"]
    pid = project["id"]
    gql("""mutation($p: ID!, $d: String!) { updateProjectV2(input: {projectId: $p, public: false,
        shortDescription: $d}) { projectV2 { id } } }""",
        {"p": pid, "d": "Reading List → prototypes. One-way mirror of the Skunkworks Sloth board."})
    have = {f["name"]: f for f in project["fields"]["nodes"] if f}
    # Status exists on every new Project (Todo / In Progress / Done): replace its options.
    status = have.get("Status")
    if status and [o["name"] for o in status["options"]] != [s[0] for s in STATUS_OPTIONS]:
        keep = {o["name"]: o["id"] for o in status["options"]}
        opts = ", ".join(
            "{" + (f"id: {_q(keep[n])}, " if n in keep else "")
            + f"name: {_q(n)}, color: {c}, description: {_q(d)}" + "}"
            for n, c, d in STATUS_OPTIONS)
        gql(f"""mutation {{ updateProjectV2Field(input: {{fieldId: {_q(status['id'])},
            singleSelectOptions: [{opts}]}}) {{ projectV2Field {{ ... on ProjectV2SingleSelectField {{ id }} }} }} }}""")
    for name, dtype in FIELDS:
        if name in have:
            continue
        extra = ""
        if name == "Vertical":
            # Every vertical in the shared enum, so a new vertical never needs a field rewrite.
            extra = ", singleSelectOptions: [" + ", ".join(
                "{" + f"name: {_q(v.value)}, color: {_COLORS[i % len(_COLORS)]}, description: \"\"" + "}"
                for i, v in enumerate(Vertical)) + "]"
        gql(f"""mutation {{ createProjectV2Field(input: {{projectId: {_q(pid)}, dataType: {dtype},
            name: {_q(name)}{extra}}}) {{ projectV2Field {{ ... on ProjectV2FieldCommon {{ id }} }} }} }}""")
    project = gql(FIELDS_QUERY, {"id": pid})["node"]
    views = {v["name"]: v for v in project["views"]["nodes"]}
    if "Board" not in views:
        try:
            gql("""mutation($p: ID!) { createProjectV2View(input: {projectId: $p, name: "Board",
                layout: BOARD_LAYOUT}) { projectV2View { id } } }""", {"p": pid})
            project = gql(FIELDS_QUERY, {"id": pid})["node"]
        except GitHubError as e:  # views were UI-only for years; the author can add it by hand
            print(f"warning: could not create the Board view ({e}); add it in the UI")
    ids = _ids_from(project, viewer["login"])
    IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    IDS_PATH.write_text(json.dumps(ids, indent=1) + "\n")
    return {"project": ids["url"], "number": ids["number"], "public": ids["public"],
            "fields": sorted(ids["fields"]), "views": sorted(ids["views"]), "ids_file": str(IDS_PATH)}


# ---------------------------------------------------------------------------------- sync

ITEMS_QUERY = """
query($id: ID!, $after: String) { node(id: $id) { ... on ProjectV2 {
  readme
  items(first: 100, after: $after) { pageInfo { hasNextPage endCursor } nodes {
    id
    content { ... on DraftIssue { id title body } }
    fieldValues(first: 30) { nodes {
      ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
    } } } } } } }
"""


def fetch_items(project_id: str) -> tuple[list[dict], str]:
    items, after, readme = [], None, ""
    while True:
        node = gql(ITEMS_QUERY, {"id": project_id, "after": after})["node"]
        readme = node.get("readme") or ""
        for it in node["items"]["nodes"]:
            values = {}
            for v in it["fieldValues"]["nodes"]:
                if v and v.get("field"):
                    values[v["field"]["name"]] = next(
                        (v[k] for k in ("text", "number", "date", "name") if k in v), None)
            content = it.get("content") or {}
            items.append({"id": it["id"], "draft_id": content.get("id"), "title": content.get("title"),
                          "body": content.get("body"), "values": values})
        page = node["items"]["pageInfo"]
        if not page["hasNextPage"]:
            return items, readme
        after = page["endCursor"]


def desired(card: dict, run: dict | None) -> dict:
    """Field values a card should show. None = cleared."""
    return {
        "Status": Column(card["column"]).value.capitalize(),
        "Vertical": card["vertical"],
        "Card ID": card["id"],
        "Box (min)": card["box_minutes"],
        "Picked": card["picked_on"].isoformat() if card.get("picked_on") else None,
        "Cost (USD)": float(run["cost_usd"]) if run and run.get("cost_usd") is not None else None,
        "Model": (run or {}).get("model_id") or None,
        "Repo URL": (run or {}).get("repo_url") or None,
        "Links": len(card["link_ids"]),
    }


def _same(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-6
    return a == b


def _norm(text: str | None) -> str:
    return (text or "").replace("\r\n", "\n").strip()


def field_changes(want: dict, have: dict) -> dict:
    return {k: v for k, v in want.items() if not _same(v, have.get(k))}


def _value_literal(field: dict, value) -> str:
    kind = field["type"]
    if kind == "SINGLE_SELECT":
        return "{singleSelectOptionId: %s}" % _q(field["options"][value])
    if kind == "NUMBER":
        return "{number: %s}" % float(value)
    if kind == "DATE":
        return "{date: %s}" % _q(value)
    return "{text: %s}" % _q(str(value))


def field_mutations(ids: dict, item_id: str, changes: dict, prefix: str) -> list[str]:
    out = []
    for i, (name, value) in enumerate(changes.items()):
        field = ids["fields"][name]
        alias = f"{prefix}_{i}"
        base = f"projectId: {_q(ids['project_id'])}, itemId: {_q(item_id)}, fieldId: {_q(field['id'])}"
        if value is None:
            out.append(f"{alias}: clearProjectV2ItemFieldValue(input: {{{base}}}) {{ clientMutationId }}")
        else:
            out.append(f"{alias}: updateProjectV2ItemFieldValue(input: {{{base}, "
                       f"value: {_value_literal(field, value)}}}) {{ clientMutationId }}")
    return out


def _run_batches(mutations: list[str]) -> dict:
    data = {}
    for i in range(0, len(mutations), BATCH):
        data.update(gql("mutation { " + "\n".join(mutations[i:i + BATCH]) + " }"))
    return data


def readme_text(conn) -> str:
    from . import store
    counts = store.link_counts(conn)
    cards = store.all_cards(conn)
    runs = store.latest_runs(conn)
    by_col = {c.value: 0 for c in Column}
    for c in cards:
        by_col[c["column"]] = by_col.get(c["column"], 0) + 1
    today = [c for c in cards if c["column"] == Column.today]
    total_cost = conn.execute("SELECT coalesce(sum(cost_usd), 0) AS s FROM runs").fetchone()["s"]
    try:
        from .focus import current_focus, describe
        focus_line = describe(current_focus(conn))
    except Exception:  # noqa: BLE001 - the README never blocks a sync
        focus_line = "not set"
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    pick = f"`{today[0]['id']}` {today[0]['title']}" if today else "none yet"
    built_runs = [r for r in runs.values() if r["outcome"] == "done" and r.get("approved")]
    return "\n".join([
        "## Status",
        "",
        f"**Reading List:** {counts['collected']} collected · {counts['kept']} kept · "
        f"{counts['valhalla']} in Valhalla ({counts['valhalla_confirmed']} confirmed) · "
        f"{counts['unsure']} unsure · {counts['untriaged']} not triaged yet",
        "",
        f"**This week's focus:** {focus_line}",
        "",
        f"**Today's pick:** {pick}",
        "",
        "**Board:** " + " · ".join(f"{n} {col}" for col, n in by_col.items()),
        "",
        f"**Prototypes built:** {len(built_runs)} · **Worker cost so far:** ${float(total_cost):.2f}",
        "",
        "---",
        "",
        f"_Updated {stamp} by `sloth board sync`. This Project is a one-way mirror of the board "
        "in Postgres: edits made here (including dragging cards) are overwritten by the next sync. "
        "Only cards (wording, box, the 2-5 links each came from, run results) are sent here; the rest "
        "of the Reading List, triage and Valhalla stay in Postgres and Discord._",
        "",
    ])


def _strip_stamp(text: str) -> str:
    return re.sub(r"Updated \d{4}-\d\d-\d\d \d\d:\d\d UTC", "Updated", text)


def set_readme(ids: dict, text: str) -> None:
    subprocess.run(["gh", "project", "edit", str(ids["number"]), "--owner", ids["owner"],
                    "--readme", text], check=True, capture_output=True, text=True, timeout=60)


def sync(*, prune: bool = False, readme: bool = True, conn=None) -> dict:
    """Mirror every card to the Project. Applies run rows first so Builder moves show up."""
    from . import store
    from .cards import apply_runs, render_all
    from .markdown import card_markdown

    ids = load_ids()
    if not ids:
        raise GitHubError(f"no {IDS_PATH}; run `sloth board init` first")
    global _calls
    _calls, t0 = 0, time.monotonic()
    if conn is None:
        from ..core.db import connect
        with connect() as c:
            return sync(prune=prune, readme=readme, conn=c)

    moves = apply_runs(conn)
    render_all(conn)
    cards = store.all_cards(conn)
    runs = store.latest_runs(conn)
    links = store.links_by_id(conn, sorted({i for c in cards for i in c["link_ids"]}))
    items, current_readme = fetch_items(ids["project_id"])
    by_card = {it["values"].get("Card ID"): it for it in items if it["values"].get("Card ID")}
    by_item = {it["id"]: it for it in items}

    stats = {"cards": len(cards), "created": 0, "bodies": 0, "fields": 0, "pruned": 0,
             "moves_from_runs": moves}
    # 1. create missing drafts (one batched mutation per BATCH cards)
    missing = [c for c in cards if c["id"] not in by_card
               and not (c.get("gh_item_id") and c["gh_item_id"] in by_item)]
    creates = [
        f"c{i}: addProjectV2DraftIssue(input: {{projectId: {_q(ids['project_id'])}, "
        f"title: {_q(c['title'])}, body: {_q(card_markdown(c, links, runs.get(c['id']), frontmatter=False))}}}) "
        f"{{ projectItem {{ id content {{ ... on DraftIssue {{ id }} }} }} }}"
        for i, c in enumerate(missing)]
    created = _run_batches(creates)
    for i, c in enumerate(missing):
        item = created[f"c{i}"]["projectItem"]
        new = {"id": item["id"], "draft_id": item["content"]["id"], "title": c["title"],
               "body": card_markdown(c, links, runs.get(c["id"]), frontmatter=False), "values": {}}
        by_card[c["id"]] = by_item[item["id"]] = new
        conn.execute("UPDATE cards SET gh_item_id = %s WHERE id = %s", (item["id"], c["id"]))
        stats["created"] += 1
    conn.commit()

    # 2. diff bodies and fields; batch every change
    mutations = []
    for n, c in enumerate(cards):
        item = by_card.get(c["id"]) or by_item.get(c.get("gh_item_id"))
        run = runs.get(c["id"])
        body = card_markdown(c, links, run, frontmatter=False)
        if item["draft_id"] and (item["title"] != c["title"] or _norm(item["body"]) != _norm(body)):
            mutations.append(f"b{n}: updateProjectV2DraftIssue(input: {{draftIssueId: {_q(item['draft_id'])}, "
                             f"title: {_q(c['title'])}, body: {_q(body)}}}) {{ clientMutationId }}")
            stats["bodies"] += 1
        changes = field_changes(desired(c, run), item["values"])
        mutations += field_mutations(ids, item["id"], changes, f"f{n}")
        stats["fields"] += len(changes)
        if c.get("gh_item_id") != item["id"]:
            conn.execute("UPDATE cards SET gh_item_id = %s WHERE id = %s", (item["id"], c["id"]))
    if prune:
        known = {c["id"] for c in cards}
        for n, it in enumerate(items):
            if it["values"].get("Card ID") not in known:
                mutations.append(f"d{n}: deleteProjectV2Item(input: {{projectId: {_q(ids['project_id'])}, "
                                 f"itemId: {_q(it['id'])}}}) {{ deletedItemId }}")
                stats["pruned"] += 1
    _run_batches(mutations)
    conn.execute("UPDATE cards SET gh_synced_at = now() WHERE gh_item_id IS NOT NULL")
    conn.commit()

    if readme:
        text = readme_text(conn)
        if _strip_stamp(text).strip() != _strip_stamp(current_readme).strip():
            set_readme(ids, text)
            _calls += 1
            stats["readme"] = "updated"
        else:
            stats["readme"] = "unchanged"
    stats["graphql_calls"] = _calls
    stats["seconds"] = round(time.monotonic() - t0, 1)
    stats["project"] = ids["url"]
    return stats


def today_local() -> date:
    return datetime.now().astimezone().date()
