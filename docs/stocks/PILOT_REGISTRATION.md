# Pilot registration (Nov 12, 2026): schema check, scores nothing, no ledger try

Universe rule (hand-typed, fixed before any pull; 20 per listing venue, large, long-listed, no ticker changes or major spin-offs since 2018 known to the desk):
- XNAS.ITCH: AAPL MSFT AMZN GOOGL NVDA INTC CSCO PEP COST ADBE NFLX AMGN GILD QCOM TXN SBUX MDLZ CMCSA AVGO AMAT
- XNYS.PILLAR: JPM BAC WFC XOM CVX JNJ PG KO WMT HD DIS VZ T MRK PFE UNH CAT BA MMM LLY

Free estimates run Nov 12 ~17:15Z, 2018-05-01 to 2026-11-12, historical-streaming (recorded figure was $0.30):
| Dataset | Schema | Estimate |
|---|---|---|
| XNAS.ITCH | ohlcv-1d | $0.0704 |
| XNYS.PILLAR | ohlcv-1d | $0.0672 |
| XNAS.ITCH | statistics | $0.0819 |
| XNYS.PILLAR | statistics | $0.0815 |
| Pilot total | | $0.3010 |
| One-week schema check (2024-03-04 to 03-09), statistics, each venue | | $0.0002 each |
| S1: ARCX.PILLAR statistics, SPY QQQ IWM DIA | | $0.0185 |
| S1: ARCX.PILLAR ohlcv-1d, same | | $0.0134 |
| S1 total | | $0.0319 (recorded $0.03) |

Question the pilot answers: does the `statistics` schema on the listing venue carry the official opening and closing auction price per name (stat types), on each venue, across the whole span? Raw output stays in scratch space only.

STATUS: no paid pull made. The first pull call (one week of statistics, about $0.0004) was refused by the session's permission classifier; no workaround attempted. Spend $0.
