"""Recall candidate retrieval over the local CPSC + NHTSA index. Deterministic and explainable:
the model layer later reads the top candidates' free text to decide whether the exact model is covered."""
from __future__ import annotations

import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

INDEX = Path(__file__).resolve().parents[2] / "data" / "index"
MODEL_RE = re.compile(r"\b(?=[A-Z0-9-]*\d)[A-Z]{0,5}-?\d{2,7}[A-Z0-9]*(?:-[A-Z0-9]+)*\b")
STOP = {"baby", "infant", "the", "and", "for", "with", "inc", "llc", "co", "recalls", "recall", "due", "risk", "brand", "new", "used",
        "kids", "products", "company", "corporation", "child", "children", "toddler", "seat"}

# Recalls that cover every model, so brand + product type is enough (docs §B).
ALL_MODELS = {"19105": {"rock", "play"}, "23088": {"rock", "play"}, "19112": {"rocking", "sleeper"}, "23089": {"rocking", "sleeper"},
              "21198": {"lounger"}, "13083": {"nap", "nanny"}, "10309": {"nap", "nanny"}, "12247": {"bumbo"}}  # id -> name words that must appear
# Recalls whose remedy is visible in photos: feature name -> value that means "fixed".
REMEDY_VISIBLE = {"25009": ("snuga_headrest_present", False), "22200": ("strap_fastener_present", True),
                  "12247": ("bumbo_belt_present", True), "14028": ("cord_cover_present", True)}
RELATED = {
    "inclined_sleeper": {"inclined_sleeper", "bassinet", "play_yard", "swing", "bouncer_rocker"},
    "lounger": {"lounger", "nursing_pillow", "bouncer_rocker"},
    "nursing_pillow": {"lounger", "nursing_pillow"},
    "bassinet": {"bassinet", "play_yard", "inclined_sleeper", "crib"},
    "play_yard": {"play_yard", "bassinet", "inclined_sleeper", "crib_mattress"},
    "swing": {"swing", "bouncer_rocker", "inclined_sleeper"},
    "bouncer_rocker": {"bouncer_rocker", "swing", "inclined_sleeper"},
    "crib": {"crib", "toddler_bed", "crib_bumper", "crib_mattress"},
    "in_bed_sleeper": {"bassinet", "inclined_sleeper", "lounger"},
}


@lru_cache(maxsize=1)
def cpsc() -> list[dict]:
    return json.loads((INDEX / "cpsc_baby.json").read_text())


@lru_cache(maxsize=1)
def nhtsa() -> list[dict]:
    return json.loads((INDEX / "nhtsa_child_seats.json").read_text())


