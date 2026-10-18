"""Member-facing text in Spanish (default) and English. Numbers are formatted here, never by the model."""

from __future__ import annotations

from decimal import Decimal

T: dict[str, dict[str, str]] = {
    "es": {
        "not_member": "Todavía no estás registrado en el club. Pídele al administrador del club que te registre y vuelve a escribir.",
        "ask_kind": "¿Esa pieza la tienes para ofrecer o la estás buscando?",
        "ask_part_number": "¿Cuál es el número de parte (por ejemplo TAM54500)? Si no lo sabes, dime la marca, el chasis y qué pieza es.",
        "ask_description": "¿Qué pieza es exactamente (por ejemplo: piñón 68T, amortiguadores delanteros)?",
        "ask_brand_or_chassis": "¿Para qué marca y chasis es la pieza (por ejemplo: Tamiya TT-02)?",
        "ask_listing": "No entendí la publicación. ¿Qué pieza tienes o buscas, con número de parte si lo sabes?",
        "saved_HAVE": "Anotado: ofreces {item}. Publicación #{id}.",
        "saved_NEED": "Anotado: buscas {item}. Publicación #{id}.",
        "matches_found": "Encontré {n} coincidencia(s) en el club; les escribí por privado a ambos:",
        "no_match_NEED": "Nadie del club lo tiene por ahora. Si quieres, te cotizo la importación desde EE. UU.",
        "no_match_HAVE": "Nadie del club lo está buscando por ahora; te aviso si alguien lo pide.",
        "match_line": "• {item} — {name}",
        "dm_need": "¡Coincidencia! {name} (+{phone}) tiene {item}. Escríbele: https://wa.me/{phone}",
        "dm_have": "¡Coincidencia! {name} (+{phone}) está buscando {item}, que tú ofreces. Escríbele: https://wa.me/{phone}",
        "cond_new": "nuevo", "cond_used": "usado", "cond_unknown": "estado sin indicar",
        "listing_closed": "Publicación #{id} cerrada.",
        "listing_not_found": "No encontré la publicación #{id}.",
        "search_none": "No encontré nada parecido en el club.",
        "search_some": "Esto encontré en el club:",
        "quote_head": "Cotización de importación ({store})",
        "quote_price": "Precio en tienda: {price} USD",
        "quote_qty": "Cantidad: {qty} × {unit} USD",
        "quote_weight": "Peso según la tienda: {weight}",
        "quote_fee": "Tarifa de importación ({grams} g × {per_kg}/kg): {fee} USD",
        "quote_total_self": "Total si lo compras tú y lo envías a \"{address}\": {total} USD",
        "quote_total_plain": "Total con importación: {total} USD",
        "quote_total_proc": "Total si lo pedimos por ti (+{pct}% de procesamiento, {proc}): {total} USD",
        "quote_stock_yes": "Stock: disponible{delivery}",
        "quote_stock_no": "Stock: agotado en la tienda por ahora",
        "quote_cta": "Responde SÍ para agregarlo al pedido de hoy (cotización #{id}).",
        "quote_not_found": "No encontré \"{query}\" en {store}. ¿Me pasas el número de parte exacto (por ejemplo TAM54500)?",
        "quote_no_weight": "Encontré {title} a {price} USD, pero la tienda no indica el peso, así que no puedo calcular la importación. El administrador te confirmará el precio.",
        "quote_store_down": "No pude consultar la tienda en este momento. Intenta de nuevo en unos minutos.",
        "quote_accepted": "Listo: {title} va en el pedido de hoy. Total: {total} USD (cotización #{id}).",
        "quote_check_title": "Ojo: no encontré el código exacto; revisa que el título corresponda a tu pieza.",
        "quote_accepted_self": "Listo: anotado {title}. Cómpralo y envíalo a \"{address}\". Tarifa de importación a pagar: {fee} USD (cotización #{id}).",
        "quote_accept_bad": "No encontré una cotización #{id} pendiente a tu nombre.",
        "quote_list_none": "No tienes cotizaciones.",
        "quote_list_head": "Tus cotizaciones:",
        "quote_list_line": "#{id} {title}: {total} USD ({status})",
        "status_quoted": "pendiente", "status_accepted": "aceptada", "status_ordered": "en pedido",
        "orders_none": "No hay cotizaciones aceptadas pendientes de pedir.",
        "orders_head": "Pedido del día {date}",
        "orders_store": "Tienda {store} (pedido #{id}):",
        "orders_item": "• {qty} × {title}: {price} USD — +{phone}",
        "orders_self": "(lo compra el miembro; solo se cobra la tarifa)",
        "orders_totals": "Subtotal tienda: {subtotal} USD · Tarifas: {fees} USD · Procesamiento: {proc} USD · Total a cobrar: {total} USD",
        "club_added": "Club #{id} {name} creado.",
        "member_added": "Bienvenido/a, {name}. Ya estás registrado en el club {club}.",
        "member_exists": "{name} ya estaba registrado.",
        "member_not_found": "No hay un miembro con ese número.",
        "club_not_found": "No existe el club #{id}.",
    },
    "en": {
        "not_member": "You are not registered in the club yet. Ask the club admin to register you, then write again.",
        "ask_kind": "Do you have this part to offer, or are you looking for it?",
        "ask_part_number": "What is the part number (for example TAM54500)? If you don't know it, tell me the brand, the chassis and which part it is.",
        "ask_description": "Which part is it exactly (for example: 68T spur gear, front shocks)?",
        "ask_brand_or_chassis": "Which brand and chassis is the part for (for example: Tamiya TT-02)?",
        "ask_listing": "I couldn't read that listing. Which part do you have or need, with the part number if you know it?",
        "saved_HAVE": "Saved: you have {item}. Listing #{id}.",
        "saved_NEED": "Saved: you need {item}. Listing #{id}.",
        "matches_found": "I found {n} match(es) in the club and messaged both of you privately:",
        "no_match_NEED": "Nobody in the club has it right now. If you want, I can quote an import from the US.",
        "no_match_HAVE": "Nobody in the club is looking for it right now; I'll tell you if someone asks.",
        "match_line": "• {item} — {name}",
        "dm_need": "Match! {name} (+{phone}) has {item}. Message them: https://wa.me/{phone}",
        "dm_have": "Match! {name} (+{phone}) is looking for {item}, which you have. Message them: https://wa.me/{phone}",
        "cond_new": "new", "cond_used": "used", "cond_unknown": "condition not stated",
        "listing_closed": "Listing #{id} closed.",
        "listing_not_found": "I couldn't find listing #{id}.",
        "search_none": "I found nothing similar in the club.",
        "search_some": "Here is what I found in the club:",
        "quote_head": "Import quote ({store})",
        "quote_price": "Store price: {price} USD",
        "quote_qty": "Quantity: {qty} × {unit} USD",
        "quote_weight": "Weight as listed by the store: {weight}",
        "quote_fee": "Import fee ({grams} g × {per_kg}/kg): {fee} USD",
        "quote_total_self": "Total if you buy it and ship it to \"{address}\": {total} USD",
        "quote_total_plain": "Total with import: {total} USD",
        "quote_total_proc": "Total if we order it for you (+{pct}% processing, {proc}): {total} USD",
        "quote_stock_yes": "Stock: available{delivery}",
        "quote_stock_no": "Stock: out of stock at the store right now",
        "quote_cta": "Reply YES to add it to today's order (quote #{id}).",
        "quote_not_found": "I couldn't find \"{query}\" at {store}. Can you send me the exact part number (for example TAM54500)?",
        "quote_no_weight": "I found {title} at {price} USD, but the store does not list its weight, so I can't compute the import. The admin will confirm the price.",
        "quote_store_down": "I couldn't reach the store right now. Please try again in a few minutes.",
        "quote_accepted": "Done: {title} is in today's order. Total: {total} USD (quote #{id}).",
        "quote_check_title": "Note: I couldn't find the exact code; check that the title is your part.",
        "quote_accepted_self": "Done: {title} is noted. Buy it and ship it to \"{address}\". Import fee to pay: {fee} USD (quote #{id}).",
        "quote_accept_bad": "I couldn't find a pending quote #{id} in your name.",
        "quote_list_none": "You have no quotes.",
        "quote_list_head": "Your quotes:",
        "quote_list_line": "#{id} {title}: {total} USD ({status})",
        "status_quoted": "pending", "status_accepted": "accepted", "status_ordered": "in an order",
        "orders_none": "There are no accepted quotes waiting to be ordered.",
        "orders_head": "Daily order {date}",
        "orders_store": "Store {store} (order #{id}):",
        "orders_item": "• {qty} × {title}: {price} USD — +{phone}",
        "orders_self": "(the member buys it; only the fee is collected)",
        "orders_totals": "Store subtotal: {subtotal} USD · Fees: {fees} USD · Processing: {proc} USD · Total to collect: {total} USD",
        "club_added": "Club #{id} {name} created.",
        "member_added": "Welcome, {name}. You are now registered in the {club} club.",
        "member_exists": "{name} was already registered.",
        "member_not_found": "There is no member with that number.",
        "club_not_found": "Club #{id} does not exist.",
    },
}

STORE_LABEL = {"michaelsrchobbies": "Michael's RC Hobbies"}


def t(lang: str, key: str, **kw) -> str:
    return T.get(lang, T["es"])[key].format(**kw)


def money(value: Decimal | str | float) -> str:
    return f"${Decimal(str(value)):,.2f}"


def grams(value: Decimal | str | float) -> str:
    d = Decimal(str(value))
    return f"{d:,.0f}" if d == d.to_integral_value() else f"{d:,.1f}"


def describe(lang: str, listing: dict) -> str:
    """One-line summary of a listing, e.g. `TAM54500 · tamiya tt02 · 68T spur gear (used, $10.00)`."""
    parts = [p for p in (listing.get("part_number"),
                         " ".join(x for x in (listing.get("brand"), listing.get("chassis")) if x),
                         listing.get("description")) if p]
    text = " · ".join(parts)
    extra = []
    if listing.get("kind") == "HAVE" and listing.get("condition"):
        extra.append(t(lang, f"cond_{listing['condition']}"))
    if listing.get("price_usd") is not None:
        extra.append(money(listing["price_usd"]))
    if (listing.get("qty") or 1) > 1:
        extra.append(f"x{listing['qty']}")
    return f"{text} ({', '.join(extra)})" if extra else text
