"""Does SecondLook find the recall when the listing has no brand, or a different brand?

Held-out test recalls (never seen in training), listings written by a different model family than the training listings.
For every listing we ask: is the right recall among the top 3 candidates SecondLook would send to Nemotron 3 Ultra?
  keyword       today's brand / model-number / product-name search (no model)
  base_ranker   NVIDIA llama-nemotron-rerank-1b-v2 before fine-tuning, over every recall of the same kind of product
  matcher       our fine-tuned matcher (Nebius), same candidate pool
Also: false look-alikes, i.e. distractor listings (same kind of product, different design) whose best score passes the
threshold. The threshold is chosen on the dev split and saved for the app.
Usage: python -m eval.lookalike_eval
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.ai import lookalike
from app.engine.recalls import cpsc, cpsc_candidates

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "lookalike"


def load(split: str) -> list[dict]:
    f = D / ("listings_test.jsonl" if split == "test" else "listings_trainval.jsonl")
    return [x for x in (json.loads(l) for l in f.read_text().splitlines() if l.strip()) if x["split"] == split] if f.exists() else []


def rank(rows: list[dict], model: str) -> list[list[tuple[str, float]]]:
    out = []
    for x in rows:
        cands = lookalike.pool(x["category"])
        q = lookalike.query(x["title"], x["text"], x["photo"])
        s = lookalike.score([(q, lookalike.passage(r)) for r in cands], model=model, timeout=120)
        out.append(sorted(((r["id"], v) for r, v in zip(cands, s)), key=lambda t: -t[1]))
    return out


def keyword(rows: list[dict]) -> list[list[tuple[str, float]]]:
    out = []
    for x in rows:
        c = cpsc_candidates(x["category"], x.get("brand") or "", f"{x['title']} {x['text']}", k=3)
        out.append([(r["id"], float(r["score"])) for r in c])
    return out


def metrics(rows, ranked, th=None) -> dict:
    res = {}
    for style in ("branded", "unbranded", "rebranded"):
        idx = [i for i, x in enumerate(rows) if x["style"] == style]
        if not idx:
            continue
        top1 = sum(1 for i in idx if ranked[i][:1] and ranked[i][0][0] == rows[i]["recall"] and (th is None or ranked[i][0][1] >= th))
        top3 = sum(1 for i in idx if any(rid == rows[i]["recall"] and (th is None or s >= th) for rid, s in ranked[i][:3]))
        res[style] = {"n": len(idx), "top1": round(top1 / len(idx), 3), "top3": round(top3 / len(idx), 3)}
    d = [i for i, x in enumerate(rows) if x["style"] == "distractor"]
    if d and th is not None:
        fa = sum(1 for i in d if ranked[i] and ranked[i][0][1] >= th)
        res["distractor_false_lookalike_rate"] = round(fa / len(d), 3)
    elif d:
        res["distractor_any_candidate_rate"] = round(sum(1 for i in d if ranked[i]) / len(d), 3)
    return res


def choose_threshold(rows, ranked) -> float:
    """Best F1 on dev: a 'hit' is a true listing whose top recall is right and above the threshold; a false alarm is a
    distractor whose top score is above it."""
    best, best_f1 = 0.8, -1.0
    for t in [i / 100 for i in range(30, 99)]:
        tp = sum(1 for x, r in zip(rows, ranked) if x["match"] and r and r[0][0] == x["recall"] and r[0][1] >= t)
        fp = sum(1 for x, r in zip(rows, ranked) if (not x["match"] or (r and r[0][0] != x["recall"])) and r and r[0][1] >= t)
        fn = sum(1 for x in rows if x["match"]) - tp
        f1 = 2 * tp / max(2 * tp + fp + fn, 1)
        if f1 > best_f1:
            best, best_f1 = t, f1
    return best


def main() -> None:
    test, dev = load("test"), load("dev")
    print(f"test listings: {len(test)}, dev listings: {len(dev)}, recalls in index: {len(cpsc())}")
    out = {"n_test": len(test), "generator_test": test[0]["generator"] if test else "", "methods": {}}
    t0 = time.perf_counter()
    out["methods"]["keyword"] = metrics(test, keyword(test)) | {"seconds": round(time.perf_counter() - t0, 1)}
    if lookalike.available():
        for name, model in (("base_ranker", "base-reranker"), ("matcher", "secondlook-matcher")):
            th = choose_threshold(dev, rank(dev, model)) if dev else None
            t0 = time.perf_counter()
            r = rank(test, model)
            out["methods"][name] = {"threshold_from_dev": th, "no_threshold": metrics(test, r), "at_threshold": metrics(test, r, th),
                                    "seconds_per_listing": round((time.perf_counter() - t0) / max(len(test), 1), 3)}
            if name == "matcher" and th is not None:
                (D / "threshold.json").write_text(json.dumps({"threshold": th}))
    (ROOT / "eval" / "lookalike_results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