def _stem(w: str) -> str:
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def _tokens(s: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9']+", (s or "").lower().replace("'n", "n")) if len(w) >= 3 and w not in STOP}


def _model_match(m: str, recall_models: list[str], desc_upper: str) -> bool:
    """Exact, or one is a prefix of the other differing by at most 2 trailing chars (BB501 vs BB501K)."""
    if m in recall_models or m in desc_upper:
        return True
    k = re.sub(r"[^A-Z0-9]", "", m)
    for rm in recall_models:
        r = re.sub(r"[^A-Z0-9]", "", rm)
        short, long_ = sorted((k, r), key=len)
        if len(short) >= 4 and long_.startswith(short) and len(long_) - len(short) <= 2:
            return True
    return False


def _models(s: str) -> set[str]:
    return {m for m in MODEL_RE.findall((s or "").upper()) if not re.fullmatch(r"(19|20)\d\d", m) and len(m) >= 3}


COMMON = set("""solid great new like barely gently used soft cozy easy clean older electric gray grey white black blue pink green red natural
wooden big small large free perfect excellent good comes includes include pick smoke lightly bought works folds never only brand selling
moving must firm long short full light dark simple classic modern deluxe premium plus mini max ultra super little sweet happy smart
comfort safe safety secure fresh pure cool warm sunny star moon cloud dream dreams home house family mom dad mama papa love cute
model models size color colour version style type item items edition series""".split())


GENERIC = set("""baby babies infant infants newborn toddler toddlers kids children children's crib cribs bumper bumpers high chair chairs booster
3-in-1 2-in-1 4-in-1 5-in-1 convertible bedside portable electric walker walkers stroller strollers swing swings lounger loungers bath seat seats
bassinet bassinets sleeper sleepers inclined rocking rocker rockers play yard yards playard nursing feeding pillow pillows carrier carriers recalled
recalls recall and with for the original preferred soft braided wooden folding foldable multiple certain select due of to in by a an
mattress mattresses pad pads tub tubs gate gates monitor monitors toy toys rattle rattles teether teethers products product brand
cradle cradles glider gliders bouncer bouncers jumper jumpers activity center infant's travel system systems sleep sack sacks set sets""".split())


def _brand_phrases(name: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9][\w&'.-]*|&", name or "")
    amp = re.match(r"\s*([A-Z][\w'-]*\s*&\s*[A-Z][\w'-]*)", name or "")
    out, cur = ([re.sub(r"\s+", " ", amp.group(1))] if amp else []), []
    for w in words:
        if w.lower().strip(".,") in GENERIC or w == "&":
            break
        cur.append(w)
        if len(cur) > 3:
            break
        out.append(" ".join(cur))
    return [o for o in out if len(o) >= 3 and o.lower() not in GENERIC]


@lru_cache(maxsize=1)
def brand_vocab() -> list[str]:
    """Brand phrases from recall brands and product names (e.g., 'Kids & Koalas', 'SINGES', 'Eddie Bauer'), longest first."""
    names = set()
    for r in cpsc():
        b = re.sub(r",? of [A-Z].*$|\b(Inc|LLC|Ltd|Co|Corp|Corporation|Company|The|Group|USA|International)\b\.?", "", r["brand"] or "").strip(" ,.")
        if b and not b.upper().startswith("CPSC"):
            names.update(_brand_phrases(b))
        for prod in r["products"]:
            for part in re.split(r";|,", prod or ""):
                names.update(_brand_phrases(part.strip()))
    return sorted(names, key=len, reverse=True)


def find_brand(text: str) -> str:
    """Multi-word brand phrases match case-insensitively; single words must look like a name in the text
    (capitalized or all caps) and not be a common word, so 'folds flat' or 'Solid pine crib' never match."""
    raw = text or ""
    low = f" {raw.lower()} "
    for b in brand_vocab():
        if " " in b or "&" in b:
            if b.split()[0].lower() in COMMON:
                continue
            if re.search(r"(?<![a-z0-9])" + re.escape(b.lower()) + r"(?![a-z0-9])", low):
                return b
            continue
        if len(b) < 4 or b.lower() in COMMON or b.lower() in GENERIC:
            continue
        for m in re.finditer(r"(?<![A-Za-z0-9])" + re.escape(b) + r"(?![A-Za-z0-9])", raw, flags=re.I):
            w = m.group(0)
            if w.isupper() or w[0].isupper():
                return b
    return ""


def cpsc_candidates(category: str, brand: str, text: str, k: int = 6) -> list[dict]:
    """text = product name + model text + listing text. Returns scored candidates with reasons."""
    btoks = _tokens(brand)
    mods = _models(text)
    ntoks = _tokens(text) - btoks
    cats = RELATED.get(category, {category})
    out = []
    for r in cpsc():
        hay = f"{r['brand']} {' '.join(r['manufacturers'])} {r['title']} {' '.join(r['products'])}".lower().replace("'n", "n")
        reasons, score = [], 0
        brand_hit = bool(btoks) and any(b in hay for b in btoks)
        if brand_hit:
            score += 3; reasons.append("brand")
        model_hit = [m for m in mods if _model_match(m, r["models"], r["description"].upper())]
        if model_hit:
            score += 6; reasons.append(f"model {model_hit[0]}")
        if r["category"] in cats:
            score += 2; reasons.append("product type")
        overlap = ntoks & _tokens(r["title"] + " " + " ".join(r["products"]))
        if overlap:
            score += min(len(overlap), 3); reasons.append("name: " + ", ".join(sorted(overlap)[:3]))
        same_type = r["category"] in cats
        all_models_hit = r["id"] in ALL_MODELS and brand_hit and ALL_MODELS[r["id"]] <= _tokens(text)
        definite = (bool(model_hit) and brand_hit) or all_models_hit
        possible = bool(model_hit) or (brand_hit and same_type and bool(overlap))
        if not (definite or possible):
            continue
        out.append({**{k_: r[k_] for k_ in ("source", "id", "date", "title", "url", "category", "brand", "units", "hazard", "remedy",
                                             "remedy_options", "deaths", "images", "description", "products")},
                    "score": score, "reasons": reasons, "match": "definite" if definite else "possible",
                    "all_models": r["id"] in ALL_MODELS})
    out.sort(key=lambda x: (x["match"] == "definite", x["score"], x["date"]), reverse=True)
    return out[:k]


def nhtsa_candidates(brand: str, model_text: str, dom: date | None, k: int = 5) -> list[dict]:
    b = (brand or "").strip().lower()
    mt = (model_text or "").lower()
    mtoks = _tokens(model_text)
    out = []
    for r in nhtsa():
        if not b or not any(b in m.lower() or m.lower() in b for m in r["makes"]):
            continue
        hit = [m for m in r["models"] if m.lower() in mt or (mtoks and mtoks <= _tokens(m)) or (_tokens(m) and _tokens(m) <= mtoks)]
        if not hit:
            continue
        in_range = None
        if dom and r["begin"] and r["end"]:
            in_range = r["begin"] <= dom.isoformat() <= r["end"]
        if in_range is False:
            continue
        out.append({**{k_: r[k_] for k_ in ("source", "id", "date", "brand", "units", "description", "remedy", "begin", "end", "url", "component")},
                    "title": f"{r['brand']} {', '.join(hit[:3])}: {r['component'].title()}", "models_hit": hit[:5],
                    "match": "definite" if in_range else "possible", "reasons": ["brand", f"model {hit[0]}"] + (["date in range"] if in_range else []),
                    "images": [], "hazard": r.get("consequence", ""), "deaths": 0, "products": [f"{r['brand']} {hit[0].title()}"]})
    out.sort(key=lambda x: (x["match"] == "definite", x["date"]), reverse=True)
    return out[:k]
