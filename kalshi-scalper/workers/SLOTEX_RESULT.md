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

## Amendment 1 result: C = 1, 5, 10 and entry price buckets

Registered in Amendment 1 (commit f85ec29, pushed before these cells were scored). Run: `PYTHONPATH=src python -m scalper.slotex --sizes`. Buckets use each row's own raw entry fill (so N and S buckets hold different entries); fee/ct is entry plus sell fees per contract, in cents.

| fill | exit | cost | n disc/val | C=1 PF disc | C=1 PF val | C=5 PF disc | C=5 PF val | C=10 PF disc | C=10 PF val |
|---|---|---|---|---|---|---|---|---|---|
| N | HOLD | base | 222/333 | 2.16 | 1.75 | 2.27 | 1.84 | 2.28 | 1.85 |
| N | HOLD | x1.2 | 222/333 | 2.13 | 1.72 | 2.24 | 1.81 | 2.26 | 1.82 |
| N | HOLD | +2c | 222/333 | 1.79 | 1.46 | 1.87 | 1.52 | 1.88 | 1.53 |
| N | X60 | base | 222/333 | 2.31 | 1.32 | 2.67 | 1.50 | 2.72 | 1.52 |
| N | X60 | x1.2 | 222/333 | 2.26 | 1.28 | 2.61 | 1.45 | 2.65 | 1.48 |
| N | X60 | +2c | 222/333 | 1.81 | 1.05 | 2.05 | 1.16 | 2.07 | 1.18 |
| N | TP5 | base | 222/333 | 2.31 | 1.32 | 2.67 | 1.50 | 2.72 | 1.52 |
| N | TP5 | x1.2 | 222/333 | 2.26 | 1.28 | 2.61 | 1.45 | 2.65 | 1.48 |
| N | TP5 | +2c | 222/333 | 1.81 | 1.05 | 2.05 | 1.16 | 2.07 | 1.18 |
| N | TP8 | base | 222/333 | 2.31 | 1.32 | 2.67 | 1.50 | 2.72 | 1.52 |
| N | TP8 | x1.2 | 222/333 | 2.26 | 1.28 | 2.61 | 1.45 | 2.65 | 1.48 |
| N | TP8 | +2c | 222/333 | 1.81 | 1.05 | 2.05 | 1.16 | 2.07 | 1.18 |
| N | TP5/SL2 | base | 222/333 | 2.31 | 1.32 | 2.67 | 1.50 | 2.72 | 1.52 |
| N | TP5/SL2 | x1.2 | 222/333 | 2.26 | 1.28 | 2.61 | 1.45 | 2.65 | 1.48 |
| N | TP5/SL2 | +2c | 222/333 | 1.81 | 1.05 | 2.05 | 1.16 | 2.07 | 1.18 |
| N | TP5/SL3 | base | 222/333 | 2.31 | 1.32 | 2.67 | 1.50 | 2.72 | 1.52 |
| N | TP5/SL3 | x1.2 | 222/333 | 2.26 | 1.28 | 2.61 | 1.45 | 2.65 | 1.48 |
| N | TP5/SL3 | +2c | 222/333 | 1.81 | 1.05 | 2.05 | 1.16 | 2.07 | 1.18 |
| N | TP5/SL4 | base | 222/333 | 2.31 | 1.32 | 2.67 | 1.50 | 2.72 | 1.52 |
| N | TP5/SL4 | x1.2 | 222/333 | 2.26 | 1.28 | 2.61 | 1.45 | 2.65 | 1.48 |
| N | TP5/SL4 | +2c | 222/333 | 1.81 | 1.05 | 2.05 | 1.16 | 2.07 | 1.18 |
| S | HOLD | base | 222/333 | 2.08 | 1.62 | 2.14 | 1.67 | 2.15 | 1.68 |
| S | HOLD | x1.2 | 222/333 | 2.06 | 1.60 | 2.12 | 1.65 | 2.12 | 1.65 |
| S | HOLD | +2c | 222/333 | 1.78 | 1.41 | 1.83 | 1.44 | 1.83 | 1.44 |
| S | X60 | base | 222/333 | 2.10 | 1.29 | 2.30 | 1.39 | 2.32 | 1.41 |
| S | X60 | x1.2 | 222/333 | 2.06 | 1.26 | 2.25 | 1.36 | 2.27 | 1.38 |
| S | X60 | +2c | 222/333 | 1.76 | 1.08 | 1.90 | 1.16 | 1.91 | 1.17 |
| S | TP5 | base | 222/333 | 1.99 | 1.09 | 2.18 | 1.20 | 2.21 | 1.21 |
| S | TP5 | x1.2 | 222/333 | 1.94 | 1.06 | 2.13 | 1.16 | 2.15 | 1.17 |
| S | TP5 | +2c | 222/333 | 1.60 | 0.93 | 1.73 | 1.01 | 1.75 | 1.02 |
| S | TP8 | base | 222/333 | 1.99 | 1.17 | 2.18 | 1.28 | 2.20 | 1.29 |
| S | TP8 | x1.2 | 222/333 | 1.94 | 1.13 | 2.12 | 1.24 | 2.15 | 1.25 |
| S | TP8 | +2c | 222/333 | 1.62 | 0.98 | 1.75 | 1.06 | 1.77 | 1.07 |
| S | TP5/SL2 | base | 222/333 | 1.02 | 0.80 | 1.15 | 0.90 | 1.17 | 0.91 |
| S | TP5/SL2 | x1.2 | 222/333 | 0.98 | 0.76 | 1.10 | 0.86 | 1.12 | 0.87 |
| S | TP5/SL2 | +2c | 222/333 | 0.69 | 0.65 | 0.77 | 0.72 | 0.78 | 0.73 |
| S | TP5/SL3 | base | 222/333 | 1.12 | 0.79 | 1.25 | 0.89 | 1.27 | 0.90 |
| S | TP5/SL3 | x1.2 | 222/333 | 1.08 | 0.76 | 1.20 | 0.85 | 1.22 | 0.86 |
| S | TP5/SL3 | +2c | 222/333 | 0.71 | 0.67 | 0.79 | 0.74 | 0.80 | 0.75 |
| S | TP5/SL4 | base | 222/333 | 1.16 | 0.79 | 1.30 | 0.89 | 1.32 | 0.90 |
| S | TP5/SL4 | x1.2 | 222/333 | 1.12 | 0.76 | 1.25 | 0.85 | 1.27 | 0.86 |
| S | TP5/SL4 | +2c | 222/333 | 0.78 | 0.68 | 0.86 | 0.75 | 0.87 | 0.76 |

