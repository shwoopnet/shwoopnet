# NEWH3 registration (V2 worker NEWH3, 2026-10-30, research only; written and pushed before any outcome is read)

Three new mechanisms on Kalshi's 15 minute Bitcoin market (KXBTC15M), one of them against Kalshi's hourly Bitcoin ladder (KXBTCD):
4 tries. Two ideas from the brief are declined below without a try (one is a reworded tested idea, one is already covered by two
exit studies in the form the brief gives). Nothing here touches L1's code or anything live.

**Looked at before writing (no outcome, no quote at an entry time):** the README headings and the results of NEWH1, NEWH2, GEN6, GEN7,
FALS4, MECH1, SLOTEX, EVT1, BTCAVG, LATECAL, LOCK2H, LADL1, CONF2, TIMEX1, the ideas list that holds WIDENING and SPREAD1, and
`studies/SETTLEMENT_MECHANICS_2026-10-29.md`; the table layouts of `l1b`, `book`, `fresh`, `lad2`, `conf2_lad`; the COUNT of distinct
KXBTCD closes per window in `conf2_lad` (656 closes before 2026-09-21, 140 after; `lad2` adds Sep 26 to Oct 26); that ladder strikes
are $100 apart. No quote, mid, open interest, result or trade of any window in the universes below was read.

## Common to all

- **Windows by close time (UTC):** DISCOVERY close >= 2026-08-06 00:00Z and < 2026-09-21 00:00Z; VALIDATION close < 2026-10-28 00:00Z.
  Nothing closing on or after 2026-10-28 is read. The third window is the FORWARD record: a validation survivor goes to
  `workers/candidates/` with a freeze time after its commit and is read only by the forward ledger.
- **Data:** KXBTC15M 1 minute candles from `l1b`, `book`, `fresh` (first file wins per ticker); KXBTCD candles from `lad2` then
  `conf2_lad` (first file wins per ticker; both universes were chosen from quotes 55 to 52 minutes before each close, so no universe
  look-ahead). Ladder history starts 2026-08-24, so **H1's discovery window is Aug 24 to Sep 20** (stated now, before any look).
- **Fill:** at the closing ask of the NEXT candle (ending 60 s after the signal candle) for the side bought (YES ask, or 1 - YES bid
  for NO); held to settlement unless the rule sells; one decision per window at most. A missing signal or fill candle is a data gap,
  counted, never a trade.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, on every buy and every sell. Headline PF at C = 10; C = 1 reported;
  fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF reported with all trades and with trades whose fill candle had volume 0 removed.
- **Screen (the brief):** DISCOVERY PF >= 1.5 at C = 10 on >= 100 trades and net > 0 at fees x1.2; then VALIDATION PF >= 1.3 on >= 50
  trades and net > 0 at fees x1.2. Fewer trades than the minimum in either window is NOT_ENOUGH_DATA, never a pass. Day-clustered z
  reported; the deflated bar for N about 592,000 is z about 5.2, so even a survivor earns only a forward ledger entry.
- **Verdict words:** FALSIFIED, NOT_ENOUGH_DATA, NOT_YET_FALSIFIED, NOT_RUNNABLE.

## H1 BLADX: the 15 minute window and the hourly ladder at the shared close, which book is wrong (2 tries: H1a, H1b)

- **Structure.** At every top of the hour the KXBTC15M window (opened at :45) and the KXBTCD ladder close at the same instant and
  settle on the same 60 s BRTI average. The 15 minute strike K0 (its stored floor strike, known at :45) lies between two ladder strikes
  K_lo <= K0 < K_hi. Interpolating the ladder's mids linearly in strike gives the ladder's price for "average >= K0"; the 15 minute
  mid is a second price for the same event.
- **Universe (time only):** every settled KXBTC15M market whose close is a top of the hour, with ladder strikes K_lo and K_hi in the
  ladder file for that close, K_hi - K_lo <= $250.
- **Signal:** scan candles ending 840 s to 240 s before the close, in order; at each, ladder quotes are the last ladder candle ending at
  or before that time and no more than 300 s older (else no ladder quote); both ladder strikes and the 15 minute market must have
  bid > 0, ask < 1 and spread <= 0.05. D = mid15 - P_lad. The FIRST candle with |D| >= 0.06 is the signal; one per close.
- **H1a (the ladder is right):** buy the 15 minute side the ladder calls cheap (D < 0: YES; D > 0: NO) at the next 15 minute candle's
  ask, ask in [0.10, 0.90], else no trade.
- **H1b (the 15 minute book is right):** buy the ladder side the 15 minute book calls cheap (D > 0: ladder YES; D < 0: ladder NO) on
  whichever of K_lo, K_hi is nearer K0, at the next ladder candle's ask (the last ladder candle ending at or before the 15 minute fill
  candle's end and after the signal candle; none means no trade), ask in [0.10, 0.90], settled on that strike's result.
