"""Wounds: what is wrong with a contract, decided by tools and a cited catalog, never by a model.

Tiers, best first:
  slither  verified source compiled with solc >= 0.4.0: Slither on Sourcify's standard JSON input
           (fallback: the main .sol file), shortlist of detectors only; findings are confirmed.
  catalog  ghosts/catalog/incidents.json documents an incident at this address, with references.
  regex    pre-0.4 source (Slither cannot compile it): pattern matches, confirmed=false (suspected).
  none     no source and no catalog entry.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, time
from pathlib import Path
from . import config
from . import facts as F
from .http import get_json

CATALOG_DIR = Path(__file__).resolve().parent / "catalog"
SLITHER = ["uv", "tool", "run", "--from", "slither-analyzer", "slither"]
SOLC_SELECT = ["uv", "tool", "run", "--from", "solc-select", "solc-select"]
SLITHER_TIMEOUT = 600
SNIPPET_MAX = 40

SHORTLIST = {
    "reentrancy-eth": "SWC-107", "reentrancy-no-eth": "SWC-107", "suicidal": "SWC-106",
    "arbitrary-send-eth": "SWC-105", "controlled-delegatecall": "SWC-112", "delegatecall-loop": "SWC-112",
    "uninitialized-state": "SWC-109", "uninitialized-storage": "SWC-109", "unchecked-transfer": "SWC-104",
    "unchecked-send": "SWC-104", "unchecked-lowlevel": "SWC-104", "locked-ether": None, "weak-prng": "SWC-120",
    "tx-origin": "SWC-115", "msg-value-loop": None, "unprotected-upgrade": "SWC-106",
    "incorrect-equality": "SWC-132", "shadowing-state": "SWC-119", "timestamp": "SWC-116",
}
PLAIN = {
    "reentrancy-eth": "The function calls out to another contract and only afterwards updates its own records, while ether can move. A malicious callee can call back in before the books are fixed and be paid twice.",
    "reentrancy-no-eth": "The function calls out to another contract before it finishes updating its own state. A malicious callee can re-enter while the state is half-written; no ether moves in the reentrant path itself, but the stale state can be abused.",
    "suicidal": "Anyone can call the function that destroys the contract.",
    "arbitrary-send-eth": "The function sends ether to an address the caller can choose, without a strong check on who may do it.",
    "controlled-delegatecall": "The function delegatecalls into code chosen by the caller, so a stranger can run their code with this contract's storage and balance.",
    "delegatecall-loop": "A payable delegatecall inside a loop reuses the same msg.value many times.",
    "uninitialized-state": "A state variable is read before anything ever writes it, so it holds the zero value.",
    "uninitialized-storage": "A local storage pointer is never initialized and points at slot 0, so writing to it overwrites other state.",
    "unchecked-transfer": "A token transfer's return value is ignored; a failed transfer passes silently.",
    "unchecked-send": "The result of send() is ignored; if the payment fails the contract carries on as if it succeeded.",
    "unchecked-lowlevel": "The result of a low-level call is ignored; a failed call passes silently.",
    "locked-ether": "The contract can receive ether but has no way to send it out.",
    "weak-prng": "Randomness comes from block data that a miner or caller can predict or influence.",
    "tx-origin": "Authorization uses tx.origin, so a malicious contract the owner calls can act as the owner.",
    "msg-value-loop": "msg.value is used inside a loop, so one payment is counted many times.",
    "unprotected-upgrade": "The initializer or upgrade path is unprotected; anyone can take it over.",
    "incorrect-equality": "A strict equality on a balance or amount can be broken by someone sending a little extra, locking the logic.",
    "shadowing-state": "A state variable in a child contract hides one with the same name in its parent, so the two halves disagree.",
    "timestamp": "Logic depends on block.timestamp, which miners can nudge by a few seconds (informational).",
}
IMPACT_RANK = {"High": 4, "Medium": 3, "Low": 2, "Informational": 1, "Optimization": 0}
CONF_RANK = {"High": 3, "Medium": 2, "Low": 1}


# ---------------------------------------------------------------- helpers

def parse_version(v: str | None) -> tuple[int, int, int] | None:
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(x) for x in m.groups()) if m else None


def plain_version(v: str | None) -> str | None:
    t = parse_version(v)
    return ".".join(map(str, t)) if t else None


def cut_snippet(text: str, a: int, b: int) -> str:
    """Lines a..b (1-based, inclusive) of `text`, verbatim (line endings normalized to \\n)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    a, b = max(1, a), min(len(lines), b)
    return "\n".join(lines[a - 1:b]) if a <= b else ""


