import json
from ghosts import face as F


def cap(ts, status="200", url="http://x.example/"):
    return {"ts": ts, "status": status, "mime": "text/html", "url": url}


CAPS = [cap("20150101000000", "404"), cap("20150601000000", "301"), cap("20160211005112"), cap("20160501000000"),
        cap("20160901000000", "503"), cap("20161201000000"), cap("20180101000000")]


def test_first_is_first_200_and_last_is_before_last_tx():
    s = F.select_captures(CAPS, "20160219215114")
    assert s["first"]["ts"] == "20160211005112"
    assert s["last"]["ts"] == "20160211005112"       # nothing else 200 before Feb 19 2016
    s = F.select_captures(CAPS, "20170101000000")
    assert s["last"]["ts"] == "20161201000000" and "before the ghost's last transaction" in s["note"]


def test_last_falls_back_to_latest_200():
    assert F.select_captures(CAPS, None)["last"]["ts"] == "20180101000000"
    # every 200 capture comes after the last transaction
    s = F.select_captures(CAPS, "20100101000000")
    assert s["last"]["ts"] == "20180101000000" and "after the last transaction" in s["note"]


def test_no_200_capture():
    s = F.select_captures([cap("20150101000000", "404")], "2016")
    assert s["first"] is None and s["last"] is None


def test_retry_candidates_are_neighbouring_200s():
    s = F.select_captures(CAPS, "20170101000000")
    assert [c["ts"] for c in s["candidates"]["first"]] == ["20160211005112", "20160501000000", "20161201000000"]
    assert [c["ts"] for c in s["candidates"]["last"]] == ["20161201000000", "20160501000000", "20160211005112"]


def test_ts_from_iso():
    assert F._ts_from_iso("2016-02-19T21:51:14.000000Z") == "20160219215114"
    assert F._ts_from_iso(None) is None


def test_index_adds_cover_equal_to_first():
    res = [{"ts": "1", "url": "u1", "file": "shots/1.png", "role": "first", "site": "a"},
           {"ts": "2", "url": "u2", "file": "shots/2.png", "role": "last", "site": "a"}]
    idx = F.build_index(res)
    assert [r["role"] for r in idx] == ["first", "last", "cover"]
    assert idx[2]["file"] == idx[0]["file"]
    json.dumps(idx)
    assert F.build_index([]) == []
