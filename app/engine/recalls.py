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


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", (s or "").lower().replace("'n", "n")) if len(w) >= 3 and w not in STOP}


def _models(s: str) -> set[str]:
    return {m for m in MODEL_RE.findall((s or "").upper()) if not re.fullmatch(r"(19|20)\d\d", m) and len(m) >= 3}


def cpsc_candidates(category: str, brand: str, text: str, k: int = 6) -> list[dict]:
    """text = product name + model text + listing text. Returns scored candidates with reasons."""
    btoks = _tokens(brand)
    mods = _models(text)
    ntoks = _tokens(text) - btoks
    cats = RELATED.get(category, {category})
    out = []
    for r in cpsc():
        hay = f"{r['brand']} {' '.join(r['manufacturers'])} {r['title']}".lower().replace("'n", "n")
        reasons, score = [], 0
        brand_hit = bool(btoks) and any(b in hay for b in btoks)
        if brand_hit:
            score += 3; reasons.append("brand")
        model_hit = [m for m in mods if m in r["models"] or m in r["description"].upper()]
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
                                             "remedy_options", "deaths", "images", "description")},
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
                    "images": [], "hazard": r.get("consequence", ""), "deaths": 0})
    out.sort(key=lambda x: (x["match"] == "definite", x["date"]), reverse=True)
    return out[:k]
