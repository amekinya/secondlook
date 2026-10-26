"""10-minute platform check: confirms the assumptions RefundRadar is built on.

Run:  python -m scripts.smoke_test            (cheap checks, a few cents)
      python -m scripts.smoke_test --long     (adds a ~150K-token Ultra long-context test, ~$0.20)

Needs NEBIUS_API_KEY (and TAVILY_API_KEY for the Tavily check) in the environment.
Writes a Markdown report to stdout and, on GitHub Actions, to the job summary.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import traceback

from app.config import settings

results: list[tuple[str, str, str]] = []  # (check, status, detail)


def record(check: str, ok: bool | None, detail: str) -> None:
    status = "✅" if ok else ("⚠️" if ok is None else "❌")
    results.append((check, status, detail.replace("\n", " ")[:400]))
    print(f"{status} {check}: {detail}", flush=True)


def client():
    from openai import OpenAI

    return OpenAI(base_url=settings.nebius_base_url, api_key=settings.nebius_api_key, timeout=300)


def check_models(c) -> list[str]:
    models = c.models.list()
    ids = sorted(m.id for m in models.data)
    nv = [i for i in ids if "nvidia" in i.lower() or "nemotron" in i.lower()]
    record("List models", bool(ids), f"{len(ids)} models; NVIDIA/Nemotron: {', '.join(nv) or 'none'}")
    for spec in (settings.nano, settings.super_vl, settings.ultra):
        present = spec.model_id in ids
        guess = [i for i in nv if spec.role.split("_")[0] in i.lower()]
        record(
            f"Configured {spec.role} ID present",
            present,
            spec.model_id + ("" if present else f" NOT FOUND. Candidates: {guess}"),
        )
    return ids


def check_reasoning_toggle(c) -> None:
    for spec in (settings.nano, settings.ultra):
        for think in (False, True):
            try:
                t0 = time.perf_counter()
                r = c.chat.completions.create(
                    model=spec.model_id,
                    messages=[{"role": "user", "content": "What is 17*23? Reply with just the number."}],
                    max_tokens=1024,
                    temperature=0,
                    extra_body={"chat_template_kwargs": {"enable_thinking": think}},
                )
                dt = time.perf_counter() - t0
                msg = r.choices[0].message
                rc = getattr(msg, "reasoning_content", None) or (msg.model_extra or {}).get("reasoning_content")
                record(
                    f"{spec.role} thinking={think}",
                    "391" in (msg.content or ""),
                    f"answer={msg.content!r:.40} reasoning_chars={len(rc or '')} "
                    f"out_tokens={r.usage.completion_tokens} {dt:.1f}s",
                )
            except Exception as e:
                record(f"{spec.role} thinking={think}", False, repr(e))


def check_nano_json(c) -> None:
    """The cheap tier must keep doing strict JSON with reasoning off (it maps headers, checks news, reads recall notices)."""
    schema = {"type": "object", "properties": {"answer": {"type": "integer"}, "unit": {"type": "string", "enum": ["apples", "pears"]}},
              "required": ["answer", "unit"], "additionalProperties": False}
    try:
        r = c.chat.completions.create(
            model=settings.nano.model_id, max_tokens=300, temperature=0,
            messages=[{"role": "user", "content": "Tom has 17 apples and buys 23 more. How many apples? JSON only."}],
            response_format={"type": "json_schema", "json_schema": {"name": "out", "schema": schema, "strict": True}},
            extra_body={"chat_template_kwargs": {"enable_thinking": False}})
        out = json.loads(r.choices[0].message.content)
        record("nano strict JSON (reasoning off)", out.get("answer") == 40 and out.get("unit") == "apples", json.dumps(out))
    except Exception as e:
        record("nano strict JSON (reasoning off)", False, repr(e)[:300])


def _form_image_b64() -> str:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (900, 420), "white")
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 20)
    except Exception:
        f = ImageFont.load_default()
    lines = [
        "ENTRY SUMMARY  (CBP Form 7501)",
        "1. Filer Code/Entry No.: ABC-1234567-8      2. Entry Type: 01",
        "7. Entry Date: 04/14/2025                     6. Port Code: 3901",
        "29. HTSUS No.: 9903.01.25                    34. Duty: $1,250.00",
        "29. HTSUS No.: 8517.62.0090                  34. Duty: $0.00",
        "37. Duty Total: $1,250.00",
    ]
    for i, t in enumerate(lines):
        d.text((30, 30 + i * 55), t, fill="black", font=f)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def check_vision_json(c) -> None:
    schema = {
        "type": "object",
        "properties": {
            "entry_number": {"type": "string"},
            "entry_type": {"type": "string"},
            "entry_date": {"type": "string"},
            "hts_lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"hts": {"type": "string"}, "duty_usd": {"type": "number"}},
                    "required": ["hts", "duty_usd"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["entry_number", "entry_type", "entry_date", "hts_lines"],
        "additionalProperties": False,
    }
    try:
        r = c.chat.completions.create(
            model=settings.super_vl.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the entry summary fields as JSON."},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + _form_image_b64()}},
                    ],
                }
            ],
            response_format={"type": "json_schema", "json_schema": {"name": "entry", "schema": schema, "strict": True}},
            max_tokens=800,
            temperature=0,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        out = json.loads(r.choices[0].message.content)
        ok = out.get("entry_number", "").replace(" ", "") == "ABC-1234567-8" and any(
            abs(l.get("duty_usd", 0) - 1250) < 0.01 for l in out.get("hts_lines", [])
        )
        record("Super VL reads form image -> strict JSON", ok, json.dumps(out)[:300])
    except Exception as e:
        record("Super VL reads form image -> strict JSON", False, repr(e))


def check_long_context(c) -> None:
    filler = "The quarterly shipment log entry was routine and contained no anomalies. " * 12000
    needle = "SECRET CODE: the refund pathway for entry QQQ-7777777-1 is PHASE-TWO-BLUE."
    half = len(filler) // 2
    doc = filler[:half] + needle + filler[half:]
    try:
        t0 = time.perf_counter()
        r = c.chat.completions.create(
            model=settings.ultra.model_id,
            messages=[{"role": "user", "content": doc + "\n\nWhat is the refund pathway for entry QQQ-7777777-1?"}],
            max_tokens=200,
            temperature=0,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        ans = r.choices[0].message.content or ""
        record(
            "Ultra long context (~150K tokens)",
            "PHASE-TWO-BLUE" in ans,
            f"prompt_tokens={r.usage.prompt_tokens} answer={ans!r:.80} {time.perf_counter()-t0:.1f}s",
        )
    except Exception as e:
        record("Ultra long context (~150K tokens)", False, repr(e)[:300])


def check_tavily() -> None:
    if not settings.live_tavily:
        record("Tavily", None, "TAVILY_API_KEY not set; skipped")
        return
    try:
        from tavily import TavilyClient

        t = TavilyClient(api_key=settings.tavily_api_key)
        s = t.search("CBP CAPE IEEPA refund guidance", max_results=3, include_domains=["cbp.gov"])
        urls = [r["url"] for r in s.get("results", [])]
        record("Tavily search (cbp.gov)", bool(urls), ", ".join(urls))
        if urls:
            e = t.extract(urls=urls[:1])
            n = len((e.get("results") or [{}])[0].get("raw_content", "") or "")
            record("Tavily extract", n > 500, f"{n} chars from {urls[0]}")
    except Exception as e:
        record("Tavily", False, repr(e))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--long", action="store_true", help="also run the ~150K-token Ultra test")
    args = ap.parse_args()
    if not settings.live_models:
        print("NEBIUS_API_KEY is not set.")
        return 2
    c = client()
    try:
        check_models(c)
    except Exception:
        record("List models", False, traceback.format_exc()[-300:])
    check_reasoning_toggle(c)
    check_nano_json(c)
    check_vision_json(c)
    if args.long:
        check_long_context(c)
    check_tavily()

    md = ["## RefundRadar platform smoke test", "", "| Check | Result | Detail |", "|---|---|---|"]
    md += [f"| {a} | {b} | {c_.replace('|', '/')} |" for a, b, c_ in results]
    report = "\n".join(md)
    print("\n" + report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write(report + "\n")
    return 0 if all(s != "❌" for _, s, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
