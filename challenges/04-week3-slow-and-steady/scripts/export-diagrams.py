"""Export each section of docs/diagrams/skunkworks-blueprint.html as its own PNG.

Usage: uv run --with pillow python scripts/export-diagrams.py [--theme light|dark]

Each <section> is rendered alone (same styles, forced theme) by headless Chrome at 2x,
then cropped to its content with a small margin. Output: docs/diagrams/png/NN-<slug>.png
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "diagrams" / "skunkworks-blueprint.html"
OUT = ROOT / "docs" / "diagrams" / "png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH = 1240  # CSS px; the page caps content at 1180


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", choices=["light", "dark"], default="light")
    theme = ap.parse_args().theme

    html = SRC.read_text()
    head = html[: html.index('<div class="wrap">')]
    sections = re.findall(r"<section>.*?</section>", html, flags=re.S)
    OUT.mkdir(parents=True, exist_ok=True)
    bg = (244, 246, 242) if theme == "light" else (17, 21, 19)

    for i, sec in enumerate(sections, start=1):
        title = re.search(r"<h2>(.*?)<small>", sec, flags=re.S).group(1).strip()
        title = re.sub(r"<[^>]+>", "", title)
        name = f"{i:02d}-{slugify(title)}"
        page = (f'<!doctype html><html data-theme="{theme}"><head><meta charset="utf-8">'
                f"{head}<style>.draw svg{{min-width:0}} body{{margin:0}}</style></head>"
                f'<body><div class="wrap" style="padding-block:28px 28px">{sec}</div></body></html>')
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / f"{name}.html"
            src.write_text(page)
            shot = Path(tmp) / "shot.png"
            subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                 "--force-device-scale-factor=2", f"--window-size={WIDTH},2400",
                 "--virtual-time-budget=6000", f"--screenshot={shot}", src.as_uri()],
                check=True, capture_output=True, timeout=120,
            )
            img = Image.open(shot).convert("RGB")
        diff = ImageChops.difference(img, Image.new("RGB", img.size, bg))
        box = diff.getbbox()
        if box:
            pad = 40
            box = (max(0, box[0] - pad), max(0, box[1] - pad),
                   min(img.width, box[2] + pad), min(img.height, box[3] + pad))
            img = img.crop(box)
        suffix = "" if theme == "light" else "-dark"
        target = OUT / f"{name}{suffix}.png"
        img.save(target, optimize=True)
        print(f"{target.relative_to(ROOT)}  {img.width}x{img.height}")


if __name__ == "__main__":
    main()
