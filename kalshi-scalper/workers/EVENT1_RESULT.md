# EVENT1 result (run once, 2026-11-03; research only)

Registration: `workers/EVENT1_REGISTRATION.md` (commit d327b06, pushed before the score). Code `src/scalper/event1.py`, calendar
`workers/EVENT1_CALENDAR.csv`, full numbers `studies/event1_score_2026-11-03.json`. No code change after registration. W3 (2026-10-05 on) was NOT read.

## Verdict: FALSIFIED (Try A, 8 series pooled)
Window, n, cost: Try A event windows (event time e with c - 300 < e <= c, i.e. the window closing at the event), cheap side 0.05 to 0.50 at 180 s,
fill at the next candle's ask, hard limit 0.50, held, C = 10, fee 7% x C x p x (1-p) rounded up, 8 series, N 728,734, z bar 5.27.

| window | n | win | avg fill | payoff | PF | PF x1.2 | mean c/contract | day z | control PF (n) | event minus slot control |
|---|---|---|---|---|---|---|---|---|---|---|
| W1 08-06 to 09-04 | 283 | 18.0% | 15.0c | 5.46 | **1.20** | 1.18 | +2.18 | +1.25 | 0.86 (4,772) | +5.0c, z +2.42 (261 used) |
| W2 09-05 to 10-04 | 334 | 15.9% | 16.4c | 4.71 | **0.89** | 0.88 | -1.41 | -0.84 | 0.84 (5,968) | -1.9c, z -1.09 (264 used) |
| W1+W2 | 617 | 16.9% | 15.8c | 5.03 | 1.02 | 1.01 | +0.24 | +0.19 | | net +$14.55 at 10 contracts |

FALSIFIED by the registered rule (PF under 1.5 in W1 and in W2). Not NOT_ENOUGH_DATA overall (617 trades against 150). W3 stays unread.
**Event versus baseline:** the cheap side in the same series, 15 minute slot and weekday class WITHOUT an event has PF 0.84 to 0.86, so the
cheap side loses by itself and the event windows earn about 5c a contract more in W1 and about 2c less in W2. The difference is z +2.42 in W1
and z -1.09 in W2: not an event effect that persists. By class W1 crypto looked strong (PF 2.50, diff +14.8c, z +4.4; HYPE 2.91, BNB 2.15) and W2 crypto
is PF 0.93, diff +1.2c, z +0.4 (BNB 0.50); metals are the reverse (W1 PF 0.59, W2 0.64 at z -2.8 against control). Nothing reaches z 2 in both windows
in the same direction. Chance check: of about 90 W1/W2 cells reported most have |z| under 2; the ones above 2 flip.

## Fit to the prediction (registered before the score)
Right on the verdict and the profit factor (PF 1.02, inside 0.75 to 1.10). **Wrong on the shape:** win rate 16.9% (predicted 24% to 30%),
average fill 15.8c (predicted 22c to 32c), payoff 5.03 (predicted 2.2 to 3.4). The eligible cheap sides are mostly 5c to 20c longshots, not
the 25c to 30c I assumed. The win rate sits 1.1 points ABOVE the fill (16.9% against 15.8%), before fees, so the quote is about right on average.
Probability I gave of PF 1.5 in both windows (2%) and of a persistent +2c diff (4%) was not reached.

## Groups (Try A, W1 / W2: n, PF; reports, not tries)
DATA830 (CPI, PPI, jobs, GDP and PCE, retail, claims): 21 PF 2.47 / 28 PF 1.71, diff +16.4c z 1.73 / +17.8c z 2.72. **49 trades, 7 of the 8 series, still
NOT_ENOUGH_DATA (registered floor 150): and it is the one group that is positive in both windows, so it is the only line worth a forward look.**
DATA1000 (ISM, Conference Board): 7 / 8 trades, NOT_ENOUGH_DATA. FOMC: 0 / 2 trades. EIA: 11 PF 0.41 / 10 PF 0.33, diff -4.9c / -17.9c (z -3.05 in W2), NOT_ENOUGH_DATA.
US open: PF 1.35 / 0.64. US close: PF 2.04 / 0.41 (flips). London open: 0.88 / 1.96. Asia opens: 0.88 / 0.73.
Per series Try A, W1 / W2 PF: silver 0.67 / 0.59, copper 0.27 / 0.68, WTI 1.12 / 1.22, HYPE 2.91 / 1.66, BNB 2.15 / 0.50, EURUSD - / 0.27, GBPUSD - / 1.57, USDJPY - / 1.88
(FX pairs only have W2 and W3 data; n 19 to 24 each).
**Try B (event in the first 5 minutes of the window; information only, no verdict):** W1 n 245 PF 1.13 (diff +4.9c z +2.12), W2 n 301 PF 0.86 (diff +2.4c z +1.08): same
pattern, no verdict, nothing to carry.
(A group row with 2 trades shows a nonsense z of -1.4e16: a day-cluster artifact on n = 2, ignore.)

## Counts the owner asked for
- **Events per month (calendar):** CPI 1, PPI 1, jobs 1, GDP and PCE 1, retail 1, ISM 2, Conference Board 1, claims 3 to 5, EIA 4 to 5, FOMC 0 or 1
  (Sep, Oct, Dec): about 15 to 18 data and Fed event times a month; NYSE open, NYSE close, London, Tokyo and Hong Kong opens about 21 each (105).
- **Qualifying windows (Try A):** 1,119 eligible trades in 89 days on 8 series (W1 283, W2 334, W3 502), about 375 per 30 days; 981 in Try B.
- **Months to 150 trades:** pooled 0.4; macro (releases, ISM, Conference Board, FOMC, EIA) 3.1; DATA830 alone 6.0; EIA 11.5; ISM and Conference Board 16.6;
  FOMC about 89 (never on this rate). A forward re-score of the same frozen code (no recorder needed) would add 150 pooled trades in about 2 weeks, 150 macro
  trades in about 3 months (early February 2027), and 150 data-release-only trades in about 6 months.

## Streaks (`src/scalper/streaks.py` at the observed 16.9% win rate, 617 trades)
Empirical longest losing run 41; longest winning run 4. Over 100 trades: longest losing run mean 18.0, median 17, 95th percentile 29, 99th percentile 38;
chance of at least one run of 10 straight losses in 100 trades 97.8%. Independence assumed; losses cluster (one open hits several series), so a floor.
**Worst single loss** at the 0.50 limit: $5.18 at 10 contracts (500c + 18c fee), $2.59 at 5 contracts; the largest realised fill was within the limit by construction.

## Disclosures
- Interpretation of the trigger (closed end, e = c; every event is on a quarter hour) is in the registration; the owner's "look within 2 minutes after" never fires on this calendar.
- UK, Japan and Hong Kong holidays are not removed, ISM and Conference Board dates are by rule, claims dates are by rule, FOMC has no Dec 9 verification; same in every window.
- BLS (403) and ISM / Conference Board (301) pages were not read by this worker; the Federal Reserve page was and agrees with the FOMC rows.
- Control mean falls back to the slots +- 2 hours when a slot has fewer than 10 control trades (daily opens and closes), so for those groups the diff is partly a time-of-day comparison.
- The `score` command ran once; `data/event1_score.json` makes a second run refuse.
- N: 8 tries, running count about 728,726 -> 728,734.
