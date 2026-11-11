# LOCKUP_RANK_V2: ideas ranked by speed-to-verdict times lock-up (2026-11-11, research only, no outcome read, no API call)

Method. Score = days to a first honest verdict x days the money is tied up (days to settle); lower is better. Annualized return = (net edge per contract / (capital per contract + 0.9c fee)) x (365 / days to settle), simple, NOT compounded, per slot, and it is what the idea earns IF IT WORKS at the stated edge (the edge is the registered 1c to 2c bar, not a finding; every idea here is unproven). Fills per week comes from held counts where the basis column says `held`, otherwise it is an estimate and says `est`. Politics in held data: 4,705 settled Politics and Elections markets over 74 days (about 445 a week); 757 had a life of 7 days or less, 1,875 of 14 days or less (about 72 and 177 a week); median life 21.8 days.

Cost inputs with no position (REBATE1, FEEROUND1, TOPMETH1) are left out: they tie up no money and are not strategies.

| rank | idea | source | days to settle | fills per week | basis | edge c | capital c | annualized if it works | days to verdict | score |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | STALE1 | card 9 | 0.01 | 3 | est | 1.5 | 50 | 107564% | 0.2 | 0.002 |
| 2 | LADBFLY1 | card 2 | 0.04 | 0.5 | held: README 0 of 238 strikes; est 0.5/wk | 1 | 50 | 17927% | 0.2 | 0.008 |
| 3 | MMHOUR1 | card 4 | 0.1 | 20 | held: MMSIM1 168 dev events; est 20/wk | 1 | 50 | 7171% | 0.2 | 0.02 |
| 4 | LIQ1 (liquidation reversion) | backlog | 0.01 | 20 | est; OKX recorder | 1.5 | 15 | 344340% | 3 | 0.03 |
| 5 | AVG1 | card 14 | 0.04 | 20 | est | 1.5 | 12 | 106105% | 1 | 0.04 |
| 6 | PIN1 | card 5 | 0.04 | 15 | est: hourly strikes near round numbers | 1.5 | 12 | 106105% | 1 | 0.04 |
| 7 | ROUND1 | card 13 | 0.04 | 15 | est | 1.5 | 12 | 106105% | 1 | 0.04 |
| 8 | XSER1 | card 3 | 0.04 | 0.5 | est; needs quote-data pairing | 1 | 50 | 17927% | 1 | 0.04 |
| 9 | NC15DEPTH1 | card 12 | 0.01 | 100 | est: 15 min non-crypto books | 1 | 50 | 71709% | 7 | 0.07 |
| 10 | OPT1 (Deribit implied vs KXBTCD) | backlog | 0.04 | 15 | est; recorder | 2 | 12 | 141473% | 3 | 0.12 |
| 11 | #15 mentions short lead | backlog | 0.3 | 10 | held: MENT1 45 usable quotes | 1.5 | 12 | 14147% | 2 | 0.6 |
| 12 | CAL1 | card 7 | 1 | 2 | held: AAASPREAD1 8 quoted pairs; est 2/wk | 1 | 90 | 402% | 1 | 1 |
| 13 | RULES1 (cards 6) / POLITICS_J | card; (j) | 7 | 0.5 | held: 0 confirmed rule-reversals, 76 proxy losses unreviewed | 5 | 93 | 278% | 0.2 | 1.4 |
| 14 | #12 same-observation spreads | backlog | 1 | 3 | held: gas pair 8 pairs; est 3/wk | 1 | 90 | 402% | 2 | 2 |
| 15 | POLITICS_H consistency locks | (h) | 10 | 0.1 | held: 1 credible buy-all (FLPRIMARY) in 211 event-timestamps over 74 days | 1 | 90 | 40% | 0.2 | 2 |
| 16 | EARLYCLOSE1 | card 10 | 5 | 10 | est | 1.5 | 12 | 849% | 1 | 5 |
| 17 | NEWLIST1 first-hour | card 8 | 7 | 60 | held: USWEEP2 crawl; est 60/wk | 1.5 | 12 | 606% | 1 | 7 |
| 18 | REL1 (BTC vs ETH weekly) | backlog | 7 | 5 | est; census 100 requests | 2 | 40 | 255% | 2 | 14 |
| 19 | POL short-dated cheap tails (VOTEPRIMARY, HORMUZWEEKLY, TRUTHSOCIAL, TRUMPACT, ...) | politics | 10 | 44 | held: 1,875 politics markets with life up to 14 days in 74 days (177/wk), est 25% cheap side | 1.5 | 12 | 424% | 2 | 20 |
| 20 | #14 other venue info (Metaculus/Manifold) | backlog | 21 | 5 | est: 20 matched markets | 2 | 12 | 269% | 21 | 441 |
| 21 | POL long-dated favourites (FLB1/THETA1 class) | politics | 70 | 10 | held: 4,705 settled in 74 days | 2 | 92 | 11% | 7 | 490 |

