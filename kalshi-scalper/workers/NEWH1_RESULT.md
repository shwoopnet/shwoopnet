# NEWH1 result (V2 worker NEWH1, 2026-10-30, research only)

Registration `workers/NEWH1_REGISTRATION.md` (commit 1c2f164, pushed before any scoring). Code `src/scalper/newh1.py`
(`PYTHONPATH=src NEWH1_STAGE=val python -m scalper.newh1`). Full printout `studies/newh1_result_2026-10-30.txt` (aggregates only).
Data: candles `l1b`, `book`, `fresh` (Bitcoin 7,869 windows: 4,357 discovery Aug 6 to Sep 20, 3,512 validation Sep 21 to Oct 27; gold
5,650: 3,197 / 2,453); Binance BTCUSDT spot and USD-M perpetual 1 minute klines Aug 1 to Oct 27 (126,720 minutes each, Oct 27 fetched
from data.binance.vision). Nothing closing on or after 2026-10-28 was loaded. Fill at the next candle's closing ask, held, C = 10 for the
screen, fee rounded up per order. Nothing was changed after the score.

## Verdicts

| Variant | Market | Disc n / PF10 / PF1 / PF x1.2 | Val n / PF10 / PF x1.2 | Verdict |
|---|---|---|---|---|
| BASIS_F (perp premium z >= 2, follow) | BTC | 251 / 0.84 / 0.82 / 0.82 | 201 / 0.97 / 0.96 | FALSIFIED |
| BASIS_R (same, reversed) | BTC | 250 / 0.98 / 0.96 / 0.96 | 203 / 0.85 / 0.84 | FALSIFIED |
| ROUND500 (favourite, a $500 level between spot and strike) | BTC | 434 / 0.99 / 0.96 / 0.97 | 429 / 0.97 / 0.96 | FALSIFIED |
| ROUND1000 ($1,000 level) | BTC | 249 / 0.93 / 0.91 / 0.92 | 189 / 0.77 / 0.75 | FALSIFIED |
| STALE0 (frozen zero-volume quote, spot moved 2 sigma) | BTC | 0 | 0 | NOT_ENOUGH_DATA |
| GTIE0 (previous window tied, buy YES at the open) | gold | 2 / 0.88 | 5 / 0.31 | NOT_ENOUGH_DATA |
| GTIE5 (previous move at most 5c) | gold | 36 / 0.81 | 20 / 0.86 | NOT_ENOUGH_DATA |
| FLIPREV_GOLD (fade a last-minute flip at the next open) | gold | 143 / 0.69 / 0.68 / 0.68 (z -2.34) | 104 / 0.92 / 0.90 | FALSIFIED |
| FLIPREV_BTC (control) | BTC | 148 / 0.86 / 0.85 / 0.85 | 87 / 1.16 / 1.15 | FALSIFIED |

No variant reached discovery PF 1.5 (the best was 0.99), so nothing was selected for validation; the validation lines are printed for
the record only. Zero volume both ways: every trade's fill candle had volume above 0, so both lines are identical. Fill one candle later
and the signal candle's own ask change nothing (all within 0.75 to 1.24, see the printout). **No candidate written to
`workers/candidates/`, so no evaluator was frozen and no parity check was needed.**

## What each one says

- **BASIS:** the perpetual premium carries no lean Kalshi has missed, either way, at 10 minutes left.
- **ROUND:** a round level between spot and the strike does not help the favourite; the no-level control (2,412 and 1,639 entries) is
  PF 1.02 and 0.98, and the level cells are at or below it. No barrier effect at this horizon.
- **STALE0:** the premise does not exist on candles. Every Bitcoin candle from 780 to 180 s before the close (86,559 of 86,559) has volume
  above 0, so a frozen zero-volume quote never occurs at minute resolution. Staleness, if any, lives under a minute (recorder data only).
- **GTIE:** ties are too rare to trade: 15 equal-strike gold pairs in 5,598 (0.27%); after a near-frozen window the next window settled on
  its strike in 2 of 34 (GTIE5 disc 5.9%, val 0%), not enough to beat a 50c ask plus fee.
- **FLIPREV:** no reversal of single-print noise; gold's discovery loses clearly (win 44% at a 51c fill).

## Count

**N added: 9** (BASIS 2, ROUND 2, STALE0 1, GTIE 2, FLIPREV 2; the two ROUND controls are reported, not screened). Running count about
591,970 before, about **591,979** after.
