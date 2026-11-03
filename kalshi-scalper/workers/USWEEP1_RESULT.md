# USWEEP1 result (run once on 2026-11-03; research only; code `src/scalper/usweep1.py`, data `workers/USWEEP1_RESULT.json`)

**Verdict: no lead.** 0 of 281 cells met the registered LEAD rule (n >= 100, >= 40 per half, positive in both halves, positive at fee x1.2, day-clustered z >= 2). The family is NOT_YET_FALSIFIED only in the sense that one cluster (daily commodity and index favourites) is positive in both halves on small n; nothing is near the deflated bar. Five watch items are registered forward (below).

## Reach and counts
- Series listed 15,663; in scope 15,609 (16 KXMVE parlays and 38 fifteen_min series excluded; all 15 minute crypto/gold/forex/commodity series are covered elsewhere).
- **Read: 1,753** (all 1,307 recurring hourly/daily/weekly/monthly/quarterly series plus the first 446 of the 14,302 custom/one_off/annual series in ticker order). 699 had a settled market in 60 days.
- **Eligible and tested: 119 unique series** (300+ settled markets, 20+ dates; 116 daily, 3 longer, 0 hourly): Economics 52 (mostly state gas ladders), Climate and Weather 50, Financials 6, Commodities 5, Sports 4, Crypto 2. 281 cells; 118 series produced entries.
- **NOT tested: 13,856** in-scope series (API rate limit stopped the census by count, not by any outcome), plus 580 read series with too little history. The frozen last third of each tested series' dates was never downloaded or scored.
- **N and bar, with a disclosure.** The committed series file (82660b9, Amendment 2) held 210 rows but only **119 unique series**: the census file had duplicate rows after a restart overlapped, so `select()` counted some series twice. `select()` and `score()` were then changed by 3 lines to de-duplicate tickers (no rule, band, look or threshold changed), and score was re-run on the same data. N was registered as 6 x 210 = **1,260 and 1,260 is kept as the conservative count** (the unique count would be 6 x 119 = 714). Running N about 729,995. Deflated one-sided bar at 0.05 / N: **5.27 for the whole record, 3.66 for this sweep alone**.

## Readout
281 cells. **28 are positive in both halves** (any n); with luck alone about a quarter, i.e. 70, would be, so that count says nothing by itself. Among cells with at least 40 entries in each half: 36 cells, 1 positive in both. The largest z with n >= 100 is +1.04 (KXSILVERD tail, 24 h). **Caveat on the z column:** for cells that win 100% the loss variance is zero, so z is degenerate (5 to 22) and PF is undefined (the code writes none); read those z values as a statistic artefact, not evidence.

Broad rows (n >= 100): tails 6 cells, 650 entries, pooled -0.63c; favourites 32 cells, 4,790 entries, pooled -18.9c, driven by state gas ladders whose 85c to 97c asks sit over bids of 10c or less (stale posted quotes, as FLB1 and GAS1-F found).

