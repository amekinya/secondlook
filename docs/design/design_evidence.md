# Design evidence: SecondLook + RefundRadar

Compiled 2026-10-26 under a 25-minute cap. What the tags mean:

- **[E]** published empirical evidence
- **[S]** a standard or specification
- **[P]** practitioner or vendor guidance
- **[I]** our own inference or a design call. Treat these as hypotheses to test, not as findings.
- **[C]** computed by `design_checks.py` (in this folder) with the palettes below. Rerun it with `python3 -I design_checks.py`; it exits non-zero when a proposed palette fails.

Caveat: I checked abstracts and summaries, not full texts, so effect sizes are given only where I saw them. Citations marked *(verify)* came from memory and still need their page numbers or DOI checked.

---

## (a) Evidence table

| # | Claim | Source | Year | Strength |
|---|---|---|---|---|
| 1 | People rank DANGER > WARNING > CAUTION for hazard. DANGER is far above the other two, and WARNING and CAUTION sit close together, with little agreement on which is higher. | Chapanis, *Ergonomics* 37(2) | 1994 | Strong [E]. Replicated in rows 2 and 3. |
| 2 | Signal words do raise perceived hazard over no signal word. DANGER is consistently highest, and the WARNING/CAUTION difference is small or unreliable. | Wogalter, Jarrard & Simpson, *Human Factors* 36(3) | 1994 | Strong [E] |
| 3 | Signal-word arousal strength is stable across people and tasks, but many words lie between DANGER and CAUTION with small gaps. | Hellier, Edworthy et al., *Risk Decision & Policy* 5(1) | 2000 | Moderate [E] |
| 4 | Background colour adds to perceived hazard in the order red > orange > yellow > white. Colour helps less than the signal word does. | Chapanis 1994; Braun & Silver, *Ergonomics* 38(11) | 1994, 1995 | Moderate [E] |
| 5 | Labels in colour are rated more hazardous and more readable than the same labels in black and white. | Braun, Mine & Silver, *Int J Ind Ergon* 15(3) | 1995 | Moderate [E] (n=33) |
| 6 | Colour on its own has a weak effect on risk perception. Red stands out, but orange and yellow are poorly separated. | Leonard, *Int J Ind Ergon* 23(5–6) *(verify pages)* | 1999 | Moderate [E] |
| 7 | A pictorial or icon, a border, colour and good placement all make a warning more noticeable and shorten visual search. | Laughery et al., *J Public Policy & Mktg* 12(1); Bzostek & Wogalter, *Proc. HFES* 43 | 1993, 1999 | Moderate [E] |
| 8 | Effective warnings carry four parts: a signal word, the hazard, the consequence, and how to avoid it. They should be conspicuous, brief and placed where the decision is made. | Wogalter, Conzola & Smith-Jackson, *Applied Ergonomics* 33(3) | 2002 | Strong [E] (review) |
| 9 | Naming a credible source (for example, a government agency) makes a warning more credible and compliance more likely. | Wogalter, Kalsher & Rashid, *Int J Ind Ergon* 24(2) *(verify)* | 1999 | Moderate [E] |
| 10 | Over-warning and repeated exposure lead to habituation. People pay less attention to all warnings, including the important ones. | Stewart & Martin, *J Public Policy & Mktg* 13(1) | 1994 | Moderate [E] (review) |
| 11 | The brain's response to a warning drops sharply after repeated exposure. Warnings that change their appearance ("polymorphic") habituate less. | Anderson, Kirwan, Jenkins et al., CHI '15 | 2015 | Moderate [E] (fMRI, small n) |
| 12 | In the field, click-through rates on browser warnings vary widely with design. Warnings people see often get ignored. | Akhawe & Felt, USENIX Security | 2013 | Moderate [E] (millions of impressions) |
| 13 | ANSI Z535.4 signal panels: DANGER is white on red, WARNING is black on orange, CAUTION is black on yellow, NOTICE is white italic on blue, and safety instructions are white on green. The safety alert symbol (triangle with "!") goes **only** with DANGER, WARNING and CAUTION, for personal-injury hazards. | ANSI Z535.4 (via Clarion / In Compliance) | 2023 ed. | [S] |
| 14 | Z535.1 defines the colours in Munsell notation, CIE data and chromaticity regions: Safety Red 7.5R 4.0/14, Orange 5.0YR 6.0/15, Yellow 5.0Y 8.0/12, Green 7.5G 4.0/9, Blue 2.5PB 3.5/10 *(verify against the standard)*. Commonly cited approximate on-screen hex values: red `#C8102E` (PMS 186C), orange `#FF6900` (PMS 151C), yellow `#F6D04D` (PMS 116C), green `#00843D` (PMS 355C). The hex values are not normative. | ANSI Z535.1-2022; LinkML SafetyColorEnum | 2022 | [S] for Munsell; [P] for hex |
| 15 | Red–green colour-vision deficiency affects about 8% of men and 0.5% of women of Northern European descent. Rates are lower in other populations. | Birch, *JOSA A* 29(3) | 2012 | Strong [E] |
| 16 | CVD can be simulated with a physiologically based model (Machado), or with the dichromat projection of Brettel/Viénot. | Machado, Oliveira & Fernandes, *IEEE TVCG* 15(6); Brettel, Viénot & Mollon, *JOSA A* 14(10) | 2009, 1997 | Strong [E] (standard methods) |
| 17 | **With the ANSI reference colours, Safety Red and Safety Green collapse under deuteranopia (ΔE2000 6.4) and in greyscale (5.3).** Their CIELAB lightness is nearly equal (L\* 43 vs 48). DANGER and "all clear" are therefore the hardest pair to tell apart, which is the worst possible confusion. | [C] `design_checks.py` (Machado 2009, severity 1.0) | 2026 | [C] |
| 18 | The Okabe-Ito palette (8 colours) was built so people with CVD can still tell the colours apart. Adding a 9th colour (grey) breaks it: reddish purple vs grey drops to ΔE 6.2 under deuteranopia [C]. | Okabe & Ito, *Color Universal Design*; Wong, *Nature Methods* 8 | 2008, 2011 | [P]/[E] |
| 19 | People judge a website's credibility mostly by how it looks. In a study of 2,684 participants, 46.1% of comments mentioned the design's "look". | Fogg et al., DUX '03 (Stanford Web Credibility) | 2003 | Moderate [E] (comment coding) |
| 20 | People form an aesthetic first impression in about 50 ms, and it is highly consistent with judgements made later. | Lindgaard et al., *Behaviour & IT* 25(2) | 2006 | Strong [E] |
| 21 | Visual complexity and colourfulness predict first-impression appeal, and moderately low complexity scores best. | Reinecke et al., CHI '13 | 2013 | Moderate [E] |
| 22 | Health-site users reject sites on design cues such as clutter, ads and a poor look before they read the content. | Sillence et al., CHI '04 | 2004 | Moderate [E] (qualitative) |
| 23 | Among red, blue, green and black colour schemes on finance, legal and medical sites, blue was rated most trustworthy and black least. The effect was significant but "limited". | Alberts & van der Geest, *Tech. Communication* 58(2) | 2011 | Weak–moderate [E] (n>200) |
| 24 | Showing a numeric range ("between X and Y") barely lowers trust in the number or its source. A vague verbal hedge ("there is some uncertainty") lowers trust more. | van der Bles et al., *PNAS* 117(14) (5 experiments, n≈5,800) | 2020 | Strong [E] |
| 25 | Verbal probability words ("likely", "very likely") are read very differently by different people. Pair them with numbers. | Budescu et al., *Nature Climate Change* 4 | 2014 | Strong [E] |
| 26 | Showing forecast uncertainty improves lay decisions and protects trust when a forecast turns out wrong. | Joslyn & LeClerc, *J Exp Psych: Applied* 18(1) | 2012 | Moderate [E] |
| 27 | Precise numbers are read as a sign of confidence, so false precision on an estimate implies more certainty than you have. | Jerez-Fernandez, Angulo & Oppenheimer, *Psych Science* 25(2) *(verify)* | 2014 | Moderate [E] |
| 28 | Reading speed holds steady above a "critical print size", which is roughly 0.2° of visual angle at the x-height for normal vision. Low-vision readers need larger text. | Legge & Bigelow, *J Vision* 11(5):8 | 2011 | Strong [E] (review) |
| 29 | Serifs have little effect on legibility. Spacing and size matter more. | Arditi & Cho, *Vision Research* 45(23) | 2005 | Moderate [E] |
| 30 | A larger x-height and more distinct letterforms (il1, rn/m) improve legibility. | Sheedy et al., *Human Factors* 47(4); Beier & Larson, *Info Design J* 18(2) | 2005, 2010 | Moderate [E] |
| 31 | No single font is fastest for everyone. Each person's fastest font varies, by up to about 35% in reading speed. | Wallace et al., *ACM TOCHI* 29(4) | 2022 | Moderate [E] (n≈352) |
| 32 | Atkinson Hyperlegible separates easily confused glyphs (I/l/1, 0/O, B/8) for low-vision readers. **I found no independent peer-reviewed legibility trial.** The Braille Institute reported its own quantitative study (CSUN 2024), but it was not published as a paper. | Braille Institute; CSUN AT Conf. | 2019, 2024 | Weak [P] |
| 33 | On screen, a line of about 55 characters gave good comprehension, while longer lines (about 100) were read faster when scrolling. Typographic convention is 45–75 characters per line, with 66 as the ideal. | Dyson & Haselgrove, *IJHCS* 54(4); Bringhurst, *Elements of Typographic Style* | 2001, 2004 | Moderate [E] / [P] |
| 34 | Accuracy ranking for chart encodings: position on a common scale > position on non-aligned scales > length > angle > area > shading/colour. Stacked-bar segments sit on non-aligned baselines, so people read them less accurately. | Cleveland & McGill, *JASA* 79(387) | 1984 | Strong [E] |
| 35 | A crowdsourced replication on Mechanical Turk confirmed the ranking. Judgements of stacked or non-aligned segments had higher error than aligned bars. | Heer & Bostock, CHI '10 | 2010 | Strong [E] |
| 36 | In bar-chart comparisons, the distance between the bars being compared and any distractor bars changes the error. Compare bars side by side. | Talbot, Setlur & Anand, *IEEE TVCG* 20(12) | 2014 | Moderate [E] |
| 37 | Colour hue is preattentive, but only about 5–7 categorical colours can be told apart quickly and reliably. Small marks need larger colour differences. | Healey, *IEEE Vis* '96; Healey & Enns, *TVCG* 18(7); Szafir, *TVCG* 24(1) | 1996, 2012, 2018 | Moderate–strong [E] |
| 38 | WCAG 2.2 contrast: AA requires 4.5:1 for text and 3:1 for large text (≥24px, or ≥18.66px bold). AAA requires 7:1 and 4.5:1. SC 1.4.11 requires 3:1 for UI components and meaningful graphics. SC 1.4.1 says colour must not be the only cue. SC 2.5.8 sets a 24×24 px minimum target. | W3C WCAG 2.2 | 2023 (upd. 2024) | [S] (the legal baseline; ADA Title II and EN 301 549 cite 2.1 AA) |
| 39 | APCA (Lc values) models perceived contrast better for colour pairs, but it is **not** a W3C standard. WCAG 3 is still a Working Draft. Typical guideline levels: Lc 90 preferred for body text, 75 minimum for body, 60 for medium text, and 45 for large or bold headings. | Somers / Myndex APCA; WCAG 3 WD | 2021–26 | [P] |
| 40 | **White on ANSI orange fails WCAG (2.89:1). Black on orange passes WCAG (7.27–8.04:1), but APCA gives only Lc ≈50–54, which is good for large bold text only.** | [C] | 2026 | [C] |
| 41 | Touch targets for thumbs need to be about 9.2 mm (discrete taps) for low error. | Parhi, Karlson & Bederson, MobileHCI '06 | 2006 | Moderate [E] |

