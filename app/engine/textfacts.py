"""Facts read from listing text by rules (no model). Used on its own when no model is available, and merged into
the vision model's reading so a plain statement in the listing ("great for naps", "side drops down") is never lost."""
from __future__ import annotations

import re
from datetime import date

from app.engine.assess import Item
from app.engine.recalls import find_brand

BRANDS = ["Fisher-Price", "Graco", "Chicco", "Evenflo", "Britax", "Boppy", "4moms", "Bumbo", "Delta", "Stork Craft", "Storkcraft", "Kids2",
          "Kids II", "Ingenuity", "Bright Starts", "Safety 1st", "Maxi-Cosi", "Nuna", "UPPAbaby", "Baby Trend", "Summer Infant", "Dream On Me",
          "Munchkin", "Skip Hop", "Halo", "Owlet", "Cosco", "Clek", "Peg Perego", "Joovy", "Cybex", "Doona", "Joie", "Vevor", "Costway",
          "Simplicity", "Kolcraft", "Angelcare", "Infantino", "Nap Nanny", "DockATot", "Baby Delight", "Dorel", "Little Tikes"]
CAT_RX = [
    ("inclined_sleeper", r"rock ?'?n ?play|inclined sleep|rocking sleeper|napper"), ("crib_bumper", r"bumper|slat cover|crib liner"),
    ("high_chair", r"high ?chair"), ("car_seat", r"car ?seat|booster car"), ("swing", r"\bswing\b|glider"), ("crib", r"\bcrib\b"),
    ("bassinet", r"bassinet|cradle|bedside sleeper|co-?sleeper"), ("in_bed_sleeper", r"baby nest|in-bed sleeper|sleep pod|dockatot"),
    ("play_yard", r"play ?yard|pack ?'?n ?play|playpen"), ("lounger", r"lounger|positioner"), ("nursing_pillow", r"nursing pillow"),
    ("bouncer_rocker", r"bouncer|rocker|bumbo|floor seat"), ("walker", r"walker|activity center"), ("bath", r"bath seat|bath tub|bathtub"),
    ("stroller", r"stroller"), ("carrier", r"carrier|sling"), ("sleep_sack", r"sleep sack|swaddle")]

# Text features that a plain statement settles (the listing said it), with negations ignored ("no bumper").
TEXT_FEATURES = {
    "drop_side": r"\bdrop(s|ping)?\b|side (slides|drops)",
    "padded_bumper": r"bumper",
    "marketed_for_sleep": r"\bsleep|\bnap",
    "suction_cups": r"suction",
}
_NEG = re.compile(r"(\bno|\bnot|\bwithout|\bnever|n't|\bremoved)\W+(\w+\W+){0,2}$")

BAN_NAMED = {"crib_bumper", "inclined_sleeper"}

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def mentions(rx: str, t: str) -> bool:
    """True if the pattern appears at least once without a negation just before it."""
    return any(not _NEG.search(t[max(0, m.start() - 30) : m.start()]) for m in re.finditer(rx, t))


def parse_any_date(s: str) -> date | None:
    """Label dates as people and models write them: 2015-03, 2015-03-01, 03/2015, 3/15/2015, March 2015, 2015/03."""
    s = (s or "").strip().lower()
    if not s or s in {"unknown", "n/a", "none"}:
        return None
    pats = [
        (r"\b(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?\b", lambda m: (int(m[1]), int(m[2]))),
        (r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", lambda m: (int(m[3]), int(m[1]))),
        (r"\b(\d{1,2})[-/.](\d{4})\b", lambda m: (int(m[2]), int(m[1]))),
        (r"\b([a-z]{3})[a-z]*\.?\s+(?:\d{1,2},?\s+)?(\d{4})\b", lambda m: (int(m[2]), MONTHS.get(m[1], 0))),
    ]
    for rx, ym in pats:
        m = re.search(rx, s)
        if m:
            y, mo = ym(m)
            if 1990 <= y <= 2100 and 1 <= mo <= 12:
                return date(y, mo, 1)
    return None


def item_from_text(text: str) -> Item:
    """Rule-based reading of the listing text only."""
    t = text.lower()
    cat = next((c for c, rx in CAT_RX if mentions(rx, t)), "other")
    brand = next((b for b in BRANDS if b.lower() in t), "") or find_brand(text)
    feats = {k: True for k, rx in TEXT_FEATURES.items() if mentions(rx, t)}
    if re.search(r"headrest|insert", t) and cat == "swing":
        feats["snuga_headrest_present"] = True
    if re.search(r"(restraint|safety) belt|belt (is )?installed", t) and cat == "bouncer_rocker":
        feats["bumbo_belt_present"] = True
    dom = None
    for m in re.finditer(r"manufactured|\bmade\b|\bmfd\b|\bdate\b", t):
        dom = parse_any_date(re.sub(r"\s*/\s*", "/", t[m.end() : m.end() + 45]))
        if dom:
            break
    models = " ".join(re.findall(r"\b(?=[A-Z0-9-]*\d)[A-Z]{1,5}-?\d{2,7}[A-Z0-9]*\b", text))
    return Item(category=cat, brand=brand, model_text=models, product_name="", listing_text=text[:3000], dom=dom, features=feats)


def merge_text_facts(item: Item, text: str) -> Item:
    """Fill gaps in the vision model's reading with what the listing text plainly states."""
    tx = item_from_text(" ".join(x for x in [text, item.listing_text] if x))
    if (item.category in ("", "other") or item.category_confidence < 0.5) and tx.category != "other":
        item.category = tx.category
    named = item_from_text(item.product_name).category if item.product_name else "other"
    for c in (named, tx.category):  # the listing calls itself a crib bumper or an inclined sleeper: that's what it is
        if c in BAN_NAMED and item.category not in ("crib", c):
            item.category = c
            break
    if not item.brand:
        item.brand = tx.brand
    if item.dom is None:
        item.dom = tx.dom
    extra = [m for m in tx.model_text.split() if m.lower() not in item.model_text.lower()]
    item.model_text = " ".join([item.model_text, *extra]).strip()
    feats = dict(item.features or {})
    for k, v in tx.features.items():
        if v and not feats.get(k):
            feats[k] = True
    item.features = feats
    return item
