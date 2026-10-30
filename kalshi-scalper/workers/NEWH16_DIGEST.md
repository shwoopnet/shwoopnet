# NEWH16 digest: documented edges in very short horizon binary and prediction markets (2026-10-30, research only)

Worker NEWH16 (Strategy Research V2). The owner asked directly on 2026-10-30: "research new kalshi 15 min prediction market strategies".
Method: web search and page fetches on 2026-10-30, paraphrased, no long quotes. "Evidence" means a described sample, a method and numbers a
reader could check. "Story" means an anecdote, a vendor or a blog without sample size, fees or an out of sample check. Times are US Central.
Nothing here is a trade instruction. The buy-the-favourite-and-hold family (live L1) is off limits for new tests and is only mentioned where a
source's main finding is that family.

## The five most credible sources, one line each

| # | Source | Verdict |
|---|---|---|
| 1 | Burgi, Deng, Whelan, "Makers and Takers: The Economics of the Kalshi Prediction Market" (UCD working paper, Jan 2026; https://www.karlwhelan.com/Papers/Kalshi.pdf; summary https://cepr.org/voxeu/columns/economics-kalshi-prediction-market) | Evidence. 300,000+ Kalshi contracts, fees included. It is the favourite-longshot paper, so its tradable side is L1's family (closed). Its fee facts are usable: fee 7% x P x (1-P) rounded up, 1.77% of price at 50c for a 100 contract order. |
| 2 | Bartlett and O'Hara, "Adverse Selection in Prediction Markets: Evidence from Kalshi" (NBER conference paper, version 2 Jul 2026; https://conference.nber.org/conf_papers/f243677.pdf) | Evidence. 41.6 million Kalshi trades. Traders over-bet YES in markets that mostly settle NO, and one-sided flow (VPIN) predicts maker losses in single-name markets. Quotes are hourly candles and short lived markets are mostly missing, so it does not measure 15 minute crypto. |
| 3 | Kitron and Wengrowicz, "Short-horizon mean reversion in cryptocurrency markets: a matched cross-market measurement" (arXiv 2608.21888; https://arxiv.org/pdf/2608.21888) | Evidence, preprint, no independent replication. 15 minute reversal against the previous candle on 90% of 183 Binance pairs. The authors themselves say the edge is not exploitable under benchmark spot costs (AUC gap +0.011), so a 3.5% round trip on a 50c contract cannot be paid by it. |
| 4 | Shanaev, Vasenin, Stepanov, "Turn-of-the-candle effect in bitcoin returns" (Heliyon 2023; https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/) | Evidence for a tiny effect: about 0.6 to 0.9 basis points a minute at minutes 0, 15, 30, 45, strongest in 2021, smaller out of sample in 2022. Against a 15 minute move of roughly 25 basis points it shifts a 50/50 window by about one point. Too small for a taker fee, declined without a try (see below). |
| 5 | Telonex, "top crypto traders on Polymarket 15m" (https://telonex.io/research/top-crypto-traders-polymarket-15m) and ASIC's binary options material (https://moneysmart.gov.au/investment-warnings/binary-options) | Telonex: descriptive on-chain data, one week (Feb 2 to 8, 2026), 2,688 windows, 15.3 million fills; makers net positive and takers negative by the same amount; pre-fee, vendor, no significance tests, strategy labels inferred: evidence for the maker/taker transfer, story for any named strategy. ASIC: regulator evidence that 74 to 80 percent of active retail binary option clients lost, average position under six minutes: the counterparty class of short expiry binaries loses, which says who is on the other side, not how to be paid. |

## Every source read, by topic requested

Claimed size is the source's, not ours.

### Favourite-longshot and probability weighting (buy-the-favourite is L1, closed)
- Burgi, Deng, Whelan (above). Contracts under 10c lose more than 60% of the money staked; contracts above 50c earn a small positive return; CEPR column: takers lose about 32% on average, makers about 10%. Evidence. Only mostly non 15 minute contracts, pre April 2025 fee rules (makers were not charged).
- arXiv 2602.19520, "Decomposing Crowd Wisdom: Domain-Specific Calibration Dynamics in Prediction Markets" (https://arxiv.org/pdf/2602.19520), read only through a search summary: crypto contracts on Kalshi are close to calibrated across trade sizes; longer horizons drift toward the favourite-longshot pattern; some domains are over-extreme at short horizons. Evidence (preprint), not read in full. It points away from a crypto-specific mispricing at short range.
- A blog claim of a favourite-longshot pattern in Polymarket four hour crypto windows came from a trading bot's own site. Story.

### Short expiry binary mispricing, 5 and 15 minute windows
- ASIC (above): evidence of negative expectancy for the retail side. No exploitable direction.
- Oddsshopper, "Are Kalshi's 15-minute Bitcoin markets rigged?" (https://www.oddsshopper.com/articles/prediction-markets/are-kalshi-15-minute-bitcoin-markets-rigged). Checked 2,800 windows (Sep 4 to Oct 29, 2026) against a single venue proxy (Coinbase): late flips come almost only from windows that end within $50 of the line, the 60 second average means a late move must be about four times the gap, and a 70c lead is not safe (23 of 31 first-sample flips had the loser at 70c or better). The author claims no edge and warns about the 50c fee peak. Evidence for a diagnostic, not a strategy; near-the-line flips are what LATECAL and the L1 record already measure.
- Indie Hackers posts on "latency arbitrage in 15 minute crypto markets" and a "5 versus 15 minute arbitrage bot" (indiehackers.com, found by search, not fetched). Story: no sample, no fees, no date range. Their one checkable claim, that Polymarket's quotes once lagged Binance, is the reason Polymarket added taker fees (below).

### Market maker adverse selection and inventory in thin binary books
- Bartlett and O'Hara (above). Evidence, hourly resolution. The "frequency-magnitude" result (YES over-bet in NO-leaning markets) is a taker bias, not an inventory effect.
- Telonex (above): makers net +$728,501 and takers -$728,501 in the week, takers won 53% of fills but lost money (they pay the larger prices on their wins). Descriptive.
- Capital Spectator review (https://www.capitalspectator.com/?p=25500) summarising a study of 150 million Polymarket trades: the most accurate 5% of traders profit as both maker and taker, ordinary traders lose on both sides. Secondary summary of a paper not read: treat as evidence of skill concentration, not of a rule.
- arXiv 2510.15205 (cost-function market makers lose without subsidy because adverse selection grows with liquidity): theory, not a Kalshi order book.

### Fee structure (Kalshi fee peaks at 50c)
- Kalshi taker fee 7% x C x P x (1-P), rounded up to the cent per order (Burgi et al., pre-2025 rules; our registrations use it as given). At C = 10: 18c per order at 50c (1.8c a contract, 3.6% of a 50c stake) and 4c at 95c (0.4c a contract). A coin-flip priced taker trade therefore needs roughly a 53.5% hit rate before spread to break even and about 58% for profit factor 1.5. Computed here from the formula, not a source claim.
- Polymarket added dynamic taker fees to its 15 minute crypto markets on Jan 5, 2026 (The Block https://www.theblock.co/post/384461/polymarket-adds-taker-fees-to-15-minute-crypto-markets-to-fund-liquidity-rebates; Cointelegraph https://cointelegraph.com/news/polymarket-quietly-adds-taker-fees-15-minute-crypto-markets; Polymarket docs https://docs.polymarket.com/polymarket-learn/trading/maker-rebates-program). Fee also scales with P(1-P)-type shape, funds a maker rebate, and is stated to be aimed at latency arbitrage. Reported peak rates near 1.8% are unverified. Evidence the fee exists; story for how much latency profit there was.

### Time of day liquidity
- No source found that tests a time-of-day edge on 15 minute binaries. Bartlett and O'Hara show hourly volume figures only. The only time-of-day result in this digest is the turn of the candle effect (source 4), which is below the fee. Our own record has time of day, hour and weekday tests (HOUR2, HOUR3, MKTTIME1, IDEAS100).

### Settlement source mechanics
- Kalshi help, "Crypto markets" (https://help.kalshi.com/en/articles/13823838-crypto-markets): most crypto markets settle on a CF Benchmarks index; a 15 minute market compares the average of the minute before it closes with the average of the minute before it opened. Official. The page does not state the tie rule. Our own SETTLEMENT_MECHANICS and BTCAVG work uses the same fact.
- Polymarket's matching windows ("btc-updown-15m-<start>", public gamma API, read 2026-10-30): resolves Up if the Chainlink end price is at or above the start price (a point comparison, NOT a time weighted average; corrected 2026-10-30 after XVENUE1 read the rule text); Kalshi uses two one minute averages of a different index. So the two venues can disagree on a close window. XVENUE1 measured the disagreement rate: 1.44% of 16,222 windows, 0.53% when both are priced 80c or higher.
- Gold settles on a single print (our SETTLEMENT_MECHANICS page): second resolution is NOT_RUNNABLE without the print source.

### Cross venue differences, Kalshi against Polymarket
- Open source "polymarket-kalshi btc arbitrage bot" (https://github.com/CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot) and a dev.to post: buy opposite sides when the total is under $1. Story: hourly markets, no results, and the author notes being filled on one venue and stuck on the other.
- Glassnode latency monitor (hyperlatency.glassnode.com): host did not resolve from this session (not on the allowed network list), so not read.
- Our own record already holds three Polymarket tests (PM1 Oct 13, PM2, PM3: does Polymarket's price carry information Kalshi's does not; all FALSIFIED) and a noon ladder test (PM1 Oct 27, NOT_ENOUGH_DATA).

## What this digest says in one paragraph

Every source that measures money says the same thing: takers on short binaries pay the maker, the cost peaks at 50c, and the bias that survives fees sits at the extremes, where L1 already trades and the owner closed further work. The directional effects at 15 minutes that are documented (reversal after taker flow, turn of the candle, intraday momentum) are a few basis points or an AUC of 0.51, and their own authors say spot costs absorb them. A Kalshi taker at 50c pays about 3.6% plus half a spread. Hence the tests below ask for something larger than the papers claim, on the chance Kalshi's makers behave differently from a spot book, and I expect all of them to fail; they are registered so the failure is on the record.

## Mechanisms considered and the ledger's nearest tests

| Mechanism | Nearest tests (README, V2 census) | Decision |
|---|---|---|
| Favourite-longshot, YES over-betting | L1 and every family A entry; QUIRK1 (both sides at the first candle on 18 series, 28 of 28 FALSIFIED, YES base rates 45% to 54%) | Closed (owner, Oct 28). Not tried. |
| Reversal after taker flow, 15 minutes | PERPFLOW1 (288 rules, FLOW5/15/30 followed and faded, FALSIFIED); FLOW1; BTC1 FADE (previous window result, a coin flip) | Spot flow is covered. The untested piece is size of the previous move and multi hour trend: registered as T1 and T2. |
| Turn of the candle drift | QUIRK1 Bitcoin YES at the first candle (FALSIFIED) | Declined: effect about 1 point, fee 3.6%. |
| Short horizon momentum | BTC1 CONT, IDEAS20 TREND4 and STREAK3 (as L1 filters only), S06 | Multi hour trend as an entry: registered as T1. |
| Cross venue (Polymarket) | PM1, PM2, PM3, PM1 ladder | Standalone entry on a price gap, never run as an entry: registered as T3 (the filter forms are FALSIFIED). |
| Latency to spot | leadlag, LAG2/LAG2B, RECORD1 (recorder, forward) | Not repeated. |
| Maker rebates, queue effects | MAKER2 to MAKER5, QUOTE1, QUOTE2B, L1Q1 | Not repeated; R6 pending. |
| Settlement averaging | BTCAVG (NOT_ENOUGH_DATA), LATECAL, GOLDFV1, GOLDPYTH-H (NOT_RUNNABLE) | Not repeated. |
| Two venue disagreement on settlement (Chainlink TWAP against CF index) | none | Proposal only (recorder), see the result file. |
