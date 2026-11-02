# ESPORT1 result (2026-11-02; registration commit 2590e42, scorer committed before any candle)

```
ESPORT1 run 2026-11-02T16:04:01.912803+00:00 N=728708 z bar 5.27 cost 7% x C x p x (1-p) rounded up, C 10, taker at the ask
universe events 7530, with candles 7530
A KXCS2MAP: eligible events 1550; Brier Elo 0.2428 market mid 0.2222
A KXCS2MAP W1: n 164 events 164 PF 0.85 mean -3.30c z -0.95 loss 67% | fees x1.2 PF 0.84
A KXCS2MAP W2: n 194 events 194 PF 0.90 mean -2.26c z -0.69 loss 64% | fees x1.2 PF 0.89
A KXCS2MAP W3 holdout NOT read (W1 and W2 did not both pass, or Elo Brier not better than the market)
A KXCS2MAP pooled read windows: n 358 events 358 PF 0.88 mean -2.74c z -1.14 loss 66%
A KXCS2MAP info gap 0.05: W1 n 241 PF 0.83 W2 n 271 PF 0.92
A KXCS2MAP info gap 0.12: W1 n 105 PF 0.73 W2 n 136 PF 0.89
VERDICT A KXCS2MAP FALSIFIED: PF under 1.5 in a window; not positive at fees x1.2; Elo Brier not better than the market; pooled z -1.14 under 5.27; pooled mean under 2c
B LOL+DOTA2+VALORANT: eligible events 2376; Brier Elo 0.2350 market mid 0.2164
B LOL+DOTA2+VALORANT W1: n 186 events 186 PF 0.81 mean -4.38c z -1.34 loss 72% | fees x1.2 PF 0.80
B LOL+DOTA2+VALORANT W2: n 275 events 275 PF 0.85 mean -3.28c z -1.23 loss 71% | fees x1.2 PF 0.84
B LOL+DOTA2+VALORANT W3 holdout NOT read (W1 and W2 did not both pass, or Elo Brier not better than the market)
B LOL+DOTA2+VALORANT pooled read windows: n 461 events 461 PF 0.83 mean -3.73c z -1.81 loss 71%
B LOL+DOTA2+VALORANT info gap 0.05: W1 n 292 PF 0.76 W2 n 390 PF 0.82
B LOL+DOTA2+VALORANT info gap 0.12: W1 n 100 PF 0.65 W2 n 176 PF 1.07
VERDICT B LOL+DOTA2+VALORANT FALSIFIED: PF under 1.5 in a window; not positive at fees x1.2; Elo Brier not better than the market; pooled z -1.81 under 5.27; pooled mean under 2c
```

Verdict: both tries FALSIFIED. Elo Brier 0.2428 against the market mid 0.2222 (A) and 0.2350 against 0.2164 (B), so the market beats a Kalshi-only Elo, as predicted. Profit factor 0.85 / 0.90 (A) and 0.81 / 0.85 (B) in W1 / W2, mean -2c to -4c per contract at 10 contracts, taker at the ask, fee 7% x C x p x (1-p) rounded up. The W3 holdout was not read (W1 and W2 did not pass). N + 2, running count about 728,708 (z bar 5.27).
Disclosures: universe 7,530 map-1 events (CS2 plus LoL, Dota 2, Valorant) after Elo burn-in; only 1,550 (A) and 2,376 (B) had a valid two-sided 1 minute quote in the 10 minutes before the scheduled start (historical candles are sparse), so the result describes quoted events only. One market per event (first team alphabetically). Kalshi's `close_time` (winner declared) was the Elo's result clock. Nothing is promoted; no promote verb.
Forward read: not recommended (falsified). If ever wanted: about 1.5 to 2 qualifying trades a day on CS2 alone, so 150 trades is about 10 to 14 weeks (about 2027-02); candles stay retrievable after the fact, no recorder needed.
Code `src/scalper/esport1.py`, tests `tests/test_esport1.py`. Scratch cache (not committed) in the session scratchpad.
