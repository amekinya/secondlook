"""Deterministic verdict: item facts (from photos/listing text) -> bans, recalls, car seat expiry, checklist."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

from app.engine import catalog as C
from app.engine.recalls import REMEDY_VISIBLE, cpsc_candidates, nhtsa_candidates


@dataclass
class Item:
    category: str = "other"
    category_confidence: float = 0.0
    brand: str = ""
    model_text: str = ""
    product_name: str = ""
    listing_text: str = ""
    dom: date | None = None  # date of manufacture (from label or listing)
    printed_expiration: date | None = None
    features: dict = field(default_factory=dict)  # incline_raised, marketed_for_sleep, drop_side, padded_bumper, ...
    missing_parts: list[str] = field(default_factory=list)


def _add(reasons: list[dict], rule_id: str, **extra) -> None:
    r = C.RULES[rule_id]
    reasons.append({"rule_id": r.id, "level": r.level, "title": extra.pop("title", r.title), "detail": extra.pop("detail", r.detail),
                    "cite": r.cite, "tag": r.tag, **extra})


def assess(item: Item, today: date | None = None, judgments: dict[str, str] | None = None) -> dict:
    today = today or date.today()
    f = item.features or {}
    cat = item.category
    reasons: list[dict] = []
    judgments = judgments or {}

    # --- Bans and standards (category + visible features) ---------------------------------
    if cat == "inclined_sleeper" or (f.get("incline_raised") and f.get("marketed_for_sleep") and cat in {"bassinet", "play_yard", "swing", "bouncer_rocker", "in_bed_sleeper"}):
        _add(reasons, "R-INC-01")
    if cat == "crib_bumper":
        if f.get("mesh_liner") and not f.get("padded_bumper"):
            pass
        else:
            _add(reasons, "R-BMP-01")
    if cat == "crib" and f.get("padded_bumper"):
        _add(reasons, "R-BMP-01", title="Listing includes a padded crib bumper",
             detail="The bumper in the photos is banned from sale (since Nov 12, 2022). The crib itself may be fine; leave the bumper out.")
    if cat == "crib":
        if f.get("drop_side"):
            _add(reasons, "R-CRB-01")
        elif item.dom and item.dom < date(2011, 6, 28):
            _add(reasons, "R-CRB-02")
        elif item.dom is None:
            _add(reasons, "R-CRB-03")
    if cat == "in_bed_sleeper" and not f.get("legs_or_stand"):
        _add(reasons, "R-ISP-01")
    if cat == "lounger":
        if f.get("restraint_strap") and item.dom and item.dom > date(2025, 5, 5):
            _add(reasons, "R-ISC-02")
        _add(reasons, "R-ISC-01")
    if cat == "nursing_pillow" and f.get("restraint_strap") and item.dom and item.dom > date(2025, 4, 23):
        _add(reasons, "R-NP-01")
    if cat == "sleep_sack" and f.get("weighted"):
        _add(reasons, "R-WGT-01")
    if cat == "walker":
        _add(reasons, "R-WLK-01")
    if cat == "bath" and f.get("suction_cups"):
        _add(reasons, "R-BTH-01")

    # --- Car seats ------------------------------------------------------------------------
    car_seat = None
    if cat == "car_seat":
        car_seat = _car_seat(item, today, reasons)

    # --- Recalls ----------------------------------------------------------------------------
    text = " ".join([item.product_name, item.model_text, item.listing_text])
    recalls = []
    if cat == "car_seat":
        recalls = nhtsa_candidates(item.brand, f"{item.model_text} {item.product_name}", item.dom)
    elif cat != "other":
        recalls = cpsc_candidates(cat, item.brand, text)
    for rc in recalls:
        j = judgments.get(rc["id"])
        if j == "does_not_apply":
            rc["match"] = "ruled_out"
            continue
        if j == "applies":
            rc["match"] = "definite"
        if rc["match"] == "definite":
            remedy = REMEDY_VISIBLE.get(rc["id"])
            if remedy and f.get(remedy[0]) is not None and f.get(remedy[0]) == remedy[1]:
                _add(reasons, "R-RCL-03", recall=rc["id"], title=f"Recall {rc['id']} fix appears done")
                rc["remedied"] = True
            else:
                _add(reasons, "R-CS-RCL" if rc["source"] == "NHTSA" else "R-RCL-01", recall=rc["id"], title=rc["title"])
        elif rc["match"] == "possible":
            _add(reasons, "R-RCL-02", recall=rc["id"], title=f"Possible recall: {rc['title']}")
    recalls = [r for r in recalls if r["match"] != "ruled_out"]

    if item.missing_parts:
        _add(reasons, "R-PARTS", title="Parts look missing", detail="From the photos: " + "; ".join(item.missing_parts[:5]))
    if not reasons:
        _add(reasons, "R-NONE")

    order = {lv: i for i, lv in enumerate(C.LEVELS)}
    reasons.sort(key=lambda r: order[r["level"]])
    level = reasons[0]["level"]
    label, tone, sub = C.LEVEL_UI[level]
    questions = list(dict.fromkeys(C.QUESTIONS.get(cat, []) + C.QUESTIONS["_any"]))
    if any(r["rule_id"] == "R-RCL-02" for r in reasons):
        questions.insert(0, "What's the exact model number on the label? (It decides whether the recall applies.)")
    return {
        "level": level, "label": label, "tone": tone, "sub": sub, "category": cat,
        "category_label": C.CATEGORIES.get(cat, cat), "reasons": reasons, "recalls": recalls[:4],
        "car_seat": car_seat, "checklist": C.PARTS.get(cat, []), "questions": questions[:5],
        "item": {**asdict(item), "dom": item.dom.isoformat() if item.dom else None,
                 "printed_expiration": item.printed_expiration.isoformat() if item.printed_expiration else None},
        "rules_verified_as_of": C.RULES_VERIFIED_AS_OF.isoformat(),
    }


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d + timedelta(days=365 * years)


def _car_seat(item: Item, today: date, reasons: list[dict]) -> dict:
    info = {"dom": item.dom.isoformat() if item.dom else None, "expires": None, "basis": None, "life": None}
    if item.printed_expiration:
        exp = item.printed_expiration
        info.update(expires=exp.isoformat(), basis="printed on the seat")
    elif item.dom:
        life = C.CAR_SEAT_LIFE.get((item.brand or "").strip().lower())
        if life:
            lo, hi, note, tag = life
            info.update(life=f"{lo}-{hi} years" if lo != hi else f"{lo} years", life_note=note, life_tag=tag)
            exp_lo, exp_hi = _add_years(item.dom, lo), _add_years(item.dom, hi)
            if exp_hi < today:
                exp = exp_hi
                info.update(expires=exp_hi.isoformat(), basis=f"manufacture date + {hi} years (brand maximum)")
            elif exp_lo < today:
                info.update(expires=exp_lo.isoformat(), basis=f"manufacture date + {lo}-{hi} years; depends on the model", ambiguous=True)
                _add(reasons, "R-CS-EXP-SOON", title="Car seat may already be expired",
                     detail=f"Made {item.dom:%b %Y}. {item.brand} seats last {lo}-{hi} years depending on model, so this one expired {exp_lo:%b %Y} or expires by {exp_hi:%b %Y}. Ask for the 'do not use after' date.")
                exp = None
            else:
                exp = exp_lo
                info.update(expires=exp_lo.isoformat(), basis=f"manufacture date + {lo} years (brand minimum)")
        else:
            exp = None
            info.update(basis="brand lifespan unknown; read the 'do not use after' date")
    else:
        exp = None
    if exp is not None:
        if exp < today:
            _add(reasons, "R-CS-EXP", title=f"Car seat expired {exp:%b %Y}", expires=exp.isoformat())
        elif exp < today + timedelta(days=365):
            _add(reasons, "R-CS-EXP-SOON", title=f"Car seat expires {exp:%b %Y}")
    if not item.dom and not item.printed_expiration:
        _add(reasons, "R-CS-LBL")
    else:
        _add(reasons, "R-CS-LBL", title="Ask about crash history", detail="Never use a seat that's been in a moderate or severe crash. NHTSA lists five conditions that make a crash 'minor'.")
    return info
