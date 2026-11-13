# SPXSCALP: cheap-side S&P scalp (DRAFT, NOT REGISTERED)

Status: DRAFT written Nov 13, 2026 for the owner's S&P scalp. Nothing is registered, committed to a job or read. It is registered only after the owner names the market and before anyone reads the candles. VA ruling (Nov 13): VERSION of the closed mid-band scalp family, not NEW, so it does not count toward the 20 to 30. The Head freezes it as ONE try, counted.

## Rule (fixed before any data)
- Market: KXINX15M for the 15 minute variant (the owner's main case, about 25 minutes left, needs another series: market not named yet).
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
