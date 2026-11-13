# Hourly temperature measurement: the reader as frozen (second freeze), Nov 13, 2026, 02:18Z

A cost and timing MEASUREMENT, zero tries. No list or candle of these series has landed; this reader was built from the note's text and tested only on made-up data. The first freeze (commit 3bceb4bc, reader 7572d7a1, note 8191bd32) is DEAD: Auditor B found pin 6 could be read two ways and asked for hardening; the Head of R&D ruled (reading 1; stop on a market lacking a field) and the note's Amendment 2 carries both rulings and the hardening.

| File | sha256 |
|---|---|
| `hourlytemp/hourlytemp.py` (commands `job`, `measure`) | `f443ae6016209dffd2113c552d67fa3dd3750d9ec0e5a7abb39ca224a24c9970` |
| `HOURLYTEMP_MEASUREMENT_NOTE.md` (amendments 1, 2 and 3; amendment 3 is text only, after the second build) | `3e496e1266d41551afe3710eb98a927bd0c5b45eadd5e771d81297518dca2091` |
| `hourlytemp/fixture_outputs/make_fixtures_MADE_UP_DATA.py` | `2dc43128f4a5a810b475800a37dfaa79ad5d92ebd39d2a409451c7e9344b7264` |
| `hourlytemp/INPUT_LAYOUT.md` (for the second builder; no figures) | `5eb4fdb8c74ddd9391eb94d7622a6150e2814144054a5775b1c1a802e3b54768` |

The older `hourlytemp/measure.py` and `hourlytemp/build_candles_job.py` are removed. The lists job's note (`desk_b_jobs/HOURLYTEMP_LISTS.json`, and its copy under `kalshi_pull_jobs/` on main) still names the old builder; the job itself is unchanged and the builder is now `hourlytemp.py job`.

## What it prints, what it cannot show

