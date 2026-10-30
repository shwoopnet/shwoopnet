# SLOTEX-ETH registration (2026-10-30, written and pushed before any scoring)

Worker SLOTEX-ETH (part of SLOTEX), Strategy Research V2. Research only, information only, no tuning, no promote verb.

## Rule (pre-fixed, the same core as SLOTEX/GEN6, moved to Ethereum `KXETH15M`)
- Signal candle ends 180 s before the close. Cheap side = first of YES, NO whose ask is 5c to 50c there. doi = oi(-180 candle) minus oi(-360 candle) (`oi` the end-of-candle snapshot).
- Threshold (i) ETH-P90: Ethereum's own 90th percentile of doi, computed once on discovery windows only (closing 2026-08-06 to 2026-09-20, every window with both oi candles, any side), as `sorted(v)[int(0.9 * (n - 1))]` (the fals4 Check 5 method). Threshold (ii) ABS: 86,300 (fals4 `THRESH`). Fire when doi > threshold.
- Fill at the next candle's closing ask (-120 s). Exits: HOLD (settlement, no sell fee) and X60 (sell at the bid of the -60 candle; bid 0 or missing = stake lost, no sale).
- Fees 7% x C x p x (1-p) rounded up per order, on the entry and on the sell. C = 5 and 10. Costs: base, fees x1.2, entry +2c.
- Stages: discovery 2026-08-06 to 2026-09-20, validation 2026-09-21 to 2026-10-27. Nothing closing on or after 2026-10-28 is read. Code: `src/scalper/slotex.py` (`--eth`), reusing `fals4.py`'s loader with the series swapped.
- Also reported: share of entries with a nonzero bid at 60 s.

## Co-loss with Bitcoin (same 15 minute window, matched on close time)
"Lost" = that order's net < 0 under the exit (C = 10, base cost).
- Both fired: Bitcoin core (ABS, as scored in SLOTEX) and Ethereum (each threshold). Counts of windows where both fired, both lost, exactly one lost, neither; expected both-lost under independence = n x (BTC loss rate) x (ETH loss rate), the rates taken within those same windows.
- BTC fired, ETH did not: Ethereum's outcome in that window under the same side choice (ETH's own cheap side at its -180 candle, same fill and exit, no OI condition; skipped where ETH has no cheap side or no fill), with the same observed vs independence comparison.

## Counterparty
As GEN6: late takers who pay up for the favourite as open interest jumps, leaving the cheap side underpriced. Whether that is a Bitcoin-specific crowd or a cross-market one is what this asks.

## Prediction (before scoring)
Ethereum ABS fires far less often than Bitcoin (open interest is smaller), n under 100 per stage. ETH-P90 hold PF between 1.0 and 1.6 in validation. Co-loss above independence (Bitcoin and Ethereum move together): observed both-lost at least 1.3 times the independence figure.

## Kill rule (as SLOTEX)
A variant with PF < 1.5 in either stage at base, or <= 1.0 at fees x1.2 or at +2c, is FALSIFIED; otherwise NOT_YET_FALSIFIED (two windows only, information only). Co-loss cells carry no verdict.

## Cell count
- Scoring: 2 thresholds x 2 exits x 2 sizes x 3 costs x 2 stages = 48.
- Co-loss: (both fired + BTC-only vs ETH) x 2 ETH thresholds x 2 exits x 2 stages = 16.
- **N = 64.**
