# How to price a paper trade (one page for card writers, 2026-11-12)

Everything here is measured on recorded public data by the Forensics Desk; the file behind each number is named at the end. No live account figure is used. Where a number rests on one series or a few days, section 6 says so. If your card's market is not covered, say "assumed, not measured" on the card.

## 1. Which price sources are current

| Source | Status | Use it for |
|---|---|---|
| Order book reads (`book15r6/`, `nc15/`, the hourly Bitcoin ladder `book/`, the book part of `combo-data`) | **Current** | Signals and fills at seconds scale |
| Trade tapes (exchange time stamps) | **Current** | What actually traded, and when |
| 1 minute candles, bid and ask close | **Current on `KXBTC15M`** (within about 1 s and 1c of the book at the minute's end). Any other series: assumed, not measured | One price per minute. Weaker in the last minute before a close |
| **Any market LIST quote** (`quotes/` and its `ladder.csv`, and by the same endpoint the in-game, daily, weather, politics and combo quote files) | **A delayed copy**: refreshed about every 11 s, so 0 to 11 s old (5.5 on average), about 7 s behind the tape. Markets in one response have different ages | Price LEVELS in slow markets only. Never a seconds-level signal, a lag, a lock or a parity check |
| The perps list, perp candles, the bot's own single-market read | **Not known** | Label "assumed" (the perps list is being measured: PERPSLIST1) |

Rule: a result priced from a list quote at seconds scale is not a tradable figure. Two list quotes read in the same second are not simultaneous.

## 2. The fee

Taker fee per contract, per side traded: **0.07 x price x (1 - price)**, rounded up to the cent on the whole order. Settlement is free. A maker fee of zero is an assumption in our work, not a measurement, and it is wrong for some families: Desk B's Nov 10 listing shows 32 non-sports series that charge maker fees (CPI, payrolls, Fed, GDP and similar) and 14 with no fee; the fee fields for sports and weather were cut off in that listing and are not known. Check the family's fee class (`FAMILY_TABLE.md` on `claude/idea-desk-b`) before using this table.

| Price | 5c or 95c | 10c or 90c | 20c or 80c | 30c or 70c | 40c or 60c | 50c |
|---|---|---|---|---|---|---|
| Fee per contract | 0.33c | 0.63c | 1.12c | 1.47c | 1.68c | 1.75c |

- At 1 contract the rounding makes the fee 1c below about 17c or above about 83c, otherwise 2c. Score at 10 contracts or with the unrounded fee, and say which.
- **Cost floor on a liquid market** (1c spread): buy and hold to settlement costs about 1.5c against the mid at mid prices; in and out costs about 3c. The fee is two thirds of it.

## 3. The taker fill haircut

A taker order sent at the price you saw does not always fill, because the price moves in the seconds before it arrives. Share of 1 contract immediate-or-cancel buys that fill, by how long the order takes to arrive and how far above the price seen the limit is set:

| Market and side | Limit | about 2 s | 2 to 4 s | 6 s | 10 s |
|---|---|---|---|---|---|
| Bitcoin 15 minute, cheap side 5c to 30c, 3 to 2 minutes before the close | at the ask seen | 67% | 66% | 66% | 66% |
| | +1c | 84% | 82% | 76% | 73% |
| | +2c | 91% | 88% | 82% | 78% |
| Gold 15 minute, favourite 88c to 97c, about 6 minutes before the close | at the ask seen | 59% | 56% | 49% | 46% |
| | +1c | 94% | 92% | 83% | 73% |
| Every 15 minute series measured (five crypto and gold; eleven non-crypto), either side, any price, 6 minutes before | at the ask seen | 62% to 66% (non-crypto at 5 s: 59% to 73%) | | 56% to 58% (non-crypto at 10 s: 55% to 66%) | |
| | +1c | 84% to 86% (non-crypto at 5 s: 76% to 84%) | | 75% to 77% (non-crypto at 10 s: 69% to 78%) | |
| Hourly Bitcoin ladder, strikes priced 30c to 70c, 30 minutes before | at the ask seen | | 73% (3 s) | 64% | |
| | +1c | | 86% (3 s) | 77% | |

**How to apply it.**
1. **If an order book is recorded for your market:** replay each paper trade on the book. Take the first book poll at least 2 s after the signal (and, separately, 6 s), set the limit your rule really uses, walk the book's levels up to that limit, and count a miss as no trade. Report the 2 s and the 6 s line.
2. **If no book is recorded** (candles or list quotes only): cut the trade COUNT, not the price. With a limit 1c above the price seen, drop 15% of trades for a 2 s arrival and 23% for 6 s, and add 1c to the price paid on the rest as the worst case. With the limit at the price seen, drop a third. For a slow, realistic arrival (5 to 10 s) drop about 34% at the price seen, about 25% with +1c, about 20% with +2c.
3. **The missed trades are not random.** A limit keeps the signals the market moved against and loses the ones it moved with: on the Bitcoin cheap side (+1c limit, 2 s) the side's mid was 5.4c higher 30 s later for the orders that MISSED and 1.0c lower for the ones that filled. Whether the missed ones also win more at settlement was not measured. So dropping trades at random may still be generous; say so on the card.
4. Size is not the problem at small size: 1 contract and 10 (or 15 on gold) fill at the same rate, and on gold the size shown at the best price covers 15 contracts at 96% of instants. A "would fill" flag built from size at the touch tells you almost nothing.

A resting (maker) order is a different trade with its own fill and selection questions; nothing on this page prices it.

## 4. What a paper record can be trusted for

- **Price: yes, to about 0.2c a contract (measured on the gold favourite).** A filled taker order pays the price seen or slightly less, and that roughly cancels the weaker signals a limit keeps. On the Bitcoin cheap side the fills are also cheaper than the price seen; the net was not measured there because no outcome was read.
- **Count: no.** A third of the trades at the price seen, or a sixth to a quarter with a 1c higher limit, would not have happened, and they lean toward the winners.
- **Timing: only to the grain of the source.** A candle gives one instant a minute; a list quote is up to 11 s old.
- So quote a paper result as: profit factor and n AFTER the haircut, the limit and delay assumed, and the source of the price.

## 4b. Two rules for every scorer (ruled by the Head of R&D, 2026-11-12, after the scorer audit)

1. **No cut over the whole sample.** No threshold, cut or universe filter may be computed over the whole development sample and then applied to earlier bets, even when it reads no outcome (a tercile of a signal, a "which titles are in" kill line). Either it is a constant written in the registration, or it is walk-forward from earlier data only. Where a registered step order does select on development, the development figure is labelled "selected on development": it can falsify, it cannot support. Only a frozen held-out read can support.
2. **No haircut from a later value.** A "ran away" or "missed" haircut is never built from a later candle or from any value measured after the decision: near a close, the side whose price rises next is the side that is winning, so such a filter removes rows by the outcome. Use the book replay where a book exists (section 3, rule 1). Where none exists, use a RANDOM drop at the measured miss rate, with the stated caveat that real misses lean toward winners.

The same audit's general test, for anyone writing a scorer: a time or value known only after the bet (a later close or settlement time, a later candle, a sibling market's result before its own close, a result field) must not decide the signal, the price, or WHICH bets exist. A guard that drops a record by how long something lasted afterwards is such a value.

