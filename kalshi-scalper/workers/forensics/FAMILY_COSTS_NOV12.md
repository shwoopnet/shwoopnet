# Measured costs by market family, first cut (2026-11-12)

For Desk B's census of Kalshi market families (task 5 from the Head of R&D). **A measurement from recorded public data only: no rule scored, no outcome value used (result files were read only for close and settle times), zero tries, zero Kalshi requests.** Nothing about the live account. Scripts `familycost_15min.py`, `familycost_ladder.py`, `familycost_list.py`; raw output `results/FAMILYCOST_R6.json`, `FAMILYCOST_NC15.json`, `FAMILYCOST_LADDER.json`, `FAMILYCOST_LIST.json`. The 15 minute and ladder scripts were drafted by a helper and checked by this desk: their haircut for the Bitcoin cheap side (67% at the ask seen, 82% with +1c, 2 s) and for the gold favourite (55%, 92%) reproduce FILLHAIRCUT1 and GOLDHAIRCUT1.

## How to read the columns

- **Taker fee** assumed everywhere: 0.07 x price x (1 - price) per contract per side traded, settlement free. That is 1.75c a side at 50c, 0.6c at 10c or 90c. Desk B holds the fee-class column; where a family has a different fee the cost figures below must be redone.
- **Hold cost** = half the spread plus one fee: what a 1 contract taker gives up against the mid when buying and holding to settlement. **Round trip** = the whole spread plus two fees: in and out before settlement. Medians over two-sided quotes; "p75" is the 75th percentile.
- **Fill haircut** (only where an order book is recorded): a 1 contract buy with its limit at the ask seen; the share that still finds that price at the first book poll at least 2 s later and at least 6 s later, and the same with the limit 1c higher. Both sides of every two-sided instant. Written "at ask / +1c".
- **Data kind**: BOOK = order book reads (current). CANDLE = 1 minute candles (current, measured on Bitcoin 15 minute only, CANDLEVSBOOK1). LIST = market-list quotes, a copy up to about 11 s old, and not simultaneous across markets.
- A market's brackets or strikes are ONE event, not several.

## A. Families with a recorded order book

### 15 minute series (R6: closes Oct 29 to Nov 12; NC15: closes Nov 11 19:45Z to Nov 12 16:00Z, about 20 hours, one weekday)

Events: a new market every 15 minutes while the underlying trades, so up to 96 a day; about 35,000 a year for a crypto series, about 24,000 for one that closes at weekends (my arithmetic, not a count). Settlement: a result was already posted at the recorder's read about a minute after the close in 99.7% to 99.9% of R6 windows and 98% to 100% of NC15 windows. Look at 6 minutes before the close (400 to 330 s); the second haircut pair is 6 s.

| Series | Windows measured | Contracts traded per window (median) | Two-sided at 6 min / at 2 to 3 min | Spread median (p75) | Size at the touch (median) | Hold cost | Round trip | Fill at 2 s: at ask / +1c | Fill at 6 s |
|---|---|---|---|---|---|---|---|---|---|
| Bitcoin | 981 | 3,400,000 | 100% / 95% | 1c (1c) | 3,500 | 1.5c | 3.0c | 62% / 85% | 56% / 77% |
| Ethereum | 983 | 225,000 | 100% / 95% | 1c (1c) | 400 | 1.5c | 2.9c | 62% / 84% | 56% / 76% |
| XRP | 988 | 136,000 | 100% / 93% | 1c (1c) | 200 | 1.5c | 3.0c | 64% / 86% | 57% / 77% |
| Dogecoin | 1,005 | 66,000 | 100% / 96% | 1c (1c) | 72 | 1.5c | 2.9c | 66% / 86% | 58% / 77% |
| Gold | 658 | 500,000 | 100% / 99% | 1c (1c) | 1,500 | 1.5c | 3.0c | 63% / 84% | 57% / 75% |

NC15 polls every 5 s, so its two haircut pairs are at about **5 s and 10 s**, not 2 s and 6 s.

