"""Discord approval wording for #sk-worker. The coordinator wires the buttons (Hermes clarify);
each button maps to one CLI command, so the model never decides to push."""

from __future__ import annotations

from pathlib import Path


def approval_request(run_id: int, card_title: str, repo_dir: str, *, tests_passed: bool) -> dict:
    """First tap: push the local repo to a new *private* GitHub repo."""
    name = Path(repo_dir).name
    warn = "" if tests_passed else "\n⚠️ Tests did not pass; approving pushes it as-is for the record."
    return {
        "text": (f"Push **{card_title}** to GitHub? It goes up as a **private** repo "
                 f"(`sloth-{name}`). Reply `approve {run_id}` here to push it, or ignore this to keep it "
                 f"local; making it public is a separate step.{warn}"),
        "buttons": [
            {"label": "Approve: push private", "style": "success", "command": f"sloth approve {run_id}"},
            {"label": "Not now", "style": "secondary", "command": None},
        ],
    }


def publish_request(run_id: int, card_title: str, repo_url: str) -> dict:
    """Second tap, only after the author has looked at the private repo."""
    return {
        "text": (f"**{card_title}** is on GitHub (private): {repo_url}\n"
                 f"Have a look; reply `publish {run_id}` here to make it public."),
        "buttons": [
            {"label": "Make public", "style": "danger", "command": f"sloth approve {run_id} --public"},
            {"label": "Keep private", "style": "secondary", "command": None},
        ],
    }
