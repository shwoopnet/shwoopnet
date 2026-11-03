# SPIKE1 registration: mean reversion after a contract-implied spike on the non-crypto, non-gold 15 minute markets (Strategy Research V2, worker SPIKE1, research only)

Written 2026-11-03 BEFORE any win, loss, profit factor or result of any spike, reversal, continuation or control trade was computed.
What was looked at first, all outcome-free (`python -m scalper.spike1 counts`, quotes only; `load()` does not even select the `result`
column unless score asks): window counts, date ranges, median signal-candle spread, the number of spike windows and of would-be cheap
trades per series and third. **Disclosed:** those counts were seen before this file was written, including that a spike lands at an
extreme mid almost always (see "Structural fact"), and the trigger rate of about 5% to 9% of windows per series. No win rate, fill
quality after the fill candle, or PnL was computed. Code: `src/scalper/spike1.py`, tests `tests/test_spike1.py`. Nothing here means
trade, touches live code, `functions/`, L1 or OICORE, or has a promote verb.

**Plain statement.** The likeliest outcome is FALSIFIED. The cheap side of a thin 15 minute market loses on its own (EVENT1 baseline
PF 0.84 to 0.86, PUB20 P01 to P03 PF 0.77 to 0.90), a mid spike on a thin book is mostly the book moving and the underlying with it, and
the prior that a 15 minute binary overshoots and comes back inside 3 to 11 minutes is low. Prior of a survivor 3%.

## Duplicate check (what is the same, what is different)
`grep -n -i "SCALP2\|LADFADE\|GEN8\|GEN9\|IDEAS20\|PUB20\|overreaction\|spike" README.md workers/OICORE_SHAPE_INVENTORY.md`:
- **SCALP2** (PF 0.57), **GEN8/GEN9**: fade of a news or price overshoot on **gold and Bitcoin only** (L1 markets). SPIKE1 differs on market:
  **9 series that are neither crypto nor gold**, so it cannot hedge or overlap an L1 or OICORE position. Same idea, new markets.
- **LADFADE**: fade on the hourly **ladder** strikes. SPIKE1 is the 15 minute single contract, no ladder.
- **IDEAS20 volume-surge reversion** and **PUB20 rules 5/6**: volume surge and benchmark-fix windows; SPIKE1's trigger is a price (mid)
  move in sd units, not volume or clock time. PUB20 P01 to P03 and EVENT1 already price the unconditional cheap side of these same
  nine series: it loses. SPIKE1's control reuses that: it asks whether the spike adds anything over the same cheap side with no spike.
- **OICORE_SHAPE_INVENTORY**: Bitcoin open-interest shapes; not this.
- **NEW:** a mid-price spike trigger (3 sd within 2 minutes), cheap side against the move, paired with the same spike's continuation
  side and a same-series, same-hour, same-look no-spike control, on the nine non-crypto non-gold series. Not tried before.

## Reference price (said plainly)
The trigger uses **Kalshi's own contract**: the YES mid (bid_c + ask_c)/2 of the 1 minute candle. No outside spot is used. A keyless
reference exists (Yahoo's chart endpoint answers without a key, tested 2026-11-03 for EURUSD=X) but it serves **1 minute bars for the
last 8 days only** ("Only 8 days worth of 1m granularity data are allowed"), which are all inside the frozen W3, so it cannot score W1 or
W2 and is not used. A contract-implied spike mixes a real move of the underlying with a book move without one; SPIKE1 cannot tell them apart.

## Universe (chosen on metadata only)
Rule: a series is in when it has at least 400 windows with a usable trailing sd in W1+W2 and median signal-candle spread of 0.03 or less.
Counts (windows with sd, W1 / W2): EURUSD 0 / 431, GBPUSD 0 / 455, USDJPY 0 / 436, silver 2,089 / 1,900, copper 561 / 1,866,
WTI 2,054 / 1,972, natural gas 533 / 1,919, platinum 0 / 917, palladium 0 / 923; median spread 0.01 to 0.03 for all.
**In (9):** KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXSILVER15M, KXCOPPER15M, KXWTI15M, KXNATGAS15M, KXPLATINUM15M, KXPALLADIUM15M.
**Out:** KXAUDUSD15M and KXUSDCAD15M (their whole history, from 2026-10-07, is inside the frozen W3: 0 windows in W1+W2); Brent, the Treasury
series and the index series (not 15 minute markets with history); every crypto series and gold (L1, OICORE, banned areas).
Window thirds by close time (UTC), the same cuts as EVENT1 and PUB20: **W1 2026-08-06 to 09-04, W2 09-05 to 10-04, W3 (frozen holdout)
10-05 to the end of the data**, unread unless the screen passes. **Disclosed:** W1 holds only silver, WTI, copper (from 08-27) and gas
(from 08-27); the FX pairs, platinum and palladium start 09-18 to 09-23 and appear in W2 and W3 only. Per-series results are
information, not tries.

## Trigger (ONE definition, fixed)
For a 15 minute market with close time c and 1 minute candles ending at c-840 ... c:
- mid(e) = (bid_c + ask_c)/2 of the candle ending e, valid only if 0 < bid < ask < 1 and ask - bid <= 0.10.
- **sd** = RMS of the 1 minute mid changes (both candles valid) over the **four windows that closed at c-900, c-1800, c-2700, c-3600** of the
  SAME series (the previous 60 minutes; each window's settlement candle excluded), floored at 0.01; none if fewer than 40 changes.
  Looks only at earlier windows: no look-ahead.
- **Look times** (signal candle end): c-720, c-660, ..., c-240 (nine looks; the trade fills one candle later, c-660 ... c-180).
- delta = mid(look) - mid(look - 120). **Spike** iff |delta| / (sd x sqrt 2) >= 3 AND |delta| >= 0.05 (the 3 sd is for a 2 minute change under
  a random walk; the 5c minimum stops a quiet hour turning a 1c wiggle into an event).
- **Eligible trade:** the FIRST look in the window that is a spike AND has a cheap side: the side whose ask on the signal candle is 0.05 to
  0.30 (YES first on a tie, spread <= 0.10 already required), AND the next candle's ask for that side is at most 0.30 (hard limit; above
  it is no trade). One trade per window, fill at the NEXT candle's ask, held to settlement, C = 10, fee 7% x C x p x (1-p) rounded up
  (`gen6.fee`), no sell fee. Also reported at fee x1.2 and at +1c slippage (the candle ask is a last quote with no size, so a fill is not certain).

## Structural fact (found in the counts, before any outcome) and what it does to the design
A mid spike in a bounded binary lands at an extreme: in a tabulation of silver's first 1,500 windows (quotes only), all 85 down spikes ended at mids of 0.0 to 0.5 and
all 73 up spikes at 0.5 to 1.0, in the direction of the move. So the cheap side (ask <= 0.30) after a spike is **almost always the side AGAINST the
move** (NO after a spike up to >= 0.70, YES after a spike down to <= 0.30). The brief's "continuation cheap side" (the cheap side in the
spike's direction) needs a spike UP that still ends at a mid <= 0.30, which is a jump of 5c or more from a mid below 0.25; the counts
show **0 such trades in every series and every third**. So:
- **Try A (primary, REVERSAL):** the cheap side against the spike, as above.
- **Try B (CONTINUATION, separately counted):** the same triggers, the side IN the spike's direction (the favourite, ask roughly 0.70 to
  0.95), bought at the next candle's ask on the same candle as A, hard limit 0.97, fee as above, held. This is the only way the
  continuation can be priced, and is the other leg of the same window (A and B are opposite sides of one contract, so their net returns add
  to about minus the spread plus fees). It is NOT a cheap-side trade; the literal cheap-side continuation has n = 0 and is reported as such.
  Question it answers: **which side does the spike favour**, measured per window as (A net) minus (B net) in cents.