It prints, first, the settlement rules text of one market of each of the four series, exactly as listed. Then, for each city and each look (55, 30 and 10 minutes before the hour) over the seven fixed days, under two readings of the quote (the last candle inside the market's 60 minute life, and only a candle ending at the look): how many strikes had a quote, how many were two-sided, the median spread, the median round trip, the median one-way entry cost near the money, the share already priced at 95c or 5c and beyond, and the median ask of the nearer-certain side by distance from the money. Then the count of candles with no volume field, the share of market-minutes with a trade per city, the size at the touch on open markets per series, the number of candle requests answered whole, and one verdict: CLOSED as too costly only if both readings put every one of the twelve city-and-look medians above 4c; NOT closed only if both readings find one at 4c or less; otherwise not decided. It cannot show whether any rule makes money (no result field is read, and the fixtures carry a made-up result to prove it is ignored), how any outside reading relates to the settled value (none is read), depth beyond one level, or whether a carried quote could have been paid. A NOT closed verdict approves nothing: any rule would need its own card, registration and try.

## Fixtures (all made up, whole cents) and what each must print

| Fixture | Input case | Carried | Exact | Verdict or stop |
|---|---|---|---|---|
| `closed` (spread 8c everywhere, one-way 6c) | case_03 | closed | closed | CLOSED |
| `not_closed` (Miami at 10 minutes 2c wide, one-way 3c) | case_06 | not closed | not closed | NOT closed |
| `boundary_4c` (New York at 30 minutes: median one-way exactly 4.00c; plain floats give 0.04000000000000002) | case_01 | not closed | not closed | NOT closed |
| `just_above_4c` (same cell at 4.50c) | case_07 | closed | closed | CLOSED |
| `carry_matters` (Los Angeles tight from 15 minutes, no candle in the last 12) | case_05 | not closed | cannot say | not decided |
| `odd_cases` (Chicago never quoted; a tie for nearest 50c; an empty book at a look with a good quote a minute earlier) | case_02 | cannot say | cannot say | not decided |
| `pull_not_whole` (figures as `closed`, one candle request refused) | case_04 | closed | closed | not decided: the pull is not whole |
| `other_job` (the candle job asked for one ticker fewer than the sample) | case_08 | | | reader refuses |
| `no_job` (the candle run's manifest carries no job) | case_09 | | | reader refuses |
| `missing_field`, `odd_life`, `mixed_types`, `list_cut`, `over_cap` (builder only) | case_10, 11, 12, 13, 15 | | | no job written |
| `outside` (a market closing on Nov 12; builder only) | case_14 | | | refused |

My printed lines on each are in `hourlytemp/fixture_outputs/`; the inputs, under neutral names, are in `hourlytemp/fixture_inputs_MADE_UP_DATA/`. Tested by hand and not committed (a committed link would break the site build): a link inside a candle run pointing into a HELDOUT_ folder, a link pointing outside the run, a manifest file name with `..`, a `markets.json` one market short, a `markets.json` with one strike edited (all refused), and the builder's own job as the manifest's job with one of two requests answered (not decided). The job the builder writes passed the pull runner's own `check_job`. Worked one-way costs from the code: bid 48c ask 50c gives 3.00c; bid 47c ask 50c gives 3.50c; bid 98c ask 99c gives 1.50c (the fee price held at 99c).

## Known limits of the reader itself

1. The rank is taken among strikes with a two-sided quote, so a strike with an empty book near the money shifts the ranks of those beyond it.
2. The one-way cost uses the YES ask on every strike; buying NO on a strike is priced from the YES bid in the market and may differ by the spread's shape.
3. The size line is a single list copy of markets open at the pull, not of the sampled week.
4. If an hour has more than 100 strikes across the four cities, or two hours do not fit one request and the count passes 110, the builder writes nothing and the count goes to the Head of R&D; nothing is dropped to fit.
5. The lists job allows three pages of 1,000 a series. A series with more than 3,000 settled markets in the seven days ends on a cursor and the builder writes nothing.

## Second build (Testing Desk), Nov 13

Built from the note only (commit a7b2a5fc on `claude/testing-desk`, `testing/hourlytemp_second.py`), printed before comparing. On the fifteen made-up cases: 1,848 figures compared across the seven measured cases, 2 differences (one point: whether a candle showing an empty book counts as a strike "with a quote"); all twelve-median lines, trade shares, pooled sizes and verdicts the same; the seven refusal and stop cases the same; the builder's request count differed on one case (the packing rule was not written down). Amendment 3 fixes the three wordings to the audited reader, by the Head's ruling; the reader's hash did not change. Note before amendment 3: f5cf6af9...; Auditor B's CLEAN was given on that note and this reader, with the structure-check gate on every landed run.

## The two builds print the same (Nov 13, about 02:38Z)

After Amendment 3 the Testing Desk re-ran its reader (commit 728766dd on `claude/testing-desk`, `hourlytemp_second_prints_v3/`). Compared again on all fifteen made-up cases: 2,016 figures across the seven measured cases (24 lines a case, 12 figures a line, the two-sided share now included), 0 different; the candle job's request count the same in every case (2, and 168 with no job written in the over-the-cap case); every verdict, refusal and stop the same. Auditor B confirmed that Amendment 3's words describe the reader it passed. State: reader f443ae60 (audited CLEAN, second build matched), note 3e496e12. Still to come before any figure is read: the lists pull, then Auditor B's structure check on each landed run.

## Held-out line added to the note (Nov 13, 2026, 07:07Z)

On the Head of R&D's order of 06:53Z, `HOURLYTEMP_MEASUREMENT_NOTE.md` gained one dated held-out line (text only; no pin, figure or reading changed). The note's sha256 is now f7176b1c05804db85cd108eb80e5302177e42128f4c7a62780301e2be2d7bb3b (it was 3e496e1266d41551afe3710eb98a927bd0c5b45eadd5e771d81297518dca2091). The reader `hourlytemp.py` is unchanged at f443ae6016209dffd2113c552d67fa3dd3750d9ec0e5a7abb39ca224a24c9970. The shared guard `deskb_guard.py` is now 14f969bc8983bff2a0696b3dcab745d748119de28fc4c5692370933cad0b1df9 (it also refuses runs listed in `HELDOUT_PULL_RUNS.md`); the nine measure fixtures print byte-identical lines under it. W-CAT-CAL1 weather is released, so the sample stays 2026-11-05 to 2026-11-11.

**07:10Z:** a registry cross-check paragraph was added under the held-out line (text only). The note's sha256 is now f83c67858db66ddcf2c61ebf69256dcf04339e61f05ea981f6bd480f0752a154. The shared guard's docstring was reworded on Auditor B's gate (code unchanged); its sha256 is now a199f946cca9da8e0a3c56f0524109629b420ef91b20e77d54fa3b6b6b0f9dcd. The reader is unchanged.

## The lists landed; the builder STOPPED on its own rule (Nov 13, 2026, 08:04Z)

Run `pull/HOURLYTEMP_LISTS/2026-11-13T0756Z_43389350994/` (13 answers; the job on main byte-equal to the committed one, sha256 015a0b46). Auditor B's structure check PASSED before the run was opened (08:03Z: manifest, hashes, lengths, cursors, tickers, every settled close inside 2026-11-05 to 2026-11-11, strike fields present). Then one command on the audited reader (f443ae60), `job`, which reads tickers, strikes and times only. It printed (kept in `hourlytemp/real_read/job_lines_2026-11-13T0756Z.txt`):

- settled markets in the sample 6,720 | clock hours 166 | requests 102 (cap 110)
- 140 MARKETS DID NOT LIVE EXACTLY 60 MINUTES: no job written.

This is Amendment 2, item 3 working as written: a sampled market whose close minus open is not exactly 3,600 seconds stops the builder, because the carried quote and the job's time ranges assume the 60 minute life. No candle job exists, nothing was cut, no pin was bent. No price and no result has been read. The stop is with the Head of R&D. I have run nothing else on the run: which markets, which series and what lives they had is not known to me, because the reader prints only the count.

## The times-only breakdown of the 140 (Nov 13, 2026, 08:07Z)

Approved by the Head of R&D; script `hourlytemp/lives_breakdown.py` committed first (75ddb85f, sha256 6b1d7ae16d1fdcac4e0df0c2347d8807ce101ca881d372284bfe1225797ed2fb); Auditor B read the whole file and confirmed it takes only ticker, open_time and close_time before it ran. Printed lines: `hourlytemp/real_read/lives_lines_2026-11-13T0756Z.txt`, sha256 281a2eb47f8a4627cf3323ae228b5b4d11a8e31479dd0236152f4a02671d7834. Its first section equals Auditor B's independent count figure for figure.

What it shows, counts only:
- 6,720 settled markets in 658 series-hours. 615 series-hours have 10 markets; 43 have more (39 have 13, one has 15, three have 16).
- All 140 odd markets sit in those 43 series-hours, and in every one of them only PART of the hour is odd: the 10 other markets of the hour lived the full 60 minutes. The odd ones opened late (lives of 540 to 2,940 seconds; 80 of them 2,340 seconds) in groups of 3, or 5 or 6 with two different opening times.
- By series: Chicago 48, coastal Los Angeles 68, Miami 15, New York 9. By close hour of day (UTC) the 43 series-hours fall at 13 to 18 (40 of them), plus one each at 00, 08 and 23.
- Clock hours: all four series lack 2026-11-05T09 and T10; New York lacks six more (Nov 8 01; Nov 9 02, 07, 10, 11, 17). So 166 of 168 for three series and 160 for New York.

My reading, an inference and not a count: these are strikes ADDED to an hour's ladder after it opened. No strike value was read, so whether the added strikes are the ones nearest the money is not known. Nothing is decided; no candle job exists; the reader and the note are unchanged.

## AMENDMENT 4 written; the reader changed (Nov 13, 2026, 08:15Z). Before any candle is pulled.

On the Head of R&D's ruling of 08:09Z (course 1: keep all 6,720 markets, each from its own open time).

| File | sha256 now | was |
|---|---|---|
| `HOURLYTEMP_MEASUREMENT_NOTE.md` (Amendment 4 appended) | 079e137162236185e3ff3feaf5c8b9a1e24cfde2c1923c8c047da13bb3739bad | f83c67858db66ddcf2c61ebf69256dcf04339e61f05ea981f6bd480f0752a154 |
| `hourlytemp/hourlytemp.py` | bc76e8fc001fa409296050c9f60c90397a33bca015cdca5d2470c7d499afd572 | f443ae6016209dffd2113c552d67fa3dd3750d9ec0e5a7abb39ca224a24c9970 |

**What changed in the reader, and nothing else:** (1) `sample`: a life under 3,600 seconds is no longer a stop; it still stops on a life longer than 3,600 seconds, a close off the clock hour, or an open at or after the close. (2) new `late`, `gained`, `describe`: the count and table of late strikes, the series-hours that gained strikes (listed), the clock hours present per series with the missing ones named. (3) `job`: late markets go into their own requests (`l001` onward), one per distinct open and close time, range from their own open; full-hour requests are built from full-life markets as before; the cap is 140; the job's held-out line is the new `HELDOUT_LINE`. (4) `reading` is split into `look_figures`, `line_of` and `reading`: a strike whose own open is at or after the look is "not yet open" and skipped before any quote is looked for; every figure line is printed for ALL series-hours and again without those that gained strikes; the line and the verdict read ALL hours. (5) `measure`: the counts line, the trade-minutes line and the line under each reading are printed twice in the same way; trade-minutes are over each market's own minutes of life. The quote search, the two-sided test, the money, the ranks, the fee, the cost line, the verdict words and the whole-run and same-sample refusals are untouched.

**Made-up fixtures (`fixture_outputs/make_fixtures_MADE_UP_DATA.py`, now 34b2ac12):** the 15 old cases are regenerated with byte-identical content; on the 9 old cases that reach `measure`, every ALL-hours figure line of the new reader equals the old reader's line once the new prefix ("ALL n series-hours: not yet open 0") is taken off, and every verdict or refusal is the same. Four new cases: 16 (three late shapes: a strike opening 21 minutes before the close that becomes the money at the 10 minute look, strikes opening 9 minutes before the close that are open at no look, and an hour with two opening times), 17 (the hour that gained strikes decides the line: 3.00c on all hours, 6.00c without it; the verdict reads all hours), 18 (a close at half past the hour: stop), 19 (an open equal to the close: stop). A job built from case 16 passes the pull runner's own check (main's copy): two full-hour requests and four late ones of 21, 9, 39 and 29 minutes. The stored outputs in `fixture_outputs/` are those of the new reader.

**Not done on purpose:** the new builder has NOT been run on the real lists. Order from here: Auditor B's diff against Amendment 4, the Testing Desk's re-run on cases 16 to 19, then the candle job to the Head with its request count and held-out line.

## Second build re-run for Amendment 4 (the Testing Desk, 08:16Z): same on every figure

The Testing Desk rebuilt `hourlytemp_second.py` (sha256 starting 33ec5776) from Amendment 4's text only and printed all 19 made-up cases before comparing (its commit e0b8896b on `claude/testing-desk`, `hourlytemp_second_prints_v4/`). Compared with the outputs of the reader bc76e8fc: 5,840 figures over the 11 cases that reach the measure step, none differ (both readings of the quote, both sets of hours, every city and look, and the trade-minute shares with their counts); the verdict lines agree in words on all 11; the eight stop cases stop for the same reasons; the request counts agree (case 16: 6; case 17: 3; case 15: 168, over the cap of 140).

One difference, on a printed information line and not a figure: the missing clock hours. The second build counts the hours missing inside each series' own first-to-last span; this reader counts against the 168 clock hours of the fixed seven days. Amendment 4 (d) does not state the number; the Head of R&D's ruling of 08:12Z said "against the 168 expected". A clarifying line is asked of the Head, to be written once after Auditor B's diff. The Testing Desk's three readings where the text is silent (a look exactly at a strike's own open is not yet open; a series-hour is a series and a close hour; its late-request formula) match this reader.

## The candle job is built (Nov 13, 2026, 08:22Z). Not dispatched.

After Auditor B's CLEAN on the Amendment 4 diff (08:19Z) and the Testing Desk's matching re-run, one command on the audited reader (bc76e8fc): `job` on `pull/HOURLYTEMP_LISTS/2026-11-13T0756Z_43389350994/`, tickers, strikes and times only. Printed lines: `hourlytemp/real_read/job_lines_amendment4_2026-11-13T0756Z.txt`.

- **`desk_b_jobs/HOURLYTEMP_CANDLES.json`, sha256 3b96fa34bac8b7ee70bc1876f10ef7b6e80d46581589db6f7c9afd9381ab6344.** 129 requests, one page each, cap 140: 84 full-hour requests (82 of them two clock hours) and 45 late-strike requests (2 to 6 tickers, ranges of 540 to 2,940 seconds, each from its own open to its close). The count equals Auditor B's independent count from times alone (84 + 45).
- 6,720 tickers asked, each exactly once, equal to the job's ticker allowlist and to the sample. One-minute candles. Earliest range start 2026-11-04T23:00:00Z (the open of the hour closing 2026-11-05T00:00Z), latest range end 2026-11-11T23:00:00Z. The largest request is 9,680 ticker-minutes (limit 9,800); the whole job is 796,374 ticker-minutes at most.
- The job passes the pull runner's own load and check (main's copy). Its held-out line names W-CAT-CAL1 weather (released), WXNEW1 (holdout 2026-10-19 to 2026-10-31, before the sample) and WXOTHER1 (closed unread).
- `markets.json` (the sample the measure step checks the candle run against) is not committed (1.1 MB); it is rebuilt by the same command from the same lists run, sha256 6364a152a5648571db3f569c8048ba40f2a0a409206d6e13f840efa452d4aeb9.
- Printed with it: 140 late strikes with the table of lives; 658 series-hours, 43 of which gained strikes, listed; clock hours present 166 of 168 for Chicago, Los Angeles and Miami and 160 for New York, the missing ones named. All equal to the times-only breakdown and to Auditor B's count.

It goes to the Head of R&D with the count, bounds and held-out line, and to Auditor B for a diff against the lists run, before any dispatch. A job file needs the owner's typed merge.

**08:23Z:** the clarifying line to Amendment 4 is written (text only: missing hours are counted against the 168 clock hours of the fixed seven days; a series-hour is one event). The note's sha256 is now 3ff1de2d600352148aa02ac5c48f6ba8ada67fe02136e66817f842de675dd9f7 (it was 079e1371). The reader (bc76e8fc) and the candle job (3b96fa34) are unchanged.

**08:24Z:** the candle job (3b96fa34) PASSED Auditor B's diff against the lists run (129 requests, 6,720 tickers each once and equal to the settled markets of the run, every late request's range equal to its markets' own open and close, no full-hour request holding a late ticker, nothing ending after 2026-11-11T23:59:59Z) and was ACCEPTED by the Head of R&D, who sent it to the Chief of Staff for the next jobs change (it needs the owner's typed merge). When its run lands: Auditor B's structure check before anyone opens it, then this reader (bc76e8fc) and the Testing Desk's build on the same frozen copy; figures go to the Head when both print the same.

**08:26Z:** the Testing Desk's second reader ran its sample step on the same lists run (its commit bea805e9 on `claude/testing-desk`; Auditor B CLEAN for that step): 6,720 markets and a candle job of 129 requests, the same as this builder. Its measuring step waits for the candle run, as mine does.
