# Hourly temperature measurement: the reader as frozen, Nov 13, 2026, 02:05Z

A cost and timing MEASUREMENT, zero tries. No list or candle of these series has landed; this reader was built from the note's text and tested only on made-up data.

| File | sha256 |
|---|---|
| `hourlytemp/hourlytemp.py` (commands `job`, `measure`) | `7572d7a1de935a2600bc760722a599c5f2d3b454598b6f2d06118329b7c741f3` |
| `HOURLYTEMP_MEASUREMENT_NOTE.md` (with the Nov 13 amendment, pins 1 to 12) | `8191bd321c9825480e99aaf5921f1f4a8539bf3fa89b8cce5a2be8fb0c869f4d` |
| `hourlytemp/fixture_outputs/make_fixtures_MADE_UP_DATA.py` | `57f88d2135a3c254a3d3a755fd9e20f38de8168cb411219b6523376b613262cf` |

The older `hourlytemp/measure.py` and `hourlytemp/build_candles_job.py` are removed. The lists job's note (`desk_b_jobs/HOURLYTEMP_LISTS.json`, and its copy under `kalshi_pull_jobs/` on main) still names the old builder; the job itself is unchanged and the builder is now `hourlytemp.py job`.

## What it prints, what it cannot show

It prints, first, the settlement rules text of one market of each of the four series, exactly as listed. Then, for each city and each look (55, 30 and 10 minutes before the hour) over the seven fixed days, under two readings of the quote (the last candle inside the market's 60 minute life, and only a candle ending at the look): how many strikes had a quote, how many were two-sided, the median spread, the median round trip, the median one-way entry cost near the money, the share already priced at 95c or 5c and beyond, and the median ask of the nearer-certain side by distance from the money. Then the share of market-minutes with a trade per city, the size at the touch on open markets per series, and one verdict: CLOSED as too costly only if both readings put every one of the twelve city-and-look medians above 4c; NOT closed only if both readings find one at 4c or less; otherwise not decided. It cannot show whether any rule makes money (no result field is read, and the fixtures carry a made-up result to prove it is ignored), how any outside reading relates to the settled value (none is read), depth beyond one level, or whether a carried quote could have been paid. A NOT closed verdict approves nothing: any rule would need its own card, registration and try.

## Fixtures (all made up, whole cents) and what each must print

| Fixture | Carried | Exact | Verdict |
|---|---|---|---|
| `closed` (spread 8c everywhere, one-way 6c) | closed | closed | CLOSED |
| `not_closed` (Miami at 10 minutes 2c wide, one-way 3c) | not closed | not closed | NOT closed |
| `boundary_4c` (New York at 30 minutes: median one-way exactly 4.00c; plain floats give 0.04000000000000002) | not closed | not closed | NOT closed |
| `just_above_4c` (same cell at 4.50c) | closed | closed | CLOSED |
| `carry_matters` (Los Angeles tight from 15 minutes, no candle in the last 12) | not closed | cannot say | not decided |
| `odd_cases` (Chicago never quoted; a tie for nearest 50c; an empty book at a look with a good quote a minute earlier) | cannot say | cannot say | not decided |
| `pull_not_whole` (figures as `closed`, one candle request refused) | closed | closed | not decided: the pull is not whole |
| `list_cut`, `outside`, `over_cap` (builder only) | no job written; refused; no job written | | |

My printed lines on each are in `hourlytemp/fixture_outputs/`. The job the builder writes for `closed` and `odd_cases` passed the pull runner's own `check_job`.

## Known limits of the reader itself

1. The rank is taken among strikes with a two-sided quote, so a strike with an empty book near the money shifts the ranks of those beyond it.
2. The one-way cost uses the YES ask on every strike; buying NO on a strike is priced from the YES bid in the market and may differ by the spread's shape.
3. The size line is a single list copy of markets open at the pull, not of the sampled week.
4. If an hour has more than 100 strikes across the four cities, or two hours do not fit one request and the count passes 110, the builder writes nothing and the count goes to the Head of R&D; nothing is dropped to fit.
