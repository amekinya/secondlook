"""Build the demo marketplace ("Swapboard", an invented, clearly-labeled demo site).

Problem listings use photos from U.S. CPSC recall notices (CPSC permits copying recall photos).
Safe listings use Pexels photos (Pexels license: free to use). The car-seat label is synthetic.
Each listing has an expected verdict, so the page doubles as a benchmark.

Output: app/static/market/img/*.jpg and app/static/market/listings.json
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "app" / "static" / "market"
CPSC = ROOT / "cpsc_images"
STOCK = ROOT / "stock"

# (image source, title, price, place, seller text, expected level, truth note)
L = [
    ("cpsc:eval_19105", "Rock 'n Play sleeper, barely used", "$25", "Naperville", "Fisher-Price rocking sleeper, baby slept in it every night for 3 months. Folds flat for travel.", "ILLEGAL_TO_SELL", "Inclined sleeper, banned; recall 19105"),
    ("pexels:4713256", "White crib, fixed sides, great condition", "$90", "Wheaton", "Convertible crib, fixed sides, bought new in 2021. Label on the back. Mattress not included.", "CHECK", "No issue visible; ask for label"),
    ("cpsc:demo_26169", "Braided crib bumper set (gray/mint/pink)", "$15", "Lisle", "Soft braided bumpers, tie around the crib slats. Keeps arms and legs from getting stuck.", "ILLEGAL_TO_SELL", "Padded crib bumper, banned"),
    ("pexels:5789135", "Lightweight umbrella stroller", "$35", "Aurora", "Gray stroller with canopy, 5-point harness, folds easily. Great for travel.", "OK_SO_FAR", "No recall matched"),
    ("cpsc:eval_21198", "Boppy newborn lounger, floral", "$18", "Downers Grove", "Boppy lounger, perfect for newborn naps and tummy time. Washable cover.", "RECALLED", "Boppy Newborn Lounger, recall 21198"),
    ("pexels:3875217", "Wooden baby play gym with hanging toys", "$30", "Naperville", "Montessori style wooden activity gym, natural wood with felt toys.", "OK_SO_FAR", "Infant toy, no recall matched"),
    ("cpsc:demo_25009", "Fisher-Price Snugabunny cradle swing", "$35", "Wheaton", "Cradle 'n swing with the bunny headrest and insert. Model V0099. All settings work.", "RECALLED", "Snuga swing recall 25009, remedy not done"),
    ("cpsc:demo_10046", "Solid wood crib, side drops down", "$60", "Bolingbrook", "Older crib but sturdy. Front side slides down so it's easy to lift baby out.", "ILLEGAL_TO_SELL", "Drop-side crib"),
    ("pexels:29564428", "White high chair with tray", "$40", "Lisle", "Easy-clean high chair, adjustable tray, 5-point harness. Smoke-free home.", "OK_SO_FAR", "No recall matched"),
    ("cpsc:eval_26591", "VEVOR baby lounger, snow deer print", "$20", "Aurora", "Cozy baby lounger nest, great for naps on the couch or bed.", "RECALLED", "VEVOR lounger recall 26591"),
    ("cpsc:eval_22200", "4moms MamaRoo infant seat", "$70", "Naperville", "MamaRoo with all 5 motions and sounds, 3-point harness. Works perfectly.", "RECALLED", "MamaRoo 3-point recall 22200 (strap fastener)"),
    ("pexels:2138133", "Woven baby wrap carrier", "$22", "Downers Grove", "Long woven wrap, navy and red stripes. Used for one baby.", "OK_SO_FAR", "No recall matched"),
    ("cpsc:eval_19177", "Eddie Bauer rocking bassinet", "$45", "Wheaton", "Slumber & Soothe rock bassinet, gently rocks and has a hood. Baby slept great in it.", "ILLEGAL_TO_SELL", "Inclined sleeper recall 19177"),
    ("cpsc:demo_12247", "Bumbo floor seat with safety belt", "$12", "Lisle", "Bumbo seat in good shape, restraint belt installed. Great for sitting practice.", "OK_SO_FAR", "Bumbo recall 12247, belt fix done"),
    ("cpsc:eval_22768", "Infant bath seat with suction cups", "$10", "Bolingbrook", "Bath seat that suctions to the tub so baby can sit up in the bath. Blue.", "CHECK", "Unbranded suction-cup bath seat; ask the brand (Yuboloo recall 22768)"),
    ("pexels:7028060", "Natural pine crib (fixed sides)", "$75", "Naperville", "Solid pine crib, fixed sides, from a smoke-free home. Assembly instructions included.", "CHECK", "No issue visible; ask for label"),
    ("cpsc:eval_20730", "Baby walker with toy tray", "$25", "Aurora", "Kids & Koalas walker, folds flat, music and lights on the tray.", "RECALLED", "Kids & Koalas walker recall 20730"),
    ("cpsc:demo_26074", "Electric baby swing with mosquito net", "$40", "Downers Grove", "Swing / rocker with remote and net. My son napped in it every day. Model BB501.", "ILLEGAL_TO_SELL", "Vevor swing recall 26074 (inclined sleep)"),
    ("pexels:25797471", "Full-size stroller, gray", "$55", "Wheaton", "Reclining seat, big basket, adjustable handle. Some wear on the wheels.", "OK_SO_FAR", "No recall matched"),
    ("cpsc:eval_24153", "3-in-1 high chair and booster", "$30", "Lisle", "SINGES high chair, converts to booster seat. Clean and folds.", "RECALLED", "SINGES high chair recall 24153"),
    ("cpsc:eval_27027", "Bedside sleeper / bassinet", "$50", "Bolingbrook", "Papablic convertible bedside sleeper, attaches to the side of your bed.", "RECALLED", "Papablic bedside sleeper recall 27027"),
    ("synth:carseat", "Evenflo convertible car seat", "$30", "Naperville", "Rear or forward facing, clean cover. Sticker from the bottom in the photo.", "UNSAFE_ADVISORY", "Made 03/2015, Evenflo 10-yr life, expired"),
    ("pexels:7708639", "Convertible car seat (installed photo)", "$45", "Aurora", "Car seat in great shape, no stains. Comes with manual.", "CHECK", "Car seat: labels and crash history needed"),
    ("cpsc:eval_25456", "Baby lounger, grey feather", "$15", "Downers Grove", "URMYWO newborn lounger, soft and portable.", "RECALLED", "URMYWO lounger recall 25456"),
]


WORD = {"ILLEGAL_TO_SELL": "DANGER", "RECALLED": "DANGER", "UNSAFE_ADVISORY": "WARNING", "CHECK": "CAUTION", "OK_SO_FAR": "OK"}


def save(img: Image.Image, name: str) -> str:
    img = img.convert("RGB")
    img.thumbnail((640, 640))
    canvas = Image.new("RGB", (640, 640), "white")
    canvas.paste(img, ((640 - img.width) // 2, (640 - img.height) // 2))
    p = OUT / "img" / f"{name}.jpg"
    canvas.save(p, quality=84)
    return f"/static/market/img/{name}.jpg"


def load(src: str) -> Image.Image:
    kind, key = src.split(":", 1)
    if kind == "cpsc":
        m = next(CPSC.glob(f"{key}.*"))
        return Image.open(m)
    if kind == "pexels":
        return Image.open(STOCK / f"px_{key}.jpg")
    from data.make_listings import car_seat_label  # noqa: PLC0415

    return car_seat_label()


def main():
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    rows = []
    for i, (src, title, price, place, text, expected, truth) in enumerate(L, start=1):
        url = save(load(src), f"l{i:02d}")
        rows.append({"id": f"l{i:02d}", "title": title, "price": price, "place": place, "text": text, "image": url,
                     "photo_source": "CPSC recall notice" if src.startswith("cpsc") else ("Pexels" if src.startswith("pexels") else "synthetic"),
                     "expected_level": expected, "expected_word": WORD[expected], "truth": truth})
    (OUT / "listings.json").write_text(json.dumps(rows, indent=1))
    print(f"wrote {len(rows)} listings; problem items: {sum(r['expected_level'] in ('ILLEGAL_TO_SELL', 'RECALLED', 'UNSAFE_ADVISORY') for r in rows)}")


if __name__ == "__main__":
    main()
