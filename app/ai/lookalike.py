"""Look-alike recall finder: our fine-tuned NVIDIA llama-nemotron-rerank-1b-v2, served on a Nebius Serverless Endpoint.

Recalled products are often resold with no brand, or under a different made-up brand, so brand and model matching
never finds them. The matcher reads the listing (title, text and what the photo shows) against every recall notice of
the same kind of product and scores how likely the listing IS that recalled product. It only proposes candidates:
Nemotron 3 Ultra still reads each notice, and code decides (a look-alike alone is never more than CAUTION).
"""
from __future__ import annotations

import time

import httpx

from app.ai.client import CallRecord, LiveModelUnavailable
from app.config import settings


def available() -> bool:
    return bool(settings.endpoint_url)


def passage(r: dict) -> str:
    """How a recall notice is shown to the matcher (must match scripts/build_lookalike_pairs.py)."""
    prods = "; ".join(r.get("products", [])[:4])
    return f"{r['title']}. Products: {prods}. {r.get('description', '')[:700]}"


def query(title: str, text: str, looks: str) -> str:
    return f"Listing: {title}. {text[:600]} Photo shows: {looks[:300]}".strip()


def score(pairs: list[tuple[str, str]], model: str | None = None, calls: list[CallRecord] | None = None, timeout: float = 20) -> list[float]:
    if not available():
        raise LiveModelUnavailable("ENDPOINT_URL not set")
    headers = {"Authorization": f"Bearer {settings.endpoint_token}"} if settings.endpoint_token else {}
    t0 = time.perf_counter()
    out: list[float] = []
    try:
        with httpx.Client(timeout=timeout) as c:
            for i in range(0, len(pairs), 2048):
                r = c.post(settings.endpoint_url.rstrip("/") + "/score", headers=headers,
                           json={"model": model or settings.lookalike_model, "pairs": [list(p) for p in pairs[i:i + 2048]]})
                if r.status_code != 200:
                    raise LiveModelUnavailable(f"matcher HTTP {r.status_code}: {r.text[:200]}")
                out += r.json()["scores"]
    except httpx.HTTPError as e:
        raise LiveModelUnavailable(f"matcher unreachable: {e}") from e
    if calls is not None:
        calls.append(CallRecord("matcher", f"{model or settings.lookalike_model} (Nebius endpoint)", time.perf_counter() - t0, len(pairs), 0, 0, 0.0,
                                "Look-alike recall search"))
    return out


def pool(category: str) -> list[dict]:
    from app.engine.recalls import RELATED, cpsc  # noqa: PLC0415

    cats = RELATED.get(category, {category})
    return [r for r in cpsc() if r["category"] in cats]


def find(category: str, title: str, text: str, looks: str, calls: list[CallRecord] | None = None, k: int = 3,
         threshold: float | None = None, model: str | None = None) -> list[dict]:
    """-> [{id, score}] for the k best look-alike recalls scoring at or above the threshold."""
    if category in ("", "other", "car_seat"):
        return []
    cands = pool(category)
    if not cands:
        return []
    q = query(title, text, looks)
    scores = score([(q, passage(r)) for r in cands], model=model, calls=calls)
    th = settings.lookalike_threshold if threshold is None else threshold
    ranked = sorted(zip(cands, scores), key=lambda x: -x[1])[:k]
    return [{"id": r["id"], "score": round(s, 4)} for r, s in ranked if s >= th]


def for_item(item, calls: list[CallRecord] | None = None) -> list[dict]:
    """Look-alikes for an assessed Item; empty when the endpoint is off or unreachable (the app works without it)."""
    if not available() or item.category in ("", "other", "car_seat"):
        return []
    try:
        return find(item.category, item.product_name, item.listing_text, item.looks, calls)
    except LiveModelUnavailable:
        return []