| Series | Windows | Contracts per window (median) | Two-sided at 6 min / at 2 to 3 min | Spread median (p75) | Size at the touch | Hold cost | Round trip | Fill at 5 s: at ask / +1c | Fill at 10 s |
|---|---|---|---|---|---|---|---|---|---|
| WTI oil | 59 | 101,000 | 100% / 100% | 1c (1c) | 160 | 1.7c | 3.4c | 62% / 81% | 56% / 74% |
| Silver | 51 | 92,000 | 100% / 100% | 1c (1c) | 177 | 1.9c | 3.7c | 59% / 78% | 55% / 71% |
| HYPE | 63 | 37,000 | 100% / 92% | 1c (2c) | 32 | 1.7c | 3.5c | 59% / 76% | 55% / 69% |
| BNB | 62 | 29,000 | 100% / 85% | 1c (1c) | 29 | 1.6c | 3.3c | 61% / 77% | 55% / 70% |
| Natural gas | 65 | 23,000 | 100% / 93% | 2c (4c) | 130 | 2.5c | 5.1c | 71% / 82% | 64% / 75% |
| Copper | 54 | 15,000 | 99% / 84% | 3c (5c) | 26 | 2.8c | 5.6c | 69% / 80% | 62% / 73% |
| EUR/USD | 52 | 7,600 | 98% / 64% | 2c (2c) | 560 | 1.7c | 3.4c | 73% / 83% | 66% / 78% |
| AUD/USD | 62 | 7,300 | 98% / 68% | 2c (2c) | 560 | 1.6c | 3.1c | 73% / 84% | 66% / 78% |
| USD/JPY | 59 | 6,700 | 100% / 75% | 2c (2c) | 560 | 2.0c | 3.9c | 71% / 82% | 66% / 77% |
| GBP/USD | 52 | 5,700 | 97% / 73% | 2c (2c) | 560 | 2.0c | 4.0c | 71% / 82% | 65% / 77% |
| USD/CAD | 59 | 3,800 | 97% / 72% | 3c (6c) | 180 | 2.5c | 5.0c | 68% / 80% | 63% / 74% |

What the two tables say for a card writer:

1. **The fee is most of the cost, not the spread.** On the liquid series the spread is one tick; a round trip at a mid-priced market costs about 3c, of which 2c or more is fee. Any card needs its edge per contract to clear about 1.5c (hold) or 3c (in and out) at mid prices before anything else.
2. **A third of taker orders miss.** At the ask seen, 59% to 73% fill a few seconds later on every series; with a 1c higher limit 76% to 86%. So a card's paper count should be cut by about a third, or its price raised by 1c and the count cut by about a fifth. This is the same on every 15 minute series measured, crypto or not.
3. **The forex series are thin where it matters**: one maker posts 560 contracts 2c wide, traded volume is 20 to 500 times smaller than Bitcoin's, and the book is one-sided in a quarter to a third of instants at 2 to 3 minutes before the close. Copper, natural gas and USD/CAD cost 5c or more a round trip.
4. The NC15 rows rest on 20 hours of one weekday. Treat them as a first reading.

### Hourly Bitcoin ladder (`book/`, Nov 8, 10, 11; 64 hourly events, the 7 strikes nearest the money)

Events: 24 a day, about 8,760 a year; strikes of one hour are one event. Settlement speed: not recorded. Contracts traded per strike over the 55 recorded minutes: 100,000 at the median.

| Look | Strikes | Two-sided | Spread median (p75) | Size at the touch | Hold cost | Round trip | Fill at 3 s: at ask / +1c | Fill at 6 s |
|---|---|---|---|---|---|---|---|---|
| 30 minutes before, all 7 strikes | 373 | 83% | 1c (1c) | 1,150 | 1.3c | 2.5c | 86% / 95% | 79% / 90% |
| 30 minutes before, mid 30c to 70c | 102 | n/a | 1c (1c) | 670 | 2.2c | 4.4c | 73% / 86% | 64% / 77% |
| 6 minutes before, all 7 strikes | about 370 | 39% | 1c (1c) | 1,030 | 0.9c | 1.8c | 79% / 91% | 73% / 85% |
| 6 minutes before, mid 30c to 70c | about 60 | n/a | 1c (2c) | 640 | 2.2c | 4.4c | 61% / 76% | 56% / 67% |

