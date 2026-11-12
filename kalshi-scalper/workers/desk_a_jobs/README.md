# Idea Desk A: pull job files, ready for the day `kalshi-pull` is approved (Nov 12, 2026)

**Nothing here runs.** `kalshi-pull` is a design only (`workers/KALSHI_PULL_DESIGN.md`) and is on HOLD until a person has read Kalshi's Developer Agreement and Terms of Use. These files follow that design's schema (an endpoint id plus typed fields, no free path; a hard request cap; `heldout` stated). Public market data only: no key, no account, no order. When the workflow exists they move to the `pull-jobs` branch unchanged and Main dispatches them by commit.

| Job file | For | Entries | Requests, worst case | Reads a result or a price? | Should it run? (see `DESK_A_POWER_NOV12.md`) |
|---|---|---|---|---|---|
| `DESKA_WXDAYEND_A.json` | finishing card 74's registered 40 city-day sample | 18 candle reads + 4 lists | 22 | prices of already-settled brackets, development sample only | Yes, but last: it closes the card under its own rule |
| `DESKA_ECONFADE_0A.json` | card 87, step 0 part A: the market lists | 6 | 16 | no price | Only if Main wants the one falsification run |
| `DESKA_POLN1_UNIVERSE.json` | POL-n1 step 1: market open and close dates | 20 | 20 | no price | Recommended NOT to run: the card cannot reach a verdict |

Two follow-on jobs cannot be written exactly until their first part has answered, because their tickers come from that answer. They are specified here so writing them takes minutes:

- **`DESKA_WXDAYEND_B`** (4 requests). For each of the four Nov 10 events listed by job A, the one market whose `result` is `yes`: `{"ep": "candles", "series": <series>, "ticker": <that ticker>, "start_ts": close - 7200, "end_ts": close, "period": 1}`, with `close` = that market's `close_time`. Then the registered rule is read over all 40: FAIL if fewer than 3 show an ask at or under 0.96 after the local day ended. Denver's 9 include the 2 Refinement already read (their run did not record which); the repeat costs 2 requests and keeps the job exact.
- **`DESKA_ECONFADE_0B`** (about 70 requests, cap 80). One `candles` (or `hist_candles` for markets before the live cutoff) entry per CPI or payrolls release in the committed event file: the market of the NEXT Fed meeting nearest 50c at the previous day's close, `period` 1, `start_ts` = release time minus 1,800 s, `end_ts` = release time plus 1,500 s. The event file (`event_id, kind, release_utc, source line`, keyed by hand from the BLS release archive) is committed BEFORE this job is written. Counts only: shocks and confirmed retraces. NOT_ENOUGH_DATA and stop under 80 qualifying events, before any outcome is read.

How the winning weather brackets in job A were found without a Kalshi read: the weather recorder's own results files on `quote-data` (`wxens/results/`), which list each settled market's result and close time. Nov 10 was not in them yet, hence the 4 list reads.

Not written, on purpose: no job for PERPBIN1, MMMAP1 or RESIL1 (they need no reads), none for ORHARVEST1 or RACEMAKE1 (parked behind MMSIM1, and what they need is a recorder, not a pull), and none for the queue rows this desk does not own (Refinement's and V2's pulls are theirs to write).
