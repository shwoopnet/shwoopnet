# EVT1 registration: scheduled-event windows on gold and Bitcoin 15 minute markets (Strategy Research V2, worker EVT1, research only)

Written 2026-10-30 BEFORE any profit, loss, win rate or price of an event window was computed. Only event and window counts
(`python -m scalper.evt1 counts`, table below) were looked at. Code: `src/scalper/evt1.py` (committed with this file).

## Ledger check (not a reworded tested idea, with two overlaps stated)

- L10 / N4 / O20 in the README queued exactly this ("scheduled release windows, gold and Bitcoin") as "not runnable until a dated
  calendar exists". `studies/EVENT_CALENDAR_2026.csv` (worker CAL) is that calendar. So this is the first run of L10, not a re-run.
- Overlap 1: IDEAS20D `DATA_0830ET` (Bitcoin and Ethereum, windows closing 12:30 to 14:00 UTC on all days, against the coin's own
  average) read about zero. It was a clock-time rule on every day, not a release-date rule; EVT1's MACRO0830 uses release days only,
  with non-release days at the same slot as the control.
- Overlap 2: MKTTIME1 (4 hour blocks, weekdays) and HOURCLOSE (:00 UTC closes) were time-of-day rules. Every EVT1 comparison is
  against the SAME market at the SAME 15 minute clock slot on days without the event (or, for daily recurring times, other slots of
  the same days, below), so a time-of-day effect cancels out of the difference. The three daily-recurring "settlement" types
  (CME gold settle, CME Bitcoin close, funding) cannot be separated from time of day; for them the comparison is against nearby slots,
  which makes them close to a time-of-day test by construction. Stated, and they are counted in N.
- CAL_REL1_DRAFT (bill auctions as an L1 stand-down) was not registered; TSY_BILL here covers the same windows.

## Rule, exactly

**Markets (chosen by the brief, on nothing else):** KXGOLD15M and KXBTC15M. History: `scalper.gen7.load_windows` (files l1b, book,
fresh, five), settled windows only.

**Windows by date (close time, UTC):** DISCOVERY 2026-08-06 to 2026-09-20 (close < 2026-09-21 00:00Z); VALIDATION 2026-09-21 to
2026-10-27 (close < 2026-10-28 00:00Z). Nothing closing on or after 2026-10-28 is read. The third window required by RULES.md is the
FORWARD record: a screen survivor goes to `workers/candidates/` with a freeze time after this commit and is read only by the forward
ledger. There is no historical holdout.

**Events** (`evt1.calendar()`):
- From `studies/EVENT_CALENDAR_2026.csv`, status `verified` or `rule` (never `unverified`): CPI, PPI, JOBS, GDP_PCE (GDP and PCE are
  released together; one type), RETAIL, CLAIMS (rule rows only, Thursday 8:30 ET), FOMC (2:00 pm ET), EIA (Weekly Petroleum Status
  Report), TSY_BILL (bill auction close 11:30 ET), TSY_COUPON (coupon auction close, 1:00 pm ET; FRN 11:30), MAINT (Coinbase,
  Kraken, Bitstamp maintenance whose calendar note says "trading or API scope"; Kraken is covered only from mid September).
  Several auctions at one time are one event.
- Added by official recurring rule (generated in code, no new CSV rows; sources: CME Group settlement procedures for COMEX gold
  GC, daily settlement 13:30 ET; CME Bitcoin futures BTC daily close and settlement 16:00 ET / 15:00 CT; Deribit options and futures
  expiry Friday 08:00 UTC; perpetual funding at 00:00, 08:00, 16:00 UTC on Binance, Bybit, OKX):
  CME_GOLD_SETTLE (weekdays 13:30 America/New_York), CME_BTC_CLOSE (weekdays 16:00 America/New_York), both skipping
  2026-09-07 (Labor Day), 2026-11-26, 2026-12-25; DERIBIT (Fridays 08:00 UTC); FUNDING (daily 00, 08, 16 UTC).

**Positions.** For an event at time e, the containing window is the one with close - 900 <= e < close (for an event on the quarter
hour, the window that opens at e). BEFORE is the window that closes 15 minutes earlier (it closes at or before e), AFTER the one
that closes 15 minutes later.

**Units (fixed now; pooled groups named before scoring).**
- Both markets: CPI, PPI, JOBS, GDP_PCE, RETAIL, CLAIMS, FOMC, EIA, TSY_BILL, TSY_COUPON, and the groups
  MACRO0830 = "US macro releases at 07:30 CT" (CPI, PPI, JOBS, GDP_PCE, RETAIL, CLAIMS), MONTHLY0830 (the same without CLAIMS),
  TSY (TSY_BILL and TSY_COUPON). 13 units.
- Gold only: CME_GOLD_SETTLE. Bitcoin only: CME_BTC_CLOSE, DERIBIT, FUNDING, MAINT and the group SETTLE_BTC = "settlement or expiry
  times" (CME_BTC_CLOSE, DERIBIT, FUNDING). Gold 14 units, Bitcoin 18 units.

