# Raw floating point comparisons on registered lines: a static check (Forensics desk, 2026-11-13)

Ordered by the Head of R&D after the MAPBREAK second build found a spread of exactly 4c counted as wider than 4c (`0.54 - 0.50 <= 0.04` is false in a computer). Every frozen scorer that reads tonight was parsed, never run on a landed file, and every comparison was listed with `cmpscan.py` and read by hand. Edge cases were checked on invented prices only. No landed file and no result was opened.

What counts as a hit: a registered line (a price band, a spread limit, a gap or jump threshold, a cost kill, a bucket edge, a verdict bar) compared with a value that came out of arithmetic (a subtraction, a sum, a mid, a ratio) with no tolerance and no rounding first. A quote parsed straight from the feed and compared with a constant is safe (the same decimal gives the same number). A whole-number ratio compared with a constant is safe (division is correctly rounded).

| File (commit) | Finding |
|---|---|
| Desk A `desk_a_verify/inplayjump.py` (3389828e, unchanged at c4575f14) | Jump, pre-jump mid band, entry ask band, entry spread, the 5c quiet range, the tennis 2c steps, the cost kill and the fee all carry a 1e-9 tolerance. **Line 159**, the placebo's 10c price bucket `int((p - 0.20) / 0.10)`: a price paid of exactly 0.30, 0.50, 0.60 or 0.70 falls into the bucket BELOW (checked for every whole cent from 20c to 85c; those four are the only ones). It touches Amendment 3's "grouped by price paid in 10c steps". The rule arm and the placebo arm use the same function, so it shifts four edges by one cent and favours neither arm. **Lines 178 to 179**, the verdict bars (PF under 1.0, PF 1.5 or more, halves over 1.0) are raw; they bite only if a profit factor lands exactly on the bar. |
| Desk A pilot builders `build_inplayjump_pilot.py`, `_pilotval.py`, `_validation.py`, `_candles.py` (c4575f14) | No raw comparison on a registered line. The first three compare whole numbers only; the candles builder's screen lines (45, 59) carry a tolerance. |
| Desk B `rematch/stage1_measure.py`, `rematch/common.py` (1f2920b3) | No raw comparison on a registered line. Spread, fall, quiet move, ask band and cost kill carry 1e-9; the fee rounds up with a tolerance; the 80% start share (line 163) is `count < 0.8 * n`, checked exact for every n that is a multiple of 5 up to 2,000. |
| Desk B `nhlot/measure_prices.py` (987d5a87), `nhlot/build_candles_job.py` | No raw comparison that can bite on whole-cent quotes. The registered bars (ask 0.43, spread 0.03) carry 1e-9. Line 94, the moneyline mid band 0.30 to 0.70, is raw on `(bid + ask) / 2`: zero whole-cent quote pairs are misjudged (every pair checked); it fails only for tenth-of-a-cent quotes 47c wide. A tolerance there costs nothing. Lines 102, 104, 132 and 134 compare a parsed quote with the level directly (safe). |
| Testing Desk `tie3.py` (f39b768f) | **Line 157, two hits.** `sp <= SPREAD_MAX` with `sp = ask - bid`: of the 95 whole-cent quote pairs exactly 4c apart, 53 are judged wider than 4c. `r - ask >= RULE_EDGE`: of the 89 cases with the rate on a whole cent and the ask exactly 10c under, 55 are judged under 10c. Both lower the printed share of games with the ask 10c under and a spread of 4c or less. The survival line (163) compares the median gap and median spread after rounding to four decimals, which is safe. |
| History Miner `esoctie/esoctie.py` (sha256 76578a15...) | The 10c gap line, the 4c spread line and the cost kill are compared after rounding to four decimals: safe (generous by at most half a hundredth of a cent on the gap). **Line 123**, the strength bucket on `f = (bid + ask) / 2`, is raw: a mid of exactly 0.45 from quotes 0.43/0.47, 0.42/0.48 or 0.41/0.49, and exactly 0.65 from 0.61/0.69 or 0.60/0.70, goes to the bucket BELOW (27 whole-cent pairs in all, most of them far wider than any real quote). It touches registration point 3 (bucket edges 0, 0.45, 0.55, 0.65, 0.75, 1.0). The base rate and the bet use the same function, so it is consistent, not look-ahead. **Lines 235 to 240**: the profit factor is rounded to three decimals before the 1.0 and 1.5 bars, so 1.4996 reads as 1.5. |
| Forensics `wheel0/wheel0.py` (sha256 10a7b363...) | Every band, the spread line, the fill, the HOT bar and its halves, the 1.15 line and both p lines carry a tolerance. **Line 355**, the NOT SUPPORTED line `pfh < 1.0`, is raw; it bites only if the pooled profit factor after HOT is exactly 1.0. My own file; reported like the others. |

## How to rerun

