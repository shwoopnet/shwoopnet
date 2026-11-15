# EXITREPLAY1 gold hold, haircut recompute build 1: hand case (Idea Desk C, Nov 15, 2026, written before the code)

The rule is EXITREPLAY1's hold arm as printed (Forensics, `exitreplay1.py`), recomputed under the Head of R&D's rules of Nov 15, 14:31Z.

**The rule.**
- **Universe:** KXGOLD15M windows in R6's `book15r6/*/*/coverage.csv.gz`.
  - The close must be from 2026-10-29T00:00Z to before **2026-11-07T20:24Z**. That cut is S-HOLDVSSELL's held-out start; windows at or after it are counted as `cut_dropped`, never read.
  - The result must be yes or no; otherwise `dropped_no_result`.
  - The worst `max_gap_ms` over the runs that saw it must be 15,000 or less; otherwise `dropped_gap`.
  - A window seen in several runs is one window. Its result is the first yes or no seen.
- **Books:** each ticker's rows, with duplicate (ticker, t_recv_ms) rows dropped.
  - A row is usable if yes_bid_px_1 and no_bid_px_1 are both present, yes_bid_px_1 < 1 - no_bid_px_1, and t < close.
- **Look:** the last usable row with t in [close - 370 s, close - 360 s]. None means `no_look`.
- **Side:** YES ask = 1 - no_bid_px_1, NO ask = 1 - yes_bid_px_1. YES if its ask is in [0.88, 0.97], else NO if its ask is in the band, else `no_band`. Both edges are inclusive, with 1e-9.
- **Fill and fee:**
  - Entry at the ask seen (RAW), at the ask seen + 1c, and at + 2c.
  - The fee is per order, rounded up to the cent, for 1 contract: ceil(7% x p x (1 - p) x 100) / 100.
  - The entry is 360 s before the close, so C8's 2c-primary rule does not apply.
  - Held to settlement: a win pays 1 - ask - fee, a loss is -(ask + fee).
- **Statistics:**
  - PF = the sum of positive results over the sum of losses; a zero result counts as neither.
  - Halves: entries sorted by close time; half 1 is the first floor(n/2), half 2 is the rest.
- **The bar (counting only):** PF 1.3 or better at 1c with both halves 1.0 or better at 1c, AND PF 1.0 or better at 2c.
- **Label:** "book replay, upper bound on queue; upper bound, not fill-checked".

**Hand files.** `hand/book15r6/`, two invented runs.

| Window | Close (UTC) | Result | Look row | Expected |
|---|---|---|---|---|
| A | 10-30 12:15 | yes | rows at -368 s (0.80/0.18) and -362 s (0.90/0.08); seen in two runs (gaps 5,000 and 9,000) with one duplicate row | last row is used, YES at 0.92 |
| B | 10-31 08:00 | yes | yes_bid 0.06, no_bid 0.89 | NO at 0.94, a loss |
| C | 11-02 | no | gap 20,000 | `dropped_gap` |
| D | 11-03 | yes | only row at -380 s | `no_look` |
| E | 11-04 | yes | ask 0.85 | `no_band` |
| J | 11-05 | empty | | `dropped_no_result` |
| F | 11-06 10:00 | yes | yes_bid 0.95, no_bid 0.03 | YES at 0.97 (edge) |
| I | 11-07 20:30 | | | after the cut: `cut_dropped` |
| G | 11-08 | | | after the cut: `cut_dropped` |
| H | | | KXBTC15M | ignored |

**Expected by hand.**
- **Counts:**
  - listed gold windows in the date range: 9 (A, B, C, D, E, J, F, I, G);
  - cut_dropped 2; dropped_no_result 1; dropped_gap 1;
  - no_look 1; no_band 1; entries 3 (A, B, F).
- **A, YES, won:**
  - RAW: ask 0.92, fee ceil(0.5152) = 1c, +0.07;
  - 1c: ask 0.93, fee 1c, +0.06;
  - 2c: ask 0.94, fee 1c, +0.05.
- **B, NO, lost:**
  - RAW: ask 0.94, fee ceil(0.3948) = 1c, -0.95;
  - 1c: ask 0.95, fee 1c, -0.96;
  - 2c: ask 0.96, fee 1c, -0.97.
- **F, YES, won:**
  - RAW: ask 0.97, fee ceil(0.2037) = 1c, +0.02;
  - 1c: ask 0.98, fee 1c, +0.01;
  - 2c: ask 0.99, fee ceil(0.0693) = 1c, 0.00.
- **Halves (n = 3):** half 1 = [A], half 2 = [B, F].

| Basis | PF | Half 1 | Half 2 |
|---|---|---|---|
| RAW | 0.09 / 0.95 = 0.0947 | inf | 0.02 / 0.95 = 0.0211 |
| 1c | 0.07 / 0.96 = 0.0729 | inf | 0.01 / 0.96 = 0.0104 |
| 2c | 0.05 / 0.97 = 0.0515 | inf | 0.00 / 0.97 = 0.0 |

- **Bar:** not met, "does not count: fails the haircut".

## Amendment 1 (Nov 15, 2026, 14:37Z, before the run; the Head of R&D's Option A)

**The cut moves to 2026-11-05T00:00Z.** RESIL1 reserves R6 closes from Nov 5. RESIL1 is closed unread, but under the Head's ruling a reserved window stays cut for price and result reads. So only Forensics' D block (Oct 29 to Nov 4) is read.

Expected on the same hand files:
- **Cut windows:** J (11-05), F (11-06), I and G are at or after the cut and are counted, never read.
- **Counts:** listed 9, cut_dropped 4, dropped_no_result 0, dropped_gap 1 (C), no_look 1 (D), no_band 1 (E), entries 2 (A and B).
- **Halves (n = 2):** half 1 = [A], half 2 = [B].

| Basis | PF | Half 1 | Half 2 | Net |
|---|---|---|---|---|
| RAW | 0.07 / 0.95 = 0.0737 | inf | 0.0 | -0.88 |
| 1c | 0.06 / 0.96 = 0.0625 | inf | 0.0 | -0.90 |
| 2c | 0.05 / 0.97 = 0.0515 | inf | 0.0 | -0.92 |

- **Bar:** "does not count: fails the haircut".
