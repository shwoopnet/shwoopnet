# NEWH15 registration (Strategy Research V2 worker NEWH15, 2026-10-30, research only)

Written and pushed BEFORE any NEWH15 rule was joined to a fill quote or to any race outcome. Inventory: `workers/NEWH15_INVENTORY.md`.
Code `src/scalper/newh15.py` (committed after this file); result `workers/NEWH15_RESULT.md`. The owner asked directly: "research
new kalshi 15 min prediction market strategies". Times are UTC in code, US Central (CDT, UTC-5) in words. Nothing touches `functions/`,
`index.html` or anything live; no recorder is started.

## What was looked at before this was written (disclosure)

Series list and market listings (counts, first and last close, `expiration_value` against `floor_strike` for tie counts, volumes), the
rules text and settlement source of each series, the median spread at 10 minutes left from the candle files already on disk (alts2,
alts3, alts4, fresh, rep, five, l1b), one race event's candles (5 markets, two candles each, to learn the quote shape: a 9c spread
and a 294-contract median volume), and the result column of the 158 rate windows and 44 AUD/USD windows per hour of day (rates and
AUD/USD only, no strategy, no fill). **No race result was read by any statistic**; the single race row printed shows one winner label
(a label in the first listing row; no statistic used it). No BTC15M quote was joined to a race market before this file.

## Ledger check (what this is NOT)

- **The family is new.** `KXCRYPTOLEAD15M` ("Coin Race 15 minutes": which of BTC, ETH, SOL, XRP, HYPE has the highest return over the
  window; five mutually exclusive YES markets per event) appears in the ledger once, FLAT-R (README, "Left out on purpose: ...
  comparison markets, not a strike"), and in no test. 6,343 settled events (31,715 markets) from 2026-08-24; median 294 contracts a
  market (thin).
- **Not L1, not an exit/size/filter/hour/throttle variant, not cheap-side-late, not a round trip.** Entry is at 9 minutes left on a
  one-in-five market, held to settlement; the BTC15M quote is used only as a STATE read (market direction), never traded.
- **Not a lead-lag trade between two books of the same asset** (NEWH12 XLAG, LAG2): the other book is a different contract on a
  different question (a ranking, not a threshold). **Not ARB1** (zero locks; I register no lock). **Not BTC1 CONT/FADE or S06/S07**
  (those use the prior window's result; this uses the same window's BTC15M price at 10 minutes left).
- Cross-asset market-wide features inside GEN1 (README, "market-wide move") fed a favourite or candle rule on threshold markets on 18
  series; none touched the race.

## Mechanism and counterparty

The race pays the coin with the highest return. All five coins load on one crypto factor; their loadings differ (HYPE and SOL high,
BTC lowest). When the factor rises, the winner is drawn from the HIGH-beta coins; when it falls, the "highest" return is the LEAST
negative one, which comes from the LOW-beta coins. The identity of the likely leader therefore flips with the direction of the
market, and the direction is public and priced in the liquid BTC15M book (median 2.5 million contracts a market) from minute 5.
The five race books are thin (median 294 contracts, spreads 9c in the one event seen) and are quoted around one-in-five. The
counterparty is whoever quotes or hits the race books at 9 minutes left without conditioning on the BTC15M price: thin-book makers
who update slowly and takers buying brand-name coins. They lose when direction has already been resolved by the liquid book and the race
book still prices the coin at a direction-free share.

## Common to every rule (fixed now)

- **Windows by close time (UTC):** DISCOVERY 2026-08-24 00:00 to 2026-09-28 00:00 (35 days); VALIDATION 2026-09-28 to 2026-10-18
  (20 days); HOLDOUT 2026-10-18 to 2026-10-30 end (the latest 12 days; read ONLY if a rule passed discovery and validation, once, after that
  result is committed and pushed).
- **Universe (by time only):** every settled `KXCRYPTOLEAD15M` event with all five markets listed and exactly one YES result, matched to the
  `KXBTC15M` market with the same close time.
- **State read (signal candle):** the `KXBTC15M` candle ending 600 s before the close (10 minutes left). Needs bid_c and ask_c quoted,
  0 < bid < ask < 1, ask minus bid at most 0.05; m = (bid_c + ask_c) / 2. UP means m >= 0.70, DOWN means m <= 0.30. Thresholds fixed now,
  chosen as round values, not from any outcome.
- **Fill:** the race market's candle ending 540 s before the close (the NEXT candle after the signal), at that candle's ask_c for a YES buy
  and at 1 minus bid_c for a NO buy; both quotes must exist; fill price between 0.15 and 0.85 inclusive, else "no fill" (counted).
  Held to settlement; nothing is sold. One-minute candles carry no sizes, so a fill of 10 contracts is modelled, not observed.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order. Headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose fill candle (race market) had volume 0.
- **Bar (each rule):** PF at C = 10 at least 1.5 in EACH of the three windows, positive net at fees x1.2 in each, at least 100 / 50 / 30
  trades (discovery / validation / holdout), a named counterparty, and a pooled day-clustered z at least the deflated bar.
- **N:** running count after NEWH16 about 728,658, plus 3 tries here and 1 information look = **about 728,662**; one-sided Bonferroni z
  bar at 0.05 **5.27**.
- **Verdicts:** FALSIFIED if discovery PF (C = 10) is under 1.0 with n >= 100, or validation PF under 1.0 with n >= 50; NOT_ENOUGH_DATA
  if n is under the minimum in a window; NOT_YET_FALSIFIED only if every bar above holds; NOT_RUNNABLE if the candles cannot be built.

## H1 RACE-UP-HYPE (1 try): in an up market buy the high-beta leader

- **Rule:** state UP; buy YES on the HYPE race market.
- **Prediction:** the market underprices HYPE as leader in up moves: win rate at least 4 points above the fill price in discovery. My
  honest expectation is weaker: PF 0.85 to 1.10 at C = 10, FALSIFIED, because 9c spreads and a 7% fee on a 25c to 35c ticket eat 4 points.
- **Kill:** as above.

## H2 RACE-DOWN-BTC (1 try): in a down market buy the low-beta leader

- **Rule:** state DOWN; buy YES on the BTC race market.
- **Prediction:** BTC is the most frequent leader in down windows; win rate at least 4 points above the fill price. Expected PF 0.85 to 1.10.

## H3 RACE-UP-BTCNO (1 try): in an up market sell the low-beta coin

- **Rule:** state UP; buy NO on the BTC race market (fill = 1 minus bid; usually 0.80 to 0.85, so most tickets will be "no fill" above 0.85,
  which is counted and part of the verdict).
- **Prediction:** the NO pays more often than its 0.80 to 0.85 price implies (BTC is the leader well under 15% of up windows). Expected
  PF 0.9 to 1.1 on the fills that exist; most signals fall outside the 0.85 cap.

## Information only (no try, no claim)

Discovery window only, reported with the result: the share of events each coin led, split by UP, DOWN and MIDDLE state (the mechanism check),
and the median spread of the race books at the fill candle. Rules not built, with the reason, are in the inventory file.

## Data

Candles for all race markets and for `KXBTC15M` through Kalshi's public batch candlestick endpoint into `data/newh15/candles.sqlite`
(ignored; never committed). Coverage gaps (a market with no candle at the signal or fill minute) are counted in the funnel.
