# NEWH9 registration (Strategy Research V2 worker NEWH9, 2026-10-30, research only)

Written and pushed BEFORE any NEWH9 rule was joined to a fill quote after its signal or to any outcome. Code `src/scalper/newh9.py`
(committed with this file); result `workers/NEWH9_RESULT.md`. Markets: KXGOLD15M, KXBTC15M and their hourly ladders KXBTCD and KXGOLDH.
Times in this file are UTC for the code and US Central (CDT, UTC-5, the whole sample) in words.

## Scope and what is NOT here

- No rule buys the 88c to 97c favourite and holds (L1); no L1 exit, size, filter, hour or throttle test.
- No "cheap side late" trade (buying a 5c to 50c side in the last minutes, with or without open interest).
- Every single-leg rule here enters in the FIRST two minutes of a 15 minute window at a price between 30c and 70c.

## What was looked at before this was written (disclosure)

1. Ledger: `workers/RULES.md`, `workers/DIRECTOR_2026-10-30.md`, `workers/NEWH8_REGISTRATION.md`, `NEWH8_RESULT.md`,
   `src/scalper/newh8.py` (loader reused), README headings and these sections: ARB1 and its result, the 2026-10-26 ladder arbitrage
   snapshot (information, 0 locks in 4,064 pairs, never a try), KX10, XM1, CONF2, CORR1, QUIRK1 and its result, SIDE1/HOUR1/XLEAD1,
   FIX1 (one paragraph), EVT1 result, NEWH2 GLADH and NEWH3 BLADX (registrations), GEN9 registration header.
