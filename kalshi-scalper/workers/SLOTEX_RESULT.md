# SLOTEX result (2026-10-30)

Registration: `workers/SLOTEX_REGISTRATION.md` (pushed before scoring, commit 1548d7c). Code: `src/scalper/slotex.py` (reuses `fals4.py`). N added = 84 cells (7 exits x 2 fills x 3 costs x 2 stages). Bitcoin `KXBTC15M` only, windows closing 2026-08-06 to 2026-10-27; nothing on or after 2026-10-28 read.

The baseline reproduces GEN6/FALS4 exactly: hold, next-candle fill, disc n 222 PF 2.28, val n 333 PF 1.85.

## Table (C = 10, fees on entry and every sell, bid 0 or missing at a sell point = stake lost)

Fill N = next candle's ask (-120 s); fill S = signal candle's ask (-180 s). Exit mix = share exiting by take profit / stop / at 60 s. Nonzero bid at 60 s is the share of entries whose held side had a bid above 0 at the -60 candle (same entries for both fills).

| fill | exit | cost | disc n | disc PF | disc net $ | val n | val PF | val net $ | exit mix disc (tp/stop/60s) | exit mix val | nonzero bid@60s disc/val |
|---|---|---|---|---|---|---|---|---|---|---|---|
| N | HOLD | base | 222 | 2.28 | 237.48 | 333 | 1.85 | 254.96 | - | - | 89.6%/83.2% |
| N | HOLD | x1.2 | 222 | 2.26 | 234.47 | 333 | 1.82 | 250.14 | - | - | 89.6%/83.2% |
| N | HOLD | +2c | 222 | 1.88 | 191.10 | 333 | 1.53 | 185.62 | - | - | 89.6%/83.2% |
| N | X60 | base | 222 | 2.72 | 210.78 | 333 | 1.52 | 118.77 | 0%/0%/100% | 0%/0%/100% | 89.6%/83.2% |
| N | X60 | x1.2 | 222 | 2.65 | 205.97 | 333 | 1.48 | 111.28 | 0%/0%/100% | 0%/0%/100% | 89.6%/83.2% |
| N | X60 | +2c | 222 | 2.07 | 164.40 | 333 | 1.18 | 49.43 | 0%/0%/100% | 0%/0%/100% | 89.6%/83.2% |
| N | TP5 | base | 222 | 2.72 | 210.78 | 333 | 1.52 | 118.77 | 32%/0%/68% | 27%/0%/73% | 89.6%/83.2% |
| N | TP5 | x1.2 | 222 | 2.65 | 205.97 | 333 | 1.48 | 111.28 | 32%/0%/68% | 27%/0%/73% | 89.6%/83.2% |
| N | TP5 | +2c | 222 | 2.07 | 164.40 | 333 | 1.18 | 49.43 | 32%/0%/68% | 27%/0%/73% | 89.6%/83.2% |
| N | TP8 | base | 222 | 2.72 | 210.78 | 333 | 1.52 | 118.77 | 32%/0%/68% | 26%/0%/74% | 89.6%/83.2% |
| N | TP8 | x1.2 | 222 | 2.65 | 205.97 | 333 | 1.48 | 111.28 | 32%/0%/68% | 26%/0%/74% | 89.6%/83.2% |
| N | TP8 | +2c | 222 | 2.07 | 164.40 | 333 | 1.18 | 49.43 | 31%/0%/69% | 26%/0%/74% | 89.6%/83.2% |
| N | TP5/SL2 | base | 222 | 2.72 | 210.78 | 333 | 1.52 | 118.77 | 32%/40%/28% | 27%/40%/33% | 89.6%/83.2% |
| N | TP5/SL2 | x1.2 | 222 | 2.65 | 205.97 | 333 | 1.48 | 111.28 | 32%/40%/28% | 27%/40%/33% | 89.6%/83.2% |
| N | TP5/SL2 | +2c | 222 | 2.07 | 164.40 | 333 | 1.18 | 49.43 | 32%/53%/15% | 27%/54%/19% | 89.6%/83.2% |
| N | TP5/SL3 | base | 222 | 2.72 | 210.78 | 333 | 1.52 | 118.77 | 32%/32%/35% | 27%/37%/36% | 89.6%/83.2% |
| N | TP5/SL3 | x1.2 | 222 | 2.65 | 205.97 | 333 | 1.48 | 111.28 | 32%/32%/35% | 27%/37%/36% | 89.6%/83.2% |
| N | TP5/SL3 | +2c | 222 | 2.07 | 164.40 | 333 | 1.18 | 49.43 | 32%/46%/22% | 27%/48%/26% | 89.6%/83.2% |
| N | TP5/SL4 | base | 222 | 2.72 | 210.78 | 333 | 1.52 | 118.77 | 32%/27%/41% | 27%/35%/38% | 89.6%/83.2% |
| N | TP5/SL4 | x1.2 | 222 | 2.65 | 205.97 | 333 | 1.48 | 111.28 | 32%/27%/41% | 27%/35%/38% | 89.6%/83.2% |
| N | TP5/SL4 | +2c | 222 | 2.07 | 164.40 | 333 | 1.18 | 49.43 | 32%/40%/28% | 27%/40%/33% | 89.6%/83.2% |
| S | HOLD | base | 222 | 2.15 | 266.40 | 333 | 1.68 | 268.00 | - | - | 89.6%/83.2% |
| S | HOLD | x1.2 | 222 | 2.12 | 262.46 | 333 | 1.65 | 261.87 | - | - | 89.6%/83.2% |
| S | HOLD | +2c | 222 | 1.83 | 219.95 | 333 | 1.44 | 198.71 | - | - | 89.6%/83.2% |
| S | X60 | base | 222 | 2.32 | 239.70 | 333 | 1.41 | 131.81 | 0%/0%/100% | 0%/0%/100% | 89.6%/83.2% |
| S | X60 | x1.2 | 222 | 2.27 | 233.96 | 333 | 1.38 | 123.01 | 0%/0%/100% | 0%/0%/100% | 89.6%/83.2% |
| S | X60 | +2c | 222 | 1.91 | 193.25 | 333 | 1.17 | 62.52 | 0%/0%/100% | 0%/0%/100% | 89.6%/83.2% |
| S | TP5 | base | 222 | 2.21 | 193.97 | 333 | 1.21 | 58.84 | 43%/0%/57% | 39%/0%/61% | 89.6%/83.2% |
| S | TP5 | x1.2 | 222 | 2.15 | 187.49 | 333 | 1.17 | 48.87 | 43%/0%/57% | 39%/0%/61% | 89.6%/83.2% |
| S | TP5 | +2c | 222 | 1.75 | 143.41 | 333 | 1.02 | 5.45 | 42%/0%/58% | 37%/0%/63% | 89.6%/83.2% |
| S | TP8 | base | 222 | 2.20 | 197.73 | 333 | 1.29 | 83.95 | 42%/0%/58% | 37%/0%/63% | 89.6%/83.2% |
| S | TP8 | x1.2 | 222 | 2.15 | 191.29 | 333 | 1.25 | 74.19 | 42%/0%/58% | 37%/0%/63% | 89.6%/83.2% |
| S | TP8 | +2c | 222 | 1.77 | 149.90 | 333 | 1.07 | 23.18 | 41%/0%/59% | 35%/0%/65% | 89.6%/83.2% |
| S | TP5/SL2 | base | 222 | 1.17 | 26.13 | 333 | 0.91 | -23.04 | 28%/71%/0% | 31%/68%/1% | 89.6%/83.2% |
| S | TP5/SL2 | x1.2 | 222 | 1.12 | 19.26 | 333 | 0.87 | -33.63 | 28%/71%/0% | 31%/68%/1% | 89.6%/83.2% |
| S | TP5/SL2 | +2c | 222 | 0.78 | -42.81 | 333 | 0.73 | -83.89 | 26%/73%/1% | 27%/73%/0% | 89.6%/83.2% |
| S | TP5/SL3 | base | 222 | 1.27 | 43.06 | 333 | 0.90 | -25.57 | 30%/69%/1% | 32%/66%/3% | 89.6%/83.2% |
| S | TP5/SL3 | x1.2 | 222 | 1.22 | 36.23 | 333 | 0.86 | -36.11 | 30%/69%/1% | 32%/66%/3% | 89.6%/83.2% |
| S | TP5/SL3 | +2c | 222 | 0.80 | -38.82 | 333 | 0.75 | -77.68 | 26%/73%/1% | 28%/72%/0% | 89.6%/83.2% |
| S | TP5/SL4 | base | 222 | 1.32 | 51.46 | 333 | 0.90 | -27.24 | 31%/67%/3% | 32%/64%/4% | 89.6%/83.2% |
| S | TP5/SL4 | x1.2 | 222 | 1.27 | 44.60 | 333 | 0.86 | -37.77 | 31%/67%/3% | 32%/64%/4% | 89.6%/83.2% |
| S | TP5/SL4 | +2c | 222 | 0.87 | -24.43 | 333 | 0.76 | -76.43 | 27%/72%/1% | 29%/71%/1% | 89.6%/83.2% |

