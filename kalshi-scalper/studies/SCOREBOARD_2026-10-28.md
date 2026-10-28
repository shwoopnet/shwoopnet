# Research scoreboard, 2026-10-28

One page: what has been tried, how big the samples were, and what the verdict was. Every verdict word is from a pre-registered, run-once test (`FALSIFIED`, `NOT_ENOUGH_DATA`, `NOT_YET_FALSIFIED`; nothing means "trade"). About 21,800 variants have been counted; the 83 result sections below are the units.

## Totals

- Result sections in `README.md`: 83. Verdict words in them: FALSIFIED 169, NOT_ENOUGH_DATA 29, NOT_YET_FALSIFIED 19 (the last includes forward claims that are still open, not passes).
- **Passed and survived a forward read: none.** Open forward claims: P6F (allocator, reads 2026-11-12), P6R, FLOOR1 and THIN1 (XRP, 2026-11-12), HOURS1 (12 to 18 UTC), REV1 (Bitcoin late cheap NO, 2026-11-05), ABSORB-F (2026-12-01), GAS1-F (2026-11-22), FLIP1 and E3F/FWD1/VOL1 (mid-November).
- Live profit factor (owner's orders, 2026-10-07 to 10-26): 1.22 over 620 fills; history of the live rule (L1) pooled 1.02 over 31,581 entries.

## Families, what is tested and what is not

| Market family | Tested (IDs) | Largest samples | Verdicts | Status |
|---|---|---|---|---|
| 15 minute crypto (Bitcoin, Ethereum, Solana, XRP, Dogecoin, HYPE, BNB, NEAR, ZEC) price and timing rules | L1 (live), T1-T5, E1-E3C, FEAT1-4, TREE1-2, FACT1, SEARCH5K, QUIRK1, RT1-2, HUNT1-2, UNDER1, PULL1, BOUNCE1, CAL1, HOURS2, P1-P6 | 31,581 L1 entries; 852,975 grid observations; 4,230 and 5,000 rule searches | FALSIFIED almost throughout; P6 allocator and HOURS1 and REV1 open forward | Exhausted for price patterns |
| 15 minute crypto, order flow and tape (Kalshi tape, Binance flow, Deribit) | TAPE20, FLOW1 (32 variants), FP3 (64 rules), IV1, LAG tests, BTCBOOK, SWEEP1 (pending download) | 2,322 entries; 4,786 entries; 37,340 minutes | FALSIFIED | One test pending (SWEEP1) |
| 15 minute metals, energy, FX (gold, silver, WTI, natural gas, copper, USDCAD, AUDUSD) | L1 unchanged (E5, E5B), P6 picks, gold study, GAS1/CMD1 | 1,000 to 2,500 entries per series | Mixed: gold, silver, natural gas profit factor 1.1 to 1.3 in history | Live, thin edge |
| Hourly and daily crypto ladders (KXBTCD, KXETHD) | E4, XM1, LAD1 (6 variants), ARB1, ladder arbitrage scans | 704 closes; 4,064 pairs | FALSIFIED, zero locks | Exhausted |
| Underlying markets (Deribit perpetual, Binance spot) for the same signals | SEARCH5K features, CRYPTO1 (384), PERP1-3, PERP3 fast (336), FUND1 | 7.8 years daily; 78 days of minutes | FALSIFIED | Exhausted at these speeds |
| Sports (tennis, basketball, football, hockey) | SP1, SC1 (62,747 events), F6, F7, FP3, MAKER1, SPORTS jump scalps | 20,286 tennis markets; 1,788 totals games | FALSIFIED | Taker costs 4c a round trip |
| Weather (daily highs, rain) | WX1 (forecast), WX2, WX3 (ladder arbitrage), DT1 | 1,197 trades; 269 events | FALSIFIED | Market beats the public forecast |
| Long-dated and non-price markets (favourites, politics, gas, approval, commodities) | FLB1, GAS1, APP1, CMD1, XM1 | 209 to 2,000 markets | FALSIFIED / NOT_ENOUGH_DATA | Thin |
| Equities, ETFs, funds (not Kalshi) | BUYDIP1, IDX1, SECT1, SLOW1, DL1/DL10, VM/VM2, V3/V4, RP1, CS1, FA1, HS1, HL1, SL1, EL1, EX10 | 17 years daily | FALSIFIED | Closed by the blank slate |
| Execution and sizing (not new strategies) | TP1 (99c), exit25 and 21 real exits, MAKER2, MAKER3, THROTTLE1, GROW1 (running) | 28,873 opportunities; 31,293 entries | FALSIFIED as edges; THROTTLE1 cuts drawdown 30% | L1 upkeep lane |

## Not yet tested at all (Kalshi categories with liquid daily or event markets)

- **Economic releases** (CPI and inflation, payrolls, GDP, jobless claims, Treasury yields): 871 series in the Economics category, none tested except gas prices and approval.
- **Mentions** (earnings-call words, speech words, KXEARNINGSMENTION*, KXPERSONMENTION): a large, repeating family, never tested.
- **Entertainment, box office, ratings, music charts**: never tested.
- **Elections and politics** (candidate and party markets): FLB1 covered long-dated favourites only.
- **Financial index levels** (S&P 500 and Nasdaq daily ranges): never tested.
- **Companies and tech** (earnings beats, product events): never tested.

## Every result section (auto-listed from README.md; verdict words counted, largest sample quoted)

| Section | FALSIFIED | NOT_ENOUGH_DATA | NOT_YET_FALSIFIED | Largest n in the text |
|---|---|---|---|---|
| T1 to T4 | 4 | 0 | 0 | 1240 |
| E1 and E2 | 5 | 0 | 1 | 12506 |
| T5 | 3 | 0 | 0 | 1240 |
| B4 | 4 | 0 | 1 | 3379 |
| SP1, heavy favourites in sports game-winner markets | 1 | 0 | 0 | 209 |
| E3, L1 unchanged on seven more 15 minute series | 5 | 0 | 2 | 19139 |
| E3B, the backward holdout for XRP and Dogecoin | 1 | 0 | 1 | 13062 |
| PM1, Polymarket's 15 minute price against Kalshi's | 2 | 0 | 0 | 728 |
| L1B, the live rule on the 28 days before the book | 2 | 0 | 2 | 7213 |
| E4, L1 unchanged on the hourly ladders | 3 | 0 | 0 |  |
| PM2, skip an L1 entry when Polymarket disagrees, on the 28 older days | 3 | 0 | 0 | 1738 |
| FLB1, favourites in long-dated, non-sports, non-price markets | 5 | 0 | 0 | 2669 |
| E5, L1 unchanged on other commodities and two more coins | 9 | 0 | 0 | 32314 |
| XM1, the hourly ladder as a second price for the 15 minute market | 3 | 0 | 0 |  |
| ARB1, locked arithmetic across mutually exclusive events | 1 | 0 | 0 | 14100 |
| E5B, crude oil on E5's holdout | 1 | 0 | 0 |  |
| E3C, HYPE and BNB on the 29 older days | 2 | 0 | 0 | 5442 |
| BUYDIP1, buy at key levels against plain monthly buying | 6 | 0 | 0 |  |
| IDX1, overnight drift, turn of the month and the pre-holiday session | 3 | 2 | 0 |  |
| TP1, take profit at 99c on L1's entries | 1 | 0 | 0 |  |
| GAS1, APP1 and CMD1 | 5 | 3 | 0 |  |
| PERP1 | 1 | 0 | 1 | 745 |
| PERP2 and PERP3 | 4 | 1 | 0 |  |
| TREE1 and PAT1 | 2 | 0 | 0 | 2062 |
| TREE2 | 1 | 0 | 0 |  |
| SLOW1 | 5 | 0 | 1 |  |
| SECT1 | 3 | 0 | 0 |  |
| FUND1 | 0 | 0 | 2 |  |
| VM | 3 | 0 | 1 |  |
| VM2 | 2 | 0 | 0 |  |
| DL1 | 1 | 0 | 1 | 200 |
| LQ1 | 2 | 0 | 0 |  |
| V3 and V4 | 3 | 0 | 0 |  |
| RP1, CS1 and FA1 | 4 | 1 | 0 |  |
| HS1 | 1 | 0 | 0 | 79852 |
| HS1b | 2 | 0 | 0 | 69867 |
| HL1 and SL1 | 4 | 0 | 0 |  |
| EL1 | 2 | 0 | 0 | 79852 |
| EX10 | 1 | 0 | 1 | 10779 |
| SESS1 and SCI1 | 3 | 0 | 0 | 24064 |
| MC1, SF1 and CAP1 | 3 | 0 | 0 | 8085 |
| SIDE1, HOUR1 and XLEAD1 | 2 | 1 | 1 |  |
| DL10 | 1 | 0 | 1 | 10779 |
| VRP2 | 2 | 0 | 0 |  |
| FIX1 and the JUMP1 history look | 2 | 1 | 1 | 200 |
| CM1 and VT1 | 2 | 0 | 0 |  |
| the 21 real exit sells against holding to settlement | 0 | 0 | 0 |  |
| FEAT1 | 2 | 0 | 1 | 24792 |
| FEAT2 | 0 | 0 | 1 | 24792 |
| FEAT3 | 1 | 0 | 0 | 3611 |
| FEAT4 | 1 | 0 | 0 | 20339 |
| QUIRK1 | 1 | 1 | 0 |  |
| IV1, implied-volatility fair value | 3 | 0 | 0 |  |
| SEARCH5K | 1 | 0 | 0 | 2819 |
| RT1, take 99c and re-enter at 92c | 3 | 0 | 0 |  |
| RT2, reverse after a 99c favourite drops to 92c | 1 | 2 | 0 |  |
| BTCBOOK | 1 | 0 | 0 |  |
| FACT1, 4,230 complete strategies for Bitcoin and Ethereum | 0 | 2 | 0 | 7393 |
| PROG1 | 3 | 4 | 0 |  |
| P5, a market-wide volatility state | 1 | 0 | 0 | 28390 |
| P6, adaptive timing-and-series allocator | 0 | 2 | 0 | 1609 |
| TAPE20, the trade tape in the two minutes before the 6 minute decision | 1 | 4 | 0 |  |
| ladder arbitrage snapshot and two quick checks of the owner's pasted claims | 0 | 0 | 0 | 28390 |
| LAD1, option-style fair value on the hourly Bitcoin ladder | 2 | 0 | 0 |  |
| CRYPTO1, slow Bitcoin and Ethereum strategies, 2019 to 2026 | 1 | 1 | 0 |  |
| SC1, in-play tennis scalping after a 5c jump | 1 | 1 | 0 |  |
| HOURS2 | 1 | 1 | 0 |  |
| HUNT1 | 1 | 0 | 0 | 523 |
| HUNT2 | 2 | 0 | 0 | 852975 |
| F6 and F7 | 1 | 1 | 0 | 2281 |
| WX3 | 1 | 0 | 0 |  |
| FP3 | 2 | 0 | 0 |  |
| MAKER1 | 1 | 0 | 0 | 3159 |
| BOUNCE1 | 1 | 0 | 0 | 1205 |
| UNDER1 | 2 | 0 | 0 | 1561 |
| PULL1 | 1 | 0 | 0 |  |
| CAL1 | 2 | 0 | 0 |  |
| PM1 | 0 | 1 | 0 |  |
| PERP3 | 1 | 0 | 0 |  |
| MAKER2 | 1 | 0 | 0 |  |
| MAKER3 | 1 | 0 | 0 |  |
| THROTTLE1 | 2 | 0 | 0 |  |
| FLOW1 | 1 | 0 | 0 |  |

## Added 2026-10-28 (after the first version)

| Test | Lane | Family | Result |
|---|---|---|---|
| GROW1 | L1 upkeep | sizing on L1 | FALSIFIED by 0.01 PF: plain fractional sizing PF 0.99 (loses); walk-forward series choice PF 1.14, 0% of 200 resamples below $500, same signal as P6 |
| EXIT2 | L1 upkeep | exit line | Hold PF 1.016 beats the 25c line (0.981) on both halves; 15c line 0.988; higher lines worse |
| THROTTLE1 | L1 upkeep | size throttle | FALSIFIED on total, drawdown -30% |
| CPI1 | discovery | economic releases (CPI, core CPI) | NOT_ENOUGH_DATA: 7 trades on 2 releases (quotes missing 24h before releases) |
| MENT1 | discovery | earnings-call words | NOT_ENOUGH_DATA by rule (71 events of 100): PF 0.92 on 268 trades |
| SWEEP1 | (retired) | BTC 15 minute tape | Not run, excluded by process rule 3 |

## Strategy cards (owner: build a total of 10), status 2026-10-28

| # | Card | Result |
|---|---|---|
| 1 | CARRY1 funding carry BTC/ETH | FALSIFIED as a deployable: whole period +5.0% a year, daily PF 5.44, drawdown 0.72%; last 12 months 0% (funding below the entry line); liquidation caveat |
| 2 | BASIS1 quarterly basis | Closed by arithmetic: 5.3% a year gross, about 3% net |
| 3 | FUNDX1 Binance vs Deribit funding | NOT_ENOUGH_DATA: 6 entries; 3% to 4% a year difference |
| 4 | PAIRS1 ETH vs BTC | FALSIFIED: PF 0.62, 72 trades, -8.3% a year, drawdown 52% |
| 5 | QUOTE1 two-sided quoting BTC/ETH | Registered; tape downloading; about 200 windows against 300 needed |
| 6 | LOCK2 coincident-close locks | Registered; forward, needs the recorder's ladder data (from 2026-10-28 15:45 UTC) |
| 7 to 9 | QUOTE2 (hourly ladder), QUOTE3 (gold), LOCK3 (gold) | Wait for recorder data |
| 10 | DIGI1 Kalshi vs Deribit options | Forward only, not registered |
