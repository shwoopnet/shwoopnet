# PIVOT_SCOPING: should research move off Kalshi? (Nov 9, 2026)

Research only. No orders, accounts or credentials. Written from the research record and general market knowledge, NOT from fresh web checks: every rule, limit and data source below must be verified before anyone relies on it (rules change; PDT rules in particular were under revision). Not legal, tax or investment advice.

## Candid record first
- Kalshi: N 1,450,505 hypotheses counted, zero survivors at the owner bar (PF 1.5 in three windows after fees, deflated, named counterparty). Fee and spread structure is a large part of why: cheap tickets pay fee on every leg, favourite legs lose to the haircut.
- Crypto perps: about 40 tests, no pass.
- Old Alpaca equities server (retired Oct 26): its backtests were later withdrawn for lookahead; costs were the binding constraint (spread measured at 0.2% median round trip 0.7% against 0.62% gross).
- Lesson that transfers: the first answer was wrong in the flattering direction six times. A new market inherits the same failure modes unless the harness is used from day one.

## 1. Free historical data
| Market | Sources | Depth / bar | Traps |
|---|---|---|---|
| US equities | Alpaca free (IEX only; SIP needs paid), Yahoo/Stooq daily, SEC EDGAR filings | daily 20+ years; 1 min limited; tick not free | Survivorship (delisted names missing), split/dividend adjustment, IEX is not the consolidated close (771.18 vs 771.10 measured), corporate-action lookahead |
| Options | CBOE delayed/EOD files, Alpaca options snapshots (recent only), our option-chain recorder (stopped when the server was retired) | deep history is paid (OPRA); free is shallow | Stale quotes, wide spreads, no historical IV surface, assignment/dividend effects |
| Crypto spot | Binance/Coinbase/Kraken public candles and trades, free | 1 min to tick, years | Exchange-specific, wash volume, listing survivorship (dead coins vanish) |
| Crypto perps | Exchange public funding and klines (we hold a recorder on Kalshi perps only), Binance/Bybit/OKX public | 1 min, funding history years | Funding timing, mark vs last, liquidation cascades unmodelled, venue not usable by a US LLC (check) |
| Futures | CME delayed, Databento/Polygon paid; free: Stooq/Yahoo continuous series, Quandl-style legacy | daily free; intraday paid | Continuous-contract roll artefacts, tick-size/session changes, no free depth |

## 2. Capital and rules (small US LLC), flags to verify
- Equities: pattern day trader rule (4+ day trades in 5 days on margin accounts under $25k) was under reform; cash accounts have settlement limits; margin 2:1 overnight. Wash-sale applies to securities (tax flag).
- Options: broker approval levels (1 to 4); defined-risk spreads usually level 2 to 3; short options need margin or cash-secured; assignment risk on short legs.
- Crypto spot: no PDT, usually no leverage for US retail; tax treated as property (flag). Perps: US retail access to offshore perps is restricted; regulated US perps are new and thin (check venue legality for an LLC).
- Futures: per-contract margin set by broker/CME (micro contracts, e.g. MES/MNQ, need low thousands); no PDT; Section 1256 tax treatment (flag); cleanest leverage for a small account.

## 3. Competition and where retail-sized edges can remain
- Equities (large/mid cap, liquid): none in fast signals; HFT/market makers win. Plausible: slow, capacity-limited (small caps, post-event drift, index inclusion), but costs and survivorship eat backtests.
- Options: market makers price the surface well. Retail-sized niches: selling structurally overpriced premium (variance risk premium) is real but is insurance with fat tails, not an edge you can verify in months.
- Crypto spot: efficient on majors; alts have wide spreads (our measurement). Events (listings, unlocks) are crowded.
- Perps: funding carry exists but is a risk premium; crowded, venue risk.
- Futures: deepest liquidity and lowest friction, so least room for a small edge, but costs are lowest and a sound structure (trend/carry across many markets) is documented with decades of data. Edge is small and slow.

## 4. What transfers
Falsification-first registration, deflation counting (ledger), fee modeling with real tickets, holdout guard, audit hooks, recorders for forward data, scan harness (needs a new adapter per market; Kalshi-specific fee model must be replaced). What does NOT transfer: Kalshi's fixed-payout structure (binary), the 3c to 30c cheap-side logic, the 15 minute window cadence.

## 5. Two testable ideas per market (priors honest, mostly low)
- Equities: (a) post-earnings drift in small caps, 20 day hold, net of 0.3% cost; prior of passing 10%. Loser: slow institutions/inattentive holders. (b) S&P index-inclusion run-up, prior 8%; loser: index funds forced to buy at a known date (crowded now).
- Options: (a) short-dated index put spread at fixed delta vs realized vol, prior 10% (premium exists, tail risk makes the bar hard to clear on a short sample); loser: hedgers paying for insurance. (b) earnings IV crush calendar, prior 5%.
- Crypto spot: (a) funding-rate extreme mean reversion on majors, prior 8%; loser: late leveraged longs. (b) weekend spread/volume seasonality in alts, prior 5%; costs likely kill it.
- Perps: (a) funding carry delta-neutral (spot vs perp), prior 20% for a small positive carry, but it is a risk premium with venue and basis risk. (b) liquidation-cascade fade, prior 5%. Both already partly covered by our 40 tests.
- Futures: (a) multi-market trend following (micro contracts), prior 15% for a positive net result over a decade, many false starts shorter; loser: hedgers/mean reverters. (b) roll-yield/carry across commodities, prior 12%; loser: producers hedging.

## 6. Recommendation
Scope ONE market first: futures (micro index and a few commodities), starting free daily data only. Why: no PDT rule, lowest friction, longest honest history, defined tax treatment, fits slow low-capacity rules where our harness (registration, deflation, holdout) is strongest, and nothing in it requires fast infrastructure. First deliverable (research only): a futures adapter for scan.py with real roll handling and a contract-level fee model, one registered trend-following family, zero accounts. Honest expectation: a small, slow edge at best, no income soon; an unfunded passing backtest here proves little until forward data confirms it. Keep Kalshi research and the live bot running in parallel.