---

## (b) Recommendations

### SecondLook (warning stamps, stressed parents, phones)

**1. Tier semantics.** Spend the signal words where the research says they actually differ.

| Tier | Use when | Signal word | Why |
|---|---|---|---|
| 1 | Banned, or recalled with a stop-use order or known deaths or serious injuries. Examples: inclined sleepers, drop-side cribs, padded crib bumpers. | **DANGER** | This is the one word that reliably reads as the highest hazard (rows 1–2). Keep it rare. [E→I] |
| 2 | Recalled with a remedy (a repair kit, refund or replacement), or a serious hazard that can be avoided. | **WARNING** | [I] |
| 3 | A *possible* match: the model or date code isn't confirmed, or there's a minor hazard. | **CAUTION — Check model number** | People can't reliably tell WARNING from CAUTION (rows 1–3), so carry the difference **in the words** ("check model number") and not only in the signal word. [E→I] |
| 4 | Nothing matched in our sources. | **No known issues** (not a signal word) | ANSI reserves the triangle for injury hazards (row 13). "Safe" would claim more than we know. [S/I] |

**2. Palette.** Computed in `design_checks.py`.

| Tier | Band fill | Text on band | WCAG | APCA Lc | Icon (shape coding) |
|---|---|---|---|---|---|
| DANGER | `#B0001E` (L\*37) | `#FFFFFF` | 7.33 | −87.9 | Triangle with "!", white on red |
| WARNING | `#FF7A00` (L\*66) | `#000000`, **≥24px bold only** | 8.04 | 53.8 | Triangle with "!", black |
| CAUTION | `#FFD23F` (L\*86), plus a 2px `#8A6D00` border so it shows on white (`#8A6D00` vs white = 4.92:1) | `#000000` | 14.54 | 82.7 | Triangle with "!", black |
| No known issues | **Outlined chip, not a band.** Fill `#E8F5EE`, border `#2E7D5B` | `#0B5D3B` | 7.09 | 79.3 | Check in a circle (not a triangle) |
| Body text | `#FFFFFF` page | `#1A1A1A` | 17.4 | 104 | — |
| Muted text | `#FFFFFF` | `#595959` | 7.00 | 84 | — |

