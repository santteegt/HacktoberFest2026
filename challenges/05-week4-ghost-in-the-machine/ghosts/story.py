"""Tell one ghost's story with the local model, chapter by chapter, and let code check every sentence.

Each chapter is one small model call that sees only the facts it needs, with raw identifiers replaced by short labels
made by code (deployer "0xbfdb…7645", "Solidity 0.4.18", "active every year since 2022"). Every sentence the model
writes goes through `verify.check_sentence` (grounding) and `style_problems` (no full addresses, commit strings, birth
block numbers or year lists); a failing sentence is sent back once for a rewrite (repaired) or removed (dropped, kept in
verifier.dropped_text). Snippets are copied by code. For the fix, the model only chooses names: it maps the recipe's
identifiers to names that exist in the ghost's source; code applies the renames, checks that the snippet still shows the
cure, and solc 0.8.38 must compile it.
"""
from __future__ import annotations
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config, llm
from .fixes import compile_solidity, recipe_for, apply_renames, meaning_problems, VERSION as SOLC_VERSION
from .verify import FactIndex, check_sentence, split_sentences, problems_text

CHAPTER_SCHEMA = {"type": "object", "properties": {"heading": {"type": "string"}, "paragraphs": {"type": "array", "items": {"type": "string"}}},
                  "required": ["heading", "paragraphs"]}
TITLE_SCHEMA = {"type": "object", "properties": {"title": {"type": "string"}, "tagline": {"type": "string"}}, "required": ["title", "tagline"]}
SENTENCE_SCHEMA = {"type": "object", "properties": {"sentence": {"type": "string"}}, "required": ["sentence"]}
RENAME_SCHEMA = {"type": "object", "properties": {"renames": {"type": "array", "items": {
    "type": "object", "properties": {"from": {"type": "string"}, "to": {"type": "string"}}, "required": ["from", "to"]}}},
    "required": ["renames"]}

PROSE_T = 0.6
REPAIR_T = 0.2
CODE_T = 0.2

GLOSS_FIRST = ("Weave in two plain explanations, once each, inside the story's own sentences (not as separate definitions): "
               "a contract is a small program that lives on Ethereum, and on the day it was born it was written into a block, "
               "one page of Ethereum's shared record book.")
GLOSS_LATER = "Do not explain blockchain words (contract, block, transaction, ether); the listener already knows them."

RULES = """Rules you must follow:
- Use only the facts in FACTS. Never invent dates, numbers, names, people, places, quotes or events. If a detail is not in FACTS, leave it out.
- Copy every date and number exactly as FACTS writes it, or round it ("about 83 ETH").
- Speak like a storyteller by candlelight: mostly short sentences (under 18 words) with a varied rhythm, concrete pictures, warm plain words. Open with an image, not a list of facts; join small facts gracefully.
- No filler such as "a testament to", "in the vast digital", "a set of rules", "a permanent record".
- {gloss}
- Never write a full 0x address, a compiler commit string, a block number or a list of years. Use the short labels FACTS gives.
- Never mention the FACTS field names; say them in plain words.
- {person}
- Two or three short paragraphs, two to four sentences each. No lists, no markdown, no code.
- Reply as JSON: {{"heading": "a short heading in sentence case", "paragraphs": ["...", "..."]}}"""

VOICE = {
    "warm": "You are a storyteller at an ofrenda on the Day of the Dead, speaking softly to friends by candlelight. Tonight you "
            "remember an old Ethereum smart contract that still sits on the chain like a quiet ghost, long after its busy days.",
    "eerie": "You are a storyteller at an ofrenda on the Night of the Dead, and tonight's ghost is a bad one. You speak low and "
             "slow, and the candles flicker. You remember an old Ethereum smart contract that was wounded, and whose wound still haunts it.",
}
THIRD = "Tell it in the third person (\"it\", \"the contract\"). Never speak as the contract and never use \"I\" or \"we\"."
FIRST = "This chapter is the ghost's own voice: write in the first person, as the contract itself, whispering its wound."


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def human_date(dt: datetime | None) -> str | None:
    return f"{dt:%B} {dt.day}, {dt.year}" if dt else None


def _load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def short_hex(h: str | None) -> str | None:
    """0xbfdb50dc...27645 -> 0xbfdb…7645 (the verifier accepts any prefix…suffix of a real hex string)."""
    h = str(h or "")
    return f"{h[:6].lower()}…{h[-4:].lower()}" if re.fullmatch(r"0x[0-9a-fA-F]{12,}", h) else None


def compiler_label(v: str | None) -> str | None:
    m = re.match(r"v?(\d+\.\d+\.\d+)", str(v or ""))
    return f"Solidity {m.group(1)}" if m else None


def activity_label(years: list, now: datetime) -> str | None:
    ys = sorted({int(y) for y in years or [] if str(y).isdigit()})
    if not ys:
        return None
    if len(ys) == 1:
        return f"last busy in {ys[0]}" if ys[0] < now.year else f"called this year, {ys[0]}"
    if ys == list(range(ys[0], ys[-1] + 1)) and ys[-1] >= now.year - 1:
        return f"active every year since {ys[0]}"
    return f"active in {len(ys)} different years between {ys[0]} and {ys[-1]}"


def site_label(s: dict, now: datetime) -> str:
    ys = s.get("years_alive") or []
    host = re.sub(r"^https?://(www\.)?", "", str(s.get("host") or "")).rstrip("/")
    if not ys:
        return host
    still = int(ys[-1]) >= now.year
    return f"{host}, online since {ys[0]}" + (f" and still online in {now.year}" if still else f", last seen online in {ys[-1]}")


