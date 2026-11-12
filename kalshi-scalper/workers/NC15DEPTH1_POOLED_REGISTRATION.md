# NC15DEPTH1, ONE pooled cell (registered Nov 12, 2026, BEFORE any NC15 outcome is read)

Idea Desk A, on the Head of R&D's job order (cell registration, counts only, due before Nov 19). Card: `IDEA_CARDS_NOV11B` card 12 on V2's branch (depth and imbalance on the non-crypto 15 minute books), which has no cell definition and no development estimate; this file supplies the definition. Research only: no order, no key, zero Kalshi requests (files already on `nc-data:nc15/`). **No `result` column, no settlement and no price move after the look has been read for this file.** Only the file names, the coverage columns that describe polling, and (after this commit) the book columns at the look are used, to count.

**Not a duplicate.** Closest existing mechanism: DEPTH1 (gold and Bitcoin five level imbalance at 8 minutes, V2). This is the same data structure on the eleven non-crypto series, a different universe and look, pooled into one cell; it is not a favourite-late rule (entry band 0.10 to 0.90 and either side). Counterparty (hypothesis, not a finding): a resting maker who leaves one side thin and is swept; if the result cannot support it the result file reads "no counterparty named".

## The cell (one, fixed now)

- Universe: the eleven `nc15` series (`KXSILVER15M, KXCOPPER15M, KXWTI15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXHYPE15M, KXBNB15M, KXAUDUSD15M, KXUSDCAD15M, KXNATGAS15M`), pooled. Not split by series, now or later.
- Look: the last poll at or before close minus 600 s, no more than 10 s earlier (exchange time: offset = median of Date header + 0.5 s minus `t_recv_ms` over the run). No poll = window not in the cell (counted).
- Feature: `imb5` = (sum of the five YES bid sizes minus sum of the five NO bid sizes) / their total, from that poll.
- Cell membership: `abs(imb5) >= 0.50`. Direction: `imb5 > 0` buys YES (NO side thin), `imb5 < 0` buys NO. The threshold 0.50 is a round number chosen before any data was looked at and is not tuned.
- Trade: 1 contract of the implied side at its best ask, at the first poll at or after the look plus 1.0 s (within 20 s), ask 0.10 to 0.90 with at least 1 contract displayed, else no trade (counted). Held to settlement. Fee 7% x p x (1 - p), rounded up to the cent per order; stress x1.2. No exit, no resting order.
- Unit: one market window is one trade; z clustered by US Central date.

## Sample and counts

- **Forward only.** Scoring uses windows closing at or after `2026-11-19T00:00:00Z` (a date constant). Windows before it are used for COUNTS ONLY (how many fall in the cell) and are never scored, so nothing already recorded is both counted and read for outcome.
- Counts (done now, no outcome): windows per series with a look poll, windows in the cell, windows with the entry ask in the band. These go to the Head of R&D.
- **Assumption, stated:** there is no development estimate, so the effect size is an assumption (3c a contract, 1.5c if shrunk), per V2's `POWER2_QUEUE.md`. Under 3c the cell needs about 3,400 to 5,400 cell windows; under 1.5c about 13,700 to 21,000.

## Labels and bar (fixed now)

- **Minimum before any read:** 3,400 scored cell trades. Nothing is read below it. The recorder stops by itself on 2026-12-31; a read is then taken on what exists.
- Cleared its registered bar: n of 3,400 or more; cash PF 1.5 or better pooled and in each third by close date; both halves above 1.0; mean net above 0 at fee x1.2; date-clustered z of 5.46 or more (one-sided; the shared strict N is about 2,113,000 per the Head of R&D's ledger). Never called a research-bar pass.
- FALSIFIED: cash PF under 1.0 pooled with n of 1,000 or more. Below about 100 trades: "no evidence at n = x". Anything between: keep recording.
- **Try count: N +1** (one cell, one look, one feature, one pooled figure). No other look, threshold or series split will be tried.