- **Why we move away from the raw ANSI hexes** [C]. Fills step in lightness, L\* 37 → 66 → 86 → 95, so each tier differs in **lightness** as well as hue. The worst pair under protan, deutan and tritan simulation is ΔE2000 ≥ 12.3, compared with 6.4 for the ANSI red/green pair.
  - The hues still read as red, orange and yellow, so the ANSI association is preserved. [I]
- **Don't put white on orange** [C]. It fails WCAG at 2.89:1. APCA would actually prefer white there, and that disagreement is a known artifact of WCAG 2. We still follow both ANSI and WCAG and use black text.
- **Text on the bands.** Put only the signal word and at most a three-word hazard label on the band. The detail sentence goes on white below the band, because `#1A1A1A` on orange is APCA Lc 52, which is too low for body-size text. [C/I]
- **Redundant coding (WCAG 1.4.1)**, so tiers survive CVD and greyscale (greyscale CAUTION vs chip is ΔE 6.0) [C]. Use all four cues:
  - the word
  - icon shape: triangle vs circle-check
  - fill vs outline
  - fixed position: the stamp always sits top-left of the listing image

**3. Stamping many listings on one page** (habituation, rows 10–12) [I unless noted]
- Put a page-level summary first: **"2 DANGER · 1 WARNING · 3 to check · 42 no known issues"**. Tapping a count jumps to those listings.
- Stamp loudly **only** when there's a match (tiers 1–3). Tier 4 gets the small chip, or nothing at all on dense grids. If everything is stamped, nothing stands out.
- Sort or filter so flagged listings come first. Never let DANGER scroll off the first screen.
- Keep the stamp format constant so people recognise it. Make the content specific (product name, hazard, recall date), which fits the finding that specific, varied content habituates less (row 11).
- Each flagged stamp gets the four parts from row 8, plus the source from row 9. Example:
  > **⚠ DANGER — Recalled infant sleeper.** Infant deaths reported. Do not buy or use for sleep. *Source: CPSC recall 19-xxx, Apr 2019.*

