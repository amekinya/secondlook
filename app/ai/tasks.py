"""SecondLook model tasks. Each has a fallback so the app always answers.

- identify       Nemotron 3.5 Super VL: listing screenshot/photos (+ text) -> item facts (category, brand, labels, visible features)
- judge_recalls  Nemotron 3 Ultra: reads candidate recalls' free text (model lists, date ranges) -> applies / doesn't / unclear
- write_verdict  Nemotron 3 Ultra: plain-language summary + a polite message to the seller, from the engine's findings only
- extract_listing Tavily Extract: a public listing URL -> text (+ image URLs)
- recall_news    Tavily Search + Nemotron 3 Nano: anything newer than our recall snapshot for this brand/product?
"""
from __future__ import annotations

import base64
import json
from datetime import date
from typing import Any

from app.ai.client import CallRecord, LiveModelUnavailable, chat_json
from app.config import settings
from app.engine import catalog as C
from app.engine.assess import Item

FEATURES = ["incline_raised", "marketed_for_sleep", "drop_side", "padded_bumper", "mesh_liner", "restraint_strap", "suction_cups",
            "legs_or_stand", "snuga_headrest_present", "strap_fastener_present", "bumbo_belt_present", "single_cup_tray",
            "cord_cover_present", "weighted"]

ID_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(C.CATEGORIES)},
        "category_confidence": {"type": "number"},
        "brand": {"type": "string"},
        "product_name": {"type": "string"},
        "model_text": {"type": "string", "description": "model numbers seen on labels or in the listing text"},
        "date_of_manufacture": {"type": "string", "description": "YYYY-MM-DD or YYYY-MM if printed; empty if not visible"},
        "printed_expiration": {"type": "string", "description": "YYYY-MM-DD or YYYY-MM if a 'do not use after' date is printed; else empty"},
        "listing_text": {"type": "string", "description": "title and description text visible in the screenshot"},
        "features": {"type": "object", "properties": {k: {"type": "string", "enum": ["yes", "no", "unknown"]} for k in FEATURES},
                     "required": FEATURES, "additionalProperties": False},
        "missing_parts": {"type": "array", "items": {"type": "string"}},
        "what_i_see": {"type": "string"},
    },
    "required": ["category", "category_confidence", "brand", "product_name", "model_text", "date_of_manufacture", "printed_expiration",
                 "listing_text", "features", "missing_parts", "what_i_see"],
    "additionalProperties": False,
}

ID_PROMPT = (
    "You are checking a second-hand baby product listing for a parent. Look at the photo(s) and any listing text.\n"
    "Identify the product type (category) from the allowed list, the brand and product name if visible or stated, any model numbers, "
    "and any printed date of manufacture or 'do not use after' date on labels.\n"
    "Feature definitions (answer yes/no/unknown from what is visible or stated):\n"
    "- incline_raised: the sleep/seat surface is tilted with the head end raised more than about 10 degrees\n"
    "- marketed_for_sleep: the listing or product says sleep, nap, sleeper, overnight\n"
    "- drop_side: a crib side that slides up/down on tracks or is described as dropping\n"
    "- padded_bumper: padded fabric/braided bumpers, vinyl bumper guards or slat covers inside a crib; mesh_liner: a thin non-padded mesh liner\n"
    "- restraint_strap: a strap or harness on a lounger/nursing pillow\n- suction_cups: suction-cup feet (bath seats)\n"
    "- legs_or_stand: a sleep product stands on legs/stand rather than lying on an adult bed\n"
    "- snuga_headrest_present: a plush animal headrest/insert on a Fisher-Price Snuga-style swing\n"
    "- strap_fastener_present: a strap fastener under a 4moms MamaRoo seat; bumbo_belt_present: a restraint belt on a Bumbo-style floor seat\n"
    "- single_cup_tray: a child tray with a single cupholder on a stroller; cord_cover_present: a rigid cover on a monitor sensor-pad cord\n"
    "- weighted: described or shown as a weighted sleep product\n"
    "Be literal: never invent brands, models or dates. Use 'unknown' when unsure. category 'other' if it isn't baby gear."
)


