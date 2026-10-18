"""`rcparts` CLI. Every command prints exactly one JSON object on stdout.

Exit 0 for every handled outcome (including `ok: false`), 2 for a malformed command line,
1 for a crash (still as JSON). `reply` is the text to send to the member verbatim.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import db, demo, deposit, matcher
from .config import MATCH_SCOPES, Settings
from .i18n import STORE_LABEL, describe, money, t
from .listing import KINDS, normalize_part_number, normalize_phone, validate_listing
from .notify import send_dm
from .quote import compute_quote, to_grams
from .replies import eligible_for_order, order_summary, quote_reply


def strip_json_fence(text: str) -> str:
    """Models often wrap JSON in ```json fences or prefix a bare "json" word."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        t = t.rsplit("```", 1)[0]
    t = t.strip()
    if t.lower().startswith("json") and not t.startswith("{"):
        t = t[4:].strip()
    return t
from .store import STORE_NAME, StoreClient, StoreError, pick_best

ACT_SEND = "Send `reply` to the member as-is. Do not add prices, totals or part details of your own."


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str))


def out(reply: str = "", action: str = ACT_SEND, ok: bool = True, **data) -> dict:
    return {"ok": ok, "reply": reply, "action": action, **data}


def _listing_view(row: dict) -> dict:
    keep = ("id", "club_id", "member_id", "kind", "brand", "chassis", "part_number", "description", "condition",
            "price_usd", "qty", "status", "closed_reason", "created_at", "member_name", "member_phone",
            "club_name")
    return {k: row[k] for k in keep if k in row}


def sender_from_env(env=None) -> str:
    """Hermes sets HERMES_SESSION_USER_ID (e.g. 5939...@s.whatsapp.net) and HERMES_SESSION_KEY
    (agent:<profile>:whatsapp:dm:<phone>) for the turn; use them when the model omits --phone."""
    env = os.environ if env is None else env
    uid = env.get("HERMES_SESSION_USER_ID", "")
    if "@" in uid:
        return normalize_phone(uid.split("@", 1)[0])
    m = re.search(r":dm:(\d{6,16})$", env.get("HERMES_SESSION_KEY", ""))
    return m.group(1) if m else ""


def _member_or_reply(conn, s: Settings, phone: str):
    if not normalize_phone(phone):
        return None, out(t(s.reply_lang, "unknown_sender"), ok=False, error="unknown_sender",
                         action="Call again with --phone <digits>: the sender's number is the digits before "
                                "@s.whatsapp.net in the session's user_id. Never look it up in the database.")
    member = db.get_member(conn, normalize_phone(phone))
    if member:
        return member, None
    return None, out(t(s.reply_lang, "not_member"), ok=False, error="not_member",
                     action="Send `reply` to the member as-is. Nothing was saved.")


def _not_maintainer(s: Settings) -> dict:
    return out(t(s.reply_lang, "not_maintainer"), ok=False, error="not_maintainer",
               action="Send `reply` as-is. Only the maintainer can run this; do not retry for this sender.")


def _maintainer_check(a, s: Settings) -> dict | None:
    """Maintainer-only commands: the effective sender (the Hermes session sender, or --phone from the
    plain CLI) must be MAINTAINER_PHONE. Returns a refusal, or None when allowed."""
    phone = normalize_phone(getattr(a, "phone", None) or sender_from_env())
    if not s.maintainer_phone or phone != s.maintainer_phone:
        return _not_maintainer(s)
    return None


def _session_guard(s: Settings) -> dict | None:
    """Admin commands without --phone (db reset, demo data): from the plain CLI they run as-is; inside
    a Hermes turn only the maintainer may trigger them."""
    sender = sender_from_env()
    if sender and sender != s.maintainer_phone:
        return _not_maintainer(s)
    return None


def _club_suffix(lang: str, row: dict, own_club_id) -> str:
    """" (de Cuenca Touring)" when the other member is in another club, else ""."""
    if row.get("club_id") is not None and row.get("club_id") != own_club_id and row.get("club_name"):
        return t(lang, "from_club", club=row["club_name"])
    return ""


# --- db -------------------------------------------------------------------------

def cmd_db_init(a, s):
    with db.connect(s.database_url) as conn:
        trgm = db.init_schema(conn)
    return out(action="Schema is ready. Nothing to send.", **trgm)


def cmd_db_reset(a, s):
    refusal = _session_guard(s)
    if refusal:
        return refusal
    if not a.yes:
        return out(ok=False, error="confirm_required", tables=db.schema_tables(),
                   action="This drops every rcparts table (and only those). Re-run with --yes to confirm.")
    with db.connect(s.database_url) as conn:
        info = db.reset_schema(conn)
    return out(action="Schema dropped and recreated. Nothing to send.", **info)


def cmd_db_check(a, s):
    with db.connect(s.database_url) as conn:
        info = db.check(conn)
    return out(action="Report the database status to the maintainer.", **info)


# --- clubs and members ------------------------------------------------------------

def cmd_club_add(a, s):
    with db.connect(s.database_url) as conn:
        club = db.add_club(conn, a.name.strip(), a.country.strip(), a.city.strip(), a.jid)
    return out(t(s.reply_lang, "club_added", id=club["id"], name=club["name"]), club=club)


def cmd_club_list(a, s):
    with db.connect(s.database_url) as conn:
        return out(action="Use the data; nothing to send unless asked.", clubs=db.list_clubs(conn))