**4. Type and size**
- **Typeface.** Use **Atkinson Hyperlegible Next**, which disambiguates I/l/1 and 0/O. That matters when people match model numbers and date codes.
  - The evidence for the font itself is weak (row 32), while the evidence for distinct glyphs is moderate (row 30).
  - Fallback is system-ui. [I]
- **Body size on mobile is 17–18px.** Calculation [I]: with an x-height of about 0.5 em at about 0.164 mm per CSS px (an iPhone at 390 px wide), at 33 cm:
  - 16px gives 0.23° of x-height, which is just above the critical print size of 0.2° (row 28).
  - 18px gives 0.26°, which leaves margin for stress, glare and glancing.
  - Nothing goes below 14px. Signal words are 24px/700 uppercase with 0.04em letter spacing.
- **Line length:** a maximum of 65ch on desktop. Mobile naturally lands at 35–45ch. Line height is 1.5. (Row 33.)
- **Targets:** at least 44×44 px (Apple / WCAG AAA), and never below 24×24 (WCAG AA 2.5.8). One-handed thumb use is about 9 mm (row 41).

**5. Uncertainty wording** [E rows 24–25 → I]
- Never write "Safe". Write: **"No known issues found** in CPSC recalls and the Health Canada database, checked 26 Oct 2026. Recalls are added over time; check the model number on the product label."
- For a possible match, give the reason as a fact rather than a hedge: "Name matches recall 23-145; **model number not visible in photos**."

### RefundRadar (money and legal deadlines, trust)