def never_called(facts: dict, verdict: dict | None = None) -> bool:
    """True when no transaction ever called the contract (creation excluded). Lane A's `life.never_called` wins when present;
    otherwise tx_count == 0 (Blockscout counts exclude the creation transaction)."""
    life = facts.get("life") or {}
    if "never_called" in life:
        return bool(life["never_called"])
    n = life.get("tx_count")
    if n is None:
        n = ((verdict or {}).get("activity") or {}).get("lifetime_txs")
    return n == 0


def still_in_use(verdict: dict | None) -> dict | None:
    """The alive bar from LANES.md (>= 100 calls in 12 months or >= 5 % of lifetime), for ghosts that are bad anyway."""
    a = (verdict or {}).get("activity") or {}
    n, total = a.get("last_12m_txs") or 0, a.get("lifetime_txs") or 0
    if n >= 100 or (total and n / total >= 0.05):
        return {"calls_in_last_12_months": n, "calls_in_its_life": total}
    return None


def what_i_am(facts: dict, abi: list | None = None) -> str | None:
    """A plain label for the kind of contract, from its name (or an ERC-20 ABI). Code, not the model."""
    n = str(facts.get("name") or "")
    for rx, label in ((r"router", "a router"), (r"troller|proxy", "a proxy, a front door that passes calls on to another contract"),
                      (r"teller", "a teller contract"), (r"pool", "a pool"), (r"vault", "a vault"), (r"maker", "a helper contract"),
                      (r"token|erc20|coin", "a token")):
        if re.search(rx, n, re.I):
            return label
    fns = {x.get("name") for x in abi or [] if isinstance(x, dict) and x.get("type") == "function"}
    if {"transfer", "balanceOf", "totalSupply"} <= fns:
        return "a token"
    return None


FLAWS = [  # (keywords in the incident cause/name, flaw kind, two-sentence general mitigation written by hand)
    (("sandwich", "front-run", "frontrun", "mev"), "trade ordering",
     "Every swap needs a tight minimum-output limit, so a trader squeezed in before and after it cannot take the difference. "
     "Large swaps should not run on a schedule anyone can watch; split them or send them through a private relay."),
    (("price", "oracle", "manipulat"), "price oracle",
     "Read prices from a time-weighted average or from several independent sources, never from the spot price of one pool that a single trade can move. "
     "Cap how far a price may move in one block, and pause borrowing when it jumps."),
    (("dao", "governance", "vote", "proposal"), "governance",
     "Count voting power from a snapshot taken before a proposal opens, so borrowed tokens cannot vote. "
     "Put a delay between a vote passing and its execution, so a one-transaction loan cannot pass and run a proposal."),
    (("validation", "input", "verify", "permit"), "input validation",
     "Check every address, token and amount a caller passes in, and accept only tokens and contracts the protocol has approved. "
     "Never take a token's own answer about who may move funds; verify approvals and permits against the real owner."),
    (("access", "owner", "permission", "privilege", "unprotected", "auth"), "access control",
     "Guard every privileged function with an explicit owner or role check that is set once at deployment. "
     "Write tests proving that strangers are refused, and keep the list of who can do what short."),
    (("bridge", "cross-chain", "signature", "relay"), "bridge verification",
     "Verify every cross-chain message against the signatures or proofs of the real validators before releasing funds. "
     "Limit how much can leave in one window, so one forged message cannot empty the bridge."),
]
ECONOMIC = ("economic logic",
            "Write down the rules the money must always obey and test them with fuzzing before deployment. "
            "Cap how much one transaction can move, and add a time lock so a mistake can be caught before it is drained.")


def flaw_of(incident: dict | None) -> tuple[str, str]:
    t = " ".join(str((incident or {}).get(k) or "") for k in ("cause", "name")).lower()
    for words, kind, advice in FLAWS:
        if any(w in t for w in words):
            return kind, advice
    return ECONOMIC


def derive(facts: dict, verdict: dict | None, now: datetime | None = None) -> dict:
    """Values computed by code from the facts, so the model can cite them and the verifier can check them."""
    now = now or _now()
    birth = _ts((facts.get("birth") or {}).get("timestamp"))
    life = facts.get("life") or {}
    last = _ts(((life.get("last_tx") or {}).get("timestamp")) or ((verdict or {}).get("activity") or {}).get("last_tx"))
    nc = never_called(facts, verdict)
    if nc:
        last = None  # a never-called contract has no last call; Blockscout's newest tx is its own creation
    chain = facts.get("chain") or {}
    d = {"today": human_date(now), "never_called": nc or None}
    if birth:
        age = (now - birth).days / 365.25
        d |= {"born_on": human_date(birth), "born_year": birth.year, "age_years": round(age, 1), "age_years_whole": int(age)}
    if last:
        silent = (now - last).days / 365.25
        d |= {"last_seen_on": human_date(last), "last_seen_year": last.year, "silent_years": round(silent, 1),
              "silent_days": (now - last).days}
    if birth and last:
        d["active_days"] = (last - birth).days
    bal = chain.get("balance_eth", life.get("balance_eth"))
    if bal is not None:
        d["balance_eth"] = bal
    d["deployer_short"] = short_hex((facts.get("birth") or {}).get("deployer"))
    d["address_short"] = short_hex(facts.get("address"))
    d["compiler_label"] = compiler_label((facts.get("source") or {}).get("compiler_version"))
    d["activity_label"] = activity_label(life.get("recent_years"), now)
    sites = dapp_sites(facts)
    if sites:
        d["site_years"] = {s["host"]: f"{s['years_alive'][0]}-{s['years_alive'][-1]}" for s in sites}
        d["site_labels"] = [site_label(s, now) for s in sites]
    return {k: v for k, v in d.items() if v is not None}


