"""One recipe per wound check: what modern Solidity does about it (two sentences) and a minimal 0.8.38 snippet.

Every snippet here compiles with solc 0.8.38 (`uv run pytest tests/test_b_fixes.py` checks it when solc is present).
The explanations are written once, by hand, and are shown as-is; the model only tells the tale around them.
"""
from __future__ import annotations
import re

R: dict[str, dict] = {}


def _r(key, title, explain, code, swc=(), aliases=()):
    R[key] = {"check": key, "title": title, "explain": explain, "code": code.strip() + "\n", "swc": list(swc), "aliases": list(aliases)}


_r("reentrancy-eth", "Pay last, lock the door",
   "Modern contracts follow checks-effects-interactions: they update their own books before they send ether, so a caller "
   "that calls back in finds the balance already at zero. A reentrancy lock (a `nonReentrant` modifier, or OpenZeppelin's "
   "ReentrancyGuard) closes the door for the whole function, and `call` replaces the old `send` with a checked return value.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Vault {
    mapping(address => uint256) public balances;
    bool private locked;

    modifier nonReentrant() {
        require(!locked, "reentrant call");
        locked = true;
        _;
        locked = false;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external nonReentrant {
        uint256 amount = balances[msg.sender];   // checks
        require(amount > 0, "nothing to withdraw");
        balances[msg.sender] = 0;                // effects
        (bool ok, ) = payable(msg.sender).call{value: amount}("");  // interactions
        require(ok, "transfer failed");
    }
}
""", swc=["SWC-107"], aliases=["reentrancy-no-eth", "reentrancy-benign", "reentrancy-events", "reentrancy", "reentrancy-unlimited-gas"])

_r("unchecked-lowlevel", "Read the answer of every call",
   "Old `send` and low-level `call` return false instead of failing, so a contract that ignores the answer keeps going as if "
   "the money arrived. Modern Solidity code checks the boolean that `call` returns and reverts on failure, and it lets each "
   "recipient pull its own payment so one stubborn wallet cannot block everyone else.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Payouts {
    mapping(address => uint256) public owed;

    function credit(address who) external payable {
        owed[who] += msg.value;
    }

    // Pull, don't push: each recipient withdraws, and a failed transfer reverts instead of vanishing.
    function claim() external {
        uint256 amount = owed[msg.sender];
        require(amount > 0, "nothing owed");
        owed[msg.sender] = 0;
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "transfer failed");
    }
}
""", swc=["SWC-104"], aliases=["unchecked-send", "unchecked-transfer", "unchecked-call", "unchecked-return", "send-gas-stipend"])

_r("suicidal", "No one may pull the plug",
   "`selfdestruct` is deprecated since Solidity 0.8.18, and since the Cancun upgrade (EIP-6780) it no longer deletes a "
   "contract's code unless called in the same transaction that created it. A modern contract simply leaves it out and guards "
   "every dangerous function with an explicit owner check set in the `constructor`.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Guarded {
    address public immutable owner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    // No selfdestruct: retire the contract by pausing it and letting the owner sweep funds.
    bool public retired;

    function retire(address payable to) external onlyOwner {
        retired = true;
        (bool ok, ) = to.call{value: address(this).balance}("");
        require(ok, "sweep failed");
    }
}
""", swc=["SWC-106"], aliases=["selfdestruct", "unprotected-selfdestruct"])

_r("controlled-delegatecall", "Never lend your body to a stranger",
   "`delegatecall` runs someone else's code with your contract's storage and balance, so letting a caller choose the target "
   "hands them the keys. Modern contracts delegate only to a fixed, trusted implementation set in the `constructor` (or "
   "behind an owner-only upgrade) and never to an address taken from user input.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract FixedDelegate {
    address public immutable implementation;

    constructor(address impl) {
        require(impl.code.length > 0, "not a contract");
        implementation = impl;
    }

    function forward(bytes calldata data) external returns (bytes memory) {
        (bool ok, bytes memory out) = implementation.delegatecall(data);  // target is fixed, not chosen by the caller
        require(ok, "delegatecall failed");
        return out;
    }
}
""", swc=["SWC-112"], aliases=["delegatecall-loop", "unprotected-upgrade"])

