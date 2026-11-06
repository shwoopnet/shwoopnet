# FLOWX1 result (scored once 2026-11-06; registration commit 0a99487; code `src/scalper/flowx1.py`): NOT_ENOUGH_DATA (37 of 150 treated entries), sign negative

Cheap side only (ask 3c to 30c, taker, held, fee 7% x C x p x (1-p) rounded up, C=10 unless stated). Closes 2026-09-06 to before the 2026-10-03T16:00Z cut (frozen third never fetched; August not usable because the historical endpoints were rate limited). Full print: `workers/FLOWX1_SCORE_PRINT.txt`.

**Funnel.** 1,685 candidates (md5 sample of the 1,444,008-market census, 69 series, volume at least 100, at most 40 per series, 3 per event), whole list processed inside the time box. 439 had no flow window, 821 no signal candle, 255 outside 3c to 30c, 28 no fill candle, 14 over the 0.30 limit, 13 ties, 44 under 10 contracts of tape in the hour (NoFlow). **71 scoreable entries** on 65 events and 20 days: 37 high flow, 34 complement, 22 low flow. The funnel is the finding: most one-hour-before-close hourly, daily and weekly tails have no two-sided minute quote or no tape at all.

| arm | n (events, days) | win vs paid | net per contract C=10 (C=1) | PF (x1.2) | day z |
|---|---|---|---|---|---|
| control, all cheap-side entries | 71 (65, 20) | 15.5% vs 13.9c | -6.75c (+0.21c) | 0.61 (0.55) | -1.17 |
| HIGH flow >= +0.30 (primary) | 37 (36, 17) | 18.9% vs 15.7c | -6.03c (+1.68c) | 0.68 (0.61) | -0.81 |
| complement | 34 (32, 16) | 11.8% vs 11.9c | -7.53c (-1.38c) | 0.52 (0.47) | -1.04 |
| LOW flow <= -0.30 (secondary) | 22 (21, 13) | 9.1% vs 12.6c | -11.27c (-4.77c) | 0.33 (0.29) | -2.01 |

Halves (D1 before 2026-09-20 / D2 after), high flow: D1 n 15 +0.93c PF 1.06; D2 n 22 -10.77c PF 0.45. By family, high flow: commodities n 18 -10.06c, fx n 7 -4.57c, indices n 11 -0.36c, crypto n 1. Treated minus complement +1.5c per contract, event-level permutation one sided p 0.452. Low flow is worse than high flow (-11.3c vs -6.0c), the direction FLOW1's lead assumed is not supported, but n is 22.

**Verdict word: NOT_ENOUGH_DATA** (37 treated entries and 36 events against the registered 150 and 40; 17 days against 8 is met). Sign check against the kill rule: treated mean -6.03c is under the +0.5c bar and PF 0.68 is under 1.5, so a FALSIFIED would fire at n 150; the pooled cheap-side baseline of about -5.5c to -6c is reproduced almost exactly by the treated arm (-6.0c), i.e. the flow filter adds nothing visible. No lead, no probe spec, holdout not read.

**Accrual needed.** Scoreable entries came at 71 per 1,685 candidates (4.2%), 37 treated. 150 treated needs about 7,000 candidates screened (the census holds about 50,000 with volume at least 100 but the per-series cap and per-event cap bind), roughly 5 hours of polite fetching, plus the frozen third and later closes (which need the coordinator). The binding limit is the tail market having a two-sided quote and tape one hour before the close, not the fetch rate.

Tries 2 (high arm, low arm). N +2 charged (running about 730,453, z bar about 5.27).
