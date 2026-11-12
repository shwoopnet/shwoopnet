# Stocks desk data plan (Task 1), Nov 12, 2026

Carried over from the predecessor desk (its commit a7133e69, sha256 390e0de9...). Re-committed here with the Alpaca items marked out of scope per the Head's ruling 5.

**SPEND SO FAR: $0 of the $25 cap. Pulls made: 0. Paid calls made: 0.** Every figure came from Databento's free metadata calls. No Databento data is in this file. No credential was seen. Databento is reached through the proxy (hist.databento.com answered free metadata calls on Nov 12).

## (a) Sources, terms read Nov 12, 2026

**Databento** (Terms of Use effective Jan 31, 2024; User Agreement read Nov 12, no effective date shown).
- 1.1: licence is "solely for its internal business purposes".
- 1.5(e): "Customer agrees to limit all use of Third-Party Data by itself and its Authorized Users to internal Customer purposes and not to engage in any Redistribution of Third-Party Data"; Redistribution is "publication or distribution of covered data ... and all other means of furnishing such data or other information derived from the same to entities other than Customer".
- 1.6: any Redistribution needs "explicit attribution of Databento as its source".
- On termination "you will immediately destroy any downloaded or printed Materials"; 9.3: afterwards the customer "may no longer download, access, or use any Third-Party Data".
- Risk, flagged not resolved: "information derived from" furnished to anyone but us falls inside Redistribution, and a public repo is "anyone". Aggregates are the weakest claim, prices and per-day series the strongest. Until the owner rules: no derived result in the repo (Head ruling 1).

**Alpaca market data** (out of scope: owner cut Alpaca Oct 26; kept only as record). Basic plan free, IEX only, history since 2016, latest 15 minutes withheld; Algo Trader Plus $99 a month. NASDAQ OMX subscriber agreement: Non-Professional data "only for personal use". Alpaca redistribution terms not read.

### Estimated cost (free estimate call, historical-streaming)
| Item | Estimate |
|---|---|
| Pilot, 40 liquid names, daily bars plus closing statistics, 2018-05 to now (XNAS.ITCH, XNYS.PILLAR): ohlcv-1d $0.07+$0.07, statistics $0.08+$0.08 | $0.30 |
| 500-name universe, same (extrapolation, exact call before any pull) | about $4 to $5 |
| Closing imbalance, 40 names, 1 year: XNAS 20 names $4.43, XNYS 20 names $9.86 | $14.29 |
| Closing imbalance, 40 names, 3 years | about $43, over cap |
| 1 minute bars, 40 names, Apr 2023 to now (EQUS.MINI) | $9.45 |
| 1 minute bars SPY, QQQ, IWM same span | $0.84 |
| Consolidated daily, ALL symbols, Apr 2023 to now (EQUS.MINI) | $13.13 |
| ARCX.PILLAR ohlcv-1m SPY 2018-05 to now | $1.15 |
| ARCX 1m eight ETFs (SPY SSO SPXL SPXU SDS QQQ TQQQ SQQQ) | $6.83 |
| ARCX statistics SPY QQQ IWM DIA | $0.02; ohlcv-1d $0.01 |
| May 2018 ALL_SYMBOLS ohlcv-1d: XNAS / XNYS / ARCX | $0.25 / $0.11 / $0.24 |

Traps: ALL_SYMBOLS imbalance, one month, Nasdaq $239.25, NYSE $25.71. Statistics all symbols 2018 on: XNAS $44.04, XNYS $11.09, ARCX $6.38. EQUS.SUMMARY statistics $38,805. Use named universes. Keep at least $5 unspent.

## (b) What each source provides
Databento: official close = `statistics` schema on the LISTING venue's dataset (XNAS.ITCH, XNYS.PILLAR, ARCX.PILLAR) from 2018-05-01; `imbalance` on the same. Presence of the closing-price stat per venue NOT yet confirmed (the pilot checks it, against the SPY lesson in CLAUDE.md). Consolidated daily EQUS.SUMMARY from 2024-07-01 only; intraday EQUS.MINI and DBEQ.BASIC from 2023-03-28, composites NOT verified equal to the SIP; before 2023 single venue only (the IEX-is-not-the-close lesson). Bars unadjusted; corporate actions product NOT confirmed. Delisted names resolve (SIVB, dated mapping). Earnings dates and index lists are not in Databento: hand-typed dates with source only (Head ruling 6).
Survivorship: freeze the universe by a rule on data known at the start date, including names that later delisted.

## (c) Paper and live route (facts, no action)
No working broker key exists. Any route would be: paper at pinned rules first, then the owner's popup for any live probe. Nothing exists today and no account was opened or changed.

## (d) Owner questions (popup-ready)
1. Databento redistribution: may aggregate results (no prices or series) go in the PUBLIC repo? (a) ask Databento support in writing first, results stay in messages (recommended); (b) aggregates only, accept the risk; (c) never in the repo.
2. Spend: keep $25 (pilot $0.30, universe daily about $5, one-year imbalance $14.29, reserve $5+) or raise to $50?
3. Alpaca key: moot after Head ruling 5.
4. Is the Databento account personal or a business entity? (Nasdaq "only for personal use"; Databento "internal Customer purposes".)
5. OK to use SEC EDGAR and S&P and Russell announcements for dates, hand-typed with source? (Head: hand-typed only.)