def strip_comments(src: str) -> str:
    """Blank out // and /* */ comments (string literals respected), keeping line numbers and columns."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1]); i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i); j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2); j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in src[i:j])); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def functions(code: str) -> list[dict]:
    """[{name, start, end}] (1-based lines) for every `function` with a body, by brace matching on comment-free code."""
    res = []
    for m in re.finditer(r"\bfunction\s+(\w*)\s*\(", code):
        k = code.find("{", m.end())
        semi = code.find(";", m.end())
        if k < 0 or (0 <= semi < k):
            continue  # declaration without body
        depth, j = 0, k
        while j < len(code):
            if code[j] == "{":
                depth += 1
            elif code[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        res.append({"name": m.group(1), "start": code.count("\n", 0, m.start()) + 1,
                    "end": code.count("\n", 0, j) + 1, "body": code[k:j + 1]})
    return res


def enclosing(funcs: list[dict], line: int) -> dict | None:
    inside = [f for f in funcs if f["start"] <= line <= f["end"]]
    return min(inside, key=lambda f: f["end"] - f["start"]) if inside else None


def window(funcs: list[dict], line: int, span: int = 2) -> tuple[int, int]:
    """The enclosing function when it is short, else the line with `span` lines around it."""
    f = enclosing(funcs, line)
    if f and f["end"] - f["start"] < SNIPPET_MAX // 2:
        return f["start"], f["end"]
    lo, hi = line - span, line + span
    if f:
        lo, hi = max(lo, f["start"]), min(hi, f["end"])
    return max(1, lo), hi


# ---------------------------------------------------------------- catalog

def load_catalog() -> list[dict]:
    out = []
    for p in sorted(CATALOG_DIR.glob("*.json")):
        d = json.loads(p.read_text())
        out.extend(d if isinstance(d, list) else [d])
    return out


def catalog_entry(address: str, catalog: list[dict] | None = None) -> dict | None:
    a = address.lower()
    for e in catalog if catalog is not None else load_catalog():
        if (e.get("address") or "").lower() == a:
            return e
    return None


def incident_of(e: dict | None) -> dict | None:
    if not e or not e.get("incident"):
        return None
    return {"id": e.get("id"), "name": e.get("name"), "date": e.get("date"), "loss_usd": e.get("loss_usd"),
            "loss_eth": e.get("loss_eth"), "loss_note": e.get("loss_note"), "cause": e.get("cause"),
            "swc": e.get("swc"), "summary": e.get("summary"), "references": e.get("references") or []}


# ---------------------------------------------------------------- regex tier

def regex_findings(files: dict[str, str]) -> list[dict]:
    """Suspected wounds in pre-0.4 source. `files` maps a display path to its text."""
    out = []
    for path, text in files.items():
        code = strip_comments(text.replace("\r\n", "\n").replace("\r", "\n"))
        lines = code.split("\n")
        funcs = functions(code)
        contracts = set(re.findall(r"\b(?:contract|library)\s+(\w+)", code))

        def add(check, swc, impact, title, line_a, line_b, why):
            out.append({"check": check, "swc": swc, "title": title, "impact": impact, "confidence": "Low",
                        "confirmed": False, "file": path, "lines": [line_a, line_b],
                        "snippet": cut_snippet(text, line_a, line_b), "description": why, "reference_url": None,
                        "match_line": line_a if line_a == line_b else None})

        for i, ln in enumerate(lines, 1):
            fn = (enclosing(funcs, i) or {}).get("name") or "?"
            if re.search(r"\.call\.value\s*\(", ln):
                a, b = window(funcs, i)
                add("call-value", "SWC-107", "Medium", f"call.value() with all remaining gas in {fn}()", a, b,
                    "A low-level call.value() forwards all remaining gas to the recipient, which can run code and call back in before this function finishes.")
                out[-1]["match_line"] = i
            for m in re.finditer(r"\.send\s*\(", ln):
                head = ln[:m.start()].strip()
                if re.match(r"^(if|while|require|assert|return|bool|var)\b", head) or re.search(r"[!=&|?]|\(\s*$", head) \
                        or re.match(r"^\(", head):
                    continue
                if not re.match(r"^[\w.\[\]()]+$", head):
                    continue
                a, b = window(funcs, i)
                add("unchecked-send", "SWC-104", "Medium", f"Unchecked send() in {fn}()", a, b,
                    "send() forwards only 2,300 gas and returns false on failure; the result is ignored, so a failed payment passes silently.")
                out[-1]["match_line"] = i
            if re.search(r"\b(suicide|selfdestruct)\s*\(", ln):
                a, b = window(funcs, i)
                add("selfdestruct", "SWC-106", "Medium", f"Self-destruct in {fn}()", a, b,
                    "The contract can destroy itself here; whether only the owner can reach this line must be read from the code.")
                out[-1]["match_line"] = i
            if re.search(r"\btx\.origin\b", ln):
                a, b = window(funcs, i)
                add("tx-origin", "SWC-115", "Medium", f"tx.origin used in {fn}()", a, b,
                    "tx.origin is the original sender of the whole transaction; using it for authorization lets a contract the owner calls act as the owner.")
                out[-1]["match_line"] = i
        for f in funcs:
            nm = f["name"]
            if nm and nm[0].isupper() and nm not in contracts and re.search(r"=\s*msg\.sender\b", f["body"]):
                a, b = f["start"], min(f["end"], f["start"] + SNIPPET_MAX - 1)
                add("constructor-name", "SWC-118", "High", f"{nm}() looks like a constructor but no contract is named {nm}", a, b,
                    f"{nm}() is written like a constructor (capitalized, assigns msg.sender) but the contract is named "
                    f"{', '.join(sorted(contracts)) or '?'}; in Solidity before 0.4.22 only a function named exactly like the contract is the constructor, so anyone can call this one.")
                out[-1]["match_line"] = f["start"]
    return out


# ---------------------------------------------------------------- slither tier

def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None, timeout: int = SLITHER_TIMEOUT):
    return subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True, timeout=timeout)


def tool_version(cmd: list[str]) -> str | None:
    try:
        r = _run(cmd + ["--version"], timeout=120)
        return (r.stdout or r.stderr).strip().splitlines()[-1] if r.returncode == 0 else None
    except Exception:
        return None


def ensure_solc(version: str) -> None:
    r = _run(SOLC_SELECT + ["install", version], timeout=300)
    if r.returncode != 0 and "already installed" not in (r.stdout + r.stderr).lower():
        raise RuntimeError(f"solc-select install {version} failed: {(r.stderr or r.stdout)[-300:]}")


def fetch_stdjson(address: str, gd: Path) -> dict | None:
    d = get_json(f"{config.SOURCIFY_BASE}/v2/contract/1/{address}",
                 params={"fields": "stdJsonInput,compilation"}, ttl=None)
    std = (d or {}).get("stdJsonInput") if isinstance(d, dict) else None
    if std:
        (gd / "stdjson.json").write_text(json.dumps(std, indent=1))
    return std


def run_slither(address: str, version: str, gd: Path, main_name: str | None = None) -> tuple[dict | None, dict]:
    """Returns (slither json or None, run info). Work dir is src/ so Slither resolves relative source paths."""
    info: dict = {"method": None, "errors": []}
    src = gd / "src"
    out = gd / "slither.json"
    ensure_solc(version)
    env = {"SOLC_VERSION": version}
    std = None
    try:
        std = fetch_stdjson(address, gd)
    except Exception as ex:
        info["errors"].append(f"stdjson fetch: {ex}"[:300])
    attempts = []
    if std:
        src.mkdir(exist_ok=True)
        clean = {F.safe_relpath(k).as_posix(): v for k, v in std["sources"].items()}
        for k, v in clean.items():  # materialize sources at the paths the standard JSON names
            p = src / k
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                p.write_text((v or {}).get("content") or "")
        std2 = {**std, "sources": clean}
        (gd / "stdjson.slither.json").write_text(json.dumps(std2))
        attempts.append(("solc-json", [str(gd / "stdjson.slither.json"), "--compile-force-framework", "solc-json"]))
    mains = sorted(src.rglob("*.sol"), key=lambda p: p.stem != main_name) if src.exists() else []
    if mains:
        attempts.append(("single-file", [str(mains[0].relative_to(src))]))
    for method, args in attempts:
        out.unlink(missing_ok=True)
        t0 = time.time()
        r = _run(SLITHER + args + ["--json", str(out)], cwd=src, env=env)
        info.setdefault("seconds", {})[method] = round(time.time() - t0, 2)
        if out.exists():
            d = json.loads(out.read_text())
            if d.get("success"):
                info["method"] = method
                return d, info
            info["errors"].append(f"{method}: {(d.get('error') or '')[:300]}")
        else:
            info["errors"].append(f"{method}: exit {r.returncode}: {(r.stderr or '')[-300:]}")
    return None, info


def slither_findings(d: dict, src: Path) -> list[dict]:
    out, seen = [], set()
    for det in (d.get("results") or {}).get("detectors") or []:
        chk = det.get("check")
        if chk not in SHORTLIST:
            continue
        els = [e for e in det.get("elements") or [] if (e.get("source_mapping") or {}).get("lines")]
        if not els:
            continue
        head = els[0]
        sm = head["source_mapping"]
        fname = sm.get("filename_relative") or sm.get("filename_short")
        lines = sm["lines"]
        a, b = min(lines), max(lines)
        if b - a + 1 > SNIPPET_MAX:  # long function: the reported statements instead
            node_lines = [ln for e in els[1:] if e["source_mapping"].get("filename_relative") == fname
                          for ln in e["source_mapping"]["lines"]]
            if node_lines and max(node_lines) - min(node_lines) + 1 <= SNIPPET_MAX:
                a, b = min(node_lines), max(node_lines)
            else:
                b = a + SNIPPET_MAX - 1
        key = (chk, fname, a, b)
        if key in seen:
            continue
        seen.add(key)
        p = src / fname if fname else None
        text = p.read_text() if p and p.exists() else ""
        impact = det.get("impact")
        first = (det.get("description") or "").strip().splitlines()[0]
        title = re.sub(r"\s*\([^()]*#[\d-]+\)", "", first).rstrip(":").strip()[:160]
        out.append({"check": chk, "swc": SHORTLIST[chk], "title": title,
                    "impact": "Informational" if chk == "timestamp" else impact, "confidence": det.get("confidence"),
                    "confirmed": True, "file": fname, "lines": [a, b], "snippet": cut_snippet(text, a, b),
                    "description": PLAIN.get(chk, "") + " Slither: " + (det.get("description") or "").strip()[:600],
                    "reference_url": f"https://github.com/crytic/slither/wiki/Detector-Documentation#{chk}"})
    out.sort(key=lambda w: (-IMPACT_RANK.get(w["impact"], 0), -CONF_RANK.get(w["confidence"], 0), w["lines"][0]))
    return out


# ---------------------------------------------------------------- catalog x findings

def apply_catalog(findings: list[dict], entry: dict | None, files: dict[str, str]) -> list[dict]:
    """A documented incident confirms the matching findings in the guilty function; if none match, it adds one."""
    if not entry or not entry.get("incident"):
        return findings
    hint, checks = entry.get("function_hint"), set(entry.get("checks") or [])
    ref = (entry.get("references") or [None])[0]
    hit = False
    for w in findings:
        if w["check"] not in checks:
            continue
        text = files.get(w["file"], "")
        fn = enclosing(functions(strip_comments(text)), w.get("match_line") or w["lines"][0]) if text else None
        if hint is None or (fn and fn["name"] == hint):
            w.update(confirmed=True, reference_url=ref, confidence="High",
                     description=w["description"] + f" Documented incident: {entry.get('name')} ({entry.get('date')}).")
            hit = True
    if hit:
        return findings
    w = {"check": "catalog", "swc": entry.get("swc"), "title": entry.get("name"), "impact": "High", "confidence": "High",
         "confirmed": True, "file": None, "lines": None, "snippet": None,
         "description": entry.get("cause") or "", "reference_url": ref, "match_line": None}
    for path, text in files.items():  # point at the guilty function when the source has it
        code = strip_comments(text)
        fn = next((f for f in functions(code) if f["name"] == hint), None) if hint else None
        if fn:
            a, b = fn["start"], fn["end"]
            if b - a + 1 > SNIPPET_MAX:
                lh = entry.get("line_hint")
                at = next((i for i, ln in enumerate(code.split("\n"), 1) if lh and lh in ln and a <= i <= b), None)
                a, b = (max(a, at - SNIPPET_MAX // 2), min(b, at + SNIPPET_MAX // 2)) if at else (a, a + SNIPPET_MAX - 1)
            w.update(file=path, lines=[a, b], snippet=cut_snippet(text, a, b))
            break
    return [w] + findings


# ---------------------------------------------------------------- main

def source_files(f: dict, gd: Path) -> tuple[dict[str, str], str]:
    """{display path: text} from src/ (Sourcify/Blockscout) or, failing that, Ethereum History's source.eh.sol."""
    src = gd / "src"
    files = {}
    if f.get("source") and src.exists():
        for p in sorted(src.rglob("*.sol")):
            files[p.relative_to(src).as_posix()] = p.read_text()
        if files:
            return files, "src"
    eh = gd / "source.eh.sol"
    if eh.exists():
        return {"source.eh.sol": eh.read_text()}, "eh"
    return {}, "none"


