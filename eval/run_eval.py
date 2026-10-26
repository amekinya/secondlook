"""SecondLook benchmark (needs NEBIUS_API_KEY).

1. Product recognition: Nemotron 3.5 Super VL names the product type in 57 CPSC recall photos (14 categories).
2. Recall matching: 40 listings built from real recall records (brand + product + a model number the recall covers)
   plus 40 decoys (same brand and product type, a model number no recall covers).
   Systems: rules + retrieval only; rules + retrieval + Nemotron 3 Ultra reading the notices; Ultra alone from memory.
3. Demo listings: does the full pipeline reach the expected verdict on the 6 demo screenshots?
Writes eval/results.json and eval/RESULTS.md.
"""
from __future__ import annotations

import json
import random
import re
import statistics
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

from app.ai import tasks
from app.ai.client import CallRecord, chat_json
from app.config import settings
from app.engine.assess import Item, assess
from app.engine.recalls import cpsc

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 10, 25)
calls: list[CallRecord] = []
LENIENT = {"inclined_sleeper": {"swing", "bassinet", "bouncer_rocker", "play_yard"}, "swing": {"bouncer_rocker", "inclined_sleeper"},
           "bouncer_rocker": {"swing", "inclined_sleeper"}, "lounger": {"nursing_pillow", "in_bed_sleeper"}, "nursing_pillow": {"lounger"},
           "bassinet": {"in_bed_sleeper", "play_yard", "inclined_sleeper"}, "play_yard": {"bassinet", "crib"}, "crib": {"play_yard"},
           "walker": {"bouncer_rocker"}, "high_chair": {"bouncer_rocker"}}


def recognition() -> dict:
    labels = json.loads((ROOT / "data/cpsc_images/eval_labels.json").read_text())
    strict = lenient = 0
    per_cat = defaultdict(lambda: [0, 0])
    rows = []
    for lab in labels:
        p = ROOT / "data/cpsc_images" / lab["file"]
        local: list[CallRecord] = []
        try:
            d = tasks.identify([(p.read_bytes(), "image/jpeg" if p.suffix == ".jpg" else "image/png")], "", local)
            got = d.get("category", "")
        except Exception as e:
            got = "ERR"
        calls.extend(local)
        s = got == lab["category"]
        l = s or got in LENIENT.get(lab["category"], set())
        strict += s; lenient += l
        per_cat[lab["category"]][0] += s; per_cat[lab["category"]][1] += 1
        rows.append({"file": lab["file"], "expected": lab["category"], "got": got})
    n = len(labels)
    return {"n": n, "strict": round(strict / n, 3), "lenient": round(lenient / n, 3),
            "by_category": {k: f"{a}/{b}" for k, (a, b) in sorted(per_cat.items())}, "rows": rows}


def _listing_set(k: int = 40) -> list[dict]:
    rng = random.Random(7)
    pool = [r for r in cpsc() if len(r["models"]) >= 1 and r["brand"] and len(r["brand"]) < 40 and r["category"] not in {"toy_infant"}
            and r["date"] >= "2012"]
    rng.shuffle(pool)
    out = []
    for r in pool[:k]:
        model = rng.choice(r["models"][:10])
        name = (r["products"] or [r["title"]])[0][:60]
        brand = r["brand"].split(",")[0]
        out.append({"kind": "positive", "recall": r["id"], "category": r["category"], "brand": brand, "name": name, "model": model})
        decoy = f"{rng.choice('QXZ')}{rng.choice('RKV')}-{rng.randint(10000, 99999)}"
        out.append({"kind": "decoy", "recall": r["id"], "category": r["category"], "brand": brand, "name": name, "model": decoy})
    return out


BASELINE_SCHEMA = {"type": "object", "properties": {"recalled": {"type": "boolean"}, "recall_number": {"type": "string"}},
                   "required": ["recalled", "recall_number"], "additionalProperties": False}


