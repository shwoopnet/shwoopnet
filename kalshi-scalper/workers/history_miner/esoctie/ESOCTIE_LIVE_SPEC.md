# ESOCTIE live spec sheet, for the probation-seat ranking (History Miner, Nov 12, 2026, 20:10Z)

Written for the Head of R&D's ranking under the owner's "Probation seats, 3 contracts" decision. It describes how the REGISTERED rule would be placed live. It changes nothing in the registration or the frozen scorers, and probation fills are never research evidence. ESOCTIE leaves the pool if its development read is under 1.0. Research and design only; no live figure. [research]

## 1. The order

- **Market:** KXESOCCERGAME only (e-soccer, about 8 to 15 minute games, three markets an event: two players' clubs and `-TIE`).
- **Side:** YES on the event's `-TIE` market. Never a team contract, never NO.
- **Decision moment:** S = the date and four-digit clock time at the front of the event key (for example `26NOV091943` is Nov 9, 19:43 US Eastern), converted with US daylight-saving rules. The event is eligible only if the Tie market opened 10 to 240 minutes before S. Decide at S minus 60 seconds.
- **Quotes used:** the Tie's best bid and ask and both team contracts' bids and asks. All three must be two-sided (0 < bid < ask < 1). Research uses the 1 minute candle close at S minus 60 s, stepping back a minute at a time to S minus 10 min if not two-sided. **Live equivalent:** poll the three books once a minute from S minus 10 min and act at S minus 60 s on the latest minute in which all three were two-sided; if none, no order.
- **Trigger:** b minus the Tie's ask is 10c or more, AND the Tie's spread is 4c or less. b is defined in section 2.
- **Price band:** none beyond the trigger. The registration closes the card if the median Tie ask is under 15c (cheap tail), so the trigger cannot fire on a cheap tail unless b is also low.
- **Limit:** the Tie's ask plus 1c, immediate-or-cancel. **Size:** 3 contracts (research is 1; the fee is rounded up on the 3-contract order, about 0.07 x 3 x p x (1 minus p), which is slightly cheaper per contract than the 1-contract rounding used in research).
- **Exit:** hold to settlement (about 12 minutes after S, settles about 4 minutes after that). No early sell.
- **One order per event.** Never a second order on the same event.

## 2. The state the bot must hold: the walk-forward base rate b

- **Definition (registered):** for the bet's strength bucket, b = (number of earlier ELIGIBLE events in that bucket whose Tie settled YES) / (number of earlier eligible events in that bucket with a yes or no result). "Earlier" = the event's market closed at least 300 seconds before this bet's decision moment. An eligible event is one that passed the open-time guard and had all three contracts two-sided at its own decision moment.
- **Bucket:** f = the larger of the two team contracts' mids at that event's OWN decision moment; edges 0, 0.45, 0.55, 0.65, 0.75, 1.0. A bucket needs 300 earlier events; under that, no order.
- **History it starts from:** every eligible event from 2026-09-12 on. That means b needs, for every past event, its decision-moment f (from quotes, not in the settled lists) AND its Tie result (in the lists).
- **Is a daily refreshed number a faithful substitute? Not quite, and it must say so.** A table refreshed once a day lags the registered value by up to a day of events. At about 18,000 earlier events by mid-November, a day adds about 450, so b moves by a few tenths of a point at most; but it is a different number, so a daily table is a VERSION, not the registered rule. **More important: a keyless job reading only public settled LISTS cannot build b at all,** because the bucket needs each past event's pre-game team mids, which are not in a settled list. The faithful build is: seed the per-bucket counts once from the research candle pull (Sep 12 to the latest development close), then have the live bot itself record f at every decision moment it evaluates (order or not) and add each event's result once its close plus 300 s has passed. A small job that reads settled lists can supply the results; the bot must supply f.
- **When the state is missing** (no seed, a bucket under 300, a gap in the bot's own record, a Tie result not yet admitted): no order.

## 3. Expected bets a day

Not yet counted: `ESOCTIE_LISTS` had NOT landed on `kalshi-pull-data` at 20:05Z. The census (Nov 10, a lower bound) shows about 450 events a day. My prediction, registered before data: the 10c and 4c trigger fires on under 3% of eligible events, so under about 13 bets a day, and about 75% that the card closes as "efficient" before any bet is scored. The real figure comes from the measurement.

## 4. Evidence

None yet. Probability it reaches the research bar: 1 to 2%. Probability the development read is at or above 1.0: my guess about 25% (most likely outcome: closed at the measurement as "efficient"). Timeline: lists land (pending Main's run), then the candle job (estimated 1,000 to 2,000 requests, one or two runs) on the Head's go, then the measurement and development read within the hour of the candles. If the lists run tonight, a read Friday is possible.

## 5. What is hard to build live by Sunday

1. **Shard 0.** Every KXESOCCERGAME market in the census listing has exchange_index 0 (1,350 of 1,350; the series object agrees). The bot's live markets are on shard 2, and earlier notes say shard 0 holds little or no money. Money has to be moved by hand (Kalshi, Transfers) before any order fills; the bot will log `shard_short` and send nothing otherwise.
2. **Not a 15 minute series.** The live engines (L1 and the second slot) are built around 15 minute tickers (`SLOT_TICKER_RE`, `SLOT_SERIES_ALLOWED`, entry spans in seconds before a 15 minute close). E-soccer needs the non-15-minute long-hold order path Main estimated at 2 to 3 days, plus a key-clock parser with US daylight-saving rules.
3. **The state.** The seed (section 2) needs the research candle pull to have run, and the bot must keep its own per-event record of f; a list-only job cannot.
4. **Polling load.** About 450 events a day, three markets each, read once a minute for the last 10 minutes before each start: about 13,500 market reads a day on top of today's.
5. **Quote source.** Research prices from minute-end candles (freshness measured on Bitcoin 15 minute only); live would act on the book. The 1c slip and the fill haircut table apply; live fills at the ask seen are about 59% to 73% on other series.

## 6. exchange_index

0 for every KXESOCCERGAME market in the Nov 10 listing (1,350 markets) and on the series object.