_r("tx-origin", "Ask who knocks, not who sent them",
   "`tx.origin` is the wallet that started the whole transaction, so a malicious contract the owner visits can act in the "
   "owner's name. Modern Solidity code authorizes with `msg.sender`, the immediate caller, and keeps `tx.origin` out of access checks.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Wallet {
    address public immutable owner;

    constructor() {
        owner = msg.sender;
    }

    function pay(address payable to, uint256 amount) external {
        require(msg.sender == owner, "not owner");  // msg.sender, never tx.origin
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "transfer failed");
    }

    receive() external payable {}
}
""", swc=["SWC-115"], aliases=[])

_r("uninitialized-storage", "No pointer left pointing at slot zero",
   "Before 0.5, a local struct or array declared without a location silently pointed at storage slot zero and could overwrite "
   "the owner. Since Solidity 0.5 every reference variable must say `memory`, `storage` or `calldata`, and the compiler "
   "rejects an uninitialized storage pointer.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Registry {
    struct Entry { address who; uint256 amount; }
    address public owner = msg.sender;
    Entry[] public entries;

    function add(uint256 amount) external {
        Entry memory e = Entry({who: msg.sender, amount: amount});  // explicit data location
        entries.push(e);
    }
}
""", swc=["SWC-109"], aliases=["uninitialized-state", "uninitialized-local", "uninitialized-storage-pointer"])

_r("weak-prng", "Dice the miners cannot load",
   "Block hashes, timestamps and `block.prevrandao` are known to, or nudged by, whoever produces the block, so a lottery "
   "built on them can be predicted. Modern contracts use commit-reveal schemes or a verifiable randomness oracle and never "
   "settle money on a value the block producer controls.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

// Commit-reveal: players commit a hash first and reveal later, so no one can see or steer the outcome in one block.
contract CommitReveal {
    mapping(address => bytes32) public commits;
    mapping(address => uint256) public revealedAt;

    function commit(bytes32 hash) external {
        require(commits[msg.sender] == bytes32(0), "already committed");
        commits[msg.sender] = hash;
    }

    function reveal(uint256 secret, bytes32 salt) external returns (uint256 roll) {
        require(commits[msg.sender] == keccak256(abi.encodePacked(secret, salt, msg.sender)), "bad reveal");
        delete commits[msg.sender];
        revealedAt[msg.sender] = block.number;
        roll = uint256(keccak256(abi.encodePacked(secret, salt))) % 100;
    }
}
""", swc=["SWC-120"], aliases=["timestamp", "block-timestamp", "bad-randomness"])

_r("constructor-name", "A birth rite no one can repeat",
   "Before 0.4.22 a constructor was a function named like the contract, so renaming the contract and forgetting the function "
   "left a public function anyone could call to crown themselves owner. Since 0.4.22 the `constructor` keyword runs exactly "
   "once at deployment, since 0.5 the old style no longer compiles, and every privileged function carries an `onlyOwner` guard.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Pyramid {
    address private creator;
    uint256 private collectedFees;

    constructor() {           // runs once, at deployment; no one can call it again
        creator = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == creator, "not owner");
        _;
    }

    receive() external payable {
        collectedFees += msg.value;
    }

    function collectFees() external onlyOwner {
        uint256 amount = collectedFees;
        collectedFees = 0;
        (bool ok, ) = payable(creator).call{value: amount}("");
        require(ok, "transfer failed");
    }

    function changeOwner(address newOwner) external onlyOwner {
        require(newOwner != address(0), "zero owner");
        creator = newOwner;
    }
}
""", swc=["SWC-118"], aliases=["constructor-name-mismatch", "wrong-constructor-name", "incorrect-constructor-name",
                              "missing-constructor", "constructor-mismatch", "unprotected-initializer"])

_r("locked-ether", "Every coin has a way out",
   "A contract that accepts ether but has no function that can send it keeps that ether forever. Modern contracts that are "
   "`payable` always ship a withdraw path, guarded by an owner check, and refuse ether they were never meant to hold.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Till {
    address public immutable owner;

    constructor() {
        owner = msg.sender;
    }

    receive() external payable {}

    function withdraw(address payable to, uint256 amount) external {
        require(msg.sender == owner, "not owner");
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "transfer failed");
    }
}
""", swc=[], aliases=[])

_r("arbitrary-send-eth", "Only the owed may be paid",
   "A function that sends ether to an address any caller chooses lets strangers empty the contract. Modern contracts pay only "
   "amounts recorded for `msg.sender`, after an access check, using `call` with a checked return.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Escrow {
    mapping(address => uint256) public owed;

    function fund(address beneficiary) external payable {
        owed[beneficiary] += msg.value;
    }

    function release() external {
        uint256 amount = owed[msg.sender];   // the caller can only take what is recorded for the caller
        owed[msg.sender] = 0;
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "transfer failed");
    }
}
""", swc=["SWC-105"], aliases=["unprotected-ether-withdrawal"])

