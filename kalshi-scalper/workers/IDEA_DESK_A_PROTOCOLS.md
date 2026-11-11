# Idea Desk A: ready-to-run protocols for the top three (Nov 11, 2026)

Companion to `IDEA_DESK_A_NOV11.md` (same branch). Written BEFORE any outcome, price path or P&L of these tests was read. This desk writes cards and protocols only and calls no Kalshi endpoint; V2 or Refinement runs them (R&D roster, `docs/RND_CHARTER.md` section 9). The only data I opened to write this were file listings and the header row plus one sample row of the R6 book, tape and coverage files and of one hourly perps file, to get the column names right.

Shared conventions (the research branch's own): cash basis, 1 contract, taker fee 0.07 x p x (1-p) per contract unrounded unless stated, development then a held-out part read ONCE and only for a development survivor, verdict words FALSIFIED / NOT_YET_FALSIFIED / NOT_ENOUGH_DATA as defined in `docs/RND_CHARTER.md` section 4, deflation against the shared count (about 1,100,000, z about 5.34) and reported beside the lenient bar (N 8,795, z about 4.39). Every script refuses a second scored run. The tester must check `workers/DATA_INVENTORY.md`'s frozen-window key before loading any file.

Order to run them, cheapest first: P3 stage A and P4 (one pass over the same tape files, no outcome), P2 stage 0 and 1 (counts), P1 gate 0 (a docs read). Each of those can close its card in hours.

---

## P1. EXDIV1: ex-dividend mechanics on Kalshi single-stock perps

**Claim to falsify.** A short perp position opened before the prior cash close and covered after the ex-dividend cash open earns about the dividend, net of fees, spread and funding, because the perp is not adjusted for the dividend and does not trade at a discount beforehand.

**Gate 0 (docs only, about 1 hour, no data).** Read Kalshi's published contract terms and help pages for the equity perps. Three questions, each answered with the quoted text and its page: (a) is a dividend or other corporate action passed to holders, through funding, a cash adjustment or a reference-price adjustment; (b) is `reference_price` the raw last sale or an adjusted series; (c) is there any launch fee waiver on perps (a separate cost input, asked here only because the same pages answer it). If (a) says dividends are passed through: **CLOSED, 0 tries.** If the pages do not answer (a), go on; gate 1 answers it empirically.

**Calendar (keyed by hand, frozen before any perp row for those dates is read).** One CSV: `ticker, ex_date (New York date), amount_usd, prior_close_usd (left blank until scoring), source (the company's own press release title and date), keyed_on`. Universe: every Kalshi equity or ETF perp in `perp-data:perps/perps-<date>.csv` whose `asset_class` is Equities or Indices and which has an ex-date between 2026-11-06 and 2027-02-26. No automated calendar source is cleared; do not script one. An ex-date found after its own date has passed is still allowed in (the date is public knowledge in advance), but the file's commit time is recorded so a reader can see which rows were keyed late.

**Data.** `perp-data:perps30/<date>/close.csv.gz` and `open.csv.gz` (30 second samples, 15:40 to 17:00 and 09:10 to 10:30 New York, columns `ts_utc, ticker, bid, ask, bid_size, ask_size, price, reference_price, settlement_mark, open_interest, funding_cap, funding_deadband, halt_sources, is_open`), `perp-data:funding/<date>.csv.gz` (funding history), `perp-data:perps/` hourly as a fallback. The saved Yahoo cash bars (`cash1m/`) stop on Nov 11 and are NOT needed: `reference_price` is the cash leg.

**Gate 1 (descriptive, no P&L, run as soon as 8 events exist, about Dec 1).** For each event, with t0 = the last sample at or before 15:59:30 New York on the session before the ex-date and t1 = the first sample at or after 10:00:00 on the ex-date:
- `ref_drop = reference_price(t1) / reference_price(t0) - 1` (should be about minus the yield plus the market's overnight move);
- `prem(t) = (bid(t) + ask(t)) / 2 / reference_price(t) - 1` at t0 minus 2 sessions, t0, and t1;
- classify each event: PRE-PRICED (prem(t0) at or below minus half the yield), UNADJUSTED-UNPRICED (prem(t0) within plus or minus a quarter of the yield and the perp mid falls with the reference), ADJUSTED (the reference does not drop by the dividend relative to the non-ex names).
Kill: if 6 of the first 8 events are PRE-PRICED or ADJUSTED, **CLOSED** before any trade is scored (1 try counted).

**Gate 2 (the scored test, registered now).** Two variants, 2 tries:
- **U (unhedged):** events with `amount / prior_close` at or above 0.5%. Sell the stock perp at `bid(t0)`, buy back at `ask(t1)`. P&L per $1 notional = `bid(t0)/ask(t1) - 1` minus 2 x 0.12% fee, plus or minus the funding rows between t0 and t1 with the correct sign for a short.
- **H (index-hedged, paired inside the strategy's own position):** events at or above 0.8%. Same short, plus a long of equal notional in `KXUS500PERP` bought at its ask at t0 and sold at its bid at t1; 4 crossings, 0.48% fee.
- Skip an event if either sample is missing, `is_open` is false at t0 or t1, a halt source is listed, or the stock's ask size at t1 or bid size at t0 is zero. Count the skips.
- Placebo, reported beside each variant and never a rescue: the same rule on the same tickers 5 sessions earlier, and on all non-ex names on the event's own dates.

**Cuts.** Development = ex-dates Nov 6 to Dec 31, 2026. Held-out = Jan 1 to Feb 26, 2027, read once, only if development survives. Unit of clustering = the ex-date (several names can share one).

**Bars.** Development survivor: at least 20 events on at least 12 distinct dates, cash PF 1.5 or better, mean net above +0.20% of notional, and the placebo mean within one standard error of zero. NOT_ENOUGH_DATA below 20 events. FALSIFIED if PF is under 1.0 at 20 or more events. Held-out: PF 1.5 or better on at least 15 events. The date-clustered z is reported against both deflation bars; with about 45 events it cannot reach 5.34, so the best honest outcome here is "a LEAD with a mechanism", and the write-up must say that.

**What would make the result a lie.** (1) Keying the calendar after looking at premium paths: the calendar commit must precede the first data read. (2) Using the perp `price` (last trade) instead of bid and ask. (3) Dropping losing events as "data problems": the skip rules above are the only ones. (4) Earnings on the same night: flag any event whose company reports between t0 and t1 and report the result with and without them, as registered here.

**Live note.** No code trades perps. Anything live is a new product, an owner popup and a build; this protocol produces evidence only.

---

## P2. TIECOND1: conditional tie premium on the non-crypto 15 minute markets

**Claim to falsify.** In pre-identifiable quiet or frozen windows the chance that the settle print equals the strike is high enough that buying YES at the open beats its price after the fee.

**Stage 0 (validation, counts only).** For every non-crypto 15 minute series in the held market tables (`alts2`, `alts3`, `fxusd/candles`, `rep`, `fresh`; fields `ticker, close, result, strike`), order windows by close time and, for each pair of consecutive windows with no gap, compute `d = strike(t+1) - strike(t)`. Check: `result(t) == 'yes'` if and only if `d >= 0`. Report the agreement rate per series. If agreement is under 99.5% for a series, drop that series (the next strike is not its settle print) and say so. This stage also gives every later study the exact settle value, which RULES1 said was not computable.

**Stage 1 (census, counts only, the kill gate).**
- `tie(t) = (d == 0)`. `tick(series)` = the smallest positive |d| seen in that series' first 500 windows.
- Predictors known at the open of window t (nothing from window t itself): `q8` = median |d| in ticks over the previous 8 contiguous windows; `ties4` = number of ties in the previous 4 windows; `hour` = UTC hour of the open; `first_after_gap` = no window in the previous 30 minutes.
- Table: tie rate with a Wilson interval by series group (FX, metals, energy, rates) x `q8` tercile (cut points from the first third of each series' dates only) and separately by `ties4` (0, 1, 2 or more, 4).
- **Kill:** if no cell with at least 300 windows has a tie rate whose lower interval bound is 6% or more, **CLOSED** (1 try). Report the best cell either way.
- Also report, as a fact for the Chief of Staff, how many windows exist at all during the daily break, weekends and the US holidays in the sample (Labor Day Sep 7, Columbus Day Oct 12). Zero means arm B has nothing to test.

**Stage 2 (scored, only if stage 1 survives; cells fixed by stage 1 before any quote is read).** For each surviving cell: at the first 1 minute candle of the window, if YES ask is at or below 0.55 and (YES ask minus YES bid) is at or below 0.04, buy 1 YES at the ask, hold to settlement. Fee as above. Report cash PF, mean per trade, tie share of the wins, and the same rule's result with ties removed (it should then be about minus the fee and spread; if it is not, the edge is something else and the write-up must say so). Mirror control: buy NO under the same conditions.
- Tries counted: one per surviving cell, at most 4, plus the stage 1 kill try.
- Cuts: the inventory's frozen key applies. Rows closing on or after 2026-10-05 are the frozen third (F1) for these files, so development is everything before it (FX has only Sep 23 to Oct 4, about 1,150 windows a pair) and the held-out read is the frozen third, once, for a survivor only.
- Bars: n at least 100 in development, cash PF 1.5 or better, date-clustered z reported against both bars; held-out PF 1.5 or better at n 60 or more.

**Arm B (forward, dated).** Thursday Nov 26, 2026 (CME halts early for Thanksgiving), then Dec 24 to 25 and Jan 1. From the NC15 recorder (`nc-data:nc15/`, once merged; silver, copper, oil, natural gas and the FX pairs): for each window that opens while the source is closed, record whether it was listed, its first YES ask and its result. Three holidays cannot make n 100; arm B is an existence check that either finds windows trading under 97c that settle YES every time, or closes itself. Halt times are keyed by hand from the exchange's published holiday hours.

**Maker variant, not scored here.** A resting YES bid pays no fee on these series, so the break-even tie mass is much lower, but a fill model needs the NC15 tape. If stage 1 survives and stage 2 fails only on the fee, register a maker version on NC15 as a separate card.

**What would make the result a lie.** (1) Using window t's own move in a predictor. (2) Cut points for the terciles taken from the whole sample. (3) Reading the frozen third to choose cells. (4) The rule-text conflict (primary "at least", FX secondary "strictly greater"): if stage 0 shows ties settling NO anywhere, stop and flag it; do not flip the side quietly.

---

## P3. RETAILFRAC1: app retail versus API flow from fractional trade sizes

**Claim to falsify.** When dollar-typed (fractional size) taker flow and whole-number taker flow point opposite ways in a 15 minute window, the whole-number side wins more often than its price says.

**Data.** `quote-data:book15r6/<date>/<HHMM>/trades.csv.gz` (`ticker, created_time` to the microsecond, `yes_price_dollars, count_fp, taker_outcome_side`), `book.csv.gz` (`t_recv_ms, ticker, series, close_time, yes_bid_px_1..5, yes_bid_sz_1..5, no_bid_px_1..5, no_bid_sz_1..5`; the YES ask is `1 - no_bid_px_1`, the NO ask is `1 - yes_bid_px_1`), `coverage.csv.gz` (`close_time, series, ticker, polls, ok_polls, max_gap_ms, tape_trades, volume_fp, result, note`). Five series Oct 29 to Nov 13, Bitcoin and Ethereum to Nov 20. Use only windows whose coverage row has a result, `tape_sum_count` within 1% of `volume_fp`, and `max_gap_ms` under 10,000.

**Definitions.** `frac(trade)` = `count_fp` differs from its nearest integer by more than 0.001. Signed size in YES direction: `+count_fp` if `taker_outcome_side == 'yes'`, else `-count_fp`. T = `close_time`.

**Stage A (map, no outcome column is loaded; 2 hours).** Per series and overall:
1. share of trades and of contracts that are fractional;
2. median and 90th percentile size of each class;
3. the fractional share of contracts by minutes to close (15 one-minute buckets) and by UTC 4 hour block;
4. the YES share of each class's contracts, and the mean price paid for the side bought, by class;
5. the per-window correlation between net fractional flow and net whole flow over (T-600 s, T-360 s].
**Kill:** CLOSED (1 try) if the fractional share of contracts is under 2% or over 98% in every series, or if item 5 is above +0.8 in every series (the two classes are the same crowd). Stage A's tables are worth committing even if the card closes: they tell every maker card where the dollar-typed flow is.
Thresholds for stage B come from stage A and are fixed before stage B loads a result: `f_min` and `w_min` = the development median of |net fractional flow| and of |net whole flow| over (T-600 s, T-360 s], per series.

**Stage B (scored once).**
- Signal at T-360 s: `F` = net fractional flow and `W` = net whole flow over (T-600 s, T-360 s]. Fire when `|F| >= f_min`, `|W| >= w_min` and `sign(F) != sign(W)`.
- Side = `sign(W)` (YES if positive). Entry at the first book snapshot at or after T-300 s (one minute later, the bot's real cadence), at that side's ask, only if the ask is between 0.10 and 0.85 and the size resting at that ask is at least 1. Hold to settlement. 1 contract, fee as above.
- One try: the pooled five-series result. Per-series lines, the mirror (side = `sign(F)`), and the "agree" windows (same thresholds, signs equal, side = `sign(W)`) are descriptive and cannot rescue the pooled line.
- Cuts: development = windows closing before 2026-11-08 00:00 UTC; held-out = Nov 8 to the end of the recorder, read once for a survivor.
- Bars: development n at least 150 on at least 8 dates, cash PF 1.5 or better, mean above +1.5c, date-clustered z against both bars; held-out PF 1.5 or better at n 100 or more. FALSIFIED if development PF is under 1.0 at n 150 or more.
- Correlation note for the Verification Analyst: Bitcoin windows overlap OICORE's market, so report the share of fired windows in which OICORE's own trigger also fired (from the nightly report's rows), as information.

**Family budget, stated plainly.** FLOW1 and TAPEFLOW1 are FALSIFIED. If the Chief of Staff counts this card in the same family, a FALSIFIED here closes order-flow rules for good under the charter. That is a reason to run stage A first and to spend stage B only if stage A shows two clearly different crowds.

**What would make the result a lie.** (1) Choosing `f_min`, `w_min`, the flow span or the entry band after seeing stage B. (2) Entering at T-360 s (the signal's own second) instead of a minute later. (3) Treating "whole number" as "API": it is only "not dollar-typed", and the write-up must use that wording. (4) Joined-late windows (coverage `note`) have a complete tape but a short book; keep them for stage A and drop them from stage B unless a snapshot exists at T-300 s.

---

## P4. CRONCLUSTER1 stage A (rides on P3's files; a measurement, no outcome, no try counted)

1. From the same tape: contracts taken by second of the minute (0 to 59), per series and per minutes-to-close bucket. `peak = (contracts in seconds 0 to 9) / (total x 10/60)`. Interval by resampling whole windows.
2. From the book: for every minute boundary inside a window, the size resting at each side's best ask and the spread at the last snapshot in seconds 52 to 59, against the first snapshot in seconds 8 to 15.
3. Report `peak` and the before-and-after depth ratio for gold at 6 to 7 minutes to close (where L1 buys) and for Bitcoin at 2 to 3 minutes (where OICORE buys), next to the all-window figures.
**Reading it:** `peak` at or above 1.3 with an interval clear of 1, AND touch depth lower after the boundary than before it, is a finding worth handing to Refinement as a candidate version of each strategy's send time (tested beside the parent on fill rate and net dollars, lifecycle 7g). Anything less: "no cluster", closed, and say so.
