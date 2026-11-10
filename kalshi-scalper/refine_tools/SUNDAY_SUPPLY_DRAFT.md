# Sunday supply draft (for Sun Nov 15, 7:17 PM CT), DRAFT from verified results only, 2026-11-10

Basis: cash, PF per contract, unrounded fee, hold to settlement, N tried about 770. Honest summary: **fewer than 3 NEW candidates qualify.** There are 0 new rules. The four below are the already registered shadow rules (PR 753) and are the only ones with an independent-window pass at both +0c and +1c. None is a pass: Bonferroni z about 5.2 is out of reach at these n.

1. GOLDALL: gold favourite 0.88-0.97, 6m look (330-400 s left), every L1 signal logged. Independent Aug 13 to Sep 1: PF 1.60 (439) / 1.36 at +1c. Held-out: independent window, n 439; no tuning. Code: none (on main). Prior low-medium.
2. GOLDHI6S: gold favourite 0.92-0.97, 6m look, spread at most 2c. Independent window: 1.68 (265) / 1.35. Code: needs deploy-latest.sh (PR 753). Prior low.
3. XRPFAV6: XRP favourite 0.88-0.92, 6m look, spread at most 2c. Independent June to early Sept: 1.645 (137) / 1.46. Code: PR 753. Prior low (live XRP 0.49 over 65 fills, paused).
4. XRPYES10: XRP YES 0.88-0.97, 10m look (570-640 s). Independent June to early Sept: 1.91 (70) / 1.66. Code: on main. Prior low.
5. Not offered: Bitcoin (BTCHI6 1.13 / 0.91 independent, BTCHI10 contested 0.90 on V2's Jun to Aug), Ethereum (ETHNO6, ETHL1 fail on 4.3 weeks), silver (candle 1.19 at +1c, halves 1.28 / 1.11, tracked by C9 only, quotes not held), and every longshot, near-even, late-favourite, hourly ladder and 54-series scan family (see ONDECK.md closed lists).
Caveats: gold net is thin (+1.5c GOLDALL, +1.0c GOLDHI6S per contract at +1c) and the independent gold window is 3 weeks, not the earlier months. Shadow rows assume a fill at the touch. Common pass: 150 forward signals, PF at least 1.3, second half at least 1.2, 14 days, no day above 30 percent of net; forward read 2026-12-14. Expected forward signals a week (candle model): GOLDALL 126, XRPFAV6 88, GOLDHI6S 72, XRPYES10 55.

## Needs data (pull this week to make a new candidate)

- Gold earlier windows: Aug 6 to 12 and everything before Aug 13 were not reached (1,358 of 2,153); finish the pull for a longer independent check, and a gold weekend split (not yet built; W-GOLDCAL1 found no calendar skip candidate, so this is a look, not a lead).
- XRP earlier than June (history exists to at least 2026-04-04) and later Sept to Oct; the XRPFAV6 time-of-day skew needs full 24 hour cover.
- Bitcoin: the remaining 330 of 1,536 June to July windows (BTCHI10 is contested between 1.58 and 0.90 on overlapping months; a clean window decides it).
- OICORE: 13 more triggers on the Jun to Jul window to reach 40 (now 27, PF 1.59 / 1.41), and an independent window for other series needs a series-scaled threshold (rise 99th percentile 6,500 to 13,700 elsewhere).
- Ethereum: nothing to pull; two independent reads already fail. Dogecoin, AUD/USD, USD/CAD: no candle history held for shadow checks (AUD/USD quotes not held by the bot).
- EVENT830: read the CPI forex trades (EURUSD, GBPUSD, USDJPY 26NOV100830-30, closing 13:30Z Nov 10) at 13:50Z; first result is 5 earlier trades, 0 wins, -0.85, so one release is an anecdote, not a test. Record the outcome before deciding any change.
- Silver and BNB: quotes appear only near events; C9 forward count continues.
