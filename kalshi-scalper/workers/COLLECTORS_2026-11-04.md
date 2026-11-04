# Forward data collectors, ranked (DRAFT for the owner; nothing built, nothing merged, 2026-11-04)

Asked by main: at most 3 collectors that would turn a NOT_ENOUGH_DATA family into a testable one within 30 to 60 days; for each the expected events per month, the date it becomes testable, and the Actions-minute cost. The owner decides. All numbers are my estimates from today's results (marked E); none was measured on a runner. Public repo assumed (Actions minutes free); every collector would be recorder-only files on a branch cut from origin/main, public keyless data, no key, no order, quote-data branch.

## 1. NHL goal and assist ladder quote recorder (KXNHLGOAL, KXNHLAST), at the look
- Why: the only cheap-side pool that came out positive on fresh data (NHLALL1 goals +6.8c, cap 2, 150 trades; audit central estimate about +2c to +3c; assists +6.4c but H2 flat; first goal and points negative; NFL, MLB, soccer did not replicate). It failed to be decisive only on history and data availability: only 14 of 115 new games had a usable ladder at the look (in-game volume made the universe unreliable, NHLAUDIT1), and the clean out-of-sample test is the 225 frozen post-2026-10-03 events, which need owner approval.
- What it records: for each NHL game the full 1+ rung ladder (bid, ask, sizes, volume) at 120, 90, 60, 30 and 5 minutes before puck drop (ESPN start time), plus the ESPN box score goals and assists the next day, so the universe is fixed by pre-puck-drop volume and not by in-game volume.
- Events per month (E): about 120 to 130 NHL games a month in season; about 14 rungs and 40% usable ladders; about 100 cheap trades a month at cap 2, so 150 trades in about 45 days.
- Testable: one frozen read (cuts 2.75 and 3.66, E 3.9085 and m 0.3 for goals; E 4.21 for assists) on about 2026-12-20 to 2027-01-05, in addition to the 225 frozen events if the owner opens them (that read is available today without any new collector).
- Cost (E): one job per game window, 6 runs a day of about 8 minutes, about 1,400 Actions minutes a month; or 3 runs a day: about 700.

## 2. Keyless Yahoo 1-minute reference recorder for FX, WTI, natural gas (and silver) (RECPLAN1 item 1)
- Why: FXREF1, HRLYFX1 and COMDAY1 failed only because no free minute reference covers the pre-cut history (Yahoo keeps about 7 days of 1-minute data). The reference is perishable, so the first run backfills 7 days.
- What: add an adapter in scripts/ref_adapters.py (the RECREF recorder) for 7 symbols (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, CL=F, NG=F, plus SI=F), 1-minute bars, one daily run; Kalshi candles can be fetched later, only the reference must be recorded.
- Events per month (E): FXREF1 treated trades 50 to 200 a month; hourly silver/WTI ladders about 100 treated trades per 30 days at the 10-minute look (HRLYFX1 estimate).
- Testable: FXREF1 registered read on or after 2026-12-15 (about 45 days of reference); P(pass) under 3% (model-vs-quote failed 8 times); worth building mainly because it is near-free.
- Cost (E): 0 extra minutes if it rides the existing RECREF job; 30 to 60 minutes a month as a separate daily job.

## 3. Daily ladder watchlist extension for STRESSDAY1 (config-only, RECDAILY)
- Why: STRESSDAY1 had only 10 stress days against the 25 required; entries were enough (399 stress-day entries). The binding limit is days, not trades.
- What: add the Financials and Commodities daily ladder series to workers/RECDAILY_WATCHLIST.json (a data file, no code), so quotes at the look and entry timestamps are stored on quote-data.
- Events per month (E): about 340 entries a month; stress days about 7 to 8 a month (a third of trading days).
- Testable: 25 stress days and 150 stress entries in about 55 trading days: late January 2027. P(pass) low (cheap side loses everywhere in the pooled record), but the cost is nearly zero.
- Cost (E): 0 to 720 Actions minutes a month depending on whether RECDAILY needs extra runs.

## Considered and not ranked
- OUT1 NBA/NHL injury polling (ESPN injuries endpoint with timestamps from 2026-11-05): 15 to 60 treated a month, 3 to 10 months to 150; the quote may already carry an Out status public days earlier. Not within 60 days.
- EARNPR1 forward (events 2026-10-04 to 2026-12-15, read 2026-12-16): about 30 and 50 treated trades; information only, no collector needed (Kalshi candles and EDGAR are fetched after the fact).
- WXENS1/WXLOW1, RAINCAL: already recorders; see RECWATCH1_REPORT.md for their health and RECPATCH1 (branch claude/v2-recorder-fixes1).
- TRUMPTOPIC1 snapshot: measured take-up 0 to 2 a month; not worth a collector.
- Soccer goalscorer (XI1): negative on 94 matches; not worth building.

## Honest summary
Only collector 1 addresses a result that was positive on fresh data, and even that lead is small (audit: about +2c to +3c) and has failed to replicate in NFL, MLB and soccer. Collectors 2 and 3 are near-free options on negative priors. Opening the 225 frozen NHL events (owner approval) answers the NHL question faster than any collector.
