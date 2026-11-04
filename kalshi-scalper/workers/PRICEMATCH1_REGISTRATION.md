# PRICEMATCH1 registration: after exact price matching, does ANY liquidity feature move the cheap side? (2026-11-04)

Registered before any outcome was joined (the census printed counts only). Discovery only: no live code, no `functions/`, no L1, no OICORE, no promote verb. **Owner rule (strict): CHEAP SIDE ONLY, ask 3c to 30c.** Code asserts no entry above 0.30; no favourite-side result is computed; no 15 minute crypto or gold candle trigger.

## Duplicate check
README and workers searched (LIQ1, MODEL1, OVERROUND1, CALIB1, AUDIT1, POWER1; "price-matched", "stratif"). LIQ1 compared groups raw and flagged the ask mix as an unresolved caveat ("no price-matched comparison was registered"); OVERROUND1 is raw terciles on weather only; MODEL1 is a pooled model with no liquidity-feature contrast and ended NOT_ENOUGH_DATA; CALIB1 conditions on category and ask bucket, not on liquidity. **No exact price-matched (ask-bin stratified, Mantel-Haenszel style) contrast of liquidity features has been run: not a duplicate.**

## Hypothesis
LIQ1 ranked the loss by spread (TIGHT -2.8c, WIDE -10.0c) but TIGHT averages a 10.7c ask against 16.9c for WIDE. Question: within an ask bin (so the same price paid), does tight beat wide, busy beat untraded, low overround beat high? Prediction: the within-bin difference shrinks toward 0 and every cell stays negative (the loss is the favourite-longshot / fee structure at that price, not stale quotes). Counterparty if it did not shrink: the maker or stale quote on the other side.

## Data (no new fetch)
The LIQ1 pool (`LIQ1_OUT/features.jsonl`, `res.json`; 16,201 entries before the cap): CALIB1's USWEEP1/2/3 and NEWLIST1 development caches, frozen third from 2026-10-03T16:00Z excluded (NEWLIST1 close >= t2 dropped; sweep caches hold no frozen market). Overround = OVERROUND1's event overround per (event, look), from its weather sweep cache (`overround1.build(False)`, structure and quotes only); it exists only for weather ladders (entries without it are excluded from the overround feature alone). Pool cap: at most **2 entries per event** over the WHOLE pool (the 2 with smallest md5(market|look)), giving **6,515 entries, 3,558 events** (LIQ1's CONTROL; the per-group cap of LIQ1 is not used, so cell counts are smaller than LIQ1's).

## Definitions (fixed here)
- **Ask bin** = ask in whole cents, 3 to 30 (28 bins). Entry, fee and net as CALIB1/LIQ1 (buy cheap side at the ask, hold to settlement, fee 7% x p x (1-p) rounded up per 10 contracts).
- **Cuts (reused, never refitted):** spread TIGHT <= 2.0c, WIDE >= 5.0c; volume HIGHV > 30.93, LOWV = 0; overround LOWOR < 0.07, HIGHOR >= 0.12. Middles are MIDSP, MIDV, MIDOR (reported as cells, not in the contrast).
- **Within-bin pooled difference (Mantel-Haenszel style)** = sum over bins of w_b x (mean net of favoured level - mean net of opposite level), w_b = n1 n0/(n1+n0), over bins with >= 5 entries of each level in that sample. Favoured minus opposite: TIGHT minus WIDE; HIGHV minus LOWV; LOWOR minus HIGHOR. CI = event-cluster bootstrap (2,000 draws, seed 20261104, events resampled, same bins).
- **Halves D1/D2** = first and second half of all events by earliest entry time.
- **Cells (9 plus control):** TIGHT, MIDSP, WIDE, HIGHV, MIDV, LOWV, LOWOR, MIDOR, HIGHOR, and CONTROL. Statistic: mean net per contract (event-cluster 95%; a Bonferroni-style lower bound at the 0.28 percentile for 9 cells is also printed) and the **excess over the ask-bin mean** (cell net minus the pooled mean net of the entry's ask bin; event-cluster 95%), win rate, price, PF, D1/D2.
- Best achievable: among the 9 cells with n >= 150, the highest mean net, reported with its CI, its Bonferroni lower bound and halves.

## Claims, kill rules, prediction (fixed before any outcome is joined)
Three claims (N +2 each, **+6**): for each feature, the pooled within-bin difference is above 0 in BOTH D1 and D2 with the lower 95% bound above 0 in each. `SUPPORTED` if so; `NOT_ENOUGH_DATA` if either side has under 150 entries in the sample; else `FALSIFIED`. A cell is a `LEAD_CANDIDATE` only if its net lower 95% bound is above 0 in BOTH halves AND a mechanism is stated (a net above 0 without that is reported, never promoted). A cell is `NOT_ENOUGH_DATA` under 150 entries. Overall `FALSIFIED` if no cell has net above 0 in both halves. Nothing else is tuned; no other feature, cut or bin is tried.

**Prediction.** Pooled within-bin differences are small, about 0 to +2c (tight minus wide, shrunk from the raw 7c), CIs spanning or only barely above 0; all 9 cells and the control negative after fee (best cell about -2c to -4c); no LEAD. Overall FALSIFIED (about 90%). Census (counts only): spread TIGHT 2,621 / MIDSP 1,331 / WIDE 2,563; volume HIGHV 2,108 / MIDV 855 / LOWV 3,552; overround LOWOR 360 / MIDOR 473 / HIGHOR 433 (5,249 without an overround). Bins with at least 5 of each side: spread 25 of 28 (TIGHT entries inside them 1,614 of 2,621), volume 28, overround 25.

Read once; `score` refuses a second run (`workers/PRICEMATCH1_RESULT.json`). Code `src/scalper/pricematch1.py`, tests `tests/test_pricematch1.py` (synthetic only).