- **Counterparty:** the slower of two quoting bots on two books that settle on the same number; when the price moves, one book's
  makers refresh later and leave a stale quote for takers. Honest alternative: both books are quoted by the same firms and a 6c gap is
  noise of minute-close quotes (each book's last quote of the minute comes from a different second, LOCK2H).
- **How this differs:** NEWH2 GLADH was gold (Pyth single price at the close, KXGOLDH strikes $2 apart) and traded only the 15 minute
  leg; here it is Bitcoin (60 s average), the strike grid is $100, and BOTH legs are traded, so the test says which book is wrong.
  LADL1 was L1's favourite rule on the ladder alone (no comparison between books); LOCK2H looked only for riskless two-leg locks;
  CONF1 and CONF2 used the ladder as a same-side filter on L1 favourites (88c to 97c), not as a price for the 15 minute contract.
- **Prediction:** as on gold, the 15 minute book prices its own strike at least as well as an interpolation of two neighbours: H1a
  discovery PF about 0.8, H1b about 1.1. Both FALSIFIED (or NOT_ENOUGH_DATA if fewer than 100 discovery trades).
- **Kill:** discovery PF < 1.5 on >= 100 trades, or validation PF < 1.3 on >= 50, or net <= 0 at fees x1.2: FALSIFIED.

## H2 WIDEN: quoters withdraw in the last 5 minutes

- **Universe (time only):** every settled KXBTC15M market in the two windows.
- **Signal:** baseline spread = median of (ask - bid) over candles ending 840 s to 420 s before the close with bid > 0 and ask < 1
  (at least 4 such candles, else no signal). Scan candles ending 300 s to 120 s before the close; the FIRST with spread >= max(0.04,
  2 x baseline) and mid in [0.15, 0.85] is the signal.
- **Rule:** buy the cheap side (NO if mid > 0.5, YES if mid < 0.5; mid exactly 0.5: no trade) at the next candle's ask, ask in
  [0.05, 0.50], else no trade.
- **Counterparty:** takers who buy the favourite near the mid while the makers have stepped back because they see risk (a pending
  move or informed flow); a wider spread at a contested price says the outcome is less certain than the mid, so the cheap side is
  underpriced. Honest alternative: the spread widens on thin minutes and says nothing about the outcome.
- **How this differs:** ideas20's WIDENING (n 1) and SPREAD1 / TX5 were filters or exits on L1 favourites at 88c to 97c; this is a
  standalone cheap-side entry at a contested price after a widening in the last 5 minutes.
- **Control (information, not screened, not counted):** the same cheap-side rule at the first candle ending 300 s to 120 s with mid in
  [0.15, 0.85] and NO widening, in windows without a signal.
- **Prediction:** win rate within 2 points of the mean fill; discovery PF 0.9 to 1.1; FALSIFIED.
- **Kill:** as H1.

## H3 EXITOI: holders leaving before the close, read as an L1 exit (1 try; Bitcoin; L1 upkeep read, no entry rule)

- **Entries (L1's own, as in the history studies, but with this brief's fill):** at the candle ending 360 s before the close, the
  side whose price to buy (YES ask, or 1 - YES bid) is in [0.88, 0.97] (YES first); filled at the next candle's ask, fill <= 0.99.
- **Exit rule:** if the open interest at the candle ending 180 s before the close is at most 0.95 x the open interest at the candle
  ending 360 s (net contracts closed by at least 5%: holders exiting), sell at the closing bid of the next candle (ending 120 s) for
  the side held (YES bid, or 1 - YES ask), fee on the sale; a bid of 0 means hold. Otherwise hold to settlement.
- **Counterparty / mechanism:** holders who exit the favourite in the final minutes regardless of price (traders who will not carry
  risk into the averaging minute) push its bid down until 60 s; if that flow also predicts losses (they know something), selling with
  them at 120 s beats holding.
- **Not the open interest lead:** GEN6's core buys the CHEAP side after open interest ROSE; this reads a FALL as an exit trigger on
  L1's own favourite; it adds no entry and cannot change that lead's forward record.
- **Bar (the TIMEX1 "better than hold" bar, since an exit removes no entries):** on the same entries, PF of the rule above PF of hold
  by >= 0.03 at C = 10 in BOTH windows, with >= 50 triggered entries in each, and a day-clustered z of the per-entry difference
  (rule minus hold) >= 2.0 pooled. Also reported: triggered count, the mean change of the held side's bid from 120 s to 60 s for
  triggered against untriggered entries (the "sag"), and their loss rates.
- **Prediction:** the trigger fires on a few percent of entries; triggered entries lose slightly more often, but selling at 120 s gives
  up more wins than it saves (as TIME1, TX1, TX2 and EXIT2): FALSIFIED.

## Declined (no try spent)

- **The strike set from a 60 s average that the opening quotes may not anchor to:** this is L8 (2026-10-07, FALSIFIED, -2.38c, both
  halves negative). Reworded tested idea.
- **Does L1's favourite bid sag before 60 s, read as a time exit:** selling L1 at a fixed late time or on a weak late bid is TIME1,
  TX1 and TX2 (TIMEX1, 2026-10-29) and EXIT2; the calibration of the last 150 s quotes is LATECAL. H3 is the one untested form (an
  exit triggered by observable exit flow, not by price or time).

## Count

N tried: **4** (H1a, H1b, H2, H3). Controls and descriptive lines are not counted. Running count about 592,057 before, about 592,061
after (plus other workers' additions).
