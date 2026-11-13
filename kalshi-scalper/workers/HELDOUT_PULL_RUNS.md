# Landed pull runs that hold held-out material (a list, not a move)

Rule (h): a development run must not contain held-out markets with their result fields. When a run that already landed on the `kalshi-pull-data` branch turns out to hold held-out material, it is LISTED HERE. The folder on the data branch is NOT moved, edited or renamed (a move would break the run's manifest and any auditor hash, and only the pull workflow writes that branch). Desks and scorers must refuse a run listed here as development input; a scorer that refuses a run holding a market that closes after its own window is the second guard.

| Run folder (under `pull/`) | Job | What is held out in it | Held out by | Listed |
|---|---|---|---|---|
| `POLGAPH_LISTS/2026-11-13T0627Z_43378777252` | POLGAPH_LISTS | Settled markets closing from 2026-11-05T00:00Z to 2026-11-12 (eight days) with their result fields, all 69 of POLGAPH's series; also one event from 2026-11-10T19:14Z held out by W-CAT-POLENT1 | POLI2 (Testing Desk card, closed on cost, never read) from 2026-11-05T00:00Z; W-CAT-POLENT1 (Refinement) from 2026-11-10T19:14Z | 2026-11-13, at the Head of R&D's request |

Notes: no result or price in this run has been read (the structure check and the job builder read tickers and times only). POLGAPH's development now ends 2026-11-04T23:59:59Z and its held-out starts 2026-11-05T00:00Z; a new lists job bounded at Nov 4 replaces this run for development use, and the hourly candle job dfc64533 is dead. Only the owner or the Head of R&D adds or removes a row.
