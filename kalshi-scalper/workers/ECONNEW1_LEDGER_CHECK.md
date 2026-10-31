# ECONNEW1 step 1: ledger check for economic-release markets (Strategy Research V2, 2026-10-30 evening, research only)

No settled result was read for any angle here. Counts, dates, volumes and spreads only. There is no `research/MECHANISMS.md`; the record is
`README.md` and `workers/CENSUS_2026-10-30.md`. Section names below are the README headings they come from.

## 1. What is already crossed off (with where)

| Item | Verdict | README section / worker file | What it covered |
|---|---|---|---|
| CPI1 | NOT_ENOUGH_DATA | "Pre-registration: CPI1" + "CPI1 amendment (2026-10-28 ...)" + "Result: CPI1 (run once on 2026-10-28 ...)"; `src/scalper/cpi1.py` | Cleveland Fed nowcast against Kalshi KXCPI / KXCPICORE "above T" strikes, quote 24 h before release. 7 trades on 2 releases: only 29 headline and 19 core markets (2 events each) had a bid AND ask candle; Kalshi's hourly history before about 2026-08-24 holds trades, not quotes. Re-checked today from the stored candles: at 24, 12, 6, 2 and 1 hours before the release, 14 headline and 8 to 9 core markets, 2 events. **CORRECTION (found later the same day, see ECONNEW1_RESULT.md): that count is a parser artifact.** `cpi1.py` read the field `close_dollars`, which only LIVE candles use; Kalshi's historical candles name it `close`. A raw historical candle of CPI-24JUN-T0.1 has a bid and ask in 22 of 22 hourly candles. So CPI1's NOT_ENOUGH_DATA cause ("quotes missing 24 h before") is wrong and CPI1 has never been validly scored; `ment1.py` has the same bug. A last-trade-price version (CPI2) was named in the result as a different cost rule needing its own registration; it has not been registered. |
| EVT1 macro cells | NOT_ENOUGH_DATA | "Result: EVT1 (scheduled-event windows, gold and Bitcoin), 2026-10-29"; `workers/EVT1_*` | gold and Bitcoin 15 minute markets around CPI, PPI, jobs, retail, GDP, FOMC, claims, EIA: 1 to 7 windows each. |
| L10 / N4 | underpowered, "not runnable" at the time | README section with the N4 row ("Scheduled releases (L10)"), table rows `L10`, `N3`, `O20` | gold and Bitcoin favourites in the 15 minutes around CPI, jobs, FOMC; 6 to 8 events in 69 days. Superseded by CAL and EVT1. |
| CAL (event calendar) | information only (a calendar and a power count, no result) | `workers/CAL_RESULT.md`, `workers/CAL_build.py`, `workers/CAL_power.py`, `workers/CAL_REL1_DRAFT.md`; the file is `studies/EVENT_CALENDAR_2026.csv` | 262 rows, 2026-08-01 to 2026-12-31, from bls.gov/schedule/2026, bea.gov/news/schedule/full, Census release PDFs, federalreserve.gov, eia.gov, fiscaldata.treasury.gov and exchange status pages. Claims rows are `rule` (dol.gov answered 403). Pooled 8:30 ET windows reach 300 entries on 30 days about mid-December 2026. |
| DAILY2 | FALSIFIED x3 | "DAILY2, Kalshi daily WTI, EUR/USD and USD/JPY markets ..."; `workers/DAILY2_*`, `src/scalper/daily2.py` | daily range markets against Yahoo reference prices. 10 year Treasury daily: NOT_RUNNABLE (no settled series). |
| INX1 | FALSIFIED | "INX1, Kalshi's S&P 500 and Nasdaq 100 4 pm ..."; `workers/INX1_*` | index "above K" markets against index plus implied volatility. |
| Treasury 15 minute rate series (KX2YRRATE15M, KX5YRRATE15M, KX10YRRATE15M, KX30YRRATE15M) | NOT_RUNNABLE / NOT_ENOUGH_DATA | "Series admission" census (`FLAT` replication section, 8 series incl. 4 yields at 158 markets each), "NEWH17" screen (`workers/NEWH17_SCREEN.md`), YIELDMAKE dated re-look about 2026-11-30 | 476 windows, 25c spread, 12 days of history all of it holdout. Fee arithmetic: a taker entry on a wide spread needs about 73%. |
| NEWH10 I2 | information only | "Result: NEWH10 ..."; `workers/NEWH10_RESULT.md` | 7:30 AM CT (8:30 ET) release hour on the Bitcoin hourly ladder: 15 release days, 30c wing wins 53% (PF 2.56) against 18% other weekdays. Not a claim; history cannot add events. |
| GAS1 / GAS1-F (not a release but an economic series) | FALSIFIED (GAS1), forward GAS1-F open | "GAS1: the AAA national average gas price ladder"; "Gas price markets, full 67 day look (2026-10-22)" | persistence model for the daily AAA ladder with no futures input (its own text names "the futures market" as the blind spot). |
| MENT1, EVT-style sports/mentions | not economic | listed only to say they are not this family | |

