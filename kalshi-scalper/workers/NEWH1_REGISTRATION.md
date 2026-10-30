# NEWH1 registration (Strategy Research V2 worker NEWH1, 2026-10-30, research only)

Written and pushed BEFORE any NEWH1 entry was joined to any outcome. Code will be `src/scalper/newh1.py`; result `workers/NEWH1_RESULT.md`.

## Ledger check (why these are new)

Read: `workers/RULES.md`, the README headings, the S01 to S42 and O1 to O42 catalogues, L1 to L14, `studies/NOVIEW_MECHANISMS_2026-10-28.md`,
`studies/SETTLEMENT_MECHANICS_2026-10-29.md`, and the GEN4 to GEN7, FALS3, FALS4, SLOTEX, EVT1, BTCAVG, LATECAL results. (`research/MECHANISMS.md`
is not in this repo; the README says it lives in `shwoop-server`, and covers equities.) Rejected as already tested: cross-window
momentum or reversal (S06 to S11, BTC1 CONT), shock and gap fades (S09, S14), opening burst and opening quote (S39, O13, first-5-minute
families), vol regime (L13, S10, S12, S13, S38), weekend Bitcoin (S13, O37), strike gap at the open (L8), final-minute averaging (L9, BTCAVG),
late calibration and underdog grids (LATECAL, GEN6), outside prices at minute resolution (GOLDFV1, XMAC1, GEN5), scheduled events (EVT1).

What is new below: the perpetual-spot basis (O34 was NOT_RUNNABLE for lack of a feed; Binance USD-M and spot 1 minute files are now on
disk), round-number barriers (never an input), staleness conditioned on a zero-volume frozen quote (L5/O11 were book-based and never run
on candles), the gold greater-or-equal tie rule on a frozen Pyth feed, and single-print noise reversion after a last-minute flip.

**Looked at before writing this (structure only, no NEXT-window outcome):** counts of contiguous gold window pairs with equal strikes
(15 of 5,598, Aug 6 to Oct 27; Bitcoin 0 of 7,850), counts of gold windows whose previous window's strike move was at most 5c (88) or 10c
(150), and gold windows by weekday (228 on Saturday or Sunday). An equal-strike pair reveals that window's own result (YES by the rule), not
the result of the window after it, which is what H4 trades.

## Common to every hypothesis (fixed now)

