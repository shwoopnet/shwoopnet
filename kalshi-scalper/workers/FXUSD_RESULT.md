# FXUSD result (2026-10-30, run once)

Registered first in `workers/FXUSD_REGISTRATION.md` (commit 2221343), scored once with `PYTHONPATH=src python -m scalper.fxusd score` (no `--holdout`).
Candles: the five series, 10,747 markets, fetched after the registration was pushed. Nothing live was touched, no recorder was built.

## Verdicts

| Cell | Words | Why |
|---|---|---|
| A FIX_PRE, buy USD up (the one trade) | **NOT_ENOUGH_DATA** | discovery PF 1.44 is below the 1.5 bar, validation PF 0.61, and trades are 59 / 23 against the bar of 100 / 50 / 30. Holdout not read (A did not pass discovery and validation). Not FALSIFIED only because discovery PF was 1.0 or better, which is the registered line. |
| B REL_0730 (count only) | **NOT_ENOUGH_DATA** | n 85 in discovery plus validation, interval 0.459 to 0.665 |
| B REL_0800 (count only) | **NOT_ENOUGH_DATA** | n 85, interval 0.357 to 0.564 |
| C WEEK_OPEN (count only) | **NOT_ENOUGH_DATA** | n 16, interval 0.332 to 0.769 |

As the registration said in advance, no cell can show a gap of fewer than about 18 points at these counts, so none of the looks is a null result.

## Counts and corrections

- Pooled windows **10,747** (EURUSD, GBPUSD, USDJPY 2,525 each; AUDUSD, USDCAD 1,586 each). Days 33; splits by Central date: discovery 2026-09-23 to 10-15 (20 days), validation 10-16 to 10-22 (6), holdout 10-23 to 10-30 (7, unread).
- Sign correction: "USD up" is the NO side on EURUSD, GBPUSD, AUDUSD (USD is the quote currency) and the YES side on USDJPY, USDCAD. The brief's instruction to flip the USD-base pairs was the wrong way round; the registration says so. Ties settle YES, so a USD-up bet loses every tie on the three NO-side pairs (1.8%, 1.9%, 2.7%) and collects every tie on USDJPY (1.1%) and USDCAD (2.3%).
- The UK/US mismatch week (2026-10-26 to 10-30; fix at 10:45 to 11:00 Central, not 9:45 to 10:00) lies wholly in the holdout, so the aligned versus mismatch split is empty in the scored splits: **aligned 85 windows (disc 60, val 25), mismatch 0.** Rows for the mismatch regime are n 0 by construction, not by lack of effort.
- Baseline (windows in no registered moment, disc plus val, 7,846 windows): USD-up share, ties out, **0.488** [0.477, 0.499]; as settled 0.485. The five week sample drifted slightly toward the USD falling (discovery 0.493, validation 0.475), so a USD-up bet starts with the wind against it.

## Each moment's USD-up share (ties out, non-tie windows) and n

| Moment | Discovery | Validation | Discovery plus validation (95% Wilson) |
|---|---|---|---|
| A FIX_PRE (pair windows closing at 16:00 London) | 0.617, n 60 | 0.542, n 24 (1 tie) | 0.595 [0.488, 0.694], n 84 |
| B REL_0730 (weekdays, includes all days) | 0.533, n 60 | 0.640, n 25 | 0.565 [0.459, 0.665], n 85 |
| B REL_0800 | 0.500, n 60 | 0.360, n 25 | 0.459 [0.357, 0.564], n 85 |
| C WEEK_OPEN (Sunday 16:15 Central) | 0.455, n 11 | 0.800, n 5 | 0.562 [0.332, 0.769], n 16 |

As settled (ties as Kalshi): A 0.617 / 0.520 / 0.588; the other cells have no ties. Nothing has a lower bound at the 53.5% break-even gap with the same sign in both splits (REL_0730 comes closest, 0.533 then 0.640, interval 0.459 to 0.665, and REL_0800 goes the opposite way in validation, which is the usual look of noise at n 25).

## A, the one trade: buy USD up at the next candle's quote, C = 10, 20c to 80c

| Split | Trades (windows) | Hit | Mean fill | PF C10 | PF x1.2 | PF C1 | Net C10 | Day z | Volume>0 candles only |
|---|---|---|---|---|---|---|---|---|---|
| Discovery | 59 (60; 1 out of band) | 62.7% | 0.531 | **1.44** | 1.42 | 1.42 | +$46.79 | 0.85 | n 55, PF 1.40 |
| Validation | 23 (25; 2 out of band) | 47.8% | 0.569 | **0.61** | 0.60 | 0.59 | -$24.65 | -0.96 | n 21, PF 0.75 |
| Holdout | not read | | | | | | | | |

Break-even hit at the mean fill 0.531 is about 55%; discovery's 62.7% on 59 trades is 1.2 standard errors above it. The deflated bar (z about 5.27) is missed by 4.4 points on discovery alone; the observed day-clustered z is 0.85 and -0.96. The prediction (PF 0.8 to 1.0) is 0.4 off in discovery on the high side and inside the range in validation, consistent with noise around a break-even-minus-cost process.

## What this does and does not say

- The five FX series are one factor, and pooling them did what it was meant to do for sample size (10,747 windows), but each calendar moment is one window per pair per weekday, and only 33 days exist. 115 windows is the ceiling for any weekday-time moment; the bars of 100 / 50 / 30 trades cannot be met by a one-window-a-day rule in five weeks. A longer rule of this kind needs about 3 more months of history or a moment that occurs on many windows a day.
- There is no evidence for a fix run-up (+11.7 points in discovery, +4.2 in validation, both inside their intervals) or a release effect (REL_0730 up, REL_0800 down, the two cancel), and the USD baseline drift is itself 1 to 2 points off 50%.
- The best discovery PF (1.44) falls to 0.61 the next week, the pattern the ledger has seen on every small-n calendar cell (HOUR2, EVT1). Not a finding.
- Tries: 4 (A, REL_0730, REL_0800, WEEK_OPEN). **N goes from about 728,662 to about 728,666** (plus the other new workers).

## Proposed README section (for the lead to add; I did not edit README.md)

```
## Result: FXUSD (pooled US dollar calendar moments, five Kalshi FX 15 minute series), 2026-10-30

Registered first (`workers/FXUSD_REGISTRATION.md`, commit 2221343), scored once (`workers/FXUSD_RESULT.md`, `src/scalper/fxusd.py`). The five FX series (EUR/USD, GBP/USD, USD/JPY 2,525 windows each from 2026-09-23; AUD/USD, USD/CAD 1,586 each from 2026-10-07) pooled by USD direction: 10,747 windows, 33 days. USD up is the NO side on the three USD-quote pairs and the YES side on USD/JPY and USD/CAD (ties settle YES, 1.1% to 2.7%), which the brief had reversed. Moments chosen from the calendar before any data: the window closing at the 4 PM London fix (A, buy USD up; the UK/US mismatch week 10-26 to 10-30 is computed from London time and sits wholly in the holdout), windows starting 07:30 and 08:00 Central on weekdays (B, count only), the first window after the Sunday open (C, count only). A: discovery 59 trades PF 1.44, validation 23 trades PF 0.61 (hit 62.7% then 47.8%), holdout unread: NOT_ENOUGH_DATA (trades short of 100 / 50 / 30, PF below 1.5; a one-window-a-day rule has at most 115 pooled windows in 33 days). B and C looks: USD-up shares 0.565, 0.459 and 0.562 with intervals 18 points wide or more: NOT_ENOUGH_DATA. Baseline USD-up share of the other windows 0.488. N +4; running count about 728,666.
```