def cmd_member_add(a, s):
    phone = normalize_phone(a.phone)
    if len(phone) < 8:
        return out(ok=False, error="bad_phone", action="Ask for the phone number with country code, digits only.")
    brands = [b.strip().lower() for b in (a.brands or "").split(",") if b.strip()]
    with db.connect(s.database_url) as conn:
        club = db.get_club(conn, a.club)
        if not club:
            return out(t(s.reply_lang, "club_not_found", id=a.club), ok=False, error="club_not_found")
        member, created = db.add_member(conn, a.club, phone, a.name.strip(), a.rc_class, brands)
    key = "member_added" if created else "member_exists"
    return out(t(s.reply_lang, key, name=member["display_name"], club=member["club_name"]),
               member=member, created=created)


def cmd_member_get(a, s):
    with db.connect(s.database_url) as conn:
        member = db.get_member(conn, normalize_phone(a.phone))
    if not member:
        return out(t(s.reply_lang, "member_not_found"), ok=False, error="not_member", member=None,
                   action="This number is not registered. Tell the member to ask the club admin to register them.")
    return out(action="Use the data; nothing to send unless asked.", member=member)


def cmd_member_list(a, s):
    with db.connect(s.database_url) as conn:
        return out(action="Use the data; nothing to send unless asked.", members=db.list_members(conn, a.club))


# --- listings ----------------------------------------------------------------------

def cmd_listing_add(a, s):
    lang = s.reply_lang
    try:
        raw = json.loads(strip_json_fence(a.json))
    except json.JSONDecodeError as exc:
        return out(t(lang, "ask_listing"), ok=False, error="bad_json", missing=["listing"], detail=str(exc),
                   action="Your listing JSON was invalid. Rebuild it from the member's message and call again; "
                          "if you can't, send `reply`.")
    v = validate_listing(raw)
    with db.connect(s.database_url) as conn:
        member, refusal = _member_or_reply(conn, s, a.phone)
        if refusal:
            return refusal
        if not v.ok:
            return out(t(lang, f"ask_{v.missing[0]}"), ok=False, error="missing_fields", missing=v.missing,
                       listing=v.listing, warnings=v.warnings,
                       action="Send `reply` (one question) to the member. When they answer, rebuild the full "
                              "listing JSON with the answer and call `rcparts listing add` again.")
        row = db.insert_listing(conn, member, v.listing)
        matches = []
        for hit in matcher.find_matches(conn, row, s.match_scope):
            need, have = (row, hit) if row["kind"] == "NEED" else (hit, row)
            match_id = db.record_match(conn, need["id"], have["id"], hit["method"], hit["score"])
            if match_id is None:
                continue
            matches.append({"match_id": match_id, "method": hit["method"], "score": hit["score"],
                            "listing": _listing_view(hit), "notified": False, "notify_error": None})
        conn.commit()

        item = describe(lang, row)
        lines = [t(lang, f"saved_{row['kind']}", item=item, id=row["id"])]
        if matches:
            lines.append(t(lang, "matches_found", n=len(matches)))
            for m in matches:
                lines.append(t(lang, "match_line", item=describe(lang, m["listing"]),
                               name=m["listing"]["member_name"] + _club_suffix(lang, m["listing"], row["club_id"])))
        else:
            lines.append(t(lang, f"no_match_{row['kind']}"))

        for m in matches:
            other = m["listing"]
            need_l, have_l = (row, other) if row["kind"] == "NEED" else (other, row)
            need_phone = member["phone"] if row["kind"] == "NEED" else other["member_phone"]
            have_phone = member["phone"] if row["kind"] == "HAVE" else other["member_phone"]
            # Each DM names the other member; across clubs it also says which club they are in.
            cross = other.get("club_id") != row["club_id"]
            me = member["display_name"] + (t(lang, "from_club", club=member["club_name"]) if cross else "")
            them = other["member_name"] + _club_suffix(lang, other, row["club_id"])
            need_name = me if row["kind"] == "NEED" else them
            have_name = me if row["kind"] == "HAVE" else them
            if a.no_notify:
                m["notify_error"] = "skipped (--no-notify)"
                continue
            errors = []
            for phone, text in (
                (need_phone, t(lang, "dm_need", name=have_name, phone=have_phone, item=describe(lang, have_l))),
                (have_phone, t(lang, "dm_have", name=need_name, phone=need_phone, item=describe(lang, need_l))),
            ):
                sent, err = send_dm(s.hermes_send_cmd, phone, text)
                if not sent:
                    errors.append(f"+{phone}: {err}")
            m["notified"] = not errors
            m["notify_error"] = "; ".join(errors) or None
            db.mark_notified(conn, m["match_id"], m["notify_error"])

    if row["kind"] == "NEED" and not matches:
        action = (f"{ACT_SEND} If the member wants an import quote, run "
                  f"`rcparts quote --listing {row['id']}`.")
    elif not matches:
        action = ACT_SEND
    elif a.no_notify:
        action = f"{ACT_SEND} Match DMs were skipped (--no-notify)."
    elif any(not m["notified"] for m in matches):
        action = f"{ACT_SEND} Some match DMs were not delivered (see `notify_error`); tell the maintainer."
    else:
        action = f"{ACT_SEND} Match DMs were already sent by code; do not message the other member yourself."
    return out("\n".join(lines), action=action, listing=_listing_view(row), matches=matches,
               warnings=v.warnings, match_scope=s.match_scope)