- **Control (not a try):** the cheap side (ask 0.05 to 0.30) at the same look and fill rule in windows of the same series where the same
  look has |z| < 2 (no spike), matched on (series, UTC hour of day, look, third); if that cell has fewer than 5 trades, the cell one hour
  either side; if still fewer, the trade is dropped from the difference. Reported: control PF, and A minus control per trade, day-clustered.

## Mechanism and counterparty
In a thin book a single sweep or a stale-then-repriced quote moves the mid far more than the underlying moved; the cheap side against it is
then priced off a book that the next candle partly undoes. **Counterparty:** momentum chasers who lifted the book, and stale makers who
repriced late. **Why it may not work:** the sweep may be the underlying (information), the opposite side is then the right price, and the
fee at 20c to 30c is 1.1c to 1.5c a contract on a 5c to 15c edge needed. This is a hypothesis about thin-book overshoot, nothing more.

## Numeric predictions (written before any outcome)
- Trigger rate: spike at some look in 5% to 9% of windows with a trailing sd (silver 8.4%, WTI 8.0%, FX about 5% to 6% were seen as counts);
  eligible Try A trades about 4% to 6% of windows: W1 about 290, W2 about 560 pooled, about 35 a day in the W3 months. Try A **n in W1+W2 >= 150: yes (about 850)**.
- Try A: win 14% to 20% (central 16%), fill 15c to 25c (central 20c), payoff 3.5 to 5, **PF 0.85 (0.50 to 1.30)**, mean net -1.5c to -3c.
- Try B: win 78% to 88%, **PF 0.97 (0.90 to 1.05)**, mean net -0.5c to -2c.
- Control PF 0.85 (0.70 to 1.00). A minus control +1c (-3c to +5c). **P(Try A PF >= 1.5 in both W1 and W2) 3%.**
- A minus B per window: negative, because the two legs sum to about minus (spread + fees) and a longshot rarely beats its price.

## Kill rules (fixed now)
- **NOT_ENOUGH_DATA:** Try A under 150 trades in W1+W2 pooled, or under 40 in either W1 or W2 (a half that cannot be scored cannot pass).
- **FALSIFIED:** Try A PF under 1.5 in W1 or in W2 (or in W3 if W3 is read) after fees; **or** (A minus B) not positive in both W1 and W2;
  **or** A minus control not positive in either half; **or** PF at fee x1.2 at or under 1.0. Try B is FALSIFIED on the same PF test.
  z (day-clustered mean net) under the deflated bar 5.27 (N about 728,755 plus this entry) is NOT_YET_FALSIFIED at best; no result can promote.
- **W3 (frozen last third, 10-05 on) is read ONLY if Try A passes W1 and W2 on every line above**, and then once.

## If positive in both halves with a mechanism (capped-probe SPEC only, not built)
1 contract, YES or NO as the trigger says, hard fill limit 0.30, held; one trade per window; at most 1 open trade at a time across the 9 series;
kill at 40 fills with PF under 1.2 or net under -$10; worst single loss at the 0.30 limit about $0.31 per contract; worst day (35 fills a day at
16% wins) about -$8 at 1 contract; 40 fills in about 1 to 2 days of W3 volume. No live code; the owner decides.

## Tries and N
Two tries (Try A reversal, Try B continuation), 2 each: **N +4** (the coordinator keeps the total; reference about 728,755, z bar about 5.27).
The control, the per-series tables, fee x1.2 and +1c slippage are information, not tries.
