# ECONNEW1 result (Strategy Research V2, 2026-10-31, research only)

Registered first: `workers/ECONNEW1_REGISTRATION.md` (commit d894e78, before any claims candle was scored) and its Amendment 1 (49e44a2). Ledger check: `workers/ECONNEW1_LEDGER_CHECK.md`.
Code `src/scalper/econnew1.py`; raw output `data/econnew1_result.txt` (local only, data/ is not committed).

## Angle (a): weekly initial jobless claims strikes (KXJOBLESSCLAIMS) against a persistence model: FALSIFIED

Rule as registered: forecast f = half last print + half 4 week mean (FRED ICSA), empirical error over 104 weeks, buy the side whose model probability beats the quote by 5c, quote 24 hours before the release,
10 contracts per order, hold to settlement, fee 7% x C x p x (1-p) rounded up per order. Universe 262 strikes (model probability 0.10 to 0.90) on 62 weekly releases, 2025-06-12 to 2026-10-29.
Entries: 151 by quote, 4 by assumed-spread trade price.

| Window | Trades | Releases | PF | Mean per contract | Release-clustered z | Loss rate |
|---|---|---|---|---|---|---|
| Discovery (to 2026-03-31) | 79 | 30 | 1.55 | +8.60c | +1.29 | 39% |
| Validation (2026-04-01 to 10-16) | 73 | 27 | **0.57** | -8.70c | -1.62 | 70% |
| Frozen holdout (2026-10-17 on; 2 releases) | 3 | 2 | 3.44 | +27.37c | +0.95 | 33% |
| Pooled discovery + validation | 152 | 57 | 1.02 | +0.29c | +0.07 | 54% |
| Pooled, fees x1.2 | 152 | 57 | 1.00 | +0.03c | +0.01 | 54% |

Information only: edge 0.03: 179 trades, PF 0.89; edge 0.08: 122 trades, PF 0.83; quote-mode only (all windows): 151 trades, PF 1.08, z +0.29; quoted spread at most 10c: 131 trades, PF 0.98.
Brier on 246 markets with a price: model 0.1837, market 0.1725 (the market is better calibrated than the model). Look-ahead control: FRED value against Kalshi's first print, mean absolute difference 1,309 claims on 55 weeks (under the 3,000 void line).

**Verdict `FALSIFIED`** (validation PF 0.57 is under 1.5; pooled PF 1.02, z +0.07, far under the deflated z bar 5.27). The discovery PF of 1.55 clears 1.5 and does not survive the next half: the usual shape. The holdout holds 3 trades, which cannot support a claim either way.
Prediction before the run: PF 0.7 to 1.1, z between -2 and +1; pooled PF 1.02 and z +0.07 are inside it.

**Disclosure: run 1 was seen.** The first run (after the registration was pushed) used the parser that reads `close_dollars` and so dropped every historical-era quote: 24 entries, discovery 0, validation 21 trades PF 2.44, verdict NOT_ENOUGH_DATA.
Amendment 1 (pushed before run 2) records it; run 2 fixed only the field name. The verdict is run 2's. The run 1 validation PF of 2.44 on 21 trades came from the live-era releases (since 2026-08), which are part of run 2's 73 validation trades.

## Important correction found on the way: CPI1 and MENT1 were scored on a parser bug