## The 28 cells positive in both halves (sorted by n; "traded" = decision candle had volume)
| Series | Look | Rule | n | Dates | Win | Price | Excess | Net | PF | z | Half 1 / Half 2 (n) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KXSILVERD | 24 h | tail | 106 | 10 | 15.1% | 7.9c | +7.2c | +6.61c | 1.94 | 1.04 | +5.5 (58) / +7.9 (48); only 2 traded |
| KXNATGASD | 6 h | fav | 67 | 6 | 98.5% | 92.4c | +6.1c | +5.60c | 5.27 | 3.71 | +7.3 (30) / +4.2 (37) |
| KXHIGHTSATX | 24 h | fav | 52 | 32 | 96.2% | 91.1c | +5.1c | +4.49c | 2.30 | 1.79 | +4.6 (26) / +4.4 (26) |
| KXGOLDD | 6 h | fav | 48 | 10 | 97.9% | 93.0c | +4.9c | +4.44c | 3.30 | 2.22 | +6.4 (24) / +2.5 (24) |
| KXBRENTD | 1 h | fav | 44 | 18 | 97.7% | 93.0c | +4.7c | +4.22c | 3.14 | 2.10 | +2.8 (25) / +6.1 (19) |
| KXAAAGASDWV | 24 h | fav | 43 | 10 | 95.3% | 93.9c | +1.4c | +0.99c | 1.23 | 0.28 | +5.9 (5) / +0.3 (38) |
| KXHIGHDEN | 24 h | fav | 43 | 28 | 95.3% | 91.6c | +3.7c | +3.16c | 1.77 | 1.01 | +2.2 (20) / +4.0 (23) |
| KXHIGHTDAL | 24 h | fav | 42 | 26 | 95.2% | 91.8c | +3.5c | +2.89c | 1.69 | 0.92 | +2.6 (20) / +3.1 (22) |
| KXAAAGASDLA | 24 h | fav | 41 | 11 | 95.1% | 93.4c | +1.8c | +1.27c | 1.29 | 0.53 | +7.6 (6) / +0.2 (35) |
| KXSILVERD | 6 h | fav | 41 | 10 | 100% | 93.0c | +7.0c | +6.50c | n/a | 22.25 (degenerate) | +6.7 (21) / +6.3 (20) |
| KXAAAGASDAL | 24 h | fav | 39 | 11 | 100% | 93.7c | +6.3c | +5.87c | n/a | 11.72 (degenerate) | +4.9 (3) / +6.0 (36) |
| KXHIGHAUS | 24 h | tail | 38 | 28 | 10.5% | 8.9c | +1.7c | +1.05c | 1.13 | 0.21 | +1.5 (19) / +0.6 (19) |
| KXHIGHTBOS | 24 h | fav | 33 | 20 | 100% | 92.3c | +7.7c | +7.14c | n/a | 7.78 (degenerate) | +6.5 (18) / +7.9 (15) |
| KXHIGHTLV | 24 h | fav | 31 | 24 | 100% | 93.2c | +6.8c | +6.29c | n/a | 9.63 (degenerate) | +5.8 (16) / +6.8 (15) |
| KXLOWTATL | 24 h | tail | 31 | 18 | 12.9% | 8.7c | +4.2c | +3.63c | 1.47 | 0.54 | +3.3 (23) / +4.6 (8) |
| KXLOWTMIN | 24 h | fav | 29 | 18 | 96.6% | 92.8c | +3.8c | +3.27c | 1.97 | 0.89 | +1.8 (19) / +6.0 (10) |
| KXLOWTNYC | 24 h | fav | 29 | 18 | 96.6% | 92.4c | +4.2c | +3.64c | 2.20 | 1.23 | +1.6 (18) / +7.0 (11) |
| KXINX | 6 h | fav | 27 | 13 | 100% | 93.9c | +6.1c | +5.71c | n/a | 11.72 (degenerate) | +4.7 (11) / +6.4 (16) |
| KXHIGHLAX | 24 h | tail | 26 | 18 | 15.4% | 10.2c | +5.2c | +4.55c | 1.49 | 0.65 | +9.3 (10) / +1.5 (16) |
| KXLOWTHOU | 24 h | fav | 26 | 18 | 100% | 93.6c | +6.4c | +5.92c | n/a | 10.40 (degenerate) | +6.7 (18) / +4.3 (8) |
| KXLOWTCHI | 24 h | tail | 22 | 17 | 13.6% | 8.9c | +4.8c | +4.17c | 1.51 | 0.57 | +2.0 (17) / +11.5 (5) |
| KXRAIN | 24 h | fav | 21 | 10 | 100% | 94.0c | +6.0c | +5.55c | n/a | 14.21 (degenerate) | +5.9 (9) / +5.3 (12) |
| KXLOWTSATX, KXGOLDD 1 h, KXLOWTAUS, KXLOWTSDF, KXSHIBAD, KXLOWTOKC | various | fav | 6 to 15 each | 5 to 12 | 100% | | | +3.8c to +7.2c | n/a | degenerate | n too small |

