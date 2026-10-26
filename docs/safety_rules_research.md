# SecondLook: Safety Rules & Data Research

**Compiled:** 2026-10-25, for a hackathon due 2026-10-30
**Scope:** US federal rules for second-hand baby gear. Covers banned product types, recalled models, missing safety-critical parts, car seat expiration, data sources, marketplace policies, evidence, and competitors.

**Confidence tags used throughout**
- **[P]**: Primary source checked directly (CFR, Federal Register, statute, CPSC/NHTSA page or data, manufacturer page). The date shown is the publication or effective date. Pages without a date are marked "accessed 2026-10-25".
- **[T]**: Tested live against the API or data during this research (2026-10-25).
- **[S]**: Secondary source only (retailer, news, law firm, advocacy group). Needs confirmation before you rely on it as a rule.
- **[U]**: Unconfirmed, conflicting, or my own legal interpretation. Do not present it to users as fact.

---

## 0. Ten findings that change the build

1. **There is no federal car seat expiration rule.** FMVSS 213 (49 CFR 571.213) requires a "Manufactured in [month/year]" label and model number. It contains no expiration provision; I searched the full eCFR text on 2026-10-25. Manufacturers set the expiration. **[P]**
2. **Car seats are outside CPSC jurisdiction.** The CPSA's definition of "consumer product" excludes motor vehicle equipment (15 U.S.C. 2052(a)(5)(C)). Car seat recalls come from NHTSA, not the CPSC API. **[P]**
3. **Two bans apply regardless of manufacture date: inclined sleepers (16 CFR 1310) and crib bumpers (16 CFR 1309).** Both took effect Nov 12, 2022. The crib standard (16 CFR 1219/1220) also explicitly covers the resale of *used* cribs. **[P]**
4. **Most other nursery standards apply only to products manufactured after their effective date** (CPSA §9(g)(1), 15 U.S.C. 2058(g)(1)). A 2019 nursing pillow is not illegal under the 2025 nursing pillow rule. The rules engine has to date-gate. **[P]**
5. **Nursing pillows are 16 CFR 1242, not 1241.** Part 1241 is Crib Mattresses and Part 1243 is Infant Support Cushions. **[P]**
6. **The CPSC Recall API has no key, sends CORS `*`, and works as a bulk download.** Any unknown parameter returns the entire database: 10,058 records, 27.8 MB, about 10 s. **[T]**
7. **The API's `Products.Model` field is empty in all 10,058 records.** Model numbers appear only inside the free-text `Description`. The `Hazard`, `UPC` and `ManufacturerCountry` filters returned 0 results even for values known to be in the data. **[T]**
8. **CPSC unilateral "Product Safety Warnings" are not in the Recall API.** These are issued when a firm (often an Amazon or Temu seller) refuses to recall, and many are infant loungers and walkers. Example: the Fasando lounger warning of 2025-11-20, linked to 1 infant death, is absent. You need a separate source for them. **[T]**
9. **CPSC's own policy says recall photos can be copied and distributed without permission.** Other images on CPSC sites may not be. **[P]**
10. **No competitor found analyzes a third-party listing screenshot against banned-category rules plus recalls plus car seat expiration.** All the apps found are "scan what you own" inventory or barcode tools. **[S/T]**

---

## A. Banned and regulated product categories

### A1. Legal framework for RESALE (applies to every row below)

| Provision | What it says (paraphrased) | Applies to private individuals? | Source |
|---|---|---|---|
| CPSA §19(a)(1), 15 U.S.C. 2068(a)(1) | It is unlawful for **any person** to sell, offer for sale or distribute a product that does not conform to an applicable CPSC rule, standard or ban. | Statute says "any person". **[P]** | law.cornell.edu/uscode/text/15/2068 |
| CPSA §19(a)(2)(B) | It is unlawful for any person to sell a product subject to a voluntary corrective action (a recall) that CPSC has announced, or that the seller knew or should have known about. | Yes, by text. **[P]** | same |
| CPSA §19(b) | Exceptions: the seller holds a compliance certificate, or relied in good faith on the manufacturer's representation. | Narrow. **[P]** | same |
| CPSA §20, 15 U.S.C. 2069 | Civil penalties apply to **knowing** violations. "Knowingly" includes the knowledge a reasonable person would have after exercising due care. | **[P]** | law.cornell.edu/uscode/text/15/2069 |
| Penalty amounts | Up to $120,000 per violation and $17,150,000 per related series (86 FR 68244, effective 2022-01-01). The next 5-year adjustment is due Dec 1, 2026. | **[P]** | federalregister.gov 2021-26082 |
| CPSA §8, 15 U.S.C. 2057 | Basis for declaring a "banned hazardous product". The SSBA bans use this status. | **[P]** | law.cornell.edu/uscode/text/15/2057 |
| CPSA §9(g)(1), 15 U.S.C. 2058(g)(1) | A consumer product safety **standard** applies only to products **manufactured after** its effective date. | Key to date-gating. **[P]** | law.cornell.edu/uscode/text/15/2058 |
| CPSIA §104(c), 15 U.S.C. 2056a(c) | No person may sell or resell a crib that doesn't meet the standard. The provision lists manufacturers, distributors, those "in the business" of selling or reselling, child care facilities, and public accommodations. | It names businesses; 16 CFR 1219.1(b) covers "resale" of "new or used" cribs. **[P]** Liability for a one-off private seller is **[U]**. | law.cornell.edu/uscode/text/15/2056a; eCFR 1219 |
| CPSC "Stop Online Sale of Recalled Products" | CPSC says its laws cover products sold second-hand by a consumer on an online marketplace, and that selling any recalled product is illegal. Cites §19. | Yes, per CPSC. **[P]** (accessed 2026-10-25, page undated) | cpsc.gov/Business--Manufacturing/Business-Education/ResaleThrift-Stores-Information-Center/Stop-Online-Sale-of-Recalled-Products |
| CPSC Reseller's Guide (Pub. #254) | Covers thrift and consignment stores, flea markets, yard sales, online auction sellers and people giving items away. Resellers cannot knowingly sell non-compliant products. Its list includes most cribs made before June 2011, all drop-side cribs (even immobilized), and durable infant products that are wobbly or missing parts. | Yes. **[P]** (issued Jan 2013, revised May 2014) | cpsc.gov/s3fs-public/ResellersGuide_0.pdf |
| CPSC Resale/Thrift FAQ | Covers resellers on auction sites and people giving products away. Resellers are not required to *test* used products, but noncompliant or hazardous items should be destroyed. | **[P]** (undated) | cpsc.gov/.../Resale-and-Thrift-Store-Frequently-Asked-Questions |
| Car seats: 49 U.S.C. 30112(b)(1) | The ban on selling noncompliant motor vehicle equipment **does not apply** after the first good-faith purchase by someone other than a reseller. Private resale of a used non-recalled seat is therefore not federally prohibited. | **[P]** statute; applying it to marketplace resale is my reading **[U]**. | law.cornell.edu/uscode/text/49/30112 |
| Car seats: 49 U.S.C. 30120(j) | "No person" may sell equipment that is the subject of a defect or noncompliance notice, in usable condition, unless it has been remedied. | Text says "no person". Whether NHTSA enforces this against private individuals is **[U]**. | law.cornell.edu/uscode/text/49/30120 |

### A2. Category table

Abbreviations: SSBA = Safe Sleep for Babies Act of 2021 (Pub. L. 117-126, signed 2022-05-16). DOM = date of manufacture.

