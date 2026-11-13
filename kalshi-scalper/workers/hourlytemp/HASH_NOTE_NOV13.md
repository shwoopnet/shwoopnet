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
