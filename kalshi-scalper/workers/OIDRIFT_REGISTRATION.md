# OIDRIFT registration: Bitcoin open interest core with a drifting threshold, forward only (research only)

Written and pushed BEFORE the candidate file exists and before the forward ledger scores any window. 1 try, no tuning.

**Ledger check.** Not a new idea: it is GEN6's open interest core (`workers/candidates/REF_GEN6_OICORE.json`, FALS4 SURVIVES,
`workers/FALS4_RESULT.md`) with the threshold defined the way FALS4's check 5 computed it. It is a second forward definition of the
same bet, so the two rows are NOT independent evidence: most drift signals are also fixed-threshold signals.

## The rule, exactly (candidate `REF_GEN6_OIDRIFT`, evaluator `scalper.oidrift:forward_eval`)

- Market `KXBTC15M` only. Source `candles` (1 minute candles, `end_ts -> (yes_bid_close, yes_ask_close, volume, oi)`).
- Signal candle: the one ENDING exactly 180 s before the close. Back candle: the one ending 360 s before the close.
  `doi = oi(-180) - oi(-360)`. A missing signal or back candle, or an open interest of 0 there (the ledger stores a missing oi as 0),
  is NoData, never a no-trade.
- Threshold for a window closing on UTC day D: the 90th percentile (`sorted(v)[int(0.9 * (len(v) - 1))]`) of `doi` over every
  settled KXBTC15M window closing in `[D - 30 days, D)` (UTC midnights), i.e. earlier days only, all strictly before the scored window.
  Inputs read from `data/l1b.sqlite`, `data/book.sqlite`, `data/fresh.sqlite` (first file holding a ticker wins, as FALS4), with the
  raw candle oi (null oi excluded). Fewer than 20 distinct days with a value in that span: NoData.
- Trade when `doi > threshold`. Side: the cheap side at the signal candle, YES first (YES ask in [0.05, 0.50]; else NO ask =
  1 - YES bid in [0.05, 0.50]); neither in band: no trade.
- Fill: that side's closing ask on the candle ending 120 s before the close (the next candle). Missing: NoData. Held to settlement.
- Freeze: written in the candidate file, at or after its commit time, rounded up to the next hour UTC. Only windows closing after it
  count. No window closing on or after 2026-10-28 is scored by me outside the ledger's forward path.

## Counterparty

As GEN6 / FALS4: the takers who pile into the favourite during a burst of new contracts 3 to 6 minutes before the close and pay up for
it; the cheap side is mispriced low after the burst (FALS4 check 7: the favourite in the same windows, PF 0.36 / 0.45).

## Parity (history, before the freeze, information)

On Sep 21 to Oct 27 (validation) the evaluator, fed windows built the way the ledger builds them, must reproduce FALS4 check 5:
n 67, PF 2.65 at C = 10. Any trade-level mismatch is reported in `workers/OIDRIFT_RESULT.md`. Discovery will differ from FALS4's
72 / 5.19 because this rule needs 20 days, FALS4's check needed 10.

## Prediction and kill

- Prediction: forward PF at 10 contracts between 1.2 and 2.5 once it has 30 trades; about 1.8 trades a day (67 over 37 days).
- Kill (FALSIFIED): forward PF at 10 contracts below 1.0 after 40 trades, or below 1.3 after 80. Fees 7% x C x p x (1-p) rounded up
  per order at C = 1 and 10, and a x1.2 stress, as the ledger prices them. Zero-volume candles: reported by the ledger flag.
- The ledger's READY FOR THE FALSIFIER line earns a falsifier read only. Verdict words per `workers/RULES.md`.

## Tries

N added: 1 (this forward definition). Parity is a reproduction of FALS4's already counted check 5 and adds no try.