Entry price buckets, base cost (raw entry fill). fee/ct = mean entry+sell fees per contract, cents.

| fill | exit | bucket | n disc/val | C=1 PF disc/val | C=1 fee/ct disc/val | C=5 PF disc/val | C=5 fee/ct disc/val | C=10 PF disc/val | C=10 fee/ct disc/val |
|---|---|---|---|---|---|---|---|---|---|
| N | HOLD | <10c | 122/171 | 3.02/1.74 | 1.00/1.00 | 3.60/2.07 | 0.35/0.35 | 3.66/2.10 | 0.29/0.29 |
| N | HOLD | 10-20c | 32/43 | 3.21/2.12 | 1.16/1.09 | 3.25/2.15 | 0.96/0.94 | 3.27/2.16 | 0.90/0.89 |
| N | HOLD | >20c | 68/119 | 1.53/1.66 | 1.94/1.95 | 1.56/1.69 | 1.54/1.55 | 1.56/1.70 | 1.50/1.51 |
| N | X60 | <10c | 122/171 | 2.35/1.05 | 1.90/1.75 | 3.39/1.47 | 0.69/0.60 | 3.55/1.53 | 0.56/0.49 |
| N | X60 | 10-20c | 32/43 | 4.39/1.39 | 2.44/2.21 | 4.74/1.49 | 1.69/1.47 | 4.78/1.50 | 1.58/1.37 |
| N | X60 | >20c | 68/119 | 1.70/1.42 | 3.34/3.28 | 1.81/1.51 | 2.38/2.40 | 1.83/1.52 | 2.28/2.31 |
| N | TP5 | <10c | 122/171 | 2.35/1.05 | 1.90/1.75 | 3.39/1.47 | 0.69/0.60 | 3.55/1.53 | 0.56/0.49 |
| N | TP5 | 10-20c | 32/43 | 4.39/1.39 | 2.44/2.21 | 4.74/1.49 | 1.69/1.47 | 4.78/1.50 | 1.58/1.37 |
| N | TP5 | >20c | 68/119 | 1.70/1.42 | 3.34/3.28 | 1.81/1.51 | 2.38/2.40 | 1.83/1.52 | 2.28/2.31 |
| N | TP8 | <10c | 122/171 | 2.35/1.05 | 1.90/1.75 | 3.39/1.47 | 0.69/0.60 | 3.55/1.53 | 0.56/0.49 |
| N | TP8 | 10-20c | 32/43 | 4.39/1.39 | 2.44/2.21 | 4.74/1.49 | 1.69/1.47 | 4.78/1.50 | 1.58/1.37 |
| N | TP8 | >20c | 68/119 | 1.70/1.42 | 3.34/3.28 | 1.81/1.51 | 2.38/2.40 | 1.83/1.52 | 2.28/2.31 |
| N | TP5/SL2 | <10c | 122/171 | 2.35/1.05 | 1.90/1.75 | 3.39/1.47 | 0.69/0.60 | 3.55/1.53 | 0.56/0.49 |
| N | TP5/SL2 | 10-20c | 32/43 | 4.39/1.39 | 2.44/2.21 | 4.74/1.49 | 1.69/1.47 | 4.78/1.50 | 1.58/1.37 |
| N | TP5/SL2 | >20c | 68/119 | 1.70/1.42 | 3.34/3.28 | 1.81/1.51 | 2.38/2.40 | 1.83/1.52 | 2.28/2.31 |
| N | TP5/SL3 | <10c | 122/171 | 2.35/1.05 | 1.90/1.75 | 3.39/1.47 | 0.69/0.60 | 3.55/1.53 | 0.56/0.49 |
| N | TP5/SL3 | 10-20c | 32/43 | 4.39/1.39 | 2.44/2.21 | 4.74/1.49 | 1.69/1.47 | 4.78/1.50 | 1.58/1.37 |
| N | TP5/SL3 | >20c | 68/119 | 1.70/1.42 | 3.34/3.28 | 1.81/1.51 | 2.38/2.40 | 1.83/1.52 | 2.28/2.31 |
| N | TP5/SL4 | <10c | 122/171 | 2.35/1.05 | 1.90/1.75 | 3.39/1.47 | 0.69/0.60 | 3.55/1.53 | 0.56/0.49 |
| N | TP5/SL4 | 10-20c | 32/43 | 4.39/1.39 | 2.44/2.21 | 4.74/1.49 | 1.69/1.47 | 4.78/1.50 | 1.58/1.37 |
| N | TP5/SL4 | >20c | 68/119 | 1.70/1.42 | 3.34/3.28 | 1.81/1.51 | 2.38/2.40 | 1.83/1.52 | 2.28/2.31 |
| S | HOLD | <10c | 89/120 | 1.10/0.82 | 1.00/1.00 | 1.17/0.87 | 0.56/0.55 | 1.18/0.88 | 0.52/0.51 |
| S | HOLD | 10-20c | 65/90 | 2.89/1.69 | 1.09/1.16 | 2.93/1.72 | 0.93/0.93 | 2.94/1.73 | 0.87/0.88 |
| S | HOLD | >20c | 68/123 | 2.21/1.93 | 2.00/2.00 | 2.26/1.96 | 1.54/1.60 | 2.26/1.97 | 1.49/1.55 |
| S | X60 | <10c | 89/120 | 1.45/0.75 | 1.94/1.77 | 1.69/0.87 | 0.94/0.84 | 1.72/0.89 | 0.84/0.74 |
| S | X60 | 10-20c | 65/90 | 2.93/1.03 | 2.25/2.10 | 3.15/1.10 | 1.49/1.35 | 3.19/1.11 | 1.36/1.23 |
| S | X60 | >20c | 68/123 | 2.04/1.72 | 3.28/3.28 | 2.16/1.81 | 2.30/2.39 | 2.17/1.82 | 2.19/2.29 |
| S | TP5 | <10c | 89/120 | 1.23/0.65 | 2.03/1.85 | 1.44/0.77 | 1.07/0.93 | 1.47/0.79 | 0.96/0.84 |
| S | TP5 | 10-20c | 65/90 | 2.70/0.70 | 2.37/2.26 | 2.91/0.76 | 1.66/1.51 | 2.95/0.77 | 1.53/1.40 |
| S | TP5 | >20c | 68/123 | 2.08/1.63 | 3.40/3.50 | 2.21/1.73 | 2.51/2.69 | 2.22/1.74 | 2.41/2.60 |
| S | TP8 | <10c | 89/120 | 1.29/0.70 | 2.04/1.87 | 1.51/0.82 | 1.07/0.92 | 1.54/0.83 | 0.96/0.83 |
| S | TP8 | 10-20c | 65/90 | 2.72/0.75 | 2.37/2.22 | 2.93/0.81 | 1.66/1.49 | 2.97/0.82 | 1.53/1.37 |
| S | TP8 | >20c | 68/123 | 2.02/1.74 | 3.38/3.45 | 2.14/1.84 | 2.49/2.63 | 2.16/1.85 | 2.38/2.54 |
| S | TP5/SL2 | <10c | 89/120 | 1.13/0.62 | 2.18/2.11 | 1.39/0.78 | 1.10/0.98 | 1.42/0.80 | 0.99/0.87 |
| S | TP5/SL2 | 10-20c | 65/90 | 1.31/0.48 | 2.28/2.38 | 1.42/0.54 | 1.60/1.59 | 1.44/0.55 | 1.49/1.48 |
| S | TP5/SL2 | >20c | 68/123 | 0.76/1.08 | 3.60/3.63 | 0.83/1.16 | 2.74/2.82 | 0.84/1.17 | 2.64/2.74 |
| S | TP5/SL3 | <10c | 89/120 | 1.23/0.61 | 2.16/2.09 | 1.50/0.75 | 1.08/0.96 | 1.54/0.77 | 0.97/0.86 |
| S | TP5/SL3 | 10-20c | 65/90 | 1.52/0.47 | 2.29/2.38 | 1.65/0.53 | 1.61/1.58 | 1.67/0.54 | 1.49/1.47 |
| S | TP5/SL3 | >20c | 68/123 | 0.76/1.09 | 3.60/3.62 | 0.83/1.17 | 2.74/2.82 | 0.84/1.18 | 2.64/2.74 |
| S | TP5/SL4 | <10c | 89/120 | 1.26/0.58 | 2.16/2.08 | 1.53/0.71 | 1.09/0.95 | 1.56/0.73 | 0.98/0.84 |
| S | TP5/SL4 | 10-20c | 65/90 | 1.64/0.54 | 2.31/2.41 | 1.78/0.60 | 1.61/1.60 | 1.81/0.61 | 1.50/1.49 |
| S | TP5/SL4 | >20c | 68/123 | 0.76/1.05 | 3.60/3.60 | 0.83/1.13 | 2.74/2.80 | 0.84/1.14 | 2.64/2.72 |