def cmd_listing_list(a, s):
    with db.connect(s.database_url) as conn:
        rows = db.list_listings(conn, normalize_phone(a.phone) if a.phone else None, a.club,
                                a.kind, a.status)
    return out(action="Use the data; summarize only what is in `listings`.",
               listings=[_listing_view(r) for r in rows])


CLOSE_REASONS = ("sold", "unavailable", "found")


def cmd_listing_close(a, s):
    if (a.id is None) == (a.text is None):
        raise UsageError("rcparts listing close: needs exactly one of --id or --text")
    lang = s.reply_lang
    with db.connect(s.database_url) as conn:
        member = None
        if a.phone or a.text is not None:
            member, refusal = _member_or_reply(conn, s, a.phone)
            if refusal:
                return refusal
        if a.text is not None:
            own = db.active_listings_for_member(conn, member["id"])
            kind = {"sold": "HAVE", "found": "NEED"}.get(a.reason) or matcher.infer_close_kind(a.text)
            picked = matcher.pick_listings_to_close(own, a.text, kind)
            if not picked:
                lines = [t(lang, "close_none")]
                if own:
                    lines.append(t(lang, "close_open_head"))
                    lines += [t(lang, "close_line", n=i, id=l["id"], item=describe(lang, l)) for i, l in enumerate(own, 1)]
                else:
                    lines = [t(lang, "close_none_empty")]
                return out("\n".join(lines), ok=False, error="not_found",
                           open_listings=[_listing_view(l) for l in own],
                           action=f"{ACT_SEND} If the member then names one, run "
                                  f"`rcparts listing close --id <LISTING_ID>`.")
            if len(picked) > 1:
                lines = [t(lang, "close_ambiguous")]
                lines += [t(lang, "close_line", n=i, id=l["id"], item=describe(lang, l)) for i, l in enumerate(picked, 1)]
                return out("\n".join(lines), ok=False, error="ambiguous",
                           candidates=[_listing_view(l) for l in picked],
                           action="Send `reply` and ask which one. When the member answers (a number from the list "
                                  "or a #id), run `rcparts listing close --id <LISTING_ID>` with that listing's id.")
            target = picked[0]
        else:
            target = db.get_listing(conn, a.id)
            if not target or (member and target["member_id"] != member["id"]) or target["status"] == "closed":
                return out(t(lang, "listing_not_found", id=a.id), ok=False, error="not_found")
        reason = a.reason or ("sold" if target["kind"] == "HAVE" else "found")
        counterparts = db.match_counterparts(conn, target["id"])
        closed = db.close_listing(conn, target["id"], member["id"] if member else None, reason)
        if not closed:
            return out(t(lang, "listing_not_found", id=target["id"]), ok=False, error="not_found")
        db.reopen_unmatched(conn, [c["id"] for c in counterparts])

    notified = []
    reason_text = t(lang, f"close_reason_{reason}")
    for c in counterparts:
        entry = {"listing_id": c["id"], "member_name": c["member_name"], "sent": False, "error": None}
        if a.no_notify:
            entry["error"] = "skipped (--no-notify)"
        else:
            name = closed["member_name"] + _club_suffix(lang, closed, c["club_id"])
            text = t(lang, f"dm_closed_{closed['kind']}", name=name, item=describe(lang, closed), reason=reason_text)
            entry["sent"], entry["error"] = send_dm(s.hermes_send_cmd, c["member_phone"], text)
        notified.append(entry)
    lines = [t(lang, "listing_closed_text", id=closed["id"], item=describe(lang, closed), reason=reason_text)]
    if any(n["sent"] for n in notified):
        lines.append(t(lang, "close_notified", n=sum(n["sent"] for n in notified)))
    action = ACT_SEND
    if any(not n["sent"] and n["error"] and not a.no_notify for n in notified):
        action += " Some notices to matched members failed (see `notified`); tell the maintainer."
    return out("\n".join(lines), action=action, listing=_listing_view(closed), listing_id=closed["id"],
               reason=reason, notified=notified)


def cmd_search(a, s):
    lang = s.reply_lang
    scope = a.scope or s.match_scope
    with db.connect(s.database_url) as conn:
        club_id = a.club
        if club_id is None:
            member, refusal = _member_or_reply(conn, s, a.phone)
            if refusal:
                return refusal
            club_id = member["club_id"]
        rows = matcher.search(conn, club_id, a.text, a.kind, scope)
    results = [{**_listing_view(r), "method": r["method"], "score": r["score"]} for r in rows]
    if not results:
        return out(t(lang, "search_none"), results=[], scope=scope,
                   action=f"{ACT_SEND} You may offer an import quote with `rcparts quote`.")
    lines = [t(lang, "search_some")] + [
        f"• [{r['kind']}] {describe(lang, r)} — {r['member_name']}{_club_suffix(lang, r, club_id)}" for r in results]
    # No phone numbers here: search replies can land in the club group. Contact goes through match DMs.
    for r in results:
        r.pop("member_phone", None)
    return out("\n".join(lines), results=results, scope=scope,
               action=f"{ACT_SEND} To connect with the owner, the member posts a NEED; the match DM shares contacts.")


# --- quotes ------------------------------------------------------------------------

