# NEWH15 inventory: every Kalshi series with 15 minute markets (2026-10-30, public API, no key, no scoring)

Built from Kalshi's public `/series` list (15,562 series; **38 have frequency `fifteen_min`**), the paged `/markets?status=settled`
listing of each (all history Kalshi still serves: it starts **2026-08-24**), and each series' posted rules and settlement source.
Spreads are the median at the candle ending 10 minutes before the close, from the candle files already on disk (they end around
Oct 23 and hold only two-sided quotes); volume is contracts traded per settled market from the listing. Nothing here is a result.
The inventory step read no strategy outcome; the only outcome-adjacent counts are tie counts (settled value equal to the strike).

## Table (all 38)

| Series | What it settles on (source) | First settled | Settled windows | Median contracts / market | Median spread at 10 min left | In the ledger |
|---|---|---|---|---|---|---|
| KX10YRRATE15M (10-year Treasury yield 15-minute) | Pyth - 10Y UST; 1 min yield candle close vs an "opening target yield" (single print), listed 07:00 to 21:00 UTC only | 2026-10-19 | 476 | 168 | 25c (n 48) | L1 shape only (FLAT-R, 158) |
| KX2YRRATE15M (2-year Treasury yield 15-minute) | Pyth - 2Y UST; 1 min yield candle close vs an "opening target yield" (single print), listed 07:00 to 21:00 UTC only | 2026-10-19 | 476 | 377 | 25c (n 47) | L1 shape only (FLAT-R, 158) |
| KX30YRRATE15M (30-year Treasury yield 15-minute) | Pyth - 30Y UST; 1 min yield candle close vs an "opening target yield" (single print), listed 07:00 to 21:00 UTC only | 2026-10-19 | 476 | 171 | 25c (n 46) | L1 shape only (FLAT-R, 158) |
| KX5YRRATE15M (5-year Treasury yield 15-minute) | Pyth - 5Y UST; 1 min yield candle close vs an "opening target yield" (single print), listed 07:00 to 21:00 UTC only | 2026-10-19 | 476 | 161 | 25c (n 51) | L1 shape only (FLAT-R, 158) |
| KXADA15M (Cardano 15 Minute) | CF Benchmarks; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXAUDUSD15M (15-minute AUDUSD) | Pyth; exchange rate print vs open print | 2026-10-07 | 1,586 | 2297 | 3c (n 985) | yes (probe, FLAT-R) |
| KXBCH15M (Bitcoin Cash 15 Minute) | CF Benchmarks; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXBNB15M (BNB 15 min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 14345 | 1c (n 8307) | yes (FLAT2, XLEAD1, GEN1 pool; L1 shape and market-wide feature) |
| KXBRENT15M (Brent 15-minute) | Pyth - Brent; 1 min candle close vs 4:45-type open candle (single print) | 2026-10-21 | 674 | 5870 | 10c (n 69) | partly (FLAT-R, 71 markets) |
| KXBTC15M (BTC 15 min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 2544484 | 1c (n 4421) | yes (L1 live and ~200 variants) |
| KXCOFFEE15M (Coffee 15-minute) | Pyth; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXCOPPER15M (Copper 15-minute) | Pyth - Copper; 1 min candle close vs 4:45-type open candle (single print) | 2026-08-27 | 4,325 | 14919 | 2c (n 4485) | yes (FLAT2, HOUR2) |
| KXCRYPTOCOMP15M (Crypto Comparison 15 minute) | CF Benchmarks; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXCRYPTOLEAD15M (Coin Race 15 minutes) | CF Benchmarks; highest return of 5 coins | 2026-08-24 | 31,715 | 294 | - | NO (named once in FLAT-R, left out; never tested) |
| KXDJIA15M (Dow Jones 15-minute) | For example, Google Finance; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXDOGE15M (DOGE 15 min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 30394 | 1c (n 5584) | yes (L1 live, fills, FLAT2) |
| KXETH15M (ETH 15 min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 132766 | 1c (n 4420) | yes (L1 live, SMOOTH, SLOTEX-ETH, ETHFUNNEL) |
| KXEURUSD15M (15-minute EURUSD) | Pyth; exchange rate print vs open print | 2026-09-23 | 2,525 | 4982 | 3c (n 2691) | yes (FLAT2, DAILY2 is the daily range series) |
| KXGBPUSD15M (15-minute GBPUSD) | Pyth - GBPUSD; exchange rate print vs open print | 2026-09-23 | 2,525 | 3828 | 3c (n 2667) | yes (FLAT2) |
| KXGBPUSD15MTEST (GBPUSD 15M TEST) | Pyth; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXGOLD15M (Gold 15-minute) | Pyth - Gold; 1 min candle close vs 4:45-type open candle (single print) | 2026-08-24 | 4,723 | 280192 | 1c (n 4070) | yes (L1 live, ~100 registrations) |
| KXHYPE15M (HYPE 15 min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 22381 | 1c (n 8281) | yes (FLAT2, XLEAD1, GEN1) |
| KXINX15M (S&P 500 15-minute) | For example, Google Finance; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXKPOWMID15M (KPOW Midterms 15-minute) | Pyth - KPOW Midterms; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXNATGAS15M (Natural Gas 15-minute) | Pyth - NATGAS; 1 min candle close vs 4:45-type open candle (single print) | 2026-08-27 | 4,553 | 14399 | 1c (n 4715) | yes (GAS1, probe, FWD8) |
| KXNDQ15M (Nasdaq 100 15-minute) | For example, Google Finance; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXNEAR15M (NEAR 15m) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 14017 | 3c (n 8292) | yes (FLAT2, GEN1) |
| KXPALLADIUM15M (Palladium 15-minute) | Pyth - Palladium; 1 min candle close vs 4:45-type open candle (single print) | 2026-09-17 | 2,763 | 6436 | 3c (n 2916) | yes (FLAT2, HOUR2) |
| KXPLATINUM15M (Platinum 15-minute) | Pyth - Platinum; 1 min candle close vs 4:45-type open candle (single print) | 2026-09-17 | 2,763 | 6149 | 3c (n 2852) | yes (FLAT2, HOUR2) |
| KXSILVER15M (Silver 15-minute) | Pyth - Silver; 1 min candle close vs 4:45-type open candle (single print) | 2026-08-24 | 4,688 | 46656 | 1c (n 5952) | yes (PPW1, NEWH2 GSILV, CONF1 TWIN, FLAT2) |
| KXSOL15M (SOL 15 min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 51757 | 1c (n 6320) | yes (FLAT-R, QUOTE recorder; L1 shape only) |
| KXTON15M (TON 15m) | CF Benchmarks; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXUSDCAD15M (15-minute USDCAD) | Pyth; exchange rate print vs open print | 2026-10-07 | 1,586 | 2330 | 3c (n 999) | yes (probe, FLAT-R) |
| KXUSDJPY15M (Fifteen-min USDJPY) | Pyth; exchange rate print vs open print | 2026-09-23 | 2,525 | 3834 | 3c (n 2596) | yes (FLAT2) |
| KXUSDMXN15M (15-minute USDMXN) | Pyth; no market has ever settled / rules not posted | - | 0 | - | - | nothing to cover (0 settled windows) |
| KXWTI15M (WTI 15-minute) | Pyth - WTI; 1 min candle close vs 4:45-type open candle (single print) | 2026-08-24 | 4,916 | 72019 | 1c (n 6182) | yes (E5B, FLAT2, probe tests) |
| KXXRP15M (XRP 15 min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 63045 | 1c (n 5488) | yes (L1, paused; FLAT2, FWD7) |
| KXZEC15M (Zcash 15min) | CF Benchmarks; 60 s average vs prior 60 s average | 2026-08-24 | 6,428 | 16996 | 2c (n 8220) | yes (FLAT2, XLEAD1, GEN1) |

**New since the ledger's last census (Oct 22: "Kalshi lists 35 fifteen-minute series")**: `KXCRYPTOLEAD15M` (the Coin Race: first
settled 2026-08-24, so it is not new, just untested), `KXHYPE15M`/`KXZEC15M`/`KXNEAR15M`/`KXBNB15M` are in the ledger from Oct 22;
the only series added after that are `KX2YRRATE15M`-style rate series (Oct 19), Brent (Oct 21), USD/CAD (Oct 7), Platinum/Palladium (Sep 17)
and the empty shells: ADA, BCH, TON, S&P 500, Nasdaq 100, Dow Jones, USD/MXN, Coffee, Crypto Comparison, KPOW Midterms, and a
GBPUSD test series have **no settled market** (listed or initialised only), so nothing can be tested on them yet. The index series say "For
example, Google Finance" as the source and have never settled a window.

## Settlement mechanics (what each family settles on)

- **Crypto (CF Benchmarks RTI, 12 series incl. BTC on BRTI):** YES if the simple average of the 60 seconds of the index before the close is at
  least the average of the 60 seconds before the open. The strike of window k+1 is exactly the settled value of window k (`floor_strike` equals the
  previous `expiration_value`), so settled values chain.
- **Metals, oil, gas, copper (Pyth):** the close of the 1 minute Pyth candle at the close vs the close of the 1 minute candle at the open: two single prints.
- **FX (Pyth):** the pair's printed value at the close vs at the open.
- **Treasury yields (Pyth, 2/5/10/30 year):** the close of the 1 minute yield candle at the close vs an "opening target yield"; listed only 07:00 to
  21:00 UTC (3 AM to 5 PM ET); 25c median spread and 160 to 380 contracts a market: thin.
- **Coin Race:** five markets per window (BTC, ETH, SOL, XRP, HYPE); exactly one resolves YES, the coin with the highest return. 294 contracts a
  market (median), 5,000x thinner than BTC15M.
- **Ties resolve YES ("at least").** Tie counts of settled windows: WTI 131 of 4,916 (2.7%), XRP 91 of 6,428 (1.4%), EUR/USD 45 (1.8%), GBP/USD 48,
  AUD/USD 43 (2.7%), USD/CAD 36 (2.3%), 2-year yield 19 of 476 (4.0%), gold 16, silver 20, all others under 1%. A tie premium is half the tie rate on the YES side (at most
  about 1.3c for WTI) against a 7% quadratic fee of 1.75c at 50c plus a half spread: **killed by arithmetic, 0 tries.**

## Which series cleared the 1,500 settled windows line

BTC, ETH, SOL, XRP, DOGE, BNB, HYPE, ZEC, NEAR (6,428 each), gold 4,723, silver 4,688, WTI 4,916, natural gas 4,553, copper 4,325, palladium and
platinum 2,763, EUR/USD, GBP/USD, USD/JPY 2,525, AUD/USD and USD/CAD 1,586, and the Coin Race (6,343 events, 31,715 markets). Rates (476), Brent (674) and the
shells are under it. Every one except the Coin Race already has L1-shape tests (FLAT2, FLAT-R, GEN1 pool) and the mid-window candle-feature
families C, E, F, G are closed for BTC and gold; the other series' only mid-window tests are in the pooled GEN1 and FLAT searches.

## What was NOT designed, and why (ledger check, no tries spent)

| Idea | Reason |
|---|---|
| Prior-window continuation or fade on the thin RTI coins (strike chain noise reversion) | Same shape as BTC1 CONT/FADE (FALSIFIED), S06/S07, XLEAD1; a reworded tested rule. |
| Tie premium (YES side, WTI/rates/FX) | Arithmetic: 1.3c at most against 1.75c fee plus spread. |
| Market-wide or partner-lag rules between the 15 minute books | GEN1 market-wide feature and NEWH12 XLAG: FALSIFIED. |
| Scheduled releases (EIA storage, CPI, jobs, FOMC) on oil, gas, yields | About 9 to 15 releases in the 67 days: far under 100 trades (EVT1 already NOT_ENOUGH_DATA). |
| Rates, index, Brent | Under 700 windows or none ever settled (NOT_ENOUGH_DATA before a try). |
| Sessions and breaks on the other metals (the NEWH2 GBREAK, GREOPEN shape) | Gold's break tests FALSIFIED or NOT_ENOUGH_DATA; hour and clock variants are barred by the Oct 28 owner order. |
| Favourite or cheap-side calibration on any series | L1, TAIL and cheap-side-late, barred. |

The Coin Race is the one 15 minute family with thousands of settled windows and **no test in the ledger**; its three registered tries are in
`workers/NEWH15_REGISTRATION.md`.

## Recorder proposal (owner decision; nothing was built)

None needed for the registered tries (public candles suffice). If the Coin Race passes anything, the missing data is its **order book sizes**
(candles carry none, and median volume is 294 contracts a market, so a 10 contract fill is not observed): a recorder of the five race books
(top five levels every few seconds in the last 12 minutes) next to BTC15M would be the only way to test fills; see the result file.
