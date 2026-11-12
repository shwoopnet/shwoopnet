# Queued Kalshi pull jobs (PULLJOBS1, Nov 12, 2026)
Research only. Zero Kalshi calls were made writing these files. Each job is a JSON file a generic runner (`src/scalper/pullrunner.py`) executes only with an explicit approval. The pull worker ("kalshi-pull") is not approved yet; nothing here runs until it is.

## How to run (only after approval)
```
python3 -I src/scalper/pullrunner.py workers/pulljobs/<JOB>.json --dry-run            # prints the plan, calls nothing
python3 -I src/scalper/pullrunner.py workers/pulljobs/<JOB>.json --approved <JOB>     # real run; --max N may only lower the cap
python3 -I src/scalper/pulljobs_ingest.py <MENTPERSIST1 job id>                        # offline: scratch files into data/ment1.sqlite
```
The runner refuses without `--approved <job_id>`, refuses a job that is not `active`, calls only `api.elections.kalshi.com` (GET), checks every request against the job's endpoint patterns, ticker and series allowlists and params, refuses account, portfolio, order and key paths, sends no credential, paces requests, counts a cap, pauses 300 s on a 429 and stops on a second 429 in a row (exit 2, cursor saved, rerun resumes), stops at each checkpoint (exit 3, rerun acknowledges), and writes `<JOB>_READLOG.json` (status codes, counts, timestamps, request ids, never a payload). Response bodies go to `/tmp/pulljobs/<JOB>` (scratch, never committed). Test: `python3 -I tests/test_pullrunner.py`.

## Rate reality
Kalshi answers 429 every 2 to 4 requests from this shared address: about 25 reads an hour (one read about every 144 s on average, including the 5 minute pauses). Pacing is 15 s in each file (the registered pacing) and the 429 rule does the throttling. Hours below are reads divided by 25.

## Ranking, value to a verdict per read (my ranking comes AFTER the first row)
| rank | job | status | reads | hours at 25/h | what a verdict needs / gives | value per read |
|---|---|---|---|---|---|---|
| 0 | **Refinement's approval NO-side pull** (not written here; it is Refinement's and main's call) | main says it is the single scarce pull to spend the first reads on | n/a | n/a | n/a | spend first |
| 1 | `COMBO1_OPENBOOK` | active | 3 | 0.1 | one page of OPEN combos in 3 collections: any real two-sided quote? Yes reopens COMBO1 with a recorder; no closes it for good | highest: a family-level close or reopen for 3 reads |
| 2 | `MENTPERSIST1_A_300` | active | 300 | 12 | development trades about 83 R1 and 33 R2 (held 500 give 48 and 20; 300 reads add about 52 and 22). Enough for the registered KILL test (PF under 1.0 on 60 or more R1 trades) and the development gates; NOT enough for the held-out gate (about 17 held-out R1 trades, 30 needed) | one kill-or-continue answer per 300 reads |
| 3 | `MENTPERSIST1_B_1300` | active, after A | about 220 more reads to the R1 gate (total about 520, 21 hours); cap 1,300 (total 1,600, 64 hours) | 9 to 52 | R1 reaches the registered stop (130 trades by the rule) near 470 reads and 30 held-out trades near 520; R2 (0.073 trades a read) needs about 1,230 reads for 30 held-out trades and will probably hit the 1,600 cap first: NOT_ENOUGH_DATA for R2 is the likely outcome | lowest; stop at the checkpoint where R1 has 130 trades |
| - | `CLINICAL2_REMAINDER` | retired | 0 | 0 | see below | no value |
| - | `POLCOMBO1B_REOPEN` | inactive | 0 (about 122 if reopened) | 0 | see below | no value now |

Total if everything active runs to its stop: 3 + 300 + about 220 = about 523 reads, about 21 hours. Absolute maximum (no early stop): 1,603 reads, 64 hours.
Recommended order of the reads: Refinement's approval NO-side first; then `COMBO1_OPENBOOK` (3 reads); then `MENTPERSIST1_A_300`; then `MENTPERSIST1_B_1300` up to the first checkpoint block where R1 has 130 trades.

## Held-data arithmetic behind the MENTPERSIST1 numbers (counts, no outcome; MMPOWER1 style)
Pool after the 5 already read: 15,703 new markets in ascending md5 order. The 274 held markets with a PREV give 79 usable decision quotes (spread 0.05 or less), 48 R1 and 20 R2 trades by the rule: 0.175 and 0.073 trades per candle read. A read adds 0.29 quotable markets. 300 reads: about 52 R1, 22 R2. Development takes the earlier two thirds of new markets read, held-out the last third (cut committed once, Amendment 1): held-out R1 trades = 0.175 x reads / 3, so 30 held-out R1 trades need about 515 reads, 30 held-out R2 about 1,230. These rates come from 274 markets and carry wide error (R1: 48 of 274 = 17.5% plus or minus 4.5 points), so treat the read counts as plus or minus 30%. The A job alone cannot run `commit-cut`; that needs the pull to be complete or at its cap.

## Retirements and reasons
- **CLINICAL2 remainder: RETIRE.** The card closed on its own kill rule on Nov 11: at most 17 distinct settled events in the nine series against a gate of 100, about 1 new settled event a month (83 months). The candle step (up to 126 reads) cannot raise an event count, and the 65 extra series would cost 130 listing reads for a family where 75 of 126 settled markets took more than 90 days to close. Reopen only on a registered RETURN (new source or family, or 100 events).
- **COMBO1 historical walk and candle pricing (17+ pages, 300 to 500 candle reads): RETIRE.** All 34 sampled combos had ask 1.0000 and bid 0.0000 in every candle: a combo is quoted on demand, not on a resting book, so a candle read cannot give a buyable ask and every combo would be skipped. Replaced by the 3 read `COMBO1_OPENBOOK` probe, which checks the live book once; only a quoted open combo reopens the card.
- **POLCOMBO1B remaining census: RETIRED by its kill rule** (two sampled runs, no candidate, 74 of 75 politics-leg combos showed 0.00/0.00). `POLCOMBO1B_REOPEN` is written inactive: the runner refuses it and it has no requests, because it needs a cursor-following feature the runner does not have. Reopen only on the protocol's condition (a politics-leg combo with a live two-sided quote, or 100 settled politics combos).

## Other queued pulls found (not written)
- NHLAST1 / NHLALL1 forward reads (about 135 unfetched assist games, 881 unfetched pre-cut games, the frozen games after 2026-10-03): each game needs a market list plus candle reads, and the frozen games are opened only with the owner's approval. A job file needs the registered frozen-game cut first.
- ECONNEW1 CPI1 refetch and core PCE vs Cleveland nowcast: needs approval and a corrected `pick()`; Refinement owns the economics pulls.
- EXECSUM D3 / BILLS-D0 / BILLS-D15 held-out: scratch cache not kept and no committed close-time cut; no job until the cut constant is committed.

## Files
`MENTPERSIST1_A_300.json`, `MENTPERSIST1_B_1300.json` (plan order = ascending md5 of the new-market pool, first 1,600 after the 5 already in `done`; built by `src/scalper/pulljobs_build.py`), `COMBO1_OPENBOOK.json`, `CLINICAL2_REMAINDER.json` (retired), `POLCOMBO1B_REOPEN.json` (inactive). Each carries job_id, card, protocol file and commit, host, allowed endpoints, allowlists, pacing, max and expected requests, priority, cursor file, scratch output dir, stop rules, privacy rules, fields to keep, and what it will NOT decide.
