import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
NOOP_SEND = "sh -c 'cat >/dev/null' rcparts-test"


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """Never read the real .env (real numbers, the real `hermes send`) and never message anyone.
    DB tests still get DATABASE_URL from the shell."""
    monkeypatch.setenv("RCPARTS_ENV_FILE", "/nonexistent/.env")
    monkeypatch.setenv("HERMES_SEND_CMD", NOOP_SEND)
    monkeypatch.setenv("MAINTAINER_PHONE", "593990000001")
    monkeypatch.setenv("WHATSAPP_ALLOWED_USERS", "593990000001,593990000002")
    monkeypatch.setenv("RCPARTS_DATA_DIR", str(tmp_path / "data"))
    for key in ("HERMES_SESSION_USER_ID", "HERMES_SESSION_KEY", "HERMES_SESSION_CHAT_TYPE", "HERMES_SESSION_CHAT_ID",
                "MATCH_SCOPE", "WHATSAPP_GROUP_ALLOWED_USERS",
                "DEPOSIT_ACCOUNT", "HERMES_DOCUMENT_CACHE_DIR"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def load_fixture():
    def _load(name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return _load
