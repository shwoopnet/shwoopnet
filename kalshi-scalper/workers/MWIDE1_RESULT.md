# MWIDE1 result (2026-11-05, US Central): FALSIFIED (passive cheap-side bids on wide-spread daily, weekly and monthly markets)

Registered first (`workers/MWIDE1_REGISTRATION.md`, commit 857b169, before any tape or outcome). Scored once with `python3 -I src/scalper/mwide1.py score` (raw output `data/mwide1_result.txt`, tape `data/mwide1_tape.json`, git-ignored). Window: markets closing 2026-09-04 to before the frozen cut 2026-10-03T16:00Z (nothing at or after it was fetched). Halves D1 (close before 2026-09-18 11:00 PM CT) and D2. Units: 759 posted orders on 98 series, 30 close days (cluster = UTC close date). Fee: taker formula 7% x C x p x (1-p) rounded up, C = 10 (maker rate unknown, not assumed). N +1 (about 730,441, deflated z bar about 5.27). No tape was truncated and no result was missing.

## Numbers first (pessimistic fill: only a taker print strictly below our bid proves a fill)
| | n | win vs price paid | net per contract | PF | day-clustered z |
|---|---|---|---|---|---|
| **Pessimistic fills (verdict)** | 541 of 759 posted (71%) | 10.2% vs 13.2c (gap -3.0 pt) | **-3.79c** | **0.68** | -3.33 |
| D1 | 297 | 9.8% vs 13.6c | -4.68c | 0.62 | -3.16 |
| D2 | 244 | 10.7% vs 12.6c | -2.71c | 0.75 | -1.68 |
| fees x1.2 | 541 | | -3.93c | 0.67 | -3.45 |
| maker fee 0 (information) | 541 | | -3.00c | 0.73 | -2.64 |
| YES-side bids / NO-side bids | 417 / 124 | | -2.99c / -6.47c | 0.73 / 0.51 | |
| Optimistic fills (a print at or below the bid) | 555 | 11.0% vs 13.0c | -2.80c | 0.76 | -2.39 |
| Per posted order, unfilled counted as zero | 759 | | **-2.70c** | | |
| Taker control, same trigger candle (cheap side ask 3c to 30c) | 357 | 12.3% vs 16.9c | -5.59c | 0.63 | -3.87 |
| Taker control restricted to the orders that filled | 310 | 8.1% vs 16.7c | -9.62c | 0.39 | -7.31 |
| **Unfilled orders, hypothetically bought at the bid** | 218 | 63.3% vs 9.2c | +53.47c | 25.1 | +16.1 |

## Verdict by the registered kill rules: FALSIFIED
PF under 1.5 in both halves (0.62, 0.75); net per fill negative in both; pooled z -3.33 (the bar was +5.27); PF 0.67 at fees x1.2; net per fill is only +1.8c above the all-triggers taker control and +5.8c above the taker control on the same filled markets, under the 6c bar and still negative. Prediction check: net -3c to -6c per fill (hit: -3.79c), PF 0.3 to 0.8 (hit: 0.68), win rate 2 to 5 points under price (hit: -3.0), unfilled orders earn more than filled (hit, enormously), fill rate 35% (MISSED: 71%).

## Read
- **This is adverse selection, measured.** The bid fills when the cheap side gets cheaper, which on a daily or weekly market is mostly the side losing as the close nears: the 541 fills win 10.2% against 13.2c paid, and the 218 orders that never filled would have won 63.3% (a bid that the price never traded below belongs to a side that was holding up). Same trap as MAKER2, MAKER3, MAKERMID1 (-3.78c on hourly Bitcoin) and L1Q1.
- **The 71% fill rate is the price of resting to the close.** Many fills are prints near expiry as a dying side collapses to 1c, which a live resting order would also get. Fill timing was not split (information, not registered).
- **The maker does beat the taker on the same markets** (-3.79c against -9.62c on the filled set), so the spread cushion is real, but it is only about two thirds of what adverse selection takes back. A cushion that small does not reach the pooled cheap-side baseline fix of 6c.
- Family table (pessimistic fills, picked from 98 series, flags only): no family has 30 fills; the best cells (KXRAINWKND +15.5c on 9, KXBIGGESTQUAKE +10.1c on 13, KXHIGHTSATX +35.1c on 4) are single digits to teens of orders and expected from 98 cells. The AAA gas price series (the most numerous, 21 states) are almost all negative (-7c to -20c).
- Caveats: fills are inferred from public prints, so a real queue could see fewer fills than the pessimistic model (a print below our bid proves the level cleared; resting orders can also be cancelled or missed by latency); entry is the hourly candle close, so the true best bid at post time is approximated; the sample overlaps NEWLIST1's hash sample (taker outcomes of the same markets were seen by that worker, no maker outcome).

## What the recorded data allow, and what accrual would be needed
- **RECDAILY (`daily/quotes`)**: 7 polls across 2026-11-04 to 11-05, 30 minute to 6 hour gaps, bid, ask, last, volume, no sizes and no tape. It cannot prove any fill, so it tests nothing about a resting bid. **`sportspre`** has bid and ask sizes but its markets are games, not daily, weekly or monthly, and its poll spacing is hours. **`book`** is hourly Bitcoin (MAKERTAIL1, MAKERMID1 own it). So the answer above comes from the public trade tape of settled markets, not from the recorders.
- A forward read would need no new recorder: the same rule on RECDAILY's markets after their close (the tape of a settled market stays on the public API). To reach 150 pessimistic fills in a window the same size as this one (30 close days, about 540 fills) the forward needs roughly 8 weeks of closes; 150 fills would take about 3 weeks. Not registered, because the verdict here is already a clear FALSIFIED (z -3.33, PF 0.68, both halves negative), so a forward read would only be worth it if a new condition (for example only series whose fills come early, or only wide books under 20c) were registered first, and that would be a new try with its own N.
- The frozen third (closes from 2026-10-03T16:00Z) was never fetched or scored.

Research only; no promote verb; nothing touches trading code.