| # | Category | Legal basis | Effective date | Covers resale? | Visual cues (amateur photos) | Label / text cues | Source |
|---|---|---|---|---|---|---|---|
| 1 | **Inclined sleepers for infants** | SSBA, 15 U.S.C. 2057d; 16 CFR 1310 (88 FR 55554, 2023-08-16) | Statutory ban **2022-11-12**, regardless of DOM; codifying rule effective 2023-09-15 | **Yes.** Banned hazardous product under §8, so selling or offering is unlawful under §19 **[P]** | Fabric "hammock" seat with the head end raised (>10°) on a tubular A-frame or curved rocking base; padded side walls; hood. Examples: Rock 'n Play, Kids2 rocking sleepers, inclined inserts in play yards or bassinets. Many 2025-26 Amazon "baby swings" are recalled as violating this ban. | Definition needs a sleep surface **>10°** AND intended, marketed or designed for **sleep** for an infant **up to 1 year**. Text cues: "sleeper", "napper", "incline sleeper", "sleep", "overnight", "Rock 'n Play". A bouncer or rocker *not* marketed for sleep is not covered by this definition. | eCFR 16 CFR 1310 [P]; CPSC SSBA business guidance [P] |
| 2 | **Crib bumpers** | SSBA, 15 U.S.C. 2057e; 16 CFR 1309 (88 FR 54878, 2023-08-14) | Statutory **2022-11-12**, regardless of DOM; rule effective 2023-09-13 | **Yes** **[P]** | Padded fabric panels or rolls tied around the inside of crib slats; **braided** bumpers (several 2025-26 recalls); vinyl bumper guards; **vertical slat covers** (sleeves on each slat). Often visible in "crib + bedding set" listings. | Includes padded bumpers, supported or unsupported vinyl bumper guards, and vertical slat covers. **Excludes non-padded mesh crib liners.** Text cues: "bumper", "crib liner", "slat covers", "bedding set". | eCFR 16 CFR 1309 [P] |
| 3 | **Full-size and non-full-size cribs**, including **drop-side cribs** | CPSIA §104(c); 16 CFR 1219 / 1220 (75 FR 81766, 2010-12-28) | **2011-06-28** for any manufacture, sale or **resale** (child care facilities and hotels: 2012-12-28) | **Yes, explicitly**: covers "new and used" cribs and "resale" **[P]** | **Drop-side**: one long side slides up and down on tracks, with visible trigger locks, plastic or metal pegs, or spring hardware; mismatched rail heights. Other flags: corner posts more than 1/16 in. high, headboard cutouts, slat gaps over 2 3/8 in. (about a soda can), missing or cracked slats, wooden stabilizer bars under the mattress support. Mesh-sided cribs: mesh holes over 1/4 in. | Under 16 CFR 1130.4, durable infant products made since **2010-06-28** carry permanent marking with manufacturer, model and month/year of manufacture. **DOM before 2011-06-28 means likely noncompliant.** CPSC says you cannot tell compliance by looking; if there is no label and the crib was bought before 2011-06-28, it is unlikely to be certified. Text cues: "drop side", "Jenny Lind" (some recalled), "vintage crib", year. | eCFR 1219/1220 [P]; CPSC crib Q&A (2011, updated 2013) [P]; CPSC Crib Information Center [P]; CPSC 2010-12-17 release (ends traditional drop sides) [P] |
| 4 | **Infant sleep products** (in-bed sleepers, baby nests/pods, compact or travel bassinets, baby boxes, infant tents) | 16 CFR 1236 (86 FR 33022, 2021-06-23); incorporates ASTM F3118-17a with modifications | Products manufactured **after 2022-06-23** | Yes for items made after 2022-06-23 (§19(a)(1)). Older flat items: not covered by 1236 **[P]**. Older inclined items: banned under row 1. | Low, soft-sided "nest" or "pod" lying on an adult bed; no legs or stand; foam pad with padded bumpers. Rule requires meeting the bassinet standard (stand, stability, side height). | Covers products for infants **up to 5 months**. Names implying sleep ("bed", "bassinet", "crib") pull a product into scope. Sleep surface must be ≤10°. CPSC cited DockATot Deluxe+ (made on or after 2022-06-23). Look for "co-sleeper", "in-bed sleeper", "baby nest", "lounger for sleep". | eCFR 1236 [P]; CPSC news release 2022-11-09 [P]; CPSC ISP business guidance [P] |
| 5 | **Infant support cushions** (loungers, positioners, wedges, crib pillows, tummy-time pillows) | 16 CFR 1243 (89 FR 87467, 2024-11-04) | Products manufactured **after 2025-05-05** | Yes if made after 2025-05-05. Older units: only recalled ones (e.g. Boppy lounger) are illegal to sell. | **U-shaped or donut cushion with a raised rim and central recess** (Boppy-lounger form); wedge; head positioner; side "anti-roll" bolsters. Any **restraint strap** is a violation. | Rule requires **no restraint**, max incline ≤10°, a firmness test, a sidewall-angle test and a permanent warning. Exempts car seat and stroller liners, rigid-frame seats, and nursing pillows (unless also sold as loungers). Text cues: "lounger", "newborn lounger", "positioner", "anti-roll", "tummy time pillow". | eCFR 1243 [P]; FR 2024-25181 [P] |
| 6 | **Nursing pillows** | 16 CFR **1242** (89 FR 85388, 2024-10-25) | Products manufactured **after 2025-04-23** | Yes if made after 2025-04-23 | C or U shape worn around the caregiver's waist. **Infant restraint straps are prohibited.** Sagging, soft surfaces fail the firmness test, but that cannot be judged from a photo. | Requirements: firmness (>10.0 N per 1 in.), infant containment (9-in. probe), no infant restraints, permanent warnings. Maternity pillows, slings and soft carriers are exempt. eBay requires a label image and a compliance disclaimer. | eCFR 1242 [P] |
| 7 | **Crib and play yard mattresses**, including aftermarket | 16 CFR 1241 (87 FR 8640, 2022-02-15) | Manufactured **after 2022-08-15**; ASTM F2933-25 update (91 FR 6510) effective 2026-05-03 | Yes if made after 2022-08-15 | Thick foam pad inside a mesh play yard; "fits most play yards" listings; a mattress stacked on the original pad; gaps at the edges. | An aftermarket play yard mattress must be tested with each brand and model it claims to fit. CPSC warnings (e.g. Hiccapop, 2025-03-06, about 108,000 units) tell parents to use only the original mattress or one that names the play yard's brand and model. | eCFR 1241 [P]; CPSC Warning 25-174 [P] |
| 8 | **Bassinets and cradles** / **bedside sleepers** / **play yards** | 16 CFR 1218 (78 FR 63019); 1222 (79 FR 2581); 1221 (77 FR 52220) | 1218: 2014-04-23 (ASTM F2194-25 from 2026-02-21). 1222: 2014-07-15 (rev. 2023-08-05). 1221: 2013-02-28 (rev. 2025-04-05) | Date-gated (§9(g)) | Bedside sleepers need intact bed-attachment straps (AirClub recall 2026-03-26 replaced L-shaped straps with four T-buckle straps). Missing or aftermarket mattress pads. Simplicity 3-in-1/4-in-1 bassinets with a Velcro fabric flap over metal bars. | 16 CFR 1130 label with model and DOM | eCFR [P]; FR API [P]; CPSC recall 26342 [T] |
| 9 | **Infant walkers** | 16 CFR 1216 (75 FR 35266, 2010-06-21); older walker bans revoked (75 FR 35279) | Manufactured or imported on or after **2010-12-21** | Date-gated. The Reseller's Guide says not to sell walkers without stair-fall protection **[P]** | Wheeled frame with a seat. Check underneath for **rubber gripping strips**; otherwise the base must be at least **36 in.** wide. Many 2025-26 recalls and CPSC warnings of cheap Amazon walkers. | DOM label | eCFR 1216 [P]; Reseller's Guide [P] |
| 10 | **Infant bath seats** | 16 CFR 1215 (75 FR 31691, 2010-06-04); ASTM F1967-24 | Manufactured or imported on or after **2010-12-06** | Date-gated. Reseller's Guide: don't sell pre-2010-12-06 seats with **suction cups**, broken seats, or seats without permanent warnings **[P]** | Ring or upright seat with **suction-cup feet**. Many 2025-26 recalls for drowning hazard (YCXXKJ, NFSVLB, CheerKid, Trankerloop, ONTHEWEI). | Permanent drowning warning | eCFR 1215 [P]; Reseller's Guide [P]; CPSC API [T] |
| 11 | **Infant and cradle swings**; **bouncers** | 1223 (orig. 77 FR 66703, effective 2013-05-07; ASTM F2088-25 via 91 FR 20875, effective 2026-07-25); 1229 (effective 2018-03-19) | as listed | Date-gated | Snuga swings should have the **headrest and body insert removed** (that is the remedy). MamaRoo should have a **strap fastener** (the remedy). | Model on underside of motor housing or base | eCFR [P]; recalls 25009, 22200 [T] |
| 12 | **Infant rockers** | **No final rule.** NPR 88 FR 73551 (2023-10-26), docket CPSC-0046 | n/a | Not regulated by a specific standard **[P]**. Fisher-Price Infant-to-Toddler and Newborn-to-Toddler Rockers carry a CPSC **warning** (2022-06-14: 13 deaths, more than 17M sold worldwide). That is not a recall. | Reclined seat on a curved rocking base, often with a toy bar | — | FR API search 2026-10-25 (no final rule) [P]; CPSC release 22-157 [P] |
| 13 | **Weighted infant sleep products** (weighted sleep sacks, swaddles, blankets) | **No federal ban or rule.** CPSC voted 3-1 in Nov 2023 not to pursue a standard. CPSC website says not to use them. The SIDS Act (S.4939, 118th Congress, introduced Aug 2024) would ban them. | n/a | **Not federally illegal** **[S]**. eBay bans them; Meta added "weighted sleep wearables" to its prohibited list after the CR evaluation (2026) **[S]**. | Sleep sack or swaddle with beads or weighted pads; "weighted" in the title. | Brands named in litigation: Dreamland Baby (Dreamland v. CPSC pending in D.D.C., per NCLA 2026-02-12) **[S]** | NCLA 2026-02-12 [S]; CR 2024-08-02 [S]; eBay policy [P] |
| 14 | **Button and coin batteries** in products (Reese's Law) | Pub. L. 117-171; 15 U.S.C. 2056e; 16 CFR 1263 (88 FR 65274, 2023-09-21) | Performance requirements: **2023-10-23**. Battery package labels: made after 2024-09-21 | Date-gated. **Toys are exempt** if they meet the toy standard, 16 CFR 1250 (ASTM F963) | Light-up toys, crib mobiles, remote controls: the battery door must need a **tool (screw)** or two independent movements to open. | Warning icon on the product or package | eCFR 1263 [P] |
| 15 | **Magnets** (non-toy) | 16 CFR 1262 (87 FR 57756, 2022-09-21) | Manufactured after 2022-10-21. Upheld by the 10th Circuit on 2025-03-03 **[S]** | Date-gated; toys exempt (covered by 1250) | Small loose high-power magnet sets | — | eCFR 1262 [P]; JD Supra (2025) [S] |
| 16 | **Toys** (for completeness) | 16 CFR 1250 = ASTM F963-23 (effective 2024-04-20); small parts for under-3 (16 CFR 1501); water beads (90 FR 57820, effective 2026-03-12) | as listed | Date-gated; recalled toys illegal to sell | Small parts on infant toys, pull strings | — | eCFR 1250 [P] |
| 17 | **Car seats** (not CPSC) | FMVSS 213, 49 CFR 571.213; labels at S5.5.2; registration card at S5.8 | — | Private resale of a non-recalled seat is not federally prohibited **[U]**. Recalled and unremedied: see 49 U.S.C. 30120(j) **[U]** | See Section D | Label must show model name or number, manufacturer, "Manufactured in [month, year]", and place of manufacture | eCFR 49 CFR 571.213 [P] |

**Other durable infant standards** (all date-gated by DOM): high chairs 1231 (2019-06-19); strollers 1227 (2015-09-10); sling carriers 1228 (2018-01-30); soft carriers 1226 (2014-09-29); hand-held carriers 1225 (2014-06-06); gates 1239 (2021-07-06); infant bath tubs 1234 (2017-10-02); changing products 1235 (2019-06-26); stationary activity centers 1238 (2019-12-18); portable bed rails 1224 (2012-08-29); booster seats (furniture-type) 1237 (2020-01-02); toddler beds 1217 (2011-10-20). Dates are each rule's original effective date, from the Federal Register API **[P]**. In Sept 2026 CPSC withdrew a direct final rule that would have revoked obsolete bouncer and activity center provisions (91 FR 58817), so nothing changed **[P]**.

### A3. Draft deterministic rule set

Verdict levels: **ILLEGAL_TO_SELL** (cite a statute or ban), **RECALLED** (cite a recall number and remedy), **UNSAFE_ADVISORY** (CPSC or NHTSA guidance, not a legal ban), **CHECK** (information missing), **OK_SO_FAR**.

- `R-INC-01`: category is inclined_sleeper (incline >10° AND marketed for sleep, age under 12 months) → ILLEGAL_TO_SELL (16 CFR 1310). Ignore DOM.
- `R-BMP-01`: category is crib_bumper (padded, vinyl guard or slat cover) → ILLEGAL_TO_SELL (16 CFR 1309). If the item is a mesh liner, the result is OK.
- `R-CRB-01`: crib with drop side → ILLEGAL_TO_SELL (16 CFR 1219/1220, CPSC Reseller's Guide), even if immobilized.
- `R-CRB-02`: crib with DOM before 2011-06-28 → ILLEGAL_TO_SELL (likely noncompliant; CPSC guidance). If DOM is unknown → CHECK (ask for the tracking label).
- `R-ISP-01`: flat or in-bed sleeper with DOM after 2022-06-23 and no legs or stand → likely violates 16 CFR 1236 → UNSAFE_ADVISORY. Escalate to ILLEGAL only on a matching CPSC recall or warning.
- `R-ISC-01`: infant lounger or positioner with a restraint, or made after 2025-05-05 → check against 16 CFR 1243. Treat any lounger as UNSAFE_ADVISORY: CPSC warns against loungers for sleep, and eBay bans them.
- `R-NP-01`: nursing pillow with an infant restraint and DOM after 2025-04-23 → violates 16 CFR 1242(c).
- `R-RCL-*`: brand and model match a CPSC recall (Section B or the local index) → RECALLED. Show the remedy. If the remedy is a repair kit, check for evidence of the repair (Snuga insert removed, MamaRoo strap fastener, Bumbo belt).
- `R-CS-EXP`: car seat → read "Do not use after" or "Expiration" date, else DOM + brand lifespan (Section D). Past → UNSAFE_ADVISORY (manufacturer instruction). DOM or model label missing → CHECK (NHTSA checklist).
- `R-CS-RCL`: car seat brand/model and DOM falls between NHTSA BGMAN and ENDMAN → RECALLED (NHTSA campaign).
- `R-WGT-01`: weighted infant sleep wearable or blanket → UNSAFE_ADVISORY (CPSC website warning; eBay and Meta prohibit). Not illegal federally.
- `R-PARTS-*`: Section E checklist.

---

## B. Top recalled baby products still circulating

Data comes from the CPSC Recall API full download (2026-10-25) **[T]**, unless the row is marked NHTSA. Deaths are as reported in the recall notice; later counts are cited where a newer primary source exists.

| # | Product | Recall # / date | Units | Deaths / incidents | Models / identifiers | Remedy | How to identify (visual and label) |
|---|---|---|---|---|---|---|---|
| 1 | **Fisher-Price Rock 'n Play Sleeper** (all models) | 19105 (2019-04-12); reannounced **23088** (2023-01-09) | ~4.7M | ~100 deaths reported; at least 8 after the recall | **All models**; sold Sept 2009 to Apr 2019 | Refund or voucher. CPSC says reselling is illegal. Also banned as an inclined sleeper. | Inclined fabric hammock seat with padded sides and a hood, on white tubular legs joined at a hub, with a curved rocking base. Fisher-Price logo on the fabric. Model numbers aren't needed because every model is recalled. |
| 2 | **Kids2 (Kids II) Rocking Sleepers**: Ingenuity, Bright Starts, Disney Baby, DreamComfort | 19112 (2019-04-26); reannounced **23089** (2023-01-09) | ~694,000 | 15 deaths (4 after the recall) | All models; style numbers 10081, 10126, 10127, 10148, 10289, 10292, 10320, 10380, 10568, 10729, 10872, 10888, 10890, 11021, 11022, 11063, 11164, 11171 … 60600, 60635 (full list in the notice) | Refund | Similar inclined seat on bent-wire rocker rails. The brand appears on the seat fabric. |
| 3 | **Boppy Newborn Lounger** (Original, Preferred, Pottery Barn Kids) | **21198** (2021-09-23) | ~3.3M (+35k Canada) | 8 deaths at recall; **10** per CPSC's letter to Meta of 2023-06-06 **[P]** | All; about 23 × 22 × 7 in.; sold 2004–2021 | Refund | **U or donut-shaped lounger with a recessed center**, often floral or plush. It is NOT the C-shaped Boppy nursing pillow. CPSC asked for about 1,000 Marketplace takedowns a month. |
| 4 | **Fisher-Price Snuga Swings** | **25009** (2024-10-10) | ~2.1M | 5 deaths (2012–2022; infants sleeping, unrestrained, with added bedding) | 21 models: BGB32, CCF38, CHM56, CHM69, CHM76, CHM78, DRG43, FKL21, GJB53, GKH44, GNG38, GNG40, GVF83, HBM23, HDY10, HGX49, V0099, W9510, X7051, X7345, X7347. Model and name are under the motor housing. | **Repair:** cut off the headrest and remove the body-support insert; $25 refund | A swing with an animal-themed plush headrest ("Snugabunny", "Snugapuppy"). **If the headrest or insert is still present, the recall was not remedied.** |
| 5 | **4moms MamaRoo** (v1.0–4.0, 3-point harness) and **RockaRoo** | **22200** (2022-08-15) | 2M + 220k | 1 death (a crawling 10-month-old caught in a strap under the seat) | MamaRoo 4M-005 (v1/2), 1026 (v3), 1037 (v4); RockaRoo 4M-012. Model on the bottom. The 5-point-harness MamaRoo is excluded. | Repair: a free strap fastener | Oval seat on a round base with buttons. **Straps dangling under the seat = not remedied.** |
| 6 | **Fisher-Price 4-in-1 Rock 'n Glide Soother** and 2-in-1 Soothe 'n Play Glider | **21147** (2021-06-03) | 120k + 55k | 4 deaths | CHP56, CHP55, CBT81; GDD28, GDD39, GDD41, GGW85, GNX43, GVG43, HBD26, HBD27. Model under the base. | Refund | Powered glider seat on a base |
| 7 | Other **inclined sleepers** recalled 2019–2021 | 19151 (FP Ultra-Lite Day & Night play yard insert, 71k); 19177 (Eddie Bauer and Disney, Dorel, 24k); 20059 (SwaddleMe By Your Bed, 46k); 20060 (Evenflo Pillo, 3.1k); 20061 (Delta and others, 5.9k); **20062 (Graco Little Lounger, 111k)**; 20075 / 21125 (Kolcraft accessory, 51k); 21052 (Graco Pack 'n Play inclined accessories, 51k) | — | None reported in these notices | Graco Little Lounger: 1872034, 1875063, 1875102, 1877160, 1882081, 1896313, 1908957, 1914283, 2047734, 1922809 (label on a metal leg). Graco playard accessories: 2034085, 2048753, 2053215, 1947177, 1896392, 1946902, 1946903, 2105055. FP play yards: CBV60, CHP86, CHR06, CJK24, DJD11. | Refund for the insert; the play yard itself can still be used | **The inclined insert is the banned part.** A play yard listing that includes it should be flagged. |
| 8 | **Stork Craft drop-side cribs** (including Fisher-Price-logo models) | **10046** (2009-11-23) | 1.213M US + 968k Canada | 4 suffocation deaths; 110 detachments | Made Jan 1993 to Oct 2009. "storkcraft baby" or "storkling" on the teething rail; DOM on the instruction sheet attached to the mattress support board. | Repair kit (sold as a drop-side crib, it is illegal regardless) | Drop-side hardware |
| 9 | **Delta Enterprise drop-side cribs**: Safety Peg | **09017** (2008-10-21); reannounced 11179 (2011-03-22) | 985k | 2 deaths (entrapment with **missing safety pegs**) | Models 4320–4980 (list in the notice); made in Taiwan or Indonesia, 1995–2005 (4624 in 2007); label on the mattress support board | Repair kit | Look for the bright safety pegs on each leg |
| 10 | **Delta** drop-side (three hardware types) and wooden stabilizer bars; also 09016 (spring peg, 600k) | **10273** (2010-06-24) | 747k | Entrapments and falls | Delta cribs 2000–2009 | Immobilizer kit | Mattress support collapse if the stabilizer bars are installed upside down |
| 11 | **Simplicity drop-side cribs** (also Graco-logo) | **07307** (2007-09-21); also 08401, 09260 | ~1M (+600k, 400k) | 2 deaths, 1 more investigated | 4600, 4605, 4705, 5000, 8000, 8324, 8800, 8740, 8910, 8994, 8050, 8750, 8760, 8996 (label on the headboard) | The firm is defunct; **dispose** | Drop side |
| 12 | **Generation 2 Worldwide / ChildESIGNS** drop-side cribs | **10134** (2010-02-09) | 500k | 3 deaths | Name on the headboard or footboard label; "ChildESIGNS" on the teething rail | Do not fix; stop using | Drop side |
| 13 | **Evenflo Jenny Lind** drop-side cribs | **10274** (2010-06-24) | 750k | Entrapment and falls | 012614–0161617 (label on the bottom beam of the headboard) | Immobilizer | Spindle-turned "Jenny Lind" posts |
| 14 | **Dorel Asia** cribs | **10114** (2010-01-19) | 635k | 1 death | DA… and GP… model codes (list in the notice) | Replacement kit | — |
| 15 | **Simplicity 3-in-1 / 4-in-1 convertible bassinets** | **08381** (2008-08-28) | ~900k | 2 strangulation deaths | Metal bars covered by a Velcro fabric flap | Refund | The Velcro flap over the lower bars is the tell. Modified units with the fabric stitched down are excluded. |
| 16 | **Nap Nanny** recliners (Gen 1, Gen 2, Chill) | 10309 (2010-07-26); **13083** (2012-12-27) | ~155k | 5 deaths (per the 13083 title) | Bucket-shaped foam recliner with a fabric cover and 3-point harness | Retailer return | Foam bucket seat |
| 17 | **Infantino SlingRider** and Wendy Bellissimo slings | **10177** (2010-03-24) | ~1M | 3 deaths | "Infantino" on the plastic slider; item numbers 3937500H7 and 3937501H7 | Replacement | Pouch sling with padded strap |
| 18 | **Peg Perego Venezia and Pliko-P3** strollers (2004–2007) | **12232** (2012-07-24) | API says "About 6,223,000"; widely reported as ~223,000 **[U] (verify)** | 1 strangulation death | IPP328…, IPVA13… (list); label on the seat back or footboard | Repair kit | **Single-cupholder child tray** = recalled (bumper bar or two-cup tray excluded) |
| 19 | **Angelcare Movement & Sound** monitors | **14028** (2013-11-21) | 600k | 2 cord-strangulation deaths | AC1100, AC201, AC300, AC401, AC601, 49255 without rigid cord covers | Repair (cord cover) | Sensor pad under the mattress with a long cord. **No rigid cord cover = unremedied.** |
| 20 | **Bumbo** floor seats | **12247** (2012-08-15) | 4M | 19 skull fractures after the 2007 warning recall | All one-piece foam seats with leg holes | Repair: **restraint belt kit** | **No belt = unremedied.** "Bumbo" raised on the front. |
| 21 | **Graco strollers** (Aspen, Breeze, Capri, Cirrus, Glider, Kite, LiteRider, Sierra, Solara, Sterling, TravelMate) | **15032** (2014-11-20) | 4.7M | 6 fingertip amputations | DOM 2000-08-01 to 2014-09-25; label at the bottom of the rear leg | Hinge repair kit | External sliding fold-lock hinges |
| 22 | **AirClub convertible bassinet / bedside sleeper** | **26342** (2026-03-26) | 110,400 | None reported | "Product Model QX-831" under the mattress pad; Amazon, 2023–2025 | Replacement strap kit | Quilted grey, beige or purple bassinet |
| 23 | **Car seats (NHTSA)**: Graco toddler and booster buckles | **NHTSA 14C001000** (Feb 2014) | 4.18M | — | Cozy Cline, Comfort Sport, Classic Ride 50, My Ride 65/70, Size4Me 70, Smart Seat, Nautilus … (MY 2009–2013) | Replacement buckle | Harness buckle |
| 24 | **Car seats (NHTSA)**: Graco SnugRide infant seats | **NHTSA 14C004000** | 1.91M | — | SnugRide (various), made July 2010 to May 2013 | Buckle | — |
| 25 | **Car seats (NHTSA)**: recent | **24C002000** Nuna RAVA (608,786; DOM 2016-07-16 to 2023-10-25; harness adjuster); **25C010000** Evenflo Gold/Revolve360 Slim (324,997; DOM 2022-12-01 to 2024-12-08; headrest foam); **25C006000** Safety 1st Grow & Go Sprint (179,845; CC321GYU and others); **26C006000** Britax B-Safe Gen 2 / FlexFit / Plus / 35 / Ultra / Endeavours (114,660; DOM 2020-12-28 to 2023-05-10; handle screw; **remedy still under development** as of the 2026-09-30 letters) | — | — | NHTSA API, campaign number lookup **[T]** | Kits | Match on brand, model and DOM against the BGMAN–ENDMAN range |

**CPSC unilateral warnings** to include manually, because they are not in the API **[P]**: Fasando baby loungers (Warning 26-097, 2025-11-20, **1 infant death**, about 6,200 units, Amazon); Jocute loungers (2025); Aila Aiden loungers, LullaBear Choco Bear support cushions, Yemkezo carriers, Flyboss bouncers, Fyzvexo, XIOYIG and CiuseiAnx walkers, Tuyedoqe travel bassinets (all 2026); Hiccapop play yard mattresses (25-174, 2025-03-06, about 108,000 units); Beianpp and Criblike mattresses. There is also the Fisher-Price Infant-to-Toddler / Newborn-to-Toddler Rockers warning (2022-06-14, 13 deaths) and a Kids2 Bright Starts Rocker warning (1 death in 2019) **[S]**.

**Trend from the API dump [T]:** recalls of infant products whose title cites a violated mandatory standard numbered 1 in 2022, 12 in 2023, 22 in 2024, 51 in 2025, and 32 in 2026 through Oct 22. Most are low-volume products from Amazon, Walmart.com, Temu and SHEIN sellers. The volume of brand-name recalls is shrinking while violation recalls of marketplace sellers grow, so photo recognition must handle generic, unbranded loungers and walkers.

---

## C. CPSC Recalls API

### C1. Basics

| Item | Value | Tag |
|---|---|---|
| Base URL | `https://www.saferproducts.gov/RestWebServices/Recall` | [P][T] |
| Flattened variant | `https://www.saferproducts.gov/RestWebServices/RecallDelimited`: collections become pipe-separated quoted strings | [P][T] |
| Format | XML by default; add `format=json` | [P][T] |
| API key | **None** | [T] |
| CORS | `access-control-allow-origin: *` (methods GET, POST, PUT, DELETE, OPTIONS), so it can be called from the browser | [T] |
| Rate limits | None documented; none hit in about 60 calls. Plan for a nightly bulk pull plus an incremental sync. | [T] |
| Programmer's Guide | v1.4, 2018-09-17: https://www.cpsc.gov/s3fs-public/RecallRetrievalWebServicesProgrammersGuide20180917.pdf | [P] |
| Matching | Case-insensitive substring ("wildcard") on each field; parameters combine with AND | [P][T] |
| **Bulk download** | The API has no official bulk endpoint, but `?format=json` with no filters, or with any **unknown** parameter, returns **all records**: 10,058 recalls, 1973-06-08 to 2026-10-22, 27.8 MB, about 10 s. The guide warns that made-up parameters return everything, so watch for typos in production. | [P][T] |
| RSS | `https://www.cpsc.gov/Newsroom/CPSC-RSS-Feed/Recalls-RSS` works (recalls only, no warnings). The widget feeds are `cpscrss.js` and `childrss.js`. | [T] |
| Recall number format | Fiscal-year prefix: `27xxx` is FY2027, which started 2026-10-01, and URLs use `/Recalls/2027/…`. Recall 25009 is dated 2024-10-10. | [T] |

### C2. Parameters (from the guide) and how each tested

| Parameter | Works? (2026-10-25) |
|---|---|
| `RecallID`, `RecallNumber` | Yes |
| `RecallDateStart`, `RecallDateEnd` (YYYY-MM-DD) | Yes (2026-09-01 to 2026-10-25 returned 81) |
| `LastPublishDateStart`, `LastPublishDateEnd` | Yes; use for incremental sync |
| `RecallTitle`, `RecallDescription`, `RecallURL`, `ConsumerContact` | Yes. `RecallDescription=BGB32` found Snuga. |
| `ProductName` | Yes (`lounger` returned 25) |
| `Manufacturer`, `Retailer`, `Importer`, `Distributor` | Yes |
| `ImageURL`, `InconjunctionURL`, `Injury`, `Remedy`, `RemedyOption` | Yes |
| `Hazard` | **Broken**: 0 results, including the guide's own example (`RecallTitle=stroller&Hazard=pinch`) |
| `UPC` | **Returned 0** for a UPC that exists in the data (840059614922). Match UPCs locally. |
| `ManufacturerCountry` | **Returned 0** for China. Filter locally. |
| `ProductType` (undocumented) | Works (`Cribs` returned 142), but `Products.Type` is empty for every 2017–2025 recall |

### C3. JSON fields

Top level: `RecallID`, `RecallNumber`, `RecallDate`, `Description`, `URL`, `Title`, `ConsumerContact`, `LastPublishDate`, `Products[]`, `Inconjunctions[]` (e.g. Health Canada link), `Images[]`, `Injuries[]`, `Manufacturers[]`, `Retailers[]` (free text, includes sale dates and prices), `Importers[]`, `Distributors[]`, `SoldAtLabel` (always null), `ManufacturerCountries[]`, `ProductUPCs[]`, `Hazards[]`, `Remedies[]`, `RemedyOptions[]`.

`Products[]` has `Name`, `Description`, `Model`, `Type`, `CategoryID` and `NumberOfUnits` (free text such as "About 3.3 million (35,000 in Canada)"). `Images[]` has `URL` and `Caption`. `Hazards[]` has `Name`, `HazardType` (empty) and `HazardTypeID` (empty). `Remedies[]` has `Name`. `RemedyOptions[]` has `Option` (Refund, Repair, Replace, …).

**Field coverage across the 10,058 records [T]:**
- `Products.Model`: **0 records populated**. Model numbers appear only in `Description` free text, often as tables flattened into a string. You will need regex extraction.
- `ProductUPCs`: 458 records.
- `Images`: 8,382 records, with 22,701 images, of which 21,617 have captions. Every recall since 2015 has images. Hosts are `www.cpsc.gov/s3fs-public/…` plus 4,248 legacy `~/link/….jpg` URLs, which still return 200. Some filenames contain spaces, so URL-encode them.
- `Products.Type` / `CategoryID`: populated for 2015, part of 2016, and 92 of 490 in 2026. **Empty for 2017–2025.** Category filtering is unreliable; classify by keyword on Title, Description and Products.Name.
- `Injuries.Name`: free text including death counts. Parse it with regex, e.g. "(\d+|one|two…) … deaths".

**Infant-relevant Type values and CategoryIDs (only where populated):** Cribs 1902; Crib Mattress/Bumper Pad 1902; Bumper Pads 1867; Bassinets/Baby Hammocks 1537; Bassinets and Cradles 67558; Play Yards 67569; Playpens/Play yards 2073; Strollers 67584 / 2155; Strollers and Car Seats 67582; Infant Carriers/Slings/Backpacks/Car Seats 2010; Baby Carriers 67549; Baby Walkers/Stationary Entertainers 1835; High Chairs 67565; Swings (Baby/Cradle) 2161; Portable Baby Swings 67570; Bouncers/Jumpers 1861; Baby Seats (Non-Bath) 1834; Bathtubs & Seats (Baby) 1845; Baby Bathtub Seats or Rings 807; Baby Mattresses and Pads 67555; Pacifiers & Accessories 2057; Pacifiers and Teething Rings 67568; Teething Items 2166; Rattles 2093 / 68372; Gates (Safety) 1972; Changing Tables 1878; Bed Rails 67745; Toys (Crib) 2210; Crib Mobiles and Gyms 67560 **[T]**.

### C4. Example queries (all tested 2026-10-25)

```
# One recall by number
https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallNumber=21198
# Brand or keyword in the title
https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallTitle=Boppy
# Model number inside the description text
https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallDescription=BGB32
# Product name keyword
https://www.saferproducts.gov/RestWebServices/Recall?format=json&ProductName=lounger
# Date window
https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallTitle=sleeper&RecallDateStart=2019-01-01&RecallDateEnd=2019-12-31
# Incremental sync since the last run
https://www.saferproducts.gov/RestWebServices/Recall?format=json&LastPublishDateStart=2026-10-01
# Remedy type
https://www.saferproducts.gov/RestWebServices/Recall?format=json&RemedyOption=Repair&RecallDateStart=2026-01-01
# Full database (bulk)
https://www.saferproducts.gov/RestWebServices/Recall?format=json
```

**Recommended architecture:** pull the full JSON once and store it locally (SQLite or JSON). Build a keyword classifier for the "infant" subset (title regex covering crib, bassinet, sleeper, lounger, swing, bouncer, walker, stroller, carrier, high chair, bath seat, play yard, bumper, nursing pillow, and so on). Extract model tokens from `Description` with a regex such as `[A-Z]{1,5}-?\d{2,6}[A-Z0-9-]*`. Match the VLM's {brand, product type, model, DOM} against the index. Hard-code the "all models" recalls in Section B (Rock 'n Play, Kids2, Boppy lounger, Nap Nanny), because they have no model numbers to match.

### C5. Gaps and companion sources

- **CPSC Product Safety Warnings are missing from the API [T].** They live at `cpsc.gov/Warnings/{year}/…`. In this environment, cpsc.gov HTML pages returned **403 (Akamai)** to curl even with a browser user agent, though PDFs, images and the RSS feed loaded. A third-party Apify actor ("US CPSC Recall and Safety Warning Monitor") claims to cover warnings **[S]**. For the demo, hand-curate about 20 infant warnings (see the list after Section B).
- **NHTSA (car seats):**
  - The API endpoint `https://api.nhtsa.gov/recalls/campaignNumber?campaignNumber=24C002000` works with no key **[T]**. It returns Manufacturer, Component, PotentialNumberofUnitsAffected, Summary, Consequence, Remedy, Make, Model and ModelYear.
  - `recallsByVehicle` returned 0 for car seat makes and models (GRACO/SNUGRIDE/9999) **[T]**. NHTSA documents no product-type or child-seat recall endpoint **[P]** (NHTSA Datasets and APIs page).
  - **Bulk flat file:** `https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip` (14.9 MB zipped, 312 MB unzipped, tab-delimited; layout in `RCL.txt`, updated May 2025) **[T]**. Filter `RCLTYPECD = 'C'` for child restraints: 65 campaigns since 2010 **[T]**. Fields include CAMPNO, MAKETXT, MODELTXT, **BGMAN and ENDMAN** (the manufacture date range, needed for DOM matching), POTAFF, DESC_DEFECT, CORRECTIVE_ACTION, and MFR_COMP_PTNO.
- **Health Canada:** `Inconjunctions[].URL` links joint recalls.

### C6. Image copyright

- CPSC's Privacy Policy page has a copyright section. It says text, brochures and posters are public information that may be freely distributed, copied or linked, as long as CPSC endorsement isn't implied and CPSC is credited. It says **recall notices, including photos of recalled items, may be copied and distributed without permission**. Other photos on CPSC sites may be licensed from stock services or other copyright holders and may need permission **[P]** (cpsc.gov/About-CPSC/Policies-Statements-and-Directives/Privacy-Policy, accessed 2026-10-25, undated).
- Many recall photos are supplied by the firm, so they are not formally US government works under 17 U.S.C. 105. CPSC's stated permission is the practical basis for reuse **[U]**.
- An older CPSC recalls page says information on those pages is public and may be freely distributed, copied or linked (business.cpsc.gov/recalls/privacy.html) **[P]**.
- **Recommendation:** display recall photos with the caption "Image: U.S. CPSC recall notice #NNNNN" and a link. Don't imply endorsement.

---

## D. Car seats: expiration and used-seat rules

### D1. Federal position

- **No federal expiration requirement.** FMVSS 213 contains no expiration or useful-life provision (eCFR text searched 2026-10-25) **[P]**.
- **Required labels** (49 CFR 571.213 S5.5.2) **[P]**: model name or number; manufacturer; "Manufactured in ____" with month and year; place of manufacture; a compliance statement. Seats made before 2025-06-30 also carry an attached registration card showing model and DOM (S5.8.1); later seats use an upgraded form (S5.8.1.1).
- **NHTSA Used Car Seat Safety Checklist** (nhtsa.gov/car-seats-and-booster-seats/used-car-seat-safety-checklist, undated, accessed 2026-10-25) **[P]**:
  1. The seat has not been in a moderate or severe crash.
  2. It has labels with DOM and model number. NHTSA says you need these to check recalls and to judge whether the seat is too old.
  3. It has no open recalls. If it does, contact the manufacturer.
  4. It has all its parts.
  5. It has its instruction manual. A replacement can be had from the manufacturer.
- **NHTSA "Car Seat Use After a Crash"** **[P]**: replace a seat after a moderate or severe crash. A crash counts as minor only if all five of these hold: the vehicle was driven away; the door nearest the seat was undamaged; nobody was injured; the airbags did not deploy; and there is no visible damage to the seat.
- **CPSC Reseller's Guide** tells resellers to check the expiration with NHTSA and the manufacturer, and to destroy recalled seats that can't be repaired **[P]**.
- **JPMA** guidance (no more than 6 years from DOM) appears only via Indiana University's injury prevention page **[S]**.

### D2. Expiration by brand

| Brand | Useful life (from DOM unless noted) | Where the date is | Source and date | Tag |
|---|---|---|---|---|
| **Graco** | Belt-positioning boosters: **10 yr**. Harnessed seats with **steel-reinforced** belt paths: **10 yr**. Harnessed seats with **plastic-reinforced** belt paths (e.g. Contender 65): **7 yr**. | DOM on a label; useful life in the manual or **stamped into the seat** ("Do not use this child restraint after…"). Expiration = DOM + life. | gracobaby.com/carseatexpirationpage.html (accessed 2026-10-25; undated) | [P] |
| **Chicco** | By type: infant **6**; rotating convertible **8**; all-in-one **8 or 10**; harness booster **8**; booster **8**. Overall range 6–10. | **Underside of the seat or the base**; DOM label or manual | chiccousa.com/baby-talk/common-car-seat-questions-answered/ and /baby-talk/why-do-car-seats-expire/ (undated) | [P] |
| **Britax** | **6–10 yr** depending on model; exact figure in the manual's Warnings section | **Serial label** shows DOM; many models made after 2018 also print the expiration date. Britax strollers don't expire. | us.britax.com/support/faq/expiration-dates (undated) | [P] |
| **Evenflo** | **All car and booster seats now 10 yr.** Seats made before Jan 2025 may differ, so the label governs. | DOM label on the bottom, side or back, with model and **expiration date** | evenflo.com blog "When Do Car Seats Expire?" (2026-03-17) | [P] |
| **Safety 1st** (Dorel) | **8–12 yr** depending on product; lifespan in the manual | DOM sticker on the **back** of the seat | safety1st.com/pages/car-seat-expiration (accessed 2026-10-25) | [P] |
| **Maxi-Cosi** (Dorel) | **8–12 yr**, same wording as Safety 1st | DOM sticker on the back | maxicosi.com/us-en/car-seat-expiration (accessed 2026-10-25) | [P] |
| **Cosco** (Dorel) | Scenera NEXT: **8 yr** if made after 2013-12-14, otherwise 6. No primary page found (coscokids.com expiration and FAQ pages return 404). Sister brands say 8–12. | Expiration embossed on the seat and listed in the manual | twiniversity.com (updated 2025-08-12) | **[S]** |
| **Clek** | **9-year expiration** for foonf, fllo, liing and oobr | DOM on the **underside** of the carrier and the base (Clek's 2019 liing notice) | clekinc.com product pages (accessed 2026-10-25); Clek CSN PDF of 2019-06-17 | [P] |
| **Nuna** | Not stated in the manual excerpt. Retailers say **PIPA ~7 yr**; MacroBaby says "7 years from the original purchase date", which conflicts with a DOM basis. | Manual: check the label on the **underside of the base or the seat** for the expiration date | Nuna PIPA rx US manual [P]; macrobaby.com [S] | **[U]** for years. Read the printed date. |
| **UPPAbaby** | MESA V3: **7 yr** from DOM (retailer). The official comparison PDF (2026-02) gives only the use period, not expiration. | Expiration label on the bottom of the carrier **and** the base | strolleria.com [S]; UPPAbaby comparison PDF [P] | **[U]** |
| Others (Diono, Cybex, Peg Perego, Baby Trend, Doona, Joie) | Not researched | — | — | [U] |

**App logic:**
1. Use the OCR'd explicit expiration ("Do not use after", "Expiration date", "Expires") if present.
2. Otherwise use DOM + model life, then + brand default; tag the result "estimated".
3. If there is no DOM or model label, return CHECK and cite the NHTSA checklist.
4. **Infant seat bases may have their own expiration** **[S]**.

---

## E. Missing safety-critical parts checklist

| Category | Check (from photos and text) | Why / source |
|---|---|---|
| **Any durable infant product** | Permanent label with manufacturer, model, and month/year of manufacture (16 CFR 1130.4, required since 2010-06-28 for most categories). Product is not wobbly or broken. | 16 CFR 1130 [P]. Reseller's Guide says not to sell durable infant products that are missing parts or wobbly [P]. |
| **Full-size crib** | All screws, bolts and brackets present and tight; mattress support present and the right way up (Delta stabilizer-bar recall); no missing or cracked slats; slat gap ≤ 2 3/8 in.; corner posts ≤ 1/16 in.; no headboard or footboard cutouts; firm, tight-fitting mattress; **all four safety pegs present** on Delta "Safety Peg" cribs; no drop side. | CPSC Crib Safety Tips [P]; recalls 09017, 10273 [T] |
| **Play yard / mesh crib** | Mesh holes < 1/4 in.; no tears, holes or loose threads; top-rail cover intact; no missing or loose staples; **original mattress only** (or an aftermarket one naming the brand and model); no extra padding or stacked mattresses; recalled **inclined sleeper inserts** removed. | CPSC Crib Safety Tips [P]; CPSC Warning 25-174 [P]; recalls 19151, 21052 [T] |
| **Bassinet / bedside sleeper** | Original mattress pad; legs and stand (required under 16 CFR 1218 / 1236); **bed-attachment straps** on bedside sleepers; fabric intact over metal bars (Simplicity). | eCFR 1218 / 1222 [P]; recalls 26342, 08381 [T] |
| **Car seat** | DOM and model labels; **instruction manual**; all parts, including harness straps, **chest clip**, crotch buckle, infant inserts as sold, **base** (infant seats), LATCH connectors and top tether; no visible cracks; crash history disclosed. | NHTSA Used Car Seat Checklist [P]; crash criteria [P]. Chest clip and LATCH as specific items are **[S]**: NHTSA says "all parts" without listing them. |
| **Stroller** | Harness or restraint; working fold-lock hinges (Graco 15032); for Peg Perego Venezia and Pliko-P3, a two-cup tray or bumper bar rather than the recalled single-cup tray. | Recalls 15032, 12232 [T] |
| **Swing** | Harness present. **Snuga**: headrest and body insert should be absent (that is the remedy). **MamaRoo** (3-point): the strap fastener should be present. | Recalls 25009, 22200 [T] |
| **Floor seat (Bumbo)** | Restraint belt present (repair kit) | Recall 12247 [T] |
| **Walker** | Rubber stair-fall gripping strips underneath, or a base at least 36 in. wide | Reseller's Guide [P]; 16 CFR 1216 [P] |
| **Bath seat** | No suction-cup-only design from before 2010-12-06; permanent drowning warning present | Reseller's Guide [P] |
| **Baby monitor (Angelcare sensor pad)** | Rigid cord cover present | Recall 14028 [T] |
| **Battery toys and mobiles** | Battery compartment secured by a screw | 16 CFR 1263 / 1250 [P] |
| **Nursing pillow / lounger** | No restraint straps (prohibited by 1242 and 1243) | eCFR [P] |

---

## F. Marketplace policies

| Platform | Policy (paraphrased) | Baby-specific items | Car seats | Source / date | Tag |
|---|---|---|---|---|---|
| **eBay** | Recalled Items policy (help id 4300) prohibits items recalled by a manufacturer or agency, items banned by law, and identified hazards. | Prohibited: **infant inclined sleepers, crib bumpers**, weighted infant blankets, swaddles and sleep sacks, sleep bags that can cover the head, **baby loungers**, pillows marketed for sleep, sleep positioners and nests, anti-roll products, SIDS-prevention claims, self-feeding devices, protective baby helmets. Allowed only if compliant: nursing pillows meeting 1242 (label image plus disclaimer required) and support cushions meeting 1243. **Used cribs not allowed**; new cribs only if they meet the 2011 standard. | **Used car seats not allowed**; new ones only with an FMVSS 213 statement | ebay.com/help/Policy/-/Recalled_items_policy?id=4300 (accessed 2026-10-25; undated) | [P] |
| **Facebook Marketplace (Meta)** | Commerce Policies prohibit recalled products. KID quoted the wording that listings may not promote "buying or selling of recalled products". | After CR's 2026 evaluation, Meta said it **added drop-side cribs, water beads and weighted sleep wearables** to its prohibited list, and that it uses automated detection plus human review and is adding recall warning labels. | Meta reviewed its **automated car seat warnings**; CR couldn't trigger them on retest. | Policy page wouldn't load here (robots or HTTP 400). Wording via kidsindanger.org (c. 2019) [S]; Quartz 2026-10-07 [S]; KOLD 2026-09-25 [S] | **[U]** for current policy text |
| **Craigslist** | The prohibited list includes "recalled items". The /about/recalled_items page says unlawful sales of recalled items are prohibited and links to CPSC, the Reseller's Guide, SaferProducts.gov, Recalls.gov and Safercar.gov. | No category list | Not specific | craigslist.org/about/prohibited and /about/recalled_items (accessed 2026-10-25) | [P] |
| **OfferUp** | Prohibited Items Guidelines: recalled items not allowed. | Named examples (non-exhaustive): **Rock 'n Play**, Rock 'n Glide, Soothe 'n Play glider, **drop-side cribs**, **Boppy newborn loungers**, Momaid loungers, **crib bumpers** (non-padded mesh liners allowed), IKEA 2016 dressers. Fisher-Price Infant-to-Toddler rockers listed under "warnings". Removes false claims of CPSC certification. | Not addressed | help.offerup.com/hc/en-us/articles/360032329711 (**updated 2026-09-15**, via WebFetch) | [P] |
| **Mercari** | No banned children's product list at the time of CR's tests; committed to adding a "recalled or banned" report option. | — | — | CR evaluation 2026-09-23 [S]; the help site was unreachable from here | [S] |

---

## G. Evidence of the problem

**Deaths and injuries (CPSC primary data)**

- **CPSC nursery products report, Aug 2026** (Ted Yang, CPSC Epidemiology) **[P]**:
  - About **71,100** emergency-department-treated injuries to children under 5 in 2025 (385 per 100k).
  - **522 deaths in 2021–2023**, an average of 174 a year. By product: cribs and mattresses 159, bassinets and cradles 130, play yards 97, portable swings 20, infant carriers 16, bath seats 15, bouncers 14, inclined sleep products 11.
  - In-bed sleepers: **22 deaths** in 2021–2023.
  - Inclined-sleep deaths fell from **27 in 2019 to 1 in 2023** after the ban.
  - URL: cpsc.gov/s3fs-public/Nursery-Products-Annual-Report-2026.pdf
- **2025 report (Mar 2026)**: 70,000 ED injuries in 2024; 537 deaths in 2020–2022 **[P]**.
- **Inclined sleep products** (86 FR 33022, 2021-06-23) **[P]**: 59 fatal incidents in 2005–June 2019 (from the SNPR), plus 10 more fatalities reported before the final rule.
- **Crib bumpers** (85 FR 18878, NPR of 2020-04-03) **[P]**: 113 fatalities in 1990–Mar 2019; CPSC staff classified 30 as incidental. A 2022-11-15 Schakowsky press release cites CPSC counts of 83 bumper deaths and 97 inclined sleeper deaths **[S]**.
- **Drop-side cribs** **[P]**:
  - CPSC 2010-05-07: 32 deaths since 2000 plus 14 possible; 11 recalls covering more than 7M drop-side cribs in 5 years.
  - CPSC 2010-12-17: more than 11M cribs recalled since 2007.
- **Nursing pillows** (89 FR 85388) **[P]**: 154 fatal incidents in 2010–2022; 94% involved infants 6 months or younger.
- **Infant support cushions** (89 FR 87467) **[P]**: 79 fatalities in 2010–2022.
- **Rockers** (88 FR 73551 NPR) **[P]**: 11 fatalities in 2011–2022, 9 of them during sleep.
- **Product-level** **[P/T]**: Rock 'n Play about 100 deaths; Kids2 sleepers 15; Boppy lounger 10; Fisher-Price rockers 13 (warning); Snuga 5; Rock 'n Glide 4; MamaRoo 1; Fasando lounger 1 (2025 warning).

**Marketplace evidence**

- **Consumer Reports evaluation, published 2026-09-23** (testing May–June 2026; findings shared July 2026) **[P]**. CR tested Facebook Marketplace, eBay, Mercari and Craigslist for drop-side cribs, crib bumpers, inclined sleepers and in-bed sleepers.
  - **In-bed sleepers:** Facebook had 50 in its first 65 listings (CR stopped counting); Mercari 12 of 400; eBay 7 of 400; Craigslist 2 of 49.
  - **Facebook was the only platform with all four banned types.** eBay had bumpers, drop-side cribs and in-bed sleepers; Mercari had bumpers and in-bed sleepers; Craigslist had in-bed sleepers.
  - **Reported listings:** Facebook, Craigslist and Mercari removed none. eBay removed a bumper within 30 minutes but not an in-bed sleeper.
  - Follow-up coverage ran 2026-09-25 (KOLD/AZFamily), 2026-10-06 (News4JAX) and 2026-10-07 (Quartz) **[S]**. I found no separate October 2026 CR investigation **[U]**.
- **eBay** says it blocked 21M unsafe listings worldwide in 2025 and 98.2% of prohibited listings at creation (via Quartz) **[S]**.
- **CPSC letter to Meta, 2023-06-06** **[P]**: CPSC made about **1,000 takedown requests a month** for Boppy loungers over the prior year; 10 Boppy deaths. The Aug 2023 House Energy & Commerce letter cites "thousands of takedown requests" **[S]**.
- **CPSC enforcement pace:** a record 28 recalls and warnings in the week of 2025-05-15, all of the warnings unilateral (MoFo, 2025-06-30) **[S]**. API trend: see the end of Section B **[T]**.

**Parents buying used gear**

- **Mott Poll**, U-M C.S. Mott Children's Hospital, Vol. 43 Issue 3, **2023-05-15**, n = 932 parents of children aged 0–7 **[P]** (mottnpch.org/node/3000):
  - **53%** have used pre-owned equipment.
  - By product: cribs 28%, high chairs 24%, strollers 17%, playpens 15%, bath seats 13%, infant car seats 7%, boosters 8%.
  - **63%** find it hard to tell whether used equipment is safe.
  - Only **49%** are "very likely" to look up recalls.
  - Use is higher at lower incomes: 58% under $100k vs 48% above **[S via Futurity]**.
- No 2024–2026 survey of used baby gear purchasing was found **[U]**.

---

## H. Competitor check (2026)

| Product | What it does | Input types | Sources | Checks third-party listings or screenshots? | Banned categories? | Car seat expiration? | Tag |
|---|---|---|---|---|---|---|---|
| **Tutela: Baby Product Scanner** (iOS; Sam Daniel; v1.0 Apr 15, v1.4 Aug 4, 2026) | 0–100 trust score from recalls, investigations, ingredients and certifications; watchlist alerts; 70k+ product catalog; comparisons | "Scan" (method unspecified) and catalog search | CPSC, NHTSA, FDA | No | No | Lifespan guides only | [S] |
| **Recalled.co** | Inventory of products you own, with recall alerts | Photo of label or model number | CPSC, NHTSA, FDA, USDA | No | No | No | [S]; SaaSHub showed it "Down" |
| **RecallSentry** (Center for Recall Safety LLC; v1.0 Jan 29, v1.1.0 Apr 14, 2026) | Household inventory with RecallMatch alerts | Barcode / UPC / QR / VIN (paid tier) | FDA, USDA, CPSC, NHTSA | No | No | No | [S] |
| **kept** (getkeptapp.com) | Home inventory; automatic CPSC recall matching | Barcode or photo | CPSC | No (mentions hand-me-downs) | No | No | [S] (post updated 2026-10-15) |
| **RecallScope** | Family recall alerts and watchlist; small sellers can check before listing | Barcode, brand, keyword, VIN | FDA, CPSC, USDA FSIS, NHTSA, plus international registries | Seller-side pre-listing check only | No | No | [S] |
| **MyParentingBook Recall Checker** (web) | Search child-product recalls | Brand, model, UPC | CPSC, FDA, NHTSA, CDC; refreshed twice a day | No | No | No | [S] |
| **Baby Label: Safety Scanner** (STREAMSLATE LLC) | Ingredient analysis and product ID from photos; recall notices | Photo | "Publicly reported recalls" (FDA mentioned) | No | No | No | [S] |
| **Pebbo** | AI ingredient analysis for baby food and cosmetics | Photo of label | — | No | No | No | [S] |
| **Kids' Recall** (Chrome; v1.0.0, 2026-07-07, 7 users) | Flags children's products on retail pages against CPSC recalls | Page context | CPSC | **Amazon only** | No | No | [S] |
| **RecallRadar** (Chrome; v1.3.5, 2026-08-30, 6 users) | Recall matches on "supported retailer" pages | Page context | Public recall records | Unspecified retailers | No | No | [S] |
| **Meta (Facebook Marketplace) native** | Automated detection, human review, car seat and generator warnings, "recall warning labels" announced 2026 | — | — | Platform-side; CR couldn't trigger the warning on retest | Partial | No | [S] |
| **GoodBuy Gear** (curated resale) | Human inspection checklists (about 30 checks for car seats); sellers attest a seat is under 8 years old and crash-free | In-warehouse | — | Its own inventory only | — | Age attestation | [S] (Modern Retail 2024-05-08) |
| Hackathon / GitHub projects | None found in Devpost or GitHub keyword searches | — | — | — | — | — | [U] (shallow search) |

**Gap:** every tool found works on products you own or on retailer pages, using barcode or model lookup. **None takes a Marketplace or Craigslist listing screenshot, identifies an unbranded item visually, applies the banned-category and date-gate rules, and checks car seat expiration.** CR's 2026 data shows the biggest risk is generic, unbranded loungers and in-bed sleepers, which barcode tools can't catch.

---

## I. Open questions and unconfirmed items

1. **Meta Commerce Policy text.** The live page couldn't be fetched. Confirm the wording and the newly added items (drop-side cribs, weighted sleep wearables) in a browser.
2. **Nuna, UPPAbaby and Cosco lifespans.** Only retailer sources were found; Nuna and Cosco primary pages weren't reachable. In the demo, read the printed expiration date rather than estimating.
3. **Do private individuals face liability for reselling recalled car seats** under 49 U.S.C. 30120(j)? NHTSA guidance on this wasn't found.
4. **One-off private crib sellers.** The statute (CPSIA §104(c)) names businesses, while 16 CFR 1219.1(b) and CPSC guidance say resale of used noncompliant cribs is prohibited and that consumers "should not resell". Phrase verdicts as "illegal to sell under federal crib rules (per CPSC)", not as personal legal advice.
5. **CPSC Warnings data feed.** No API or RSS feed for warnings was found; cpsc.gov HTML returned 403 to scripts. Find a feed or plan to scrape from a browser-like client.
6. **Peg Perego 12232 units.** The API says "About 6,223,000"; it is widely reported as about 223,000. Check the live cpsc.gov notice.
7. **Infant support cushion date.** The CFR says products manufactured after **2025-05-05**; CPSC's nursery report says "effective November 4, 2024", which is the publication date. Use the CFR date.
8. **Weighted sleep products.** Is the SIDS Act reintroduced or pending in the 119th Congress? Is there a ruling in *Dreamland Baby v. CPSC*?
9. **Infant rocker rule.** Only the 2023 NPR exists. Watch for a final rule.
10. **Measuring incline from photos.** The legal test is >10° plus marketing for sleep. Camera angle makes measuring from photos unreliable, so use "inclined + sleep-marketed" classification and listing text rather than an angle measurement. Validate on test images.
11. **State laws.** Pre-SSBA state bumper bans and any state car seat resale laws were not researched.
12. **Survey data after 2023.** No 2024–2026 survey of used baby gear purchases was found.
13. **Civil penalty adjustment** due Dec 1, 2026. Amounts may change.
14. **Chest clip and LATCH as "required parts".** NHTSA's checklist says "all parts" without listing them. Use the seat's manual.

---

## J. Sources (accessed 2026-10-25 unless noted)

**Statutes and regulations**
- 15 U.S.C. 2052 (definitions; motor vehicle equipment exclusion): https://www.law.cornell.edu/uscode/text/15/2052
- 15 U.S.C. 2056a (CPSIA §104; cribs at (c)): https://www.law.cornell.edu/uscode/text/15/2056a
- 15 U.S.C. 2057 (banned hazardous products): https://www.law.cornell.edu/uscode/text/15/2057
- 15 U.S.C. 2058 (§9(g) effective date / manufactured after): https://www.law.cornell.edu/uscode/text/15/2058
- 15 U.S.C. 2068 (§19 prohibited acts): https://www.law.cornell.edu/uscode/text/15/2068
- 15 U.S.C. 2069 (§20 civil penalties; "knowingly"): https://www.law.cornell.edu/uscode/text/15/2069
- 49 U.S.C. 30112 (sale of noncompliant equipment; first-purchase exception): https://www.law.cornell.edu/uscode/text/49/30112
- 49 U.S.C. 30120 (remedies; (j) sale of recalled equipment): https://www.law.cornell.edu/uscode/text/49/30120
- eCFR Title 16 Parts 1130, 1215, 1216, 1218–1223, 1229, 1236, 1241, 1242, 1243, 1250, 1262, 1263, 1309 and 1310 (versioner API, as of 2026-10-01): https://www.ecfr.gov/api/versioner/v1/full/2026-10-01/title-16.xml?part=NNNN
- eCFR 49 CFR 571.213 (FMVSS 213): https://www.ecfr.gov/current/title-49/section-571.213

**Federal Register**
- 75 FR 81766 (2010-12-28), cribs final rule: https://www.federalregister.gov/documents/2010/12/28/2010-32178
- 75 FR 35266 (2010-06-21), infant walkers: https://www.federalregister.gov/documents/2010/06/21/2010-14323
- 75 FR 31691 (2010-06-04), infant bath seats: https://www.federalregister.gov/documents/2010/06/04/2010-13073
- 78 FR 63019 (2013-10-23), bassinets: https://www.federalregister.gov/documents/2013/10/23/2013-24203
- 85 FR 18878 (2020-04-03), crib bumper NPR (113 fatalities): https://www.govinfo.gov/content/pkg/FR-2020-04-03/html/2020-06142.htm
- 86 FR 33022 (2021-06-23), infant sleep products: https://www.federalregister.gov/documents/2021/06/23/2021-12723
- 86 FR 68244 (2021-12-01), civil penalty amounts: https://www.federalregister.gov/documents/2021/12/01/2021-26082
- 87 FR 8640 (2022-02-15), crib mattresses: https://www.federalregister.gov/documents/2022/02/15/2022-02414
- 87 FR 57756 (2022-09-21), magnets: https://www.federalregister.gov/documents/2022/09/21/2022-20200
- 88 FR 54878 (2023-08-14), ban of crib bumpers: https://www.federalregister.gov/documents/2023/08/14/2023-17355
- 88 FR 55554 (2023-08-16), ban of inclined sleepers: https://www.federalregister.gov/documents/2023/08/16/2023-17350
- 88 FR 65274 (2023-09-21), button and coin batteries: https://www.federalregister.gov/documents/2023/09/21/2023-20333
- 88 FR 73551 (2023-10-26), infant rockers NPR: https://www.federalregister.gov/documents/2023/10/26/2023-23322
- 89 FR 85388 (2024-10-25), nursing pillows: https://www.federalregister.gov/documents/2024/10/25/2024-24403
- 89 FR 87467 (2024-11-04), infant support cushions: https://www.govinfo.gov/content/pkg/FR-2024-11-04/html/2024-25181.htm
- 90 FR 57820 (2025-12-12), water beads: Federal Register API
- 91 FR 20875 (2026-04-20), swings, ASTM F2088-25: https://www.federalregister.gov/documents/2026/04/20/2026-07638
- 91 FR 45992 / 91 FR 58817 (2026-07-22 / 2026-09-17), bouncer and activity center revocation, then withdrawal: https://www.federalregister.gov/documents/2026/09/17/2026-19065

**CPSC**
- Recall API Programmer's Guide v1.4 (2018-09-17): https://www.cpsc.gov/s3fs-public/RecallRetrievalWebServicesProgrammersGuide20180917.pdf
- Recall API: https://www.saferproducts.gov/RestWebServices/Recall
- Recalls RSS: https://www.cpsc.gov/Newsroom/CPSC-RSS-Feed/Recalls-RSS
- Privacy Policy (copyright section; recall photos): https://cpsc.gov/About-CPSC/Policies-Statements-and-Directives/Privacy-Policy
- Recalls privacy notice: https://business.cpsc.gov/recalls/privacy.html
- Reseller's Guide, Pub. 254 (Jan 2013, rev. May 2014): https://www.cpsc.gov/s3fs-public/ResellersGuide_0.pdf
- Resale and Thrift Store FAQ: https://www.cpsc.gov/Business--Manufacturing/Business-Education/ResaleThrift-Stores-Information-Center/Resale-and-Thrift-Store-Frequently-Asked-Questions
- Stop Online Sale of Recalled Products: https://www.cpsc.gov/Business--Manufacturing/Business-Education/ResaleThrift-Stores-Information-Center/Stop-Online-Sale-of-Recalled-Products
- SSBA business guidance: https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Safe-Sleep-for-Babies-Act-Business-Guidance
- Infant Sleep Products guidance: https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Infant-Sleep-Products
- ISP compliance news release (2022-11-09): https://www.cpsc.gov/Newsroom/News-Releases/2023/CPSC-Tells-Manufacturers-Importers-Distributors-and-Retailers-They-Must-Protect-Infants-by-Complying-with-Infant-Sleep-Product-Rule
- Crib Safety Tips: https://www.cpsc.gov/Safety-Education/Safety-Guides/Cribs/Crib-Safety-Tips
- New Crib Standard Q&A (2011; updated 2013): https://www.cpsc.gov/onsafety/2011/06/the-new-crib-standard-questions-and-answers
- Crib Information Center: https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Full-Size-Baby-Cribs/Crib-Information-Center-
- Drop-side warning, 32 deaths (2010-05-07): https://www.cpsc.gov/Newsroom/News-Releases/2010/CPSC-Issues-Warning-on-Drop-Side-Cribs32-Fatalities-in-Drop-Side-Cribs-in-Last-9-Years
- New crib standards approved (2010-12-17): https://www.cpsc.gov/Newsroom/News-Releases/2011/CPSC-Approves-Strong-New-Crib-Safety-Standards-To-Ensure-a-Safe-Sleep-for-Babies-and-Toddlers
- Fisher-Price rockers warning, 13 deaths (2022-06-14): https://www.cpsc.gov/Newsroom/News-Releases/2022/CPSC-and-Fisher-Price-Warn-Consumers-About-13-Deaths-in-Fisher-Price-Infant-to-Toddler-and-Newborn-to-Toddler-Rockers-Advise-Rockers-Should-Never-Be-Used-for-Sleep
- Letter to Meta (2023-06-06): https://www.cpsc.gov/About-CPSC/Chairman/Alexander-Hoehn-Saric/Letter/Letter-to-Meta-CEO-Zuckerberg-from-CPSC-Commissioners
- Rock 'n Play reannouncement 23088 (2023-01-09): https://www.cpsc.gov/Recalls/2023/Fisher-Price-Reannounces-Recall-of-4-7-Million-Rock-n-Play-Sleepers-At-Least-Eight-Deaths-Occurred-After-Recall
- Fasando lounger warning 26-097 (2025-11-20): https://cpsc.gov/Warnings/2026/CPSC-Warns-Consumers-to-Immediately-Stop-Usi-Fasando-Baby-Loungers-Due-to-Risk-of-Serious-Injury-or-Death-from-Fall-and-Entrapment-Hazards-Violates-Mandatory-Standard-for-Infant-Sleep-Products-Infant-Death-Reported
- Hiccapop warning 25-174 (2025-03-06): https://www.cpsc.gov/Warnings/2025/CPSC-Warns-Consumers-to-Immediately-Stop-Using-Hiccapop-Play-Yard-Mattresses-Due-to-Risk-of-Serious-Injury-or-Death-from-Entrapment-or-Suffocation-Violations-of-the-Federal-Regulations-for-Crib-Mattresses
- Nursery Products Annual Report 2026 (Aug 2026): https://www.cpsc.gov/s3fs-public/Nursery-Products-Annual-Report-2026.pdf; also the 2025 (Mar 2026) and 2024 (Aug 2024) editions at the same path pattern
- Recall notice URLs for every recall in Section B are in the API's `URL` field (e.g. 21198 Boppy, 25009 Snuga, 22200 MamaRoo, 19112 Kids II, 21147 Rock 'n Glide, 10046 Stork Craft)

**NHTSA**
- Used Car Seat Safety Checklist: https://www.nhtsa.gov/car-seats-and-booster-seats/used-car-seat-safety-checklist
- Car Seat Use After a Crash: https://www.nhtsa.gov/car-seat-use-after-crash
- Datasets and APIs: https://www.nhtsa.gov/node/102181
- Recall API by campaign number: https://api.nhtsa.gov/recalls/campaignNumber?campaignNumber=24C002000
- Recall flat file: https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip; layout: https://static.nhtsa.gov/odi/ffdd/rcl/RCL.txt (updated May 2025)

**Manufacturers**
- Graco: https://www.gracobaby.com/carseatexpirationpage.html
- Chicco: https://www.chiccousa.com/baby-talk/common-car-seat-questions-answered/ ; https://www.chiccousa.com/baby-talk/why-do-car-seats-expire/
- Britax: https://us.britax.com/support/faq/expiration-dates
- Evenflo (2026-03-17): https://www.evenflo.com/blogs/evenflo-blog/when-do-car-seats-expire-what-parents-need-to-know
- Safety 1st: https://safety1st.com/pages/car-seat-expiration
- Maxi-Cosi: https://www.maxicosi.com/us-en/car-seat-expiration
- Clek: https://clekinc.com/products/foonf , /fllo , /liing , /oobr ; liing notice PDF (2019-06-17): https://support.clekinc.com/hc/en-us/article_attachments/9148657334541
- Nuna PIPA rx manual: https://dl.nunababy.eu/Instruction_Manual/US/PIPA-rx/Nuna_PIPArx_UserManual_US.pdf
- UPPAbaby comparison chart (2026-02): https://back.prod.uppababy.com/media/1b/15/ed/1771616314/260202_CarSeatComparison_US_Web.pdf

**Marketplaces**
- eBay Recalled Items policy: https://www.ebay.com/help/Policy/-/Recalled_items_policy?id=4300
- Craigslist: https://www.craigslist.org/about/prohibited ; https://www.craigslist.org/about/recalled_items
- OfferUp (updated 2026-09-15): https://help.offerup.com/hc/en-us/articles/360032329711-Prohibited-Items-Guidelines
- Facebook Commerce Policies (not loadable here): https://www.facebook.com/policies_center/commerce

**Evidence, news and secondary**
- Consumer Reports press release (2026-09-23): https://advocacy.consumerreports.org/press_release/banned-unsafe-baby-products-still-for-sale-on-popular-secondhand-marketplaces-consumer-reports-evaluation-finds/
- Consumer Reports article (2026-09-23): https://www.consumerreports.org/babies-kids/how-to-avoid-unsafe-used-baby-gear-when-shopping-online-a7805010094/
- Quartz (2026-10-07): https://qz.com/banned-baby-gear-secondhand-marketplaces-consumer-reports
- KOLD (2026-09-25): https://www.kold.com/2026/09/25/banned-baby-products-still-sale-secondhand-marketplaces/
- News4JAX (2026-10-06): https://www.news4jax.com/money/2026/10/06/consumer-reports-warns-parents-about-unsafe-baby-gear-being-sold-on-craigslist-ebay-facebook-marketplace-other-sites/
- Mott Poll (2023-05-15): https://mottnpch.org/node/3000
- Fox Business on the House E&C letter (2023-08-22): https://www.foxbusiness.com/lifestyle/recalled-products-tied-infant-deaths-still-being-sold-metas-facebook-marketplace-lawmakers-say
- Schakowsky press release (2022-11-15): https://schakowsky.house.gov/media/press-releases/schakowsky-c-rdenas-bill-ban-dangerous-baby-sleeping-products-takes-effect
- NCLA on weighted sleep sacks (2026-02-12): https://nclalegal.org/press_release/ncla-asks-d-c-court-to-stop-cpsc-from-making-baseless-claims-on-weighted-sleep-sacks-for-babies/
- CR on the SIDS Act (2024-08-02): https://advocacy.consumerreports.org/press_release/consumer-reports-supports-new-bill-in-congress-to-ban-weighted-infant-sleep-products
- MoFo on the CPSC weekly record (2025-06-30): https://www.mofo.com/resources/insights/250630-cpsc-issues-weekly-record-level-of-product-safety-notices
- JD Supra on the 10th Circuit magnet rule (2025-03): https://www.jdsupra.com/legalnews/tenth-circuit-denies-challenge-to-cpsc-8969891
- Kids In Danger on Facebook's recalled-products policy: https://kidsindanger.org/2019/08/facebook-bans-selling-recalled-products-yet-customers-still-unable-to-report-recalled-items
- Twiniversity on Cosco Scenera NEXT (updated 2025-08-12): https://twiniversity.com/cosco-car-seat-what-you-need-to-know-about-the-cosco-scenera-next
- Strolleria on UPPAbaby Mesa expiration: https://strolleria.com/pages/when-does-the-uppababy-mesa-series-expire
- MacroBaby on Nuna PIPA: https://www.macrobaby.com/pages/how-long-will-the-nuna-pipa-last
- Modern Retail on resale safety checks (2024-05-08): https://www.modernretail.co/operations/how-resale-marketplaces-safety-check-hard-goods-like-car-seats-strollers/
- Indiana University, Life of a Car Seat (JPMA 6-year guidance): https://preventinjury.medicine.iu.edu/child-passenger-safety/selecting-the-best-car-seat/life-of-a-car-seat

**Competitors**
- Tutela: https://apps.apple.com/app/id6761012349
- RecallSentry: https://apps.apple.com/us/app/recallsentry/id6757089047
- Recalled.co: https://www.saashub.com/recalled-co
- kept: https://getkeptapp.com/blog/baby-product-recalls/
- RecallScope: https://recallscope.com/
- MyParentingBook Recall Checker: https://myparentingbook.com/tools/recall-checker
- Baby Label: https://apps.apple.com/app/id6760225641
- Pebbo: https://apps.apple.com/st/app/id6743235328
- Kids' Recall (Chrome): https://chromeboard.com/extension/kids-recall-depnaafogfchmjpgefhamjkakbbagpog
- RecallRadar (Chrome): https://chromeboard.com/extension/recallradar-alhpbmedbpjgekhfjhnicfdpjodeknin
