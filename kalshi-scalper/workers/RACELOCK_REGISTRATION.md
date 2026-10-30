# RACELOCK registration (Strategy Research V2 worker RACELOCK, 2026-10-30, research only)

Written and pushed BEFORE any quote was scored and before any settled result was read for this task. Code `src/scalper/racelock.py`
(committed after this file), fetcher `src/scalper/racelock_fetch.py` (already running; it stores only bid, ask, price and volume at the
candles ending 600, 540 and 480 seconds before the close, and NOT the result). Result file `workers/RACELOCK_RESULT.md`.
Owner request: "research new kalshi 15 min prediction market strategies". Times are UTC in code, US Central (CDT, UTC-5) in words.
Nothing touches `functions/`, `index.html` or anything live; no recorder is built.

## Lane and ledger check

`KXCRYPTOLEAD15M` (Coin Race: which of BTC, ETH, SOL, XRP, HYPE has the highest return over the 15 minute window; five mutually exclusive
YES markets per event) is the series NEWH15 tests DIRECTIONALLY (BTC15M state at 10 minutes left selects a coin). This task tests only
the structure of the five books (Dutch book and over-round). It uses no BTC15M price and no direction view, so it does not share a
rule with H1 to H3 of `workers/NEWH15_REGISTRATION.md`. ARB1 to ARB5 (README) tested locks between a market and a ladder on threshold
series; none on a partitioned race. Disclosure of what was seen: the NEWH15 registration and inventory, the market listing
(tickers, event and close times), one printed listing row (it showed one `result: yes`, used by no statistic), and the quote shape of one
market's candles (a 7c spread at 25c bid, 32c ask). No sum of asks, no lock count and no outcome tally exists yet.

## Mechanism and counterparty

Five markets, exactly one resolves YES, so the five YES prices must sum to 1 and the five NO prices to 4. Buying all five YES at their
asks pays exactly 1 per set and costs the sum of the asks; buying all five NO at 1 minus each bid pays exactly 4 per set and costs
5 minus the sum of the bids. A lock needs thin books to quote all five legs inconsistently by more than the fee. The counterparty to a
lock is a maker who quotes one leg without checking the other four; the counterparty to T2 is the thin-book maker who pads one name
(brand coins, 9c spreads, median 294 contracts a market). I expect the books to be over-round (asks sum well above 1, bids below 1)
because makers pad every leg, so I expect T1 to find no fillable lock.

## Common to every test (fixed now)

- **Universe (time only):** every `KXCRYPTOLEAD15M` event from the listing with all five markets listed (BTC, ETH, SOL, XRP, HYPE) and
  closing in the window. The exactly-one-YES condition is checked once, after the registration, as a structural count (events with a
  number of YES results other than 1 are reported and dropped from the T2 outcome scoring; T1 locks are valued only on events that pass).
- **Windows by close time (UTC):** DISCOVERY 2026-08-24 00:00 to 2026-09-28 00:00; VALIDATION 2026-09-28 to 2026-10-18; HOLDOUT
  2026-10-18 to 2026-10-30 end, read ONLY if both earlier windows pass, once, after that result is committed and pushed.
- **Look:** the one minute candle ending 540 s before the close (9 minutes left). **Fill:** the NEXT candle, ending 480 s before the close.
  Quotes are the candle closes `bid_c` and `ask_c`. A leg is "quoted" if its candle exists with 0 < bid < ask < 1. One minute candles
  carry no sizes: a fill of 10 contracts a leg is modelled, not observed, and the real depth (median 294 contracts a market) is not known
  at the touch. A lock that only exists on a leg with candle volume 0 is reported separately.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order per leg; headline C = 10 a leg, C = 1 also shown; and fees x1.2 at C = 10.
- **N:** NEWH15's running count about 728,662; this task adds T1 (2 sides, counted 2), T2 (1) and the information look (1) = **about
  728,666**; one-sided Bonferroni z bar at 0.05 is **5.27**.
- **Verdicts:** FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE only.

