# NEWH7 result (V2 worker NEWH7, 2026-10-30, research only)

Registration `workers/NEWH7_REGISTRATION.md` (commit 16ef7d0, pushed before any data was fetched or scored). Code
`src/scalper/newh7.py` (`PYTHONPATH=src python -m scalper.newh7 fetch`, then `run`, run once). Printout
`studies/newh7_result_2026-10-30.txt` (aggregates only). Nothing was changed after the score.

**Data (public, no key, into `data/newh7.sqlite`, ignored by git):** CBOE GVZ daily closes and Yahoo GC=F daily closes (145 dates
each, same dates); Deribit BTC DVOL and BTC-PERPETUAL 1 minute; Coinbase BTC-USD 1 minute; Binance spot BTCUSDT 1 minute
(123,653 to 123,840 minutes each, 2026-08-03 to 2026-10-27 23:59 UTC). Nothing on or after 2026-10-28 was fetched or loaded.
Kalshi: the NEWH6 candle loader (gold 5,645 windows, Bitcoin 7,869). Fills at the next candle's ask; H1 and H2 held to settlement
(no sale); H3 sold at the bid, zero-bid rule as NEWH6 (it never fired: no-sale 0). Fees rounded up per order on every buy and sell.
**Zero volume both ways:** no fill or sale candle had volume 0, so both lines are identical.

## Verdicts (PF at C = 10 unless stated; C = 1 and fees x1.2 in the printout)

| Rule | Market | Disc n / PF10 / PF1 / PF x1.2 / day z | Val n / PF10 / PF x1.2 / day z | Verdict |
|---|---|---|---|---|
| H1 IVGAP (GVZ / RV20 top third; cheap side 10-40c at 600 s, held) | gold | 805 / 0.85 / 0.83 / 0.84 / -1.71 | 1,131 / 0.81 / 0.80 / -4.56 | FALSIFIED |
| H1 IVGAP (DVOL / RV24h top third; same trade) | Bitcoin | 892 / 0.84 / 0.82 / 0.83 / -1.75 | 421 / 0.81 / 0.80 / -1.19 | FALSIFIED |
| H2 COINPREM (Coinbase-over-Binance premium 15 min change, top or bottom decile; that side at 20-50c, held) | Bitcoin | 257 / 0.93 / 0.91 / 0.91 / -0.55 | 180 / 0.78 / 0.77 / -1.69 | FALSIFIED |
| H3 VEGALAG (DVOL 5 min rise at the 99th percentile; cheap side, sold 3 min later) | Bitcoin | 43 / 0.67 / 0.60 / 0.64 / -1.18 | 49 / 0.75 / 0.71 / -0.86 | NOT_ENOUGH_DATA (point estimates below 1) |

**Screen passes: 0.** No candidate written to `workers/candidates/`, so no evaluator was frozen and no parity check was needed
(`forward_eval` in the module only raises NoData).

## What each one says

- **IVGAP:** the cheap side at 10 minutes left loses about 3c to 4c a contract on both markets whatever the volatility gap
  (information lines, all windows: gold PF 0.81 / 0.81, Bitcoin 0.81 / 0.87). The top-third gap days are no better than the rest
  (gold 0.85 against 0.79 in discovery, 0.81 against 0.83 in validation; Bitcoin 0.84 against 0.80, then 0.81 against 0.89). Kalshi's
  makers do not underprice moves when options pay for more movement; the cheap side stays overpriced, as UNDER1 and TAIL found.
- **COINPREM:** a 15 minute rise in the Coinbase premium (cuts about +/-1.2 basis points) does not carry Bitcoin's outcome past
  what Kalshi already quotes; the side it points to wins about 31% to 34% at an average 34c fill. Kalshi's quoters see the US venues.
- **VEGALAG:** a DVOL jump at the 99th percentile (0.21 points in 5 minutes) lands inside 10 to 7 minutes before a close with a cheap
  side only 92 times in 83 days (fewer than predicted: the jumps cluster); its round trips lose 2c to 3c a contract. Too few to screen.
- **Declined without a try (in the registration):** DVOL fair value against the book (IV1, LAD1), GVZ fair value at minute
  resolution (no gold minute path before Oct; GOLDFV1), the US equity open and close windows (S12, EVT1's CME_BTC_CLOSE; gold one
  window a day), the LBMA auctions (FIX1; one or two windows a day), Kalshi listing and volume metadata (empty book at open, OI
  already GEN6/GEN7/MECH1, no signed counterparty for volume attention outside the closed favourite trade).

## Count

**N added: 4** (IVGAP gold, IVGAP Bitcoin, COINPREM, VEGALAG; information lines not counted). Running count about 592,082 (after
NEWH6) plus other workers' additions, plus 4.
