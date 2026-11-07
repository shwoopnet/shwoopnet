# VIRT1 result (2026-11-07; registration commit 34cea57, sha256 6c3b385a302bb1a1a683c8d5ab0540e603f52f0dfc91af3addee105b39f0aca9, scorer committed after it): NOT_ENOUGH_DATA (15 treated), every sign on the FALSIFIED side

Scored once, development only (starts before 2026-10-28T00:00Z), `python -m scalper.virt1 run`; raw output `workers/VIRT1_SCORE_LOG.txt`. The held-out third (start at or after 2026-10-28) was never fetched, rated or stored.

```
K: eSoccer 24 (log-loss 0.9627 on 4,417 D1 games, dbar 0.193), eBasketball 32 (0.6519 on 788), Liga Pro 16 (0.6919 on only 5 games)
fetched 2,359 ready development events (eSoccer 1,000, eBasketball 1,000, Liga Pro 359), no look 344, no cheap side 2,501, cheap-side rows 1,514, treated (one per event) 15
treated: n 15 mean -0.61c win 13.3% vs mean ask 13.1% PF 0.95 z(event) -0.07   (fees x1.2 PF 0.93)
  D1 n 8 mean -1.96c PF 0.84 | D2 n 7 mean +0.93c PF 1.08
control (all cheap sides): n 1,514 mean -4.95c win 15.8% vs mean ask 19.6% PF 0.71 z(event) -5.28 z(day) -5.10   (fees x1.2 PF 0.70)
  D1 n 705 mean -5.02c PF 0.72 | D2 n 809 mean -4.89c PF 0.71
treated by series: eSoccer n 2 (-18.00c), eBasketball n 13 (+2.06c, PF 1.19), Liga Pro n 0
Brier of the first market, fetched events (n 1,994): model 0.2231, quote mid 0.2107
VERDICT NOT_ENOUGH_DATA; fetched 22% of the 10,820 ready development events; projected treated on all about 69
```

**Verdict: NOT_ENOUGH_DATA** by the registered rule (15 treated, under 150). There is no lead: the kill rule would also read FALSIFIED if n had allowed it (PF 0.84 in D1, 1.08 in D2, both under 1.5; net not above 0 in D1). The 15 trades are noise (win rate 13.3% against an ask of 13.1%, z -0.07), and the only positive slice (13 eBasketball trades, +2.06c) is 13 events, not evidence.

What the numbers do say, all of it consistent with the honest prior:
1. **The quote beats the rating.** Model Brier 0.2231 against the quote mid 0.2107 on 1,994 events, so the market already prices the controllers' skill gap better than a Kalshi-only player and team rating. The model almost never reads a cheap side at 3 times its ask (15 of 1,514 cheap-side rows, 1.0%): where the market says 10c, the rating says 10c to 15c, not 30c.
2. **The cheap side loses the usual amount here too.** The control (every cheap side, 1,514 rows, 2,359 events) is -4.95c per contract (win 15.8% against an ask of 19.6%, PF 0.71, z -5.28 clustered by event), the same sign and size as the pooled cheap-side baseline (about -5.5c to -6.2c), with D1 -5.02c and D2 -4.89c. No hidden counterparty edge in virtual-sports retail pricing shows up in the unconditioned cheap tail.
3. **eSoccer draw structure** (handled explicitly: three markets, draw probability dbar x 2 x min(E, 1-E), dbar 0.193 fitted on D1, NO sides carry the draw mass): the model flagged 2 treated eSoccer trades (both win-yes, both lost, -18.00c) and no TIE-yes and no NO side. The tie market is not mispriced to the model's eye; nothing here to follow.

**Why it is not worth the held-out read.** The development projection is about 69 treated events on ALL 10,820 ready development events (15 per 2,359 fetched). The held-out third is about half the size of development, so about 35 treated events: it cannot reach 150, so reading it on or after 2026-11-21 returns NOT_ENOUGH_DATA whatever it says. Reaching 150 treated would need roughly 5 months of new events at the current rate. I recommend not spending the held-out read and not extending the fetch (extending the same md5 order to the unfetched 8,461 ready events would project about 69 treated, still under 150, and the sign is the falsified one).

Disclosures. (1) **Count correction:** the registration table gave development 13,133 events (start before 2026-10-28T06:52Z, the exact two-thirds point) and held-out 6,567, but the rule it fixes is the cut at 2026-10-28T00:00Z, which gives 12,957 development events after dropping 2 odd shapes (eSoccer 9,404 and others as listed, recomputed at the rounded cut); the cut date, not the count, is what was registered. (2) Russia Liga Pro has many players with few games: only 5 D1 games and 359 development events pass the 8 prior games rule, so K 16 for Liga Pro is a fit to 5 games (the grid minimum by a hair) and the series contributed no treated trade. (3) The fetch was 2,359 events, not the 3,000 the cap allowed, because Liga Pro had only 359 ready events; it took 92 minutes at 1.3 s pacing plus Kalshi's slow responses, with no repeated 429 and no block. (4) 344 events had no valid quote at the look (a quote needed ask minus bid at most 0.10; virtual markets are often empty or one-sided before the start). (5) The ticker time was used as the scheduled start; the look is 120 s before it. A game starting early would make the look live, which would only add noise to treated and control alike. (6) Two held-out-region events were read before registering (see the registration, section 2) and are excluded from the held-out read. (7) Quote is not a fill. (8) Nothing is promoted; no promote verb.

N +3: running count about 1,230,543 (z bar about 5.3). Code `src/scalper/virt1.py`, tests `tests/test_virt1.py` (5 passing, synthetic). Caches outside the repo.
