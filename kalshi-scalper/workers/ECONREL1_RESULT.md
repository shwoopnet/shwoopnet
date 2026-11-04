# ECONREL1 result (Strategy Research V2, 2026-11-04, discovery lane, research only)

Verdict: **DUPLICATE, NOT_RUNNABLE (and NOT_ENOUGH_DATA by census).** No registration written, no candle fetched, no outcome joined, no rule scored. N +0.

## Duplicate check
Source: row 11 of `workers/SCOUT1_REGISTRATION.md`. The item (pre-release look at cheap bracket asks 3c to 30c against a structural reference, model probability >= 3x ask, hard limit 0.30, held) is the NOWCAST1 rule (`workers/NOWCAST1_REGISTRATION.md`, result `NOWCAST1_RESULT.md`, 2026-11-03) on CPI, core CPI, core PCE and GDP, already run: 12 development trades on 10 release dates, PF 1.00, one win carries all the profit, NOT_ENOUGH_DATA; 14% of release-series (26% from 2025) produce a trade. Both-sides versions: CPI1 rerun (47 releases, PF 1.11, FALSIFIED), ECONNEW2 (core PCE, NOT_ENOUGH_DATA). Persistence reference: ECONNEW1 (claims, FALSIFIED). Calendar-driven 15 minute series: EVENT1, EVENT830, USWEEP1 to 3 (different object). FEDIMPL1 and PUBINDEX1 are other ladders.

## What row 11 adds that is not covered
Payrolls (43 events), unemployment (63), ISM (14), ADP (19), housing starts (6). Reference status, all checked in ECONNEW1 and NOWCAST1: no keyless consensus or nowcast with history (the Cleveland Fed publishes none for jobs; consensus is paid; Philadelphia SPF is quarterly and coarse; ALFRED needs a key for vintages). The only keyless reference would be a persistence-plus-surprise model from the last print alone, which is what the ladder already prices (unemployment moves 0.0 or +-0.1 in most months; the brackets are 0.1 wide). It has no information the retail price lacks, so it is not a counterparty finding, only a restatement of the longshot calibration already seen in NOWCAST1 (win 8.3% vs 7.8c).

## Census (listings only, no candles, frozen cut 2026-10-03T16:00Z untouched)
Counts from the scout listing: payrolls 43 events, unemployment 63, ISM 14, ADP 19, housing starts 6 = 145 release-series with only a persistence reference; with the NOWCAST1 cheap-ratio rate (14% to 26% of release-series trade) that is 20 to 38 expected trades before the holdout is removed, 13 to 25 in development. Adding the four already-tested series (130 release-series, 12 trades) does not change it. Against the bar of about 150 expected trades or about 100 pooled releases with a real reference: fails on trades by a factor of 4 to 7.

## Months to go
Release-series per month on these markets about 8 (CPI, core CPI, core PCE, payrolls, unemployment, ADP, ISM x2, GDP 0.33, housing starts 1, minus overlaps). At 14% to 26%: 1.1 to 2.1 trades a month. 150 trades from the existing roughly 35 needs 55 to 105 months (about 4.5 to 9 years). Not reachable inside any useful horizon.

## Conclusion
Duplicate in spirit of NOWCAST1/CPI1/ECONNEW1; the new series have no outside reference; the sample cannot reach 150. No forward line registered beyond NOWCAST1's. N +0 (running about 730,379).