def matching() -> dict:
    items = _listing_set()
    res = {"rules_only": [], "rules_plus_ultra": [], "ultra_from_memory": []}
    for it in items:
        item = Item(category=it["category"], brand=it["brand"], product_name=it["name"], model_text=it["model"],
                    listing_text=f"{it['brand']} {it['name']} model {it['model']}")
        a = assess(item, TODAY)
        hit_rules = any(r["id"] == it["recall"] and r["match"] == "definite" for r in a["recalls"])
        local: list[CallRecord] = []
        try:
            js = tasks.judge_recalls(item, a["recalls"], local)
            jd = {j["recall_id"]: j["verdict"] for j in js}
        except Exception:
            jd = {}
        calls.extend(local)
        b = assess(item, TODAY, jd)
        hit_judge = any(r["id"] == it["recall"] and r["match"] == "definite" for r in b["recalls"])
        local = []
        try:
            m = chat_json(settings.ultra, [{"role": "user", "content": f"Is this specific product under a US CPSC recall? {it['brand']} {it['name']}, model {it['model']}. "
                                                                         "Answer from your own knowledge; give the recall number if yes."}],
                          schema=BASELINE_SCHEMA, purpose="Ultra-from-memory baseline", reasoning=True, max_tokens=2000, calls=local, enforce_cap=False)
            hit_mem = bool(m.get("recalled")) and (it["kind"] == "decoy" or re.sub(r"\D", "", m.get("recall_number", "")) == re.sub(r"\D", "", it["recall"]))
            hit_mem = bool(m.get("recalled")) if it["kind"] == "decoy" else hit_mem
        except Exception:
            hit_mem = False
        calls.extend(local)
        for key, hit in (("rules_only", hit_rules), ("rules_plus_ultra", hit_judge), ("ultra_from_memory", hit_mem)):
            res[key].append((it["kind"], hit))
    out = {"n_positive": sum(1 for i in items if i["kind"] == "positive"), "n_decoy": sum(1 for i in items if i["kind"] == "decoy")}
    for key, rows in res.items():
        tp = sum(1 for k, h in rows if k == "positive" and h)
        fp = sum(1 for k, h in rows if k == "decoy" and h)
        out[key] = {"recall_caught": round(tp / out["n_positive"], 3), "false_alarms_on_decoys": round(fp / out["n_decoy"], 3)}
    return out


def demo() -> dict:
    meta = json.loads((ROOT / "data/listings/listings.json").read_text())
    from app.main import item_from_text, run_check  # noqa: PLC0415

    rows = []
    for m in meta:
        local: list[CallRecord] = []
        steps: list[dict] = []
        try:
            d = tasks.identify([((ROOT / "data/listings" / m["file"]).read_bytes(), "image/png")], "", local)
            item = tasks.item_from_identify(d)
        except Exception:
            item = item_from_text(f"{m['title']}. {m['text']}")
        r = run_check(item, TODAY, local, steps)
        calls.extend(local)
        rows.append({"file": m["file"], "expected": m["expected_level"], "got": r["level"], "ok": r["level"] == m["expected_level"]})
    return {"correct": f"{sum(r['ok'] for r in rows)}/{len(rows)}", "rows": rows}


def tiers() -> dict:
    out = {}
    for role in ("nano", "super_vl", "ultra"):
        cs = [c for c in calls if c.role == role]
        if cs:
            out[role] = {"model": cs[0].model_id, "calls": len(cs), "avg_seconds": round(statistics.mean(c.seconds for c in cs), 2),
                         "cost_usd": round(sum(c.cost_usd for c in cs), 4)}
    return out


def main():
    r = {"run_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "recognition": recognition(), "matching": matching(), "demo": demo()}
    r["tiers"] = tiers()
    (ROOT / "eval/results.json").write_text(json.dumps(r, indent=1))
    md = [f"# SecondLook benchmark results\n\nRun {r['run_at']}.\n",
          f"## 1. Product recognition ({r['recognition']['n']} CPSC recall photos, 14 product types)\n",
          f"Nemotron 3.5 Super VL named the exact product type in {r['recognition']['strict']:.0%} of photos ({r['recognition']['lenient']:.0%} counting near neighbors such as swing vs. inclined sleeper).\n",
          f"## 2. Recall matching ({r['matching']['n_positive']} recalled listings + {r['matching']['n_decoy']} decoys)\n",
          "| System | Recalls caught | False alarms on decoys |", "|---|---|---|"]
    names = {"rules_only": "Rules + recall index", "rules_plus_ultra": "Rules + recall index + Nemotron 3 Ultra reading the notices",
             "ultra_from_memory": "Nemotron 3 Ultra alone (from memory)"}
    for k, label in names.items():
        md.append(f"| {label} | {r['matching'][k]['recall_caught']:.0%} | {r['matching'][k]['false_alarms_on_decoys']:.0%} |")
    md += [f"\n## 3. Demo listings\n\n{r['demo']['correct']} reached the expected verdict.\n", "## 4. Cost and latency\n",
           "| Tier | Model | Calls | Avg seconds | Cost |", "|---|---|---|---|---|"]
    md += [f"| {k} | {v['model']} | {v['calls']} | {v['avg_seconds']} | ${v['cost_usd']:.3f} |" for k, v in r["tiers"].items()]
    (ROOT / "eval/RESULTS.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
