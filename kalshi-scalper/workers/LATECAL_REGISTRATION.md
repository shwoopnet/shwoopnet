# LATECAL registration (V2 worker, 2026-10-29, research only)

Written and pushed BEFORE any outcome column (`results.csv` `result`) was read. Ledger check: `workers/LATECAL_CHECK.md` (sub-minute surface not covered; HUNT2's finest step is 1 minute). Before writing this only the recorder's tickers were counted (Bitcoin about 257 windows Oct 22 to 29, gold about 58 windows Oct 28 to 29); no price was compared with any outcome.

## Question

Is Kalshi's own touch calibrated in the last 120 seconds? For a side quoted at ask p with s seconds left, does it win about p of the time?

## Data and universe (chosen on time only)

- `origin/quote-data` at b7dc9cbe8, `quotes/*/*/quotes.csv.gz` and `results.csv.gz`. Markets: `KXGOLD15M` (rows since 2026-10-28) and `KXBTC15M` (rows since 2026-10-22). Every window on file; none dropped for any price reason.
- Close time from the ticker (Eastern, EDT = UTC-4 through 2026-10-31). Seconds left s = close - t_recv_ms/1000.
- Sides: YES at `yes_ask` with size `ask_size`; NO at 1 - `yes_bid` with size `bid_size`.
- A poll is usable for a side if `status` is active, the quote is two-sided (0 < yes_bid < yes_ask < 1) and the side's size at its ask is at least 1 contract.
- Outcome: `result` from results.csv (yes or no), joined by ticker; a window with no result is dropped and counted.

## Cells (32 tries)

Time left s in {120 to 90, 90 to 60, 60 to 30, 30 to 10} (left-closed on the larger number: 120 >= s > 90, etc., last cell 30 >= s > 10) x the side's ask in {0.50 to 0.80, 0.80 to 0.90, 0.90 to 0.95, 0.95 to 0.98} (lower bound inclusive, upper exclusive; 0.98 excluded) x market (gold, Bitcoin) = 32 cells. For each window, cell and side: the FIRST usable poll in the time range whose side ask is in the band. One observation per window, cell and side (both sides can land in 0.50 to 0.80 if the book is wide; both kept, disclosed).

## Report per cell

n windows, win rate, mean ask, win minus ask with binomial z = (wins - sum p) / sqrt(sum p(1-p)), net per contract and profit factor after the fee rounded up to the cent per order (7% x C x p x (1-p)) at C = 1, also at C = 10 (fee per contract = rounded order fee / 10), and at fees x1.2. Fill check (information): the same at the NEXT poll's ask for that side (no next usable poll = no fill), because a quote seen at a poll may be gone 0.5 s later. Zero-volume candles: not applicable (polls, not candles); a poll with zero size at the ask is unusable by rule.

## Three windows by date

Per market, its windows ordered by close time and cut into thirds by count (T1, T2, T3). T3 is the holdout, read once.

## The one rule (1 try; total N = 33 for this worker)

**Rule.** Choose the cells (of the 32) whose win minus mean ask is at least **+0.03** on T1 and T2 pooled AND positive in each of T1 and T2, with at least 30 windows in T1 + T2. Then on T3, buy every side whose first usable poll falls in a chosen cell (1 contract, at that poll's ask, held to settlement). Cells are chosen only from T1 and T2; T3 is not looked at until the choice is written to the result file.

**Counterparty.** Late-window quoters who widen or pull quotes as settlement nears, leaving a stale or mispriced touch that a taker can hit.

**Prediction.** Cells scatter around zero (win minus ask within about +-3 points, |z| under 2 for most); a few cells pass the +3 point screen on T1 + T2 by chance; on T3 the chosen cells fall back toward zero or below: **FALSIFIED** (prior of a pass about 2%). The most likely "winners" on T1 + T2 are the 0.95 to 0.98 bands, where one loss costs about 97c, so a short run of no losses looks like underpricing.

**Verdict on T3 (read once).**
- `NOT_ENOUGH_DATA` if no cell is chosen with 30 windows, or the rule has fewer than 30 T3 trades. Any single cell with fewer than 30 windows in a window is `NOT_ENOUGH_DATA` for that cell.
- `FALSIFIED` if, with at least 30 T3 trades, T3 win minus ask is at or below 0, or T3 PF at C = 1 is under 1.5, or PF is under 1.5 in T1 or T2 for the chosen cells, or net is at or below 0 at fees x1.2 on T3.
- `NOT_YET_FALSIFIED` only if PF at least 1.5 in each of T1, T2 and T3 after rounded fees at C = 1 AND at the next-poll fill, positive at fees x1.2, and the pooled z (T1 to T3) at least 5.17 (the deflated bar for N about 439,000). PF at least 1.5 everywhere with z under 5.17 is `NOT_ENOUGH_DATA`, not a pass.

**Kill.** Fewer than 30 windows in a cell: that cell is `NOT_ENOUGH_DATA` and cannot be chosen.

## Tries

32 cells + 1 rule = **33**, each counted.

## Code

`workers/LATECAL_score.py` (written after this file is pushed). It reads the result column only after building the poll table, and prints T1 + T2 and the chosen cells before computing anything on T3.
