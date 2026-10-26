"""SecondLook rule catalog: categories, bans, date-gated standards, car seat lifespans, parts checklists.
Every rule cites its source; full research with tags in docs/safety_rules_research.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

RULES_VERIFIED_AS_OF = date(2026, 10, 25)

# Verdict levels, worst first
LEVELS = ["ILLEGAL_TO_SELL", "RECALLED", "UNSAFE_ADVISORY", "CHECK", "OK_SO_FAR"]
LEVEL_UI = {
    "ILLEGAL_TO_SELL": ("Don't buy", "bad", "Banned from sale in the US"),
    "RECALLED": ("Don't buy (or get the fix)", "bad", "This product is recalled"),
    "UNSAFE_ADVISORY": ("Think twice", "warn", "Safety agencies warn against this"),
    "CHECK": ("Ask before you buy", "warn", "Missing information you need first"),
    "OK_SO_FAR": ("No known problems", "good", "Nothing found, but check the item in person"),
}

CATEGORIES: dict[str, str] = {
    "inclined_sleeper": "Inclined infant sleeper",
    "crib_bumper": "Crib bumper / liner / slat covers",
    "crib": "Crib",
    "bassinet": "Bassinet, cradle or bedside sleeper",
    "in_bed_sleeper": "In-bed sleeper / baby nest",
    "play_yard": "Play yard",
    "crib_mattress": "Crib or play yard mattress",
    "lounger": "Infant lounger / positioner / support cushion",
    "nursing_pillow": "Nursing pillow",
    "swing": "Infant swing or glider",
    "bouncer_rocker": "Bouncer, rocker or floor seat",
    "walker": "Infant walker / activity center",
    "bath": "Bath seat or infant tub",
    "high_chair": "High chair or booster",
    "stroller": "Stroller",
    "carrier": "Baby carrier or sling",
    "car_seat": "Car seat",
    "gate": "Safety gate",
    "changing_table": "Changing table",
    "monitor": "Baby monitor",
    "sleep_sack": "Sleep sack / swaddle",
    "toy_infant": "Infant toy",
    "toddler_bed": "Toddler bed or bed rail",
    "other": "Other / not baby gear",
}


@dataclass(frozen=True)
class Rule:
    id: str
    level: str
    title: str
    detail: str
    cite: str
    tag: str = "P"


RULES: dict[str, Rule] = {r.id: r for r in [
    Rule("R-INC-01", "ILLEGAL_TO_SELL", "Inclined infant sleepers are banned",
         "Since Nov 12, 2022, sleep products for infants with an incline over 10 degrees are banned hazardous products, no matter when they were made. Selling one is unlawful.",
         "Safe Sleep for Babies Act; 16 CFR 1310; CPSA §19"),
    Rule("R-BMP-01", "ILLEGAL_TO_SELL", "Padded crib bumpers are banned",
         "Since Nov 12, 2022, padded crib bumpers, vinyl bumper guards and vertical slat covers are banned from sale, no matter when they were made. Non-padded mesh liners are not covered.",
         "Safe Sleep for Babies Act; 16 CFR 1309; CPSA §19"),
    Rule("R-CRB-01", "ILLEGAL_TO_SELL", "Drop-side cribs can't be resold",
         "The federal crib standard has covered resale of new and used cribs since June 28, 2011. Drop-side cribs don't meet it, even if the side has been immobilized.",
         "16 CFR 1219/1220; CPSIA §104(c); CPSC Reseller's Guide"),
    Rule("R-CRB-02", "ILLEGAL_TO_SELL", "Crib made before June 28, 2011",
         "Cribs made before the 2011 standard are unlikely to comply, and the standard covers resale of used cribs.",
         "16 CFR 1219/1220; CPSC crib Q&A"),
    Rule("R-CRB-03", "CHECK", "Crib with no manufacture date shown",
         "You can't tell a compliant crib by looking. Ask for a photo of the label showing the model and month/year of manufacture (required on cribs since 2010).",
         "16 CFR 1130.4; CPSC crib Q&A"),
    Rule("R-ISP-01", "UNSAFE_ADVISORY", "Flat in-bed sleepers and baby nests",
         "Infant sleep products made after June 23, 2022 must meet the bassinet standard (legs or stand, stability, side height). Soft nests or pods used on an adult bed generally don't.",
         "16 CFR 1236", "P"),
    Rule("R-ISC-01", "UNSAFE_ADVISORY", "Infant loungers aren't safe for sleep",
         "CPSC warns against using loungers and positioners for sleep; loungers made after May 5, 2025 must meet a new standard (no restraints, max 10° incline). eBay bans them.",
         "16 CFR 1243; CPSC safe-sleep guidance"),
    Rule("R-ISC-02", "ILLEGAL_TO_SELL", "Lounger with a restraint strap (made after May 5, 2025)",
         "Infant support cushions made after May 5, 2025 may not have restraint straps.",
         "16 CFR 1243"),
    Rule("R-NP-01", "ILLEGAL_TO_SELL", "Nursing pillow with an infant strap (made after Apr 23, 2025)",
         "Nursing pillows made after April 23, 2025 may not have infant restraints.",
         "16 CFR 1242"),
    Rule("R-WGT-01", "UNSAFE_ADVISORY", "Weighted infant sleep products",
         "Not federally banned, but CPSC advises against weighted sleep sacks, swaddles and blankets for infants; eBay and Meta prohibit listing them.",
         "CPSC safe-sleep guidance; eBay and Meta policies", "S"),
    Rule("R-WLK-01", "CHECK", "Walker: check stair-fall protection",
         "Walkers must have gripping strips underneath or a base at least 36 inches wide (standard for walkers made after Dec 21, 2010). Ask for a photo underneath.",
         "16 CFR 1216; CPSC Reseller's Guide"),
    Rule("R-BTH-01", "CHECK", "Bath seat: check suction cups and the drowning warning",
         "Don't buy suction-cup bath seats made before Dec 6, 2010, or any without the permanent drowning warning.",
         "16 CFR 1215; CPSC Reseller's Guide"),
    Rule("R-RCL-01", "RECALLED", "Recalled product",
         "Selling a recalled product is unlawful for any seller, including individuals on marketplaces. Use the recall's remedy instead of buying it.",
         "CPSA §19(a)(2)(B); CPSC 'Stop Online Sale of Recalled Products'"),
    Rule("R-RCL-02", "CHECK", "Possible recall: confirm the model number",
         "This brand and product type have a recall that depends on the model number or manufacture date. Ask for a photo of the label.",
         "CPSC Recalls database"),
    Rule("R-RCL-LOOK", "CHECK", "Looks like a recalled product",
         "The description and photo match a recalled product, but the brand or model isn't confirmed. Recalled products are often resold "
         "with no brand or under a different brand name. Ask the seller who made it and for a photo of the label before buying.",
         "CPSC Recalls database; SecondLook look-alike matcher (fine-tuned NVIDIA reranker)"),
    Rule("R-RCL-03", "OK_SO_FAR", "Recall remedy appears to be done",
         "This model was recalled, but the photos suggest the fix was applied. Confirm with the seller.",
         "CPSC recall remedy"),
    Rule("R-CS-EXP", "UNSAFE_ADVISORY", "Car seat past its expiration",
         "Manufacturers set car seat lifespans (no federal rule). Plastic degrades and standards change; don't use a seat past its date.",
         "Manufacturer instructions; NHTSA used car seat checklist", "P"),
    Rule("R-CS-EXP-SOON", "CHECK", "Car seat expires soon",
         "The seat will expire within a year; factor that into the price and how long you'll need it.",
         "Manufacturer instructions"),
    Rule("R-CS-LBL", "CHECK", "Car seat: labels, manual and crash history",
         "NHTSA says only buy a used seat if it has its manufacture-date and model labels, all parts, its manual, no open recalls, and has never been in a moderate or severe crash.",
         "NHTSA Used Car Seat Safety Checklist"),
    Rule("R-CS-RCL", "RECALLED", "Car seat recall",
         "This car seat's brand, model and manufacture date fall inside an NHTSA recall. Contact the manufacturer for the remedy before using it.",
         "NHTSA recall campaign; 49 U.S.C. 30120(j)"),
    Rule("R-PARTS", "CHECK", "Safety parts to confirm",
         "Durable infant products should have their permanent label (maker, model, month/year made) and no missing or broken parts.",
         "16 CFR 1130; CPSC Reseller's Guide"),
    Rule("R-NONE", "OK_SO_FAR", "No known recall or ban found",
         "We found no ban, standard problem or recall for what's visible. That isn't a safety guarantee; check it in person.",
         "CPSC and NHTSA recall data"),
]}

# Car seat useful life by brand (years from date of manufacture). Source: docs §D2.
CAR_SEAT_LIFE: dict[str, tuple[int, int, str, str]] = {
    # brand: (min, max, note, tag)
    "graco": (7, 10, "10 years for boosters and steel-reinforced harness seats, 7 for plastic-reinforced; check the stamped date", "P"),
    "chicco": (6, 10, "Infant seats 6 years; convertibles and boosters 8; some all-in-ones 10", "P"),
    "britax": (6, 10, "6-10 years by model; many post-2018 seats print the date", "P"),
    "evenflo": (10, 10, "10 years for current seats; older seats: the label governs", "P"),
    "safety 1st": (8, 12, "8-12 years by product", "P"),
    "maxi-cosi": (8, 12, "8-12 years by product", "P"),
    "cosco": (6, 8, "Scenera NEXT 8 years if made after Dec 14, 2013, else 6", "S"),
    "clek": (9, 9, "9 years", "P"),
    "nuna": (7, 7, "Retailers cite ~7 years; read the printed date", "U"),
    "uppababy": (7, 7, "Retailers cite 7 years for MESA; read the printed date", "U"),
}

PARTS: dict[str, list[str]] = {
    "crib": ["All screws, bolts and brackets present and tight", "Mattress support present and right way up", "No missing or cracked slats; gaps no wider than a soda can (2 3/8 in.)", "No drop side", "Label with model and month/year made"],
    "play_yard": ["Mesh holes smaller than 1/4 in., no tears", "Original mattress only (or one naming this brand and model)", "No inclined sleeper insert (banned)", "Top rails lock and covers intact"],
    "bassinet": ["Legs or stand present", "Original mattress pad", "Bed-attachment straps (bedside sleepers)", "Label with model and month/year made"],
    "car_seat": ["Manufacture-date and model labels", "Instruction manual", "Harness, chest clip and buckle", "Base (infant seats), LATCH connectors and top tether", "No cracks; never in a moderate or severe crash"],
    "stroller": ["Harness works", "Fold locks engage", "Peg Perego Venezia/Pliko-P3: no single-cupholder tray (recalled)"],
    "swing": ["Harness present", "Fisher-Price Snuga: headrest and insert removed (recall fix)", "4moms MamaRoo (3-point): strap fastener present (recall fix)"],
    "bouncer_rocker": ["Restraint present", "Bumbo floor seat: restraint belt kit installed (recall fix)"],
    "walker": ["Gripping strips underneath or base at least 36 in. wide"],
    "bath": ["Permanent drowning warning", "Not a suction-cup seat made before Dec 2010"],
    "lounger": ["No restraint straps", "Never used for sleep"],
    "nursing_pillow": ["No infant straps"],
    "monitor": ["Angelcare sensor pads: rigid cord cover present (recall fix)"],
    "high_chair": ["Restraint and crotch post present", "Tray locks", "Label with model and month/year made"],
}

QUESTIONS: dict[str, list[str]] = {
    "_any": ["Can you send a photo of the label with the model number and the month/year it was made?",
             "Are all the original parts and the instructions included?"],
    "crib": ["Is it a fixed-side crib (no side that slides up and down)?"],
    "car_seat": ["Has it ever been in a car crash, even a minor one?", "Can you photo the sticker with the manufacture and expiration dates?"],
    "swing": ["Has the recall fix been done (headrest/insert removed or strap fastener added), if this model was recalled?"],
    "play_yard": ["Does it include the original mattress, and is any inclined sleeper insert included?"],
}