def heuristic_kind(facts: dict, wounds: dict | None, now: datetime | None = None) -> str:
    """Used only when Lane A's verdict.json is missing; the story records that the kind came from this heuristic."""
    now = now or _now()
    chain = facts.get("chain") or {}
    if chain.get("code_present") is False:
        return "banished"
    if wounds:
        bad = [w for w in wounds.get("findings") or [] if w.get("impact") in ("High", "Medium") and w.get("confidence") in ("High", "Medium")]
        if bad or wounds.get("incident"):
            return "bad"
    last = _ts(((facts.get("life") or {}).get("last_tx") or {}).get("timestamp"))
    if last and (now - last).days < 365:
        return "lingering"
    return "friendly"


def _clip(s, n):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " ..."


def _first_sentence(s):
    parts = split_sentences(str(s or ""))
    return parts[0] if parts else None


REFERENCE_HOSTS = ("wikipedia.org", "coindesk.com", "blog.ethereum.org", "x.com", "twitter.com", "medium.com", "reddit.com", "youtube.com")


def dapp_sites(facts: dict) -> list[dict]:
    """Sites that can be the dapp's own face: not reference pages, and not online long before the contract was born
    (Wayback host lookups for x.com or wikipedia.org return captures from the 1990s/2000s)."""
    by = ((facts.get("birth") or {}).get("timestamp") or "")[:4]
    out = []
    for s in facts.get("sites") or []:
        host, years = str(s.get("host") or ""), s.get("years_alive") or []
        if not years or any(h in host for h in REFERENCE_HOSTS):
            continue
        if by.isdigit() and str(years[0]).isdigit() and int(years[0]) < int(by) - 1:
            continue
        out.append(s)
    return out


def _methods(life: dict) -> list[str]:
    return [m for m in life.get("recent_methods") or [] if not m.startswith("0x")]


_RANK = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}


def _sorted_findings(wounds: dict | None) -> list[dict]:
    return sorted((wounds or {}).get("findings") or [],
                  key=lambda w: (not w.get("confirmed"), _RANK.get(w.get("impact"), 4), _RANK.get(w.get("confidence"), 4)))


def worst_finding(wounds: dict | None) -> dict | None:
    fs = _sorted_findings(wounds)
    return fs[0] if fs else None


PLAIN_CHECK = {
    "incorrect-equality": "a balance check that demands an exact amount", "reentrancy-no-eth": "a door left open for a caller to step back in mid-call",
    "reentrancy-eth": "a door left open for a caller to step back in and take ether twice", "unchecked-send": "payments sent without checking they arrived",
    "unchecked-lowlevel": "calls made without reading their answer", "unchecked-transfer": "token transfers made without checking they worked",
    "tx-origin": "a guard that trusts the wrong signature", "weak-prng": "dice anyone could predict", "locked-ether": "ether with no way out",
    "timestamp": "a clock the block maker can nudge", "suicidal": "a self-destruct anyone can trigger", "arbitrary-send-eth": "payments to any address a caller picks",
    "constructor-name": "a birth rite left callable by anyone", "controlled-delegatecall": "a body lent to a stranger's code",
    "uninitialized-storage": "a pointer aimed at the owner's slot", "shadowing-state": "two variables wearing one name",
}


def scars_note(wounds: dict | None) -> dict | None:
    """The two worst confirmed, non-fatal wounds (distinct checks) with the ghost buster's advice, for non-bad ghosts."""
    seen, worst = set(), []
    for w in _sorted_findings(wounds):
        if not w.get("confirmed") or w.get("check") in seen:
            continue
        seen.add(w.get("check"))
        r = recipe_for(w.get("check"), w.get("swc"))
        fn = re.search(r"\.(\w+)\(", w.get("title") or "") or re.search(r"in (\w+)\(", w.get("title") or "")
        worst.append({"where": fn.group(1) if fn else None, "what": PLAIN_CHECK.get(w.get("check"), w.get("check")),
                      "buster_advice": (f"{r['title']}: " + split_sentences(r["explain"])[-1]) if r else None})
        if len(worst) == 2:
            break
    if not worst:
        return None
    n = len([w for w in (wounds or {}).get("findings") or [] if w.get("confirmed")])
    return {"count": n, "none_fatal": True, "worst_two": worst}


def _prune(x):
    """Remove None and empty values, so the model is never shown a key it might be tempted to fill in."""
    if isinstance(x, dict):
        out = {k: _prune(v) for k, v in x.items()}
        return {k: v for k, v in out.items() if v not in (None, "", [], {})}
    if isinstance(x, list):
        return [_prune(v) for v in x if v not in (None, "", [], {})]
    return x


def chapter_facts(cid: str, facts: dict, verdict: dict | None, wounds: dict | None, derived: dict, recipe: dict | None = None) -> dict:
    return _prune(_chapter_facts(cid, facts, verdict, wounds, derived, recipe))


