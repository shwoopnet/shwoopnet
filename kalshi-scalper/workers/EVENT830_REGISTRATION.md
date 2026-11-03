# EVENT830 registration: forward-only freeze of the one EVENT1 slice that was positive in both windows (Strategy Research V2, research only)

Written 2026-11-03 about 13:45 UTC, BEFORE any forward window of this rule has closed (the first possible one closes 2026-11-05 13:30 UTC).
The owner's go was relayed by main. **Freeze time: 2026-11-03T15:00:00Z** (windows with close time strictly after it count; the first release is
Thursday 2026-11-05). Nothing here means trade. No promote verb. Touches no live code, `functions/`, L1 or OICORE.

**Plain statement.** The likeliest outcome is FALSIFIED. This slice (DATA830) was picked out of EVENT1's groups AFTER its pooled verdict was
FALSIFIED, because it was the one line positive in both windows. That is selection on the outcome, so its history (49 trades) is a reason to
look forward, not evidence. The contrary hypothesis (a known release is already in the quote, and the cheap side loses by itself, PF 0.84 to
0.86 in EVENT1's controls) is the prior.

## Ledger check (how this differs)
EVENT1 (`workers/EVENT1_REGISTRATION.md`, `EVENT1_RESULT.md`) tested 8 series pooled over a wide calendar and was FALSIFIED (PF 1.20 / 0.89). Its group
DATA830 (CPI, PPI, jobs, GDP and PCE, retail, weekly claims) read 21 trades PF 2.47 and 28 trades PF 1.71, event minus same-slot control +16.4c z 1.73
and +17.8c z 2.72, NOT_ENOUGH_DATA (floor 150). EVT1 (gold and Bitcoin, 2026-10-29/30) found macro releases NOT_ENOUGH_DATA and every powered cell
FALSIFIED. EVENT830 is a different object from both: ONE pre-fixed slice, **forward windows only** (nothing in the 89 days of history is re-scored or
tuned), and a control defined on the Eastern clock (EVENT1 used UTC slots, which shift an hour when daylight saving time ends; it ended 2026-11-01, so
8:30 ET is 13:30 UTC from now on, 12:30 UTC before). Not a duplicate of CPI1, ECONNEW1/2 (those price Kalshi's own economics markets).

## Universe (fixed)
KXSILVER15M, KXCOPPER15M, KXWTI15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXHYPE15M, KXBNB15M, the 8 series EVENT1 used. None is an L1 or OICORE
market, so a cheap-side position cannot hedge L1 (Bitcoin, Ethereum, gold, Dogecoin and paused XRP are excluded).

## Trigger
A 15 minute window whose close time c is exactly a US **8:30 ET** release of: CPI, PPI, the jobs report (Employment Situation), advance retail sales,
GDP (second or third estimate) and PCE (Personal Income and Outlays), or the Thursday weekly jobless claims. 8:30 ET is 13:30 UTC (7:30 am Central) while
Eastern standard time applies (2026-11-01 to 2027-03-13). The window is the one that opens at 13:15 UTC and closes at the release. Dates are in
`workers/EVENT830_CALENDAR.md` and frozen in `src/scalper/event830.py` (`RELEASES`); the frozen list runs to 2026-12-31. Dates after it are appended from
official schedules only, never removed or changed, each committed before its window closes; a window not on the list is simply not evaluated (it is
not scored as a no-trade). Holiday-week claims (2026-11-26, 12-24, 12-31) are left out because the day is unconfirmed. Interpretation disclosure: the
release is at the close (e = c), so this tests the 3 minutes leading INTO a known release, not the minutes after it.

## Trade (exactly EVENT1's, `event1.window_trade`)
At the 1 minute candle ending **180 s before the close**: require 0 < bid < ask < 1 and ask - bid <= 0.10. The **cheaper side** is YES if its ask is
0.05 to 0.50, else NO if its ask (1 - YES bid) is 0.05 to 0.50, else no trade. **Fill at that side's ask on the next candle (ending 120 s before the
close), HARD LIMIT 0.50:** a fill ask above 0.50 is no trade, never filled higher. Held to settlement, 1 order per series per window, taker at the ask,
**fee 7% x C x p x (1-p) rounded up to the cent per order**, fees x1.2 shown. Headline C = 10, also priced at 1. A missing or one-sided signal or fill
candle is NoData for the forward ledger (not evaluated, not a no-trade); EVENT1 counted those as no trade, so the counts differ slightly by design.

## Mechanism (the counterparty)
Market makers on these 15 minute markets do not widen the cheap side for a release they know is coming, so a longshot on the side the release can flip
is underpriced. Fails if makers do widen (EVENT1's controls say the cheap side is otherwise a loser) or if the history was luck.

## Baseline (control, forward, same code)
Control trades are the same rule on windows of the same 8 series that close at **08:30 America/New_York on a weekday that has no release on the list
and is not a US federal holiday**, after the freeze. (Minor 8:30 releases not on the list, such as import prices or trade balance, sit in the control; that
dilutes the contrast and so is conservative.) The headline difference is the mean net (cents per contract, C = 10, after fee) of event trades minus the
mean net of control trades of the same series (at least 10 control trades for a series, else that trade is dropped and the drop counted), with a
day-clustered z. `python -m scalper.event830 report` prints it.

## NUMERIC PREDICTION (written before any forward window)
Per trade, all 8 series pooled, regressed hard from the 49-trade history (selected for being good) toward EVENT1's pooled behaviour:
- **Trades per month about 35 (range 28 to 42)**: about 7 to 8 release dates a month (Nov 8, Dec 7 on the list) times about 4.8 trades per date (EVENT1 DATA830
  after the FX pairs began: 43 trades on 9 dates; all 8 series now trade). **150 trades take about 4.3 months, about mid March 2027; 40 fills about 2026-12-04.**
- **Win rate 17% to 22% (central 19%)**, average fill 14c to 18c, payoff (average win / average loss) 4.5 to 5.8, win rate about 1c above the fill before fees.
- **Profit factor central 1.05, range 0.70 to 1.60 at C = 10 after fees**, mean -1c to +4c per contract; event minus control +1c central (-5c to +8c).
- Probability PF >= 1.2 at 150 trades: **25%**. Probability event minus control is positive at 150: **45%**. Probability both kill rules are passed: **15%**. Probability
  PF >= 1.5 at 150: 8%. Probability of passing the deflated bar (below): under 1%.
- Streaks (`src/scalper/streaks.py`, 19% win, 100 trades): see the result; at this win rate a 10-loss run is likely (about 85% in 100 trades). Losses cluster:
  one release hits several series at once, so the independence figure is a floor.

## KILL RULES (fixed now, no tuning)
- **NOT_ENOUGH_DATA** until 150 settled event trades exist. The report prints a message "NOT_ENOUGH_DATA: n of 150 trades, about X months to go at Y per
  month" every time.
- **STOPPED_EARLY (counts as FALSIFIED)** at 40 or more settled event trades if PF (C = 10, after fees) is under 1.0.
- **FALSIFIED** at 150 trades if PF is under 1.2, or if event minus control is not positive (point estimate at or below 0). Fees x1.2 PF at or under 1.0
  also falsifies.
- **NOT_YET_FALSIFIED** otherwise. N = 728,735, one-sided z bar for 0.05 / N about 5.27; a pooled day-clustered z under the bar is reported as
  NOT_YET_FALSIFIED, never a pass, and a count of about 150 trades cannot reach it alone. No promote verb. The ledger's own READY FOR THE FALSIFIER line
  (PF 1.5 at 1 and 10 contracts, 30+ trades, 10+ trade days) earns a falsifier read and nothing more.

## SMALLEST HONEST LIVE PROBE (SPEC ONLY, for the owner; NOT built, NOT approved, nothing placed)
Only if the forward ledger shows 40 settled event trades with PF at or above 1.2 and event minus control positive (not before about 2026-12-04, and likely
a few days later): **1 contract, HARD LIMIT 0.50, the cheaper side as above, held to settlement, only on the 8 series above, only in the window closing at a
listed release.** Worst single loss: **$0.52 at 1 contract** (50c plus fee ceil(7% x 0.5 x 0.5 x 100) = 2c). At most 8 simultaneous orders on one release, so
worst case one release about $4.16 before the stop. **Kill:** stop at 40 live fills if live PF is under 1.2, or at cumulative -$15 whichever comes first,
latched until a reviewed edit. It would be a separate slot under `docs/SECOND_SLOT_DESIGN.md` (shares the account stop and window cap), never L1's markets.
This is a description, not a request: the registration promotes nothing.

## N tried
One try (this single slice). Running count about 728,734 -> **728,735**. Per-series, per-release-type and per-month tables are reports.

## Forward evaluator
`scalper.event830:forward_eval` (source `candles`), candidate `workers/candidates/EVENT830.json`, tested in `tests/test_event830.py`. Any change to the rule
after this commit is a new id with a new freeze.
