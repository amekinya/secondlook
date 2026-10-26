"""SecondLook web app. Stateless: nothing uploaded is stored."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.ai import tasks
from app.ai.client import CallRecord, LiveModelUnavailable, ledger
from app.config import settings
from app.engine import catalog as C
from app.engine.assess import Item, assess
from app.engine.recalls import find_brand

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
LISTINGS = ROOT / "data" / "listings"
DEMO_TODAY = date(2026, 10, 25)

app = FastAPI(title="SecondLook")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
MAX = 12 * 1024 * 1024

BRANDS = ["Fisher-Price", "Graco", "Chicco", "Evenflo", "Britax", "Boppy", "4moms", "Bumbo", "Delta", "Stork Craft", "Storkcraft", "Kids2",
          "Kids II", "Ingenuity", "Bright Starts", "Safety 1st", "Maxi-Cosi", "Nuna", "UPPAbaby", "Baby Trend", "Summer Infant", "Dream On Me",
          "Munchkin", "Skip Hop", "Halo", "Owlet", "Cosco", "Clek", "Peg Perego", "Joovy", "Cybex", "Doona", "Joie", "Vevor", "Costway",
          "Simplicity", "Kolcraft", "Angelcare", "Infantino", "Nap Nanny", "DockATot", "Baby Delight", "Dorel", "Little Tikes"]
CAT_RX = [(c, rx) for c, rx in [
    ("inclined_sleeper", r"rock ?'?n ?play|inclined sleep|rocking sleeper|napper"), ("crib_bumper", r"bumper|slat cover|crib liner"),
    ("high_chair", r"high ?chair"), ("car_seat", r"car ?seat|booster car"), ("swing", r"\bswing\b|glider"), ("crib", r"\bcrib\b"), ("bassinet", r"bassinet|cradle|bedside sleeper|co-?sleeper"),
    ("in_bed_sleeper", r"baby nest|in-bed sleeper|sleep pod|dockatot"), ("play_yard", r"play ?yard|pack ?'?n ?play|playpen"),
    ("lounger", r"lounger|positioner"), ("nursing_pillow", r"nursing pillow"),
    ("bouncer_rocker", r"bouncer|rocker|bumbo|floor seat"), ("walker", r"walker|activity center"), ("bath", r"bath seat|bath tub|bathtub"),
    ("high_chair", r"high ?chair"), ("stroller", r"stroller"), ("carrier", r"carrier|sling"), ("sleep_sack", r"sleep sack|swaddle")]]


def _demo_cache() -> dict:
    try:
        return json.loads((LISTINGS / "demo_cache.json").read_text())
    except Exception:
        return {}


def _calls_json(calls: list[CallRecord]) -> list[dict]:
    return [asdict(c) | {"seconds": round(c.seconds, 2), "cost_usd": round(c.cost_usd, 5)} for c in calls]


def item_from_text(text: str) -> Item:
    """Rule-based fallback when the vision model isn't available: read the listing text only."""
    t = text.lower()
    cat = next((c for c, rx in CAT_RX if re.search(rx, t)), "other")
    brand = next((b for b in BRANDS if b.lower() in t), "") or find_brand(text)
    feats = {}
    if re.search(r"\bdrop(s|ping)?\b|side (slides|drops)", t):
        feats["drop_side"] = True
    if re.search(r"bumper", t):
        feats["padded_bumper"] = True
    if re.search(r"\bsleep|\bnap", t):
        feats["marketed_for_sleep"] = True
    if re.search(r"headrest|insert", t) and cat == "swing":
        feats["snuga_headrest_present"] = True
    if re.search(r"suction", t):
        feats["suction_cups"] = True
    if re.search(r"(restraint|safety) belt|belt (is )?installed", t) and cat == "bouncer_rocker":
        feats["bumbo_belt_present"] = True
    dom = None
    m = re.search(r"(?:manufactured|made|mfd|date)\D{0,25}(\d{1,2})\s*/\s*(\d{4})", t)
    if m:
        dom = date(int(m.group(2)), int(m.group(1)), 1)
    models = " ".join(re.findall(r"\b(?=[A-Z0-9-]*\d)[A-Z]{1,5}-?\d{2,7}[A-Z0-9]*\b", text))
    return Item(category=cat, brand=brand, model_text=models, product_name="", listing_text=text[:3000], dom=dom, features=feats)