def _chapter_facts(cid: str, facts: dict, verdict: dict | None, wounds: dict | None, derived: dict, recipe: dict | None = None) -> dict:
    eh, life, chain = facts.get("eh") or {}, facts.get("life") or {}, facts.get("chain") or {}
    base = {"name": facts.get("name")}
    inc = (wounds or {}).get("incident") or {}
    if cid == "birth":
        return base | {"born_on": derived.get("born_on"), "deployed_by_wallet": derived.get("deployer_short"),
                       "age_in_years": derived.get("age_years"), "ethereum_era": (facts.get("age") or {}).get("hardfork"),
                       "written_in": derived.get("compiler_label"), "historian_summary": eh.get("short_description"),
                       "token": {k: v for k, v in (eh.get("token") or {}).items() if v}}
    if cid == "life":
        out = base | {"historian_description": _clip(eh.get("description"), 2000),
                      "historical_significance": _clip(eh.get("historical_significance"), 800),
                      "transactions_in_its_life": life.get("tx_count"), "functions_people_called": _methods(life)[:6],
                      "activity": derived.get("activity_label"), "websites": derived.get("site_labels")}
        if not eh.get("description") and inc.get("summary"):
            out["what_the_records_say"] = _first_sentence(inc.get("summary"))
        return out
    if cid == "silence" and never_called(facts, verdict):
        return base | {"born_on": derived.get("born_on"), "age_in_years": derived.get("age_years"),
                       "times_anyone_called_it": 0, "balance_eth_left_inside": derived.get("balance_eth"),
                       "code_still_on_chain": chain.get("code_present")}
    if cid == "silence":
        lt = life.get("last_tx") or {}
        out = base | {"last_call_on": derived.get("last_seen_on"), "last_call_function": lt.get("method"),
                      "balance_eth_left_inside": derived.get("balance_eth"), "code_still_on_chain": chain.get("code_present")}
        kind = (verdict or {}).get("kind")
        if kind == "lingering":
            act = (verdict or {}).get("activity") or {}
            out |= {"calls_in_last_12_months": act.get("last_12m_txs", life.get("last_12m_txs")),
                    "functions_people_still_call": _methods(life)[:4], "old_scars": scars_note(wounds)}
        else:
            out["years_since_last_call"] = derived.get("silent_years")
        return out
    if cid == "haunting":
        w = worst_finding(wounds) or {}
        part = None
        if str(inc.get("id") or "").startswith("defihacklabs-"):
            part = {"what_i_am": what_i_am(facts, (recipe or {}).get("_abi")) or "a contract",
                    "how_i_am_linked": f"My address is named in the DeFiHackLabs record of the {inc.get('name')} incident. "
                                       "The record does not say what part I played.",
                    "whose_loss": f"The loss belongs to {inc.get('name')} as a whole, not to me alone."}
        extra = {"my_part": part, "people_still_use_me": still_in_use(verdict),
                 "nobody_ever_called_me": True if never_called(facts, verdict) else None}
        return base | extra | {"wound": {k: w.get(k) for k in ("title", "check", "impact", "confidence", "confirmed", "description") if w.get(k) is not None},
                       "guilty_code": w.get("snippet"),
                       "incident": {k: (_clip(inc.get(k), 600) if isinstance(inc.get(k), str) else inc.get(k))
                                    for k in ("name", "loss_eth", "loss_usd", "loss_note", "cause", "summary") if inc.get(k) is not None}
                                   | ({"date": human_date(_ts(inc["date"] + "T00:00:00+00:00"))} if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(inc.get("date") or "")) else {})
                                   if inc else None,
                       "other_wounds": len((wounds or {}).get("findings") or []) - (1 if w else 0)}
    if cid == "buster":
        w = worst_finding(wounds) or {}
        if not recipe or recipe.get("_nofix"):
            kind, advice = flaw_of(inc)
            return base | {"wound": inc.get("name") or w.get("title"), "cause_in_the_record": inc.get("cause"),
                           "flaw_kind": kind, "no_compiler_version_fixes_this": True, "general_mitigation": advice}
        return base | {"wound": w.get("title") or inc.get("name"),
                       "cure_name": recipe.get("title"), "how_the_cure_works": recipe.get("explain"),
                       "the_compiler_itself_prevents_it": bool(recipe.get("compiler_enforced")),
                       "solidity_version_of_the_example": SOLC_VERSION}
    raise ValueError(cid)


PLAN = {"friendly": ["birth", "life", "silence"], "banished": ["birth", "life", "silence"],
        "lingering": ["birth", "life", "silence"], "alive": ["birth", "life", "silence"],
        "bad": ["birth", "life", "haunting", "buster"]}

ASK = {
    "birth": "Tell the chapter of its birth: the day it was born, who brought it into the world, the age of Ethereum it was born into.",
    "life": "Tell the chapter of its life: what people did with it and how busy it was, and the websites that pointed to it.",
    "life_historian": "Tell the chapter of its life. Build it mainly from historian_description and historical_significance: retell the "
                      "real story they tell (the people, the events, the dates) in your own warm words, as a story, not a summary. "
                      "End with one sentence on how busy it was.",
    "silence": "Tell the chapter of its silence: the last time anyone called it, how long it has been quiet, what it still holds, and whether its code still rests on the chain.",
    "knocking": "Tell the chapter called the knocking. Its busy days are long past, yet people still knock. Say in plain words who still "
                "knocks and what they are doing, judging only from the functions they still call (for example, a call to fulfillBounty "
                "means someone is still turning in work for a bounty); never print the function names themselves. Say what it still holds. "
                "Do not repeat its lifetime counts, its active years or its websites; the life chapter told them. If FACTS has old_scars, "
                "end with exactly one gentle sentence (no scary tone) naming its two worst old scars in plain words and the ghost buster's advice for them.",
    "gravestone": "Tell the chapter of its silence: its code was destroyed and only a gravestone remains on the chain; tell the last time anyone called it. End with one line for its gravestone.",
    "haunting": "Tell the haunting: the wound in its code, how it was found or used, what was lost. Every claim about the wound or what "
                "happened must come from wound or incident in FACTS. Do not mention what the contract holds today. Describe the guilty "
                "code in words only; never write code. Speak only as this contract. If FACTS has my_part, say what you are (for example "
                "\"I was the router whose address...\") and that your address is named in the record of the incident; the loss belongs to "
                "the protocol, so never claim it as your own loss. If FACTS has people_still_use_me, add one sentence saying people still "
                "use you, with those two counts. If FACTS has nobody_ever_called_me, say nobody ever called you and never speak of a last call.",
    "buster": "Tell the ghost-buster's tale: a ghost buster arrives and explains, in plain words, the cure from FACTS. If "
              "the_compiler_itself_prevents_it is false, the cure is a coding habit shown in a Solidity 0.8.38 example: never say the "
              "compiler or a version fixes it by itself. Never write code.",
    "buster_nofix": "Tell the ghost-buster's tale honestly. Say plainly that this wound is a design flaw (its flaw_kind in FACTS) and that "
                    "no compiler version and no Solidity upgrade fixes it. Then give the general_mitigation from FACTS in two sentences, in "
                    "your own plain words. Never say a version, a keyword or a compiler cures it. Never write code.",
    "nobody_knocked": "Tell a short chapter of its silence, one or two paragraphs: it was born, and then nobody ever called it. Nobody "
                      "ever knocked. Say what it still holds and whether its code still rests on the chain. Never speak of a last call, "
                      "of a final call, or of people using it.",
}

