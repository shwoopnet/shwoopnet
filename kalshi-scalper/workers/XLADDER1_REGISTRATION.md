# XLADDER1 registration (Strategy Research V2, written 2026-11-03 BEFORE any Kalshi bracket candle was downloaded and before any price, result flag or PnL of any XLADDER1 pair was read; research only)

Brief: the same underlying settling at the same instant appears in more than one Kalshi ladder; where two series price the same event the prices must agree, and a gap above fee plus spread is a lock or a cheap-side buy held to settlement. No outside price is used.

## Duplicate check (done first)
Read README ARB1 to ARB5, RULES1/FEE1, NEWH13 (GLOCKH, GLADX-L), LADLONG1, XMET1, PUB20 P08, SPORTCONS1, WX3 and the 10-23 consistency scan, IDXFUT1, INX1, SETTLE1, USWEEP1. Findings:
- **Bitcoin and Ethereum:** the daily "above K at 5pm ET" and the hourly "above K" ladders are ONE series (`KXBTCD`, `KXETHD`, different events), so there is no cross-series pair. The range series `KXBTC`/`KXETH` against `KXBTCD`/`KXETHD` at the same close is ARB4 (live scans, 12 scans, 0 persistent, best +0.10c). **DUPLICATE, not re-run.**
- **Gold:** 15 minute against the hourly strike is NEWH13 GLOCKH/GLADX-L (NOT_ENOUGH_DATA); KXGOLDD/KXGOLDH/KXGOLDW candles on file start 900 s before the close and are mostly zero volume (NEWH9, NEWH13 notes). **Not run, not a try.**
- **S&P 500 and Nasdaq 100 4 pm ET:** `KXINX`/`KXNASDAQ100` (daily range: 28 brackets of 25 or 100 points plus a "less" and a "greater" tail, 30 markets an event) against `KXINXU`/`KXNASDAQ100U` (the "above K" ladder, strikes 5 or 10 points apart, event `H1600`): IDXFUT1 and INX1 test the ladder against an OUTSIDE price; IDXFUT1 says the range series "have no candle history on disk"; ARB2 did live crossed-ladder scans inside one series and ARB4 only crypto. **No test of the range series against the ladder at the same 4 pm close exists. This is the new cell.**

## What was looked at before registering (disclosure)
Only structure, no price or outcome: the settled listings of `KXINX` and `KXNASDAQ100` (43 events each, 1,290 markets each, 2026-08-24 to 2026-10-28), their strike types and strikes, and how many bracket cap strikes also exist as a `KXINXU`/`KXNASDAQ100U` strike in `data/inx1.sqlite` (540 of 1,204 for S&P; 922 of 1,204 for Nasdaq). No bracket candle was read.

## Mechanism and counterparty
The two series are quoted by different books (a range book with 30 markets, a ladder book with about 300) for the same settlement value (the index level at 4 pm ET). Identity for strikes lo < cap on the ladder and the bracket between them: P(between) = P(above lo) - P(above cap). Who pays: a quoter who moves one book and not the other (stale or one-sided), or retail trading the range book by feel.

## Universe (fixed now)
Index series pairs: (KXINX bracket, KXINXU ladder) and (KXNASDAQ100 bracket, KXNASDAQ100U ladder), events with H1600 close, 2026-08-24 to 2026-10-28 (the days `inx1.sqlite` holds). A bracket is usable when KXINXU/KXNASDAQ100U (from `inx1.sqlite`) has a market at BOTH of its edges: ladder strike within 0.011 of the bracket floor_strike and of the cap_strike. Candles of the bracket markets: Kalshi batch candlesticks, 1 minute, from 90 minutes to 8 minutes before the close (same window as the ladder on file), cached under `data/xladder1.sqlite`, 1 thread, sleeps, 429 retried.
**Split by event date (fixed now):** per index, events sorted by date: first 15 DISCOVERY, next 14 VALIDATION, last 14 HOLDOUT (frozen, unread; not scored until the owner or coordinator allows, and only if both earlier windows pass).