Near the money the ladder costs the same as the 15 minute market (about 4.4c a round trip) and fills a little better half an hour out. By 6 minutes before the close six strikes in ten are one-sided.

### Combos (`combo-data`, ONE snapshot, Nov 12 14:35Z; the recorder began today)

5,000 combos listed (the list was cut off there), 400 with any posted quote or any volume, **18 of 400 (4.5%) two-sided**. On those 18: spread 3.4c at the median on a 13c mid; round trip 4.3c, a third of the price. A YES bid above zero on 9%, a YES ask under 1 on 7%; 43% have ever traded; legs 10 at the median. The 5 book rows captured have a bid on one side only. **Not enough to cost.** What can be said: a taker can rarely trade both ways, so a combo card is a buy-and-hold card or nothing, and it should be priced at the posted ask with no assumption of an exit. Days to close: 2.5 at the median.

## B. Families recorded as list quotes only (no haircut can be measured; prices are a copy up to about 11 s old)

| Family | Sample | Events and settlement | Two-sided | Spread median (p75, p90) | Size at the ask | Hold cost | Round trip | Volume | Reading |
|---|---|---|---|---|---|---|---|---|---|
| **Sports, NBA moneyline** | 60 open games, Nov 8 to 12, polled about every 2 minutes | League schedule (not measured here). Settlement not recorded | 98% | 2c (3c, 9c) | 660 | 2.4c | 4.8c | 81,000 a market | Fee is 3.5c of the round trip |
| NBA spread, total (the two lines nearest 50c) | 34 games | same | 94% | 1c (2c, 3c) | 4,700 to 7,900 | 2.2c | 4.5c | 26,000 to 36,000 | Tight and deep |
| NFL moneyline | 33 games | same | 100% | 1c (2c, 4c) | 5,900 | 2.1c | 4.2c | 58,000 | Tight and deep |
| NFL spread, total | 20 games | same | 100% | 1c (1c to 2c) | 240 to 6,600 | 2.2c | 4.5c | 3,900 to 30,000 | |
| NHL moneyline | 68 games | same | 99% | 2c (4c, 6c) | 360 | 2.7c | 5.5c | 800 | Thin |
| **NHL spread, total** | 47 games | same | 96% to 98% | 3c to 4c (8c to 9c) | 290 to 690 | 3.2c to 3.5c | **6.4c to 6.9c (p75 10.7c to 12.5c)** | 6 to 950 | **Too costly for a taker, move on** |
| **Politics, all recorded series** | 3 snapshots, Nov 11 to 12; 20 series, 22 open events, 131 markets | 8 events closed in the 28 hours the result files cover (weekly shipping series, daily approval). Days to close 5.8 at the median. Settle delay not measurable from 3 snapshots | 83% | 1c (4c, 9c) | 1,570 | 1.7c | 3.4c, on a 12.5c cheap-side price (36% of the price) | 6,000 a market | Most markets sit near 0 or 1 |
| Politics, markets priced 20c to 80c | 40 markets | same | n/a | 3c (6c, 15c) | n/a | 3.2c | **6.3c (p75 9.3c)** | n/a | A card here needs 3c to hold, 6c to trade out |
| **Weather, daily high** | 14 cities, 74 city-days, Nov 4 to 11, 6 brackets each | 14 x 365 city-days a year; same-day cities move together. First seen settled a median 22 hours after the listed close (an upper bound: the result is looked for a few times a day) | 81% | 1c (2c, 4c); 20c to 80c brackets 2c (3c, 5c) | not recorded | 1.6c; 2.3c near the money | 3.3c; 4.5c near the money | 200 a bracket | Tradable for a holder; no sizes recorded |
| **Weather, daily low** | same | same | 76% | **10c (17c, 20c)** | not recorded | 5.8c; 10c near the money | **11.5c; 20c near the money** | 35 a bracket | **Too costly for a taker, move on** |
| **Daily and weekly commodity ladders** (gold, silver, copper, Brent, WTI, natural gas) | Daily watchlist, Nov 5 to 12, 4 to 5 events a series | One event per trading day (about 250 a year) or per week (52). Settled a median 61 to 81 minutes after the close (WTI daily 8 hours; weekly ladders about a day) | 28% to 74% | 1c to 4c (3c to 4c) | not recorded | 2c to 3c | 3.3c to 5.8c; 4.4c to 7.4c near the money | 0 to 2,700 a strike | Half the strikes or more have no two-sided quote |
| **Daily and weekly forex ladders, index dailies, Treasury yield dailies (the `KXUST` series)** (EUR/USD, USD/JPY, the AD and AW ladders, S&P 500, Nasdaq 100, Dow, 2 to 30 year Treasury yields) | same watchlist | Daily or weekly. Forex dailies settle 2 minutes after the close; index dailies 3 hours; Treasury yields 2.5 hours | 10% to 98% | **8c to 18c** (Dow 4c) | not recorded | 5c to 10c (Dow 3c) | **10c to 20c** (Dow 6.4c) | 0 to 500 | **Too costly for a taker, move on** |
| Monthly high and low barriers, Bitcoin and Ethereum | 1 event a month each | 12 a year. Settled about 44 hours after the close | 38% to 100% | 1c to 2c (2c to 3c) | not recorded | 1.2c to 2c | 2.4c to 4.0c | Bitcoin 112,000 to 131,000; Ethereum 0 to 19,000 | Cheap to trade, 12 events a year |
| Monthly barriers, Solana, XRP, Dogecoin, BNB, HYPE | 1 event a month each | 12 a year | 37% to 98% | 4c to 10c | not recorded | 3c to 7c | **5c to 13c** | under 4,000 | **Too costly, and 12 events a year: move on** |
| CPI and core CPI | 1 event each in the sample | 12 a year. Settled 10 to 73 minutes after the close | 33% to 36% | 1c to 1.5c (1c to 3c) | not recorded | 1.3c | 2.6c to 2.7c; 4.4c to 6.5c near the money | 49,000 to 77,000 | Cheap, 12 events a year |
| Daily SOFR | 2 events | One per business day. Settled about 110 minutes after the close | 31% | 1c (2c) | not recorded | 1.0c | 2.1c | 1,600 | Too few rows to say more |
| **Perps** (88 markets; 30 second samples Nov 6, hourly Nov 10 to 12) | 13,000 rows | No settlement; continuous | 98% active and two-sided in trading hours | Indices 1 basis point of price; oil 2; metals 3; crypto 7; single stocks 13 to 16 (middle half 6 to 27) | recorded, not summarised | fee not known to this desk | fee not known to this desk | 24 hour volume: indices 24 to 52 million, oil 15 to 18 million, metals 2.3 million, crypto 0.6 million, stocks 40,000 to 66,000 | The spread alone on single stock perps is 13 to 16 basis points; whether the perps list is a delayed copy is not measured |

