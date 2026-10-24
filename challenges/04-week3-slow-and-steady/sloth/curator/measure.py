"""M0.2: triage speed and quality on a random sample of real links. Real samples stay in .sloth/."""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from sloth.core.config import ROOT

from . import store
from .rules import DupeIndex, judge
from .triage import decide, label

OUT = ROOT / ".sloth" / "m02"


def sample(conn, n: int = 50, *, seed: int = 26) -> list[dict]:
    """n random enriched links that the code rules leave to the model."""
    rows = conn.execute("SELECT l.* FROM links l JOIN enrichment e ON e.link_id = l.id ORDER BY l.id").fetchall()
    enr = store.enrichment_for(conn, [r["id"] for r in rows])
    dupes = DupeIndex(store.all_links_with_final_url(conn))
    pool = [r for r in rows if judge(r, enr.get(r["id"]), dupes) is None]
    random.Random(seed).shuffle(pool)
    return pool[:n]


def run(conn, n: int = 50, label_n: int = 20, *, seed: int = 26, out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    links = sample(conn, n, seed=seed)
    enr = store.enrichment_for(conn, [r["id"] for r in links])
    results, t0 = [], time.monotonic()
    for link in links:
        lab = label(link, enr.get(link["id"]))
        results.append({"link_id": link["id"], "outcome": decide(lab, link, enr.get(link["id"])),
                        "verified": lab.verified, "tries": lab.tries, "problems": lab.problems,
                        "tokens_in": lab.tokens_in, "tokens_out": lab.tokens_out, "ms": lab.ms,
                        "model": lab.model, "triage": lab.triage.model_dump(mode="json")})
    wall = time.monotonic() - t0
    summary = {
        "at": datetime.now(UTC).isoformat(timespec="seconds"), "n": len(results), "wall_s": round(wall, 1),
        "links_per_min": round(len(results) / wall * 60, 2),
        "tokens_in": sum(r["tokens_in"] for r in results), "tokens_out": sum(r["tokens_out"] for r in results),
        "median_ms": sorted(r["ms"] for r in results)[len(results) // 2],
        "verified_first_try": sum(r["verified"] and r["tries"] == 1 for r in results),
        "verified_after_retry": sum(r["verified"] and r["tries"] == 2 for r in results),
        "unverified": sum(not r["verified"] for r in results),
        "outcomes": {o: sum(r["outcome"] == o for r in results) for o in ("kept", "valhalla", "unsure")},
        "model": results[0]["model"] if results else None,
    }
    (out / "results.json").write_text(json.dumps({"summary": summary, "results": results}, indent=1, default=str))
    by_id = {r["id"]: r for r in links}
    picks = random.Random(seed + 1).sample(results, min(label_n, len(results)))
    write_label_file(out / "labels.md", [by_id[p["link_id"]] for p in picks])
    return summary


def write_label_file(path: Path, links: list[dict]) -> None:
    md = ["# M0.2 labels (about 10 minutes)", "",
          "For each link, replace the `?` after **keep** with `y` (still worth my time) or `n` (Valhalla),",
          "and after **build** with 0-3 (0 nothing to build, 1 vague inspiration, 2 weekend prototype,",
          "3 obvious 2-hour prototype). Don't open the links unless you need to; judge like you would at a glance.", ""]
    for i, link in enumerate(links, 1):
        saved = f"{link['saved_at']:%Y-%m-%d}" if link.get("saved_at") else "?"
        md += [f"## {i}. {link.get('title') or '(no title)'}", f"<{link['url']}>",
               f"id {link['id']} · {link.get('folder_path') or ''} · saved {saved}", "",
               "keep: ?", "build: ?", ""]
    path.write_text("\n".join(md))


_ITEM = re.compile(r"^id (\d+) .*?$.*?^keep:\s*(\S+)\s*$.*?^build:\s*(\S+)\s*$", re.M | re.S)


def parse_labels(text: str) -> dict[int, dict]:
    out = {}
    for m in _ITEM.finditer(text):
        keep, build = m.group(2).lower(), m.group(3)
        if keep in ("y", "n") and build.isdigit():
            out[int(m.group(1))] = {"keep": keep == "y", "build": int(build)}
    return out


def score(out: Path = OUT) -> dict:
    labels = parse_labels((out / "labels.md").read_text())
    res = {r["link_id"]: r for r in json.loads((out / "results.json").read_text())["results"]}
    rows = [(labels[i], res[i]) for i in labels if i in res]
    n = len(rows)
    if not n:
        return {"labelled": 0}
    # The author's "keep" vs the pipeline's outcome (unsure counts as a disagreement either way).
    keep_agree = sum(a["keep"] == (r["outcome"] == "kept") for a, r in rows)
    build_exact = sum(a["build"] == r["triage"]["buildable"] for a, r in rows)
    build_within1 = sum(abs(a["build"] - r["triage"]["buildable"]) <= 1 for a, r in rows)
    card_agree = sum((a["build"] >= 2) == (r["triage"]["buildable"] >= 2) for a, r in rows)
    s = {"labelled": n, "keep_agreement": f"{keep_agree}/{n}", "buildable_exact": f"{build_exact}/{n}",
         "buildable_within_1": f"{build_within1}/{n}", "card_eligible_agreement (build>=2)": f"{card_agree}/{n}",
         "unsure": sum(r["outcome"] == "unsure" for _, r in rows),
         "author_keep_rate": f"{sum(a['keep'] for a, _ in rows)}/{n}"}
    (out / "score.json").write_text(json.dumps(s, indent=1))
    return s
