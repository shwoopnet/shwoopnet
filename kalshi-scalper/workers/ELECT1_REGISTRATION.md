# ELECT1 registration: cheap-side races on US midterm election night (2026-11-03)

Registered 2026-11-03, about 20:10 UTC, BEFORE polls close (23:00 UTC) and before any
race result is known. Discovery only. No live code, no L1, no OICORE, no promote verb.
Prices have NOT been looked at yet when this file is written; the rating mapping below
is fixed before any price is read.

## What it tests

Do cheap-side prices (ask 3c to 30c) in race-level winner markets on election night
under-price the true chance? A one-time, high-count forward sample. Counterparty hypothesis:
longshot bias, retail buying the favourite side and under-weighting independent
information (ratings) that already says the underdog has a real chance.

## Universe rule (metadata only, fixed now)

Every OPEN Kalshi market (status open, API at snapshot time) whose series is a US
race-level winner or party-winner market:

- Senate: series `SENATE??`, `SENATEPARTY*`, `KXSENATE??` (race winner, not nominee, not
  margin, not combo), plus `KXAKSENATE`.
- Governor: `GOVPARTY*`, `KXGOV??` race winner (not nominee markets `*NOM*`).
- House district: `HOUSE??n` style district series, `KXHOUSE??n`, `HOUSEPARTY-*`.
- Chamber control: `HOUSE`, `SENATE`, `KXHOUSE`, `KXSENATE`, `CONTROLH`, `CONTROLS`.
- Excluded: nominee/primary markets, margin/seat-count/bracket markets, combos, turnout,
  exit polls, non-US races, markets that are not open, any with `close_time` before the
  snapshot.

A market enters the universe if it has a yes bid and a yes ask quoted (both > 0), and
(volume >= 100 contracts or open interest >= 100). A market already effectively
decided by being called is excluded on quotes alone: yes ask >= 0.97 or yes bid <= 0.03
on BOTH sides (no side has ask between 3c and 30c) simply produces no trade under the
rule, so no separate call judgement is made (no outside knowledge of results is used).
Unit of analysis is the race (one trade per race, see below).

## Snapshot

As soon as this file is pushed, record every universe market's bid, ask, last, volume,
open interest and close time, each with its own UTC timestamp, to
`workers/ELECT1_SNAPSHOT_2026-11-03.csv`. Only these quotes count; any later quote does not.
Fill assumption: buy at the snapshot ask (taker) for 10 contracts (C=10). Quotes are
dollar strings from the public API. If the API is rate limited, markets missing from the
snapshot are listed in the result and are not traded.

## Rules (all held to settlement, one trade per race)

For each race the two candidate sides are the YES side of each market (a two-candidate
race has two markets or a yes/no pair; a one-market race offers YES and NO with the NO
ask = 1 - yes bid). Cheap side = a side with ask 0.03 to 0.30 inclusive. If a race has
several cheap candidates, take the one with the lowest ask (ties: lower ticker).

- **CONTROL (all cheap-band):** buy the cheap side of every race with a cheap side. No
  reference condition. Hard limit: ask <= 0.30.
- **REF rule (rating-implied probability at least 3x ask):** buy the cheap side only if
  the reference probability of that side winning is >= 3 x its ask, with hard limit
  ask <= 0.30. Races with no reference are not traded under REF.

### Reference (state which worked)

Tried in order: Silver Bulletin forecast (natesilver.net page loads but exposes no
keyless forecast table; not used), Wikipedia 2026 Senate / House / gubernatorial election
pages (reachable from this sandbox, raw wikitext, carries the Cook Political Report,
Sabato's Crystal Ball and Inside Elections ratings tables). **Reference = Wikipedia
ratings tables (Cook, Sabato, Inside Elections), consensus of the ones available per race.**
Pre-registered probability for the party the rating favours (fixed now, before prices):

| Rating | favoured party wins | underdog wins |
|---|---|---|
| Solid | 0.97 | 0.03 |
| Likely | 0.88 | 0.12 |
| Lean | 0.72 | 0.28 |
| Tilt | 0.60 | 0.40 |
| Toss-up | 0.50 | 0.50 |

Per race, average the mapped probabilities across the available raters (a rater that
disagrees on direction counts for its own side). Reference prob of a side = that average.
If the page ratings cannot be parsed for a race, the race has no reference.
Rating-based rule only: this is not a polling average; if a stronger keyless source
becomes reachable it is a different test.

## Numeric prediction

Pre-registered before results: control cheap-band win rate is BELOW the mean ask (the
usual longshot bias), so control net after fees is not above 0. REF rule: win rate at
least the mean ask paid, profit factor >= 1.5 (net of fee) would be the signal. Honest
expectation: the control is not profitable; the REF rule is the only way this passes.

## Costs

Fee per trade = ceil to the cent of 0.07 x C x p x (1-p) with C = 10 and p the fill
price, per order, applied to every entry (no fee on settlement). PF = gross wins net
of fee / gross losses plus fee.

## Correlation warning

Races are correlated through a national swing (a Democratic or Republican night moves
dozens of races together), so the effective sample is far smaller than the trade count.
Results are reported by party direction of the bought side, by race type (Senate,
Governor, House, control) and with a cluster-robust interval (clusters: race type x
state, and a bootstrap that resamples whole party directions by night) in addition to
the naive one. A pass cannot exceed **NOT_YET_FALSIFIED**: one night, one national
swing, no holdout.

## Kill rules

- **FALSIFIED**: mean net after fees per trade not above 0, or PF < 1.5, for the REF rule
  (CONTROL is reported as the baseline and does not by itself pass anything).
- **NOT_ENOUGH_DATA**: fewer than 150 trades under the rule at scoring.
- Otherwise NOT_YET_FALSIFIED (best case; cannot be higher).

## No holdout

It is a one-time event; there is no second sample and no holdout, said plainly. Nothing
here can promote anything. No ongoing capped probe follows from a single election; a
later cycle (primary season, 2028) would need its own registration.

## N

N +k: +2 per rule (CONTROL, REF) = **+4** counted by the coordinator.

## Settle-time read plan

Results arrive over the night and the next day. After 2026-11-04 12:00 UTC, run
`python3 -I src/scalper/elect1.py score workers/ELECT1_SNAPSHOT_2026-11-03.csv` which re-reads each
snapshot market's `result` from the public API (resumable, writes
`workers/ELECT1_RESULTS_RAW.csv`), then scores once. Markets still unsettled at that
time are listed and excluded; the score is then re-run only if more settle, with the
count of re-runs written in the result.