**1. Palette and trust**
- Use a restrained interface: one blue primary `#1F4E9C` (white text 7.99:1), neutral greys and a white background. The trust effect of blue is small but positive (row 23).
  - The bigger trust levers are **low clutter and a polished look** (rows 19–22).
  - Keep red for the HOLD state only. [E/I]
- **Big dollar verdict:**
  - Colour `#0B3B2E` or `#111827` on white (12.5–17.7:1), at 40–56px/700 with tabular lining figures.
  - Don't paint it green: colour should mark state, not decoration. [I]
- **HOLD banner:**
  - Solid `#B42318` with white text (6.57:1), plus a stop or alert icon and the word **HOLD**.
  - For inline row flags, use a light tint `#FEF3F2` with `#7A1A12` text (9.74:1).
  - Have only one banner, pinned above the verdict. It can't be dismissed until the problem is resolved.
  - Structure it like a warning: what is blocked, why, the consequence, the fix, and a button. Example: "**HOLD — 3 entries can't be filed.** Missing CBP Form 7501 for entries ending -4412, -4419, -4420. Refund window closes 14 Mar 2027. [Upload forms]".
  - Use `role="alert"` only when the hold first appears. On a static page, use a labelled region. [I/S]
- **Deadline amber:** `#F5A524` with `#1A1A1A` text (8.53:1, Lc 62.8).

**2. "Where the money sits" with 9 categories** (rows 34–37)
- Don't use a single 9-segment stacked bar as the main reading. The segments sit on non-aligned baselines, so people misjudge them, and 9 hues is more than the 5–7 people can tell apart quickly.
- Recommended pair:
  1. **Overview:** one 100% bar with **3 groups only**: *Refund-ready / Needs action / Not recoverable*. Label each directly with $ and %.
  2. **Detail:** a **sorted horizontal bar chart of all 9 categories on a common baseline**, grouped under the 3 group headings, with the $ value at the end of each bar.
- **Colour encoding:** hue marks the group and lightness marks the step [C]:
  - blues `#1F4E9C` `#5B8BD9` `#A9C4F0`
  - ambers `#B25E00` `#F5A524` `#FBD38D`
  - greys `#3F3F46` `#8E8E96` `#D4D4D8`
  - Minimum ΔE2000 is 14.0 for normal vision and 11.7 under deuteranopia. **In greyscale, cross-group pairs collapse (ΔE 1.0)**, so the group label or heading must carry that difference.
- Put 1–2px white gaps between segments. The light segments are below 3:1 against white, so SC 1.4.11 needs the information in text: direct labels plus a "View as table" toggle. [S/I]

**3. Deadline timeline** [E row 34 → I]
- Use a horizontal time axis with a "Today" rule. Plot each deadline as a point or tick on the same scale, which is the most accurate encoding.
- Label every deadline with an **absolute date plus the number of days left**: "14 Mar 2027 · 139 days".
- Urgency colour (amber under 30 days, red under 7) is extra: always pair it with the days-left text and an icon.
- With more than about 8 deadlines, switch to a sorted table with a sparkline column.

**4. Numbers and tables**
- **Typeface:** Inter or IBM Plex Sans for the UI.
  - Set `font-variant-numeric: tabular-nums lining-nums` on every money column and on the verdict.
  - Right-align money and align it on the decimal point.
  - Use IBM Plex Mono for entry numbers.
  - These are typographic conventions [P].
- **Sizes:** body 16px; table 14–15px with a 1.4 line height; no text under 12px. Prose blocks are at most 70ch wide. [P/E row 33]

**5. Uncertainty wording** (rows 24–27)
- Give **a point estimate plus a numeric range, and say what drives the uncertainty**: "**Estimated refund: $41,200** (likely $38,000–$44,500). Based on 37 of 42 entries; 5 need documents before we can count them."
- Round estimates to the nearest $100. Show exact cents only for amounts that have been computed or confirmed. False precision implies false confidence (row 27).
- Don't use a bare hedge such as "approximately" or "there may be some uncertainty": vague hedges cost more trust than a range (row 24).
- Write probability words with a number: "likely (about 80%)".
- Separate the **legal deadline** ("CBP must receive by 14 Mar 2027") from **our estimate** ("we estimate processing takes 60–90 days"). Say "not legal advice" once, plainly, in the footer, not on every card. [I]

---

## (c) Automated test plan

