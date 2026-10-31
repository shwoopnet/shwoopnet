# OICOREX1 inventory: which 15 minute series have usable open interest (2026-10-31)

Worker OICOREX1. Counts only, no outcome is read. Source: every 15 minute series in `data/{e3b,alts2,alts3,alts4,rep,fresh,l1b,book,five}.sqlite` (a ticker in two files is taken once, first file in that order; settled windows only). "Usable" = `oi` present at the candles ending 360 s and 180 s before the close in nearly every window AND moving between them (a flat or empty `oi` cannot make a `doi`). Spread = ask minus bid of the YES side at the candle ending 180 s before the close (median over windows with that candle).

| series | settled windows | candles | first / last close (UTC) | windows with oi at -360 and -180 | oi at -180 differs from oi at -360 | median spread at -180 | windows with a 5c to 50c side at 180 s | usable? |
|---|---|---|---|---|---|---|---|---|
| KX10YRRATE15M | 158 | 1499 | 10-19 / 10-22 | 10.8% | 2.5% | 0.270 | 16 | no: oi null in 80%+ of windows and flat; 158 windows |
| KX2YRRATE15M | 158 | 1482 | 10-19 / 10-22 | 15.2% | 2.5% | 0.900 | 11 | no: oi null in 80%+ of windows and flat; 158 windows |
| KX30YRRATE15M | 158 | 1506 | 10-19 / 10-22 | 15.2% | 2.5% | 0.920 | 8 | no: oi null in 80%+ of windows and flat; 158 windows |
| KX5YRRATE15M | 158 | 1535 | 10-19 / 10-22 | 19.6% | 4.4% | 0.940 | 6 | no: oi null in 80%+ of windows and flat; 158 windows |
| KXAUDUSD15M | 1008 | 15733 | 10-07 / 10-22 | 97.2% | 94.8% | 0.020 | 592 | oi yes, but no discovery data (history is Oct 5 to 22): NOT_ENOUGH_DATA |
| KXBNB15M | 8133 | 129685 | 08-06 / 10-30 | 100.0% | 100.0% | 0.009 | 4118 | yes, scored (try-cap rank, see registration) |
| KXBRENT15M | 71 | 1089 | 10-21 / 10-22 | 91.5% | 77.5% | 0.080 | 51 | no: 71 windows (Oct 21 to 22 only) |
| KXBTC15M | 8137 | 129749 | 08-06 / 10-30 | 100.0% | 100.0% | 0.001 | 4437 | reference (the core's own market) |
| KXCOPPER15M | 4332 | 68792 | 08-27 / 10-30 | 100.0% | 100.0% | 0.010 | 2810 | oi yes; NOT scored: below the 8 try cap by the pre-set rank |
| KXDOGE15M | 8137 | 129761 | 08-06 / 10-30 | 100.0% | 100.0% | 0.007 | 4158 | yes, named by the owner (scored) |
| KXETH15M | 8137 | 129760 | 08-06 / 10-30 | 100.0% | 100.0% | 0.004 | 4143 | oi yes; already FALSIFIED (SLOTEX-ETH), not reopened |
| KXEURUSD15M | 2532 | 40070 | 09-23 / 10-30 | 98.9% | 97.6% | 0.020 | 1554 | oi yes, but history starts on or after Sep 18, so no discovery threshold can be set: NOT_ENOUGH_DATA |
| KXGBPUSD15M | 2532 | 39986 | 09-23 / 10-30 | 98.1% | 96.3% | 0.020 | 1643 | oi yes, but history starts on or after Sep 18, so no discovery threshold can be set: NOT_ENOUGH_DATA |
| KXGOLD15M | 5903 | 93827 | 08-06 / 10-30 | 100.0% | 100.0% | 0.010 | 3671 | oi yes; already FALSIFIED (GEN6, GEN7), not reopened |
| KXHYPE15M | 8133 | 129677 | 08-06 / 10-30 | 100.0% | 100.0% | 0.007 | 3922 | yes, scored (try-cap rank, see registration) |
| KXNATGAS15M | 4561 | 72502 | 08-27 / 10-30 | 100.0% | 100.0% | 0.010 | 3191 | oi yes; NOT scored: below the 8 try cap by the pre-set rank |
| KXNEAR15M | 8137 | 129725 | 08-06 / 10-30 | 100.0% | 100.0% | 0.010 | 4491 | yes, scored (try-cap rank, see registration) |
| KXPALLADIUM15M | 2771 | 43797 | 09-17 / 10-30 | 100.0% | 100.0% | 0.020 | 1907 | oi yes, but history starts on or after Sep 18, so no discovery threshold can be set: NOT_ENOUGH_DATA |
| KXPLATINUM15M | 2771 | 43781 | 09-17 / 10-30 | 99.9% | 99.9% | 0.020 | 1773 | oi yes, but history starts on or after Sep 18, so no discovery threshold can be set: NOT_ENOUGH_DATA |
| KXSILVER15M | 5872 | 93157 | 08-06 / 10-30 | 100.0% | 99.9% | 0.010 | 3677 | yes, scored (try-cap rank, see registration) |
| KXSOL15M | 6320 | 100829 | 08-17 / 10-22 | 100.0% | 100.0% | 0.006 | 3200 | oi yes; NOT scored: below the 8 try cap by the pre-set rank |
| KXUSDCAD15M | 1008 | 15923 | 10-07 / 10-22 | 97.8% | 95.4% | 0.020 | 633 | oi yes, but no discovery data (history is Oct 5 to 22): NOT_ENOUGH_DATA |
| KXUSDJPY15M | 2532 | 40004 | 09-23 / 10-30 | 98.9% | 98.0% | 0.020 | 1628 | oi yes, but history starts on or after Sep 18, so no discovery threshold can be set: NOT_ENOUGH_DATA |
| KXWTI15M | 6101 | 97021 | 08-06 / 10-30 | 100.0% | 100.0% | 0.010 | 3902 | yes, scored (try-cap rank, see registration) |
| KXXRP15M | 8137 | 129740 | 08-06 / 10-30 | 100.0% | 100.0% | 0.006 | 4169 | yes, named by the owner (scored) |
| KXZEC15M | 8137 | 129714 | 08-06 / 10-30 | 100.0% | 100.0% | 0.011 | 4272 | yes, scored (try-cap rank, see registration) |


Notes
- Dropped for unusable open interest: the four rate markets (KX2YRRATE15M, KX5YRRATE15M, KX10YRRATE15M, KX30YRRATE15M).
- No discovery data (the threshold is fixed from discovery windows, 2026-08-06 to 2026-09-20 UTC, so a series without them cannot be scored): KXBRENT15M, KXAUDUSD15M, KXUSDCAD15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXPALLADIUM15M, KXPLATINUM15M. Each is NOT_ENOUGH_DATA and costs no try.
- KXSOL15M comes from `rep.sqlite` only (2026-08-17 to 2026-10-22) and has no windows after 2026-10-22.
- Eleven series have usable open interest and a full discovery period; the try cap is 8, so the choice among them is fixed in the registration by an outcome-free rank.
