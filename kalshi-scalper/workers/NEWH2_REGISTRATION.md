# NEWH2 registration (V2 worker NEWH2, 2026-10-30, research only; written and pushed before any outcome is read)

Four new mechanisms, three on gold's 15 minute market (KXGOLD15M) and one on gold's 15 minute market against Kalshi's hourly gold
ladder (KXGOLDH). Two more ideas from the brief are declined below (one is a reworded tested idea, two fall under the owner's
2026-10-28 instruction). Nothing here touches L1 or anything live.

**Looked at before writing (no outcome, no price at an entry time):** the README headings, NEWH1, EVT1, LATECAL, BTCAVG, LOCK2H,
the settlement mechanics study; the COUNT of gold windows per UTC close time in each local file (to size the universes); that
KXGOLDH exists (listed since 2026-07-07, Pyth gold, strikes $2 apart, strike type `greater`). No quote, mid, result or trade of any
window in the universes below was read.

## Common to all four

- **Windows by close time (UTC):** DISCOVERY 2026-08-06 to 2026-09-20 (close < 2026-09-21 00:00Z); VALIDATION 2026-09-21 to
  2026-10-27 (close < 2026-10-28 00:00Z). Nothing closing on or after 2026-10-28 is read. The third window is the FORWARD record: a
  validation survivor goes to `workers/candidates/` with a freeze time after its commit and is read only by the forward ledger.
- **Data:** 15 minute candles from `l1b`, `book`, `fresh`, `five` (`scalper.gen7.load_windows` order, first file wins), silver from
  `alts3`; KXGOLDH candles fetched by `scalper.newh2 fetch` into `data/newh2_goldh.sqlite` (strikes kept: those within $12 of the
  15 minute window's strike, which is fixed at the window's open, 15 minutes before the close and 9 minutes before the entry look).
- **Fill:** at the closing ask of the NEXT candle (the one ending 60 s after the signal candle) for the side bought; held to
  settlement; one decision of one contract per window at most. A missing signal or fill candle is a data gap, counted, never a trade.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order. Headline PF at C = 10; C = 1 reported; fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF reported with all trades and with trades whose fill candle had volume 0 removed.
- **Screen (the brief):** DISCOVERY PF >= 1.5 at C = 10 on >= 100 trades and net > 0 at fees x1.2; then VALIDATION PF >= 1.3 on
  >= 50 trades and net > 0 at fees x1.2. Fewer trades than the minimum in either window is NOT_ENOUGH_DATA, never a pass.
  Day-clustered z reported; the deflated bar for N about 592,000 is z about 5.2 (RULES.md), so even a screen survivor earns only a
  forward ledger entry.
- **Verdict words:** FALSIFIED (enough trades, misses the bar), NOT_ENOUGH_DATA, NOT_YET_FALSIFIED (passes both screens; goes to the
  forward ledger only), NOT_RUNNABLE.
- **Daylight time:** every date in both windows is US daylight time (it ends 2026-11-01), so the CME times below are fixed in UTC.

## H1 GBREAK: the CME daily break (Pyth on its thinnest feed)

