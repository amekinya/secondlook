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
import traceback
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app import scan
from app.ai import lookalike, tasks
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
    ok_level = 0
    for r in rows:
        calls: list[CallRecord] = []
        t0 = time.perf_counter()
        text = f"{r['title']}. {r['text']}"
        try:
            img = scan.load_image(r["image"])
            ident = tasks.identify([img], text, calls)
            item = tasks.item_from_identify(ident, text)
            looks = lookalike.for_item(item, calls)  # same steps as scan_one in app/scan.py
            res = assess(item, DEMO_TODAY, lookalikes=looks)
            quick = []
            cands = res.get("candidates", res["recalls"])
            possible = [x for x in cands if x["match"] == "possible" or (x["match"] == "definite" and not x.get("all_models"))][:4] + \
                [x for x in cands if x["match"] == "lookalike"][:2]
            if possible:
                try:
                    quick = tasks.judge_recalls(item, possible, calls, quick=True)
                    res = assess(item, DEMO_TODAY, {j["recall_id"]: j["verdict"] for j in quick}, lookalikes=looks)
                except tasks.LiveModelUnavailable as e:
                    print(f"   quick judge unavailable for {r['id']}: {e}")
            scan_seconds = time.perf_counter() - t0
            scan_cost = sum(c.cost_usd for c in calls)
            stamp = scan._stamp(res)
            dcalls: list[CallRecord] = []
            steps: list[dict] = []
            detail = run_check(item, DEMO_TODAY, dcalls, steps)
        except Exception:
            print(f"ERROR {r['id']}\n{traceback.format_exc()}")
            continue
        cache[r["id"]] = {"id": r["id"], **stamp, "seconds": round(scan_seconds, 2), "cost_usd": round(scan_cost, 5),
                          "model": "nvidia/Nemotron-3.5-Super-VL", "identify": ident, "quick_judgments": quick,
                          "detail": {"judgments": detail.get("judgments_raw", []), "verdict": detail["writeup"], "news": detail.get("news", {}),
                                     "lookalikes": detail.get("lookalikes", []),
                                     "level": detail["level"]},
                          "calls": [asdict(c) | {"seconds": round(c.seconds, 2), "cost_usd": round(c.cost_usd, 5)} for c in calls + dcalls]}
        durations.append((r["id"], scan_seconds))
        good = stamp["word"] == r["expected_word"]
        ok += good
        ok_level += res["level"] == r["expected_level"]
        flag = "OK  " if good and res["level"] == r["expected_level"] else "OK* " if good else "MISS"
        print(f"{flag} {r['id']} {stamp['word']:8} {res['level']:16} expected {r['expected_word']:8} {r['expected_level']:16} "
              f"{scan_seconds:5.1f}s ${scan_cost:.4f}  {stamp['headline'][:55]} | detail: {detail['level']}")
        if flag != "OK  ":
            print("   item:", json.dumps({k: v for k, v in asdict(item).items() if k != "listing_text"}, default=str))
            print("   quick:", json.dumps(quick)[:1200])
    # schedule onto 8 lanes (like the live ThreadPoolExecutor)
    lanes = [0.0] * scan.WORKERS
    heapq.heapify(lanes)
    for lid, d in durations:
        start = heapq.heappop(lanes)
        cache[lid]["finished_at"] = round(start + d, 2)
        heapq.heappush(lanes, start + d)
    OUT.write_text(json.dumps(cache, indent=1))
    total = max((c["finished_at"] for c in cache.values()), default=0)
    cost = sum(c["cost_usd"] for c in cache.values())
    print(f"\nscan accuracy: signal word {ok}/{len(rows)}, exact level {ok_level}/{len(rows)}; parallel scan time {total:.1f}s; scan cost ${cost:.4f}")


if __name__ == "__main__":
    main()