def identify(images: list[tuple[bytes, str]], listing_text: str, calls: list[CallRecord] | None = None) -> dict:
    content: list[dict[str, Any]] = [{"type": "text", "text": ID_PROMPT + (f"\n\nListing text provided:\n{listing_text[:3000]}" if listing_text else "")}]
    for data, mime in images[:4]:
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}})
    return chat_json(settings.super_vl, [{"role": "user", "content": content}], schema=ID_SCHEMA,
                     purpose="Identify the product", reasoning=False, max_tokens=1500, calls=calls)


def _parse_date(s: str) -> date | None:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            from datetime import datetime

            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def item_from_identify(d: dict, extra_text: str = "") -> Item:
    from app.engine.recalls import find_brand  # noqa: PLC0415

    feats = {k: (True if v == "yes" else False if v == "no" else None) for k, v in (d.get("features") or {}).items()}
    brand = (d.get("brand") or "").strip()
    if not brand or brand.lower() in {"unknown", "n/a", "none"}:
        brand = find_brand(" ".join([d.get("listing_text", ""), d.get("product_name", ""), extra_text]))
    return Item(
        category=d.get("category", "other"), category_confidence=float(d.get("category_confidence") or 0),
        brand=brand, model_text=d.get("model_text", ""), product_name=d.get("product_name", ""),
        listing_text=" ".join(x for x in [d.get("listing_text", ""), extra_text] if x)[:3000],
        dom=_parse_date(d.get("date_of_manufacture", "")), printed_expiration=_parse_date(d.get("printed_expiration", "")),
        features={k: v for k, v in feats.items() if v is not None}, missing_parts=d.get("missing_parts", [])[:6],
    )


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"judgments": {"type": "array", "items": {"type": "object", "properties": {
        "recall_id": {"type": "string"}, "verdict": {"type": "string", "enum": ["applies", "does_not_apply", "unclear"]},
        "why": {"type": "string"}}, "required": ["recall_id", "verdict", "why"], "additionalProperties": False}}},
    "required": ["judgments"], "additionalProperties": False,
}


def judge_recalls(item: Item, candidates: list[dict], calls: list[CallRecord] | None = None, quick: bool = False) -> list[dict]:
    if not candidates:
        return []
    facts = {"category": item.category, "brand": item.brand, "product_name": item.product_name, "model_text": item.model_text,
             "date_of_manufacture": str(item.dom) if item.dom else "unknown", "listing_text": item.listing_text[:800]}
    cands = [{"recall_id": c["id"], "source": c["source"], "title": c["title"], "date": c["date"],
              "covers": c["description"][:1400], "mfg_range": f"{c.get('begin', '')}..{c.get('end', '')}" if c["source"] == "NHTSA" else ""}
             for c in candidates[:6]]
    spec = settings.nano if quick else settings.ultra
    out = chat_json(spec, [
        {"role": "system", "content": "You decide whether official product recalls cover a specific second-hand item. Use only the recall text and item facts. "
                                      "'applies' only if the recall text covers this brand AND this product (and model/date when the recall limits them). "
                                      "'unclear' if the deciding detail (model number, manufacture date) is missing. Otherwise 'does_not_apply'."},
        {"role": "user", "content": f"Item: {json.dumps(facts)}\nCandidate recalls: {json.dumps(cands)}"}],
        schema=JUDGE_SCHEMA, purpose="Judge recall matches" + (" (quick)" if quick else ""), reasoning=not quick,
        max_tokens=900 if quick else 4000, calls=calls)
    return out.get("judgments", [])


VERDICT_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}, "seller_message": {"type": "string"}, "safer_alternative": {"type": "string"}},
    "required": ["summary", "seller_message", "safer_alternative"], "additionalProperties": False,
}