## What the cluster is, and what it is not
The cluster of interest is **daily commodity and index favourites (ask 85c to 97c) 1 to 6 hours before the close**: natural gas (n 67, win 98.5% vs 92.4c paid, +6.1c, PF 5.27, z 3.71), gold daily (n 48, z 2.22), Brent (n 44, z 2.10), silver (n 41, 100% wins) and the S&P (KXINX, n 27, 100%), all positive in both halves; 24 hour weather and gas favourites are positive too (KXHIGHTSATX n 52, z 1.79). **None clears the bar:** the best is z 3.71 on 6 dates against 5.27 (3.66 sweep alone, so natural gas does clear the sweep-only figure on paper but with 6 dates and 67 strikes on those dates, which are one bet each day, not 67). 28 of 281 cells positive in both halves is below what luck gives. Many of these markets have several strikes a day, so n is inflated relative to independent days; the day-clustered z already accounts for it and is the number to read.
- **Versus prior work.** FLB1 (non-sports favourites at 24/72/168 h, 28,005 markets, -0.6c to -1.8c) is about long-dated, non-price markets and excluded Financials and Crypto; this cluster is DIFFERENT: daily price-bracket ladders on commodities and the S&P (FLB1 saw these only as the "Commodities" look-alikes, 718 entries at 72 h, -1.79c, a longer lead). It does not contradict FLB1 and it does not overturn the scout (Oct 22), whose Brent daily had 60 entries and was too thin; gas and weather 24 h favourites here (+1.0c to +7.7c on small n) disagree with the scout and WX1 (weather -4.7c) and should be read as noise until forward data says otherwise. Gas price ladders at 24 h in the broad table lose 21c (spread artifact), the opposite of the positive state gas cells above, which shows how sensitive this is to a handful of strikes.
- **Overlap with L1.** KXGOLDD is the daily gold price-bracket market, not the 15 minute gold market (KXGOLD15M). It can hold a position at the same time as L1 gold and is the same underlying asset; a probe on it is correlated with L1 gold and must not be sized as independent.
- Mechanism: none stated. The natural counterparty (someone selling the near-certain strike cheaply late in the day) is a hypothesis, not a measurement; no mechanism flag.

## Forward watch items (registered now, freeze 2026-11-03 17:00 UTC; candidate JSON `workers/candidates/USWEEP1_*.json`)
Rule for all: favourite (ask 0.85 to 0.97, hard limit 0.97), taker, held to settlement, fee 7% x C x p x (1-p) rounded up. Forward window = markets closing after the freeze (the development third before it is spent). Capped probe: **1 contract, hard limit 0.97, kill at 40 fills with PF under 1.0** (or net under -$3). **Worst loss: 98c per contract (97c plus the 1c fee) at 1 contract, $9.73 at 10 contracts.** Worst day = one losing strike per day in development at 1 contract, $0.98, but several strikes can lose together on the same day (up to the day's strike count x 98c).
| Candidate | Look | Dev n / dates | Entries per day | 40 fills in about |
|---|---|---|---|---|
| USWEEP1_KXNATGASD_FAV_360 | 6 h | 67 / 6 | 11.2 | 4 days (not 40 independent bets) |
| USWEEP1_KXGOLDD_FAV_360 | 6 h | 48 / 10 | 4.8 | 8 days |
| USWEEP1_KXBRENTD_FAV_60 | 1 h | 44 / 18 | 2.4 | 16 days |
| USWEEP1_KXSILVERD_FAV_360 | 6 h | 41 / 10 | 4.1 | 10 days |
| USWEEP1_KXHIGHTSATX_FAV_1440 | 24 h | 52 / 32 | 1.6 | 25 days |
The fifth (a weather ladder) is included as the largest remaining cell with n >= 40 and is the weakest prior (WX1, scout: weather loses); KXINX (n 27) is under the n >= 40 cut. The evaluator is `scalper.usweep1:forward_eval` (test passes) but the forward ledger feed delivers 15 minute windows only, so the five accrue in the ledger only once a daily-window feed exists; until then the read is by `python -m scalper.usweep1` rerun on the frozen dates. Honest reading: independent daily outcomes, not strikes, decide this; 40 fills is about 4 to 25 calendar days but only a handful of independent days.

The earlier tail watch items (KXSILVERD tail 24 h etc.) were replaced by these five; the silver tail (n 106, z 1.04, only 2 traded candles) is recorded above and not forwarded.
