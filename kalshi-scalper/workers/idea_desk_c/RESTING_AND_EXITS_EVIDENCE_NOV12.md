# Resting orders and exits: the outside record (Idea Desk C, Nov 12, 2026)

For the Head of R&D. Read A of the 20:26Z message. Ideas only, no Kalshi request, nothing changes a registration. [research]

**Counts:** 4 questions; 4 primary sources read in full (Burgi, Deng and Whelan on Kalshi; Becker on Kalshi; Bartlett and O'Hara on Kalshi; Whelan on Betfair), plus 4 secondary items (unverified). Answers:
- Questions with a counted answer: 2 (maker returns, adverse selection).
- Questions with "nothing found": 2 (exits that beat holding; fill rates at the mid or the bid).
- Places where a resting entry has been shown to earn after fees: 2, both small (Kalshi makers buying at 50c or more; Betfair totals where the taker's side is the favourite). None on short-dated crypto.

## 1. What a maker earns, by price level and market type

| Venue and source | Sample | Maker result | Where it is positive | Fees |
|---|---|---|---|---|
| Kalshi, Burgi, Deng and Whelan (2026), https://www.karlwhelan.com/Papers/Kalshi.pdf | 156,986 maker-bought contracts, 2021 to Apr 2025; markets open 24 h or more, volume $1,000 or more, final spread 20c or less; hourly crypto and index markets EXCLUDED | -9.64% on average (takers -31.46%) | **Makers buying at 50c or more: +2.6%, significant.** Makers buying at 10c or less lose on 5 of 6 horizons. At 1 to 10 days before the close the high-price maker returns are mostly not significant | After taker fees; no maker fee existed in the sample |
| Kalshi, Becker, https://www.jbecker.dev/research/prediction-market-microstructure | 72.1M trades, Jun 2021 to Nov 2025 | +1.12% on average; positive at 80 of 99 price levels | By category: media +3.64%, world events +3.66%, entertainment +2.40%, crypto +1.34%, weather +1.29%, sports +1.12%, politics +0.51%, finance +0.08%. Makers buying NO +1.25 points, buying YES +0.77 | GROSS of fees. **Makers lost about 2% from launch to 2023**; the positive result is after 2024 |
| Kalshi, Bartlett and O'Hara (2026), https://conference.nber.org/conf_papers/f243677.pdf | 41.6M trades, Jul 2021 to Mar 2026; 14,988 single-name and 460,658 broad markets | 1.91c a contract (single-name), 0.82c (broad). **Median broad market: -$0.01 for the maker** | Single-name markets that settle NO. On broad markets, the markets that settle YES cost makers 100% of their net | Fees ignored (maker 0.02c to 0.44c, taker 0.07c to 1.75c a contract in their period) |
| Betfair soccer, Whelan (2026), https://www.karlwhelan.com/Papers/Betfair.pdf | 902,568 pre-match 1X2 bets; 2,088,032 over and under bets; 2022 to 2024 | 1X2 +0.6% (takers -2.5%); over and under +2.0% (takers -2.2%) | Flat near zero until the TAKER's side has a win chance above 0.6, then positive. In play, makers on longshots lose almost as much as takers | After the 2% commission; the standard deviation of the 0.6% figure is 198% |

**In our units.** At 50c a contract, +2.6% is about 1.3c, +1.12% about 0.6c and 0.82c is 0.82c. Every published maker edge is **1c to 2c a contract on average**. That is the size of Kalshi's taker fee at mid prices, and it is far below the 11 to 12 points the research bar needs for a held mid-priced bet.

## 2. Adverse selection on a resting order

From Bartlett and O'Hara, verified from the text:
- **The losing side is big.** A losing maker contract loses 23.13c (single-name) or 26.59c (broad).
- **Most of the edge goes back.** The maker wins more often (+5.31c single-name, +2.01c broad), but loses more when wrong (-3.40c, -1.19c). So **about 64% (single-name) and 59% (broad) of the frequency edge is handed back to informed flow.**
- **Price impact is almost entirely permanent.** The transitory part averages about 0, so a filled resting order has no tendency to recover.
- **Toxic flow flips the sign** (VPIN, a measure of one-sided order flow). On single-name markets priced 30c to 70c, the lowest-toxicity fifth earned +$41 a bucket and the highest lost $12. The loss rate rose from 43.1% to 51.7%.
- **Toxicity has no predictive power on broad markets.**
- **Weather is the market type where one-sided flow is most informed.**

No source gives a post-fill drift in cents over a fixed window, on any venue. **This agrees with our record:** five resting-order tests failed on adverse fills, and the outside numbers say most of the gross edge goes to informed flow.

## 3. Do exits beat holding a binary bet?

**Nothing found showing a profit target, stop or trading out improves expected return over holding.**
- Makers on Polymarket crypto held 95% of their volume to settlement, and 82% even where offsetting flow existed (Bartlett and O'Hara). That says what makers do, not what earns more.
- Cash-out offers average 6.4% under fair value over 180 offers from 12 bookmakers. This is a review site whose method is not shown, so it is unverified.
- Whelan's teaching notes argue that regular cashing out lowers expected return, from a worked example, not data.

**This agrees with our record:** holding beat every exit on two families. An exit is a second taker trade that pays the spread and fee again. The published case for exits is variance control, not edge.

## 4. Counted fill rates at the mid or the bid

**Nothing found** for Kalshi, Betfair or Polymarket. The nearest are quoted spreads on Polymarket (Dubach 2026, arXiv 2604.24366): a median of about 4c at 40c to 60c, about 18% of the price at 0c to 10c, and 0.5% at 90c to 100c. Our own Forensics figure (60% to 73% for a taker order at the price seen) stays the only fill number we have.

## Where a resting entry has been shown to earn, plainly

1. **Kalshi, buying at 50c and up, as a maker, in markets open 24 hours or more:** +2.6% after taker fees, 2021 to Apr 2025, before maker fees and before the 2025 fee change. A maker buying above 50c and holding is the favourite side, so the owner's ban applies above the mid. The usable part is the band near 50c, at about 1.3c a contract.
2. **Betfair soccer totals, as the maker against a taker who backs the favourite:** +2.0% after commission. This is not a Kalshi family we hold history for.
3. **Nowhere on short-dated crypto, and nowhere on cheap contracts.** Makers lose under 10c, and the post-2024 maker edge did not exist before 2024.

**For the three resting-order variants queued for the sports recorder:** the outside record supports a small maker edge in sports (+1.12% gross on 43.6M trades) and none on the cheap side. It is a 1c to 2c edge before Kalshi's maker fee, so as a held bet it is far from the bar. It could matter only as a cost saving inside a rule that already has an edge. **For a politics limit-entry rule:** politics shows the smallest maker edge of any category except finance (+0.51% gross), so a resting entry there saves cost but brings almost no edge of its own.
