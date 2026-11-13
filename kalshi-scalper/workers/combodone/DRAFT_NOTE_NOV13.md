# COMBODONE stage 1 counter: DRAFT, NOT FROZEN (Nov 13, 2026)

Built from Idea Desk C's card at commit 17d7fe17 (`idea_desk_c/COMBODONE_CARD.md` on `claude/idea-desk-c`), before any combo-data file was opened for it. Tested on made-up data only. It is not frozen and carries no hash yet: nine further readings (10 to 18) were sent to Idea Desk C to be written into the card first. No audit has been asked for and no figure exists.

## What it prints, what it cannot show

`week` prints the completed runs of each UTC day and either the first full week or "no full week yet"; it opens coverage files only. `legs-job` writes the one leg pull (`/markets` with a `tickers` parameter, 100 a request) for that week. `count` prints: the week and its coverage; how many quote rows the week holds and how many carry a whole leg string, an empty one, a cut one; how many rows with a whole string are not eligible, by reason; the eligible snapshots with and without a resting ask; the independent combos (a still-open leg set on a UTC day) with and without a resting ask, per day and over the week, and the distinct sets; the median ask; the book figure beside it; and one line: CLOSED if fewer than 30 independent combos had a resting ask in the week, SURVIVES THE COUNT otherwise, "not decided" if the leg pull is not whole, and nothing at all beyond the daily run counts while no full week exists.

It cannot show whether a resting ask was below fair value (it holds no leg price; that is stage 2, with its own registration and try), whether an ask seen on a list copy could have been bought (list quotes are delayed; the books file covers 40 combos a run), or anything about combos outside the first 100 quote rows of a run (their legs are not recorded). A 30 minute poll misses an order that lived for seconds. It reads leg RESULTS to classify a snapshot, so it is not blind to leg outcomes, and any stage 2 must fix its held-out dates before pricing.

## Fixtures (all made up) and what each must print

| Fixture | What it is | Must print |
|---|---|---|
| `base` | 20 quote rows, one for each case of the card and its amendments | 8 eligible, 6 with an ask; 5 independent combos, 4 with an ask (3 distinct sets); median 70.00c; book 3, 2, 2; not eligible: 4 leg unknown, 1 other result, 1 lost, 2 no leg decided, 1 every leg settled, 1 closed; CLOSED (4) |
| `week_29` | base plus 25 one-leg-open combos with an ask | CLOSED (29) |
| `week_30` | base plus 26 | SURVIVES (30) |
| `runs_268` | 268 completed runs | no full week |
| `day_23` | 269 runs, one day of 23 | no full week |
| `day_not_over` | no run after the seventh day | no full week |
| `stopped_early` | one run stopped early, 268 completed | no full week |
| `second_week` | a second full week follows | the first week; figures equal `week_30` |
| `legs_refused`, `legs_cursor` | a refused leg request; an answer left on a cursor | not decided |
| `legs_other` | the leg job did not ask for one named leg | refused |

Boundaries inside `base`: an ask of 0.8700 with size 1 counts, 0.8701 does not, size 0.5 does not; a leg settled exactly 60 seconds before the snapshot satisfies (b), 59 seconds does not; a combo whose close time equals the snapshot time is closed; a book ask of exactly 87c counts, 88c does not. Tested by hand and not committed: a combo folder inside a HELDOUT_ folder and a run folder that is a link into one (both refused). The leg job the builder writes passed the check of main's pull runner (`scripts/kalshi_pull.py`).

The fixture inputs are not committed (about 9,000 small files); `make_fixtures_MADE_UP_DATA.py <dir>` writes them.