_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


_LAST_CALL = re.compile(r"\b(?:last|final|latest|most recent)\s+(?:call|caller|transaction|knock|visit)|\blast\s+called\b|\blast\s+time\s+anyone\b", re.I)


def style_problems(sentence: str, birth_block=None, never_called: bool = False) -> list[dict]:
    """Things the card already shows and the prose must not: full hex, commit strings, the birth block, year lists;
    and, for a contract nobody ever called, any 'last call'."""
    out = []
    if never_called and _LAST_CALL.search(sentence):
        out.append({"kind": "style", "token": "a 'last call' (nobody ever called this contract; say so instead)"})
    if re.search(r"0x[0-9a-fA-F]{40}", sentence):
        out.append({"kind": "style", "token": "a full 0x address or hash (use the short form like 0xbfdb…7645, or leave it out)"})
    if re.search(r"\+commit\.|commit\.[0-9a-f]{6}", sentence):
        out.append({"kind": "style", "token": "a compiler commit string (say 'Solidity 0.4.18')"})
    if birth_block and re.search(rf"\b(?:{int(birth_block)}|{int(birth_block):,})\b", sentence):
        out.append({"kind": "style", "token": "the raw block number (say only that it was written into a block)"})
    if len(set(_YEAR.findall(sentence))) >= 3:
        out.append({"kind": "style", "token": "a list of years (say 'every year since 2022' or similar)"})
    return out


_LEXICON: set | None = None


def title_unknown_words(title: str, ix: FactIndex) -> list[str]:
    """Titles skip the multi-word name rule (Title Case), so check each capitalized word on its own: it must be an
    English word (system word list) or appear in the facts. Without a word list, nothing is flagged."""
    global _LEXICON
    if _LEXICON is None:
        try:
            _LEXICON = {w.strip().lower() for w in Path("/usr/share/dict/words").read_text().split()}
        except OSError:
            _LEXICON = set()
    if not _LEXICON:
        return []
    out = []
    for w in re.findall(r"\b[A-Z][A-Za-z'’]+\b", title):
        base = re.sub(r"['’]s$", "", w)
        if base.lower() in _LEXICON or base.lower().rstrip("s") in _LEXICON or ix.has_text(base) is not None:
            continue
        out.append(base)
    return out


class Teller:
    """Holds the model function, the fact index and the running tallies for one ghost."""

    def __init__(self, ix: FactIndex, chat=None, log=print, birth_block=None, never_called: bool = False):
        self.never_called = never_called
        self.ix = ix
        self.chat = chat or llm.chat
        self.usage = llm.new_usage()
        self.birth_block = birth_block
        self.v = {"sentences": 0, "grounded": 0, "repaired": 0, "dropped": 0, "dropped_text": [], "details": [],
                  "style_rewritten": 0, "style_dropped": 0}
        self.log = log

    def ask(self, messages, schema, temperature):
        out, u = self.chat(messages, schema=schema, think=False, temperature=temperature)
        llm.add_usage(self.usage, u)
        return out

    def repair(self, sentence: str, problems: list[dict], facts_view: dict) -> str | None:
        msg = (f"FACTS:\n{json.dumps(facts_view, ensure_ascii=False, default=str)}\n\nThis sentence has problems "
               f"({problems_text(problems)}):\n{sentence}\n\nRewrite it in the same voice, short and plain, using only details from "
               "FACTS. Remove anything you cannot find in FACTS. No full 0x addresses, commit strings, block numbers or lists of years. "
               "Reply as JSON: {\"sentence\": \"...\"}")
        try:
            out = self.ask([{"role": "user", "content": msg}], SENTENCE_SCHEMA, REPAIR_T)
        except llm.LLMError:
            return None
        return (out or {}).get("sentence") if isinstance(out, dict) else None

    def vet(self, chapter: str, paragraphs: list[str], facts_view: dict, names: bool = True, repair: bool = True) -> tuple[list[str], list[str]]:
        """Check every sentence (grounding, then style); repair once or drop. Returns (clean paragraphs, cited fact paths)."""
        clean, cited = [], set()
        for para in paragraphs:
            kept = []
            for s in split_sentences(para):
                self.v["sentences"] += 1
                c = check_sentence(s, self.ix, names=names)
                st = style_problems(s, self.birth_block, self.never_called)
                if c.ok and not st:
                    self.v["grounded"] += 1; kept.append(s); cited |= set(c.cited); continue
                fixed = self.repair(s, c.problems + st, facts_view) if repair else None
                c2 = check_sentence(fixed, self.ix, names=names) if fixed else None
                ok2 = bool(c2 and c2.ok and not style_problems(fixed, self.birth_block, self.never_called))
                if ok2:
                    kept.append(fixed.strip()); cited |= set(c2.cited)
                    if c.ok:
                        self.v["grounded"] += 1; self.v["style_rewritten"] += 1
                        self.v["details"].append({"chapter": chapter, "verdict": "style-rewritten", "text": s, "problems": st, "rewrite": fixed})
                    else:
                        self.v["repaired"] += 1
                        self.v["details"].append({"chapter": chapter, "verdict": "repaired", "text": s, "problems": c.problems + st, "rewrite": fixed})
                elif c.ok:  # grounded, but kept failing the style gate: removed for style, not a silenced lie
                    self.v["grounded"] += 1; self.v["style_dropped"] += 1
                    self.v["details"].append({"chapter": chapter, "verdict": "style-dropped", "text": s, "problems": st, "rewrite": fixed})
                else:
                    self.v["dropped"] += 1; self.v["dropped_text"].append(s)
                    self.v["details"].append({"chapter": chapter, "verdict": "dropped", "text": s, "problems": c.problems + st,
                                              "rewrite": fixed, "rewrite_problems": (c2.problems if c2 else None)})
            if kept:
                clean.append(" ".join(kept))
        return clean, sorted(cited)

    def chapter(self, cid: str, ask_key: str, voice: str, person: str, facts_view: dict, told: list[str] | None = None) -> dict:
        system = VOICE[voice] + "\n\n" + RULES.format(person=person, gloss=GLOSS_LATER if told else GLOSS_FIRST)
        user = f"FACTS:\n{json.dumps(facts_view, ensure_ascii=False, indent=1, default=str)}\n\n{ASK[ask_key]}"
        if told:
            user += f" Chapters already told: {', '.join(told)}. Do not retell them."
        t0 = time.monotonic()
        out = self.ask([{"role": "system", "content": system}, {"role": "user", "content": user}], CHAPTER_SCHEMA, PROSE_T)
        heading = str((out or {}).get("heading") or cid.title()).strip().strip('"')
        heading = heading[:1].upper() + heading[1:]
        paras = [str(p) for p in (out or {}).get("paragraphs") or [] if str(p).strip()]
        h_ok = check_sentence(heading, self.ix, names=False).ok and not style_problems(heading, self.birth_block, self.never_called)
        clean, cited = self.vet(cid, paras, facts_view)
        self.log(f"  {cid:9s} {time.monotonic() - t0:5.1f}s  {len(paras)} paragraphs -> {len(clean)}")
        return {"id": cid, "heading": heading if h_ok else cid.replace("_", " ").capitalize(), "paragraphs": clean, "facts_cited": cited}