def run_check(item: Item, today: date, calls: list[CallRecord], steps: list[dict], cached: dict | None = None) -> dict:
    first = assess(item, today)
    steps.append({"step": "Checked bans, standards and recalls", "detail": f"{len(first['recalls'])} recall candidates from CPSC/NHTSA data", "model": None})
    judgments: dict[str, str] = {}
    why: dict[str, str] = {}
    to_judge = [r for r in first["recalls"] if r["match"] == "possible" or not r.get("all_models")]
    if cached and "judgments" in cached:
        js = cached["judgments"]
    elif to_judge:
        try:
            js = tasks.judge_recalls(item, to_judge, calls)
        except LiveModelUnavailable:
            js = []
    else:
        js = []
    for j in js:
        judgments[j["recall_id"]] = j["verdict"]
        why[j["recall_id"]] = j["why"]
    if js:
        steps.append({"step": "Read the recall notices", "detail": f"{len(js)} recalls checked against this item", "model": settings.ultra.model_id})
    result = assess(item, today, judgments)
    result["judgments_raw"] = js
    for rc in result["recalls"]:
        rc["why"] = why.get(rc["id"], "")
    if cached and "verdict" in cached:
        result["writeup"] = cached["verdict"]
    else:
        try:
            result["writeup"] = tasks.write_verdict(result, calls)
            steps.append({"step": "Wrote your summary and seller message", "detail": "", "model": settings.ultra.model_id})
        except LiveModelUnavailable:
            result["writeup"] = tasks.write_verdict_fallback(result)
        except Exception:
            result["writeup"] = tasks.write_verdict_fallback(result)
    if cached and "news" in cached:
        result["news"] = cached["news"]
    else:
        try:
            result["news"] = tasks.recall_news(item, [r["id"] for r in result["recalls"]], calls)
            if result["news"].get("checked"):
                steps.append({"step": "Searched recent recall news", "detail": result["news"].get("query", ""), "model": "Tavily + " + settings.nano.model_id})
        except Exception:
            result["news"] = {"checked": False}
    return result


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"live_models": settings.live_models, "live_tavily": settings.live_tavily, "spend_remaining_today": round(ledger.remaining(), 4),
            "models": {s.role: s.model_id for s in (settings.nano, settings.super_vl, settings.ultra)},
            "rules_verified_as_of": C.RULES_VERIFIED_AS_OF.isoformat()}


@app.get("/api/samples")
def samples():
    meta = json.loads((LISTINGS / "listings.json").read_text())
    return [{k: m[k] for k in ("file", "title", "price")} | {"url": f"/api/samples/{m['file']}"} for m in meta]


@app.get("/api/samples/{name}")
def sample_image(name: str):
    p = LISTINGS / Path(name).name
    if not p.exists() or p.suffix != ".png":
        raise HTTPException(404)
    return FileResponse(p, media_type="image/png")