- **Universe (time only):** KXGOLD15M windows closing at 21:15, 21:30, 21:45 or 22:00 UTC, Monday to Friday. COMEX gold (GC on
  Globex) halts 16:00 to 17:00 CT = 21:00 to 22:00 UTC every weekday (Friday's is the weekend close), so these four windows lie
  entirely in the break.
- **Rule:** at the candle ending 360 s before the close, the side whose ask is in [0.55, 0.88] (YES tried first). Fill next candle,
  ask in [0.50, 0.92], else no trade.
- **Counterparty:** buyers of the cheap side and makers who keep pricing a regular-hours range while the gold reference is fed only by
  OTC publishers and barely moves; the cheap side is overpriced, so the side leading at 6 minutes wins more often than its price.
- **Prediction:** win rate at least 6 points above the mean fill; discovery PF about 1.5. Expected n is small (about 4 windows a day on
  the days Kalshi listed them): NOT_ENOUGH_DATA is the likely verdict and is stated now.
- **Kill:** discovery PF < 1.5 on >= 100 trades, or validation PF < 1.3 on >= 50, or net <= 0 at fees x1.2: FALSIFIED.

## H2 GREOPEN: the first 90 minutes after the COMEX reopen

- **Universe (time only):** KXGOLD15M windows closing at 22:15, 22:30, 22:45, 23:00, 23:15 or 23:30 UTC, Sunday to Thursday (Globex
  reopens 17:00 CT = 22:00 UTC those evenings).
- **Rule:** at the candle ending 480 s before the close, the side whose ask is in [0.08, 0.45] (YES first). Fill next candle, ask in
  [0.05, 0.50], else no trade.
- **Counterparty:** makers who carry the break's calm into the first hour of futures trading and quote too narrow a range; the futures'
  first hour moves the reference more than the quotes allow, so the cheap side is underpriced.
- **Prediction:** win rate at least 5 points above the mean fill; discovery PF about 1.5.
- **Kill:** as H1.
- **Control (information, not screened, not counted):** the same side rule on every other gold window of the same split.

## H3 GSILV: Kalshi's silver 15 minute market as information for gold's

- **Universe:** KXGOLD15M windows with a KXSILVER15M market closing at the same time in `alts3` (silver data ends 2026-10-23, so the
  validation window is Sep 21 to Oct 23 for this one; stated before any look).
- **Rule:** at the candle ending 360 s before the close (t), dS = silver mid(t) - silver mid(t - 180), dG = gold mid(t) - gold
  mid(t - 180) (mid = (bid + ask) / 2 of the closing quotes; all four candles must exist). If |dS| >= 0.20 and sign(dS) x dG <= 0.05
  (gold has not followed), buy gold YES if dS > 0, NO if dS < 0. Fill next candle, ask in [0.25, 0.80], else no trade.
- **Counterparty:** gold's quoters who reprice from the gold reference alone; silver is the higher-beta metal and its crowd moves first
  on a shared metals move, so gold's quote is late. Honest alternative: a silver-only move (gold correctly unmoved), in which case
  this loses.
- **Prediction:** win rate at least 6 points above the mean fill; discovery PF about 1.5.
- **Kill:** as H1.

## H4 GLADH: the 15 minute gold market against the hourly gold ladder at a coincident close

- **Universe:** KXGOLD15M windows closing at the top of an hour (close mod 3600 = 0) with a KXGOLDH event closing at the same
  instant (both settle on Pyth gold at that instant; 15 minute: at or above the strike; hourly: above).
- **Rule:** at the candle ending 360 s before the close, take the hourly ladder strikes with both a bid and an ask in that candle; the
  nearest K_lo <= K15 < K_hi with K_hi - K_lo <= $6; ladder P = linear interpolation in strike of the two YES mids. 15 minute YES ask
  a_y, NO ask a_n = 1 - YES bid. If P - a_y >= 0.06 buy YES; else if (1 - P) - a_n >= 0.06 buy NO. Fill next candle, ask in
  [0.05, 0.95], else no trade.
- **Counterparty:** the thinner 15 minute book when it is out of line with the hourly ladder, which has many strikes and makers pricing
  the same instant. Honest alternative: the same bots quote both and a gap is a stale ladder quote, which this pays for.
- **Prediction:** win rate at least 4 points above the mean fill; discovery PF about 1.5. Not a lock test (LOCK2H tested locks on
  Bitcoin); this is a one-sided bet on the 15 minute book only.
- **Kill:** as H1.

## Declined (not tried, not counted)

- **Bitcoin "settlement average already locked" at 90 to 60 s:** at 90 to 60 s before the close none of the 60 s average is fixed (it
  starts at 60 s), so the premise needs sub-minute quotes inside the last minute; minute candles have no point inside it, and the
  quote recorder starts 2026-10-22, outside both windows. That version is BTCAVG (D15 / D30 / D45, the locked fraction of the
  average) and LATECAL (ask bands at 120 to 10 s); LATECAL priced bands of the ask, BTCAVG the locked part of the average, which is
  what this idea is. Reworded tested idea: NOT_RUNNABLE here, no try spent.
- **Gold's favourite at its first touch of 88c to 97c** and **the next window's favourite after an L1-type favourite lost:** both are
  buy-the-favourite-and-hold entries in L1's band (an entry-timing variant and a filter), which the owner's 2026-10-28 instruction
  closes. The second is also close to NEWH1 FLIPREV. Not tried.

## Count

**N added: 4** (H1, H2, H3, H4, one rule each, no variants; H2's control reported only). Running count about 591,979 (after NEWH1)
plus other workers' additions, plus 4.

Code: `src/scalper/newh2.py` (`fetch` for KXGOLDH, `run` scores both windows once). Result: `workers/NEWH2_RESULT.md`.