## Top 5 by speed-to-verdict times lock-up
1. STALE1 (card 9): score 0.002, 0.01 days to settle, verdict in 0.2 days, 3 fills a week (est)
2. LADBFLY1 (card 2): score 0.008, 0.04 days to settle, verdict in 0.2 days, 0.5 fills a week (held)
3. MMHOUR1 (card 4): score 0.02, 0.1 days to settle, verdict in 0.2 days, 20 fills a week (held)
4. LIQ1 (liquidation reversion) (backlog): score 0.03, 0.01 days to settle, verdict in 3 days, 20 fills a week (est; OKX recorder)
5. AVG1 (card 14): score 0.04, 0.04 days to settle, verdict in 1 days, 20 fills a week (est)

The 15 minute and hourly rows rank first by construction because their lock-up is minutes. Honest reading: the top rows hold up only on a LOW fills-per-week (LADBFLY1 and XSER1 are est 0.5 a week, the held ladder count found zero violations), so speed to a verdict is real but speed to the 100 trades a test needs is not.

## Politics only (the owner prefers markets that settle in 7 to 14 days)
- RULES1 (cards 6) / POLITICS_J: settle 7 d, fills/wk 0.5, annualized if it works 278%, verdict 0.2 d. edge = a mispriced rule case paying 5c on a 93c favourite; fires rarely
- POLITICS_H consistency locks: settle 10 d, fills/wk 0.1, annualized if it works 40%, verdict 0.2 d. lock bar 1c on about 90c cost, 7 to 10 day sets
- POL short-dated cheap tails (VOTEPRIMARY, HORMUZWEEKLY, TRUTHSOCIAL, TRUMPACT, ...): settle 10 d, fills/wk 44, annualized if it works 424%, verdict 2 d. DUPLICATE class of TAIL10/HISTLAD1 cheap tail: parked unless owner approves
- POL long-dated favourites (FLB1/THETA1 class): settle 70 d, fills/wk 10, annualized if it works 11%, verdict 7 d. FALSIFIED already; shown for scale only

Politics findings that drive this. (1) The only politics consistency set that looked executable (KXFLPRIMARY-02D26, 5 candidates, buy-all lock +5.3c unrounded, settled in 7 days) had no size information and cannot be confirmed exhaustive: one instance, a lead and not a strategy. (2) Short-dated politics supplies many fills (about 177 a week of markets with life up to 14 days) but only through cheap-tail or favourite rules, which are parked or declined (7e). (3) A locking structure (h) settles in 7 to 10 days and annualizes high if a lock exists, but fills are about 0.1 a week, so it can never reach 100 trades.

Caveat on the annualized column: for lock-ups of minutes to hours the arithmetic gives thousands of percent. That is a unit effect (a few contracts recycled at once), not a return anyone can earn; capacity and fills per week cap the dollars. Use the column to compare settle times inside the 1 to 21 day band, where it is meaningful: a 10 day politics lock needs about 40% a year at 1c on 90c, so a 1c lock on a 7 to 14 day set beats Treasury bills (about 4 to 5%) many times over, but only if one exists.
