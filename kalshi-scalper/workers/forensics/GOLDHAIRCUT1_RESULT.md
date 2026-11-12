# GOLDHAIRCUT1 result: how far to trust a "fill at the touch" paper record of the gold favourite rule (2026-11-12)

Registration: `GOLDHAIRCUT1_REGISTRATION.md` (commit 7f45021, before anything was computed). Script `goldhaircut1.py`; raw output `results/GOLDHAIRCUT1_A.json` (closes Oct 29 to Nov 8), `_B.json` (Nov 9 to 11), `_AB.json` (both). A measurement: no rule scored, no settlement result loaded, zero tries. Public R6 books and tape, zero Kalshi requests, nothing about the live account.

**Sample.** `KXGOLD15M`, the span 400 to 330 seconds before the close, the side whose ask is 88c to 97c. Both periods: 623 windows used, **292 windows with a decision instant, 6,240 instants, 33,572 taker trades**. Buckets have 167 to 196 windows each (above the 100 line). Period B alone has 98 windows. Intervals 95%, resampling whole windows. Delay columns: "1 s" is the next poll (2.0 s), "2 s" is 2 to 4 s, "5 s" is 6.0 s, "10 s" is 10.06 s.

## The answer first

1. **Trust the paper record's PRICE to within about 0.2c a contract. Do not trust its COUNT.**
2. **Count.** A paper record takes every signal. A real immediate-or-cancel buy does not:

| Limit | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|
| At the ask seen: share filled in full | 59.2% (57.6 to 60.7) | 55.5% | 48.6% (46.6 to 50.7) | 45.6% (43.2 to 47.9) |
| At the ask seen + 1c | 94.1% (93.4 to 94.8) | 91.8% | 83.2% (81.7 to 84.7) | 73.4% (71.3 to 75.5) |

   The live rule's limit is the ask it reads, rounded UP to a whole cent (`functions/kalshiLiveLib.js`), and this book quotes in tenths of a cent above about 90c, so the real limit sits between the two rows. A paper record built from a quote taken at the minute, for a rule that would send several seconds later, should expect roughly half to five sixths of its signals to fill.
3. **Price.** The fills are cheaper than the ask seen (a limit only fills when the ask stayed or fell): -0.4c, -0.6c, -1.0c, -1.6c at the ask seen for the four delays; -0.1c, -0.2c, -0.4c, -0.8c with +1c. A +1c limit is a ceiling, not a price: it does not cost a cent.
4. **Which signals fill.** A limit keeps the favourites that were weakening and loses the ones that were strengthening. Mid of the bought side 30 seconds after the decision, 15 contracts:

| Limit, delay | Filled | Missed |
|---|---|---|
| Ask seen, 5 s | -1.25c (-1.74 to -0.82) | +1.17c (+0.94 to +1.39) |
| Ask seen, 10 s | -1.82c (-2.35 to -1.32) | +1.51c (+1.31 to +1.69) |
| +1c, 5 s | -0.43c (-0.81 to -0.10) | +2.11c (+1.80 to +2.40) |
| +1c, 10 s | -0.87c (-1.26 to -0.51) | +2.36c (+2.13 to +2.57) |

5. **Those two nearly cancel.** The filled set is worth less half a minute later, but it was bought for less by almost the same amount. Net, against a paper fill at the ask seen: about -0.2c a contract for a limit at the ask seen at 5 to 10 seconds, -0.05c to -0.1c with +1c, 0.0c to -0.1c at 2 seconds. On a rule that wins a few cents and loses most of the stake, 0.2c is about 0.03 of profit factor at these prices (arithmetic at a 93c ask, not a measurement of the rule).
6. **Size is not the test.** The size shown at the touch covers 15 contracts at 95.6% of instants, and 1 and 15 contracts fill the same to within 0.9 points in every cell. A paper record's "would fill" flag that checks touch size passes almost always and says almost nothing about whether a limit order fills. The constraint is the price moving, not the size.
7. **What this cannot say.** Whether the missed favourites WIN more at settlement (no outcome loaded; the half-minute mid is the only evidence, and it says the missed ones were priced about 1c to 2c higher soon after). Anything under 2 seconds. The effect of our own order.

**So, for a paper record used to bring gold back:** count a signal as a trade only if a limit order would have filled at the first quote at least 2 seconds (and, as the live-like line, 6 seconds) after the decision, with the limit the rule would really send; price it at that quote, not at the touch seen. If the record only has the touch seen: keep its price, cut its trade count and its dollars by the miss rate above (about half at the ask seen, about a sixth to a quarter with +1c, at 5 to 10 seconds), and take about 0.2c a contract off as the selection cost.

