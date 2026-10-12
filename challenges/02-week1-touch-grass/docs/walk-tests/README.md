# Walk test reports (2026-10-08 and 2026-10-09)

The four reports produced by `phone-test/index.html` on a Redmi Note 11 (Chrome 154), exactly as the page printed them,
with a pasted mail header removed. They are the evidence behind the "web pages get no GPS while hidden" finding
in `../CHALLENGE-MEMORY.md`.

| Walk | Conditions | What the report shows |
| --- | --- | --- |
| 1 | screen on, page in front, no podcast | 1172 fixes, no gap over 5 s |
| 2 | podcast started first; a touch in the pocket switched app | page hidden 6m57s, 54 fixes, location permission asked again |
| 3 | permissions granted, screen off | page hidden 7m32s, longest gap 274 s |
| 4 | dog walk, screen on in the pocket | 2114 fixes, no gap over 4 s |

The GPS tracks themselves start and end near the author's home and are not published. `../../tests/fixtures/` holds
anonymised copies (rotated, moved, re-timed) made by `scripts/make-fixtures.py`, which the tests use.