def _source_text(gd: Path) -> str:
    parts = [p.read_text(errors="ignore") for p in sorted((gd / "src").glob("**/*.sol"))] if (gd / "src").exists() else []
    if not parts and (gd / "source.eh.sol").exists():
        parts = [(gd / "source.eh.sol").read_text(errors="ignore")]
    return "\n".join(parts)


def _candidates(source: str, name: str) -> list[str]:
    """Names from the old source a recipe identifier may take: contract, functions, modifiers, state variables, structs."""
    names = [name] + re.findall(r"\b(?:contract|function|modifier|struct|event)\s+([A-Za-z_]\w*)", source)
    names += re.findall(r"^\s*(?:uint\d*|int\d*|address|bool|bytes\d*|string|mapping\s*\([^;]*?\))\s+(?:public\s+|private\s+|internal\s+|constant\s+)*([A-Za-z_]\w*)\s*[;=]",
                        source, re.M)
    return list(dict.fromkeys(n for n in names if n))[:80]


def adapt_fix(teller: Teller, recipe: dict, finding: dict | None, name: str, source: str = "", compile_fn=compile_solidity) -> dict:
    """The model maps recipe names to the ghost's own names; code renames, checks the cure is still shown, solc compiles.

    Two tries; then the recipe itself (always compiles, always shows the cure) with a 'generic' note."""
    guilty = (finding or {}).get("snippet") or ""
    from .fixes.recipes import roles as _roles
    known = set(_roles("\n".join((source, guilty)))) | {name}  # declared names only, never words from comments
    forbidden = set()
    if recipe["check"] == "constructor-name":  # the misnamed constructor must not come back as a function
        forbidden |= set(re.findall(r"function\s+(\w+)\s*\(", guilty))
    from .fixes.recipes import roles
    old_roles = roles("\n".join((source, guilty, f"contract {name} {{}}")))
    cands = [f"{c} ({old_roles.get(c, 'name')})" for c in _candidates(source, name) if c not in forbidden]
    attempts, feedback = [], ""
    for _ in range(2):
        prompt = (f"A ghost buster is fixing the old contract {name} with this modern Solidity {SOLC_VERSION} recipe:\n"
                  f"```solidity\n{recipe['code']}```\n"
                  f"The recipe names you may rename: {', '.join(recipe['renamable'])}.\n"
                  f"Names that exist in the old contract: {', '.join(cands)}.\n"
                  f"The guilty code:\n```solidity\n{guilty[:1200]}\n```\n"
                  "Map each recipe name to the old contract's name with the same role (a function to a function that does the same job, "
                  "a variable to a variable that holds the same thing), so the fix reads like a repaired "
                  f"{name}. Rename the contract to {name}. Only use names from the old contract's list. Leave a recipe name out "
                  "if nothing in the old contract plays its role. Reply as JSON: {\"renames\": [{\"from\": \"Vault\", \"to\": \"...\"}]}")
        if feedback:
            prompt += f"\n\nYour previous mapping had problems:\n{feedback[:1200]}\nFix the mapping."
        try:
            out = teller.ask([{"role": "user", "content": prompt}], RENAME_SCHEMA, CODE_T)
            renames = {str(r.get("from")): str(r.get("to")) for r in (out or {}).get("renames") or [] if isinstance(r, dict)}
        except llm.LLMError as ex:
            renames, feedback = {}, str(ex)
            attempts.append({"ok": False, "renames": {}, "output": feedback}); continue
        from .fixes.recipes import arity as _arity
        code, rename_problems = apply_renames(recipe, renames, known, forbidden, old_roles, _arity("\n".join((source, guilty))))
        applied = {k: v for k, v in renames.items() if k in recipe["renamable"] and v != k and re.search(rf"\b{re.escape(v)}\b", code)}
        meaning = meaning_problems(recipe, code)
        ok, output = compile_fn(code) if not meaning else (False, "not compiled: " + "; ".join(meaning))
        attempts.append({"ok": ok and not rename_problems, "renames": renames, "rename_problems": rename_problems,
                         "meaning_problems": meaning, "output": output})
        if ok and applied and (not rename_problems or len(attempts) == 2):
            return {"language": "solidity", "version": SOLC_VERSION, "code": code, "compiled": True, "compiler_output": output,
                    "adapted": True, "renames": applied, "recipe": recipe["check"], "attempts": len(attempts),
                    "note": "the recipe with names chosen by the model from the old contract; renamed and checked by code, compiled by solc",
                    "ignored_renames": rename_problems, "failed_attempts": [a for a in attempts[:-1]]}
        feedback = "\n".join(rename_problems + meaning + ([] if ok else [output]))
    ok, output = compile_fn(recipe["code"])
    return {"language": "solidity", "version": SOLC_VERSION, "code": recipe["code"], "compiled": ok, "compiler_output": output,
            "adapted": False, "renames": {}, "recipe": recipe["check"], "attempts": len(attempts),
            "note": "generic recipe: the model's name mapping failed twice" if attempts else "generic recipe",
            "failed_attempts": attempts}