## Looks, quotes, fills
Looks at 60, 30 and 10 minutes before the close (the candle ending then). A quote is valid when bid and ask are both present, bid < ask, and the candle is not older than 5 minutes. Per bracket, per event, the FIRST look (60, then 30, then 10) at which a signal fires is the trade; later looks are ignored. All legs fill at the NEXT 1 minute candle's closing ask (a NO leg pays 1 - closing bid); if any leg has no valid quote at the fill candle the trade is not filled and is counted as a miss. Fee 7% x C x p x (1-p) rounded UP per order per leg at C = 10; stressed fee x1.2. The spread is crossed (asks only).

## Rule LOCK (identity lock, 3 legs, held to settlement)
For a usable bracket B with ladder edges lo, cap: (+) buy YES B, buy YES above(cap), buy NO above(lo): pays exactly $1 in every outcome. Signal lock = bid(lo) - ask(B) - ask(cap) - fees at the signal candle (fees at C = 10 on each leg), fires when at least +1.0c a contract. (-) buy NO B, buy NO above(cap)... written exactly: buy NO B, buy YES above(lo), buy NO above(cap): pays exactly $2; signal lock = 2 - [(1 - bid B) + ask(lo) + (1 - bid(cap))] - fees, fires when at least +1.0c. Also the tail legs: KXINX "greater" tail against the same-strike KXINXU market (2 legs, YES one, NO the other; pays $1) and the "less" tail against it as the complement. PnL per trade = payoff - cost at the FILL candle prices - fees, so slippage between signal and fill counts. Contracts 10 per leg.

## Rule CHEAP (single leg, cheap side against the sister ladder, held to settlement)
For a usable bracket with valid ladder quotes at both edges (spread at most 6c each): implied_yes = mid(lo) - mid(cap) (mids of bid and ask). BUY YES B when implied_yes - ask(B) >= 0.04 and ask(B) is 0.05 to 0.95; BUY NO B when bid(B) - implied_yes >= 0.04 and (1 - bid(B)) is 0.05 to 0.95. Gap 4c = rounded fee at mid prices (about 1.5c to 1.8c) plus about half the two spreads, fixed now and not tuned. Fill at the next candle's ask on that side, 10 contracts, held to settlement. One trade per bracket per event. At most 10 brackets per event per index (the ones with the largest gap at the first firing look).

## Hard limit (probe spec, if any rule survives)
1 contract per trade, one open trade per index per event, at most 5 trades a day, kill on a net loss of $5 or 20 consecutive losers or 40 fills with net below zero, worst day $5 at 1 contract. When 40 fills would exist: at the discovery rate, to be filled in the result.

## Numeric prediction (stated now)
LOCK: signal locks of at least 1c: 0 to 3 in the whole sample (best median lock -5c to -9c as in ARB4), filled at a profit: 0. CHEAP: 15 to 60 trades per month per index (stale closing quotes on thin brackets dominate the gap), win rate 2 to 6 points below the price paid, mean net -3c to -1c, PF 0.6 to 0.95. Verdict most likely FALSIFIED for CHEAP and NOT_ENOUGH_DATA for LOCK (prior of any pass 5%).

## Kill rules
FALSIFIED if mean net after fee and spread is not above 0 in BOTH discovery and validation, or profit factor (C = 10) is under 1.5 in either. NOT_ENOUGH_DATA if under 150 trades in discovery plus validation for the rule (then months to go at the observed rate reported; the history is about 2 months so a forward recorder would be the route). Pass bar for any claim: PF 1.5 or better in discovery and validation, mean net above zero at fee x1.2, day-clustered z against the deflated bar (about 5.27 at N 730,013 + 4), a named counterparty, and ONLY THEN the frozen holdout is read once. Zero-volume fill candles are reported separately and a rule that only works on them is not a pass.
**N:** +4 (two rules, +2 each). Expected read date: today 2026-11-03 (history already on file for the ladder side; the bracket side is one batch fetch).
