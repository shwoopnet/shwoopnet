# research-data, the Oct 29 archive: table names, row counts and time spans (History Miner, 2026-11-13 ~21:50Z)

Read under the Head of R&D's go of 21:41Z:
- **What was read:** table names, row counts and the min and max of each table's time column only. No price, result or other value column was read, and nothing was extracted to any branch.
- **How:** the archive (research-data.tar.gz, six parts) was reassembled in scratch space and checked against MANIFEST.txt's WHOLE sha256 (15788a02..., matched). Only the 20 .sqlite files were extracted, opened read-only and deleted after counting.
- **Disclosure:** my first pass matched a column named `close` as a close time. In iv1.sqlite that column is a price, so its min and max were taken, but they printed only as 1970 dates. Those two spans are dropped, and iv1's spans below come from its `ts` column.

| Database | Table | Rows | Time column, span (UTC dates) |
|---|---|---|---|
| alts2 | market | 19,139 | close_ts Sep 3 to Oct 13 |
| alts2 | candle | 304,522 | end_ts Sep 3 to Oct 13 |
| alts3 | market | 32,314 | close_ts Aug 6 to Oct 13 |
| alts3 | candle | 514,564 | end_ts Aug 5 to Oct 13 |
| alts4 | market | 5,442 | close_ts Aug 6 to Sep 3 |
| alts4 | candle | 86,802 | end_ts Aug 6 to Sep 3 |
| arb2 | scan / row | 12 / 98,002 | scan ts Oct 28 to Oct 29 |
| arb3 | scan / row | 12 / 39,377 | scan ts Oct 28 to Oct 29 |
| arb4 | scan / row | 12 / 1,395 | scan ts Oct 29 |
| book | market | 10,293 | close_ts Sep 2 to Oct 12 |
| book | candle | 163,980 | end_ts Sep 2 to Oct 12 |
| crypto1 | bar / fund | 135,292 / 131,308 | ts 2019-01-01 to Oct 26 (bar), 2019-04-30 to Oct 26 (fund) |
| e3b | market | 13,062 | close_ts Aug 6 to Oct 13 |
| e3b | candle | 208,366 | end_ts Aug 5 to Oct 13 |
| fresh | market | 21,755 | close_ts Oct 11 to Oct 27 |
| fresh | candle | 345,068 | end_ts Oct 11 to Oct 27 |
| iv1 | bar / dvol | 230,404 / 230,031 | ts Aug 6 to Oct 25 |
| **l1b (the L1 holdout)** | market | 7,213 | close_ts Aug 6 to Sep 2 |
| l1b | candle | 114,990 | end_ts Aug 5 to Sep 2 |
| lad1 | market | 4,296 | close_ts Sep 26 to Oct 26 |
| lad1 | candle | 235,512 | end_ts Sep 26 to Oct 25 |
| lad2 | market | 9,969 | close_ts Sep 26 to Oct 26 |
| lad2 | candle | 525,002 | end_ts Sep 26 to Oct 25 |
| ladl1 | mk / done / q | 349 / 58 / 415 | close_ts Aug 24 to Oct 28 |
| rep | market | 9,039 | close_ts Aug 17 to Oct 22 |
| rep | candle | 139,596 | end_ts Aug 16 to Oct 22 |
| search5k | bar / dv / fund | 236,162 / 235,791 / 3,936 | ts Aug 4 to Oct 25 |
| sports1 | market | 10,887 | close_ts Sep 11 to Oct 27 |
| sports1 | candle | 528,298 | end_ts Sep 10 to Oct 27 |
| theta1 | market | 30,561 | close_ts Aug 30 to Oct 29 |
| theta1 | candle / done | 81,502 / 183,366 | end_ts Aug 23 to Oct 28 |

**Totals:** 20 databases, 41 tables; about 172,000 market rows and about 3.5 million Kalshi candle rows.
- The candles hold the bid and ask close and volume per minute, with no size, so a fill on them is at best "at the ask seen".
- crypto1, iv1 and search5k hold non-Kalshi bars and funding series (their sources are named in the README sections of the tests that made them).
- Many registered tests already read these closes (see section D of DATA_INVENTORY_NOV13.md), so a new card on them must check HELDOUT_REGISTRY first.