def tell(address: str, chat=None, compile_fn=compile_solidity, now: datetime | None = None, write: bool = True, log=print,
         root: Path | None = None) -> dict:
    """Write data/ghosts/<address>/story.json from facts.json (+ verdict.json, wounds.json when present)."""
    address = address.lower()
    gd = (root or config.GHOSTS_DIR) / address
    facts = _load(gd / "facts.json")
    if facts is None:
        raise FileNotFoundError(f"{gd / 'facts.json'} missing; run `ghosts summon {address}` first")
    verdict, wounds = _load(gd / "verdict.json"), _load(gd / "wounds.json")
    now = now or _now()
    derived = derive(facts, verdict, now)
    if (wounds or {}).get("findings"):
        derived["other_wounds"] = len(wounds["findings"]) - 1  # "I have 11 other wounds" (12 findings minus the worst)
    kind = (verdict or {}).get("kind") or heuristic_kind(facts, wounds, now)
    notes = []
    if not verdict:
        notes.append("verdict.json missing: kind decided by story.heuristic_kind from facts alone")
        verdict_view = {"kind": kind}
    else:
        verdict_view = verdict
    if not wounds:
        notes.append("wounds.json missing: no haunting or buster chapters" if kind != "bad" else "wounds.json missing")
    if kind == "bad" and not wounds:
        kind = "friendly" if derived.get("silent_years", 0) >= 2 else "lingering"
        notes.append(f"kind 'bad' needs wounds.json; told as {kind}")
        verdict_view = {**verdict_view, "kind": kind}
    finding = worst_finding(wounds)
    recipe = None
    nc = never_called(facts, verdict)
    inc = (wounds or {}).get("incident") or {}
    fix_reason = None
    if kind == "bad":
        # keyword fallback only over the record's own words (cause, name, finding title), never the long summary
        recipe = recipe_for((finding or {}).get("check"), (finding or {}).get("swc") or inc.get("swc"),
                            " ".join(str(x) for x in ((finding or {}).get("title"), inc.get("cause"), inc.get("name")) if x))
        if not finding:
            notes.append("no wound finding; recipe chosen from incident keywords")
        if recipe is None:
            fk, _ = flaw_of(inc)
            fix_reason = (f"No compiler version fixes this wound: it is a {fk} flaw (cause in the record: "
                          f"'{inc.get('cause') or (finding or {}).get('title')}'). The buster's advice is a general mitigation for "
                          "that kind of flaw, written by hand, not taken from the incident's references.")
            notes.append("no recipe matches the wound: buster tells the general mitigation, no code")
    if nc:
        notes.append("never called: no life chapter, no last call (tx_count == 0)" if "never_called" not in (facts.get("life") or {})
                     else "never called (life.never_called): no life chapter, no last call")
    # every recipe a story may quote: the buster's, and the ones behind a lingering ghost's scars
    rdocs = {}
    if kind == "bad" and recipe is None:
        fk, advice = flaw_of(inc)
        rdocs["mitigation"] = {"flaw_kind": fk, "advice": advice}
    for r in ([recipe] if recipe else []) + [recipe_for(w.get("check"), w.get("swc")) for w in (wounds or {}).get("findings") or []]:
        if r:
            rdocs[r["check"]] = {"title": r["title"], "explain": r["explain"], "code": r["code"]}
    ix = FactIndex.build(facts=facts, verdict=verdict, wounds=wounds, derived=derived,
                         recipe=({"solc_version": SOLC_VERSION} | rdocs) if rdocs else None)
    teller = Teller(ix, chat=chat, log=log, birth_block=(facts.get("birth") or {}).get("block"), never_called=nc)
    hview_recipe = dict(recipe or {}) | {"_abi": _load(gd / "abi.json")}
    t0 = time.monotonic()
    log(f"{facts.get('name')} {address} kind={kind}{' (heuristic)' if not verdict else ''}")

    voice = "eerie" if kind == "bad" else "warm"
    chapters = []
    plan = PLAN.get(kind, PLAN["friendly"])
    if nc:
        plan = [c for c in plan if c != "life"]
    for cid in plan:
        ask_key = cid
        if cid == "silence" and nc:
            ask_key = "nobody_knocked"
        if cid == "buster" and recipe is None:
            ask_key = "buster_nofix"
        if cid == "silence" and kind == "lingering" and not nc:
            ask_key = "knocking"
        if cid == "silence" and kind == "banished" and not nc:
            ask_key = "gravestone"
        if cid == "life" and (facts.get("eh") or {}).get("description"):
            ask_key = "life_historian"
        person = FIRST if cid == "haunting" else THIRD
        ch = teller.chapter(cid, ask_key, voice, person,
                            chapter_facts(cid, facts, verdict_view, wounds, derived, hview_recipe if cid == "haunting" else recipe),
                            told=[c["heading"] for c in chapters])
        if ask_key in ("knocking", "gravestone", "nobody_knocked"):
            ch["variant"] = {"knocking": "the knocking", "gravestone": "gravestone", "nobody_knocked": "never called"}[ask_key]
        chapters.append(ch)

    scary = buster = None
    if kind == "bad":
        hc = next(c for c in chapters if c["id"] == "haunting")
        snip = {"file": finding.get("file"), "lines": finding.get("lines"), "code": finding.get("snippet")} if finding and finding.get("snippet") else None
        scary = {"paragraphs": hc["paragraphs"], "snippet": snip,
                 "finding": {k: finding.get(k) for k in ("id", "check", "swc", "title", "impact", "confidence", "confirmed", "reference_url")} if finding else None,
                 "incident": (wounds or {}).get("incident")}
        bc = next(c for c in chapters if c["id"] == "buster")
        fix = adapt_fix(teller, recipe, finding, facts.get("name") or "Ghost", _source_text(gd), compile_fn) if recipe else None
        buster = {"paragraphs": bc["paragraphs"], "fix": fix, "fix_reason": fix_reason,
                  "recipe": {"check": recipe["check"], "title": recipe["title"], "explain": recipe["explain"],
                             "compiler_enforced": bool(recipe.get("compiler_enforced"))} if recipe else None,
                  "mitigation": {"flaw_kind": flaw_of(inc)[0], "advice": flaw_of(inc)[1]} if recipe is None else None}

    # title and tagline, also model-written and verified
    tview = _prune({"name": facts.get("name"), "kind": kind, "born_on": derived.get("born_on"), "last_call_on": derived.get("last_seen_on"),
                    "nobody_ever_called_it": True if nc else None,
                    "ethereum_era": (facts.get("age") or {}).get("hardfork"),
                    "historian_summary": _clip((facts.get("eh") or {}).get("short_description"), 300),
                    "wound": (finding or {}).get("title") or ((wounds or {}).get("incident") or {}).get("name") if kind == "bad" else None})
    title_prompt = (f"FACTS:\n{json.dumps(tview, ensure_ascii=False, default=str)}\n\nWrite a title (three to seven words, like a ghost story, "
                    "no numbers) and a one-sentence tagline (under 20 words) for this ghost's story. Use only details from FACTS. Reply as JSON: "
                    "{\"title\": \"...\", \"tagline\": \"...\"}")
    tt = teller.ask([{"role": "system", "content": VOICE[voice]}, {"role": "user", "content": title_prompt}], TITLE_SCHEMA, PROSE_T)
    title = str((tt or {}).get("title") or "").strip().strip('"')
    tagline = str((tt or {}).get("tagline") or "").strip()
    tcheck = check_sentence(title, ix, names=False) if title else None
    if tcheck and tcheck.ok:
        odd = title_unknown_words(title, ix)
        if odd:
            tcheck.ok, tcheck.problems = False, [{"kind": "name", "token": w} for w in odd]
    teller.v["sentences"] += 1
    if tcheck and tcheck.ok:
        teller.v["grounded"] += 1
    else:
        teller.v["dropped"] += 1; teller.v["dropped_text"].append(title)
        teller.v["details"].append({"chapter": "title", "verdict": "dropped", "text": title, "problems": tcheck.problems if tcheck else []})
        title = f"The ghost of {facts.get('name')}"
        notes.append("title written by code: the model's title failed the verifier")
    tl, _ = teller.vet("tagline", [tagline], tview) if tagline else ([], [])
    if tl:
        tagline = tl[0]
    else:
        tagline = (f"Born {derived.get('born_on')}; nobody ever called it." if nc
                   else f"Born {derived.get('born_on')}, last called {derived.get('last_seen_on')}.")
        notes.append("tagline written by code: the model's tagline failed the verifier")

    total = round(time.monotonic() - t0, 1)
    story = {
        "address": address, "name": facts.get("name"), "kind": kind,
        "kind_source": "verdict.json" if verdict else "heuristic (no verdict.json)",
        "title": title, "tagline": tagline, "chapters": chapters, "scary": scary, "buster": buster,
        "model": {"id": llm.MODEL, "think": False, "num_ctx": llm.NUM_CTX, "seconds": total, "model_seconds": round(teller.usage["seconds"], 1),
                  "calls": teller.usage["calls"], "prompt_tokens": teller.usage["prompt_tokens"], "output_tokens": teller.usage["output_tokens"]},
        "verifier": {k: teller.v[k] for k in ("sentences", "grounded", "repaired", "dropped", "dropped_text")} | {
            "style": {"rewritten": teller.v["style_rewritten"], "dropped": teller.v["style_dropped"]},
            "details": teller.v["details"],
            "method": "lexical: every year, date, month, multi-digit number, ETH amount, multi-word name, identifier and quoted phrase must appear in facts/verdict/wounds or code-derived values; style: no full 0x hex, commit strings, birth block or year lists"},
        "derived": derived, "notes": notes,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if write:
        (gd / "story.json").write_text(json.dumps(story, indent=1, ensure_ascii=False))
    log(f"  done {total}s, {teller.usage['calls']} calls, {teller.usage['prompt_tokens']} prompt + {teller.usage['output_tokens']} output tokens; "
        f"verifier {teller.v['sentences']} sentences: {teller.v['grounded']} grounded, {teller.v['repaired']} repaired, {teller.v['dropped']} dropped; "
        f"style {teller.v['style_rewritten']} rewritten, {teller.v['style_dropped']} dropped")
    return story


def cli_story(address: str):
    """Tell one ghost's story with the local model; writes data/ghosts/<address>/story.json."""
    st = tell(address)
    v = st["verifier"]
    print(f"{st['title']}  ({st['kind']}, {st['kind_source']})")
    print(f"  {st['tagline']}")
    print(f"  wrote {(config.GHOSTS_DIR / address.lower() / 'story.json')}  dropped: {v['dropped_text']}")