**Sides (4), each one trade per window at most, YES tried before NO:**
- FAV360: the side whose ask is 0.88 to 0.97 at the candle ending 360 s before the close (L1's band and look).
- CHEAP360: ask 0.05 to 0.50 at 360 s. CHEAP180: ask 0.05 to 0.50 at 180 s. FAVMID180: ask above 0.50 and at most 0.85 at 180 s.
- Fill at the NEXT candle's ask (the candle ending 60 s after the signal) for that side, any price strictly between 0 and 1; held
  to settlement; 1 contract per decision. A missing signal or fill candle is a data gap, counted, never a no-trade.

**Cells:** (14 + 18) units x 3 positions x 4 sides = **384 cells**. Plus the L1 read (below): 32 units x 3 positions = **96 cells**.
**N for EVT1 = 480.** Running count about 591,486 -> about **591,966**.

**Fees.** 7% x C x p x (1 - p) rounded up to the cent per order. Headline at C = 10; C = 1 reported; fees x1.2 at C = 10 reported.
Zero-volume: a trade whose signal or fill candle had zero volume is flagged; PF is reported with and without them.

**Matched control.** Same market, same side rule, same split, windows not in ANY position of ANY event of the unit, at the same UTC
15 minute clock slot and the same weekday/weekend class as each event window. For the daily recurring types the same slot has no
event-free days, so: FUNDING uses the slot 4 hours later (04, 12, 20 UTC); CME_GOLD_SETTLE and CME_BTC_CLOSE use the slots 2 hours
earlier and 2 hours later on the same day class; DERIBIT uses the same slot on other weekdays. **Statistic:** each event trade's net
minus its slot's control mean net (per contract, C = 10); diff = the mean of those; z = diff / sqrt(day-clustered SE of the event
residuals^2 + control sampling SE^2). Event trades whose slot has no control trade are dropped from the diff (reported).

**Screen (from the brief, plus a stress line).** A cell passes only if DISCOVERY has PF >= 1.5 on >= 30 trades, diff z >= 2, net > 0
at fees x1.2, AND VALIDATION has PF >= 1.3 on >= 20 trades, diff z >= 2, net > 0 at fees x1.2. PF at C = 10.

**L1 read (for a possible skip rule).** L1's own rule (ask 0.88 to 0.97 at 360 s, filled at that signal ask, held): loss rate in each
unit x position against the same matched control, diff in loss-rate points with the same z, in both splits. Flagged when z >= 2 in
BOTH splits (higher loss rate in the event windows). A flag earns only a registered forward skip test, nothing live.

## Counterparty (stated before evidence)

Kalshi's 15 minute quoters (makers and the market maker) who price the last minutes of a window from recent realised volatility and
do not widen for a scheduled jump in the underlying: after a US 8:30 ET release, the FOMC statement, a COMEX settlement or a
derivatives expiry, the underlying can move more than the quote implies, so the cheap side is underpriced and the favourite
overpriced in the containing and following windows. Takers who pay the cheap side's ask before a release are the losers if the
quotes already widen. This is the generic "slow to widen" mechanism; for Treasury auctions and maintenance it is weak (stated).

## Numeric prediction

No cell passes the screen (prior about 90%). Most units cannot reach 30 discovery trades at all (table below): single macro types
hold 1 to 7 event windows per split, so they are `NOT_ENOUGH_DATA` by construction and are counted only for honesty. The only units
with enough windows are TSY_BILL, TSY, CME_GOLD_SETTLE, CME_BTC_CLOSE, FUNDING and SETTLE_BTC. Predicted: diffs within +/- 2c a
contract, |z| < 2 in most cells; with 384 cells about 9 to 10 cells reach |z| >= 2 in one split by chance, and both splits together
by chance about 0 to 1. L1 read: no unit flagged in both splits.

## Kill criteria and verdicts

- A cell with fewer than 30 discovery or 20 validation trades: NOT_ENOUGH_DATA.
- Otherwise a cell that fails any screen line: FALSIFIED.
- EVT1 as a whole: FALSIFIED if no powered cell passes; NOT_ENOUGH_DATA for the unpowered event types (named in the result);
  NOT_YET_FALSIFIED (forward test only) for a cell that passes, which then goes to `workers/candidates/` with evaluator
  `scalper.evt1:forward_eval` and a parity check (`python -m scalper.evt1 parity`, 0 mismatches required). Its deflated bar for
  N about 592,000 (z about 5.2) cannot be reached in sample; a pass earns only the forward ledger read.
- No parameter, slot, window or group is changed after the score. The score runs once (`score` refuses a second run).

## Counts (looked at before writing this; windows per position, no P/L)

Gold 5,645 and Bitcoin 7,869 settled windows from 2026-08-06 to 2026-10-27. Windows per position (before = contain = after, except MAINT):

| unit | discovery windows (days) | validation windows (days) |
|---|---|---|
| CPI, PPI, JOBS, RETAIL | 2 (2) each | 1 (1) each |
| GDP_PCE | 1 | 1 |
| CLAIMS | 7 | 5 |
| FOMC | 1 | 0 |
| EIA | 6 | 5 |
| MACRO0830 / MONTHLY0830 | 14 / 9 | 8 / 4 |
| TSY_BILL / TSY_COUPON / TSY | 25 (24) / 14 / 37 (24) | 22 (21) / 11 / 32 (21) |
| CME_GOLD_SETTLE, CME_BTC_CLOSE | 31 (31) | 27 (27) |
| DERIBIT | 7 | 5 |
| FUNDING | 131 (46) | 106 (37) |
| MAINT (Bitcoin) | 2 | 9 to 11 |
| SETTLE_BTC | 162 (46) | 133 (37) |

Only TSY, FUNDING and SETTLE_BTC hold 30+ windows per split before the side rule is applied; a side rule fires in a fraction of them,
so even CME settles and TSY_BILL can fall under 30 trades.