def cmd_quote(a, s):
    if a.quote_cmd == "accept":
        return cmd_quote_accept(a, s)
    if a.quote_cmd == "list":
        return cmd_quote_list(a, s)
    if (a.listing is None) == (a.query is None):
        raise UsageError("rcparts quote: needs --phone and exactly one of --listing or --query")
    lang = s.reply_lang
    with db.connect(s.database_url) as conn:
        member, refusal = _member_or_reply(conn, s, a.phone)
        if refusal:
            return refusal
        listing, qty = None, a.qty or 1
        if a.listing is not None:
            listing = db.get_listing(conn, a.listing)
            if not listing or listing["club_id"] != member["club_id"]:
                return out(t(lang, "listing_not_found", id=a.listing), ok=False, error="listing_not_found")
            qty = a.qty or listing["qty"] or 1
            queries = [listing.get("part_number"),
                       " ".join(x for x in (listing.get("chassis"), listing.get("description")) if x)]
        else:
            queries = [a.query]
        queries = list(dict.fromkeys(q.strip() for q in queries if q and q.strip()))[:2]

        client = StoreClient(s.store_crawl_delay_s)
        store_label = STORE_LABEL[STORE_NAME]
        try:
            hit, used = None, queries[0] if queries else ""
            for q in queries:
                hits = client.search(q)
                if hits:
                    hit, used = pick_best(hits, q), q
                    break
            if hit is None:
                return out(t(lang, "quote_not_found", query=used, store=store_label), ok=False, error="not_found",
                           queries=queries, action="Send `reply` as-is and wait for a part number.")
            product = client.product(hit.url)
        except StoreError as exc:
            return out(t(lang, "quote_store_down"), ok=False, error="store_unavailable", detail=str(exc))

        title = product.fulltitle or product.title or hit.title
        exact = bool(normalize_part_number(product.code or hit.code) in
                     {normalize_part_number(w) for w in used.split()} | {normalize_part_number(used)})
        if product.weight is None:
            return out(t(lang, "quote_no_weight", title=title, price=money(product.price_usd)), ok=False,
                       error="no_weight", product=product.as_json(),
                       action=f"{ACT_SEND} Tell the maintainer this product has no weight listed.")
        weight_g = to_grams(product.weight, s.weight_unit)
        m = compute_quote(product.price_usd, weight_g, s.fee_per_kg_usd, s.processing_pct, qty)
        row = db.insert_quote(conn, {
            "member_id": member["id"], "listing_id": listing["id"] if listing else None, "query": used,
            "store": STORE_NAME, "store_url": product.url or hit.url, "store_code": product.code or hit.code,
            "store_title": title, "store_price_usd": m.store_price_usd, "weight_store": product.weight * qty,
            "weight_unit": s.weight_unit, "weight_g": m.weight_g, "fee_per_kg_usd": m.fee_per_kg_usd,
            "fee_usd": m.fee_usd, "processing_pct": m.processing_pct, "processing_usd": m.processing_usd,
            "total_usd": m.total_usd, "total_with_processing_usd": m.total_with_processing_usd,
            "in_stock": product.available and product.on_stock, "stock_note": product.delivery or None,
            "qty": qty,
        })
    row["weight_store"] = product.weight  # the reply shows the per-unit weight as the store lists it
    row["fee_basis"], row["fee_rate_usd"] = s.fee_basis, s.fee_rate_usd
    reply = quote_reply(lang, row, s.us_address, exact=exact)
    action = (f"{ACT_SEND} If the member answers YES/SÍ, run "
              f"`rcparts quote accept --quote {row['id']}`.")
    if not exact:
        action += " The store had no exact code match; the member should confirm the title first."
    return out(reply, action=action, quote=row, math=m.as_json(), exact_match=exact,
               store_product=product.as_json(), weight_unit_assumed=s.weight_unit)


def cmd_quote_accept(a, s):
    if a.quote is None:
        raise UsageError("rcparts quote accept: needs --phone and --quote")
    lang = s.reply_lang
    with db.connect(s.database_url) as conn:
        member, refusal = _member_or_reply(conn, s, a.phone)
        if refusal:
            return refusal
        row = db.accept_quote(conn, a.quote, member["id"], with_processing=not a.self_order)
    if not row:
        return out(t(lang, "quote_accept_bad", id=a.quote), ok=False, error="quote_not_pending",
                   action=f"{ACT_SEND} Offer `rcparts quote list` if they are unsure.")
    if a.self_order:
        reply = t(lang, "quote_accepted_self", title=row["store_title"], address=s.us_address,
                  fee=money(row["fee_usd"]), id=row["id"])
        return out(reply, quote=row)
    account = t(lang, "deposit_account", account=s.deposit_account) if s.deposit_account else ""
    reply = t(lang, "quote_accepted_deposit", title=row["store_title"], total=money(row["total_with_processing_usd"]),
              id=row["id"], account=account)
    return out(reply, quote=row, deposit_reference=f"RC-Q{row['id']}",
               action=f"{ACT_SEND} When this member sends a PDF receipt, run "
                      f"`rcparts deposit submit --quote {row['id']} --file <the PDF path from the message>`.")


def cmd_quote_list(a, s):
    lang = s.reply_lang
    with db.connect(s.database_url) as conn:
        member, refusal = _member_or_reply(conn, s, a.phone)
        if refusal:
            return refusal
        rows = db.list_quotes(conn, member["id"])
    if not rows:
        return out(t(lang, "quote_list_none"), quotes=[])
    lines = [t(lang, "quote_list_head")]
    for r in rows:
        total = r["total_usd"] if r["with_processing"] is False else r["total_with_processing_usd"]
        lines.append(t(lang, "quote_list_line", id=r["id"], title=r["store_title"], total=money(total),
                       status=t(lang, f"status_{r['status']}")))
    return out("\n".join(lines), quotes=rows)


# --- deposits ------------------------------------------------------------------------------

