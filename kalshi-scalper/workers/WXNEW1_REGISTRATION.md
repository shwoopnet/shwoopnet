# WXNEW1 registration (written 2026-10-31 Central, BEFORE any hourly-temperature outcome, observation or candle was read for scoring)

Task: owner decision (Oct 30 evening), open weather markets as new research. The ledger check is in `workers/WXNEW1_LEDGER_CHECK.md`. Only one angle is both NEW and RUNNABLE: the hourly temperature "above K" ladders. Everything else is a reword of WX1 / post-peak certainty, closed by availability, or NOT_ENOUGH_DATA (see the ledger check). Two tries are registered, one per source family.

What was looked at before writing this (structure and availability only, no outcome used for any decision below): the series list; the number of settled events and their volume; one event's strikes and one-minute quote candles (spreads of 4c to 6c, sparse candles); that Iowa Environmental Mesonet (IEM) serves one-minute ASOS temperatures keylessly for ORD, MDW, NYC and LAX; the market rule text.

## The markets

`KXTEMPCHIHS` (Chicago Metro hourly "temperature above K", settled by Synoptic Data under Kalshi's Weather Index Methodology, a metro index, value to 0.01), `KXTEMPNYCH` (Central Park, "as reported by The Weather Company (for coordinates KNYC)", whole degrees) and `KXTEMPLAXH` (Los Angeles, TWC for coordinates KLAX, whole degrees). Each hour has one event with 10 strikes one degree apart ("greater" than K.99, i.e. at least K+1), open for the one hour before its close; the close time is the measurement time. Settled history is in each market's `expiration_value`.

Counterparty and mechanism (the same words for both tries): whoever leaves a stale or coarse quote on the hour's temperature ladder during the last 30 minutes. The ladder is priced from the temperature feed the settlement uses. We read the public one-minute NWS ASOS temperature (IEM), which is a delayed, partial view of the same weather. The edge exists only if the quote-makers update slower than a persistence-plus-trend forecast built from public ASOS data, or read a different source (for the TWC series the market is settled on a TWC value that can differ from the ASOS reading by rounding or timing, which the fitted offset below absorbs).

## Tries (2)

- **WXH-CHI**: `KXTEMPCHIHS`, stations ORD and MDW.
- **WXH-TWC**: `KXTEMPNYCH` (station NYC) and `KXTEMPLAXH` (station LAX) pooled, the identical rule with the offset and spread fitted on the pooled discovery window.

## Universe, fixed now from information available before entry

Every settled event of the series whose close time is before 2026-10-31 00:00 UTC (WXH-CHI: closes from 2026-09-10 15:00 UTC; WXH-TWC: closes 2026-08-23 23:00 UTC to 2026-09-10, the whole listing, the series stopped after that). An event is used only if it has at least 8 of its 10 strikes. No event, hour or strike is dropped or added on its outcome.

## Windows, fixed by date (UTC close date)

- WXH-CHI: discovery closes before 2026-10-04 00:00 UTC (about 23 days), validation 2026-10-04 to 2026-10-19 (15 days), frozen holdout 2026-10-19 00:00 UTC to 2026-10-31 00:00 UTC (the latest 12 days; read only if discovery and validation both pass).
- WXH-TWC: discovery closes before 2026-09-01 (about 9 days of each of two cities), validation 2026-09-01 to 2026-09-06, frozen holdout 2026-09-06 to 2026-09-11 (the latest 5 days; the listing is only 19 days long so 12 are impossible; read only if both earlier windows pass).

## The model (parameters fitted on discovery ONLY, then frozen)

Look time L = close time minus 30 minutes. Observation P(t) = the mean over the series' stations of each station's latest valid one-minute `tmpf` at or before t and within 10 minutes of t (at least one station, else no trade). Features: x0 = P(L), x1 = P(L) minus P(L minus 30 minutes). Fit by least squares on discovery events: (index at close) minus x0 = b + k x1. s = standard deviation of the residuals, floored at 0.7 F. mu = x0 + b + k x1. Threshold t = the market's floor strike for WXH-CHI (the value has two decimals); floor strike minus 0.49 for WXH-TWC (whole degree readings, so "above K.99" is "at least K+1", the continuity point is K+0.5). P(YES) = 1 minus Normal CDF((t - mu)/s). No other parameter is fitted or tuned. Pooled WXH-TWC uses one b, k and s for both cities.

## The rule (one parameter set, no variants)

Decision at L, using observations up to L only. Entry quote: the last one-minute candle of the market with end time at or before L + 60 seconds (the next available bar, a strictly later bar than the observation), `yes_bid` and `yes_ask` close; no candle in the market's life before that time, no trade. YES ask a must be at most 0.99, the bid b at least 0.01, and b not above a. Fee per contract at price q: ceil(7% x 10 x q x (1 - q) in cents) / 10 (the per-order rounding at C = 10), stress version times 1.2. edge_YES = p - a - fee(a); edge_NO = (1 - p) - (1 - b) - fee(1 - b). Take the side with the larger edge if it is at least 0.06 and the price paid is between 0.10 and 0.90. At most one trade per strike, several per event are allowed and are correlated, which is why the test clusters by event. Fill at the quoted ask (NO at 1 minus the bid), 10 contracts equal per-contract averages, held to settlement. Net per contract = payoff minus price minus fee.

## Bars (fixed)

Per window: PF (sum of net wins over sum of net losses per contract) at least 1.5 after fees, mean net above zero at fees x 1.2, and trade counts of at least 100 in discovery, 50 in validation, 30 in holdout. Event-clustered z (cluster = the event / close hour) of the mean net, and day-clustered z printed as information. Deflated bar: running count N about 728,677 before these two tries, 728,679 after; z bar about 5.27 on the pooled discovery plus validation mean net (event-clustered); holdout read once only if discovery AND validation each pass the PF, count and fee-stress bars, and then it must also clear PF 1.5 and the same fee stress.

Verdict words: `NOT_ENOUGH_DATA` if any window is below its trade count (reported with the date the count could be met, from the number of trades per day); `NOT_YET_FALSIFIED` only if every bar holds in discovery, validation and holdout including the deflated z; otherwise `FALSIFIED`. If a window fails the PF or the z, the holdout is NOT read.

## Numeric prediction (before any result)

FALSIFIED in both. Mean net per contract about -3c to -6c (the 4c to 6c quoted spread plus a fee near 1.75c at mid prices against a 0.7 F to 1.5 F forecast error), PF below 1 in discovery, model Brier within 10% of the market mid's Brier. For WXH-TWC the fitted offset b should be within about 0.5 F of zero and the TWC reading should equal the ASOS reading rounded in at least 85% of hours. Prior of passing every bar: under 3%. A pass would be an audit trigger first (check that no observation after L enters, and that the discovery fit never saw a later window).

## Information, not part of the verdict

Per window: events, trades, mean price paid, share of YES vs NO trades, model Brier vs market-mid Brier, fitted b, k, s, the share of hours where the TWC reading equals the rounded ASOS reading at the close. Trades per day for the NOT_ENOUGH_DATA date.

## Limits

Candle asks are quotes, not fills, and with 4c to 6c spreads and sparse volume many strikes cannot be filled at the quoted ask in size. The Chicago metro index is an average over many stations that the two airports only approximate. IEM's one-minute archive can have gaps (events with no observation are dropped, counted). WXH-TWC has only about 19 days in which both cities traded.

## Not run, closed, no try counted

See the ledger check: forecast-update lag (a reword of WX1, which found the market right, -4.70c, z -4.17); end-of-day or running-maximum bracket mispricing (post-peak certainty, dead; brackets 0.99 / 1.00); NWS versus TWC settlement mismatch on daily highs (Director Oct 29: identical on 67 days); monthly and cumulative markets (too few settled months); daily lows and rain (WX1's mechanism).