Kalshi's LIVE candles name the OHLC fields `close_dollars`; its HISTORICAL candles (`/historical/markets/.../candlesticks`) name them `close` and the volume field `volume`. `cpi1.py` (history path) and `ment1.py` read only `close_dollars`.
Checked on a raw historical candle set for CPI-24JUN-T0.1 (market closed 2024-07-11): 22 of 22 hourly candles have a bid and an ask. So:
- CPI1's "only 29 headline and 19 core markets have a quote 24 h before" is wrong, and the stated cause of its NOT_ENOUGH_DATA (7 trades on 2 releases) is a parser artifact. The registered CPI1 rule has not been validly scored on its roughly 50 releases.
- MENT1 (71 events, 268 trades, NOT_ENOUGH_DATA) had its quotes only from the live era for the same reason, so its event count is understated.
- Other workers that parse historical candles with `close_dollars` should be grepped (the three files that use both are `cpi1.py`, `ment1.py`, `econnew1.py`; this session did not review other workers' parsers by hand).
- The CAL power check and EVT1 used 1 minute live-era and local candles, not this path; not affected as far as I can tell.
Recommendation: the main session decides whether to rerun CPI1 as registered (refetch candles with a `pick()` that reads both names; its result file blocks a second run by design, so this needs approval) and core PCE as a REWORD with the Cleveland core PCE nowcast.
A caution that applies to every historical quote: a quote on an empty book can be very wide (bid 0.08 / ask 0.97), and quote-based fills at 1 contract are assumptions, not fills.

## Decisions on the other angles (details in the ledger check)

| Angle | NEW / REWORD | Verdict | Date the bar could be met |
|---|---|---|---|
| (a) weekly claims vs persistence of ICSA | NEW | **FALSIFIED** (scored once, run 2) | none needed |
| (b) CPI strikes vs Cleveland nowcast | REWORD of CPI1 | **REOPENED, RUNNABLE** (CPI1's cause was a parser bug); not scored here | any time, on approval |
| (b) core PCE vs Cleveland core PCE nowcast | REWORD of CPI1 on a new series | RUNNABLE (26 releases, spread 9c); not scored here | any time, on approval |
| (b) payrolls / unemployment vs any forecast | NEW | NOT_RUNNABLE: no free consensus or nowcast (ADP and consensus are not public; the Cleveland Fed has no payrolls nowcast) | none |
| (c) FOMC decision vs fed funds futures | NEW | NOT_ENOUGH_DATA: a public source exists (Atlanta Fed Market Probability Tracker, `mpt_histdata.xlsx`, daily from 2023-03-29, no key; CME FedWatch is not an API), but there are 30 meetings and only a handful with real uncertainty | about 8 a year; no date before 2030 |
| (d) release-day price path before the release | REWORD of the price-pattern family | NOT_RUNNABLE: no public consensus to drift against | none |
| (e) Treasury 15 minute series around 8:30 ET | REWORD of YIELDMAKE | NOT_RUNNABLE: 12 days, 25c spread, taker entry needs about 73% | YIELDMAKE re-look about 2026-11-30 |
| (f) weekly AAA gas ladder vs RBOB futures | NEW (GAS1 had no futures input) | RUNNABLE, not scored: 142 weekly events, volume about 18,000 a strike, Yahoo `RB=F` public; about 1,000 candle downloads under the rate limit did not fit the time cap | proposed ECONNEW2 |

Tries: one scored angle (a), registered rule, N +3 (the two information thresholds are shown, not tried): running count about 728,680 (z bar about 5.27). Nothing else was scored.

## Upcoming releases (next 30 days, US Central)

Nov 4 EIA 9:30; Nov 5 claims 7:30 (KXJOBLESSCLAIMS-26NOV05 open now, spread about 5.5c); Nov 6 jobs 7:30; Nov 10 CPI 7:30; Nov 12 claims; Nov 13 PPI 7:30; Nov 17 retail sales 7:30; Nov 19 claims;
Nov 25 GDP and PCE 7:30 and claims (Thanksgiving week, the Thursday row is unverified). No FOMC (next Dec 9). Source `studies/EVENT_CALENDAR_2026.csv`; claims dates are a rule, not read from a DOL page.

## Proposed README section (for the lead to paste; README.md not edited)

### ECONNEW1, economic-release markets: ledger check and weekly jobless claims against a persistence model (worker, 2026-10-31; `workers/ECONNEW1_LEDGER_CHECK.md`, `ECONNEW1_REGISTRATION.md` with amendment 1, `ECONNEW1_RESULT.md`, `src/scalper/econnew1.py`)

Owner opened economic releases as new research. Ledger check: CPI1, EVT1 macro cells, L10/N4, CAL, DAILY2, INX1, the Treasury 15 minute series and NEWH10 I2 are the existing record; weekly claims, payrolls, unemployment, core PCE, GDP, retail, ISM, JOLTS, housing starts, FOMC decision and the weekly gas ladder were untested.
Kalshi's economic series have deeper history than assumed (claims 62 weekly events from 2025-06; payrolls 43; unemployment 63; core PCE 26). **Weekly claims strikes (KXJOBLESSCLAIMS) against half the last ICSA print plus half the 4 week mean, quote 24 h before the release, 5c edge: FALSIFIED.**
262 strikes on 62 releases, 152 trades on 57 releases in discovery and validation: discovery PF 1.55 (79 trades), validation PF 0.57 (73), pooled PF 1.02 and release-clustered z +0.07, fees x1.2 PF 1.00, holdout 3 trades. The model's Brier (0.1837) is worse than the market's (0.1725).
**Correction:** the first run used a parser that read `close_dollars`, which only live candles have; historical candles use `close`. The same bug sits in `cpi1.py` and `ment1.py`: CPI1's "quotes missing before 2026-08" was a parser artifact (a 2024 CPI market has a bid and ask in 22 of 22 hourly candles), so CPI1 was never validly scored and MENT1's event count is understated. Rerunning CPI1 as registered, and core PCE against the Cleveland core PCE nowcast, are both RUNNABLE and wait for the lead's approval. Payrolls and unemployment have no free forecast source (NOT_RUNNABLE); FOMC against the Atlanta Fed Market Probability Tracker (public xlsx, daily from 2023-03) has too few uncertain meetings (NOT_ENOUGH_DATA, years); Treasury 15 minute and release-day drift stay NOT_RUNNABLE. Weekly AAA gas against RBOB futures is RUNNABLE and unscored (proposed ECONNEW2). N +3, running count about 728,680 (z bar 5.27).
