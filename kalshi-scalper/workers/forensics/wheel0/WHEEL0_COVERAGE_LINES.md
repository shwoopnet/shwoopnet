# WHEEL0: coverage lines of the landed candle runs (counts only)

One line a file, as the Head of R&D ordered. `wheel0_coverage.py` reads the lists with the result field untouched and scores nothing. Nothing is joined to an outcome and
`wheel0.py` (sha256 `10a7b363...`, unchanged) does not run before the Head's go, which waits for DEPTH1's read.

| Landed run | Checked | Line |
|---|---|---|
| `pull/WHEEL0_CANDLES_XRP/2026-11-13T0205Z_43349567884` | Nov 13, 02:14Z | 246 of 246 requests answered, none truncated, 41.8 MB (guide 42.3, so no split); 5,866 markets asked for, 5,866 with any candle, 5,866 with a candle at all three looks (600, 360 and 180 s before the close), 5,854 two-sided at all three, 5,866 with every minute from 600 to 180 s; closes 2026-09-12 00:00Z to 2026-11-12 20:15Z. |
| `pull/WHEEL0_CANDLES_DOGE/2026-11-13T0215Z_43350776238` | Nov 13, 02:26Z | 246 of 246 requests answered, none truncated, 41.8 MB (guide 42.3, so no split); 5,866 markets asked for, 5,866 with any candle, 5,866 with a candle at all three looks, 5,851 two-sided at all three, 5,866 with every minute from 600 to 180 s; closes 2026-09-12 00:00Z to 2026-11-12 20:15Z. |
| `pull/WHEEL0_CANDLES_GOLD/2026-11-13T0226Z_43352150367` | Nov 13, 02:40Z | 179 of 179 requests answered, none truncated, 29.0 MB (guide 30.8, so no split); 4,064 markets asked for, 4,059 with any candle (5 with none), 4,059 with a candle at all three looks, 4,058 two-sided at all three, 4,059 with every minute from 600 to 180 s; closes 2026-09-12 00:00Z to 2026-11-12 20:15Z. |
| `pull/WHEEL0_CANDLES_ETH/2026-11-13T0237Z_43353458562` | Nov 13, 02:45Z | 187 of 187 requests answered, none truncated, 31.9 MB (guide 32.2, so no split); 4,464 markets asked for, 4,464 with any candle, 4,464 with a candle at all three looks, 4,461 two-sided at all three, 4,464 with every minute from 600 to 180 s; closes 2026-09-12 00:00Z to 2026-10-28 23:45Z (the last close its job asked for). |

All four candle runs have landed and are complete (XRP, DOGE, gold, Ethereum): 858 of 858 requests answered, none truncated, no split needed. The premise test still waits:
nothing is joined to an outcome and `wheel0.py` does not run before the Head's go, which comes only after DEPTH1's read is reported and the `DEPTH1 READ MADE:` line is committed.
