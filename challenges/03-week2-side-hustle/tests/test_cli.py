import json

import pytest

from rcparts import cli
from rcparts.notify import send_dm, whatsapp_target


def run(capsys, *argv):
    code = cli.main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def test_usage_error_is_json(capsys):
    code, out = run(capsys, "listing", "add", "--phone", "1")
    assert code == 2 and out["ok"] is False and out["error"] == "usage"


def test_quote_needs_one_source(capsys, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody@127.0.0.1:1/x")
    code, out = run(capsys, "quote", "--phone", "593990000001")
    assert code == 2 and out["error"] == "usage"


def test_missing_database_url_is_json(capsys, monkeypatch):
    monkeypatch.setenv("RCPARTS_ENV_FILE", "/nonexistent/.env")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TIGER_DATA_DB_URL", raising=False)
    code, out = run(capsys, "club", "list")
    assert code == 1 and out["error"] == "config" and "action" in out


def test_send_dm_success_and_failure():
    assert whatsapp_target("593990000001") == "whatsapp:593990000001@s.whatsapp.net"
    ok, err = send_dm("sh -c 'cat >/dev/null' rcparts-test", "593990000001", "-hola")
    assert ok and err is None
    ok, err = send_dm("false", "593990000001", "hola")
    assert not ok and err.startswith("exit 1")
    ok, err = send_dm("/nonexistent/hermes send", "593990000001", "hola")
    assert not ok and "FileNotFoundError" in err
    assert send_dm("true", "", "x") == (False, "no phone number")


def test_sender_from_hermes_session_env():
    from rcparts.cli import sender_from_env
    assert sender_from_env({"HERMES_SESSION_USER_ID": "593990000001@s.whatsapp.net"}) == "593990000001"
    assert sender_from_env({"HERMES_SESSION_KEY": "agent:rc-parts:whatsapp:dm:593990000002"}) == "593990000002"
    assert sender_from_env({"HERMES_SESSION_KEY": "agent:rc-parts:whatsapp:group:1203@g.us"}) == ""
    assert sender_from_env({}) == ""