1. **Palette gate (exists now):** `python3 -I design_checks.py`.
   - It computes WCAG ratios and APCA Lc for every text/band pair, and pairwise CIEDE2000 under Machado protan, deutan, tritan and greyscale simulation.
   - It **fails CI** if a proposed text pair misses its threshold, or if any proposed hazard or category pair drops below ΔE 10 under CVD simulation. The ΔE 10 threshold is our own choice [I].
   - The current state is **0 failures**.
2. **axe-core** (`@axe-core/playwright`). Run at viewports 390×844 and 1280×800, on a fixture page holding all 4 tiers and a 48-listing grid, and on the RefundRadar dashboard with the HOLD state on and off.
   - Rules:
     - `color-contrast` (wcag2aa)
     - `color-contrast-enhanced` (AAA; enable it explicitly for body text)
     - `target-size` (wcag22aa)
     - `link-in-text-block`
     - `svg-img-alt` / `role-img-alt` (each triangle needs an accessible name, e.g. "Danger")
     - `aria-allowed-role`
     - `region`
     - `heading-order`
     - `list`
   - Treat axe **"incomplete"** contrast results on bands as failures. axe can't resolve overlays, so check those pairs in the script instead.
3. **CVD screenshot pass.** In Playwright, use the CDP call `Emulation.setEmulatedVisionDeficiency` with each of `protanopia`, `deuteranopia`, `tritanopia`, `achromatopsia` and `blurredVision`.
   - Screenshot each tier fixture, sample the band pixels, and assert ΔE2000 ≥ 10 between tiers (≥ 5 for achromatopsia).
   - Assert the DOM still exposes the signal-word text and icon names.
   - Store golden images for visual diffs.
4. **Type checks** (a Playwright script using `getComputedStyle` on every visible text node):
   - mobile body ≥ 17px (SecondLook) or ≥ 16px (RefundRadar)
   - nothing under 12px
   - signal word ≥ 24px and weight ≥ 700 (the APCA Lc 45 condition for black on orange)
   - `.num` and `.money` cells have `tabular-nums`
   - the font supports `tnum`: check its GSUB features with `fontTools`
   - prose width ≤ 75ch
5. **Reflow and spacing (WCAG 1.4.4, 1.4.10, 1.4.12).** At 320px width and 200% zoom, inject the 1.4.12 spacing CSS:
   - line-height 1.5
   - letter-spacing 0.12em
   - word-spacing 0.16em
   - paragraph spacing 2em

   Then assert there is no horizontal scroll and that no stamp or band clips (`scrollWidth ≤ clientWidth`).
6. **Chart structure checks:**
   - the overview stacked bar has ≤ 3 segments
   - the detail chart has a common baseline and is sorted
   - every chart has a text alternative or data table (`aria-describedby` or a table toggle)
   - every segment has a direct label or a text legend
7. **Copy lint** (a unit test over the UI string catalogue):
   - SecondLook must never output "safe" or "certified safe"
   - "No known issues" must appear with a source and a date
   - CAUTION must appear with a reason
   - RefundRadar estimates must match `\$[\d,]+ \(likely \$[\d,]+–\$[\d,]+\)`
   - flag bare "approximately" or "may"
   - the triangle icon must not appear with tier 4
8. **Lighthouse CI:** accessibility score ≥ 95; the "legible font sizes" audit passes.
9. **Not automatic, but 10 minutes with 3–5 people:**
   - a 5-second test ("Which listing is most dangerous?") on the 48-listing page, in normal and simulated deutan colours
   - "How much will you get back, and how sure is it?" on the dashboard

   Record time-to-find and errors.

---

## (d) Sources

