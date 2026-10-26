# SecondLook benchmark results

Run 2026-10-26 19:18 UTC.

## 1. Product recognition (54 CPSC recall photos, 14 product types)

From the photo alone (no listing text), SecondLook named the exact product type in 57% of photos (74% counting near neighbors such as swing vs. inclined sleeper). Nemotron 3.5 Super VL's own category pick: 48% (65%); in 7 photos it described the product correctly but picked 'other', and code used its description instead. Real listings also have a title, which the app reads too.

## 2. Recall matching (40 recalled listings + 40 decoys; run 2026-10-26 18:50 UTC)

| System | Recalls caught | False alarms on decoys |
|---|---|---|
| Rules + recall index | 95% | 0% |
| Rules + recall index + Nemotron 3 Ultra reading the notices | 98% | 0% |
| Nemotron 3 Ultra alone (from memory) | 0% | 55% |

## 3. Demo listings

6/6 reached the expected verdict.

## 4. Cost and latency

| Tier | Model | Calls | Avg seconds | Cost |
|---|---|---|---|---|
| nano | nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B | 6 | 25.24 | $0.001 |
| super_vl | nvidia/Nemotron-3.5-Super-VL | 60 | 1.75 | $0.036 |
| ultra | nvidia/Nemotron-3-Ultra-550b-a55b | 175 | 5.7 | $1.066 |