- **Markets:** KXGOLD15M, KXBTC15M (owner's focus). Universe: every settled window in `data/l1b.sqlite`, `book.sqlite`, `fresh.sqlite`
  (first file wins per ticker), chosen by date only.
- **Windows by close time (UTC):** DISCOVERY 2026-08-06 00:00 to 2026-09-21 00:00; VALIDATION 2026-09-21 00:00 to 2026-10-28 00:00.
  Nothing closing on or after 2026-10-28 00:00 is loaded. Validation is read once, after discovery is written down.
- **Fill:** the bought side's closing ask on the candle AFTER the signal candle (YES at `ask_c`, NO at 1 - `bid_c`). Missing candle, or ask
  not strictly inside (0, 1): no trade (counted). The signal candle's own ask is reported as an optimistic line, never screened.
- **Held to settlement.** Net per order = C x (win - fill) - fee; fee = 7% x C x p x (1 - p) rounded UP to the cent per order, at C = 1 and
  C = 10; fees x1.2 reported. PF = gross wins / gross losses, the screen uses C = 10.
- **Zero volume both ways:** every figure is reported for all trades and for trades whose fill candle had volume above 0.
- **Screen (per variant):** discovery PF 1.5 or more on 100+ trades; then validation PF 1.3 or more on 50+ trades with net above 0 at fees
  x1.2. Under 100 discovery or 50 validation trades: NOT_ENOUGH_DATA. Day-clustered z reported; the deflation bar for N about 592,000 is z
  about 5.2 and nobody expects it met. A validation survivor goes to `workers/candidates/` with `scalper.newh1:forward_eval` and a parity
  check, frozen at or after its commit time.
- **Outside data (Bitcoin only):** Binance BTCUSDT spot 1 minute klines and USD-M perpetual 1 minute klines (`data/binance/`, plus 2026-10-27
  fetched from data.binance.vision into `data/newh1/`). A kline is used only if its close time is at or before the signal candle's end T
  (the kline with open time T - 60 s closes at T). Missing klines: no trade (counted).

## H1 BASIS (Bitcoin): the perpetual premium leads spot (N = 2)

- **Mechanism and counterparty.** Leveraged demand shows first in the perpetual's premium over spot; spot (and BRTI, a spot index)
  follows within minutes. Losers: Kalshi quoters who price the contract from spot distance only, not from derivatives positioning.
- **Rule.** Signal candle ends T = 600 s before the close. b(t) = ln(perp close / spot close) per minute. z = (b(T) - mean) / sd over the
  60 minutes ending T - 60 (at least 50 present, sd above 0). Variant **BASIS_F** (follow): z >= +2 buy YES, z <= -2 buy NO. Variant
  **BASIS_R** (reverse, crowded leverage unwinds): the opposite sides. Fill ask in [0.10, 0.90].
- **Prediction.** Both fail: discovery PF 0.8 to 1.2; the basis is a few basis points and arbitraged in seconds. FALSIFIED.

## H2 ROUND (Bitcoin): round-number barriers (N = 2)

- **Mechanism and counterparty.** Take-profit and stop orders cluster at round prices (Osler 2003, FX), so price stalls at a round level
  more often than a diffusion says. When the underdog needs spot to cross a round level to win, it wins less often than quoted. Losers:
  underdog buyers and quoters using a level-free model.
- **Rule.** T = 600 s before the close; S = spot close of the kline ending at T; K = strike. Favourite = YES if S >= K else NO. Variant
  **ROUND500**: a multiple of $500 lies strictly between S and K; **ROUND1000**: a multiple of $1,000. Buy the favourite if its fill ask is in
  [0.55, 0.92]. Reported, not screened: the same band with no such level between S and K (control).
- **Prediction.** Fails; difference from control under 2 points of win rate. FALSIFIED.

## H3 STALE0 (Bitcoin): a frozen zero-volume quote while spot moved (N = 1)

- **Mechanism and counterparty.** In a minute with no trade, a resting quote that did not move is a stale order; if spot moved hard that
  minute, the side spot moved toward is cheap. Losers: resting makers who have not refreshed.
- **Rule.** Scan candles ending 780 to 180 s before the close, first match per window: the candle has volume 0 and the same `bid_c` and
  `ask_c` as the candle before it (both present); spot log return over that minute r with |r| >= 2 sigma1 (sigma1 = sd of the 60 one minute
  log returns ending one minute earlier, at least 50). r > 0 buy YES, r < 0 buy NO. Fill ask in [0.10, 0.90].
- **Prediction.** Fails: the next candle's quote has caught up (GEN5, XMAC1). Discovery PF under 1.2. FALSIFIED. The signal-candle ask line
  shows whether any staleness existed at all.

## H4 GTIE (gold): the greater-or-equal tie on a frozen Pyth feed (N = 2)

- **Mechanism and counterparty.** Gold settles YES when the Pyth close at the close is AT LEAST the strike, so a tie pays YES. When the
  feed is frozen (thin hours, weekends, publisher gaps) ties are common and YES is worth more than a symmetric 50c. Losers: quoters who
  price the open at 50/50.
- **Rule.** Window k with contiguous k - 1 (15 minutes earlier). m = strike(k) - strike(k - 1) (window k - 1's reference move, public at
  k's open). Variant **GTIE0**: m = 0 to the cent; **GTIE5**: |m| <= $0.05. Signal candle ends 840 s before the close; buy YES at the
  next candle's ask (780 s) if it is in [0.30, 0.70].
- **Prediction.** GTIE0 NOT_ENOUGH_DATA (about 15 windows in all); GTIE5 FALSIFIED (88 windows, under 100, so also likely
  NOT_ENOUGH_DATA). Reported for both: the share of entries whose settlement equals the strike.

## H5 FLIPREV (gold, Bitcoin control): single-print noise reverses after a last-minute flip (N = 2)

- **Mechanism and counterparty.** Gold settles on one Pyth print at one instant; a last-minute jump that flips the result is partly print
  noise that reverses, and that print is also the NEXT window's strike. Losers: next-window quoters who treat the opening print as fair.
  Bitcoin settles on a 60 second average, so its version is the control (less noise to reverse).
- **Rule.** Window k - 1 (contiguous): mid60 = YES mid of its candle ending 60 s before its close; res = 1 if it settled YES. Flip if
  |res - mid60| >= 0.6; d = sign(res - mid60). In window k: signal candle ends 840 s before the close, buy the side opposite d (d > 0 buy
  NO) at the next candle's ask if in [0.30, 0.70]. Variants **FLIPREV_GOLD**, **FLIPREV_BTC**.
- **Prediction.** Both fail (S09 found no reversal of large strike moves; by 780 s the quote has absorbed any reversal). FALSIFIED.

## Kill criteria and counts

- Any variant missing the screen at discovery is FALSIFIED (or NOT_ENOUGH_DATA under 100 trades) and is not looked at in validation for
  selection (its validation line is still printed for the record). Nothing is re-tuned after a score.
- A survivor that fails a fill one candle later (PF below 1.0) or fees x1.2 is FALSIFIED.
- **N tried: 9** (BASIS 2, ROUND 2, STALE0 1, GTIE 2, FLIPREV 2). Controls and optimistic fill lines are reported, not screened.
  Running count about 591,970 before, about 591,979 after.
