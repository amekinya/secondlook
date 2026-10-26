"""Parallel page scan: many listings in, one stamp per listing streamed back as each finishes.

Per listing: Nemotron 3.5 Super VL reads the photo + text (fast, no reasoning) -> deterministic rules + recall index.
Ultra only runs when the user opens a listing (detail view), so a 30-listing page scans in seconds and costs cents.
Results stream as Server-Sent Events so the page can stamp listings live with a running counter and cost meter.
"""
from __future__ import annotations

import ipaddress
import json
import queue
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.ai import tasks
from app.ai.client import CallRecord, LiveModelUnavailable, ledger
from app.config import settings
from app.engine import catalog as C
from app.engine.assess import assess

STATIC = Path(__file__).resolve().parent / "static"
CACHE = Path(__file__).resolve().parents[1] / "data" / "market_cache.json"
WORKERS = 8
MAX_IMG = 8 * 1024 * 1024


def _cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}


def _safe_url(url: str) -> bool:
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return False
    try:
        for info in socket.getaddrinfo(u.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except Exception:
        return False
    return True


def load_image(src: str) -> tuple[bytes, str] | None:
    """Local /static path, data: URL or public http(s) URL -> (bytes, mime). Guards against SSRF and huge files."""
    if not src:
        return None
    if src.startswith("/static/"):
        p = (STATIC / src[len("/static/"):]).resolve()
        if STATIC.resolve() in p.parents and p.exists():
            return p.read_bytes(), "image/png" if p.suffix == ".png" else "image/jpeg"
        return None
    if src.startswith("data:image/"):
        import base64

        head, _, b64 = src.partition(",")
        return base64.b64decode(b64)[:MAX_IMG], head[5:].split(";")[0]
    if not _safe_url(src):
        return None
    with httpx.Client(timeout=8, follow_redirects=True) as c:
        r = c.get(src, headers={"User-Agent": "SecondLook/0.1 (safety check)"})
        if r.status_code != 200 or len(r.content) > MAX_IMG:
            return None
        return r.content, r.headers.get("content-type", "image/jpeg").split(";")[0]


def _stamp(res: dict) -> dict:
    top = res["reasons"][0]
    definite = [r for r in res["recalls"] if r["match"] == "definite" and not r.get("remedied")]
    return {"level": res["level"], "label": res["label"], "tone": res["tone"], "word": res["word"],
            "headline": top["title"], "category": res["category_label"], "brand": res["item"]["brand"],
            "recalls": [r["id"] for r in definite][:3], "cite": top["cite"], "deaths": max((r.get("deaths") or 0) for r in res["reasons"])}


def scan_one(listing: dict, today: date, live: bool) -> dict:
    """Returns the stamp plus timing/cost; never raises."""
    from app.main import item_from_text  # noqa: PLC0415

    t0 = time.perf_counter()
    calls: list[CallRecord] = []
    text = f"{listing.get('title', '')}. {listing.get('text', '')}".strip()
    mode = "rules"
    ident = None
    if live:
        try:
            img = load_image(listing.get("image", ""))
            if img:
                ident = tasks.identify([img], text, calls)
                mode = "live"
        except LiveModelUnavailable:
            ident = None
        except Exception:
            ident = None
    item = tasks.item_from_identify(ident, text) if ident else item_from_text(text)
    res = assess(item, today)
    possible = [r for r in res["recalls"] if r["match"] == "possible"]
    if possible and live:  # Nemotron Nano reads the candidate notices (fast); Ultra re-checks on the detail view
        try:
            js = tasks.judge_recalls(item, possible, calls, quick=True)
            res = assess(item, today, {j["recall_id"]: j["verdict"] for j in js})
        except Exception:
            pass
    return {"id": listing.get("id"), **_stamp(res), "mode": mode, "seconds": round(time.perf_counter() - t0, 2),
            "cost_usd": round(sum(c.cost_usd for c in calls), 5), "model": settings.super_vl.model_id if mode == "live" else "rules"}


def stream_scan(listings: list[dict], today: date, prefer_cache: bool):
    """Generator of SSE lines."""
    cache = _cache() if prefer_cache else {}
    live = settings.live_models and ledger.remaining() > 0.05
    q: queue.Queue = queue.Queue()
    start = time.perf_counter()
    total = len(listings)

    def replay(item: dict, delay: float):
        time.sleep(delay)
        q.put(item)

    cached_items = [l for l in listings if l.get("id") in cache]
    fresh = [l for l in listings if l.get("id") not in cache]
    mode = "recorded" if cached_items and not fresh else ("live" if live else "rules")
    yield f"event: start\ndata: {json.dumps({'total': total, 'mode': mode, 'model': settings.super_vl.model_id, 'workers': WORKERS})}\n\n"

    threads = []
    for l in cached_items:  # replay a recorded live scan with its real per-listing timing (8 parallel lanes)
        rec = cache[l["id"]]
        threads.append(threading.Thread(target=replay, args=({**rec, "mode": "recorded"}, rec.get("finished_at", rec.get("seconds", 1.0))), daemon=True))
    for t in threads:
        t.start()
    pool = ThreadPoolExecutor(max_workers=WORKERS)
    for l in fresh:
        pool.submit(lambda x=l: q.put(scan_one(x, today, live)))

    done = 0
    cost = 0.0
    flagged = 0
    while done < total:
        try:
            item = q.get(timeout=90)
        except queue.Empty:
            break
        done += 1
        cost += item.get("cost_usd", 0.0)
        flagged += item["word"] in ("DANGER", "WARNING")
        item["progress"] = {"done": done, "total": total, "flagged": flagged, "cost_usd": round(cost, 4),
                            "elapsed": round(time.perf_counter() - start, 1)}
        yield f"event: stamp\ndata: {json.dumps(item)}\n\n"
    pool.shutdown(wait=False)
    yield f"event: done\ndata: {json.dumps({'done': done, 'total': total, 'flagged': flagged, 'cost_usd': round(cost, 4), 'elapsed': round(time.perf_counter() - start, 1), 'rules_verified_as_of': C.RULES_VERIFIED_AS_OF.isoformat()})}\n\n"
