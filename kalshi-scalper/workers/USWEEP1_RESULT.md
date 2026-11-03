# USWEEP1 result (run once on 2026-11-03; research only; code `src/scalper/usweep1.py`, data `workers/USWEEP1_RESULT.json`)

**Verdict: FALSIFIED as a family. No cell met the registered lead rule. No market type is a forward candidate; the five below are watch-only.**

## Reach and counts
- Series listed 15,663; in scope 15,609 (16 KXMVE parlays and 38 fifteen_min series excluded, and all 15 minute crypto, gold, forex and commodity series are covered elsewhere).
- Series **read**: 1,753 (all 1,307 recurring hourly/daily/weekly/monthly/quarterly series, plus the first 446 of the 14,302 custom/one_off/annual series in ticker order). 699 had a settled market in the last 60 days.
- **Eligible and tested: 119 series** (300+ settled markets, 20+ dates): 116 daily-life (D) and 3 longer (W), 0 hourly. By category: Economics 52 (mostly state gas price ladders), Climate and Weather 50, Financials 6, Commodities 5, Sports 4, Crypto 2. 281 cells (series x look x rule) had at least one entry; 118 series produced entries.
- **Correction, disclosed:** Amendment 2 said 210 eligible / N 1,260. The census file held some series twice after a restart, so `select` double counted. De-duplicated: 119 series, so **N added = 6 x 119 = 714** (running N about 729,449). Deflated one-sided bar at 0.05 / N: **5.27** (sweep alone, 0.05 / 714: 3.62). The score step was run twice on the same data for this reason only (the first run duplicated cells); no rule, band, look or threshold changed.
- **NOT tested: 13,856 in-scope series** (14,302 unread minus none counted twice; cause: the API rate limit allowed about 21 series a minute and the census was stopped by count, not by any outcome) plus 580 read series with too little history (under 300 markets or 20 dates in 60 days). Frozen last third of every tested series: not downloaded, not scored.

## Readout
| | tail (ask 5-15c) | favourite (85-97c) |
|---|---|---|
| cells with n >= 100 | 6 | 32 |
| entries | 650 | 4,790 |
| pooled net after fee | -0.63c | -18.90c |
| median cell net | -1.39c | -20.29c |
| best day-clustered z | +1.04 | -0.41 |
| cells with positive net | 2 | 0 |

Cells with at least 40 entries in each half: 36; positive in BOTH halves: **1** (luck would give about 9). Leads (n >= 100, both halves positive and >= 40, fee x1.2 positive, z >= 2.0, traded-candle subset positive): **0**.

## Ranked table (all cells with n >= 100, best z first; "both" = positive in both halves)
| Series | Look | Rule | n | Dates | Win | Price | Excess | Net | PF | z | Half 1 / Half 2 | Both |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KXSILVERD silver daily | 24 h | tail | 106 | 10 | 15.1% | 7.9c | +7.2c | +6.61c | 1.94 | +1.04 | +5.51 / +7.93 | yes |
| KXGOLDD gold daily | 24 h | tail | 105 | 10 | 8.6% | 7.9c | +0.6c | +0.09c | 1.01 | +0.02 | -4.69 / +5.36 | no |
| KXLALIGA2SPREAD La Liga 2 spread | 6 h | tail | 116 | 21 | 9.5% | 9.1c | +0.4c | -0.25c | 0.97 | -0.11 | +0.49 / -1.01 | no |
| KXBIGGESTQUAKE | 6 h | fav | 135 | 38 | 91.9% | 93.2c | -1.3c | -1.81c | 0.76 | -0.41 | +3.21 / -5.71 | no |
| KXBRENTD Brent daily | 24 h | tail | 106 | 15 | 6.6% | 9.1c | -2.5c | -3.10c | 0.66 | -0.69 | +0.32 / -4.92 | no |
All 27 further cells are negative or weaker (full list in `USWEEP1_RESULT.json`). Economics favourites (the state gas price ladders, 4,082 entries) lose -21.2c: posted asks of 85c to 97c sit over bids of 10c or less (median spread 0.6 to 0.8), so a taker at the ask pays for a quote nobody trades (only 6 to 29% of those decision candles had volume). That is the stale-quote effect FLB1 and GAS1-F already named, not a new finding. By category, tails: Commodities +1.20c (317), Sports -1.32c, Weather -4.43c; favourites: Weather -3.24c, Sports -6.10c, Commodities -11.44c.

## Top 5 as forward watch items (not leads; candidate JSON in `workers/candidates/USWEEP1_*.json`, `wired: false`)
The forward ledger only runs 15 minute windows, so none of these can run until a daily-window feed exists; they are written down so nothing is lost, and only the first is worth a look.
1. **KXSILVERD tail, 24 h before the close** (only cell positive in both halves): n 106 on 10 dates, +6.61c, z 1.04 (far under any bar), only 2 of 106 decision candles traded. Probe: 1 contract, limit 15c, worst single loss $0.16 (about one entry a day, so worst day $0.16), kill at 40 fills with PF under 1.0 or net under -$3; 40 fills would take about 40 daily markets, i.e. 40+ days.
2. KXGOLDD tail 24 h: +0.09c, z 0.02. Same probe spec; nothing to see.
3. KXLALIGA2SPREAD tail 6 h: -0.25c. Same spec.
4. KXBIGGESTQUAKE favourite 6 h: -1.81c; probe limit 97c, worst single loss $0.98. Not recommended.
5. KXBRENTD tail 24 h: -3.10c. Not recommended.

## Mechanism flags
None. No cell is positive in both halves with a stated mechanism. Silver's tail (the only both-halves-positive cell) has no named counterparty, 10 dates and a z of 1.04; the prior that it is luck is high given 36 testable cells and about 9 expected by chance.

## What this does and does not say
Prior verdicts stand (FLB1, SP1, scout, calibration scan): Kalshi's recurring daily markets are priced about right, and the only large deviation (gas ladder favourites) is a spread artifact. It does not cover the 13,856 unread custom, one_off and annual series, hourly series (none had 300 markets in 60 days) or the frozen last third of each tested series, which remains available for a forward read.
