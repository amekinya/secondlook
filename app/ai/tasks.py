"""SecondLook model tasks. Each has a fallback so the app always answers.

- identify       Nemotron 3.5 Super VL: listing screenshot/photos (+ text) -> item facts (category, brand, labels, visible features)
- judge_recalls  Nemotron 3 Ultra: reads candidate recalls' free text (model lists, date ranges) -> applies / doesn't / unclear
- write_verdict  Nemotron 3 Ultra: plain-language summary + a polite message to the seller, from the engine's findings only
- extract_listing Tavily Extract: a public listing URL -> text (+ image URLs)
- recall_news    Tavily Search + Nemotron 3.5 Lightning: anything newer than our recall snapshot for this brand/product?
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
        "what_i_see": {"type": "string", "description": "first: say in one or two sentences what product this is and what you see"},
        "category": {"type": "string", "enum": list(C.CATEGORIES)},
        "category_confidence": {"type": "number"},
        "brand": {"type": "string"},
        "product_name": {"type": "string"},
        "model_text": {"type": "string", "description": "model numbers seen on labels or in the listing text"},
        "date_of_manufacture": {"type": "string", "description": "YYYY-MM-DD or YYYY-MM if printed; empty if not visible"},
        "printed_expiration": {"type": "string", "description": "YYYY-MM-DD or YYYY-MM if a 'do not use after' date is printed; else empty"},
        "listing_text": {"type": "string", "description": "title and description text visible in the screenshot"},
        "colors_and_prints": {"type": "string", "description": "main colors and any fabric print or pattern name visible, e.g. 'white/gray, white base' or 'grey feather print'"},
        "features": {"type": "object", "properties": {k: {"type": "string", "enum": ["yes", "no", "unknown"]} for k in FEATURES},
                     "required": FEATURES, "additionalProperties": False},
        "missing_parts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["what_i_see", "category", "category_confidence", "brand", "product_name", "model_text", "date_of_manufacture", "printed_expiration",
                 "listing_text", "colors_and_prints", "features", "missing_parts"],
    "additionalProperties": False,
}

ID_PROMPT = (
    "You are checking a second-hand baby product listing for a parent. Look at the photo(s) and any listing text.\n"
    "Identify the product type (category) from the allowed list, the brand and product name if visible or stated, any model numbers, "
    "and any printed date of manufacture or 'do not use after' date on labels.\n"
    "Category notes: inclined_sleeper is only a product sold for infant sleep with a tilted surface (rocking sleepers, nappers, Rock 'n Play-style); "
    "swings, gliders, bouncers and powered rocking seats (e.g. MamaRoo) are swing or bouncer_rocker even if a baby naps in them. "
    "A rocking or tilted bassinet is bassinet. Loungers, nests and positioners that lie on a bed or floor are lounger or in_bed_sleeper.\n"
    "Copy label dates exactly as printed into date fields as YYYY-MM-DD or YYYY-MM (e.g. 'MARCH 2015 (03/2015)' -> 2015-03).\n"
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
    "Ignore photo credits and watermarks (e.g. 'Photo: U.S. CPSC recall notice') when reading brand or text.\n"
    "Be literal: never invent brands, models or dates. Use 'unknown' when unsure. category 'other' if it isn't baby gear."
)


def normalize_image(data: bytes, max_side: int = 1280) -> tuple[bytes, str]:
    """Any upload (PNG with transparency, WebP, huge photos) -> RGB JPEG on white, longest side <= max_side.
    Transparent PNGs otherwise reach the model with undefined backgrounds, and big photos cost tokens for nothing."""
    import io

    from PIL import Image, ImageOps

    try:
        im = Image.open(io.BytesIO(data))
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        im.thumbnail((max_side, max_side))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=90)
        return out.getvalue(), "image/jpeg"
    except Exception:  # noqa: BLE001  (not an image PIL can read: send as-is and let the API decide)
        return data, "image/jpeg"


def identify(images: list[tuple[bytes, str]], listing_text: str, calls: list[CallRecord] | None = None) -> dict:
    content: list[dict[str, Any]] = [{"type": "text", "text": ID_PROMPT + (f"\n\nListing text provided:\n{listing_text[:3000]}" if listing_text else "")}]
    for data, _mime in images[:4]:
        data, mime = normalize_image(data)
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}})
    return chat_json(settings.super_vl, [{"role": "user", "content": content}], schema=ID_SCHEMA,
                     purpose="Identify the product", reasoning=False, max_tokens=1500, calls=calls)


def item_from_identify(d: dict, extra_text: str = "") -> Item:
    from app.engine.recalls import find_brand  # noqa: PLC0415
    from app.engine.textfacts import merge_text_facts, parse_any_date  # noqa: PLC0415

    feats = {k: (True if v == "yes" else False if v == "no" else None) for k, v in (d.get("features") or {}).items()}
    brand = (d.get("brand") or "").strip()
    if brand.lower().strip(". ") in {"u.s", "us", "cpsc", "u.s. cpsc", "consumer product safety commission"}:
        brand = ""  # a photo credit, not a brand
    if not brand or brand.lower() in {"unknown", "n/a", "none"}:
        brand = find_brand(" ".join([d.get("listing_text", ""), d.get("product_name", ""), extra_text]))
    item = Item(
        category=d.get("category", "other"), category_confidence=float(d.get("category_confidence") or 0),
        brand=brand, model_text=d.get("model_text", ""), product_name=d.get("product_name", ""),
        listing_text=" ".join(x for x in [d.get("listing_text", ""), extra_text] if x)[:3000],
        dom=parse_any_date(d.get("date_of_manufacture", "")), printed_expiration=parse_any_date(d.get("printed_expiration", "")),
        features={k: v for k, v in feats.items() if v is not None}, missing_parts=d.get("missing_parts", [])[:6],
        colors=(d.get("colors_and_prints") or "")[:200], looks=(d.get("what_i_see") or "")[:400],
    )
    for k in ("model_text", "product_name"):
        if getattr(item, k).strip().lower() in {"unknown", "n/a", "none", "not visible"}:
            setattr(item, k, "")
    if item.category in ("", "other") and d.get("what_i_see"):  # it described "a baby walker" but picked "other"
        from app.engine.textfacts import item_from_text  # noqa: PLC0415

        item.category = item_from_text(d["what_i_see"]).category
    if item.dom is None and d.get("what_i_see"):  # a label date the model described but didn't put in the field
        from app.engine.textfacts import item_from_text  # noqa: PLC0415

        item.dom = item_from_text(d["what_i_see"]).dom
    return merge_text_facts(item, extra_text)


JUDGE_FACTS = {
    "recall_id": {"type": "string"},
    "same_brand": {"type": "string", "enum": ["yes", "no", "unclear"]},
    "same_kind_of_product": {"type": "string", "enum": ["yes", "no", "unclear"]},
    "recall_limited_to": {"type": "string", "enum": ["nothing_more", "model_numbers", "manufacture_dates", "colors_or_prints", "named_product_line", "several"]},
    "item_detail_vs_limit": {"type": "string", "enum": ["matches", "differs", "not_shown", "not_needed"]},
    "why": {"type": "string"},
}
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"judgments": {"type": "array", "items": {"type": "object", "properties": JUDGE_FACTS,
                                                              "required": list(JUDGE_FACTS), "additionalProperties": False}}},
    "required": ["judgments"], "additionalProperties": False,
}
JUDGE_SYSTEM = (
    "You compare official product recall notices with one second-hand item. Answer each question from the recall text and the item facts only.\n"
    "- same_brand: is the item the recalled brand (or the brand in the recall's product name)?\n"
    "- same_kind_of_product: is it the same kind of product (lounger, walker, swing, car seat...)?\n"
    "- recall_limited_to: what else must match beyond brand and kind. 'nothing_more' when the notice covers all of that brand's products "
    "of this kind (e.g. 'This recall involves X-branded baby walkers', or every color it was sold in), even if it says where a model number is printed. "
    "A limit the listing states plainly counts as matching (e.g. the recall covers only models with a 3-point harness and the listing says 3-point harness; "
    "the recall names a print and the listing or photo shows that print; the recall names a product line and the listing names it). "
    "Otherwise the limit: model_numbers, manufacture_dates, colors_or_prints, named_product_line (only a named product such as 'Snuga swings'), or several.\n"
    "- item_detail_vs_limit: for that limit, does the item's model/date/print/product name match the recall ('matches'), clearly differ ('differs'), "
    "or is it not shown ('not_shown')? A missing model number is 'not_shown', never 'differs'. 'not_needed' when recall_limited_to is nothing_more.\n"
    "- product_name_words_found_in_listing (computed by code): distinctive words of the recalled product's name that the listing also uses; "
    "when they name the recalled product line, a product-line limit counts as matching.\n"
    "- why: one short sentence."
)


def judge_verdict(j: dict, item: Item | None = None) -> str:
    """The rule that turns the model's reading into a verdict (code decides, not the model).
    Code also corrects two readings a model can't justify from the item facts."""
    if item is not None:
        if not item.brand and j["same_brand"] == "no":
            j["same_brand"] = "unclear"  # we don't know the item's brand, so it can't "differ"
        if j["recall_limited_to"] == "model_numbers" and not item.model_text.strip() and j["item_detail_vs_limit"] in ("differs", "matches"):
            j["item_detail_vs_limit"] = "not_shown"  # no model number in the listing is "not shown", not "different"
        if j["recall_limited_to"] == "colors_or_prints" and j["item_detail_vs_limit"] == "differs":
            j["item_detail_vs_limit"] = "not_shown"  # colors in a seller's photo are too unreliable to clear a recall
    if j["same_brand"] == "no" or j["same_kind_of_product"] == "no":
        return "does_not_apply"
    if j["same_kind_of_product"] == "yes" and j["same_brand"] in ("yes", "unclear"):
        if j["item_detail_vs_limit"] == "differs":
            return "does_not_apply"
        if j["same_brand"] == "yes" and (j["recall_limited_to"] == "nothing_more" or j["item_detail_vs_limit"] == "matches"):
            return "applies"
        if j["same_brand"] == "unclear" and j["item_detail_vs_limit"] == "matches" and j["recall_limited_to"] in ("model_numbers", "several"):
            return "applies"  # an unbranded listing whose printed model number matches the recall
    return "unclear"