2. Data inventory only: which sqlite files hold which series, close ranges, which candle offsets exist, how the ladder strikes in each
   file were chosen (CORR1's rule for `lad2.sqlite` and `conf2_lad.sqlite`: strikes with YES mid 1c to 99c 55 to 52 minutes before
   the close; NEWH2's rule for `newh2_goldh.sqlite`: strikes within $12 of the 15 minute strike fixed 15 minutes before the close).
3. `python -m scalper.newh9 counts` (window and event counts per stage, and windows kept by the clock rules; no quote after a signal
   and no result read):
   - KXBTC15M windows disc / val / hold: 4,357 / 2,560 / 1,136; KXGOLD15M 3,192 / 1,818 / 809.
   - KXBTCD events (conf2_lad first, then lad2): 656 / 631 / 257; KXGOLDH events: 444 / 429 / 153.
   - Windows kept by clock: ASIAGOLD 807 / 512 / 230; NYGOLD 620 / 400 / 180; BTC10AM 124 / 80 / 36.
4. Checked and dropped before writing (no try spent): KXGOLDD against KXGOLDH identical-contract locks (KXGOLDH has no 21:00 UTC close
   and the strike grids differ, x.99 against whole dollars: NOT_RUNNABLE); gold 15 minute against the daily ladder at 21:00 UTC (GLADH
   at another clock, and only 38 daily closes with a few near-money strikes: a variant and too thin); gold LADLEAN (the gold hourly file
   holds only the last 15 minutes of each hour, so the only possible pairing is the coincident close, GLADH).

## Common to every rule (fixed now)

- **Windows by close time (UTC):** DISCOVERY 2026-08-06 00:00 to 2026-09-21 00:00; VALIDATION 2026-09-21 00:00 to 2026-10-18 00:00;
  HOLDOUT 2026-10-18 00:00 to 2026-10-30 00:00 (frozen: read once, ONLY for a rule that passed discovery and validation, after the
  discovery and validation result is committed and pushed; otherwise it stays unread).
- **Universe:** every settled market in the files, chosen by close time only (15 minute: `l1b`, `book`, `fresh`, plus `five` for gold,
  first file wins per close; KXBTCD: `conf2_lad`, then `lad2`, first file wins per close; KXGOLDH: `newh2_goldh`). The ladder strike
  sets were chosen by their fetch rules before any entry time used here (point 2 above).
- **Fill:** at the closing ask of the NEXT 1 minute candle after the signal candle, never at the signal's own quote. Held to settlement;
  no rule sells, so no bid is used for an exit.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, per leg. Headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose signal or fill candle (any leg) had volume 0.
- **One trade per window (or ladder event) per rule.** Day-clustered z reported per window and pooled.
- **Bar (each rule):** PF at C = 10 at least 1.5 in EACH of the three windows, net positive at fees x1.2 in each, at least 100 / 50 /
  30 trades (discovery / validation / holdout), a named counterparty, and pooled day-clustered z at least the deflated bar.
  **N:** running count after GEN8 about 627,838, plus 7 here = **about 627,845** (GEN9's count lands separately); the one-sided
  Bonferroni z bar at 0.05 is **5.24** (5.25 if GEN9 adds about 12,000).

## H1 LADLOCK, Bitcoin KXBTCD and gold KXGOLDH (2 tries): adjacent-strike monotonicity lock, after fees

- **Rule:** for each hourly event, scan the 1 minute candles in time order up to 120 s before the close. For adjacent strikes K1 < K2
  (adjacent in the event's stored strike list), both quoted at the candle: YES(K1) ask a1 = `ask_c(K1)`, NO(K2) ask a2 = 1 - `bid_c(K2)`,
  both strictly inside (0, 1). Signal when lock = 1 - a1 - a2 - (fee(a1) + fee(a2)) / 10 is at least 1c per contract (C = 10 fees).
  The FIRST signal of the event is the event's only trade: buy YES(K1) and NO(K2) at the next candle's asks (whatever they are; a
  missing leg there is "no fill", counted). Payoff per set = [K1 settles yes] + [K2 settles no], which is at least 1 because "above K2"
  implies "above K1"; it is 2 when the price settles between them.
- **Counterparty:** a quoter (or resting order) that marks one strike of a ladder without reference to its neighbours, so that YES at
  the lower strike is offered below YES at the higher strike; whoever left that stale order pays the lock.
- **Honest alternative:** ladder makers do this arithmetic continuously; the 2026-10-26 snapshot (information) found 0 locks after fees
  in 4,064 pairs; minute candles mix quotes from slightly different instants, so an apparent lock may be a timing artefact that is gone
  at the next candle.
- **Prediction:** NOT_ENOUGH_DATA on both (under 100 discovery events with a signal); any trades that happen have fills at the next
  candle that no longer lock, PF near 1. Kill as below.

## H2 LADLEAN, Bitcoin (1 try): the hourly ladder's lean at the 15 minute window's open

- **Rule:** KXBTC15M windows closing at :30 and :45 past the hour (they open at :15 and :30, inside an hourly ladder event that closes
  at the next top of the hour, 45 or 30 minutes after the signal). Signal candle: the one ending 840 s before the 15 minute close (the
  window's first minute). The 15 minute strike K15 (the market's stored strike, fixed at its open) is bracketed by the adjacent quoted
  ladder strikes K_lo <= K15 < K_hi at that same candle (each with 0 <= bid < ask <= 1; K_hi - K_lo at most $200); p = linear
  interpolation in strike of their YES mids = the ladder's probability that the hour settles above K15. Lean YES if p >= 0.55, NO if
  p <= 0.45, else no trade (counted "flat"). Fill: the leaned side's ask on the 15 minute candle ending 780 s before the close, only if
  it is in [0.30, 0.70] (else counted "band"). Missing candle, strike or bracket: gap (counted).
- **Counterparty:** the 15 minute book's opening quoters, who open each window close to 50/50 around a strike equal to the current
  price, while the deeper hourly ladder's makers already price a drift or skew across the same strike (under a skewed or drifting
  distribution the at-the-money binary is not worth 50c).
- **Honest alternative:** the ladder's p at the current price is mostly interpolation noise ($100 strikes, 1c spreads) and its own
  quoting error (LAD1, KINK); at 15 of 30 to 45 minutes the drift share is a half to a third of the ladder's lean; QUIRK1 found every
  side at every first candle loses the fee plus the spread. Related tests (XM1, BLADX, LOCK2H, CONF2) all used the coincident close;
  this one never does.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.05 at C = 10, win rate within 2 points of the price paid.
- **Information look I1 (counted, never screened):** mean ladder p, mean 15 minute YES mid at the signal candle and the YES outcome rate
  for YES leans and NO leans, discovery and validation.

## H3 ASIAGOLD, gold (1 try): buy gold UP at the open during the Shanghai day session

- **Rule:** KXGOLD15M windows that OPEN from 01:00 to 07:15 UTC (8:00 PM to 2:15 AM Central), Beijing date Monday to Friday (the
  Shanghai Gold Exchange day session, 09:00 to 15:30 Beijing). Buy YES at the ask of the candle ending 780 s before the close if it is
  in [0.35, 0.65] (the candle ending 840 s must exist). Held.
- **Counterparty:** 15 minute quoters who open gold symmetric around the strike while physical and exchange demand in the Shanghai
  session lifts gold (the documented "gold rises in Asian hours, falls in New York hours" intraday pattern).
- **Honest alternative:** whatever drift there is per 15 minutes is a few hundredths of a standard deviation, under the 2c to 3c a
  contract that the fee and spread cost at 50c; QUIRK1's pooled gold first-candle cells lost on both sides.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.05.

## H4 NYGOLD, gold (1 try): buy gold DOWN at the open during the COMEX day session

- **Rule:** KXGOLD15M windows that OPEN from 12:30 to 17:15 UTC (7:30 AM to 12:15 PM Central; COMEX day session 08:20 to 13:30 ET),
  UTC Monday to Friday, not 2026-09-07 (Labor Day). Buy NO at the ask of the candle ending 780 s before the close if it is in
  [0.35, 0.65]. Held.
- **Counterparty:** the same opening quoters; the other half of the session pattern (New York hours sell gold).
- **Honest alternative:** as H3. **Prediction:** FALSIFIED; discovery PF 0.85 to 1.05.

## H5 BTC10AM, Bitcoin (1 try): buy Bitcoin DOWN at the open around the US cash open

- **Rule:** KXBTC15M windows that OPEN at 13:30, 13:45, 14:00 and 14:15 UTC (8:30 to 9:15 AM Central, 9:30 to 10:15 AM ET), UTC
  Monday to Friday, not 2026-09-07. Buy NO at the ask of the candle ending 780 s before the close if it is in [0.35, 0.65]. Held.
- **Counterparty:** the 15 minute opening quoters, against a repeated seller at the US cash open (the widely reported "10 AM ET
  Bitcoin dump", attributed in public reports to a large trading firm selling or hedging at the open).
- **Honest alternative:** a pattern that was public in 2025 is either gone or priced; 4 windows a day gives about 120 discovery trades
  and a holdout under 40.
- **Prediction:** FALSIFIED (discovery PF 0.8 to 1.2) or NOT_ENOUGH_DATA in the holdout if it got that far.

## Kill criteria (each try, no parameter changes after any score)

- Discovery: fewer than 100 trades: NOT_ENOUGH_DATA (validation printed for the record). PF at C = 10 under 1.5, or net at fees x1.2
  at or below 0: FALSIFIED.
- Validation (after a discovery pass): fewer than 50 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
- Holdout (after both passes, read once): fewer than 30 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
  All three PF gates met but pooled day z under the deflated bar: NOT_ENOUGH_DATA (a forward read could only ever add data).
  All gates met: NOT_YET_FALSIFIED, a forward registration only.

## Count

N tried: **6** (LADLOCK btc, LADLOCK gold, LADLEAN btc, ASIAGOLD, NYGOLD, BTC10AM) + 1 information look (I1) = **7**.
Running count about 627,838 (after GEN8) + 7 = **about 627,845**, plus GEN9's own count when it lands.