def _quote_total(q: dict) -> Decimal:
    return Decimal(str(q["total_usd"] if q.get("with_processing") is False else q["total_with_processing_usd"]))


def cmd_deposit_submit(a, s):
    lang = s.reply_lang
    with db.connect(s.database_url) as conn:
        member, refusal = _member_or_reply(conn, s, a.phone)
        if refusal:
            return refusal
        if a.quote is None:
            waiting = db.member_quotes_with_status(conn, member["id"], ["awaiting_deposit"])
            if not waiting:
                return out(t(lang, "deposit_none_awaiting"), ok=False, error="no_awaiting_quote")
            if len(waiting) > 1:
                lines = [t(lang, "deposit_ambiguous")] + [
                    t(lang, "deposit_quote_line", n=i, id=q["id"], title=q["store_title"], total=money(_quote_total(q)))
                    for i, q in enumerate(waiting, 1)]
                return out("\n".join(lines), ok=False, error="ambiguous", quotes=[q["id"] for q in waiting],
                           action="Send `reply` and ask which quote the receipt is for; then run "
                                  "`rcparts deposit submit --quote <QUOTE_ID> --file <same path>`.")
            quote = waiting[0]
        else:
            quote = db.get_quote(conn, a.quote)
            if not quote or quote["member_id"] != member["id"] or quote["status"] != "awaiting_deposit":
                return out(t(lang, "deposit_bad_quote", id=a.quote), ok=False, error="quote_not_awaiting_deposit",
                           action=f"{ACT_SEND} `rcparts quote list` shows the member's quotes and their status.")

        source = "argument"
        src = Path(a.file).expanduser() if a.file else None
        if src is None or not src.is_file():
            src = deposit.newest_cached_pdf(deposit.hermes_document_dirs(s.hermes_document_cache_dir))
            source = "hermes_cache_fallback"
        if src is None:
            return out(t(lang, "deposit_no_file"), ok=False, error="no_file",
                       action=f"{ACT_SEND} Wait for the member to send the PDF, then run this again with --file.")
        if not deposit.is_pdf(src):
            return out(t(lang, "deposit_not_pdf"), ok=False, error="not_pdf")

        stored = deposit.store_receipt(src, s.data_dir / "receipts", quote["id"])
        try:
            text = deposit.pdf_text(stored)
        except Exception as exc:  # noqa: BLE001 - an unreadable PDF still goes to the maintainer
            text = ""
            read_error = f"{type(exc).__name__}: {exc}"
        else:
            read_error = None
        expected = _quote_total(quote)
        chk = deposit.check_receipt_text(text, expected, quote["id"])
        checks = {**chk.checks(), "read_error": read_error}
        dep = db.insert_deposit(conn, {
            "quote_id": quote["id"], "member_id": member["id"], "file_path": str(stored),
            "original_name": src.name, "file_source": source, "expected_usd": expected,
            "amount_usd": chk.amount_usd, "reference": chk.reference, "receipt_date": chk.receipt_date,
            "checks": checks,
        })
        db.set_quote_status(conn, quote["id"], ["awaiting_deposit"], "deposit_submitted")
        conn.commit()

    mark = lambda ok: t(lang, "mark_ok" if ok else "mark_bad")  # noqa: E731
    lines = [
        t(lang, "deposit_maint_head", name=member["display_name"], id=quote["id"], title=quote["store_title"]),
        t(lang, "deposit_maint_amount", expected=money(expected),
          read=money(chk.amount_usd) if chk.amount_usd is not None else t(lang, "not_read"), mark=mark(chk.amount_ok)),
        t(lang, "deposit_maint_ref", id=quote["id"], found=chk.reference or t(lang, "not_read"),
          mark=mark(chk.reference_ok)),
        t(lang, "deposit_maint_date", date=chk.receipt_date or t(lang, "not_read")),
    ]
    if source != "argument":
        lines.append(t(lang, "deposit_maint_fallback"))
    lines += [t(lang, "deposit_maint_cta", id=quote["id"]), f"MEDIA:{stored}"]
    maint_text = "\n".join(lines)
    sent, err = False, None
    if a.no_notify:
        err = "skipped (--no-notify)"
    elif not s.maintainer_phone:
        err = "MAINTAINER_PHONE is not set"
    else:
        sent, err = send_dm(s.hermes_send_cmd, s.maintainer_phone, maint_text)
    action = ACT_SEND + (" The maintainer was sent the receipt by code." if sent else
                         f" The maintainer could not be notified ({err}); tell them a receipt is waiting.")
    return out(t(lang, "deposit_received", id=quote["id"]), action=action, deposit=dep, quote_id=quote["id"],
               maintainer_notified=sent, notify_error=err, maintainer_message=maint_text)


