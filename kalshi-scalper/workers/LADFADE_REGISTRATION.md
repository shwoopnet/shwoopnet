# LADFADE registration (Strategy Research V2 worker, 2026-10-30, research only)

Written and pushed BEFORE any holdout fill or outcome was read for this rule. Code `src/scalper/ladfade.py` (committed with this
file); result `workers/LADFADE_RESULT.md`. Market: KXBTC15M with the hourly KXBTCD ladder. Times: UTC for the code, US Central
(CDT, UTC-5, the whole sample) in words.

## Where it came from (disclosure: post hoc)

NEWH9's information look I1 (`workers/NEWH9_RESULT.md`) on KXBTC15M windows that open at :15 and :30 past the hour, at the window's
first minute, among windows where the hourly ladder leaned at least 5c from 50/50:

| Stage, lean | n | ladder p | 15 minute YES mid | YES outcome rate |
|---|---|---|---|---|
| discovery, YES | 218 | 0.589 | 0.626 | 0.569 |
| discovery, NO | 222 | 0.408 | 0.371 | 0.410 |
| validation, YES | 250 | 0.590 | 0.623 | 0.568 |
| validation, NO | 173 | 0.413 | 0.365 | 0.376 |

The 15 minute mid overshoots the ladder by 3.3c to 4.8c (mean about 3.9c) in the direction of the lean, and the outcome rate sits
near the ladder. Because this was SEEN on discovery and validation, both are SPENT for this rule and are not scored. The only clean
history is NEWH9's frozen holdout (window closes 2026-10-18 00:00 to 2026-10-30 00:00 UTC, i.e. Oct 17 7:00 PM to Oct 29 7:00 PM
Central), never read for any rule, plus forward windows.

Also looked at before writing (no outcome, no PF): to check the code runs, the funnel counts on the spent windows (discovery 254
entries, validation 251; trade counts only, no fill outcome or result read). For the forward evaluator, a smoke run on Oct 29 to 30
windows printed only "trade / no trade / no data" per window (no outcome read). Ledger check: LADLEAN (NEWH9 H2) bought WITH the
ladder's lean and was FALSIFIED; this buys AGAINST the 15 minute book's overshoot, the opposite side, so it is a new try, not a
reword. XM1, BLADX, CONF2, LOCK2H all compared at the coincident close; this compares 30 to 45 minutes before the ladder's close.

## The rule (fixed now)

- **Universe:** KXBTC15M windows closing at :30 and :45 past the hour (open at :15 and :30), chosen by clock only. Hourly ladder:
  the KXBTCD event closing at the next top of the hour (history files `conf2_lad.sqlite` then `lad2.sqlite`, first file wins per
  close, exactly as NEWH9; forward: the book recorder, `origin/quote-data` `book/`). 15 minute files `l1b`, `book`, `fresh`.