## 5. Five families where the cost already rules out a taker card

| Family | Measured round trip | Why |
|---|---|---|
| Weather, daily LOW brackets | 11.5c on an 11c price; 20c near the money | Spread 10c at the median |
| Daily and weekly forex ladders, S&P 500 and Nasdaq 100 dailies, Treasury yield dailies (the `KXUST` series) | 10c to 20c | Spread 8c to 18c, volume zero to a few hundred |
| Monthly high and low barriers on Solana, XRP, Dogecoin, BNB, HYPE | 5c to 13c | And only 12 events a year |
| NHL spread and total | 6.4c to 6.9c at the median, 10.7c to 12.5c at the 75th percentile | Thin: volume from single contracts to hundreds |
| Combos, as a trade you can exit | Not measurable: 4.5% of quoted combos had both sides | Buy and hold at the posted ask, or nothing |

For comparison, the liquid families cost about 3c (15 minute series), 4.4c (hourly Bitcoin ladder near the money), 4.2c to 4.8c (NBA and NFL lines), 3.3c to 4.5c (weather daily HIGH), 6.3c (politics markets priced 20c to 80c).

## 6. What each number rests on

| Number | Series | Sample | File |
|---|---|---|---|
| List quote is an 11 s copy | Bitcoin 15 minute quotes; hourly Bitcoin and Ethereum ladder quotes | 72,012 polls over 6 days; ladder 10 files over 2 days | `QUOTEVSBOOK1_RESULT.md`, `TAPECLOCK1_RESULT.md`, `results/LADDERSTATE1.json` |
| Candle close is the book | Bitcoin 15 minute only | 407 windows, 6 days | `CANDLEVSBOOK1_RESULT.md` |
| Bitcoin cheap-side haircut | Bitcoin 15 minute | 9,527 instants in 544 windows, Oct 29 to Nov 11 | `FILLHAIRCUT1_RESULT.md` |
| Gold favourite haircut; price to 0.2c; size at the touch | Gold 15 minute | 6,240 instants in 292 windows, Oct 29 to Nov 11 | `GOLDHAIRCUT1_RESULT.md` |
| All-series haircut, spreads, costs, the five flags | 16 fifteen minute series, the hourly Bitcoin ladder, sports, politics, weather, daily markets, combos | R6: 2 weeks. Non-crypto: 20 hours of one weekday. Ladder: 3 days. Sports: 5 days. Politics: 3 snapshots. Weather and daily: about a week. Combos: 1 snapshot | `FAMILY_COSTS_NOV12.md` |
| Which files are which kind of source | all recorders | read from the recorder code | `DATA_SOURCES_FRESHNESS.md` |

**Limits.** All of it is public, unauthenticated data from two weeks of November 2026; fill rates can change with volatility (the last three days measured were 4 to 7 points worse than the first eleven). The haircut is measured at 1 to 15 contracts and says nothing about large orders. Book polls are 2 s apart (5 s on the non-crypto series, 3 s on the ladder), so "2 s" means the first poll at least 2 s later. None of it has been checked by the Verification Analyst except the list-quote finding.
