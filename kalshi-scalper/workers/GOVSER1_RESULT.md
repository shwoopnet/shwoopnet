# GOVSER1 result (2026-11-05; registration `workers/GOVSER1_REGISTRATION.md`, pushed before the census): NOT_ENOUGH_DATA / NOT_RUNNABLE

Count-only census of settled events (Kalshi `/events?status=settled`), about 80 candidate government and agency series. No price, candle or outcome was read, nothing scored. N +1 (running about 730,441, z bar about 5.27).

| Series family (official source) | Settled events | Note |
|---|---|---|
| KXTNOTED (Treasury 10Y daily) | 664 (2023-02 to 2026-07-01) | `/markets` returns zero settled markets; SCOUT1 found median volume 0. Stopped 2026-07-01. NOT_RUNNABLE |
| KXCASED (Case-Shiller) | 256 | all listed on one date (2026-10-16), one settlement: 1 independent event |
| KX7YRRATEH (7Y yield hourly, Pyth) | 243 (2026-10-09 on) | 4 weeks of hours; a price feed, not an agency release; all but the last third post-cut |
| KXAAAGASW / KXAAAGASM (AAA) | 143 / 35 | covered by GAS1, GAS2, ECONNEW2 (FALSIFIED / NOT_ENOUGH_DATA) |
| KXNATGASD / KXNATGASW | 122 / 30 | exchange price, from 2026-05; not an agency release |
| KXDIESELD / KXDIESELW | 95 / 13 | AAA/EIA diesel; 95 events from 2026-08-28, inside the GAS family result (cheap strike overpriced, GAS2 -5.98c) |
| KXCPI, KXCPIYOY, KXJOBLESSCLAIMS, KXTSAW | 64, 47, 63, 277 | covered (NOWCAST1, CPI1, ECONNEW1, TSA1) |
| KXEGGS, KXADP, KXUST2A/5A/7A/10A/30A | 20, 20, 16 to 19 | under 100; SLOWSTAT1 NOT_RUNNABLE |
| KXEIACRUDEW, KXDIESELW, KXHOUSINGSTART, KXTGAW, KX10YRDIRHW/LW | 10, 13, 7, 4, 4 | under 25 events |
| Yield extremes monthly (DIRHM/LM, 2Y to 30Y) | 1 to 3 | far under |
| 25 other tickers tried (EIA gas storage, mortgage, PCE, ISM, retail sales, consumer sentiment, rents, home sales, etc.) | 0 | no such series or no settled markets |

**Verdict: NOT_RUNNABLE (best untested candidate KXTNOTED has events but no settled markets with quotes) and NOT_ENOUGH_DATA (no untested official-release family has 100 events; every one with 100 or more is either already covered by a registered test or is a price feed, not a release).** This matches the director's count (only 3 untested series with 100+ events, all dead). The ledger shows why a count will not rescue the idea: every official-series test so far (GAS1 -7.50c, GAS2 -5.98c, MORTGAGE1 -5.77c, ECONNEW1 +0.29c, WTIW1, TSA1) found the market mid a better forecast than the free outside series (Brier), so the outside fact is already in the quote.

**Accrual needed.** About 100 events of one release: weekly series need two years (EIA crude KXEIACRUDEW began 2026-08-28, 10 events; about 2028-08 for 100), monthly series about 8 years. Nothing to record: Kalshi keeps settled markets. Re-run this census on 2027-02-01 with SLOWSTAT1's. The only thing worth recording earlier would be the KXTNOTED daily ladder if Kalshi relists it with quotes.

Census raw numbers are in the table above (script was a scratch file, not committed).