def _review(a, s, confirm: bool):
    refusal = _maintainer_check(a, s)
    if refusal:
        return refusal
    lang = s.reply_lang
    with db.connect(s.database_url) as conn:
        quote = db.get_quote(conn, a.quote)
        allowed = ["deposit_submitted", "awaiting_deposit"] if confirm else ["deposit_submitted"]
        if not quote or quote["status"] not in allowed:
            return out(t(lang, "deposit_review_bad", id=a.quote), ok=False, error="nothing_to_review",
                       quote_status=quote["status"] if quote else None)
        dep = db.latest_deposit(conn, quote["id"], "submitted")
        reason = None if confirm else (a.reason or t(lang, "deposit_reject_default"))
        if dep:
            dep = db.review_deposit(conn, dep["id"], "confirmed" if confirm else "rejected", reason)
        db.set_quote_status(conn, quote["id"], allowed, "paid" if confirm else "awaiting_deposit")
        conn.commit()
    if confirm:
        member_text = t(lang, "deposit_confirmed_member", id=quote["id"], title=quote["store_title"])
        reply = t(lang, "deposit_confirmed", id=quote["id"], name=quote["member_name"])
    else:
        member_text = t(lang, "deposit_rejected_member", id=quote["id"], reason=reason)
        reply = t(lang, "deposit_rejected", id=quote["id"], name=quote["member_name"])
    sent, err = (False, "skipped (--no-notify)") if a.no_notify else send_dm(s.hermes_send_cmd,
                                                                               quote["member_phone"], member_text)
    action = ACT_SEND + ("" if sent or a.no_notify else f" The member was not notified ({err}).")
    return out(reply, action=action, quote_id=quote["id"], status="paid" if confirm else "awaiting_deposit",
               deposit=dep, member_notified=sent, notify_error=err)


def cmd_deposit_confirm(a, s):
    return _review(a, s, confirm=True)


def cmd_deposit_reject(a, s):
    return _review(a, s, confirm=False)


def cmd_deposit_list(a, s):
    refusal = _maintainer_check(a, s)
    if refusal:
        return refusal
    lang = s.reply_lang
    with db.connect(s.database_url) as conn:
        rows = db.list_deposits(conn, a.status)
    if not rows:
        return out(t(lang, "deposit_list_none"), deposits=[])
    lines = [t(lang, "deposit_list_head")] + [
        t(lang, "deposit_list_line", quote=r["quote_id"], name=r["member_name"], expected=money(r["expected_usd"]),
          read=money(r["amount_usd"]) if r["amount_usd"] is not None else "-", ref=r["reference"] or "-",
          status=r["status"]) for r in rows]
    return out("\n".join(lines), deposits=rows, action="Show `reply` to the maintainer only.")


# --- demo data -------------------------------------------------------------------------------

def _mask(phone: str) -> str:
    return f"***{phone[-4:]}" if phone else ""


def cmd_demo_seed(a, s):
    refusal = _session_guard(s)
    if refusal:
        return refusal
    if not s.maintainer_phone:
        return out(ok=False, error="config", action="Set MAINTAINER_PHONE in .env.")
    other = next((u for u in s.allowed_users if u and u != s.maintainer_phone), "")
    if not other:
        return out(ok=False, error="config",
                   action="WHATSAPP_ALLOWED_USERS needs a second number besides MAINTAINER_PHONE.")
    catalog_path = s.data_dir / "demo_catalog.json"
    catalog, fetched = demo.load_catalog(catalog_path, a.refresh, lambda: StoreClient(s.store_crawl_delay_s))
    plan = demo.plan_listings(catalog)
    with db.connect(s.database_url) as conn:
        club_a = db.add_club(conn, **demo.CLUB_A, jid=s.group_jid or None)
        club_b = db.add_club(conn, **demo.CLUB_B, jid=None)
        owners = {}
        for key, club, phone, name, rc_class in (("A", club_a, s.maintainer_phone, "Santiago", "1/10 touring"),
                                                 ("B", club_b, other, "Socio", None)):
            m, created = db.add_member(conn, club["id"], phone, name, rc_class, ["xray"])
            owners[key] = {**m, "created": created}
        seeded = []
        for item in plan:
            v = validate_listing(item["listing"])
            row = db.insert_listing(conn, owners[item["owner"]], v.listing)
            seeded.append({"id": row["id"], "owner": owners[item["owner"]]["display_name"],
                           "club": club_a["name"] if owners[item["owner"]]["club_id"] == club_a["id"] else club_b["name"],
                           "kind": row["kind"], "part_number": row["part_number"], "description": row["description"],
                           "price_usd": row["price_usd"], "store_price_usd": item.get("store_price_usd")})
        conn.commit()
    members = [{"name": m["display_name"], "club": m["club_name"], "phone": _mask(m["phone"]),
                "created": m["created"]} for m in owners.values()]
    return out(action="Demo data seeded (no DMs sent). Show the summary to the maintainer only.",
               catalog={"path": str(catalog_path), "fetched_now": fetched, "fetched_at": catalog.get("fetched_at"),
                        "parts": {k: len(v) for k, v in catalog["chassis"].items()}},
               clubs=[{"id": c["id"], "name": c["name"], "city": c["city"], "has_group": bool(c["whatsapp_group_jid"])}
                      for c in (club_a, club_b)],
               members=members, listings=seeded, match_scope=s.match_scope,
               demo_script=demo.demo_script(catalog))


def cmd_demo_receipt(a, s):
    refusal = _session_guard(s)
    if refusal:
        return refusal
    with db.connect(s.database_url) as conn:
        quote = db.get_quote(conn, a.quote)
    if not quote:
        return out(ok=False, error="not_found", action="No such quote.")
    expected = _quote_total(quote)
    try:
        amount = Decimal(a.amount) if a.amount is not None else expected
    except InvalidOperation:
        raise UsageError("rcparts demo receipt: --amount must be a number like 17.39")
    path = Path(a.out).expanduser() if a.out else s.data_dir / "receipts" / f"demo-RC-Q{quote['id']}.pdf"
    made = deposit.make_test_receipt(path, quote["id"], amount)
    return out(action="Test receipt written (fictional bank, watermarked). Nothing to send.", file=str(made),
               quote_id=quote["id"], amount_usd=str(amount), expected_usd=str(expected),
               matches_quote=amount == expected)


