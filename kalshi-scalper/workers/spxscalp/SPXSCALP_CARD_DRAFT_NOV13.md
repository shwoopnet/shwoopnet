# SPXSCALP: cheap-side S&P scalp (DRAFT, NOT REGISTERED)

Status: REGISTERED Nov 13, 2026 (before any candle or ES value was read), on the owner's instruction, as ONE counted try labelled VERSION (the VA: the reference-lag family on a new market; earlier ruled a version of the closed mid-band scalp family). It does NOT count toward the 20 to 30. The 0.05% threshold is a guess from the owner's words, fixed, no other tried. Counterparty: none named. The scorer takes the ES path as an argument and writes no ES-derived file; results go by message only. Still to do before any read: frozen scorer, Auditor B CLEAN, then the Testing Desk runs it from its scratch after SPXOI1_CANDLES lands and passes the structure check.

## Rule (fixed before any data)
- Market: KXINX15M (named by the owner, Nov 13). The owner's main case (about 25 minutes left) would need another series and is not part of this card.
- Entry: buy the CHEAP side when its ask is 20c to 25c, with 10 or more minutes left. Variant: band 20c to 30c (one variant, counted as part of this one try).
- Exits, all fixed now:
  - Headline: sell at 2x the entry price, or at the fixed time exit with 5 minutes left, whichever comes first.
  - Variant: sell half at 2x, hold the rest to 80c, else the time exit.
  - Comparison: hold to settlement.
- One entry per window (the first look in band).
- Size: 1 contract for the read; no live order.

## Costs and reads (C1 to C10, C7 to C10)
Entry at ask +1c, exit at bid -1c, per-order rounded fees, every figure printed at 1c AND 2c. A rule counts only at PF 1.3 with both halves 1.0 or better at 1c AND PF 1.0 or better at 2c. A rule entering or exiting in the last 2 minutes uses 2c as primary. A void refunds the price, keeps the fee, and the void count is reported. Every line says "upper bound, not fill-checked"; the 2x target fill is not fill-checked (HS1: prices jump through targets). First check before any P&L: are the index candles two-sided, and how wide is their spread (C1).

## Counterparty
None named. A price band is not a participant.

## Prediction and kill lines
Numeric prediction: none claimed beyond the null. Realistic answer: "no evidence" or FALSIFIED. Kill: FALSIFIED if 1c PF is under 1.0 in either half, or 2c PF under 1.0, or fewer than 100 entries.

## Data and held-out
Development: KXINX15M closes before 2026-12-01T00:00:00Z, on landed candles only. Held out: from 2026-12-01 onward; nothing on or after that date is touched (the date is a constant in any scorer). About 143 windows, one entry each, so PF 1.3 cannot be told from luck and the label is "no evidence" below the bar. SPXOI1 and SPXFV1 are registered on the same development windows, so this is a third look at them, counted as a try. The candle pull and scorer must be frozen (commit and sha256) and audited CLEAN by Auditor B before any landed file is opened (rules 16/16b).

## Closest existing
GEN12 and GEN13 (226 exits searched, 0 survivors), H4, SS1, SS2, EXIT1, EXIT2, HS1, and the 7e row "cheap-side price, regime and grammar rules".

## Update Nov 13: the owner's outside input (still no read, not registered)
The owner: "spx future charts are usually a little ahead it seems". The entry becomes a lead trigger, not a bare price band:
- With 10 or more minutes left, take the ES future's 1 minute close at the decision minute minus its close at the window's start minute. If the move is at least THRESHOLD in one direction, the side that direction favours is the candidate side. THRESHOLD is 0.05% of the ES level (a move of a few index points), fixed here from the owner's description only ("a little ahead" gives no number), not from any data; it is a guess and the card says so. No other threshold is tried.
- Buy the candidate side only if its Kalshi ask is 20c to 25c (variant 20c to 30c). If the candidate side is the favourite (priced above 50c) no order: the cheap-side rule is the only arm, and the favourite arm is the favourite-and-hold ban.
- Exits, haircuts C1 to C10 and the held-out date 2026-12-01 are unchanged. One try, counted.
- Data: KXINX15M candles (landing) and the ES one minute bars for Nov 5 to 12 held in the Testing Desk's scratch. The ES bars come from Databento: NO ES value, figure or derived row is ever written to this repo or any branch; this card only names the source; results go by message only. The scorer must read ES from the scratch path given as an argument and write no ES-derived file.
- Pending VA ruling NEW or VERSION against SPXFV1, LEADLAG1 and CFRTI-K. Register only after that ruling. Counterparty: if a lead is real, the counterparty is slower quote updaters on Kalshi; this is a guess and is "none named" until the VA accepts it.
