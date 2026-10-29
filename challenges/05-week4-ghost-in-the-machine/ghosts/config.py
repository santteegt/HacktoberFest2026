from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTS_HOME", Path(__file__).resolve().parent.parent))
DATA = ROOT / "data"
CACHE = DATA / "cache"
GHOSTS_DIR = DATA / "ghosts"
UA = "eth-ghosts/0.1 (+https://github.com/santteegt/HacktoberFest2026)"

EH_BASE = "https://www.ethereumhistory.com"          # the apex host 307s here
SOURCIFY_BASE = "https://sourcify.dev/server"
BLOCKSCOUT_BASE = "https://eth.blockscout.com/api/v2"
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
RPC_URL = os.environ.get("ETH_RPC_URL", "https://ethereum-rpc.publicnode.com")
ARCHIVE_RPC_URL = os.environ.get("ETH_ARCHIVE_RPC_URL", "https://eth.drpc.org")
EH_API_KEY = os.environ.get("EH_API_KEY", "")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")

for d in (CACHE, GHOSTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
