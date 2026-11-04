# RECWATCH1: do the recorders feed the forward reads? (audit at 2026-11-04 13:20 UTC, 7:20 AM CST)

Read-only support audit, N +0, no strategy, no scoring, no workflow or live code touched. Sources: `git fetch origin quote-data main perp-data` (history since 2026-10-20 only; the `quote-data`
tip tree is empty by design, so files were counted from the commits, `git log --raw`), the public Actions run list for shwoopnet/shwoopnet, `.github/workflows/record-*.yml` and
`scripts/record_*.py` on origin/main, `workers/FORWARD_CALENDAR.md`, `RECPLAN1_PROPOSAL.md`. Blobs were not downloaded, so row counts are NOT given: sizes and file counts are.
(Raw gz sizes are in bytes of the compressed file; a header-only file is about 110 to 180 bytes.)

## Headline

Every recorder is on main and pushing. The failure mode is **GitHub dropping scheduled starts**, which hits the short-cadence recorders (daily, ref, wxens, rain) far harder than the
4 hour back-to-back ones (quotes, book, R6, deribit, sportspre) that have a second hourly trigger. Verdicts:
- **OK (4 hour pattern, 67 to 100% of 4 h slots):** quotes, book (KXBTCD), book15r6 (R6), deribit, sportspre.
- **At risk:** RECDAILY (2 of ~24 expected runs per 12 h), RECREF (2 of ~6), WXENS1/WXLOW1 (2 of ~12; zero runs inside any look hour so far), QUOTE2B count (book/ coverage).
- **Failed / blind so far:** RAINCAL (no scheduled run has ever landed in a city's 6 to 8 AM window; the only real data are two manual runs and today's manual run lost to a GitHub push 500).
- **Not a dependency:** perps (`perp-data`, hourly cron, 3 to 7 commits a day of 24; no forward read uses it).

## 1. Files per recorder, last commit, volume (UTC)

| Dir (branch quote-data) | Workflow / cron | First data | Last commit | Commits per day (job-level) | Compressed bytes per day (recent) |
|---|---|---|---|---|---|
| quotes/ (RECORD1, MM1, ladder) | record-quotes `45 3,7,11,15,19,23` + `15 * * * *` | 10-22 | 11-04 12:19 | 4 to 6 of 6 (10-22 partial; 5 on 11-02, 5 on 11-03) | 2.3 to 8.8 MB |
| book/ (KXBTCD ladder, QUOTE2B, MAKERTAIL1) | record-book `50 3,7,...` + `20 * * * *` | 10-29 | 11-04 12:00 | 10-30: 4, 10-31: 4, 11-01 to 11-03: 6 | 4.0 to 13.3 MB |
| book15r6/ (R6: GF1/2, DEPTH1, BOOKCH1, MAKER5, L1Q1) | record-15m-book `5,35` + `20,50`, stops 11-13 23:59 | 10-30 | 11-04 12:02 | 5, 4, 6, 5, 6 (10-30 to 11-03) | 8.7 to 40.2 MB |
| book15/ (R2, old) | superseded | 10-29 | 10-29 20:00 | 1 | stopped, replaced by R6 |
| deribit/ | record-deribit (same 4 h pattern, stop 12-31) | 11-02 | 11-04 12:01 | 4, 6, 4 (11-02 to 11-04 12:00) | 0.7 to 1.4 MB |
| sportspre/ | record-sportspre (same pattern) | 11-02 | 11-04 12:01 | 4, 6, 4 | 7 to 38 KB (live games only) |
| raincal/ | record-rain `4,24,44 11-15` + `14,34,54 11-15` + `50 17` | 11-02 11:52 | 11-03 22:36 | 3 on 11-02, 5 on 11-03 | 4 to 8 KB (see 3) |
| daily/ (RECDAILY) | record-daily `7,37 * * * *` | 11-04 01:37 | 11-04 07:58 | 2 (expected ~46/day) | ~2.4 KB quotes + 0.2 to 1.4 KB results per run |
| ref/ (RECREF) | record-ref `23 */2 * * *` | 11-04 02:25 | 11-04 12:16 | 2 (expected 12/day) | ~5 KB quotes + 4 KB refvals per run |
| wxens/ | record-wxens `12 * * * *` | 11-04 02:19 | 11-04 10:53 | 2 (expected 24/day) | `runs/` csv only, ~180 bytes per run |
| perps (branch `perp-data`) | record-perps `7 * * * *` | 10-21 | 11-04 05:59 | 3 to 7 (24 expected) | tiny |