Day-clustered z (base cost): hold N disc 4.09 / val 4.42; X60 N disc 4.64 / val 2.61; X60 S disc 4.09 / val 2.65.

## Read

- **With fill N every slot-legal exit is X60.** The only candle after the -120 entry candle and at or before -60 is -60 itself, so TP5, TP8 and the three stops sell at the same bid as X60 (stated in the registration). Their exit-mix columns only label why the -60 bid was taken. The real choice is hold vs X60.
- **X60, fill N** (the one slot-legal exit worth a number): disc PF 2.72, val PF 1.52 (net $118.77 vs $254.96 held). Fees x1.2: val 1.48. Entry +2c: val 1.18. Exiting at 60 s gives up about half the validation profit of holding; the edge is mostly in the settlement payoff, as predicted, though the prediction (val PF below 1.2) was too pessimistic at base cost.
- **Fill S** adds a -120 candle for the TP/stop to see. TP5 and TP8 lower the validation PF (1.21, 1.29) versus X60 S (1.41): taking +5c or +8c cuts the winners that go on to much more. **Stops of 2c to 4c are hit by 64% to 71% of entries** at the next candle, because a stop measured from the entry ASK against the next BID sits inside the bid/ask spread of a 5c to 50c side; every stop variant is below PF 1.0 in validation.
- Nonzero bid at 60 s: 89.6% (disc), 83.2% (val). The other 10% to 17% of entries are booked as a total loss under X60 even though some of them would settle as wins (a held side bid at 0 with 60 s left is mostly a side about to lose, but not always).
- Candle bid is the 1 minute closing snapshot. Touches of the TP or stop inside a minute are not seen, and the sale is assumed at that closing bid for 10 contracts with no depth check (top of book size not modelled), which flatters the exits.

## Verdicts (registered kill rule: PF >= 1.5 in both stages at base, > 1.0 at fees x1.2 and at +2c)

- X60, fill N (and TP5, TP8, TP5/SL2-4 with fill N, identical by construction): **NOT_YET_FALSIFIED**, at the edge: val PF 1.52 base, 1.48 at fees x1.2 (below the RULES bar of 1.5 there), 1.18 at +2c; val day z 2.61, far below the deflated bar (about 5.17). Two windows only. A pass would earn only a forward test registration; this does not reach the RULES bar.
- X60, fill S: **FALSIFIED** (val PF 1.41).
- TP5, TP8 with fill S: **FALSIFIED** (val PF 1.21, 1.29).
- TP5 with stops 2c, 3c, 4c, fill S: **FALSIFIED** (val PF 0.90 to 0.91; stops sit inside the spread).
- HOLD is the reference, not slot-legal.