# --- daily order -----------------------------------------------------------------------

def cmd_orders_daily(a, s):
    lang = s.reply_lang
    today = dt.date.today().isoformat()
    with db.connect(s.database_url) as conn:
        quotes = [q for q in db.pending_order_quotes(conn) if eligible_for_order(q)]
        if not quotes:
            return out(t(lang, "orders_none"), orders=[], sent=False,
                       action="Nothing to order today. Do not message anyone.")
        order_ids: dict[str, int] = {}
        if not a.dry_run:
            stores: dict[str, list[int]] = {}
            for q in quotes:
                stores.setdefault(q["store"], []).append(q["id"])
            for store, ids in stores.items():
                _, summary = order_summary(lang, [q for q in quotes if q["store"] == store], {}, today)
                order_ids[store] = db.create_order(conn, store, ids, json.loads(json.dumps(summary[store],
                                                                                           default=str)))["id"]
            conn.commit()
        text, summary = order_summary(lang, quotes, order_ids, today)
        sent, err = False, None
        if a.send and not a.dry_run:
            if not s.maintainer_phone:
                err = "MAINTAINER_PHONE is not set"
            else:
                sent, err = send_dm(s.hermes_send_cmd, s.maintainer_phone, text)
            if sent:
                db.mark_order_sent(conn, list(order_ids.values()))
    action = "The summary was sent to the maintainer by code." if sent else (
        "Show `reply` to the maintainer only." if not err else f"Sending failed ({err}); tell the maintainer.")
    return out(text, action=action, orders=list(summary.values()), dry_run=a.dry_run, sent=sent,
               send_error=err)


# --- store debugging -------------------------------------------------------------------------

def cmd_store_search(a, s):
    hits = StoreClient(s.store_crawl_delay_s).search(a.query)
    best = pick_best(hits, a.query)
    return out(action="Debug output; nothing to send.", hits=[h.as_json() for h in hits],
               best=best.as_json() if best else None)


def cmd_store_product(a, s):
    p = StoreClient(s.store_crawl_delay_s).product(a.url)
    return out(action="Debug output; nothing to send.", product=p.as_json())


def cmd_store_weight_check(a, s):
    client = StoreClient(s.store_crawl_delay_s)
    hits = client.search(a.code)
    best = pick_best(hits, a.code)
    if not best or normalize_part_number(best.code) != normalize_part_number(a.code):
        return out(ok=False, error="not_found", action="Code not found at the store; try another part.",
                   hits=[h.as_json() for h in hits])
    p = client.product(best.url)
    expected = Decimal(a.expected_g)
    fits = {}
    if p.weight is not None:
        # Which unit would make the store value agree with the scale (within 10%, the store rounds)?
        for unit in ("g", "kg", "lb", "oz"):
            g = to_grams(p.weight, unit)
            fits[unit] = {"grams": str(g), "within_10pct": abs(g - expected) <= expected * Decimal("0.1")}
    return out(action="Report the result to the maintainer.", code=p.code, title=p.fulltitle, url=p.url,
               store_weight=None if p.weight is None else str(p.weight), expected_g=a.expected_g,
               equal_as_grams=p.weight is not None and p.weight == expected, unit_fits=fits,
               configured_unit=s.weight_unit)


# --- parser ------------------------------------------------------------------------------