Workflows created: daily, ref, wxens 11-03 21:18 UTC; rain, deribit, sportspre 11-01 22:47 UTC. So daily, ref and wxens have under one day of history, the 14 day table the brief asked for
does not exist for them. Missed 4 hour slots (gap 8 h between commits instead of 4): book 10-29 12:00, 10-30 12:00, 10-31 04:00 and 12:00; R6 10-30 08:02, 10-31 04:02 and 16:03, 11-02 12:02;
quotes 10-23 00:13 (12.1 h), 10-25 04:08, 10-26 04:12, 10-28 04:05, 10-31 04:13, 11-02 16:05; deribit and sportspre 11-02 16:01. Today 11-04: book, R6, deribit, sportspre each show a 4 h gap
at 04:00 to 08:00 only because one slot was committed late, not missed (4 commits by 12:00 where 4 to 5 are due).

## 2. Per recorder: cadence, actual, gaps, error markers

| Recorder | Expected cadence | Actual (last 7 d, or since start) | Gaps over 2x cadence | Last non-empty data | Error markers |
|---|---|---|---|---|---|
| RECDAILY | every 30 min | 2 runs, both success: 01:37 (slot 01:30; 109 quote rows, 134 result rows) and 07:58 (slot 07:30; 107 quote rows, 2 result rows) | gap 6.4 h, then 4 h nothing | 11-04 07:58, 20 series polled, 40 calls | n429 0, n_errors 0, clock skew -22.6 and -24.4 s (the quote clock is ~23 s off the server; fine for 30 minute looks) |
| RECREF | every 2 h (`:23`) | 2 runs, success: 02:25 and 12:16 (slot 02:00 and 12:00) | 9.8 h gap | 11-04 12:16 | n429 0, n_errors 0, **parse_failures 3 on both runs** (9 series, 8 refs polled), so one ref source and part of a series is parsing wrong every time; refvals rows 156 and 157 |
| WXENS1 / WXLOW1 | hourly, but only the 07:00 and 10:00 local STANDARD hour of each city matters (12 to 15 UTC and 15 to 18 UTC for ET to PT) | 2 runs: 02:19 and 10:53, both `cities_due 0` | **no run at 11:12, 12:12 or 13:12 UTC** (checked 13:17) | nothing yet (`ens_rows` 0 because no city was due) | n429 0, n_errors 0, `server_date_header` empty on both rows. **The Open-Meteo ensemble call has still never run on a runner**, and the ET 07:00 look for 11-04 (12:00 to 12:59 UTC) was already lost |
| R6 (`book15r6`) | trigger every 15 min, one job at a time, 4 h blocks | 30 job-commits since 10-30 00:02 | four 8 h gaps (above) | 11-04 12:02 | none checked in files; calendar says 68% coverage, on track for DEPTH1 |
| QUOTE2B / MAKERTAIL1 (`book/`) | 6 x 4 h jobs a day + hourly backstop | 32 job-commits since 10-29 | four 8 h gaps, 4 h at 11-04 08:00 | 11-04 12:00 | none checked in files |
| RECORD1 / MM1 (`quotes/`) | same pattern | 58 job-commits | six gaps of 8 h or more, one of 12.1 h | 11-04 12:19 | run 55 (started 11-02 20:52) concluded `failure` and run 56 (11-03 02:55) `cancelled`; the 4 h run 57 then covered 04:00 to 08:00 |
| RAINCAL | 6 to 8 AM local standard window per city, 30 triggers a day inside 11 to 15 UTC | 9 runs since 11-01: 3 manual (`workflow_dispatch` 11-02 11:52, 11-03 11:17, 11-04 11:18), 6 scheduled | **0 scheduled runs inside 11 to 15 UTC in three days**; scheduled runs landed at 18:15, 18:27, 20:38, 20:47, 22:35, 00:05 UTC, all outside every city's window | 11-03 11:17 quotes 675 bytes, pop 1,689 (a few markets) | header-only files (quotes 135 B, pop 114 B) on every off-window run. **11-04 11:18 manual run failed at "Commit and push": three `remote rejected (Internal Server Error)` from GitHub (a GitHub 500, not a script error), so today's data is lost** |
| DERIBIT, SPORTSPRE | 4 h pattern | 14 job-commits each since 11-02 04:01 | one 8 h gap (11-02 16:01) | 11-04 12:01 | none |
| perps | hourly | 3 to 7 commits a day | up to ~20 h | 11-04 05:59 | n/a, no forward read depends on it |

## 3. Forward reads due in the next 30 days (to 2026-12-04), data precondition and status