### Read (amendment)

- **Size matters for the early exits, not for holding.** Hold N validation PF is 1.75 / 1.84 / 1.85 at C = 1 / 5 / 10; X60 N is 1.32 / 1.50 / 1.52. An early exit pays a second rounded-up fee, and at C = 1 each one is a full cent: under 10c, mean fees are 1.75c to 1.90c a contract at C = 1 against 0.49c to 0.56c at C = 10, which is the whole drop (X60 N under 10c, val PF 1.05 at C = 1 vs 1.53 at C = 10).
- **Bucket mix:** with fill N, the under 10c entries are 293 of 555 and carry most of the hold edge (val PF 2.10 at C = 10). Under X60 the over 20c bucket is the steadiest (val 1.52 at C = 10, 1.42 at C = 1) and the 10c to 20c bucket is thin (n 32 / 43). With fill S the under 10c bucket loses in validation under every rule (PF 0.82 to 0.89 at C = 10).
- Buckets are descriptive; no verdict per bucket (registered).

### Verdicts added by size (same kill rule)

- X60 fill N (and its identical TP/stop rows): C = 10 NOT_YET_FALSIFIED (val 1.52; x1.2 1.48; +2c 1.18), C = 5 NOT_YET_FALSIFIED by the narrowest margin (val 1.50; x1.2 1.45; +2c 1.16), **C = 1 FALSIFIED** (val 1.32).
- Every fill S slot-legal variant stays FALSIFIED at C = 1 and 5 (val PF 0.79 to 1.39).
- None reaches the RULES bar (PF 1.5 at fees x1.2 in every window, deflated z about 5.17): val PF at fees x1.2 is below 1.5 at every size, and val day z for X60 N at C = 10 is 2.61.

Total N added by SLOTEX: 504 (84 + 168 + 252).