## T1 RACE-DUTCH (2 tries: YES side and NO side)

- **T1y:** at the fill candle, if all five legs are quoted and the sum of the five YES asks times C plus the five fees is below C
  (the payout of exactly one winning leg at C contracts), the set is a lock; its size is (C - cost) in dollars, and per set of one
  contract in cents.
- **T1n:** at the fill candle, if all five legs are quoted and the cost of buying NO on all five (sum of 1 - bid_i, times C, plus the five fees
  at the NO prices) is below 4C (four NO legs pay), the set is a lock.
- **Prediction (stated first):** zero fillable locks in discovery and in validation on both sides; median sum of asks 1.15 to 1.40,
  median sum of bids 0.65 to 0.90; at most 1 in 200 windows has a candle with a missing leg quote that I count as a lock by error.
- **Kill:** zero fillable locks after fees at C = 10 in discovery (n windows with all five quoted at least 1,000) is FALSIFIED for that side.
  NOT_ENOUGH_DATA if fewer than 1,000 discovery windows have all five legs quoted at the fill candle. Any lock found is NOT_YET_FALSIFIED
  only if it exists in validation too at fees x1.2 and is fillable (volume above 0 on every leg's fill candle); it would still be a
  modelled fill and earn only a forward quote check, not a trade.

## T2 RACE-OVERROUND-SIDE (1 try; scored only if T1 shows no locks)

- **Rule:** at the look candle (9 minutes left), with all five legs quoted: for each leg, mid_i = (bid_i + ask_i) / 2 and fair share
  s_i = mid_i / sum(mid); pad_i = ask_i - s_i. Pick the leg with the largest pad_i (ties: the larger ask, then alphabetical). Buy NO
  on it at the NEXT candle's price 1 - bid_i (that candle must quote it); fill between 0.15 and 0.85 inclusive, else "no fill" (counted).
  Hold to settlement; nothing is sold. 10 contracts, modelled.
- **Prediction (stated first):** NO on the padded name wins more often than its price implies by at least 3 points in discovery
  (padding means the ask overstates the YES chance). My honest expectation is weaker: the pad is mostly spread, which the buyer of NO
  at 1 minus the bid also pays on the other side, so PF 0.85 to 1.05 at C = 10, FALSIFIED.
- **Bar:** PF at C = 10 at least 1.5 in EACH of the three windows after fees, positive net at fees x1.2, at least 100 / 50 / 30 trades,
  a pooled day-clustered z at least 5.27, a named counterparty (the thin-book maker who pads a name).
- **Kill:** discovery PF under 1.0 with n at least 100 is FALSIFIED; validation PF under 1.0 with n at least 50 is FALSIFIED;
  fewer trades than the minimum in a window is NOT_ENOUGH_DATA. Zero-volume reported both ways (PF with all trades and PF without trades
  whose fill candle has volume 0).

## Information look (counted, not a rule)

Median and quartiles of the sum of YES asks and of YES bids at the look and fill candles, median spread per leg, the share of candles
with all five legs quoted, the share of events with each number of missing legs, and for the counted locks the distribution of
(sum of asks - 1). Reported per window.

## Amendment A1 (written after T1 was scored, before any settled result was read)

T1 (no result read) found a few tiny locks, not zero: at the fill candle with all five legs quoted, discovery 2,278 windows had 5 YES
locks (3 with volume above 0 on every leg) and 4 NO locks (2 with volume); validation 1,668 windows had 1 YES lock and 0 NO locks;
holdout was not looked at for a verdict (counts only, 0 locks). The largest lock is $0.37 on 10 sets (3.7 cents a set). The T2 gate said
"only if T1 shows locks do not exist". Strictly the locks exist, so I record that T2 is run on a judgement and not on the letter: the locks
are 1 window in about 700, worth cents, and they cannot carry a trade, so the over-round side test is the only question left. The holdout
is not printed by `racelock.py t2` unless `--holdout` is passed, and will be passed only if both earlier windows pass. N is unchanged.