| Cal. row | Read, date | Needs | Where we are | Status |
|---|---|---|---|---|
| 8 | RECORD1 read, ~11-04 to 11-06 | 300 qualifying trades on at least 10 dates, clock within 100 ms | 294 on 13 dates at 11-03 07:01 CT (calendar). `quotes/` pushed through 11-04 12:19 | **On track** (manual crossing; the guard refuses below 300). Clock check is a separate pass condition and `clock_ok` was False earlier; a failed clock voids it |
| 11 | MM1 AUTO at 300 gold windows, ~11-05 to 11-07 | 300 usable gold 15 min windows | 192 at 11-03 07:01 CT, ~50 a day, about 108 to go | **On track** by ~11-06, but a missed 4 h `quotes/` slot costs about 8 windows, and gold is shut Fri 17:00 to Sun 18:00 CT, so it can slip to 11-09 |
| 12 | MAKER5 and L1Q1, AUTO from 11-06 00:00 | 300 usable and 300 posted windows each | posted 1,171 and 423, usable 1,400 and 1,434 (calendar) | **On track**, gates already met |
| 4, 16 | BOOKCH1 read, ~11-12 (latest 11-14 00:00) | 150 pooled primary trades, at least 7 days | frozen 11-04 00:00, 0 trades; alternative ~6 to 8 a day | **At risk**: R6 coverage loses windows in each 8 h gap, the 7 day minimum cannot be met before 11-11 even with no gap, and no scorer entry in AUTO |
| 17 | QUOTE2B, from 11-12 | 300 usable hourly closes | 80 usable, 92 recorded at 11-03; ~25 usable a day, so ~300 on **11-12 to 11-20** | **At risk**: only one day of margin at the best coverage, the guard refuses and logs one line below 300. Each missed `book/` slot is 4 closes |
| 18 | MAKERTAIL1, 11-12 | 150 pessimistic fills on EACH side, closes from 11-03 16:00 | ~36 a day combined; each side needs 150 | **At risk**: needs ~8 days combined if the side split is even, and side fills are unequal (tails); likely NOT_ENOUGH_DATA on one side by 11-12 |
| 15 | dated L1 reads 11-12 16:00 | `data/fresh.sqlite` via `fresh_update`, 30 fresh days or 12-01 for `fwd_reads read` | not a recorder read (Kalshi candles); recorders irrelevant | Outside this audit |
| 20, 21 | GF1, GF2, DEPTH1, AUTO 11-14 02:00 | 300 signals / 300 windows per market | R6 coverage 68%, calendar says on track | **On track**; R6 stops by itself 11-13 23:59, an 8 h gap in the last two days directly removes windows |
| 25 | RAINCAL city freeze, ~11-16 | each tested city needs at least 7 of the first 14 UTC days (11-02 to 11-15) with median spread known | real data only 11-02 and 11-03, Eastern cities only, one manual pass each; 11-04 lost | **Failing**: Central, Mountain and Pacific cities have zero in-window passes, 12 days left, scheduled starts do not land in window |
| 29 | MKTTIME1-F interim, ~11-24 to 12-03 | 100 gold entries 20:00 to 24:00 CT | 14 | Not a recorder read; recorder irrelevant |
| 1, 3, 14, 28, 33, 35, 36 | USWEEP1 (daily favourites), NOWCAST1 looks 11-09 13:30, 11-24 13:30, 12-09 13:30, BARRIER1 12-03 look, FEDIMPL1 12-08 look | RECDAILY quote at the look hour (1 to 24 h before close; NOWCAST: 24 h before the release; FEDIMPL1: the business day before FOMC, live candles on the day) | RECDAILY ran twice in 11 h (a 6.4 h gap, then 4 h) | **At risk**: a 30 minute cadence that gives one run per ~5 h cannot guarantee a quote inside a one hour look. NOWCAST and FEDIMPL1 are information-only and a lost look cannot be recovered, as the calendar notes |
| (new) | WXENS1/WXLOW1 first look 11-05; read 2027-02-28 or 300 trades | ~7 trades a day pooled, one snapshot per city per look hour | 0 of ~3 morning looks recorded so far; `ens_rows` unproven | **At risk**: each look is one hour per city per day and one dropped hourly start loses it permanently (no second trigger, unlike every 4 h recorder) |
| 37 to 40 | DERIBIT, SPORTS-PRE, RAINCAL reads 2027-01-01 | 150 trades each, stop dates 12-31 | recording with the 4 h pattern (rain: see 25) | Deribit, SPORTS-PRE: **on track**. RAINCAL: **at risk**, same cause |

