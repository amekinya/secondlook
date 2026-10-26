"""Synthetic marketplace listings of recalled products, for training and testing the look-alike recall matcher.

For each CPSC recall in our index, a writer model from a DIFFERENT family than the Nemotron models SecondLook uses
writes how real sellers list that exact product: once with the brand, once with no brand ("baby lounger, barely used"),
and once under a made-up marketplace brand (the same product resold under another name). It also writes two
"distractor" listings: the same kind of product but clearly a different design, which must NOT match this recall.
Each listing includes what a photo would show, as a vision model would describe it.
Recalls are split by id (train 70% / dev 15% / test 15%), so test recalls are never seen in training.
Usage: python -m scripts.synth_lookalikes --split trainval [--generator MODEL] [--limit N]
       python -m scripts.synth_lookalikes --split test --generator <a different model>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.ai.client import CallRecord, LiveModelUnavailable, _get_client, chat_json
from app.config import ModelSpec
from app.engine.recalls import cpsc

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "lookalike"
PREFERRED = ["deepseek-ai/DeepSeek-V4.1-Flash-1017", "Qwen/Qwen3-30B-A3B-Instruct-2507", "zai-org/GLM-5.2", "MiniMaxAI/MiniMax-M3"]
LISTING = {"type": "object", "properties": {"title": {"type": "string"}, "text": {"type": "string"},
                                            "photo": {"type": "string", "description": "what the listing photo shows, 1-2 sentences, as a vision model would describe it; no brand names unless printed on the product"}},
           "required": ["title", "text", "photo"], "additionalProperties": False}
SCHEMA = {"type": "object", "properties": {
    "branded": LISTING, "unbranded": LISTING, "rebranded": LISTING,
    "rebrand_name": {"type": "string"},
    "distractors": {"type": "array", "items": LISTING, "description": "2 listings of the same kind of product with a clearly different design"}},
    "required": ["branded", "unbranded", "rebranded", "rebrand_name", "distractors"], "additionalProperties": False}


def split_of(rid: str) -> str:
    h = int(hashlib.sha1(rid.encode()).hexdigest(), 16) % 100
    return "train" if h < 70 else "dev" if h < 85 else "test"


def pick_generator(name: str | None) -> ModelSpec:
    ids = {m.id for m in _get_client().models.list().data}
    for mid in ([name] if name else []) + PREFERRED:
        if mid in ids:
            return ModelSpec("generator", mid, 0.5, 1.5)
    raise SystemExit(f"No generator model available; have: {sorted(ids)[:40]}")


def write(r: dict, gen: ModelSpec) -> tuple[list[dict], list[CallRecord]]:
    calls: list[CallRecord] = []
    notice = {"title": r["title"], "products": r.get("products", [])[:4], "models": r.get("models", [])[:6], "description": r.get("description", "")[:1500]}
    prompt = (
        "Here is a U.S. CPSC recall notice for a baby or children's product:\n" + json.dumps(notice) + "\n\n"
        "Write realistic second-hand marketplace listings (Facebook Marketplace, Craigslist, Mercari style: short, casual, sometimes typos, "
        "price and condition, pickup details). Sellers usually don't know about the recall and never mention it.\n"
        "- branded: the recalled product, naming the brand and product the way a seller would (model number only sometimes).\n"
        "- unbranded: the same recalled product, but the seller doesn't know or mention the brand or model; describe it by what it is and looks like.\n"
        "- rebranded: the same recalled product sold under a different, made-up marketplace brand (like 'QIYUELI' or 'Bebamour'); give that name in rebrand_name.\n"
        "- distractors: two listings of the SAME KIND of product (same category) that are clearly a different design, so they are NOT this recalled product.\n"
        "For each, 'photo' says what a photo shows (shape, colors, prints, parts) as a vision model would describe it.")
    try:
        out = chat_json(gen, [{"role": "user", "content": prompt}], schema=SCHEMA, purpose="Synthetic recall listings", reasoning=False,
                        max_tokens=2500, temperature=0.8, calls=calls, enforce_cap=False)
    except (LiveModelUnavailable, Exception) as e:  # noqa: BLE001
        print(f"  {r['id']} failed: {str(e)[:120]}")
        return [], calls
    base = {"recall": r["id"], "category": r["category"], "split": split_of(r["id"]), "generator": gen.model_id}
    rows = []
    for style in ("branded", "unbranded", "rebranded"):
        x = out.get(style) or {}
        if x.get("title"):
            rows.append(base | {"style": style, "title": x["title"], "text": x["text"], "photo": x["photo"], "match": True,
                                "brand": out.get("rebrand_name", "") if style == "rebranded" else ""})
    for x in (out.get("distractors") or [])[:2]:
        if x.get("title"):
            rows.append(base | {"style": "distractor", "title": x["title"], "text": x["text"], "photo": x["photo"], "match": False, "brand": ""})
    return rows, calls


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="trainval", choices=["trainval", "test"])
    ap.add_argument("--generator", default=None)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    gen = pick_generator(a.generator)
    print("generator:", gen.model_id)
    want = {"train", "dev"} if a.split == "trainval" else {"test"}
    recalls = [r for r in cpsc() if split_of(r["id"]) in want and r["category"] not in ("car_seat",)]
    if a.limit:
        recalls = recalls[: a.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    rows, calls = [], []
    with ThreadPoolExecutor(10) as ex:
        for rs, c in ex.map(lambda r: write(r, gen), recalls):
            rows += rs
            calls += c
    f = OUT / f"listings_{a.split}.jsonl"
    f.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
    print(f"{len(recalls)} recalls -> {len(rows)} listings -> {f}; {len(calls)} calls, ${sum(c.cost_usd for c in calls):.3f}")


if __name__ == "__main__":
    main()
