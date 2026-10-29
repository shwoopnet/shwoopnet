# PPW1 result (Strategy Research V2, 2026-10-29, research only)

Registration: `workers/PPW1_REGISTRATION.md` (pushed before scoring, commit 417be88). Script: `src/scalper/ppw1.py`. Raw output: `data/ppw1_ab_result.txt`, `data/ppw1_c_result.txt` (ignored data folder; figures copied below).

## Thirds A and B (written before the holdout third C was run)

`tstop1.load()` returned 32,621 entries at run time (32,499 when the registration was written; the fresh database grew by a few days), so the thirds' cut points moved slightly. Zero-volume fill candles: none among the units of any of the three rules, so the "dropped" reads equal the "all" reads.

- CHEAP1-C: PF diff (cheapest minus list order) A +0.021, B -0.028; pooled difference +0.13c a window, z +0.49. Fails the lever bar in B.
- CHEAP1-M: PF diff A -0.145, B -0.037; pooled -0.29c, z -0.88. Fails in A and B.
- SCALEIN1: add leg alone PF A 0.938, B 1.045 (n 528, 500; loss 11.6%, 10.8%; profit per win +10.9c, +11.2c). Fails the strategy bar.

## Holdout third C (run once, after the A and B lines above were written)

PF at 1 contract (10 contracts), close-date thirds A / B / C. "Comparison" is what live does now.

| Rule | Units (differing) A / B / C | PF comparison | PF rule | PF rule at C=10 | Profit per win, comparison vs rule | Loss rate, comparison vs rule | Net per unit, rule | Pooled diff, z | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| CHEAP1-C cheapest of BTC/ETH/XRP/DOGE vs list order | 1,834 (636) / 1,645 (548) / 1,572 (477) | 1.246 / 1.132 / 1.040 | 1.267 / 1.104 / 0.966 | 1.341 / 1.170 / 1.025 | +6.4c vs +7.4c (all thirds) | 5.2/5.8/6.2% vs 6.1/6.9/7.6% | +1.48 / +0.66 / -0.24c | -0.06c a window, z -0.27 | **FALSIFIED** |
| (information) the same without XRP | 1,610 (419) / 1,465 (355) / 1,422 (327) | 1.175 / 1.112 / 0.961 | 1.210 / 1.100 / 0.913 | 1.288 / 1.172 / 0.973 | +6.4c vs +7.1c | 5.6/5.9/6.7% vs 6.0/6.6/7.7% | +1.16 / +0.60 / -0.62c | -0.03c, z -0.15 | not a try |
| CHEAP1-M silver when cheaper vs gold | 623 (123) / 562 (136) / 491 (116) | 1.407 / 1.045 / 1.170 | 1.262 / 1.008 / 1.136 | 1.353 / 1.074 / 1.211 | +6.1-6.4c vs +6.7-7.1c | 4.5/6.2/5.5% vs 5.5/7.1/6.3% | +1.32 / +0.05 / +0.79c | -0.23c, z -0.88 | **FALSIFIED** |
| SCALEIN1 add leg alone (live five) | 528 / 500 / 445 adds | (entries that dipped, held alone: 0.54 / 0.61 / n.a.) | 0.938 / 1.045 / 0.801 | 0.963 / 1.070 / 0.821 | add pays +10.9 / +11.2 / +11.0c a win | add loses 11.6 / 10.8 / 13.5% | -0.63 / +0.43 / -2.37c | about -0.80c per add (all thirds) | **FALSIFIED** |

Fees x1.2: CHEAP rules unchanged at 1 contract (rounding to the cent dominates); SCALEIN1 add leg 0.907 / 1.009 / 0.774. No pass of the strategy bar anywhere (best PF 1.27, bar 1.5; z far below 5.17). Zero-volume fill candles: none in any unit, so both reads are identical.

**A flaw in the registration, found after scoring and disclosed, not used to change any verdict.** SCALEIN1's lever bar compared net per CONTRACT of the position against the entry alone. An add buys the same outcome 3c to 6c cheaper, so the per-contract average of the position improves by construction whenever an add happens (+0.28c a unit in every third, z +32 is arithmetic, not evidence). The honest measure is dollars: the position's extra money is exactly the add leg's own net, about -0.80c per add over 1,473 adds (-0.10c per entry over 11,475 entries), PF 0.94 / 1.05 / 0.80. So scale-in raises profit per win (the add pays about 11c a win against about 6c for the entry) by buying favourites that have just dipped, and those lose about twice as often (11% to 13.5% against 5% to 6.5%), which eats the bigger win. The entries that dipped are themselves the bad ones (held alone PF 0.54 in A, 0.61 in B).

**Reading for the owner's question.** Each lever did raise profit per win by about 0.7c to 5c, and each paid for it with a higher loss rate, exactly as cheaper favourites do: choosing the cheapest coin in a window (+1.0c a win, +1.0 to 1.4 points of losses), silver for gold (+0.7c, +0.8 to 1.0 points), adding on a dip (+5c a win on the add, double the loss rate). Net was flat or worse in every case, and the cheapest-coin choice turned negative in the holdout third. Kalshi prices the cheaper of two near-identical favourites as the riskier one, correctly. No lever found raises profit per win without raising the loss rate by as much.

N tried: 3 (running count about 438,908). Verdict words only; nothing here changes the bot.