@app.post("/api/check")
async def check(images: list[UploadFile] | None = File(None), text: str = Form(""), url: str = Form(""), sample: str = Form("")):
    calls: list[CallRecord] = []
    steps: list[dict] = []
    imgs: list[tuple[bytes, str]] = []
    cached = None
    today = date.today()

    if sample:
        meta = {m["file"]: m for m in json.loads((LISTINGS / "listings.json").read_text())}
        if sample not in meta:
            raise HTTPException(404, "Unknown sample.")
        imgs.append(((LISTINGS / sample).read_bytes(), "image/png"))
        cached = _demo_cache().get(sample)
        today = DEMO_TODAY
    for f in images or []:
        if not f.filename:
            continue
        data = await f.read()
        if len(data) > MAX:
            raise HTTPException(413, f"{f.filename} is too large (12 MB max).")
        imgs.append((data, f.content_type or "image/jpeg"))
    extra = text.strip()
    if url.strip():
        try:
            ex = tasks.extract_listing(url.strip())
            extra = (extra + "\n" + ex["text"]).strip()
            steps.append({"step": "Read the listing page", "detail": url.strip()[:80], "model": "Tavily Extract"})
        except Exception:
            steps.append({"step": "Couldn't read that link", "detail": "Many marketplaces need a login. Paste a screenshot or the listing text instead.", "model": None})
    if not imgs and not extra:
        raise HTTPException(400, "Add a screenshot, a photo, a listing link or the listing text.")

    ident = None
    if cached and "identify" in cached:
        ident = cached["identify"]
        steps.append({"step": "Looked at the listing", "detail": "Product, brand, labels and visible features", "model": settings.super_vl.model_id})
    elif imgs:
        try:
            ident = tasks.identify(imgs, extra, calls)
            steps.append({"step": "Looked at the listing", "detail": "Product, brand, labels and visible features", "model": settings.super_vl.model_id})
        except LiveModelUnavailable:
            ident = None
        except Exception as e:
            steps.append({"step": "Vision model didn't respond", "detail": type(e).__name__, "model": settings.super_vl.model_id})
    if ident:
        item = tasks.item_from_identify(ident, extra if not sample else "")
    else:
        meta_text = ""
        if sample:
            m = {x["file"]: x for x in json.loads((LISTINGS / "listings.json").read_text())}[sample]
            meta_text = f"{m['title']}. {m['text']}"
        item = item_from_text(" ".join(x for x in [meta_text, extra] if x))
        steps.append({"step": "Read the listing text", "detail": "Photo reading unavailable right now; used the words only", "model": None})

    result = run_check(item, today, calls, steps, cached)
    result["what_i_see"] = (ident or {}).get("what_i_see", "")
    result["pipeline"] = steps
    result["calls"] = (cached or {}).get("calls", []) if cached else _calls_json(calls)
    result["sample"] = bool(sample)
    return JSONResponse(result)


# --- Page scan (marketplace overlay / browser extension) -------------------------------------
from fastapi import Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402

from app import scan  # noqa: E402

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])
MARKET = STATIC / "market"


@app.get("/market")
def market_page():
    return FileResponse(STATIC / "market.html")


@app.get("/api/market/listings")
def market_listings():
    rows = json.loads((MARKET / "listings.json").read_text())
    return [{k: r[k] for k in ("id", "title", "price", "place", "text", "image")} for r in rows]


@app.post("/api/scan")
async def scan_page(request: Request):
    body = await request.json()
    listings = [l for l in (body.get("listings") or [])[:60] if isinstance(l, dict)]
    if not listings:
        raise HTTPException(400, "No listings found on this page.")
    demo = bool(body.get("demo"))
    today = DEMO_TODAY if demo else date.today()
    return StreamingResponse(scan.stream_scan(listings, today, prefer_cache=demo and not body.get("force_live")),
                             media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/listing")
async def listing_detail(request: Request):
    """Full check of one listing (Ultra reads recall notices + writes the summary)."""
    body = await request.json()
    calls: list[CallRecord] = []
    steps: list[dict] = []
    demo = bool(body.get("demo"))
    today = DEMO_TODAY if demo else date.today()
    lid = body.get("id", "")
    cache = scan._cache().get(lid, {}) if demo else {}
    text = f"{body.get('title', '')}. {body.get('text', '')}".strip()
    ident = cache.get("identify")
    if ident is None:
        try:
            img = scan.load_image(body.get("image", ""))
            if img:
                ident = tasks.identify([img], text, calls)
                steps.append({"step": "Looked at the listing", "detail": "", "model": settings.super_vl.model_id})
        except Exception:
            ident = None
    item = tasks.item_from_identify(ident, text) if ident else item_from_text(text)
    result = run_check(item, today, calls, steps, cache.get("detail"))
    result["pipeline"] = steps
    result["calls"] = cache.get("calls", []) if cache else _calls_json(calls)
    return JSONResponse(result)
