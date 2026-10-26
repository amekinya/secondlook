"""Precompute model outputs for the 6 demo listings so the public demo doesn't spend credits per visit.
Needs NEBIUS_API_KEY (+ TAVILY_API_KEY). Writes data/listings/demo_cache.json."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.ai import tasks
from app.ai.client import CallRecord
from app.main import DEMO_TODAY, run_check

ROOT = Path(__file__).resolve().parent.parent
L = ROOT / "data/listings"


def main():
    meta = json.loads((L / "listings.json").read_text())
    cache = {}
    for m in meta:
        calls: list[CallRecord] = []
        ident = tasks.identify([((L / m["file"]).read_bytes(), "image/png")], "", calls)
        item = tasks.item_from_identify(ident)
        steps: list[dict] = []
        res = run_check(item, DEMO_TODAY, calls, steps)
        judgments = res.get("judgments_raw", [])
        cache[m["file"]] = {"identify": ident, "judgments": judgments, "verdict": res["writeup"], "news": res.get("news", {}),
                            "calls": [asdict(c) | {"seconds": round(c.seconds, 2), "cost_usd": round(c.cost_usd, 5)} for c in calls]}
        print(m["file"], res["level"], "expected", m["expected_level"])
    (L / "demo_cache.json").write_text(json.dumps(cache, indent=1))
    print("wrote demo_cache.json")


if __name__ == "__main__":
    main()
