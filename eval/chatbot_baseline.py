"""What would a plain chatbot say? The same 24 marketplace listings, asked in one prompt with no recall data, no rules
engine and no notice reading. Compared with SecondLook's recorded scan (data/market_cache.json).

  Super VL, one prompt    photo + listing text -> verdict
  Ultra, one prompt       listing text only (Ultra doesn't take images) -> verdict, reasoning on
The number that matters: dangerous listings (banned or recalled, expected DANGER/WARNING) that the method calls OK.
Usage: python -m eval.chatbot_baseline
"""
from __future__ import annotations

import base64
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.ai.client import CallRecord, chat_json
from app.config import settings

ROOT = Path(__file__).resolve().parent.parent
LISTINGS = ROOT / "app/static/market/listings.json"
SCHEMA = {"type": "object", "properties": {"verdict": {"type": "string", "enum": ["DANGER", "WARNING", "CAUTION", "OK"]},
                                           "reason": {"type": "string"}}, "required": ["verdict", "reason"], "additionalProperties": False}
QUESTION = ("I'm thinking of buying this used baby item from a marketplace listing. Is it safe and legal to buy? "
            "Give a verdict: DANGER (banned, or recalled for a serious hazard), WARNING (safety agencies advise against it, e.g. expired), "
            "CAUTION (ask the seller something first, e.g. a possible recall depending on model number), or OK (no known issue).")


def ask(row: dict, mode: str) -> tuple[str, list[CallRecord]]:
    calls: list[CallRecord] = []
    text = f"Listing: {row['title']}. {row['text']}"
    try:
        if mode == "super_vl":
            img = (ROOT / "app" / row["image"].lstrip("/")).read_bytes()
            content = [{"type": "text", "text": QUESTION + "\n" + text},
                       {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(img).decode()}}]
            out = chat_json(settings.super_vl, [{"role": "user", "content": content}], schema=SCHEMA, purpose="Plain chatbot baseline",
                            reasoning=False, max_tokens=600, calls=calls)
        else:
            out = chat_json(settings.ultra, [{"role": "user", "content": QUESTION + "\n" + text}], schema=SCHEMA, purpose="Plain chatbot baseline",
                            reasoning=True, max_tokens=4000, calls=calls)
        return out["verdict"], calls
    except Exception as e:  # noqa: BLE001
        print("  failed", row["id"], mode, str(e)[:100])
        return "ERR", calls


def score(rows: list[dict], got: list[str]) -> dict:
    risky = [i for i, r in enumerate(rows) if r["expected_word"] in ("DANGER", "WARNING")]
    return {"exact": sum(g == r["expected_word"] for r, g in zip(rows, got)), "n": len(rows),
            "risky": len(risky), "risky_called_ok": sum(1 for i in risky if got[i] == "OK"),
            "risky_called_danger_or_warning": sum(1 for i in risky if got[i] in ("DANGER", "WARNING")),
            "ok_listings_called_danger": sum(1 for r, g in zip(rows, got) if r["expected_word"] == "OK" and g == "DANGER"),
            "per_listing": [{"id": r["id"], "expected": r["expected_word"], "got": g} for r, g in zip(rows, got)]}


def main() -> None:
    rows = json.loads(LISTINGS.read_text())
    out, cost = {}, {}
    for mode in ("super_vl", "ultra"):
        calls: list[CallRecord] = []
        with ThreadPoolExecutor(6) as ex:
            res = list(ex.map(lambda r: ask(r, mode), rows))
        for _, c in res:
            calls += c
        out[mode] = score(rows, [v for v, _ in res])
        cost[mode] = round(sum(c.cost_usd for c in calls), 4)
    cache = json.loads((ROOT / "data/market_cache.json").read_text())
    ours = [cache.get(r["id"], {}).get("word", "ERR") for r in rows]
    out["secondlook"] = score(rows, [w if w != "No known issues" else "OK" for w in ours])
    result = {"what": "24 marketplace listings (12 banned or recalled-for-deaths, 1 expired car seat, 5 ask-first, 6 fine)", "results": out, "cost_usd": cost}
    (ROOT / "eval" / "chatbot_baseline.json").write_text(json.dumps(result, indent=1))
    for k, v in out.items():
        print(f"{k:12s} exact {v['exact']}/{v['n']}  risky called OK {v['risky_called_ok']}/{v['risky']}  "
              f"risky flagged {v['risky_called_danger_or_warning']}/{v['risky']}  fine called DANGER {v['ok_listings_called_danger']}")


if __name__ == "__main__":
    main()
