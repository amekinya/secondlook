"""Automated UI audit: axe-core accessibility checks + color-vision-deficiency screenshots.

Usage: python tests/ui_audit.py http://localhost:8000 /path/to/axe.min.js out_dir [path ...]
Runs each page at phone (390px) and desktop (1280px) widths. For pages with a scan, it runs the scan first so
stamps are audited too. Writes axe results JSON and protanopia/deuteranopia/achromatopsia screenshots.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

VISION = ["protanopia", "deuteranopia", "tritanopia", "achromatopsia"]


async def audit(base: str, axe_path: str, out: Path, paths: list[str]) -> int:
    out.mkdir(parents=True, exist_ok=True)
    axe = Path(axe_path).read_text()
    serious = 0
    report = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for path in paths:
            for name, vp in (("phone", {"width": 390, "height": 844}), ("desktop", {"width": 1280, "height": 900})):
                pg = await b.new_page(viewport=vp)
                await pg.goto(base + path)
                await pg.wait_for_timeout(1200)
                if await pg.locator(".sl-btn").count():
                    await pg.click(".sl-btn")
                    await pg.wait_for_timeout(2500)
                if await pg.locator("#sampleBtn").count():
                    await pg.click("#sampleBtn")
                    await pg.wait_for_timeout(2500)
                await pg.add_script_tag(content=axe)
                res = await pg.evaluate("""async () => { const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});
                    return r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length, sample: v.nodes.slice(0,3).map(n => n.target.join(' '))})); }""")
                key = f"{path} [{name}]"
                report[key] = res
                serious += sum(1 for v in res if v["impact"] in ("serious", "critical"))
                if name == "desktop":
                    cdp = await pg.context.new_cdp_session(pg)
                    tag = path.strip("/").replace("/", "_") or "home"
                    for v in VISION:
                        await cdp.send("Emulation.setEmulatedVisionDeficiency", {"type": v})
                        await pg.screenshot(path=str(out / f"{tag}_{v}.png"))
                    await cdp.send("Emulation.setEmulatedVisionDeficiency", {"type": "none"})
                await pg.close()
        await b.close()
    (out / "axe.json").write_text(json.dumps(report, indent=1))
    for k, vs in report.items():
        print(k, "->", "no violations" if not vs else "; ".join(f"{v['impact']}: {v['id']} ({v['nodes']})" for v in vs))
    return serious


if __name__ == "__main__":
    base, axe_path, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    paths = sys.argv[4:] or ["/"]
    n = asyncio.run(audit(base, axe_path, out, paths))
    print(f"serious/critical violations: {n}")
    sys.exit(1 if n else 0)
