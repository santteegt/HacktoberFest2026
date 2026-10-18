"""Deposit receipts: read amount, reference and date from a PDF, and make clearly fake test receipts.

The checks only flag mismatches for the maintainer; a human confirms every payment.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .quote import cents

# --- parsing -----------------------------------------------------------------------

_NUM = r"\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?"
# "Monto: $17.39", "Valor USD 17,39", "Total: 17.39 USD", "Amount US$ 1,234.56"
_LABELED = re.compile(
    rf"(?:monto|valor|importe|total|amount|cantidad)\b[^\d$]{{0,25}}(?:USD|US\$|\$)?\s*({_NUM})", re.I)
_CURRENCY = re.compile(rf"(?:USD|US\$|\$)\s*({_NUM})|({_NUM})\s*(?:USD|dólares|dolares)\b", re.I)
_REFERENCE = re.compile(r"\bRC\s*[-_.]?\s*Q\s*[-_.]?\s*(\d{1,9})\b", re.I)
_MONTHS = {m: i for i, m in enumerate(
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1)}
_MONTHS.update({m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)})
_DATE_ISO = re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})(?!\d)")
_DATE_DMY = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4}|\d{2})(?!\d)")
_DATE_WORDS = re.compile(r"\b(\d{1,2})\s+(?:de\s+)?([A-Za-zéÉ]+)\s+(?:de\s+|del\s+)?(20\d{2})\b", re.I)


def parse_amount(raw: str) -> Decimal | None:
    """`17.39`, `17,39`, `1.234,56`, `1,234.56`, `1 234,56` -> Decimal. The last separator followed by
    one or two digits is the decimal mark; a separator followed by three digits groups thousands."""
    s = raw.strip().replace(" ", "").replace(" ", "")
    if not s:
        return None
    last = max(s.rfind("."), s.rfind(","))
    if last >= 0 and len(s) - last - 1 in (1, 2):
        whole, frac = s[:last], s[last + 1:]
    else:
        whole, frac = s, ""
    whole = whole.replace(".", "").replace(",", "")
    try:
        return cents(Decimal(f"{whole}.{frac or '0'}"))
    except InvalidOperation:
        return None


def amount_candidates(text: str) -> list[Decimal]:
    """Labeled amounts first ("Monto: ..."), then any currency-marked amount, in document order."""
    found: list[Decimal] = []
    for m in _LABELED.finditer(text):
        v = parse_amount(m.group(1))
        if v is not None and v not in found:
            found.append(v)
    for m in _CURRENCY.finditer(text):
        v = parse_amount(m.group(1) or m.group(2))
        if v is not None and v not in found:
            found.append(v)
    return found


def parse_reference(text: str) -> str | None:
    m = _REFERENCE.search(text)
    return f"RC-Q{int(m.group(1))}" if m else None


def parse_date(text: str) -> str | None:
    """First date in the text as ISO `YYYY-MM-DD` (day first for `dd/mm/yyyy`, as in Ecuador)."""
    candidates = []
    for m in _DATE_ISO.finditer(text):
        candidates.append((m.start(), int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for m in _DATE_DMY.finditer(text):
        y = int(m.group(3))
        candidates.append((m.start(), y + 2000 if y < 100 else y, int(m.group(2)), int(m.group(1))))
    for m in _DATE_WORDS.finditer(text):
        month = _MONTHS.get(m.group(2).lower())
        if month:
            candidates.append((m.start(), int(m.group(3)), month, int(m.group(1))))
    for _, y, mo, d in sorted(candidates):
        try:
            return dt.date(y, mo, d).isoformat()
        except ValueError:
            continue
    return None


@dataclass
class ReceiptCheck:
    amount_usd: Decimal | None
    reference: str | None
    receipt_date: str | None
    amount_ok: bool
    reference_ok: bool
    candidates: list[str] = field(default_factory=list)
    text_chars: int = 0

    def checks(self) -> dict:
        return {"amount_ok": self.amount_ok, "reference_ok": self.reference_ok,
                "amount_candidates": self.candidates, "text_chars": self.text_chars,
                "date_found": self.receipt_date is not None}


def check_receipt_text(text: str, expected_usd: Decimal, quote_id: int) -> ReceiptCheck:
    cands = amount_candidates(text)
    expected = cents(Decimal(str(expected_usd)))
    amount = cands[0] if cands else None
    ref = parse_reference(text)
    return ReceiptCheck(
        amount_usd=amount, reference=ref, receipt_date=parse_date(text),
        amount_ok=amount == expected, reference_ok=ref == f"RC-Q{quote_id}",
        candidates=[str(c) for c in cands[:5]], text_chars=len(text),
    )


# --- files ---------------------------------------------------------------------------

def is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def store_receipt(src: Path, receipts_dir: Path, quote_id: int) -> Path:
    """Copy into data/receipts/ under a name we choose (never the sender's file name)."""
    receipts_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = receipts_dir / f"RC-Q{quote_id}-{stamp}.pdf"
    n = 1
    while dest.exists():
        n += 1
        dest = receipts_dir / f"RC-Q{quote_id}-{stamp}-{n}.pdf"
    shutil.copyfile(src, dest)
    return dest.resolve()


def hermes_document_dirs(configured: str = "") -> list[Path]:
    """Where the Hermes WhatsApp bridge saves inbound documents (doc_<12 hex>_<original name>).
    The gateway passes HERMES_DOCUMENT_CACHE_DIR to the bridge; for a profile it resolves to
    <HERMES_HOME>/cache/documents (legacy <HERMES_HOME>/document_cache when that one has files)."""
    dirs = []
    if configured:
        dirs.append(Path(configured).expanduser())
    homes = [os.environ.get("HERMES_HOME", ""), "~/.hermes/profiles/rc-parts", "~/.hermes"]
    for home in filter(None, homes):
        h = Path(home).expanduser()
        dirs += [h / "cache" / "documents", h / "document_cache"]
    return list(dict.fromkeys(dirs))


def newest_cached_pdf(dirs: list[Path], max_age_s: float = 900) -> Path | None:
    """Newest PDF received in the last `max_age_s` seconds. The cache does not record the sender,
    so this is a fallback for a missing path, and the maintainer is told it was used."""
    now, best = time.time(), None
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.glob("*.pdf"):
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            if now - mtime <= max_age_s and (best is None or mtime > best[0]):
                best = (mtime, p)
    return best[1] if best else None


# --- fake test receipt ------------------------------------------------------------------

FAKE_BANK = "Banco de Prueba S.A. — entidad ficticia"
WATERMARK = "COMPROBANTE DE PRUEBA – NO VÁLIDO"


def make_test_receipt(out: Path, quote_id: int, amount_usd: Decimal, when: dt.datetime | None = None) -> Path:
    """A text-based PDF (pypdf can read it back) from a fictional bank, watermarked as a test.
    No real bank names, logos, account numbers or people."""
    from reportlab.lib.colors import Color, black
    from reportlab.lib.pagesizes import A5
    from reportlab.pdfgen import canvas

    when = when or dt.datetime.now()
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = A5
    c = canvas.Canvas(str(out), pagesize=A5)
    c.setTitle(f"Comprobante de prueba RC-Q{quote_id}")
    c.setAuthor("rcparts demo (ficticio)")

    c.setFont("Helvetica-Bold", 13)
    c.drawString(36, h - 50, FAKE_BANK)
    c.setFont("Helvetica", 9)
    c.drawString(36, h - 64, "Documento generado para pruebas del bot PartsPaddock.")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(36, h - 100, "Comprobante de depósito")
    rows = [
        ("Fecha", when.strftime("%d/%m/%Y %H:%M")),
        ("Monto", f"USD {Decimal(str(amount_usd)):.2f}"),
        ("Referencia", f"RC-Q{quote_id}"),
        ("Cuenta destino", "XXXX-0000 (demo)"),
        ("Ordenante", "Socio (demo)"),
        ("Estado", "Prueba, sin valor"),
    ]
    y = h - 130
    for label, value in rows:
        c.setFont("Helvetica", 10)
        c.drawString(36, y, f"{label}:")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(140, y, value)
        y -= 20

    c.saveState()
    c.setFillColor(Color(0.85, 0.1, 0.1, alpha=0.25))
    c.setFont("Helvetica-Bold", 22)
    c.translate(w / 2, h / 2 - 40)
    c.rotate(40)
    c.drawCentredString(0, 0, WATERMARK)
    c.restoreState()

    c.setFillColor(black)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(36, 40, f"{WATERMARK}. {FAKE_BANK}.")
    c.showPage()
    c.save()
    return out.resolve()
