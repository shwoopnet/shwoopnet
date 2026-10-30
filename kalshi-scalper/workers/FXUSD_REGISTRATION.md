# FXUSD registration (2026-10-30), written before any FX candle was fetched and before any window result was read

Worker for "Strategy Research V2". Research only. Public data only. Nothing live is touched and no recorder is built.
Code: `src/scalper/fxusd.py`. Everything below was fixed from calendar facts and listing counts only; the `counts` command
reads no result and no price.

## Ledger check (done first)

README holds FLAT2 / FLAT-R (rng5 and rise3 shape, FX pairs did not follow, AUD/USD and USD/CAD 52 and 58 flat entries),
GEN1 (pooled features), HOUR2 (hour of day on metals and gold, FALSIFIED), EVT1 (gold and Bitcoin event windows, FALSIFIED;
macro releases NOT_ENOUGH_DATA, 1 to 7 windows each). None of them tests the five FX pairs pooled by US dollar direction at
calendar moments, and none uses the 8:30 Eastern release, the London fix or the Sunday open on FX. Not a reworded tested idea.

## Data and the sign correction

Five series: KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M (2,525 windows each from 2026-09-23), KXAUDUSD15M and KXUSDCAD15M (1,586 each
from 2026-10-07). Pooled **10,747 settled windows**. The brief said to flip the sign for the USD-base pairs; that is the wrong way round.
"USD up against the foreign currency" is:

| Pair | USD is | USD up = pair | The Kalshi side that wins when USD rises |
|---|---|---|---|
| EURUSD, GBPUSD, AUDUSD | quote | down | **NO** |
| USDJPY, USDCAD | base | up | **YES** |

**Ties settle YES** (settled value equal to the strike). Tie rates: EURUSD 1.78%, GBPUSD 1.90%, AUDUSD 2.71%, USDJPY 1.11%, USDCAD 2.27%.
So a pooled "USD up" bet loses every tie on the three USD-quote pairs (it is on NO) and wins every tie on the two USD-base pairs. Two
shares are reported: **ties out** (USD rose strictly, over non-tie windows; the physical question) and **as settled** (what a bet
would actually collect). The trades use the as-settled result. The tie handicap on the NO side is about 1.8% to 2.7% of those pairs' trades,
which is as large as half the fee wedge, so it is part of the cost and is not removed.

## Splits (by Central date of the window open; 33 days from 2026-09-23 to 2026-10-30, sorted, first 60% / next 20% / last 20%)

- Discovery: **2026-09-23 to 2026-10-15** (20 days). Validation: **2026-10-16 to 2026-10-22** (6 days). Holdout: **2026-10-23 to 2026-10-30** (7 days), read once and only if discovery and validation both pass.
- The UK moved to winter time on 2026-10-25 and the US stays on summer time until 2026-11-01, so **2026-10-26 to 10-30 is the UK/US mismatch week**
  (all five days fall in the holdout; none in discovery or validation). The mismatch is handled by computing the fix from London local time (below), not by assuming a Central hour.

## The three registered moments (calendar facts, all US Central)

**A. FIX_PRE: the window that closes at 16:00 London time (the WM/Reuters 4 PM fix print), Monday to Friday.** Computed per date with `Europe/London` and
`America/Chicago`: 09:45 to 10:00 Central on 2026-09-24 to 10-23 (aligned, 90 pooled windows), **10:45 to 11:00 Central on 10-26 to 10-30** (mismatch, 25 windows; the fix is 11:00
Central that week, not 10:00 and not the 9:00 that applies after 11-01 when both zones are on winter time). The fix's one minute calculation window (15:59:30 to 16:00:30)
straddles the boundary of two 15 minute windows; I register the window that **ends at the print** (the run-up) and do not look at the window that starts at it (no second try spent).
- Pooled windows: 115 (discovery 60, validation 25, holdout 30). Pairs: EURUSD 27, GBPUSD 27, USDJPY 27, AUDUSD 17, USDCAD 17.
- **Directional hypothesis (trade): USD UP.** Mechanism: clients and month-end hedgers place fix orders that are executed at the benchmark regardless of price; banks that expect net USD buying
  pre-hedge in the minutes before the print. Named counterparty: the Kalshi quoter who prices the window near 50/50 and does not lean into the known fix flow, and the end client who gets the benchmark.
  Caveat stated now: the sign of the net fix flow varies by day and month (it depends on relative equity returns for month-end rebalancing, which I do not have), so a pooled all-days USD-up prior is weak.
  The direction is my recollection of the fix literature and is not verified from anything in this repo.

