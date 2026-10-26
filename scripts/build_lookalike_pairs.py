"""Synthetic listings -> training pairs for the look-alike matcher (label 1 = this listing IS this recalled product).
Each true listing: 1 positive + 6 hard negatives (other recalls of the same kind of product) + 2 random negatives.
Each distractor listing: negatives against its recall and 3 other recalls of the same kind.
Usage: python -m scripts.build_lookalike_pairs   (reads data/lookalike/listings_trainval.jsonl [+ listings_test.jsonl])"""
from __future__ import annotations

import json
import random
from pathlib import Path

from app.ai.lookalike import passage, query
from app.engine.recalls import RELATED, cpsc

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "lookalike"


def main() -> None:
    rng = random.Random(5)
    recs = {r["id"]: r for r in cpsc()}
    by_cat: dict[str, list[dict]] = {}
    for r in recs.values():
        by_cat.setdefault(r["category"], []).append(r)
    rows = []
    for name in ("listings_trainval.jsonl", "listings_test.jsonl"):
        p = D / name
        if p.exists():
            rows += [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    out = []
    for x in rows:
        if x["recall"] not in recs:
            continue
        q = query(x["title"], x["text"], x["photo"])
        cats = RELATED.get(x["category"], {x["category"]})
        same = [r for c in cats for r in by_cat.get(c, []) if r["id"] != x["recall"]]
        base = {"split": x["split"], "group": x["recall"], "style": x["style"]}
        if x["match"]:
            out.append(base | {"query": q, "passage": passage(recs[x["recall"]]), "label": 1})
            for r in rng.sample(same, min(6, len(same))):
                out.append(base | {"query": q, "passage": passage(r), "label": 0})
            for r in rng.sample(list(recs.values()), 2):
                if r["id"] != x["recall"]:
                    out.append(base | {"query": q, "passage": passage(r), "label": 0})
        else:
            out.append(base | {"query": q, "passage": passage(recs[x["recall"]]), "label": 0})
            for r in rng.sample(same, min(3, len(same))):
                out.append(base | {"query": q, "passage": passage(r), "label": 0})
    (D / "pairs.jsonl").write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in out) + "\n")
    cnt = {}
    for o in out:
        cnt[(o["split"], o["label"])] = cnt.get((o["split"], o["label"]), 0) + 1
    print(f"{len(out)} pairs", {f"{s}/{'pos' if l else 'neg'}": n for (s, l), n in sorted(cnt.items())})


if __name__ == "__main__":
    main()
