"""Record a real live scan of the demo marketplace so the public demo can replay it (no credits per visit).

For each listing: Super VL identification + rules + quick Nano recall judging (exactly what /api/scan does live),
then the detail view (Ultra recall reading + summary + seller message). Per-listing timings are recorded and
scheduled onto 8 parallel lanes, so the replay shows the same pacing as the real parallel scan.
Needs NEBIUS_API_KEY (+ TAVILY_API_KEY). Writes data/market_cache.json and prints accuracy vs expected labels.
"""
from __future__ import annotations

import heapq
import json
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app import scan
from app.ai import tasks
from app.ai.client import CallRecord
from app.engine.assess import assess
from app.main import DEMO_TODAY, run_check

ROOT = Path(__file__).resolve().parent.parent
LISTINGS = ROOT / "app/static/market/listings.json"
OUT = ROOT / "data/market_cache.json"


def main():
    rows = json.loads(LISTINGS.read_text())
    cache, durations = {}, []
    ok = 0
    for r in rows:
        calls: list[CallRecord] = []
        t0 = time.perf_counter()
        text = f"{r['title']}. {r['text']}"
        img = scan.load_image(r["image"])
        ident = tasks.identify([img], text, calls)
        item = tasks.item_from_identify(ident, text)
        res = assess(item, DEMO_TODAY)
        quick = []
        possible = [x for x in res["recalls"] if x["match"] == "possible"]
        if possible:
            quick = tasks.judge_recalls(item, possible, calls, quick=True)
            res = assess(item, DEMO_TODAY, {j["recall_id"]: j["verdict"] for j in quick})
        scan_seconds = time.perf_counter() - t0
        scan_cost = sum(c.cost_usd for c in calls)
        stamp = scan._stamp(res)
        # detail view (Ultra), cached separately
        dcalls: list[CallRecord] = []
        steps: list[dict] = []
        detail = run_check(item, DEMO_TODAY, dcalls, steps)
        cache[r["id"]] = {"id": r["id"], **stamp, "seconds": round(scan_seconds, 2), "cost_usd": round(scan_cost, 5),
                          "model": "nvidia/Nemotron-3.5-Super-VL", "identify": ident,
                          "detail": {"judgments": detail.get("judgments_raw", []), "verdict": detail["writeup"], "news": detail.get("news", {})},
                          "calls": [asdict(c) | {"seconds": round(c.seconds, 2), "cost_usd": round(c.cost_usd, 5)} for c in calls + dcalls]}
        durations.append((r["id"], scan_seconds))
        good = stamp["word"] == r["expected_word"]
        ok += good
        print(f"{'OK ' if good else 'MISS'} {r['id']} {stamp['word']:8} expected {r['expected_word']:8} {scan_seconds:5.1f}s ${scan_cost:.4f}  {stamp['headline'][:60]}")
    # schedule onto 8 lanes (like the live ThreadPoolExecutor)
    lanes = [0.0] * scan.WORKERS
    heapq.heapify(lanes)
    for lid, d in durations:
        start = heapq.heappop(lanes)
        cache[lid]["finished_at"] = round(start + d, 2)
        heapq.heappush(lanes, start + d)
    OUT.write_text(json.dumps(cache, indent=1))
    total = max(c["finished_at"] for c in cache.values())
    cost = sum(c["cost_usd"] for c in cache.values())
    print(f"\nscan accuracy (signal word): {ok}/{len(rows)}; parallel scan time {total:.1f}s; scan cost ${cost:.4f}")


if __name__ == "__main__":
    main()
