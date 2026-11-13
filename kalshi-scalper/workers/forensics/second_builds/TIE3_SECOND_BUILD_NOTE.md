# TIE3 measurement: independent second build (Forensics desk, 2026-11-13)

Ordered by the Head of R&D under rule 16b. Built from Desk B's registration (`tie3/TIE3_REGISTRATION.md` with its dated note and amendment, `TIE3_SERIES.json`, on `claude/idea-desk-b`).

**Disclosure.** This desk leak-tested the Testing Desk's `tie3.py` on Nov 12 and scanned it for float comparisons on Nov 13, so it had seen that code. The second build was written from the text; eleven places where the text leaves a choice are listed in the scorer and printed with every run.

**What was read.** Lists `TESTING_LISTS_BUNDLE/2026-11-12T1848Z_43283701873`, candles `TIE3_CANDLES/2026-11-13T0007Z_43334525742`. A zero-try measurement: no rule scored. This build drops the result field of every market closing on or after 2026-10-27 at read time, so no price-block result exists anywhere in it; results are read for the base block only, for the level count.

## Result: the same output, every figure compared

Against the Testing Desk's `tie3.py` (sha256 `8f73f930...`, audited CLEAN) on the same files: **117 figures compared, 117 identical** (per cell: base events, the base rate and its standard error for every quarter and series, games with a derivable start, two-sided games and their share, the median spread, the quartiles and median of base rate minus Tie ask, the share that would fire, the status).

| Cell | Base events | Base rate | Price-block games, derivable start | Two-sided | Median spread | Base rate minus ask: quartile, median, quartile | Would fire |
|---|---|---|---|---|---|---|---|
| NHL period 1 | 185 | 30.3% | 114 | 104 (91%) | 2c | -3.7c, -3.7c, -2.7c | 0 |
| NHL period 2 | 184 | 26.1% | 114 | 94 (82%) | 3c | -5.9c, -4.9c, -3.9c | 0 |
| NHL period 3 | 184 | 22.3% | 114 | 91 (80%) | 3c | -5.2c, -4.7c, -3.7c | 0 |
| NHL level after regulation | 184 | 22.8% | 114 | 99 (87%) | 1c | -0.2c, -0.2c, +0.8c | 0 |
| NFL quarters, pooled | 620 | 18.2% (per quarter 25.8%, 14.8%, 20.0%, 12.3%) | 120 | 120 (100%) | 1c | -1.0c, +0.8c, +2.8c | 0 |
| Soccer first halves, pooled | 679 | 39.0% (per series 29.5% to 50.0%) | 245 | 243 (99%) | 1c | -4.5c, -0.6c, +4.3c | 28 (11.5%) |

**Verdict, both builds: CLOSED, "efficient, move on".** No cell has a median gap of 8c or more; the best is the NFL quarters at +0.8c. In the three NHL period cells the Tie is priced ABOVE its base rate.

## Points for the record (none moves a figure)

1. **How many prices are from the exact minute.** Only 8 to 24 of each NHL and NFL cell's two-sided games, and 96 of 243 in soccer, had a two-sided candle at T itself; the rest come from stepping back up to 30 minutes, as registered. On these markets a missing minute is the normal case.
2. **Soccer's 28 "would fire" games** rest on per-series base rates from 40 to 122 base events each (standard error 4 to 8 points), so a 10c gap there is about one to two standard errors of the base rate. The registered kill line is the cell's median gap, which is -0.6c.
3. **A reading that differs but did not bite here.** Registration point 6 says events with fewer than three markets are dropped and counted; this build applies it to both blocks, the Testing Desk's build to the base block only (a ruling of Nov 13 that nothing in the price block is filtered on the number of markets). No price-block event had fewer than three, so no figure differs.
4. **The Testing Desk's build prints one price-block count that depends on the result field** ("price-block games not all settled, counted not filtered": 1). It uses only whether the field is yes or no, never which, and it filters nothing; the Head ruled it and Auditor B found the build CLEAN. This build cannot print that count because the field is dropped at read time.
5. The base rates are from about three weeks of one NHL season and one stretch of the NFL season (the history endpoint added nothing older than that here), as the registration's honest limit 2 expected.

## Files

`tie3_second.py` (sha256 `dc656c8a...`; `python3 -I tie3_second.py <TIE3_SERIES.json> --lists <run> --candles <run>`), `TIE3_SECOND_OUTPUT_landed.json`.