def build_parser() -> Parser:
    p = Parser(prog="rcparts", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=Parser)

    g = sub.add_parser("db").add_subparsers(dest="sub", required=True, parser_class=Parser)
    g.add_parser("init").set_defaults(fn=cmd_db_init)
    g.add_parser("check").set_defaults(fn=cmd_db_check)
    c = g.add_parser("reset", help="drop the rcparts tables (only those in sql/schema.sql) and recreate them")
    c.add_argument("--yes", action="store_true")
    c.set_defaults(fn=cmd_db_reset)

    g = sub.add_parser("club").add_subparsers(dest="sub", required=True, parser_class=Parser)
    c = g.add_parser("add")
    c.add_argument("--name", required=True)
    c.add_argument("--country", required=True)
    c.add_argument("--city", required=True)
    c.add_argument("--jid")
    c.set_defaults(fn=cmd_club_add)
    g.add_parser("list").set_defaults(fn=cmd_club_list)

    g = sub.add_parser("member").add_subparsers(dest="sub", required=True, parser_class=Parser)
    c = g.add_parser("add")
    c.add_argument("--club", type=int, required=True)
    c.add_argument("--phone")
    c.add_argument("--name", required=True)
    c.add_argument("--rc-class")
    c.add_argument("--brands", help="comma-separated")
    c.set_defaults(fn=cmd_member_add)
    c = g.add_parser("get")
    c.add_argument("--phone")
    c.set_defaults(fn=cmd_member_get)
    c = g.add_parser("list")
    c.add_argument("--club", type=int, required=True)
    c.set_defaults(fn=cmd_member_list)

    g = sub.add_parser("listing").add_subparsers(dest="sub", required=True, parser_class=Parser)
    c = g.add_parser("add")
    c.add_argument("--phone")
    c.add_argument("--json", required=True)
    c.add_argument("--no-notify", action="store_true")
    c.set_defaults(fn=cmd_listing_add)
    c = g.add_parser("list")
    c.add_argument("--phone")
    c.add_argument("--club", type=int)
    c.add_argument("--kind", type=str.upper, choices=KINDS)
    c.add_argument("--status", choices=("open", "matched", "closed"))
    c.set_defaults(fn=cmd_listing_list)
    c = g.add_parser("close")
    c.add_argument("--id", type=int)
    c.add_argument("--text", help="what the member said, e.g. 'ya vendí el alerón del X1'")
    c.add_argument("--reason", choices=CLOSE_REASONS, help="default: HAVE -> sold, NEED -> found")
    c.add_argument("--phone", help="only close it if this member owns it")
    c.add_argument("--no-notify", action="store_true")
    c.set_defaults(fn=cmd_listing_close)

    c = sub.add_parser("search")
    c.add_argument("--club", type=int, help="default: the sender's club")
    c.add_argument("--phone")
    c.add_argument("--text", required=True)
    c.add_argument("--kind", type=str.upper, choices=KINDS)
    c.add_argument("--scope", choices=MATCH_SCOPES, help="default: MATCH_SCOPE")
    c.set_defaults(fn=cmd_search)

    g = sub.add_parser("deposit").add_subparsers(dest="sub", required=True, parser_class=Parser)
    c = g.add_parser("submit")
    c.add_argument("--phone")
    c.add_argument("--quote", type=int, help="default: the sender's only quote awaiting a deposit")
    c.add_argument("--file", help="the PDF path from the message; default: newest PDF in the Hermes cache")
    c.add_argument("--no-notify", action="store_true")
    c.set_defaults(fn=cmd_deposit_submit)
    for name, fn in (("confirm", cmd_deposit_confirm), ("reject", cmd_deposit_reject)):
        c = g.add_parser(name)
        c.add_argument("--phone")
        c.add_argument("--quote", type=int, required=True)
        if name == "reject":
            c.add_argument("--reason")
        c.add_argument("--no-notify", action="store_true")
        c.set_defaults(fn=fn)
    c = g.add_parser("list")
    c.add_argument("--phone")
    c.add_argument("--status", choices=("submitted", "confirmed", "rejected"))
    c.set_defaults(fn=cmd_deposit_list)

    g = sub.add_parser("demo").add_subparsers(dest="sub", required=True, parser_class=Parser)
    c = g.add_parser("seed", help="clubs, the two allowlisted members and Xray listings from the store")
    c.add_argument("--refresh", action="store_true", help="fetch the store again instead of data/demo_catalog.json")
    c.add_argument("--no-notify", action="store_true", help="accepted for symmetry; seeding never sends DMs")
    c.set_defaults(fn=cmd_demo_seed)
    c = g.add_parser("receipt", help="fake, watermarked test receipt PDF for a quote")
    c.add_argument("--quote", type=int, required=True)
    c.add_argument("--amount")
    c.add_argument("--out")
    c.set_defaults(fn=cmd_demo_receipt)

    # `quote` runs a quote itself; `quote accept` and `quote list` are optional subcommands.
    c = sub.add_parser("quote")
    c.add_argument("--phone")
    c.add_argument("--listing", type=int)
    c.add_argument("--query")
    c.add_argument("--qty", type=int)
    qs = c.add_subparsers(dest="quote_cmd", parser_class=Parser)
    q = qs.add_parser("accept")
    q.add_argument("--phone")
    q.add_argument("--quote", type=int, required=True)
    q.add_argument("--self-order", action="store_true",
                   help="member buys it and ships to US_ADDRESS: no processing fee")
    q = qs.add_parser("list")
    q.add_argument("--phone")
    c.set_defaults(fn=cmd_quote)

    g = sub.add_parser("orders").add_subparsers(dest="sub", required=True, parser_class=Parser)
    c = g.add_parser("daily")
    c.add_argument("--send", action="store_true", help="DM the summary to MAINTAINER_PHONE")
    c.add_argument("--dry-run", action="store_true", help="preview without creating orders")
    c.set_defaults(fn=cmd_orders_daily)

    g = sub.add_parser("store").add_subparsers(dest="sub", required=True, parser_class=Parser)
    c = g.add_parser("search")
    c.add_argument("--query", required=True)
    c.set_defaults(fn=cmd_store_search)
    c = g.add_parser("product")
    c.add_argument("--url", required=True)
    c.set_defaults(fn=cmd_store_product)
    c = g.add_parser("weight-check")
    c.add_argument("--code", required=True)
    c.add_argument("--expected-g", type=int, required=True)
    c.set_defaults(fn=cmd_store_weight_check)
    return p


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        # Inside a Hermes turn the real sender is in the session env and always wins: the model
        # cannot see phone numbers and has been seen inventing them. --phone is for the maintainer's CLI.
        if hasattr(args, "phone"):
            sender = sender_from_env()
            if sender:
                args.phone = sender
        result = args.fn(args, Settings.from_env())
    except UsageError as exc:
        emit({"ok": False, "error": "usage", "detail": str(exc), "reply": "",
              "action": "The command line was malformed. Fix the flags (see `rcparts <command> --help`) and retry."})
        return 2
    except SystemExit as exc:  # --help
        return int(exc.code or 0)
    except db.ConfigError as exc:
        emit({"ok": False, "error": "config", "detail": str(exc), "reply": "",
              "action": "The service is misconfigured. Tell the member to try later and alert the maintainer."})
        return 1
    except Exception as exc:  # noqa: BLE001 - the agent needs JSON even on a crash
        emit({"ok": False, "error": "crash", "detail": f"{type(exc).__name__}: {exc}", "reply": "",
              "action": "Something broke. Tell the member to try later and alert the maintainer."})
        return 1
    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
