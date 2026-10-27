"""Synthetic listings -> training pairs for the look-alike matcher (label 1 = this listing IS this recalled product).

Each true listing: 1 positive + 6 hard negatives (other recalls of the same kind of product) + 2 random negatives.
Each distractor listing: negatives against its recall and 3 other recalls of the same kind.
Leakage rules:
- negatives come only from recalls in the listing's own split, so no test recall's notice is ever seen in training;
- recalls of the same product (re-announcements, expansions: same first product name) form one group; train/dev
  listings whose group also has a test recall are left out;
- recalls with the identical product list as the true one are never used as negatives (they'd be mislabeled).
Deterministic (sorted iteration, fixed seed). Usage: python -m scripts.build_lookalike_pairs
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from app.ai.lookalike import passage, query
from app.engine.recalls import RELATED, cpsc

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "lookalike"


def group_of(r: dict) -> str:
    name = (r.get("products") or [r["title"]])[0].lower()
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"\(.*?\)|®|™", "", name)).strip()


def main() -> None:
    rng = random.Random(5)
    recs = {r["id"]: r for r in cpsc()}
    rows = []
    for name in ("listings_trainval.jsonl", "listings_test.jsonl"):
        p = D / name
        if p.exists():
            rows += [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    split_of = {x["recall"]: x["split"] for x in rows}
    test_groups = {group_of(recs[r]) for r, s in split_of.items() if s == "test" and r in recs}
    by_split_cat: dict[tuple[str, str], list[dict]] = {}
    for r in sorted(recs.values(), key=lambda r: r["id"]):
        s = split_of.get(r["id"])
        if s:
            by_split_cat.setdefault((s, r["category"]), []).append(r)
    out, skipped = [], 0
    for x in rows:
        if x["recall"] not in recs:
            continue
        rc = recs[x["recall"]]
        if x["split"] != "test" and group_of(rc) in test_groups:
            skipped += 1
            continue
        q = query(x["title"], x["text"], x["photo"])
        cats = sorted(RELATED.get(x["category"], {x["category"]}))
        same = [r for c in cats for r in by_split_cat.get((x["split"], c), [])
                if r["id"] != rc["id"] and r.get("products") != rc.get("products")]
        pool = sorted((r for r in recs.values() if split_of.get(r["id"]) == x["split"] and r["id"] != rc["id"]), key=lambda r: r["id"])
        base = {"split": x["split"], "group": x["recall"], "style": x["style"]}
        if x["match"]:
            out.append(base | {"query": q, "passage": passage(rc), "label": 1})
            for r in rng.sample(same, min(6, len(same))):
                out.append(base | {"query": q, "passage": passage(r), "label": 0})
            for r in rng.sample(pool, min(2, len(pool))):
                out.append(base | {"query": q, "passage": passage(r), "label": 0})
        else:
            out.append(base | {"query": q, "passage": passage(rc), "label": 0})
            for r in rng.sample(same, min(3, len(same))):
                out.append(base | {"query": q, "passage": passage(r), "label": 0})
    (D / "pairs.jsonl").write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in out) + "\n")
    cnt: dict[tuple[str, int], int] = {}
    for o in out:
        cnt[(o["split"], o["label"])] = cnt.get((o["split"], o["label"]), 0) + 1
    print(f"{len(out)} pairs ({skipped} train/dev listings left out: same product as a test recall)",
          {f"{s}/{'pos' if lab else 'neg'}": n for (s, lab), n in sorted(cnt.items())})


if __name__ == "__main__":
    main()
