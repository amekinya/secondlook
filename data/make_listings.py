"""Build demo 'listing screenshots' from CPSC recall photos (CPSC permits copying recall photos with credit)
plus one synthetic car-seat label. Layout is a generic local-marketplace card, not any real site's design.

Outputs: data/listings/listing_N.png + data/listings/listings.json (title, text, expected verdict)
Also shrinks eval photos to <=1024 px to keep the repo and model calls small.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
IMG = ROOT / "cpsc_images"
OUT = ROOT / "listings"


def font(size, bold=False):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def car_seat_label() -> Image.Image:
    img = Image.new("RGB", (900, 620), (232, 230, 226))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 60, 840, 560], radius=10, fill="white", outline=(30, 30, 30), width=3)
    y = 90
    for txt, f in [("Evenflo Company, Inc.  Piqua, Ohio", font(30, True)), ("MODEL NO. / NO DE MODÈLE:  38112244", font(28)),
                   ("MANUFACTURED IN / FABRIQUÉ EN:", font(28)), ("MARCH 2015  (03/2015)", font(40, True)),
                   ("MADE IN CHINA / FABRIQUÉ EN CHINE", font(24)),
                   ("This restraint conforms to all applicable", font(22)), ("Federal Motor Vehicle Safety Standards.", font(22))]:
        d.text((95, y), txt, fill=(20, 20, 20), font=f)
        y += 62 if f.size >= 28 else 40
    return img.rotate(-2.5, expand=False, fillcolor=(232, 230, 226))


def card(photo: Image.Image, title: str, price: str, place: str, text: str, credit: str) -> Image.Image:
    W = 900
    photo = photo.convert("RGB")
    ph = int(photo.height * W / photo.width)
    photo = photo.resize((W, min(ph, 760)))
    img = Image.new("RGB", (W, photo.height + 520), "white")
    img.paste(photo, (0, 0))
    d = ImageDraw.Draw(img)
    y = photo.height + 24
    d.text((32, y), price, fill=(20, 20, 20), font=font(40, True)); y += 58
    for ln in wrap(d, title, font(32, True), W - 64):
        d.text((32, y), ln, fill=(20, 20, 20), font=font(32, True)); y += 42
    d.text((32, y + 4), place, fill=(110, 110, 110), font=font(24)); y += 52
    d.line([32, y, W - 32, y], fill=(225, 225, 225), width=2); y += 18
    d.text((32, y), "Seller's description", fill=(20, 20, 20), font=font(26, True)); y += 40
    for ln in wrap(d, text, font(26), W - 64)[:6]:
        d.text((32, y), ln, fill=(50, 50, 50), font=font(26)); y += 36
    d.text((32, y + 16), credit, fill=(140, 140, 140), font=font(18))
    return img.crop((0, 0, W, min(img.height, y + 56)))


LISTINGS = [
    ("demo_26074.jpg", "Baby swing with mosquito net, great for naps", "$40", "Listed 2 days ago · Aurora, IL",
     "Electric baby swing / rocker, white and gray, comes with net and remote. My son napped in it every day. Model BB501. Smoke-free home.",
     "Photo: U.S. CPSC recall notice #26074", "ILLEGAL_TO_SELL"),
    ("demo_26169.png", "Braided crib bumper, gray, like new", "$15", "Listed today · Naperville, IL",
     "Soft braided bumper that ties around the crib. Keeps little arms and legs from getting stuck in the slats. Washed, like new.",
     "Photo: U.S. CPSC recall notice #26169", "ILLEGAL_TO_SELL"),
    ("demo_25009.png", "Fisher-Price Snugabunny cradle 'n swing", "$35", "Listed 5 days ago · Wheaton, IL",
     "Cradle swing with the cute bunny headrest and insert, all music and motion settings work. Model V0099. Pick up only.",
     "Photo: U.S. CPSC recall notice #25009", "RECALLED"),
    ("demo_10046.jpg", "Solid wood crib, side drops down for easy access", "$60", "Listed 1 week ago · Lisle, IL",
     "Older crib but sturdy. The front side slides down so it's easy to lift baby out. Mattress not included.",
     "Photo: U.S. CPSC recall notice #10046", "ILLEGAL_TO_SELL"),
    ("demo_12247.jpg", "Bumbo floor seat with safety belt", "$12", "Listed 3 days ago · Downers Grove, IL",
     "Bumbo seat in good shape, has the restraint belt installed. Great for sitting practice on the floor.",
     "Photo: U.S. CPSC recall notice #12247", "OK_SO_FAR"),
    ("carseat_label", "Evenflo convertible car seat", "$30", "Listed 4 days ago · Bolingbrook, IL",
     "Convertible car seat, rear or forward facing, clean cover. Here's the sticker from the bottom.",
     "Synthetic label created for SecondLook's demo", "UNSAFE_ADVISORY"),
]


def main():
    OUT.mkdir(exist_ok=True)
    meta = []
    for i, (src, title, price, place, text, credit, expected) in enumerate(LISTINGS, start=1):
        photo = car_seat_label() if src == "carseat_label" else Image.open(IMG / src)
        im = card(photo, title, price, place, text, credit)
        name = f"listing_{i}.png"
        im.save(OUT / name, optimize=True)
        meta.append({"file": name, "title": title, "price": price, "text": text, "credit": credit, "expected_level": expected})
    (OUT / "listings.json").write_text(json.dumps(meta, indent=1))
    # shrink eval photos
    for p in [q for q in IMG.glob("eval_*") if q.suffix.lower() in (".jpg", ".jpeg", ".png")]:
        im = Image.open(p)
        if max(im.size) > 1024:
            im.thumbnail((1024, 1024))
            im.convert("RGB").save(p.with_suffix(".jpg"), quality=85)
            if p.suffix.lower() != ".jpg":
                p.unlink()
    labels = json.loads((IMG / "eval_labels.json").read_text())
    for l in labels:
        l["file"] = Path(l["file"]).with_suffix(".jpg").name if not (IMG / l["file"]).exists() else l["file"]
    (IMG / "eval_labels.json").write_text(json.dumps(labels, indent=1))
    print(f"wrote {len(meta)} listings")


if __name__ == "__main__":
    main()