Not found anywhere in the ledger: weekly jobless claims strikes (KXJOBLESSCLAIMS / KXJOBLESS), payrolls (KXPAYROLLS), unemployment (KXU3), PCE (KXPCECORE), retail sales,
GDP, ISM, JOLTS, housing starts, PPI, FOMC decision (KXFEDDECISION / KXFED) as markets to score; EVT1 and CAL used the release dates only as windows for 15 minute markets.

## 2. Economic-release series Kalshi lists today (public API, 2026-10-30 evening)

Settled counts are the union of `/historical/markets` (older) and `/markets?status=settled` (recent); "events" are distinct `event_ticker`. First/last are market close dates.
Spread is the median YES ask minus bid over currently OPEN markets whose mid is between 3c and 97c (a snapshot of today, not history). Volume is the median contracts per
settled market. Quote history (bid and ask) exists only from about 2026-08-24; before that the candles carry trade prices only.

| Series | Release | Freq | Settled markets / events | First to last | Median vol (settled) | Open-market median spread now | Ledger |
|---|---|---|---|---|---|---|---|
| KXJOBLESSCLAIMS | initial jobless claims (Thu 7:30 CT) | weekly | 611 / 62 | 2025-06-12 to 2026-10-29 | 1,107 | 5.5c | NEW |
| KXJOBLESS (old format, one strike) | same | weekly | 74 / 69 | 2021-07-21 to 2022-12-01 | 1,191 | closed | NEW |
| KXCONTCLAIMS | continuing claims | weekly | 110 / 10 | 2026-08-27 to 2026-10-29 | 32 | 7c | NEW |
| KXPAYROLLS | jobs report | monthly | 396 / 43 | 2023-04-07 to 2026-10-02 | 23,464 | 7c | NEW (queued behind CPI in the CPI1 amendment) |
| KXU3 | unemployment rate | monthly | 599 / 63 | 2021-08-05 to 2026-10-02 | 1,793 | 4c | NEW |
| KXCPI | CPI m/m | monthly | 522 / 64 | 2021-07-12 to 2026-10-14 | 16,822 | 3c | CPI1 |
| KXCPICORE | core CPI m/m | monthly | 463 / 52 | 2022-07-13 to 2026-10-14 | 2,153 | 1.5c | CPI1 |
| KXCPIYOY | CPI y/y | monthly | 671 / 47 | 2022-12-13 to 2026-10-14 | 3,337 | 2c | not tested |
| KXCPICOREYOY | core CPI y/y | monthly | 656 / 46 | 2023-01-12 to 2026-10-14 | 178 | n/a | not tested |
| KXECONSTATCPI, ...YOY | CPI (Econstats duplicates) | monthly | 91 / 8 and 211 / 10 | 2026-01-13 to 2026-10-14 | 3,400 to 3,700 | n/a | not tested |
| KXPCECORE | core PCE | monthly | 141 / 26 | 2022-12-23 to 2026-10-29 | 1,831 | 9c | NEW |
| KXPCEHEAD | headline PCE | monthly | 16 / 2 | 2026-09-30 to 2026-10-29 | 379 | n/a | NEW |
| KXGDP | GDP growth | quarterly | 192 / 22 | 2021-07-28 to 2026-10-29 | 15,957 | n/a | NEW |
| KXUSRETAIL | retail sales m/m | monthly | 69 / 8 | 2026-04-01 to 2026-10-15 | 1,707 | n/a | NEW |
| KXUSPPI | PPI m/m | monthly | 41 / 3 | 2026-05-13 to 2026-10-15 | 76 | 66c | NEW |
| KXISMPMI | ISM manufacturing | monthly | 105 / 14 | 2025-04-01 to 2026-10-01 | 740 | 7c | NEW |
| KXJOLTSOPEN | JOLTS | monthly | 20 / 2 | 2026-09-01 to 2026-09-29 | 394 | n/a | NEW |
| KXHOUSINGSTART | housing starts | monthly | 58 / 7 | 2026-04-29 to 2026-10-20 | 614 | 88c | NEW |
| KXFEDDECISION | FOMC decision | per meeting | 150 / 30 | 2023-05-03 to 2026-10-28 | 307,826 | n/a | NEW |
| KXFED | fed funds target at meeting | per meeting | 424 / 42 | 2021-07-26 to 2026-10-28 | 22,273 | 40c (far meetings) | NEW |
| KX2YFOMC, KXSPXFOMC | market move on FOMC day | per meeting | 10 / 1 and 23 / 2 | 2026-07 to 2026-08 | 118 and 873 | n/a | EVT1-adjacent, not tested |
| KXAAAGASW | AAA gas price, weekly | weekly | 1,078 / 142 | 2023-10-09 to 2026-10-26 | 18,043 | n/a | GAS1 covered the DAILY ladder only |
| KXAAAGASD | AAA gas price, daily | daily | 3,928 / 244 | 2023-09-18 to 2026-10-30 | 3,830 | n/a | GAS1 FALSIFIED |
| KXAAAGASM | AAA gas price, monthly | monthly | 461 / 34 | 2023-12-31 to 2026-09-30 | 24,268 | n/a | not tested |
| KX2YRRATE15M etc. | Treasury yield, 15 minute | 15 min | 158 each over 12 days | 2026-10 | thin | 25c | see section 1 |

