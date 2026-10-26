"""Build SecondLook's local recall index from public data.

Inputs (download once; both are public, no key):
  CPSC Recalls API bulk JSON: https://www.saferproducts.gov/RestWebServices/Recall?format=json  (pass as --cpsc)
  NHTSA recalls flat file:    https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip      (unzipped .txt, pass as --nhtsa)
Outputs:
  data/index/cpsc_baby.json      infant/juvenile-product recalls with extracted model tokens and categories
  data/index/nhtsa_child_seats.json  child-restraint (car seat) campaigns with manufacture date ranges

The CPSC API's Model field is empty in every record, so model numbers are pulled from the free-text
description with a regex (see docs/safety_rules_research.md §C3).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent / "index"

CATEGORIES = [  # (category, regex on title + product names); order matters (first match wins)
    ("inclined_sleeper", r"inclined sleep|rock ?'?n ?play|rocking sleeper|incline sleeper|sleeper.*incline|napper"),
    ("crib_bumper", r"bumper|slat cover|crib liner"),
    ("crib", r"\bcribs?\b|drop[- ]side"),
    ("bassinet", r"bassinet|cradle|bedside sleeper|co-?sleeper|in-bed sleeper|baby nest|sleep pod|travel bed"),
    ("play_yard", r"play ?yard|playard|playpen|pack ?'?n ?play|play pen"),
    ("crib_mattress", r"crib mattress|play yard mattress|playard mattress|mattress pad"),
    ("lounger", r"lounger|positioner|support cushion|tummy time pillow|infant cushion"),
    ("nursing_pillow", r"nursing pillow|feeding pillow"),
    ("swing", r"\bswings?\b|glider|soother"),
    ("bouncer_rocker", r"bouncer|rocker|baby seat|floor seat|bumbo|recliner|nap nanny"),
    ("walker", r"walker|activity center|jumper|exersaucer"),
    ("bath", r"bath seat|bath ring|bathtub|bath tub|bather"),
    ("high_chair", r"high ?chair|booster seat"),
    ("stroller", r"stroller|pram|jogger|travel system"),
    ("carrier", r"\bcarrier|sling|wrap\b|backpack carrier"),
    ("car_seat", r"car seat|child restraint|infant seat"),
    ("gate", r"\bgates?\b"),
    ("changing_table", r"changing table|changing pad|changing station"),
    ("monitor", r"baby monitor|movement monitor|sensor pad"),
    ("sleep_sack", r"sleep sack|swaddle|wearable blanket|sleepwear|weighted"),
    ("toy_infant", r"rattle|teether|teething|pacifier|crib mobile|crib toy|activity gym|play mat"),
    ("toddler_bed", r"toddler bed|bed rail"),
]
BABY_HINT = re.compile(r"\b(infant|baby|babies|toddler|newborn|nursery|crib|bassinet|cradle|stroller|car seat|high ?chair|play ?yard|"
                       r"playard|bouncer|walker|pacifier|teether|swaddle|sleeper|lounger|nursing pillow|changing table|sling)\b", re.I)
MODEL_RE = re.compile(r"\b(?=[A-Z0-9-]*\d)[A-Z]{0,5}-?\d{2,7}[A-Z0-9]*(?:-[A-Z0-9]+)*\b")
DEATH_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def classify(text: str) -> str | None:
    t = text.lower()
    for cat, rx in CATEGORIES:
        if re.search(rx, t):
            return cat
    return None


def deaths_in(s: str) -> int:
    m = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:infant\s+|child\s+|reported\s+)?deaths?", s or "", re.I)
    if not m:
        return 1 if re.search(r"\b(a|one) (infant|child|baby) died|death of a", s or "", re.I) else 0
    g = m.group(1).lower()
    return int(g) if g.isdigit() else DEATH_WORDS.get(g, 0)


def brand_of(title: str, manufacturers: list[str]) -> str:
    m = re.match(r"(.+?)\s+(?:Recalls?|Reannounces|Announces|Expands)\b", title or "")
    b = (m.group(1) if m else (manufacturers[0] if manufacturers else "")).strip()
    return re.sub(r"\b(Inc|LLC|Ltd|Co|Corp|Corporation|Company)\.?\b", "", b).strip(" ,.")


def build_cpsc(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    out = []
    for r in data:
        names = " ".join(p.get("Name", "") or "" for p in r.get("Products", []) or [])
        head = f"{r.get('Title', '')} {names}"
        if not BABY_HINT.search(head + " " + (r.get("Description") or "")[:400]):
            continue
        cat = classify(head) or classify((r.get("Description") or "")[:600])
        if cat is None:
            continue
        desc = re.sub(r"\s+", " ", r.get("Description") or "").strip()
        models = sorted({m for m in MODEL_RE.findall(desc) if not re.fullmatch(r"\d{4}", m) and len(m) >= 3})[:120]
        injuries = " ".join(i.get("Name", "") or "" for i in r.get("Injuries", []) or [])
        manufacturers = [m.get("Name", "") for m in r.get("Manufacturers", []) or [] if m.get("Name")]
        out.append({
            "source": "CPSC", "id": str(r.get("RecallNumber") or r.get("RecallID")), "date": (r.get("RecallDate") or "")[:10],
            "title": r.get("Title", ""), "url": r.get("URL", ""), "category": cat,
            "brand": brand_of(r.get("Title", ""), manufacturers), "manufacturers": manufacturers,
            "products": [p.get("Name", "") for p in r.get("Products", []) or []],
            "units": " / ".join(p.get("NumberOfUnits", "") or "" for p in r.get("Products", []) or [] if p.get("NumberOfUnits")),
            "description": desc[:1800], "models": models,
            "hazard": " ".join(h.get("Name", "") or "" for h in r.get("Hazards", []) or [])[:600],
            "remedy": " ".join(h.get("Name", "") or "" for h in r.get("Remedies", []) or [])[:600],
            "remedy_options": [o.get("Option", "") for o in r.get("RemedyOptions", []) or []],
            "injuries": injuries[:500], "deaths": deaths_in(injuries + " " + r.get("Title", "")),
            "retailers": " ".join(x.get("Name", "") or "" for x in r.get("Retailers", []) or [])[:300],
            "upcs": [u.get("UPC", "") for u in r.get("ProductUPCs", []) or [] if u.get("UPC")][:20],
            "images": [{"url": i.get("URL", ""), "caption": i.get("Caption", "")} for i in (r.get("Images") or [])[:3]],
        })
    out.sort(key=lambda x: x["date"], reverse=True)
    return out


def build_nhtsa(path: Path) -> list[dict]:
    csv.field_size_limit(sys.maxsize)
    camps: dict[str, dict] = {}
    with open(path, encoding="latin-1", newline="") as fh:
        for row in csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(row) < 22 or row[10].strip() != "C":
                continue
            c = camps.setdefault(row[1].strip(), {
                "source": "NHTSA", "id": row[1].strip(), "date": f"{row[15][:4]}-{row[15][4:6]}-{row[15][6:8]}" if len(row[15]) == 8 else "",
                "category": "car_seat", "brand": row[2].strip().title(), "makes": set(), "models": set(), "begin": "", "end": "",
                "units": row[11].strip(), "manufacturer": row[7].strip(), "description": row[19].strip()[:1800],
                "consequence": row[20].strip()[:800], "remedy": row[21].strip()[:1200], "component": row[6].strip(),
                "url": f"https://www.nhtsa.gov/?nhtsaId={row[1].strip()}",
            })
            c["makes"].add(row[2].strip())
            c["models"].add(row[3].strip())
            b, e = row[8].strip(), row[9].strip()
            if len(b) == 8 and (not c["begin"] or b < c["begin"]):
                c["begin"] = b
            if len(e) == 8 and (not c["end"] or e > c["end"]):
                c["end"] = e
    out = []
    for c in camps.values():
        c["makes"], c["models"] = sorted(c["makes"]), sorted(c["models"])
        fmt = lambda s: f"{s[:4]}-{s[4:6]}-{s[6:8]}" if s else ""
        c["begin"], c["end"] = fmt(c["begin"]), fmt(c["end"])
        out.append(c)
    out.sort(key=lambda x: x["date"], reverse=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpsc", required=True, type=Path)
    ap.add_argument("--nhtsa", required=True, type=Path)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cpsc = build_cpsc(a.cpsc)
    nh = build_nhtsa(a.nhtsa)
    (OUT / "cpsc_baby.json").write_text(json.dumps(cpsc, separators=(",", ":")))
    (OUT / "nhtsa_child_seats.json").write_text(json.dumps(nh, separators=(",", ":")))
    cats = defaultdict(int)
    for r in cpsc:
        cats[r["category"]] += 1
    print(f"CPSC baby recalls: {len(cpsc)}  NHTSA child-seat campaigns: {len(nh)}")
    print(dict(sorted(cats.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
