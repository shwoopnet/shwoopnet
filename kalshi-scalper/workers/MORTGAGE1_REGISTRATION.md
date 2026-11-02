# MORTGAGE1 registration (Strategy Research V2, written 2026-11-02 BEFORE any Kalshi candle was downloaded, any PMMS or Treasury value was joined to a market, or any result was read; research only)

Owner direction relayed by the main session: test new non-L1, non-OICORE families in parallel on existing public data; no further approval needed. Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
`grep -i "mortgage|PMMS|FRM|KX30Y"` over README.md found only `KX30YRRATE15M` (the 30 year TREASURY yield 15 minute market, an L1 style series), no mortgage-rate market and no PMMS. Not a duplicate. ECONNEW1 and ECONNEW2 are other economic series; this is a new series and a new information source (daily Treasury yield into the PMMS release).

## What was looked at before this registration (disclosure, metadata only)
The public series list and market LISTINGS for the mortgage series (tickers, event dates, strike counts, rules text). Printed: counts and the first and last event tickers. No `result`, `expiration_value`, price or candle was printed or joined. A probe showed `FRM` and `KXFRM` have no settled markets (KXFRM is Affirm's quarterly KPI market, not mortgage rates, and is excluded), `KXFM30YMTG` and `KXMORTGAGERATE` are year-end or year-long single events (one settled event, 5 to 7 strikes; not weekly), and **`KX30YMORTW` (30-year mortgage rate this week) is the weekly PMMS series: 190 settled markets on 10 weekly events (2026-08-27 to 2026-10-29, about 19 strikes each) plus one open event (2026-11-05).**

## Counterparty and mechanism
Who loses: retail traders on the weekly mortgage ladder who price off last Thursday's PMMS number and do not nowcast the move from the daily 10 year Treasury yield, to which the PMMS (a survey of lender quotes Monday to Wednesday) is tightly linked. Honest prior: the market at the look can see the same yields, and makers re-quote on them; prior of a pass under 3%.

## Data
- Settlement: Freddie Mac PMMS 30 year fixed average, FRED `MORTGAGE30US` (weekly, Thursday, two decimals), keyless CSV. Information: FRED `DGS10` (daily 10 year constant maturity, keyless CSV) as the Treasury daily yield curve; the Treasury site CSV is the fallback if FRED is unreachable.
- Kalshi: public `/markets?series_ticker=KX30YMORTW` listings and hourly candles (historical endpoint field names `yes_bid.close` / `yes_ask.close`; live `close_dollars`; read through `candlefield.py`/`econnew1.pick`, the fixed parser).

## Universe (cost and metadata only, never outcomes)
Series `KX30YMORTW` only. Event = one weekly settlement (the PMMS release of a Thursday; markets close 15:59Z, just before the noon ET release). All strikes of an event are candidates; a strike enters the scored universe only if, at the look, there is a valid two-sided quote (0 < bid < ask < 1, at most 6 hours old) with spread at most 10c. Left out on purpose: KXFRM (Affirm), FRM/FRMMIN/FRMMAX/KXFRMMIN/KXFRMMAX (no settled markets), KXMORTGAGERATE and KXFM30YMTG (annual, one event).

## Model (all fixed now)
Weekly change in PMMS: `PMMS(w) - PMMS(w-1) = a + b x (DGS10(Wed w) - DGS10(Wed w-1)) + e`, where DGS10(Wed) is the last published value dated on or before that Wednesday. Coefficients `a`, `b` and the residual standard deviation are fitted by least squares ONLY on PMMS weeks strictly before the event week (expanding window from 2010-01-07, at least 150 weeks), refitted each week. Nowcast centre `c = PMMS(w-1) + a + b dY`. Fair `P(PMMS(w) > K) = 1 - Phi((K + 0.005 - c) / sd)` (a two-decimal print is above K if it is at least K + 0.01). Information used is only what exists before the look: last Thursday's PMMS and the 10 year yield through Wednesday. A persistence-only model (`b = 0`) is computed beside it as information only.

## Look, entry rule, fees
- Look: the last hourly candle ending at or before Thursday 12:00 UTC (08:00 Eastern) of the event week, no later than 6 hours old.
- Try A: buy YES at the ask if `fair - ask >= 0.08`, buy NO at `1 - bid` if `bid - fair >= 0.08`; taker, one order of C = 10 contracts per qualifying strike, held to settlement. Try B: Try A restricted to the side priced under 50c (long shots).
- Fee `ceil(7% x C x p x (1-p) x 100) / 100` per order; stress fees x1.2. Information only (not tried): edges 0.05 and 0.12.

## Windows and holdout
Three equal time windows by event close date (events sorted, split 3/3/4 for 10 events: first third, middle third, last third). The last third is the frozen holdout: no rule, edge, spread cut or universe choice is made from any window (everything is fixed in this file), and its numbers are reported separately but not used to choose anything. If events are fewer than 12 per window, the three windows are reported but a PF there is descriptive.

## Numeric prediction (written before scoring)
The nowcast beats the market price in Brier at the look, AND buying the under-priced side at a gap of 8c or more after the fee earns profit factor at least 1.5 in each of the three windows. My own prior: the Brier of the nowcast is WORSE than the market's, trades are few (about 20 to 60 in total) and PF is below 1.5 somewhere.

## Kill criteria
- `NOT_ENOUGH_DATA`: fewer than 150 settled trades in total (the weekly series is too short: 10 settled events, 190 strikes, so 150 trades is not reachable on history; registered forward below). The PF per window is reported anyway.
- `FALSIFIED`: profit factor under 1.5 after fees in any of the three windows (when that window has at least 5 trades), or nowcast Brier no better than the market's, or fees x1.2 PF not positive, or (with 150 or more trades) pooled event-clustered z under the deflated bar 5.27.
- `NOT_YET_FALSIFIED` only if every line passes; it would permit only a forward quote-based re-read, never a trade.
- `NOT_RUNNABLE` if FRED/Treasury or the Kalshi candles are unreachable here.
A result is quoted with window, n, cost (fee at C = 10), and N.

## Forward registration (the history cannot reach 150 trades)
Same rule, unchanged, scored on weekly events from `KX30YMORTW-26NOV05` onward (history events are not re-used), read when 150 settled trades exist or on 2027-09-30, whichever is first. At about 2 to 5 trades per event that is on the order of 40 or more weekly events, so about the second half of 2027. The historical hourly candles stay downloadable from Kalshi, so no recorder is needed; if candles later stop being served, a keyless hourly quote recorder for this one series would be needed (not built).

## Overlap with L1
None: weekly mortgage-rate markets settled on a Thursday release, not a 15 minute window, no shared tickers, held to settlement; cannot hold a position at the same time as an L1 order. Not OICORE.

## Tries
Two (A and B). N +2: running count about 728,700 (z bar about 5.27).
