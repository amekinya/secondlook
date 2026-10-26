"""Precompute model outputs for the 6 demo listings so the public demo doesn't spend credits per visit.
Needs NEBIUS_API_KEY (+ TAVILY_API_KEY). Writes data/listings/demo_cache.json. One listing failing doesn't stop the rest."""
from __future__ import annotations

import json
import traceback
from dataclasses import asdict
from pathlib import Path

from app.ai import tasks
from app.ai.client import CallRecord
from app.main import DEMO_TODAY, run_check

ROOT = Path(__file__).resolve().parent.parent
L = ROOT / "data/listings"


def main():
    meta = json.loads((L / "listings.json").read_text())
    cache, ok = {}, 0
    for m in meta:
        calls: list[CallRecord] = []
        try:
            ident = tasks.identify([((L / m["file"]).read_bytes(), "image/png")], "", calls)
            item = tasks.item_from_identify(ident)
            steps: list[dict] = []
            res = run_check(item, DEMO_TODAY, calls, steps)
        except Exception:
            print(f"ERROR {m['file']}\n{traceback.format_exc()}")
            continue
        cache[m["file"]] = {"identify": ident, "judgments": res.get("judgments_raw", []), "verdict": res["writeup"], "news": res.get("news", {}),
                            "calls": [asdict(c) | {"seconds": round(c.seconds, 2), "cost_usd": round(c.cost_usd, 5)} for c in calls]}
        good = res["level"] == m["expected_level"]
        ok += good
        print(f"{'OK ' if good else 'MISS'} {m['file']} {res['level']} expected {m['expected_level']} | {res['reasons'][0]['title']}")
        if not good:
            print("   item:", json.dumps({k: v for k, v in asdict(item).items() if k != "listing_text"}, default=str))
            print("   judgments:", json.dumps(res.get("judgments_raw", []))[:1500])
    (L / "demo_cache.json").write_text(json.dumps(cache, indent=1))
    print(f"wrote demo_cache.json ({len(cache)}/{len(meta)} listings, {ok} as expected)")


if __name__ == "__main__":
    main()
