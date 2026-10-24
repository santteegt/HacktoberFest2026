import json
from pathlib import Path

from sloth.core import notify
from sloth.core.models import Card, Triage

FIX = Path(__file__).parent / "fixtures"


def test_fixtures_match_contracts():
    Card.model_validate(json.loads((FIX / "card.json").read_text()))
    for row in json.loads((FIX / "triage.json").read_text()):
        Triage.model_validate({k: v for k, v in row.items() if k != "link_index"})
    assert len(json.loads((FIX / "links.json").read_text())) == 42


def test_notify_dry_run_prints(capsys, monkeypatch):
    monkeypatch.setenv("SLOTH_DRY_RUN", "1")
    notify.post("curator", "hello")
    assert "[dry-run #curator as sloth-curator] hello" in capsys.readouterr().out
