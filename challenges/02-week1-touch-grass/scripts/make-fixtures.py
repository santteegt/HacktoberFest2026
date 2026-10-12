#!/usr/bin/env python3
"""Make anonymised copies of the real walk tracks for the tests.

The originals (phone-test/results/walk-test-N.gpx) start and end near the author's home and are gitignored.
A fixture keeps what the tests need (shape, distances, timing, gaps, accuracy) and drops where it was:
  - every point is rotated by a fixed angle around the track's centre, then moved far away (a constant offset),
  - every timestamp is moved by a constant number of days,
  - the track name is replaced.
Distances and time gaps are unchanged by a rotation and a translation (to within projection error).

Usage: python scripts/make-fixtures.py        (reads phone-test/results/*.gpx, writes tests/fixtures/*.gpx)
"""
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC, DST = ROOT / "phone-test" / "results", ROOT / "tests" / "fixtures"
ANGLE_DEG = 37.0
OFFSET = (14.2, 31.7)            # degrees of latitude / longitude: lands in the middle of an ocean
DAYS = 41                        # timestamps move this many days into the past
TRKPT = re.compile(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"([^>]*)>(.*?)</trkpt>', re.S)


def convert(text):
    pts = [(float(m[1]), float(m[2]), m[3], m[4]) for m in TRKPT.finditer(text)]
    lat0 = sum(p[0] for p in pts) / len(pts)
    lon0 = sum(p[1] for p in pts) / len(pts)
    k = math.cos(math.radians(lat0))                 # metres per degree of longitude, relative to latitude
    a = math.radians(ANGLE_DEG)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for lat, lon, attrs, body in pts:
        x, y = (lon - lon0) * k, lat - lat0           # local planar coordinates, in degrees of latitude
        xr, yr = x * ca - y * sa, x * sa + y * ca
        nlat = lat0 + OFFSET[0] + yr
        nlon = lon0 + OFFSET[1] + xr / k

        def shift(m):
            t = datetime.fromisoformat(m[1].replace("Z", "+00:00")) - timedelta(days=DAYS)
            return "<time>" + t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z</time>"
        body = re.sub(r"<time>([^<]+)</time>", shift, body)
        out.append(f'<trkpt lat="{nlat:.6f}" lon="{nlon:.6f}"{attrs}>{body}</trkpt>')
    return ('<?xml version="1.0"?><gpx version="1.1" creator="idea-leash-fixture" xmlns="http://www.topografix.com/GPX/1/1">'
            '<trk><name>fixture</name><trkseg>' + "".join(out) + "</trkseg></trk></gpx>")


def main():
    DST.mkdir(parents=True, exist_ok=True)
    for f in sorted(SRC.glob("walk-test-*.gpx")):
        (DST / f.name).write_text(convert(f.read_text()))
        print("wrote", (DST / f.name).relative_to(ROOT))


if __name__ == "__main__":
    main()
