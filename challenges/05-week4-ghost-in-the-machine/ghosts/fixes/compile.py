"""The compile gate: a fix is shown only after solc 0.8.38 compiles it (`solc --bin`, no errors).

The binary is called directly from solc-select's artifacts folder (no global `solc-select use`, so a parallel
Slither run on 0.4.x is never switched under its feet). Override with SOLC_0838=/path/to/solc.
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

VERSION = "0.8.38"


def solc_path() -> list[str] | None:
    env = os.environ.get("SOLC_0838")
    if env and Path(env).exists():
        return [env]
    p = Path.home() / ".solc-select" / "artifacts" / f"solc-{VERSION}" / f"solc-{VERSION}"
    if p.exists():
        return [str(p)]
    if shutil.which("uv"):
        return ["uv", "tool", "run", "--from", "solc-select", "solc"]  # honors SOLC_VERSION below
    return None


def compile_solidity(code: str, timeout: int = 120) -> tuple[bool, str]:
    """Compile one source with solc 0.8.38. Returns (ok, compiler_output) where output is short and human readable."""
    cmd = solc_path()
    if not cmd:
        return False, f"solc {VERSION} not found (install: uv tool run --from solc-select solc-select install {VERSION})"
    with tempfile.TemporaryDirectory(prefix="ghostfix-") as d:
        src = Path(d) / "Fix.sol"
        src.write_text(code)
        env = dict(os.environ, SOLC_VERSION=VERSION)
        try:
            r = subprocess.run(cmd + ["--bin", str(src)], capture_output=True, text=True, timeout=timeout, env=env, cwd=d)
        except (OSError, subprocess.TimeoutExpired) as ex:
            return False, f"solc failed to run: {ex}"
    err = (r.stderr or "").replace(str(src), "Fix.sol").replace(d, ".")
    if r.returncode != 0 or re.search(r"^\w*Error:", err, re.M):
        return False, err.strip()[:4000] or f"solc exited {r.returncode}"
    contracts = re.findall(r"^======= (.+?) =======$", r.stdout or "", re.M)
    bins = re.findall(r"^Binary:\s*\n([0-9a-f]*)$", r.stdout or "", re.M)
    sizes = ", ".join(f"{c.split(':')[-1]} {len(b) // 2} bytes" for c, b in zip(contracts, bins))
    summary = f"solc {VERSION} --bin: OK ({sizes or 'no bytecode'})"
    return True, (summary + ("\n" + err.strip() if err.strip() else ""))[:4000]