def judge_recalls(item: Item, candidates: list[dict], calls: list[CallRecord] | None = None, quick: bool = False) -> list[dict]:
    """Nemotron reads the recall notices (model lists, prints, date ranges) and answers fixed questions; judge_verdict decides."""
    if not candidates:
        return []
    facts = {"category": item.category, "brand": item.brand or "unknown", "product_name": item.product_name, "model_text": item.model_text or "none shown",
             "colors_and_prints": item.colors or "unknown", "date_of_manufacture": str(item.dom) if item.dom else "unknown",
             "listing_text": item.listing_text[:800]}
    cands = [{"recall_id": c["id"], "source": c["source"], "title": c["title"], "date": c["date"],
              "products": c.get("products", [])[:6], "models": c.get("models", [])[:20],
              "product_name_words_found_in_listing": named_words(c, item),
              "covers": c["description"][:1400], "mfg_range": f"{c.get('begin', '')}..{c.get('end', '')}" if c["source"] == "NHTSA" else ""}
             for c in candidates[:6]]
    spec = settings.ultra  # quick = Ultra with reasoning off (page scan); otherwise reasoning on (detail view)
    out = chat_json(spec, [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": f"Item: {json.dumps(facts)}\nRecall notices: {json.dumps(cands)}\nAnswer for every recall_id."}],
        schema=JUDGE_SCHEMA, purpose="Judge recall matches" + (" (quick)" if quick else ""), reasoning=not quick,
        max_tokens=1600 if quick else 6000, calls=calls)
    by_id = {c["id"]: c for c in candidates}
    return [lookalike_verdict(j | decide(j, by_id[j["recall_id"]], item), by_id[j["recall_id"]])
            for j in out.get("judgments", []) if j.get("recall_id") in by_id]


def lookalike_verdict(j: dict, cand: dict) -> dict:
    """A look-alike (found by our matcher, not by brand or model) is kept unless the notice reading rules it out on what
    the listing actually shows: a different kind of product, a model number or date that differs. A different brand name
    does NOT rule it out, because recalled products are resold under other names; the result is CAUTION, never RECALLED,
    unless the model number confirms it."""
    if cand.get("match") != "lookalike" or j["verdict"] == "applies":
        return j
    ruled_out = j["same_kind_of_product"] == "no" or j["item_detail_vs_limit"] == "differs" or \
        (j.get("decided_by") == "model number" and j["verdict"] == "does_not_apply")
    return j | {"verdict": "does_not_apply" if ruled_out else "lookalike"}


def named_words(cand: dict, item: Item) -> list[str]:
    """Distinctive words of the recalled product's name (not brand, not generic) that the listing also uses.
    Code computes this so the model doesn't overlook a product line the seller named ('Slumber & Soothe')."""
    import re as _re

    from app.engine.recalls import COMMON, GENERIC, _tokens  # noqa: PLC0415

    listing = _tokens(" ".join([item.product_name, item.listing_text]))
    brand = _tokens(" ".join([cand.get("brand", ""), item.brand]))
    words = set()
    for name in cand.get("products", [])[:6]:
        for seg in _re.split(r";|,| and ", name):
            words |= {w for w in _tokens(seg) if w not in brand and w not in GENERIC and w not in COMMON and not w.isdigit()}
    return sorted(w for w in words if w in listing)[:8]


def decide(j: dict, cand: dict, item: Item) -> dict:
    """Model numbers are compared by code; the model's reading decides only what code can't.
    - The item's model number matches the notice: applies (unless the notice also limits manufacture dates and they differ).
    - The notice lists model numbers, the item shows one, and none match: doesn't apply.
    - Otherwise the fixed-question reading decides (judge_verdict)."""
    from app.engine.recalls import _model_match, _models  # noqa: PLC0415

    mods = _models(item.model_text)
    if cand.get("source") == "CPSC" and mods:
        if any(_model_match(m, cand.get("models", []), cand.get("description", "").upper()) for m in mods):
            date_out = j["recall_limited_to"] in ("manufacture_dates", "several") and j["item_detail_vs_limit"] == "differs" and item.dom
            return {"verdict": "does_not_apply" if date_out else "applies", "decided_by": "model number"}
        if cand.get("models"):
            return {"verdict": "does_not_apply", "decided_by": "model number"}
    return {"verdict": judge_verdict(j, item), "decided_by": "notice reading"}


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