## Flags: "too costly, move on" (each with its number)

1. **Weather daily LOW brackets**: spread 10c at the median, round trip 11.5c on an 11c price; near the money 20c.
2. **Daily and weekly forex ladders, S&P 500 and Nasdaq 100 dailies, Treasury yield dailies (the `KXUST` series)**: spread 8c to 18c, round trip 10c to 20c, volume zero to a few hundred. (The Dow daily is cheaper, 6.4c a round trip, with zero recorded volume.)
3. **Monthly barriers on the smaller coins**: round trip 5c to 13c, one event a month.
4. **NHL spread and total**: round trip 6.4c to 6.9c at the median, 10.7c to 12.5c at the 75th percentile, volume in single contracts to hundreds.
5. **Combos, as a two-way trade**: 4.5% two-sided in the one snapshot held. (As a buy-and-hold at the posted ask they are not ruled out by this; that is what Desk B's S3 measures.)

Not flagged, but note the floor: on every liquid family the cheapest round trip is about 3c at mid prices because of the fee, and a taker's order misses about a third of the time at the price seen.

## The same figures under Desk B's family names (added 17:10Z, after `FAMILY_CENSUS_NOV12.md`, commit 7523154 on `claude/idea-desk-b`)

One row per census family this desk holds data on. "RT" = round trip for a taker, median. LIST = market-list quotes only (a copy up to about 11 s old). A correction to the first cut: the `KXUST` series are daily Treasury YIELD markets, as the census says; the first cut called them auction markets on a guess from the ticker.

| Census family (Desk B's name) | Volume (recorded) | Settlement speed | Spread median | RT | Depth at the ask | Fill haircut | Data kind | Flag |
|---|---|---|---|---|---|---|---|---|
| Crypto 15 minute, hourly and daily ladders: the 15 minute series | 66,000 (Dogecoin) to 3.4 million (Bitcoin) contracts a window | result posted within about a minute in 99.7% or more | 1c | 3.0c | 72 to 3,500 | 62% to 66% at the price seen, 84% to 86% with +1c (2 s) | BOOK and tape (R6); candles cleared on Bitcoin | |
| same family: gold 15 minute | 500,000 a window | same | 1c | 3.0c | 1,500 | 63% / 84% | BOOK and tape (R6) | |
| same family: hourly Bitcoin ladder | 100,000 a strike in 55 minutes | not recorded | 1c | 4.4c near the money | 670 | 73% / 86% at 3 s, half an hour out | BOOK and tape (`book/`); Ethereum and gold ladders LIST only | |
| Non-crypto 15 minute series (not a census row yet): oil, silver, HYPE, BNB | 29,000 to 101,000 a window | within about a minute in 98% or more | 1c | 3.3c to 3.7c | 29 to 177 | 59% to 62% / 76% to 81% at 5 s | BOOK and tape (NC15), 20 hours | |
| same: forex pairs (EUR, GBP, AUD against USD; USD/JPY) | 5,700 to 7,600 a window | same | 2c | 3.1c to 4.0c | 560 (one maker) | 71% to 73% / 82% to 84% at 5 s | BOOK and tape (NC15) | one-sided a quarter to a third of the time near the close |
| same: copper, natural gas, USD/CAD | 3,800 to 23,000 a window | same | 2c to 3c | 5.0c to 5.6c | 26 to 180 | 68% to 71% / 80% to 82% at 5 s | BOOK and tape (NC15) | costly |
| US game winners (NBA, NFL, NHL moneylines) | NBA 81,000, NFL 58,000, NHL 800 a market | not recorded | NBA 2c, NFL 1c, NHL 2c | 4.8c, 4.2c, 5.5c | 660, 5,900, 360 | none possible | LIST (in-game recorder, about every 2 minutes) | NHL thin |
| US spreads and totals | NBA 26,000 to 36,000; NFL 3,900 to 30,000; NHL 6 to 950 | not recorded | NBA and NFL 1c; NHL 3c to 4c | NBA and NFL 4.5c; **NHL 6.4c to 6.9c** | 240 to 7,900 | none possible | LIST | **NHL: too costly, move on** |
| Daily city high and low temperature: HIGH | 200 a bracket | first seen settled a median 22 hours after the listed close (upper bound) | 1c; 2c near the money | 3.3c; 4.5c near the money | not recorded | none possible | LIST (three looks a day) | |
| same family: LOW | 35 a bracket | same | **10c** | **11.5c; 20c near the money** | not recorded | none possible | LIST | **too costly, move on** |
| Daily and weekend rain | held on `quote-data` (`raincal/`), not measured in this cut | | | | | | LIST | |
| Commodity daily and weekly ladders (gold, silver, copper, gas, WTI, Brent) | 0 to 2,700 a strike | 61 to 81 minutes after the close (WTI daily 8 hours; weekly about a day) | 1c to 4c | 3.3c to 5.8c; 4.4c to 7.4c near the money | not recorded | none possible | LIST | 26% to 72% of quotes are one-sided |
| Currency daily and weekly ladders | 0 to 32 a strike | dailies 2 to 48 minutes; weeklies about 23 hours | **8c to 16c** | **10.6c to 17.2c** | not recorded | none possible | LIST | **too costly, move on** |
| Index ladders: S&P 500, Nasdaq 100, Dow | zero at the median strike | 66 minutes (Dow) to 3 hours | S&P 9c, Nasdaq 15c, Dow 4c | **10.5c, 16.4c**, Dow 6.4c | not recorded | none possible | LIST | **S&P and Nasdaq: too costly, move on** |
| Rates: Treasury yields daily, SOFR daily | Treasury 100 to 510; SOFR 1,600 | Treasury 2.5 hours; SOFR 110 minutes | **Treasury 8c to 18c**; SOFR 1c | **Treasury 9.7c to 20c**; SOFR 2.1c | not recorded | none possible | LIST | **Treasury: too costly, move on.** SOFR two-sided on only 31% of quotes |
| Macro releases: CPI and core CPI (the two held) | 49,000 to 77,000 | 10 to 73 minutes after the close | 1c to 1.5c | 2.6c to 2.7c; 4.4c to 6.5c near the money | not recorded | none possible | LIST | two-sided on a third of quotes |
| Approval and generic ballot, daily (the two approval series held) | 820 to 6,600 a market | not measurable from 3 snapshots | 1c to 3c | 3.1c to 4.3c; 4.1c to 8.9c near the money | 100 to 1,570 | none possible | LIST (politics recorder, half-hourly) | |
| Truth Social post counts (weekly, the one held) | 10,800 a market | not measurable | 1c | 2.1c; 3.5c near the money | recorded | none possible | LIST | |
| Weekly shipping and executive-order count markets on the politics recorder (Hormuz, Panama, Bab el-Mandeb, Suez, orders this week; not a census row I could match) | 500 to 14,500 a market | 8 events closed in the 28 hours of result files | 1c (Suez 10c, orders 5c) | 2.5c to 3.4c (Suez 11.7c, orders 6.4c) | recorded | none possible | LIST | Suez: too costly |
| Monthly one-touch markets: Bitcoin, Ethereum | Bitcoin 112,000 to 131,000; Ethereum 0 to 19,000 | about 44 hours after the close | 1c to 2c | 2.4c to 4.0c | not recorded | none possible | LIST | 12 events a year |
| same family: Solana, XRP, Dogecoin, BNB, HYPE | under 4,000 | same | 4c to 10c | **5c to 13c** | not recorded | none possible | LIST | **too costly, move on** |
| Kalshi perpetuals | 24 hour volume: indices 24 to 52 million, oil 15 to 18 million, metals 2.3 million, crypto 0.6 million, stocks 40,000 to 66,000 | none (continuous) | 1, 2, 3, 7 and 13 to 16 basis points of price | fee not known to this desk | recorded | none possible | LIST, freshness not measured (PERPSLIST1: no evidence at n = 4); candles "assumed" | |
| Combos | 43% of quoted combos have ever traded | days (2.5 to close at the median) | 3.4c on the 4.5% that are two-sided | not measurable | 245 where posted | not measurable (5 book rows, all one-sided) | LIST plus a small BOOK part, one snapshot | exit not available: buy and hold or nothing |

Not held by this desk (no recorder, or not measured in this cut): mentions, Steam top seller (`ref/`, held but not measured), rain, the 107 sports sub-market series, tennis, soccer, esports, cricket, gas prices, hazards, power demand, Truflation, charts, earnings, altcoin ladders, long-dated politics.

## What this file cannot say

- **Events a year** beyond the 15 minute and hourly series are from a handful of days and are Desk B's column; the counts here are what the recorder saw.
- **Sizes** are not recorded for weather or the daily watchlist. **Settlement speed** is not recorded for sports or the hourly ladder and is only an upper bound for weather.
- List-quote spreads are a copy up to about 11 s old: fine for a level, useless for a seconds-level claim.
- Sports rows mix pre-game and in-play instants and include games listed days ahead.
- Combos: one snapshot. Politics: three snapshots over 14 hours. NC15: 20 hours. Mentions and any family with no recorder: nothing held.
- Not checked by the Verification Analyst.