Facts that change the sample-size picture relative to the brief's assumption ("history only from 2026-08-24, so weekly series have about 10 events"):
1. Kalshi's historical endpoint serves much older settled markets. Claims have 62 weekly events from 2025-06 plus 69 from 2021-2022 (one strike each), payrolls 43 monthly events, unemployment 63.
2. CORRECTION: the older (historical) candles DO carry yes_bid and yes_ask (under the key `close`, not `close_dollars`). The first draft of this file said they hold trade prices only; that came from the same parser bug as CPI1. Claims has hourly quotes for 59 of its 62 events (151 quote-mode entries in the ECONNEW1 run); the quotes of an empty book can be very wide (for example bid 0.08 / ask 0.97), so a quote is not a fill.

## 3. Decision per candidate angle

Verdict key: NEW = not crossed off; REWORD = of what; RUNNABLE needs a public no-key source for the signal and enough settled events for the bar; NOT_RUNNABLE says why and the date.

| Angle | NEW / REWORD | Runnable? | Reason, evidence, date the bar could be met |
|---|---|---|---|
| (a) Weekly initial jobless claims strikes against the previous prints and the 4 week average | NEW (no claims market is in the ledger; EVT1 used claims only as a clock) | **RUNNABLE** | Source: FRED `fredgraph.csv?id=ICSA` (public CSV, no key; fetched 2026-10-30, last row week ending 2026-10-24 = 194,000). Events: 62 weekly events 2025-06-12 to 2026-10-29 with hourly bid and ask candles. Weekly, so the forward record grows by 1 event a week: Run now on 62 events (see ECONNEW1_RESULT.md: FALSIFIED). The bar of 25 releases was met by history, not by waiting. Risks stated up front: FRED holds revised and re-seasonalised history (the prior week's print is revised, fine; a small look-ahead from annual seasonal-factor revisions); the market is liquid and the persistence model is what every desk has. Prior of a pass under 5%. **Registered: ECONNEW1 angle (a).** |
| (b) CPI / jobs / PCE strikes against the Cleveland Fed nowcast or a consensus | REWORD of CPI1 for CPI; payrolls has no nowcast; PCE is a new series but the same instrument | **REOPENED: RUNNABLE, not scored here** | CPI: CPI1 died on what turned out to be a parser bug (see the correction above), so the registered CPI1 rule can be rerun as written on about 50 releases once the candles are refetched with the field fix; I did not spend a try on it because it needs the main session's approval to rerun a refused result file and it was past the time cap. The old text follows for the record: a last-trade rule (CPI2) would give about 50 events but is a different cost rule; since CPI1 was killed by the data and not by a result, CPI2 is allowed in principle, but it is a REWORD and would take one of the 3 tries on an instrument whose own spread is 1.5c to 3c and that is the most watched macro market on the exchange (14,000 to 46,000 contracts a strike). Not spent now; dated: re-read CPI1 on quotes when CPI has 25 releases with quotes, about Nov 2028 (Cleveland data), so not a date that matters. Payrolls: no free forecast source (consensus is proprietary, ADP is not public, the Cleveland Fed publishes no payrolls nowcast): NOT_RUNNABLE, no date. Core PCE: the Cleveland file has a core PCE nowcast (`Core PCE Inflation`, `Actual Core PCE Inflation` in the same nowcast_month.json CPI1 used), 26 events 2022-12 to 2026-10, median volume 1,831, spread 9c; with the parser fix its history has quotes, so it is RUNNABLE as a REWORD of CPI1 (same source, same instrument type), about 26 releases, right at the 25 release minimum; not spent here. |
| (c) FOMC decision markets against fed funds futures | NEW | **NOT_RUNNABLE** for the bar | Source: CME FedWatch is not an API. A public substitute exists: the Atlanta Fed Market Probability Tracker (`mpt_histdata.xlsx`, fetched 2026-10-30, 7 MB; probabilities of a cut or hike over a SOFR reference window from CME 3 month SOFR options, from 2023-03-29, daily). It is readable without a key. The blocker is the sample: 30 FEDDECISION events since 2023-05 and only the meetings where the market was not already at 90% or more have any room (a handful), and the bar needs 25 independent events. Next FOMC meetings: Dec 9, 2026, then Jan 27 to 28, 2027; about 8 a year, so the bar is years away (2030). Source recorded for a forward-only registration only if the owner wants it. |
| (d) Release-day price path in the hour before the release (drift vs consensus), entry look fixed beforehand | REWORD of the L-series price-pattern family and of EVT1's windows; no consensus source | **NOT_RUNNABLE** as a mechanism | There is no public consensus forecast (Bloomberg, Reuters, Trading Economics are paid or unkeyed-unavailable), so "drift vs consensus" has no information source; a price-only drift rule is a price pattern with no counterparty, the family the ledger has falsified over and over (EVT1 control, REF_BTC_UNDERDOG_180). Minute candles before 2026-08-24 carry no quotes. Not tried. |
| (e) Treasury 15 minute series around 8:30 ET releases | REWORD of YIELDMAKE and EVT1 | **NOT_RUNNABLE** | 12 days of history, all holdout, 25c median spread; the fee arithmetic (7% x p x (1-p) at the quote plus half of 25c) needs a win rate of about 73% from a coin-flip entry. YIELDMAKE is the dated re-look, about 2026-11-30. |
| (f) Weekly AAA gas price ladder against wholesale gasoline (RBOB futures) | NEW (GAS1 used persistence only and named the futures market as its blind spot) | **RUNNABLE, not scored in this session** | 142 weekly events, median volume 18,043, source Yahoo `RB=F` public chart (the same kind the repo already reads). Needs another 1,078 candle downloads under the current Kalshi 429 rate limit (the claims download alone ran about 7 markets a minute), which does not fit the time cap. Registered as a proposal for the next session (ECONNEW2), not as a try. |

Summary: **one registered angle (claims), one runnable angle deferred for time (weekly gas vs RBOB), three NOT_RUNNABLE, one NOT_ENOUGH_DATA.**

## 4. Upcoming releases, next 30 days (2026-10-31 to 2026-11-30; US Central; from `studies/EVENT_CALENDAR_2026.csv`)

| Date | Time CT | Release | Status |
|---|---|---|---|
| Wed Nov 4 | 9:30 | EIA petroleum status | verified |
| Thu Nov 5 | 7:30 | Jobless claims (KXJOBLESSCLAIMS-26NOV05, open now) | rule |
| Fri Nov 6 | 7:30 | Employment Situation, October (KXPAYROLLS, KXU3) | verified |
| Tue Nov 10 | 7:30 | CPI, October | verified |
| Thu Nov 12 | 7:30 | Jobless claims | rule |
| Fri Nov 13 | 7:30 | PPI, October | verified |
| Tue Nov 17 | 7:30 | Advance retail sales | verified |
| Thu Nov 19 | 7:30 | Jobless claims | rule |
| Wed Nov 25 | 7:30 | GDP second estimate Q3; Personal Income and Outlays (PCE) | verified |
| Wed Nov 25 (Thanksgiving week) | 7:30 | Jobless claims (the calendar row for Thu Nov 26 is `unverified`; DOL moves it to Wednesday in holiday weeks, to be confirmed on dol.gov) | unverified |

FOMC: no meeting in the window (next Dec 9, 2026). Treasury auctions are in the calendar file but are not part of this family.