Guards that would refuse for lack of data today: RECORD1 (294 of 300), MM1 (192 of 300), QUOTE2B (80 of 300), BOOKCH1 (0 of 150, under 7 days), MAKERTAIL1 (under 150 per side),
RAINCAL city freeze (fewer than 7 usable days in every non-Eastern city), WXENS1 (nothing yet to count). Four of those fail only by time and are fine if recording continues
(RECORD1, MM1, MAKER5/L1Q1, DEPTH1/GF1/GF2).

## 4. Recommendations (nothing was changed; only the owner or main can dispatch a workflow or edit one)

| # | Recorder | Finding | Action for owner / main | Urgency |
|---|---|---|---|---|
| 1 | RAINCAL | No scheduled run has landed inside a 6 to 8 AM window in 3 days; today's manual run died on GitHub's 500 | **Run `record-rain` by hand (workflow_dispatch) now and at about 13:30, 14:30 and 15:30 UTC today**, then each morning 11:15, 12:15, 13:15, 14:15, 15:15 UTC until a trigger is found that lands in window. Optional: add a third trigger group, or a retry loop (push step repeats only 3 times a second apart; GitHub 500s need a longer wait) | **Today** (Central, Mountain and Pacific cities have none) |
| 2 | WXENS1 / WXLOW1 | Cron `12 * * * *` produced 2 runs in 11 h; ET 07:00 look for 11-04 already lost; ensemble call never exercised | **Run `record-wxens` by hand at 13:12 to 13:50 UTC (CT 07:00 look), 14:12 (MT), 15:12 (PT) and again 15:12 to 15:50 UTC (ET 10:00)**, then check `wxens/runs/2026-11-04.csv` for `n429` and `ens_rows`. Add a second trigger offset by 20 to 30 minutes as the 4 h workflows did | **Today and every look morning until 11-05 first look** |
| 3 | RECDAILY | 2 runs per ~11 h instead of ~22; the 24 h before CPI (11-09 13:30 UTC) look needs a run in that hour | One manual dispatch around **2026-11-09 13:00 to 14:00 UTC** for NOWCAST1 look 1 (information only), plus a second cron (`22,52`) or a note to dispatch before each look date in rows 14, 28, 35, 36 | 11-09 |
| 4 | RECREF | 2 runs, **parse_failures 3 per run** every time | Owner or main: open the run log, see which of 3 refs or series fails to parse; no dispatch needed | This week |
| 5 | QUOTE2B (`book/`) | 80 of 300 usable closes at 11-03, no slack to 11-12 | Keep the hourly backstop; consider a manual dispatch of `record-book` whenever the latest `book` commit is more than 5 h old (RECFEED flags at 8 h). Decide on 11-10 whether to move the read date | 11-10 |
| 6 | MAKERTAIL1 | Per-side 150 fills probably unmet by 11-12 | Expect NOT_ENOUGH_DATA on a side; let the read wait for the later of the two conditions (already registered) rather than moving the date | 11-12 |
| 7 | BOOKCH1 / R6 | Dependent on R6 uptime; 7 day minimum cannot be met before 11-11 | No action beyond keeping R6 running; R6 stops 11-13 23:59, so an owner decision on extension is needed by 11-12 if BOOKCH1 or DEPTH1 falls short | 11-12 |
| 8 | quotes, book, R6, deribit, sportspre, perps | Fine (4 h pattern, with the hourly backstop) | None; manual dispatch only if a recorder shows no commit for 5 h | none |

Pattern to remember: a recorder that needs one run in a specific hour (RAINCAL, WXENS1, RECDAILY looks) should have 2 to 3 staggered triggers and a push retry, or it will be lost the way
the 4 hour recorders were before 10-31. A push failure (GitHub 500) deletes the pass because the data is not kept anywhere else.

## 5. Short answer for main

OK: quotes, book, R6, deribit, sportspre, perps (not a dependency). At risk: RECDAILY, RECREF, WXENS1/WXLOW1, QUOTE2B count, MAKERTAIL1 side split, BOOKCH1. Failed so far: RAINCAL.
Most urgent: (1) today 11-04, dispatch `record-rain` and `record-wxens` by hand inside the 07:00 to 10:00 local hours of the Central, Mountain and Pacific cities; (2) 11-09 13:00 UTC, a RECDAILY
dispatch for the NOWCAST1 CPI look; (3) 11-10 to 11-12, decide on the QUOTE2B (80 of 300) and R6 extension (stops 11-13 23:59) before the reads refuse.