_r("integer-overflow", "Numbers that cannot wrap",
   "Before 0.8, `uint` arithmetic wrapped around silently, so a balance could underflow to an enormous number. Since "
   "Solidity 0.8.0 every `+`, `-` and `*` is checked and reverts on overflow, without SafeMath.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Ledger {
    mapping(address => uint256) public balanceOf;

    function transfer(address to, uint256 amount) external {
        balanceOf[msg.sender] -= amount;  // reverts on underflow since 0.8.0
        balanceOf[to] += amount;          // reverts on overflow
    }
}
""", swc=["SWC-101"], aliases=["overflow", "underflow", "integer-underflow", "arithmetic"])

_r("msg-value-loop", "Count the coin once",
   "Reading `msg.value` inside a loop counts the same ether once per iteration, so one payment can buy many shares. Modern "
   "contracts read it once, compute the total the loop needs, and require the two to match.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Batch {
    mapping(address => uint256) public credit;

    function payMany(address[] calldata to, uint256 each) external payable {
        require(msg.value == each * to.length, "wrong total");  // msg.value checked once, outside the loop
        for (uint256 i = 0; i < to.length; i++) {
            credit[to[i]] += each;
        }
    }
}
""", swc=[], aliases=[])

_r("incorrect-equality", "Never wait for an exact balance",
   "Anyone can force ether into a contract, so a rule like `balance == target` can be broken from outside. Modern contracts "
   "track deposits in their own variable and compare with `>=`.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Goal {
    uint256 public immutable target;
    uint256 public raised;

    constructor(uint256 t) {
        target = t;
    }

    function give() external payable {
        raised += msg.value;  // own bookkeeping, not address(this).balance
    }

    function reached() external view returns (bool) {
        return raised >= target;
    }
}
""", swc=["SWC-132"], aliases=["strict-equality"])

_r("shadowing-state", "One name, one variable",
   "When a child contract redeclares a parent's state variable, the two names point at different storage and checks read the "
   "wrong one. Solidity 0.6 and later reject state-variable shadowing at compile time.",
   """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.38;

contract Owned {
    address public owner = msg.sender;
}

