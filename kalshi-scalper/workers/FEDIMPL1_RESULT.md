# FEDIMPL1 result: NOT_ENOUGH_DATA (12 trades of 150 needed; 0 wins), 2026-11-03

Registration: `workers/FEDIMPL1_REGISTRATION.md` (commit 395d212, amendment a224ec0 for forward dates only). Code `src/scalper/fedimpl1.py`, tests `tests/test_fedimpl1.py`
(7 pass). The one scored run (`python -m scalper.fedimpl1 run`, output kept in `data/fedimpl1_result.txt`, refused a second time) read the first two thirds of
meetings. **The last third (10 meetings, first decision 2025-09-17) is the frozen holdout and was not read.** Disclosure: while checking the fetch I printed the raw candles of two
2023-05 markets (a scored meeting); nothing in the rule changed after.

## Duplicate check
Covered and not re-run: Atlanta Fed tracker route (ECONNEW1 row (c), never scored), the 14:00 ET statement 15 minute window (EVENT1, EVENT830, EVT1, CAL: 0 to 5 trades). Run here (new): FOMC
decision and fed funds ladder markets against a bill-implied rate. KXTNOTE and hourly yields: NOT_RUNNABLE, the only keyless references (FRED) are daily closes.

## Reference and coverage
- Reference reachable: yes. FRED DFF and DGS1MO by curl (200, last point 2026-10-30), no key. Model E = (DGS1MO - DFF - median pre-meeting spread) in bps, normal sigma 10.
- Meetings with Kalshi history: **30** (KXFEDDECISION and its older name FEDDECISION, 2023-05-03 to 2026-10-28; the Sep and Oct 2026 meetings are in the live listing, the rest in
  the historical endpoint), each with 5 outcome markets, plus the KXFED/FED "upper bound above K" ladder of the same meeting (earlier names FED-). Candles are hourly. 20 scored, 10 holdout.
- **Quote coverage is the real limit.** Of 168 registered markets in the scored meetings, 71 had **no candle at all** on the day before the decision, 60 had no two sided book at the 19:00 UTC look, 1 had none at the
  fill, 2 errors, **34 usable (20%)**. Hourly candles exist only for markets that traded that day, and a longshot with bid 0 is one sided.
- Reference quality: the model's E was within 10 bps of the actual move on most holds, but 2023-06-14 gave -38.5 bps (a hold), 2024-11-07 -28 (a 25 cut: right sign, right size), 2025-07-30 +20 (a hold).
  Bill yields carry about +-20 bps of noise against the policy rate at one month, the same size as a 25 bp move.

## Result (first two thirds)
| | n | win | mean | PF |
|---|---|---|---|---|
| ALL (C = 10, after fee) | 12 | 0 of 12 | -3.89c | 0.00 |
| first half / second half | 1 / 11 | 0 / 0 | 0.00c / -3.75c | 0 / 0 |
| R1 KXFEDDECISION / R2 KXFED | 10 / 2 | 0 / 0 | -3.91c / -3.80c | 0 |
Fees x1.2 PF 0.00. Skips: model rule failed 9, not a cheap side 12, spread over 10c 1, no data 134. All 12 fills were at 3c to 5c (average 3.6c), the model's mean probability on the trades was 0.365 against a win
rate of 0 (0.4 wins expected from the prices). The ratio rule fired only where the bill-implied move disagreed with a market at 97% (a NO at 3c with model 0.30 or higher): the model was wrong each time. Longshots here are
at the 3c floor, so the "3x" rule asks the bill-yield model to be sure of a miss the market gives 3%, and the model's noise (sigma at least 10 bps against 25 bp cells) cannot be that sure.
- Verdict: **NOT_ENOUGH_DATA** (12 trades of 150). STOPPED_EARLY did not fire (needs 30 trades), but the direction is plain: 0 of 12, the cheap-side tail is not underpriced by this model.
- Prediction versus outcome: predicted 9 to 40 trades (hit 12), win rate 10% to 25% (missed, 0%), PF 0.4 to 1.6 (missed, 0), mean -3c to +4c (hit, -3.9c); the written word NOT_ENOUGH_DATA was right.

## Months to 40 and 150 trades
0.6 trades per meeting (12 over 20), 8 meetings a year: **40 trades take about 100 months, 150 about 375 months.** This cannot reach any bar in any useful time. Even tripling the rate by widening the
band does not change the answer.

## Forward plan (rule frozen now)
Looks: 2026-12-08 for the 2026-12-09 meeting, then the business day before 2027-01-27, 03-17, 04-28, 06-09, 07-28, 09-15, 10-27, 12-08. `PYTHONPATH=src python -m scalper.fedimpl1 forward` fetches the live candles
on the look day and prints the registered decision per market (nothing is placed). The README carries a dated forward-read line: read the Dec 2026 look on 2026-12-08 as information only, because
the history already says the line is worth no ledger of its own. No candidate JSON was written: the forward pipeline is built around 15 minute windows.

## Capped probe spec (SPEC ONLY, NOT proposed)
Not recommended: no positive half, 0 wins. Were it ever to pass (it will not): 1 contract, hard limit 0.30, held to settlement, only the FOMC decision day-before look, at most 3 orders per meeting, worst single
loss $0.31 (30c + 1c fee), worst meeting about $0.93, kill at 40 fills with PF under 1.2 or cumulative -$5; 40 fills would take until about 2035.

## N and holdout
N +4 (running count about 730,044, z bar 5.27). The holdout is untouched and stays so; reading it needs a new amendment and would spend nothing the history above leaves worth spending.
