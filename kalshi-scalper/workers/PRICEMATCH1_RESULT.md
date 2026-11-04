# PRICEMATCH1 result (run once, 2026-11-04): spread matters WITHIN an ask bin (claim SUPPORTED), but no liquidity cell reaches break-even; overall FALSIFIED as a trade

Registration `workers/PRICEMATCH1_REGISTRATION.md` (sha256 `8b57099afbdfff28d99624d216848c77bc30270562312db1418a3eed2fcd45c9`, commit 49f34d8, pushed before `score`). Data `workers/PRICEMATCH1_RESULT.json`, code `src/scalper/pricematch1.py`, tests `tests/test_pricematch1.py`. **Cheap side only (ask 3c to 30c); no favourite-side figure computed.** Pool 6,515 cheap entries, 3,558 events (LIQ1 features, max 2 per event, frozen third excluded, no new fetch). Net after fee per contract; event-cluster 95% intervals.

## Pooled within-bin differences (Mantel-Haenszel style, ask in 1c bins 3..30; favoured minus opposite)
| feature (fav - opp) | all | D1 | D2 | claim |
|---|---|---|---|---|
| spread (TIGHT - WIDE), n 2,621 / 2,563, 25 bins | +6.64c [+4.38, +9.08] | +4.58c [+1.27, +8.07] | +8.33c [+5.06, +11.72] | SUPPORTED |
| volume (HIGHV - LOWV), n 2,108 / 3,552, 28 bins | +2.65c [+0.96, +4.25] | +1.23c [-1.10, +3.44] | +3.35c [+0.94, +5.77] | FALSIFIED (D1 lower bound below 0) |
| overround (LOWOR - HIGHOR), n 360 / 433, 25 bins | +6.98c [+2.52, +11.24] | +6.83c [+2.11, +11.46] | not computable | NOT_ENOUGH_DATA (second half has 38 / 24 entries, no bin with 5 of each) |

The prediction (difference shrinks toward 0 to +2c) was WRONG for spread and overround: price matching removed almost nothing. The raw LIQ1 gap (7.2c) is +6.6c at the same ask. So the LIQ1 ordering was not mostly the ask bucket. (Matched bins are the ones with both sides; TIGHT entries concentrate in the cheapest bins, so only 1,614 of 2,621 TIGHT entries sit in bins with at least 5 WIDE.)

## Cells (net per contract, excess over the ask-bin mean)
| cell | n | win / price | net [95%] | vs bin mean | D1 / D2 net |
|---|---|---|---|---|---|
| CONTROL | 6,515 | 8.29% / 13.49c | -6.02c [-6.81, -5.23] | 0.00c | -5.28 / -6.75 |
| TIGHT | 2,621 | 9.27% / 11.39c | -2.83c [-4.07, -1.56] | +2.41c [+1.17, +3.69] | -2.60 / -3.05 |
| MIDSP | 1,331 | 6.69% / 10.96c | -4.96c [-6.29, -3.48] | +0.33c | -5.70 / -4.26 |
| WIDE | 2,563 | 8.12% / 16.96c | -9.84c [-11.06, -8.69] | -2.64c [-3.86, -1.46] | -8.54 / -11.07 |
| HIGHV | 2,108 | 9.72% / 13.44c | -4.53c [-5.82, -3.17] | +1.42c [+0.12, +2.83] | -4.46 / -4.59 |
| MIDV | 855 | 9.36% / 12.68c | -4.10c [-6.11, -2.14] | +1.70c | -4.07 / -4.13 |
| LOWV | 3,552 | 7.18% / 13.72c | -7.38c [-8.38, -6.34] | -1.25c [-2.24, -0.22] | -6.65 / -8.04 |
| LOWOR (weather) | 360 | 10.83% / 11.43c | -1.31c [-4.74, +2.22] | +3.82c [+0.37, +7.39] | -1.78 / -0.84 |
| MIDOR | 473 | 8.25% / 11.89c | -4.39c [-7.18, -1.47] | +1.03c | -5.14 / -3.68 |
| HIGHOR | 433 | 6.24% / 13.63c | -8.23c [-10.43, -5.91] | -2.20c [-4.36, +0.06] | -8.14 / -8.31 |

## Best achievable
Across the 9 registered cells the best is **LOWOR at -1.31c per contract, 95% [-4.74, +2.22] (n 360, 213 events)**; D1 -1.78c, D2 -0.84c, both negative; its Bonferroni (9 cells) lower bound is about -6c. The best cell with a tight interval is TIGHT at -2.83c [-4.07, -1.56], PF 0.72, both halves negative. **No cell is above 0 in both halves; no LEAD_CANDIDATE. Overall: FALSIFIED.** Even the best liquidity filter leaves the win rate 1.4c to 2.1c under the price paid, and the fee (about 0.7c) is on top.

## What it does show (observation)
Liquidity genuinely ranks the cheap side's calibration at the same price (TIGHT +2.4c and WIDE -2.6c versus their ask-bin means, a 5c spread of excess, stable in both halves), so a wide or untraded quote is a worse longshot than a tight one even at an identical ask. But the tight tail is still below break-even by about 2.8c, so a filter cannot create an edge, only select the least bad entries. Mechanism if it ever mattered: competitive makers price the tight books nearer fair; the wide-book ask is stale or padded. It does not reach zero, so no mechanism is promoted.

## Caveats
1. Same pool and 60-day window as LIQ1 (Weather and Economics dominate by count); only a TIGHT-minus-WIDE contrast over the shared 25 bins, so cheapest-bin TIGHT entries without a WIDE partner are in the cell table but not the contrast. 2. Overround exists only for weather ladders and only 793 entries; second half not computable. 3. Bin means include the entry itself (negligible). 4. Entry at the candle's last ask, not a fill; events overlap in time so intervals are optimistic. 5. 65% of entries have zero candle volume. 6. Cheap side only by the owner's rule.

## Forward plan
None as a trade. If liquidity is ever used it is a filter inside another registered rule. N +6.