**B. RELEASES (count only, no direction): windows starting 07:30 and 08:00 Central, Monday to Friday** (8:30 Eastern US data time is 07:30 Central year round). Two cells: REL_0730 and REL_0800.
Pooled windows 115 each. The pooled windows include **all** weekdays, release days or not; I do not separate them. No direction with a named counterparty can be stated (the sign of a release surprise is not known in advance), so this is a **no-direction look: count and a Wilson interval only, no trade.**

**C. WEEK_OPEN (count only, no direction): the first window of each pair after a gap of 12 hours or more in the listing** (not the first window of the history). 21 pooled windows (5 weeks;
EURUSD, GBPUSD, USDJPY 5 each, AUDUSD, USDCAD 3 each), all starting Sunday 16:15 Central. No sign with a counterparty, so **count only.**

## Rule for the one trade look (A)

On each FIX_PRE window buy **the USD-up side** (NO on EURUSD, GBPUSD, AUDUSD; YES on USDJPY, USDCAD). Signal: the calendar, no data. Entry: the first candle after the open (the candle ending open+60) is the signal candle;
fill strictly at the **next** candle's (ending open+120) quote that you can hit at its start: for YES the ask open, for NO one minus the YES bid open. No trade if that quote is missing or the price is outside **0.20 to 0.80**. Held to settlement.
Size C = 10 (the one-minute candles carry no sizes, so a ten contract fill is modelled, not observed); also reported at C = 1. Fee 7% x C x p x (1-p), rounded up to the cent per order; fees x1.2 check. Zero-volume candles reported both ways.

## Prediction (numeric, now)

- A: USD-up share over non-tie windows 50% plus or minus 3 points; hit rate of the bought side about 49% to 51% after ties; **PF 0.8 to 1.0 in each window** (fee wedge about 3.6c at 50c plus half the spread, break-even hit about 53.5%, PF 1.5 needs about 58%).
- B and C: shares inside 45% to 55%.
- Sample sizes cannot reach the bars: A has **60 / 25 / 30** trades against the bar of 100 / 50 / 30 (first two short, third exactly at the bar only if every window fills). Expected verdict: **NOT_ENOUGH_DATA** for A on counts alone, unless discovery PF is below 1.0.

## Verdict rules (words fixed now)

- **A trade (FIX_PRE)**: FALSIFIED if discovery PF < 1.0 after fees (the rule loses in the sample that is allowed to flatter it). NOT_ENOUGH_DATA if discovery PF is 1.0 or better but trades are below 100 / 50 / 30, or the data is otherwise short. NOT_YET_FALSIFIED only if PF >= 1.5 in each of discovery and validation (and, when read, the holdout) with trades at or above the bar, PF positive at fees x1.2, and the day-clustered z above the deflated bar below. NOT_RUNNABLE if the candles for the moment cannot be fetched.
- **Deflated bar**: running N about 728,662 plus this worker's tries; z bar about **5.27** (`Z_BAR`), day-clustered z of the per-day net, as NEWH15.
- **B and C looks (no trade)**: a gap needs the non-tie USD-up share to be outside 46.5% to 53.5% (the fee wedge) with the 95% Wilson interval excluding it, in discovery and validation with the same sign, to be called NOT_YET_FALSIFIED; with these counts (n of 115 gives an interval half-width near 9 points, 21 gives near 20 points) no cell can show a gap smaller than about 18 points, so the **expected verdict for every look is NOT_ENOUGH_DATA**. A look is FALSIFIED only if the interval of discovery plus validation lies wholly inside 46.5% to 53.5%, which also cannot happen at this n. I say this now so no cell is later read as a null result.
- **Holdout** is read only if A passes discovery and validation. The looks print discovery and validation only unless `--holdout` is passed, and `--holdout` is not passed unless A passes.

## Kill criteria

Stop and report FALSIFIED / NOT_ENOUGH_DATA as above. No second variant of the fix window (the following window, other lead times, month-end only, per-pair cuts) is run. A baseline row (windows in no registered moment) is printed as context for the USD drift of this five week sample; it is not a try.

## Tries (N)

Trade look 1 (A) + count looks 3 (REL_0730, REL_0800, WEEK_OPEN) = **4 tries**. N goes from about 728,662 to about **728,666** (plus the two other new workers). All pooled-pair cuts and the regime split of A (aligned vs mismatch weeks) are information lines, not tries.