- **Signal candle:** the 15 minute candle ending 840 s before the close (the window's first minute). Ladder p = the linear
  interpolation in strike of the YES mids of the adjacent quoted ladder strikes K_lo <= K15 < K_hi at that same minute (each
  0 <= bid < ask <= 1, K_hi - K_lo at most $200), exactly NEWH9's `ladder_p`. K15 is the 15 minute market's stored strike.
- **Lean (the population I1 was seen on):** p >= 0.55: the faded side is NO, its ladder chance 1 - p. p <= 0.45: the faded side is
  YES, its ladder chance p. Otherwise no trade ("flat").
- **Gap (fixed from the I1 means only):** the faded side's ask on the signal candle must be at least **GAP = 3c** below its ladder
  chance. Why 3c: the mean mid overshoot is about 3.9c, the faded side's ask sits about half a spread (a cent or less) above its mid,
  so a typical overshoot window shows about 3c; the C = 10 fee at 35c to 45c is 1.6c to 1.8c a contract, so 3c is the smallest gap
  that leaves at least a cent after the fee. Not tuned on any outcome.
- **Fill:** the faded side's ask on the NEXT candle (ending 780 s before the close), whatever it is, only if it is in [0.30, 0.70]
  (else counted "band"). Held to settlement. One trade per window. Missing candle, strike or bracket: counted "gap".
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order. Headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose signal or fill candle had volume 0.

## Counterparty

The 15 minute book's opening quoters and first-minute takers, who push the new window's price further from 50/50 than the deeper
hourly ladder (which prices the same strike, 30 to 45 minutes from its own close, with more makers and more depth) says is fair. If
the ladder is the better estimate, whoever buys the leaned side at the overshot price in the first minute pays the gap.

**Honest alternative:** the overshoot is partly real information the 15 minute book has first (it settles 15 to 30 minutes before
the ladder, so the two are not the same contract: the 15 minute settles on a different instant's price, and a short-horizon
probability of being above a strike near the money should be MORE extreme than the hourly one when spot has already moved, not
equal). Then the 3c to 5c is not an overshoot at all, and the outcome rates in I1 that sat near the ladder were noise of +/- 3 points
on about 200 windows. The fill one minute later crosses a spread and pays 1.6c to 1.8c a contract in fees.

## Prediction (numeric)

Holdout: 60 to 120 trades; average fill ask 0.36 to 0.42; win rate within 3 points of the average fill plus 1 point; PF at C = 10
between 0.85 and 1.20. Most likely verdict: FALSIFIED.

## Bar and kill criteria (one window, read once, no parameter change after the score)

- Holdout fewer than 30 trades: NOT_ENOUGH_DATA.
- Holdout PF at C = 10 under 1.5, or net at fees x1.2 at or below 0: **FALSIFIED** (no forward rescue; the forward candidate below
  keeps reporting as a dead candidate, as the candidates README says, and earns nothing).
- Holdout PF at C = 10 at least 1.5 and net at fees x1.2 positive: **NOT_YET_FALSIFIED, for forward only.** The full bar is PF 1.5 or
  better in three windows after fees AND a day-clustered z at the deflated bar. With **N about 627,846 after this try** the
  one-sided Bonferroni bar at 0.05 is **z about 5.24**. A 12 day holdout cannot reach it: z = mean / sd x sqrt(12) would need a daily
  mean of 1.5 standard deviations every day, which no 15 minute rule in this ledger has shown. So the honest outcomes are only
  FALSIFIED, NOT_ENOUGH_DATA or NOT_YET_FALSIFIED-for-forward; a pass earns a forward read and nothing more.
- Forward kill (only if the holdout is NOT_YET_FALSIFIED): FALSIFIED if after 100 forward trades PF at C = 10 is under 1.2 or net at
  fees x1.2 is at or below 0; reviewed at 30 trades on 10 trade days (the ledger's READY bar) and not before.

## Forward candidate

Registered with this file: `workers/candidates/LADFADE_BTC.json`, freeze **2026-10-30T12:00:00Z** (7:00 AM Central, at or after this
commit), source `candles`, evaluator `scalper.ladfade:forward_eval`. It uses existing data only: the 15 minute candles the AUTO loop
already refreshes (`data/fresh.sqlite`) and the KXBTCD book recorder (`origin/quote-data` `book/`, 7 strikes near the money every
3 s from 55 minutes before each hourly close, running since 2026-10-29). Forward ladder p uses the last poll of each strike inside
the signal minute (the same minute a candle close describes), YES ask = 1 - best NO bid. An hour the recorder missed, or a ladder
that does not bracket K15, is NoData (not evaluated, never scored as no trade). The smoke run on Oct 29 found the recorder covering
only part of the day, so forward n will grow slower than the history's rate.

## Count

N tried: **1** (LADFADE btc). Running count about 627,845 (after NEWH9) + 1 = **about 627,846**; deflated one-sided z bar **5.24**.