def write_verdict(result: dict, calls: list[CallRecord] | None = None) -> dict:
    brief = {"verdict": result["label"], "category": result["category_label"], "item": {k: result["item"][k] for k in ("brand", "product_name", "model_text", "dom")},
             "reasons": [{k: r[k] for k in ("level", "title", "detail", "cite")} for r in result["reasons"]],
             "recalls": [{k: rc.get(k) for k in ("id", "title", "remedy", "match", "deaths")} for rc in result["recalls"]],
             "car_seat": result.get("car_seat"), "questions": result["questions"]}
    return chat_json(settings.ultra, [
        {"role": "system", "content": "You help a parent decide about a used baby product. Use ONLY the findings given; never add new facts, numbers or recalls. "
                                      "Be warm, direct and brief. Don't shame the seller; many don't know about recalls or bans."},
        {"role": "user", "content": f"Findings: {json.dumps(brief)}\nWrite: summary (2-3 sentences: what it is, the verdict and the single most important reason); "
                                    "seller_message (a short friendly marketplace message: either asking the key questions, or politely passing and mentioning the recall/ban with its source); "
                                    "safer_alternative (one sentence on what to look for instead, or empty)."}],
        schema=VERDICT_SCHEMA, purpose="Write verdict", reasoning=True, max_tokens=3000, calls=calls)


def write_verdict_fallback(result: dict) -> dict:
    top = result["reasons"][0]
    q = result["questions"][:2]
    if result["level"] in {"ILLEGAL_TO_SELL", "RECALLED"}:
        msg = f"Hi! Thanks for listing this. I looked it up and it appears to be covered by a {('recall' if result['level'] == 'RECALLED' else 'federal ban')} ({top['cite']}), so I'll pass. You may want to check the remedy before selling."
    else:
        msg = "Hi! I'm interested. " + " ".join(q)
    return {"summary": f"{result['category_label']}: {result['label']}. {top['title']}.", "seller_message": msg, "safer_alternative": "", "fallback": True}


def extract_listing(url: str) -> dict:
    if not settings.live_tavily:
        raise LiveModelUnavailable("TAVILY_API_KEY not set")
    from tavily import TavilyClient

    t = TavilyClient(api_key=settings.tavily_api_key)
    res = t.extract(urls=[url], include_images=True)
    r = (res.get("results") or [{}])[0]
    return {"text": (r.get("raw_content") or "")[:6000], "images": (r.get("images") or [])[:4], "failed": bool(res.get("failed_results"))}


NEWS_SCHEMA = {
    "type": "object",
    "properties": {"new_recall": {"type": "boolean"}, "headline": {"type": "string"}, "url": {"type": "string"}, "date": {"type": "string"}},
    "required": ["new_recall", "headline", "url", "date"], "additionalProperties": False,
}


def recall_news(item: Item, known_ids: list[str], calls: list[CallRecord] | None = None) -> dict:
    if not settings.live_tavily or not (item.brand or item.product_name):
        return {"checked": False}
    from tavily import TavilyClient

    t = TavilyClient(api_key=settings.tavily_api_key)
    q = f"{item.brand} {item.product_name or C.CATEGORIES.get(item.category, '')} recall".strip()
    res = t.search(q, topic="news", days=120, max_results=5)
    items = [{"title": r.get("title", ""), "url": r.get("url", ""), "date": r.get("published_date", ""), "snippet": (r.get("content") or "")[:400]}
             for r in res.get("results", [])]
    if not items:
        return {"checked": True, "new_recall": False, "query": q}
    try:
        out = chat_json(settings.nano, [{"role": "user", "content": (
            f"Product: {item.brand} {item.product_name} ({item.category}). Recalls we already know: {known_ids}. Our recall snapshot is dated {C.RULES_VERIFIED_AS_OF}.\n"
            f"Do these news results report a NEW recall or safety warning for this specific product, newer than the snapshot? Results: {json.dumps(items)}")}],
            schema=NEWS_SCHEMA, purpose="Check recall news", reasoning=False, max_tokens=600, calls=calls)
    except LiveModelUnavailable:
        return {"checked": False}
    return {"checked": True, "query": q, **out}
