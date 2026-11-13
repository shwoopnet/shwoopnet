# COMBODONE stage 1 counter: as frozen (final), Nov 13, 2026, 02:38Z

A zero-try COUNT (go or no-go) for Idea Desk C's card. Built from the card's text only, tested on made-up data only. No combo-data file has been opened for it and no figure exists.

| File | sha256 |
|---|---|
| `combodone/combodone.py` (commands `week`, `legs-job`, `count`) | `5695b46f4163fc322dbe3d24e28b0d8e1430e1c793239b29c4714a0d5f5f4ea1` |
| `combodone/fixture_outputs/make_fixtures_MADE_UP_DATA.py` | `196e92a489269d58a6bcdb89c225ebf467496bb3053e0cc0944f4d52554187d3` |
| The card: `idea_desk_c/COMBODONE_CARD.md` at commit 4ae639d9 on `claude/idea-desk-c` (Amendments 1 to 5, readings 1 to 23) | `81974ae89253f33b6f754c9f25b320046938c3412d7e0c68b0dd1dbf5a422536` |

The first freeze (8cdf4bb9, against the card at 593597e6) is DEAD. Auditor B passed it CLEAN with two gates; the History Miner's second build (from the card only) printed the same on every figure of the 11 made-up cases (64 blocks, 0 different). The change since then is exactly: the Miner's four readings where our builds could differ on inputs the cases did not exercise (readings 19 to 22: any coverage row; a legs value that is not a whole number; a 200 row with no file; an unreadable row placed by its receive time or its folder's day), the auditor's fingerprint line as the card's Amendment 5 defines it (path, size and sha256 of the bytes of every file in a dated folder; a symbolic link refuses the run; root files excluded), and the "some seconds" wording on the 60 second line. On the 11 cases the History Miner's final build (4f2e954f) and this one name the SAME fingerprint in every case, and every other printed line is unchanged from the first freeze.

**Gates before any real figure is read (Auditor B):** (1) the leg run folder goes to Auditor B first, for a structure check against its manifest; (2) both builds run on ONE frozen copy of the combo folder and must print the same fingerprint.

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
| `legs_nofile` | a leg request answered 200 with no stored file | not decided |
| `edges` | base plus: a legs value of 2.5; a row with a time and no ticker; a row with no time in a week folder, in the D0 folder and in the D8 folder; a run whose coverage file has two rows (stopped early, then not) | as `base` except 21 quote rows, 2 unreadable, 5 leg unknown; the week still has 269 runs |

Boundaries inside `base`: an ask of 0.8700 with size 1 counts, 0.8701 does not, size 0.5 does not; a leg settled exactly 60 seconds before the snapshot satisfies (b), 59 seconds does not; a combo whose close time equals the snapshot time is closed; a book ask of exactly 87c counts, 88c does not. Tested by hand and not committed: a combo folder inside a HELDOUT_ folder and a run folder that is a link into one (both refused). The leg job the builder writes passed the check of main's pull runner (`scripts/kalshi_pull.py`).

The inputs are committed under neutral names, one archive a case: `fixture_inputs_MADE_UP_DATA/case_01.tar.gz` to `case_13.tar.gz` (the printed outputs here were made from those archives, so their fingerprints can be reproduced; the generator writes the same content, but gzip stamps the time, so a fresh run of it has other fingerprints). Tested by hand, not committed: a symbolic link inside a dated folder (refused) and a file at the root of the combo folder (fingerprint unchanged).
