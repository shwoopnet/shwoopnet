# COMBODONE stage 1 counter: as frozen, Nov 13, 2026, 02:20Z

A zero-try COUNT (go or no-go) for Idea Desk C's card. Built from the card's text only, tested on made-up data only. No combo-data file has been opened for it and no figure exists.

| File | sha256 |
|---|---|
| `combodone/combodone.py` (commands `week`, `legs-job`, `count`) | `8cdf4bb96518b26225a3d095a8bc00abd0f5e72331cfa04966eeef4dfda3db2e` |
| `combodone/fixture_outputs/make_fixtures_MADE_UP_DATA.py` | `1e782b4432807909fa53f1ebaef9c8c8be7c021474084f96363bea8b7add6da1` |
| The card: `idea_desk_c/COMBODONE_CARD.md` at commit 593597e6 on `claude/idea-desk-c` (Amendments 1 and 2, readings 1 to 18) | `985ff446fc1b2959342d20734a2feb18d190aef6a266852ec3c6303e2f7802d5` |

The held-out folder guard (`deskb_guard.py`) runs on every path, and every file opened must resolve inside the folder it was named under.

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