- Chapanis, A. (1994). Hazards associated with three signal words and four colours on warning signs. *Ergonomics* 37(2), 265–275. [Abstract (SWOV)](https://swov.nl/en/publicatie/hazards-associated-three-signal-words-and-four-colours-warning-signs)
- Wogalter, M. S., Jarrard, S. W., & Simpson, S. N. (1994). Influence of warning label signal words on perceived hazard level. *Human Factors* 36(3), 547–556. https://doi.org/10.1177/001872089403600310
- Hellier, E., Edworthy, J., et al. (2000). Investigating the perceived hazard of warning signal words. *Risk, Decision and Policy* 5(1), 39–48. [IDEAS/RePEc](https://ideas.repec.org/a/cup/rdepol/v5y2000i01p39-48_00.html)
- Braun, C. C., & Silver, N. C. (1995). Interaction of signal word and colour on warning labels. *Ergonomics* 38(11), 2207–2220. https://doi.org/10.1080/00140139508925263
- Braun, C. C., Mine, P. B., & Silver, N. C. (1995). The influence of color on warning label perceptions. *Int. J. Industrial Ergonomics* 15(3), 179–187. https://doi.org/10.1016/0169-8141(94)00036-3 ([UCF record](https://stars.library.ucf.edu/scopus1990/1874))
- Leonard, S. D. (1999). Does color of warnings affect risk perception? *Int. J. Industrial Ergonomics* 23(5–6), 499–504. *(Pages to verify.)*
- Laughery, K. R., Young, S. L., Vaubel, K. P., & Brelsford, J. W. (1993). The noticeability of warnings on alcoholic beverage containers. *J. Public Policy & Marketing* 12(1), 38–56.
- Bzostek, J. A., & Wogalter, M. S. (1999). Measuring visual search time for a product warning label as a function of icon, color, column, and vertical placement. *Proc. HFES 43rd Annual Meeting*. [NCSU repository](https://repository.lib.ncsu.edu/items/4503d14d-1985-4899-a4fe-45ba9ce79998)
- Wogalter, M. S., Conzola, V. C., & Smith-Jackson, T. L. (2002). Research-based guidelines for warning design and evaluation. *Applied Ergonomics* 33(3), 219–230. https://doi.org/10.1016/S0003-6870(02)00009-1
- Wogalter, M. S., Kalsher, M. J., & Rashid, R. (1999). Effect of signal word and source attribution on judgments of warning credibility and compliance likelihood. *Int. J. Industrial Ergonomics* 24(2), 185–192. *(Verify.)*
- Stewart, D. W., & Martin, I. M. (1994). Intended and unintended consequences of warning messages. *J. Public Policy & Marketing* 13(1), 1–19.
- Anderson, B. B., Kirwan, C. B., Jenkins, J. L., Eargle, D., Howard, S., & Vance, A. (2015). How polymorphic warnings reduce habituation in the brain: Insights from an fMRI study. *CHI '15*. [CU record](https://vivo.colorado.edu/display/pubid_323208)
- Akhawe, D., & Felt, A. P. (2013). Alice in Warningland: A large-scale field study of browser security warning effectiveness. *USENIX Security '13*.
- ANSI Z535.1-2022 (Safety Colors) and ANSI Z535.4 (Product Safety Signs and Labels). Summaries: [In Compliance, "ANSI Z535.1 – Safety Colors in Focus" (2023)](https://incompliancemag.com/ansi-z535-1-safety-colors-in-focus/); [Clarion Safety PDF](https://www.clarionsafety.com/content/clarion-icm_ANSI%20Z535.1%20-%20July%202023.pdf); approximate hex/Pantone values: [LinkML SafetyColorEnum](https://linkml.io/valuesets/elements/SafetyColorEnum/); [Munsell ANSI standards page](https://munsell.com/color-products/color-standards/munsell-ansi-color-standards/)
- ISO 3864-1:2011 and ISO 3864-4:2011, Graphical symbols: safety colours and safety signs (colorimetric specifications).
- Birch, J. (2012). Worldwide prevalence of red-green color deficiency. *JOSA A* 29(3), 313–320.
- Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE TVCG* 15(6), 1291–1298.
- Brettel, H., Viénot, F., & Mollon, J. D. (1997). Computerized simulation of color appearance for dichromats. *JOSA A* 14(10), 2647–2655.
- Okabe, M., & Ito, K. (2008). Color Universal Design: How to make figures and presentations that are friendly to colorblind people. https://jfly.uni-koeln.de/color/ ; Wong, B. (2011). Color blindness. *Nature Methods* 8, 441.
- Fogg, B. J., et al. (2003). How do users evaluate the credibility of Web sites? *DUX '03*. [Stanford Web Credibility Project](https://en.wikipedia.org/wiki/Stanford_Web_Credibility_Project); [Consumer Reports summary](https://advocacy.consumerreports.org/research/how-do-people-evaluate-a-web-sites-credibility)
- Fogg, B. J., et al. (2001). What makes Web sites credible? *CHI '01*.
- Lindgaard, G., Fernandes, G., Dudek, C., & Brown, J. (2006). Attention web designers: You have 50 milliseconds to make a good first impression! *Behaviour & IT* 25(2), 115–126.
- Reinecke, K., et al. (2013). Predicting users' first impressions of website aesthetics with a quantification of perceived visual complexity and colorfulness. *CHI '13*.
- Sillence, E., Briggs, P., Fishwick, L., & Harris, P. (2004). Trust and mistrust of online health sites. *CHI '04*.
- Alberts, W. A., & van der Geest, T. M. (2011). Color matters: Color as trustworthiness cue in web sites. *Technical Communication* 58(2), 149–160. [Ingenta](https://www.ingentaconnect.com/contentone/stc/tc/2011/00000058/00000002/art00004)
- van der Bles, A. M., van der Linden, S., Freeman, A. L. J., & Spiegelhalter, D. J. (2020). The effects of communicating uncertainty on public trust in facts and numbers. *PNAS* 117(14), 7672–7683. [PMC7149229](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7149229/); also van der Bles et al. (2019), *Royal Society Open Science* 6:181870.
- Budescu, D. V., Por, H.-H., Broomell, S. B., & Smithson, M. (2014). The interpretation of IPCC probabilistic statements around the world. *Nature Climate Change* 4, 508–512.
- Joslyn, S., & LeClerc, J. (2012). Uncertainty forecasts improve weather-related decisions and attenuate the effects of forecast error on user trust. *J. Exp. Psych.: Applied* 18(1), 126–140.
- Jerez-Fernandez, A., Angulo, A. N., & Oppenheimer, D. M. (2014). Show me the numbers: Precision as a cue to others' confidence. *Psychological Science* 25(2). *(Verify.)*
- Legge, G. E., & Bigelow, C. A. (2011). Does print size matter for reading? *Journal of Vision* 11(5):8.
- Arditi, A., & Cho, J. (2005). Serifs and font legibility. *Vision Research* 45(23), 2926–2933.
- Sheedy, J. E., et al. (2005). Text legibility and the letter superiority effect. *Human Factors* 47(4), 797–815.
- Beier, S., & Larson, K. (2010). Design improvements for frequently used fonts. *Information Design Journal* 18(2), 118–137.
- Wallace, S., et al. (2022). Towards individuated reading experiences: Different fonts increase reading speed for different individuals. *ACM TOCHI* 29(4). [PDF](https://jeffhuang.com/papers/Readability_TOCHI22.pdf); [Adobe Research](https://research.adobe.com/publication/towards-individuated-reading-experiences-different-fonts-increase-reading-speed-for-different-individuals)
- Braille Institute, Atkinson Hyperlegible (2019; Next 2024). [GitHub](https://github.com/googlefonts/atkinson-hyperlegible); [CSUN 2024 session](https://www.csun.edu/cod/conference/sessions/2024/index.php/public/presentations/view/3108.html); [All About Vision](https://www.allaboutvision.com/low-vision/atkinson-hyperlegible-typeface/)
- Dyson, M. C., & Haselgrove, M. (2001). The influence of reading speed and line length on the effectiveness of reading from screen. *IJHCS* 54(4), 585–612.
- Bringhurst, R. (2004). *The Elements of Typographic Style* (3rd ed.). Hartley & Marks.
- Cleveland, W. S., & McGill, R. (1984). Graphical perception. *JASA* 79(387), 531–554.
- Heer, J., & Bostock, M. (2010). Crowdsourcing graphical perception. *CHI '10*. [PDF](https://homes.cs.washington.edu/~jheer/files/2010-MTurk-CHI.pdf)
- Talbot, J., Setlur, V., & Anand, A. (2014). Four experiments on the perception of bar charts. *IEEE TVCG* 20(12), 2152–2160.
- Healey, C. G. (1996). Choosing effective colours for data visualization. *IEEE Visualization '96*; Healey, C. G., & Enns, J. T. (2012). Attention and visual memory in visualization and computer graphics. *IEEE TVCG* 18(7), 1170–1188.
- Szafir, D. A. (2018). Modeling color difference for visualization design. *IEEE TVCG* 24(1), 392–401.
- W3C (2023, updated 2024). *Web Content Accessibility Guidelines (WCAG) 2.2*. https://www.w3.org/TR/WCAG22/
- APCA: [Myndex apca-introduction](https://github.com/Myndex/apca-introduction); WCAG 3 Working Draft: https://www.w3.org/TR/wcag-3.0/
- Parhi, P., Karlson, A. K., & Bederson, B. B. (2006). Target size study for one-handed thumb use on small touchscreen devices. *MobileHCI '06*.
- axe-core rule list: https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md ; Chrome DevTools Protocol `Emulation.setEmulatedVisionDeficiency`: https://chromedevtools.github.io/devtools-protocol/tot/Emulation/
