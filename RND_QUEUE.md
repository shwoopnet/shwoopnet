# R&D queue (the Head of R&D keeps this from Nov 12, 2026, 15:00Z; Main kept it before)

Branch `rnd-queue`, not main. Read it with `git fetch origin rnd-queue && git show origin/rnd-queue:RND_QUEUE.md`. Rules: docs/RND_CHARTER.md and docs/POLITICS_RULES.md on main. No live account figure goes in this file or on any branch; live numbers travel by message only. Every figure below is a research result on public data, a rule or a cap. [research]

## The honest state (Nov 12, 2026)

- Probe-ready count: **0**. Nothing has passed the research bar (cash PF 1.5 in three windows, after fees, deflated). Nothing is proven (PF 1.3 over 100 fills in 2 of 3 windows).
- Two leads have fixed read dates, and **neither read can be a research-bar pass on its date**: CFRTI1-BTC (50 rows; a real verdict needs about 170) and MMSIM1 (about 400 events; the deflated bar needs about 1,900).
- One queued test can reach a real verdict in one pull: the sports SPREAD cell (about 320 fresh observations expected). Its chance of passing its own bar is small (Head of R&D estimate 3 to 5 percent; Refinement's estimate 10 to 15 percent).
- Every label on this page is one of: PASS (research bar), LEAD (not a pass), FALSIFIED (at about 100 trades or more), "no evidence at n = x" (below that), or, for slow families only, "on the paper list (unproven)".

## Who reports to whom

Research reports to the Head of R&D. Engineering, merges, deploys, recorders, kalshi-pull and everything live are the Chief of Staff's (Main). The Verification Analyst is independent of research: any claimed pass or uniqueness score is re-checked through Main, never by the desk that produced it. The owner decides every popup.

## Kalshi reads, set 2026-11-12 15:00Z (agreed split pending Main's confirmation)

- **Shared address (about 25 reads an hour, mostly 429): research holds ZERO.** No desk fetches from it. A 429 is never retried in a loop.
- **All research pulls go through kalshi-pull** (PR 795, security PASS, waits on the owner's merge; manual dispatch by the owner or Main, 1 request a second, 1,200 a run, 6 runs a day). Order, by value per read:

| Rank | Job | Reads | What it buys | State |
|---|---|---|---|---|
| 1 | ROLLOFF_PROXY | 12 | Kills or keeps the only daily politics card the same day (kill: the Wikipedia proxy fails to reproduce the settled value within 0.3 points on 80 percent of days) | ready, owner-approved |
| 2 | SPREADCELL1 (W-SPREAD-CELL1) | 274 | A one-shot out-of-sample read of one frozen cell on 1,041 never-scored events | job ready on claude/refine-live; to be ported in Main's jobs-v2 PR; the label for the middle outcome must be committed before dispatch |
| 3 | NOSIDE1_CANDLES (W-NO-ARM1) | 1,034 | A first readable development verdict on the approval NO side; what is held leans against | ready on claude/refine-live; runs only after 1 and 2 are on the data branch |
| retired | COMBO1_OPENBOOK | 0 | Answered for free: the combo recorder's first snapshot on combo-data (2026-11-12 14:35Z) has 400 quote rows, 37 with a yes bid, 27 with a yes ask under 1, 18 two-sided | closed, no read spent |

Not scheduled: a daily logging job for the spread cell (only after its read), ECONLAG (one falsification run, later), WXDAYEND remainder (22 reads, last).

## Fixed read dates (cutoffs are committed date constants; read once; nobody runs early)

| Test | First allowed | Size | Cutoff constant | Runner | Outcome labels (committed in advance) |
|---|---|---|---|---|---|
| MMMAP1 (measurement) | Nov 15 | needs 3 full NC15 dates | hourly-ladder part: events closing before 2026-11-07T15:00Z | Desk A (was V2) | a measurement, no PF verdict |
| NC15DEPTH1 pooled cell | registration due before Nov 19 | forward only | to be registered (counts only) | Desk A (was V2) | forward only; the 3c effect is an assumption |
| CFRTI1-BTC held-out | Nov 20, expected Nov 22 to 24 | 50 Bitcoin edge rows | HELDOUT_FIRST_DAY 2026-11-05 | Desk A with V2's committed script and its own | PF under 1.0 = FALSIFIED; otherwise LEAD at most; a pass means RE-TEST at about 170 rows |
| MMSIM1 and MMHOUR1 held-out | Nov 24 | about 400 hourly events | PINNED_CUTOFF 2026-11-07T15:00:00Z; the 5 events closing Nov 7 15:00Z to 19:00Z are SPENT and reported with and without | Desk A with V2's committed script and its own | PF 1.3 or better with a positive day mean = LEAD CONFIRMED; under 1.0 = FALSIFIED; else no call. Cannot be a research-bar pass before about late January |
| Combo house side, first paper read | Nov 26 | stop if fewer than 20 combos ever showed a two-sided quote with a bid, or fewer than 100 trades | to be registered by Desk B before any scoring | Desk B | paper only; 10c per dollar edge over 100 settled combos before any $2 probe |

Each read is re-checked by the Verification Analyst before a figure reaches the owner.

## Probe pipeline (leads ranked by days to a first tiny live order; every one UNPROVEN; each needs the owner's own popup)

All specs are written as CONDITIONAL on the registered read. The owner's Nov 12 decision in PR 796 says nothing new goes live until it earns it; a pre-evidence fill test would need the owner to say so explicitly.

| Rank | Lead | Gate before any order | Earliest first order if the gate is met | Odds the gate is met (Head of R&D) |
|---|---|---|---|---|
| 1 | Sports SPREAD cell, 1 contract, YES ask 5c to 15c, more than 24 h before close, hold | SPREADCELL1 read passes its registered bar; Verification Analyst re-check; uniqueness score; code path for a non-15-minute market or a hand-placed order | about 3 to 4 days after a pass | 3 to 5 percent |
| 2 | CFRTI1-BTC, 1 contract, cheap side 5c to 30c, model edge 5c or more, hold | Nov 22 to 24 read meets its registered bar (which makes it a RE-TEST lead, not a pass: a no-edge rule clears a 50 row read about 1 time in 10); venue terms for the three spot feeds read by a person; correlation with OICORE under 0.3 (at risk: same market, side and minute) | Nov 26 to 30 fast, Dec 10 to 15 safe | about 10 percent to reach a probe; under 5 percent to be proven |
| 3 | MMSIM1 one-strike fill test, 1 contract a side, flatten at T minus 15 | Nov 24 read = LEAD CONFIRMED; owner exceptions (short round trip, resting orders); a new resting-order and cancel engine through security review | Dec 1 to 3 at the earliest; Nov 20 to 23 only if the owner wants a pre-read fill test | about 25 percent for LEAD CONFIRMED (the registration itself warns a pass is unlikely); it measures fills, it cannot show profit |
| 4 | Approval NO side, 3 contracts | NOSIDE1 development and held-out reads; what is held leans against | not before late November | under 10 percent |
| 5 | Combo house side, $2 | paper edge of 10c per dollar over 100 settled combos | not before December | unknown, no evidence yet |

## Desk tasks (none needs a scarce read)

- **Refinement:** commit the SPREADCELL1 middle-outcome label and the read-once scorer before dispatch; update REFINE_HANDOFF.md; Monday rotation report; gold latch watch (message only).
- **Desk A:** runner for the fixed-date reads above; NC15DEPTH1 cell registration; held-out audit follow-through (every open test pinned).
- **Desk B:** complete shadow rule S3 (combo house side) from the combo-data fields and register it before any scoring; ROLLOFF proxy scorer ready so the kill check runs the day the 12 reads land; the paper list under POLITICS_RULES section 8 (PR 794), with the count of cards read beside any listing.
- **Probe Engineering:** design notes for the three conditional probe specs; scope a path for a non-15-minute market; resting-order engine design, off by default; nothing is built into the bot without Main's review.
- **Live-Data Forensics:** task set after its status report.
- **V2:** retiring once SHADOW_RULES_NOV12.md is pushed; its reads move to Desk A.

## Deflation ledger

One file, DEFLATION_LEDGER.md on this branch (being compiled from the per-test registrations; the quoted shared N of about 1.1 million with z 5.34, and the lenient N of 9,009 with z 4.39, are being traced to sources). Every new try is added there before it is scored.

## Retired by power analysis (POWER2, V2, 2026-11-12): do not spend reads

AVG1, STALE1, EARLYCLOSE1, TIECOND1 arm B, CLINICAL2 incl. its remainder pull, COMBO1 as a resting-ask test, POLCOMBO1B (reopen only on a live two-sided politics-leg combo quote or 100 settled), RETAILFRAC1 stage B, CRONCLUSTER1, NC15DEPTH1 per-series cells, MENTPERSIST1 fetching. Desk B retired: UNRATEROUND, FAANOTICE, SCOTUSAUTH, PRESENTQ, TARIFFDTS, CPIARITH, WIKIEDIT, SWEEPSIM, IMPLY1, both weather combo cards, NESTCOMBO. Parked: MOVPARITY arm A, BALLOTNO (to Nov 2028). Demoted: ECONLAG. Dropped: WXREVISE. Blocked: Treasury FiscalData rows 78 to 80 (terms unread). Stopped: Deribit recorder (PR 798).

## Closed or falsified (do not retry without new data)

Cheap-side grammar GEN12 and GEN13, REGIME1, SWEEP1, NONCRYPTO1, LEADLAG1, TAPEFLOW1, BFLY2, LADBFLY1 and XSER1 (monotonicity), PIN1, ROUND1, MENTCOMBO1, MENTPERSIST1, ANGLES1, EARLYCLOSE1, NEWLIST1B, EXECSUM, CFRTI1 pooled, MMSIM2, TIECOND1, EXDIV1, external-signal sweep, weather, finance, indices and sports-singles calibration sweeps (no survivor; the SPREAD cell is the one lead carried out of them), spot-lead at its Nov 11 read (missed its bar at n 58; re-read about Nov 21 to 23). The declined list is docs/STRATEGY_LIFECYCLE.md section 7e on main.

## Waiting on others

- Owner: merge 795 (kalshi-pull; nothing on the read list moves without it), 794 (paper screen), 799 (Bitcoin recorder to Dec 15; CFRTI1-BTC cannot reach 170 rows without it), the venue terms question for the three spot feeds.
- Main: the politics recorder is barely accruing (3 pushes in about 19 hours against an hourly start); a gold shadow record so gold's return rule can be met; jobs-v2 PR.