def analyze(address: str, *, use_slither: bool = True, catalog: list[dict] | None = None) -> dict:
    address = address.lower()
    f = F.summon(address)
    gd = F.ghost_dir(address)
    files, origin = source_files(f, gd)
    version = (f.get("source") or {}).get("compiler_version")
    if not version and files:  # EH source: trust only an explicit pragma
        m = re.search(r"pragma\s+solidity\s*[\^>=~]*\s*(\d+\.\d+\.\d+)", strip_comments(next(iter(files.values()))))
        version = m.group(1) if m else None
    vt = parse_version(version)
    entry = catalog_entry(address, catalog)
    findings, tier, raw, run = [], "none", None, {}
    tools = {}

    if files and vt and vt >= (0, 4, 0) and origin == "src" and use_slither:
        d, run = run_slither(address, plain_version(version), gd, (f.get("source") or {}).get("name"))
        if d is not None:
            findings = slither_findings(d, gd / "src")
            tier, raw = "slither", str((gd / "slither.json").relative_to(config.ROOT))
            tools = {"slither": tool_version(SLITHER), "solc": plain_version(version)}
    if tier == "none" and files:
        findings = regex_findings(files)
        tier = "regex"
    findings = apply_catalog(findings, entry, files)
    inc = incident_of(entry)
    if tier == "regex" and inc:
        tier = "catalog"
    if tier == "none" and entry:
        tier = "catalog"
    findings.sort(key=lambda w: (not w["confirmed"], -IMPACT_RANK.get(w["impact"], 0), -CONF_RANK.get(w["confidence"], 0)))
    for i, w in enumerate(findings, 1):
        w["id"] = f"w{i}"
        w.pop("match_line", None)
    findings = [{"id": w["id"], **{k: v for k, v in w.items() if k != "id"}} for w in findings]
    out = {"address": address, "tier": tier, "compiler_version": version,
           "analyzed_files": sorted(files), "source_origin": origin,
           "findings": findings, "incident": inc, "slither_raw": raw,
           "catalog_entry": (entry or {}).get("id"),
           "run": {**run, "tools": tools} if run else ({"tools": tools} if tools else None),
           "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (gd / "wounds.json").write_text(json.dumps(out, indent=1))
    return out
