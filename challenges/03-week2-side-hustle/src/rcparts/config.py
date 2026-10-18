"""Settings from the environment, with an optional .env in the project folder."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
WEIGHT_UNITS = {"g": Decimal("1"), "kg": Decimal("1000"), "lb": Decimal("453.59237"), "oz": Decimal("28.349523125")}
LB_PER_KG = Decimal("2.20462262185")


def load_dotenv(path: Path) -> None:
    """Minimal .env reader: KEY=VALUE lines, quotes stripped, existing env wins."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    fee_per_kg_usd: Decimal
    fee_basis: str  # "kg" or "lb": the unit the maintainer prices by; the math always runs per kg
    fee_rate_usd: Decimal  # the configured rate in that unit, for display
    processing_pct: Decimal
    us_address: str
    maintainer_phone: str
    reply_lang: str
    store_crawl_delay_s: float
    weight_unit: str
    hermes_send_cmd: str

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        if env is None:
            load_dotenv(Path(os.environ.get("RCPARTS_ENV_FILE", PROJECT_DIR / ".env")))
            env = dict(os.environ)
        lang = env.get("REPLY_LANG", "es").strip().lower() or "es"
        unit = env.get("WEIGHT_UNIT", "g").strip().lower() or "g"
        if unit not in WEIGHT_UNITS:
            raise ValueError(f"WEIGHT_UNIT must be one of {sorted(WEIGHT_UNITS)}, got {unit!r}")
        # The maintainer prices imports per pound (US carriers do); accept either unit.
        per_lb = env.get("FEE_PER_LB_USD") or env.get("FEE_PER_POUND_USD")
        if per_lb:
            fee_basis, fee_rate = "lb", Decimal(per_lb)
            fee_per_kg = fee_rate * LB_PER_KG
        else:
            fee_basis, fee_rate = "kg", Decimal(env.get("FEE_PER_KG_USD", "25") or "25")
            fee_per_kg = fee_rate
        return cls(
            database_url=env.get("DATABASE_URL") or env.get("TIGER_DATA_DB_URL") or None,
            fee_per_kg_usd=fee_per_kg,
            fee_basis=fee_basis,
            fee_rate_usd=fee_rate,
            processing_pct=Decimal(env.get("PROCESSING_PCT", "12") or "12"),
            us_address=env.get("US_ADDRESS", "").strip(),
            maintainer_phone="".join(ch for ch in env.get("MAINTAINER_PHONE", "") if ch.isdigit()),
            reply_lang=lang if lang in ("es", "en") else "es",
            store_crawl_delay_s=float(env.get("STORE_CRAWL_DELAY_S", "2") or "2"),
            weight_unit=unit,
            hermes_send_cmd=env.get("HERMES_SEND_CMD", "hermes send").strip() or "hermes send",
        )