## By price bucket (both periods)

Share filled in full, 1 contract; then price paid against the ask seen on the filled.

| Bucket (instants / windows) | Limit | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|---|
| 88c to 91c (1,876 / 196) | ask seen | 66.6% | 63.1% | 54.6% | 49.8% |
| | +1c | 90.7% | 87.9% | 77.8% | 67.2% |
| 91c to 94c (1,882 / 174) | ask seen | 53.8% | 50.6% | 42.8% | 42.0% |
| | +1c | 92.6% | 89.7% | 78.3% | 67.9% |
| 94c to 97c (2,482 / 167) | ask seen | 57.6% | 53.5% | 48.5% | 45.1% |
| | +1c | 97.8% | 96.3% | 91.0% | 82.2% |

| Bucket | Limit | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|---|
| 88c to 91c | ask seen / +1c | -0.6c / -0.2c | -0.8c / -0.4c | -1.4c / -0.7c | -2.2c / -1.5c |
| 91c to 94c | ask seen / +1c | -0.5c / -0.1c | -0.7c / -0.2c | -1.2c / -0.4c | -1.8c / -0.9c |
| 94c to 97c | ask seen / +1c | -0.3c / -0.0c | -0.4c / -0.1c | -0.7c / -0.1c | -0.9c / -0.3c |

The spread is 0.8c in the 88c to 91c bucket and 0.2c above 91c (tenth-of-a-cent ticks), which is why a limit at the exact ask seen misses so often there: the ask moves by a few tenths.

## Part 1: is the ask still there (both periods, all buckets)

| | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|
| Still at or below the ask seen | 59.2% | 55.5% | 48.6% | 45.6% |
| Within +1c | 94.1% | 91.8% | 83.2% | 73.4% |
| Mean move of the ask | 0.0c | 0.0c | 0.0c | 0.0c |
| Move when gone, mean | +0.6c | +0.7c | +1.0c | +1.3c |
| Move, 75th / 90th / 95th percentile | 0.3 / 1.0 / 1.2c | 0.4 / 1.0 / 1.4c | 0.8 / 1.5 / 2.0c | 1.1 / 2.0 / 2.6c |

The ask is as likely to have improved as worsened; when it has gone it has gone by about a cent, not by several as on Bitcoin.

## Part 2: the tape (both periods)

Takers who bought the favourite, against the ask of the last poll 2 to 4 seconds earlier: +0.08c per trade (-0.02 to +0.16), +0.06c per contract; 51% paid more, 34% less, 14.7% more than 1c more; 90th and 95th percentile +1.4c and +2.0c. Slightly less for trades of 20 contracts or more (+0.01c) than for small ones (+0.11c to +0.13c).

Share of the displayed size that trades: within 2 seconds the median instant sees 3% of the size shown at or below the ask seen bought, and the whole of it at 10% of instants; within 10 seconds, 30% and 27%. Gold's quote changes because makers re-price it, not because takers consume it (on Bitcoin the whole displayed size trades within 2 seconds at half of instants).

## The two periods

| Limit | Period | 1 s | 2 s | 5 s | 10 s |
|---|---|---|---|---|---|
| ask seen | A (Oct 29 to Nov 8, 194 windows) | 58.2% | 54.8% | 48.2% | 44.8% |
| | B (Nov 9 to 11, 98 windows) | 61.0% | 56.9% | 49.5% | 47.0% |
| +1c | A | 93.4% | 90.9% | 81.6% | 71.7% |
| | B | 95.4% | 93.6% | 86.2% | 76.6% |

The two periods agree to within 2 to 5 points; unlike Bitcoin, the later days were not worse.

## Which delay applies to what

- The LIVE rule reads the market again just before it sends, so the quote it "saw" is about 1 to 2 seconds old at arrival: the 1 s and 2 s columns, with a limit between "ask seen" and "+1c" (the ask rounded up to the cent). That puts the expected live fill share between about 55% and 94%; the live no-fill share itself is a live figure and is not quoted here (ask Main).
- A PAPER record built from the quote at the minute (a shadow row or a candle close) describes an order that would arrive several seconds later: the 5 s and 10 s columns.

## Caveats

Fourteen days with weekends closed and recorder gaps; one regime. No outcome loaded, so the selection cost is measured only as a half-minute mid. The figure "0.2c is about 0.03 of profit factor" is arithmetic at one price, shown for scale. Not checked by the Verification Analyst.