contract Child is Owned {
    // no second `owner` here: the compiler would reject it
    function isOwner(address who) external view returns (bool) {
        return who == owner;
    }
}
""", swc=["SWC-119"], aliases=["shadowing-abstract", "shadowing-local"])

# Names the model may map to the ghost's own identifiers (everything else in a recipe stays as written),
# and the patterns that make a snippet show the cure: `must` regexes have to match, `must_not` must not.
_META = {
    "reentrancy-eth": (["Vault", "balances", "deposit", "withdraw"],
                       [r"modifier nonReentrant", r"\)\s*external\s+nonReentrant", r"\]\s*=\s*0;[\s\S]*\.call\{value:", r"require\(ok"],
                       [r"\.call\{value:[\s\S]*\]\s*=\s*0;\s*\n\s*\(bool"]),
    "unchecked-lowlevel": (["Payouts", "owed", "credit", "claim"], [r"\(bool ok, \) = ", r"require\(ok"], [r"\.send\(", r"\.transfer\("]),
    "suicidal": (["Guarded", "owner", "retire", "retired"], [r"constructor\(", r"onlyOwner"], [r"selfdestruct", r"suicide"]),
    "controlled-delegatecall": (["FixedDelegate", "implementation", "forward"], [r"immutable implementation|immutable \w+;", r"delegatecall"], [r"delegatecall\(\s*msg"]),
    "tx-origin": (["Wallet", "owner", "pay"], [r"msg\.sender == \w+"], [r"tx\.origin"]),
    "uninitialized-storage": (["Registry", "Entry", "entries", "add"], [r"memory"], []),
    "weak-prng": (["CommitReveal", "commits", "commit", "reveal", "roll", "revealedAt"], [r"keccak256"], [r"block\.(timestamp|prevrandao|difficulty)\s*%", r"blockhash\("]),
    "constructor-name": (["Pyramid", "creator", "collectedFees", "collectFees", "changeOwner"],
                         [r"constructor\(\)", r"function \w+\([^)]*\) external onlyOwner"], []),
    "locked-ether": (["Till", "owner", "withdraw"], [r"\.call\{value:", r"require\(msg\.sender == "], []),
    "arbitrary-send-eth": (["Escrow", "owed", "fund", "release"], [r"owed\[msg\.sender\]|\w+\[msg\.sender\] = 0"], []),
    "integer-overflow": (["Ledger", "balanceOf", "transfer"], [r"0\.8\.38"], [r"unchecked\s*\{"]),
    "msg-value-loop": (["Batch", "credit", "payMany"], [r"require\(msg\.value == "], []),
    "incorrect-equality": (["Goal", "target", "raised", "give", "reached"], [r">= \w+"], [r"== address\(this\)\.balance", r"balance ==" ]),
    "shadowing-state": (["Owned", "Child", "owner", "isOwner"], [r"is \w+"], []),
}
for _k, (_ren, _must, _not) in _META.items():
    R[_k]["renamable"], R[_k]["must"], R[_k]["must_not"] = _ren, _must, _not
# Wounds the compiler itself now refuses or prevents (the rest are coding habits shown in 0.8.38 code)
for _k in R:
    R[_k]["compiler_enforced"] = _k in ("constructor-name", "integer-overflow", "uninitialized-storage", "shadowing-state")

_INDEX: dict[str, str] = {}
for k, v in R.items():
    _INDEX[k] = k
    for a in v["aliases"]:
        _INDEX[a] = k
    for s in v["swc"]:
        _INDEX[s.lower()] = k


def recipe_for(check: str | None = None, swc: str | None = None, text: str = "") -> dict | None:
    """Find the recipe for a wound check (Slither check name, alias or SWC id). `text` is a last-resort keyword hint."""
    for key in (check, swc):
        if key and key.lower() in _INDEX:
            return R[_INDEX[key.lower()]]
    t = (text or "").lower()
    for word, key in (("reentran", "reentrancy-eth"), ("constructor", "constructor-name"), ("selfdestruct", "suicidal"),
                      ("delegatecall", "controlled-delegatecall"), ("tx.origin", "tx-origin"), ("overflow", "integer-overflow"),
                      ("underflow", "integer-overflow"), ("random", "weak-prng"), ("send(", "unchecked-lowlevel"),
                      ("gas stipend", "unchecked-lowlevel"), ("unchecked", "unchecked-lowlevel")):
        if word in t:
            return R[key]
    return None


_SOL_WORDS = set("""abstract address after alias anonymous apply as assembly auto bool break byte bytes calldata case catch constant
constructor continue contract copyof default define delete do else emit enum error event external fallback false final for function
gwei hex if immutable implements import in indexed inline interface internal is let library macro mapping match memory modifier
mutable new null of override partial payable pragma private promise public pure receive reference relocatable return returns sealed
sizeof solidity static storage string struct super supports switch this throw true try type typedef typeof uint uint256 int unchecked
using var view virtual wei while ether msg block tx now require revert assert selfdestruct suicide""".split())


def _strip_strings(code: str):
    """Split code into (is_string_or_comment, text) parts so renames never touch literals or comments."""
    return re.split(r'("(?:[^"\\\\]|\\\\.)*"|//[^\n]*)', code)


_DECL = {"contract": r"\b(?:contract|library|interface)\s+([A-Za-z_]\w*)", "function": r"\bfunction\s+([A-Za-z_]\w*)",
         "modifier": r"\bmodifier\s+([A-Za-z_]\w*)", "struct": r"\bstruct\s+([A-Za-z_]\w*)",
         "variable": r"^\s*(?:uint\d*|int\d*|address|bool|bytes\d*|string|mapping\s*\([^;]*?\)|[A-Z]\w*(?:\[\])?)\s+"
                     r"(?:public\s+|private\s+|internal\s+|constant\s+|immutable\s+)*([A-Za-z_]\w*)\s*[;=]"}


# Words an old name must contain (as a camelCase word prefix) to take a recipe name's place, besides the recipe name's own words.
SYNONYMS = {
    "withdraw": ["withdraw", "pay", "refund", "split", "cash", "redeem"], "deposit": ["deposit", "receive", "fund", "contribute", "buy", "create"],
    "balances": ["balance", "credit", "deposit", "share", "token"], "owed": ["owed", "owe", "pending", "compensation", "balance", "refund"],
    "credit": ["credit", "owe", "record", "add"], "claim": ["claim", "withdraw", "collect", "redeem"],
    "collectFees": ["collect", "fee", "withdraw", "sweep"], "collectedFees": ["fee", "collected", "commission"],
    "changeOwner": ["owner", "transfer"], "creator": ["creator", "owner", "admin", "wizard"],
    "give": ["give", "contribute", "fund", "deposit", "increase"], "reached": ["reach", "goal", "target", "equal", "transferred"],
    "target": ["target", "goal", "amount", "value"], "raised": ["raised", "balance", "total", "paid", "transferred"],
    "retire": ["retire", "kill", "close", "destroy", "shutdown", "end"], "retired": ["retired", "killed", "closed", "dead"],
    "pay": ["pay", "send", "transfer", "execute"], "owner": ["owner", "creator", "admin", "wizard"],
    "forward": ["forward", "execute", "call", "delegate"], "implementation": ["implementation", "target", "logic", "lib"],
    "release": ["release", "withdraw", "pay", "claim"], "fund": ["fund", "deposit", "contribute"],
    "commit": ["commit", "bet", "play"], "reveal": ["reveal", "draw", "settle", "roll"], "roll": ["roll", "random", "winner", "result"],
}


_GENERIC = {"change", "set", "get", "update", "new", "is", "has", "do", "make", "all", "the", "for", "to", "of"}


def _words(name: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", name)]


def same_job(src: str, dst: str) -> bool:
    """A conservative name check: the old name must share a word with the recipe name or one of its synonyms."""
    stems = {w for w in _words(src) if w not in _GENERIC} | set(SYNONYMS.get(src, []))
    return any(w.startswith(st) or st.startswith(w) for w in _words(dst) for st in stems if len(st) >= 3 and len(w) >= 3)


def roles(code: str) -> dict[str, str]:
    """Identifier -> role (contract, function, modifier, struct, variable) for declarations in a piece of Solidity.
    Variables are declarations at the start of a line with no parentheses before the name (good enough for state variables;
    a local declared the same way also counts, which is why the role check is a guard, not a proof)."""
    out: dict[str, str] = {}
    for role, rx in _DECL.items():
        for n in re.findall(rx, code, re.M):
            out.setdefault(n, role)
    return out


def arity(code: str) -> dict[str, int]:
    """Function name -> number of parameters, for declarations in a piece of Solidity."""
    return {n: len([a for a in args.split(",") if a.strip()]) for n, args in re.findall(r"\bfunction\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", code)}


def apply_renames(recipe: dict, renames: dict[str, str], known: set[str], forbidden: set[str] = frozenset(),
                  old_roles: dict[str, str] | None = None, old_arity: dict[str, int] | None = None) -> tuple[str, list[str]]:
    """Rename recipe identifiers to the ghost's own names. Returns (code, problems). Code only, deterministic.

    A rename is allowed when its source is in the recipe's renamable list, its target is a plain identifier that appears in
    the ghost's source (`known`), is not a Solidity keyword, is not forbidden (the old constructor's name), and no two
    recipe names map to the same target."""
    problems, ok = [], {}
    rec_roles = roles(recipe["code"])
    for src, dst in (renames or {}).items():
        if src == dst:
            continue
        if src not in recipe["renamable"]:
            problems.append(f"{src} is not a renamable name in the recipe"); continue
        if not re.fullmatch(r"[A-Za-z_]\w{0,40}", dst or ""):
            problems.append(f"{dst!r} is not an identifier"); continue
        if dst in forbidden:
            problems.append(f"{dst} is the old misnamed constructor; it must not come back"); continue
        if dst.lower() in _SOL_WORDS:
            problems.append(f"{dst} is a Solidity keyword"); continue
        if dst not in known:
            problems.append(f"{dst} does not appear in the old contract"); continue
        if src in known:
            problems.append(f"{src} already exists in the old contract; it keeps its own name"); continue
        if old_roles is not None and old_roles.get(dst) and rec_roles.get(src) and old_roles[dst] != rec_roles[src]:
            problems.append(f"{dst} is a {old_roles[dst]} in the old contract but {src} is a {rec_roles[src]}"); continue
        rec_arity = arity(recipe["code"])
        if old_arity is not None and src in rec_arity and dst in old_arity and rec_arity[src] != old_arity[dst]:
            problems.append(f"{dst} takes {old_arity[dst]} argument(s) in the old contract but {src} takes {rec_arity[src]}"); continue
        if rec_roles.get(src) in ("function", "variable") and not same_job(src, dst):
            problems.append(f"{dst} does not look like it does the job of {src}"); continue
        if dst in ok.values() or (dst in recipe["renamable"] and dst not in renames):
            problems.append(f"{dst} would collide with another name"); continue
        ok[src] = dst
    parts = _strip_strings(recipe["code"])
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"\b(" + "|".join(map(re.escape, ok)) + r")\b", lambda m: ok[m.group(1)], parts[i]) if ok else parts[i]
    return "".join(parts), problems


def meaning_problems(recipe: dict, code: str) -> list[str]:
    """Patterns that make the snippet show the cure (and nothing that undoes it)."""
    out = [f"missing pattern {m!r}" for m in recipe.get("must", []) if not re.search(m, code)]
    bare = re.sub(r"//[^\n]*", "", code)
    out += [f"forbidden pattern {m!r}" for m in recipe.get("must_not", []) if re.search(m, bare)]
    return out
