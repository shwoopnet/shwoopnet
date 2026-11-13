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