`python3 -I cmpscan.py <file.py> [...]` lists every comparison that could involve a non-whole number (flags: F a decimal constant is in it, A arithmetic is in it, = an equality) and every `ceil`, `floor`, and `round` or `int` on arithmetic. The scan finds the lines; a person reads them.

## Suggested fix, one line a card

Every "or less" and "or more" on a registered line uses a tolerance of 1e-9 (as MAPBREAK's Amendment 10 now says), or prices are held as whole tenths of a cent. A bucket edge is found by whole-number arithmetic on cents. A verdict bar is compared on the unrounded figure with the same tolerance.

## Re-scans after the fixes (2026-11-13, later)

| File (commit) | Finding |
|---|---|
| Desk A `inplayjump.py` (7eeacba5, sha256 `c889c333...`) | Both hits fixed: the bucket is whole-number arithmetic on cents, the verdict bars carry 1e-9. No raw comparison left on a registered line. |
| Testing Desk `tie3.py` (sha256 `8f73f930...`) | Both hits on the old line 157 fixed (1e-9 on the spread and the 10c edge, and on the survive test). One line left for the record: 168, "nothing to buy" compares a share already rounded to three decimals with 0.5, so 0.4996 reads as half. It bites only on an exact near-tie. |
| Testing Desk `breakplay.py`, `mapbreak.py`, `polcost.py`, `poli2_count.py` (c7fa2934) | No raw comparison on a registered price, spread, gap, cost or share line. `breakplay.py` line 106 compares a parsed bid with 0.90 directly (safe: no arithmetic). Lines 335 to 337, the profit factor bars of the rule step, are raw; the Head's standing rule covers them (a verdict figure within 0.001 of its bar is recomputed in exact whole cents by both builds). |
| History Miner `esoctie.py` (sha256 `ce1e9030...`, NOTE 11) | Reported fixed by its author and audited CLEAN by Auditor B; not re-scanned here. |
| Forensics `wheel0.py` | Left frozen by the Head's ruling; the exact-cents rule is a dated line in `wheel0/WHEEL0_PRECONDITION.md`. |

## Three scorers frozen on the night of Nov 12 to 13 (scan at about 01:55Z, on the Head's order)

`cmpscan.py` lists every comparison; each listed line was then read by eye.

| File (sha256) | Finding |
|---|---|
| Desk B `voidsnap/voidsnap.py` (`c176146b...`) | CLEAN. Every registered comparison carries 1e-9: frozen within 2c (line 272), under 10 contracts (274), 10c under (278, 293), spread 4c (293), the 15c to 64c band (294), within 1c and 3c (354, 355), the 70% and 30% lines (380). Raw comparisons left are on parsed quotes (`0 < bid < ask < 1`, line 231), whole counts and times. |
| Desk B `polgap/polgaph.py` (`9186c8b5...`) | CLEAN on every registered line: steady 1c (231), band (233), spread (235), 200 contracts (238), the 2c and 5c gaps (269, 281), nearest 50c and its tie (274, 279, 297), the fill test (444, 445), the cost kill (419), the profit factor lines (393), the half-of-net test (489). TWO NOTES, neither on a verdict line: (1) lines 360 and 365 count a win or a loss as a cash result above or below zero with no tolerance; this is the known information-only difference on the "voids paid at settlement value" line (the Head's ruling of 01:48Z: a sentence, no hash change); no registered booking can produce a zero result. (2) line 352 counts a minute request as holding the 07:01 minute when `start <= 07:01:00 <= end`; my build needs `start < 07:01:00`. They differ only for a request that STARTS exactly at 07:01:00, which neither Desk B's job shape (start 07:00:00) nor any fixture has. |
| History Miner `candlegap/candlegap.py` (`a7178688...`) | CLEAN. The candle-against-book test is `abs(difference) <= 0.0101`, a tolerance by design (lines 139). The YES ask is `round(1 - NO bid, 4)`, so the "top of book changed" test (119) and "bid under ask" (122) compare rounded values. The rest are times and counts. |

## The Testing Desk's INPLAYJUMP second scorer (scan on Nov 13 at about 08:25Z, on the Head's order of 01:49Z, when the Testing Desk said it was frozen)

Files, from `claude/testing-desk` at `968d6830` (the desk named `b39596b6`; the hashes are the same): `testing/inplayjump_second.py` sha256 `fb9bca51de40b7c1...`,
the wrapper `testing/inplayjump_read.py` `6df28ad7bea0d1d5...`, `testing/scorekit.py` `02728f2afdfe62a9...`. Parsed with `cmpscan.py`, every listed line read by eye, edge
cases checked on invented whole-cent quotes only. Nothing was run on a landed file and no result was opened. This is a float scan, not a check of the rule against the
registration (Auditor B did that).

**Finding: CLEAN on every registered threshold. One point on a verdict input (rounding before a bar, not a float error), four notes.**

| Line | What it compares | Result |
|---|---|---|
| 107 | jump of 10c on mids; pre-jump mid 15c to 75c | 1e-9 both. Of 150,444 whole-cent quote pairs whose mids differ by exactly 10c, 0 are judged under (94,817 would be with no tolerance); 0 of 151,240 pairs 9.5c apart are let through. Mids of exactly 0.15 and 0.75 are kept, 0.145 and 0.755 dropped. |
| 117, 311 | tennis 2c step | 1e-9. 0 of 158,912 exact-2c pairs judged under (44,583 with no tolerance); 0 of 159,056 pairs 1.5c apart let through. |
| 152, 178 | ask 20c to 85c; spread 4c or less | 1e-9. 0 of 95 exact-4c spreads judged wider (53 with no tolerance). |
| 173 | quiet range of 5c | 1e-9. 0 of 156,959 exact-5c pairs misjudged; 0 of 157,370 pairs 4.5c apart misjudged. |
| 176 | the higher mid, tie within 1e-9 | tolerance, then the ticker order. |
| 200 (and the wrapper's stop) | cost kill, median over 4c | 1e-9; a median of exactly 4c is not "over". |
| 220 | share paid 70c or more | 1e-9 on a price already rounded to four decimals. |
| 237, 238 | profit factor under 1.0, 1.5 or more, halves above 1.0 | 1e-9 on the unrounded figure (`scorekit.pf` does not round). |
| 262 | screen: bid range plus ask range under 4c | 3e-9 on a sum of four subtractions. 0 of 17,405 exact-4c cases judged under. |
| 276, 277 | minute close inside the hour's low to high | 1e-9. |
| 43 | fee rounded up | `ceil(round(x, 6))`: equal to the exact ceiling for every price on the whole-cent, tenth-of-a-cent and hundredth-of-a-cent grids (99, 999 and 9,999 prices), and equal to `ceil(x - 1e-9)` on all of them. |
| 59 | price bucket `round(p * 100)` | Right for every whole-cent price from 21c to 86c. Same formula as Desk A's engine. |
| 53, 76, 77, 91, 92 | parsed quotes, times, whole counts (`g * 100 >= 80 * n`) | exact by construction. |

**The one point, line 238: the placebo bar is tested on figures already rounded.** Line 235 rounds the difference and its standard error to 3 decimals of a cent, and
line 238 then tests `difference >= 2 * se - 1e-9` on those rounded figures. Desk A's engine (`desk_a_verify/inplayjump.py` at `6e356373...`, line 183) tests the same bar
on the unrounded figures. The two can give opposite answers when the difference is within 0.0015c of twice the standard error (the difference's rounding moves it by up
to 0.0005c and twice the standard error by up to 0.001c). Example on invented numbers: difference 2.0004c and standard error 1.0004c is under the bar unrounded
(2.0004 against 2.0008) and at the bar rounded (2.000 against 2.000). In 2,000,000 invented draws within 0.004c of the bar, 7.8% flipped, none farther than 0.0015c from
it. The two builds agree on every figure printed so far, so no read has been near it. The Head's standing rule (a verdict figure within 0.001 of its bar is recomputed
exactly) catches most of this window but not all of it: the window here is 0.0015c. Suggested, with no hash change: at any read where the printed difference is within
0.002c of twice the printed standard error, both builds decide that bar on the unrounded figures. It is the Head's call.

**Notes, none on a verdict line:**

1. **Bucket off the whole-cent grid.** For a price on tenths of a cent, x9.5c to x9.9c (29.5c to 29.9c, 39.5c to 39.9c and so on, 30 prices between 21c and 86c) goes
   to the bucket ABOVE the 10c step it lies in, because the cents are rounded, not cut. Both builds use the same formula, so they cannot disagree; it only matters if a
   price paid is ever off the whole-cent grid, and then it moves a few placebo weights.
2. **Wins and the profit factor's sums use raw `> 0` and `< 0`** (line 211; `scorekit.pf`). No cash result here can be exactly zero: a win is at least 1 minus 86c minus
   the fee, and a loss or a void costs at least the 1c fee. So the POLGAPH case (a void paid at its value netting exactly zero) cannot arise.
3. **Line 223, `tot <= 0`, is raw.** The largest-day share prints nothing when the total net is zero or less; a total that is only float residue would print an absurd
   share. Information line.
4. **`scorekit.cluster_z`, `sd > 0`, is raw.** If every cluster mean is equal up to float residue, z prints as a huge number, not as "none". z is printed and not on
   this scorer's verdict line (lines 237 to 239 read n, profit factor, the halves and the placebo bar). The Head's DEPTH1 wording (a z over 1,000 in size is recomputed
   exactly) would cover it if applied here.

Not in the scan's reach: `scorekit.py` functions this scorer does not call (the fill, stop and resting-order helpers, which carry 1e-12).
