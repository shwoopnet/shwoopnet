# DAILY2 registration: Kalshi's WTI, EUR/USD and USD/JPY daily markets against a fair value from the outside price and its own realised volatility

Worker DAILY2, Strategy Research V2, 2026-10-29. Research only. Written and pushed **before** any Kalshi quote was compared with any reference price, model probability or outcome. Series census and ledger check: `workers/DAILY2_CHECK.md`.

## Ledger check (summary; detail in the check file)

- **Gold daily and weekly (KXGOLDD, KXGOLDW): skipped.** The GOLD2 strategy card registers the gold daily ladder against a volatility-implied probability; CMD1 already ran that mechanism on KXGOLDD (-7.1c, volatility calibrated); LADL1 and GOLDFV1 cover the rest.
- **10 year Treasury: not runnable as a daily family.** No daily 10Y series has a settled market in Kalshi's reach; the weekly ones have 3 to 8 events; the hourly Pyth series starts 2026-10-09. Not run, not counted.
- **Weekly WTI, EUR/USD, USD/JPY: 9 to 10 events each.** Not run, not counted.
- **WTI is close to a reword of CMD1** (same mechanism on `KXWTI`, decision 3 hours out, FALSIFIED pooled). DAILY2 changes the looks (60, 30, 10 minutes before the settlement) and the reference (the named futures month). Counted as new tries; if the lead judges it a reword of CMD1, the 3 WTI tries are still counted and the verdict reads as a confirmation.
- **EUR/USD and USD/JPY daily range markets (KXEURUSD, KXUSDJPY):** never tested (the ledger's FX entries are the 15 minute up/down series under L1's rule).
- Approach reused from INX1 (`workers/INX1_REGISTRATION.md`, `src/scalper/inx1.py`): universe fixed from quotes 75 minutes before the close, edge 0.05, at most 2 strikes per event per look, hold to settlement, thirds by date. INX1's series are not touched.

## What was looked at before registering (disclosed)

Series titles, settlement sources and rules text; counts of settled events and markets, strike types, close times and median contracts per event (table in the check file); one settled market per series including its `expiration_value` and `result` (KXWTI Oct 28: 102.78; KXEURUSD Oct 29: 1.11355; KXUSDJPY Oct 29: 157.825). Yahoo: bar counts and first and last timestamps only for `CL=F`, `CLZ26.NYM`, `EURUSD=X`, `JPY=X` at 1, 2 and 5 minutes. No Kalshi candle was downloaded; no model value, signal or outcome has been computed.

## The rule (exact)

- **Markets and settlement:**
  - `KXWTI`: YES if the NYMEX daily settlement of the WTI futures month named in the market's `rules_primary` ("(December 2026 contract)") is above `floor_strike`. Close 18:30 UTC.
  - `KXEURUSD`, `KXUSDJPY`: the ICE 10 AM EDT open print. `greater`: YES if above `floor_strike`; `less`: YES if below `cap_strike`; `between`: YES if from `floor_strike` to `cap_strike`. Close 14:00 UTC.
  - Outcome is Kalshi's recorded `result`.
- **Days:** every event closing from 2026-08-31 00:00 UTC to 2026-10-29 00:00 UTC (events through Oct 28) whose reference bars exist. The start date is set by Yahoo's 2 minute reach.
- **Reference (Yahoo 2 minute bars, keyless):**
  - EUR/USD: `EURUSD=X`. USD/JPY: `JPY=X`.
  - WTI, the contract Kalshi names:
    - December 2026: `CLZ26.NYM`.
    - October 2026 on a day up to its last trading day, 2026-09-22: `CL=F`.
    - November 2026 on a day from 2026-09-23 to its last trading day, 2026-10-20: `CL=F`.
    - Any other pairing (Kalshi's 2-business-day early roll while `CL=F` is still the old month, about 2026-09-18 to 09-22): no entry that day.
  - Assumption: Yahoo's `CL=F` rolls at expiry. This is disclosed and not checked against outcomes.
- **Looks:** L minutes before the close; D = close - L.
- **Information at D:**
  - S = close of the latest 2 minute bar that **ended** at or before D - 60 s, and no more than 10 minutes before D. Otherwise no entry that look. A bar starting at t ends at t + 120.
  - sigma2 = population standard deviation of the log returns between consecutive bars among the last 301 bars ending with that bar. A return is skipped if its two bars are more than 6 minutes apart. At least 150 returns are needed, else no entry.
  - T = close - (that bar's end).
  - s = sigma2 x sqrt(T / 120).
- **Fair value (zero drift, lognormal):**
  - greater: p = Phi(ln(S/K)/s).
  - less: p = 1 - Phi(ln(S/cap)/s).
  - between: p = Phi(ln(S/floor)/s) - Phi(ln(S/cap)/s).
- **Universe (fixed for the day and all looks, from quotes and time only):** strikes whose Kalshi mid ((yes_bid + yes_ask)/2) is between 0.05 and 0.95, taken at the last two-sided 1 minute candle ending at or before close - 75 min and no more than 15 minutes stale. That point is 15 minutes before the earliest look.
- **Signal:** the Kalshi 1 minute candle ending at D (its closing bid and ask; needs yes_bid > 0 and yes_ask < 1).
  - YES if p - yes_ask >= 0.05.
  - NO if yes_bid - p >= 0.05.
  - At most the 2 strikes with the largest edge per event per look.
- **Fill:** at the next candle, ending at D + 60, which is a quote one can hit after the signal is known.
  - YES at its yes_ask; NO at 1 - its yes_bid.
  - It must be two-sided (yes_bid > 0, yes_ask < 1); if not, no entry.
  - The order is taken whatever that price is: the edge is not re-checked.
  - Information only: the same orders filled at the signal candle's own close (D).
- **Exit:** hold to settlement. No stop.
- **Size:** C = 1 and C = 10 contracts per order. Candles carry no size, so the 10 contract figure is an upper bound.
- **Fees:** 7% x C x price x (1 - price), rounded up to the cent per order (`fees.taker_fee`); checked again at fees x1.2.
- **Zero volume:** the primary result keeps a fill candle with zero volume if it is two-sided. It is reported again treating those fills as unfillable.

## Variants (N tried = 8, fixed now)

| Market | Looks | Variants |
|---|---|---|
| WTI | 60, 30, 10 minutes | 3 |
| EUR/USD | 60, 30, 10 minutes | 3 |
| USD/JPY | 60, 30 minutes | 2 |

- USD/JPY is the thinnest of the three, so it gets only the two earlier looks; that keeps the total at 8.
- Each variant is scored on its own.
- Fixed and not tuned: the 0.05 edge, the 2 strike cap, the 0.05 to 0.95 universe, 75 minutes, the 301 bar window, the 60 s lag and zero drift.
- Running count before DAILY2: about 438,910 (V2_STATUS about 438,904 plus INX1's 6; other workers may add in parallel). After DAILY2: about 438,918. Deflated bar z about 5.17.

## Windows

- Unit: a close (a trading day), since the three series' days coincide.
- The days are the union of the three series' close dates in scope, sorted and split into thirds by date: A (discovery), B (validation), C (holdout).
- A and B results and verdicts are written to `workers/DAILY2_RESULT.md` and pushed before C is computed. C is read once.

## Counterparty

- **Claimed:** takers and quoters on thinly traded daily ladders who reprice slowly after a move in the outside price. In the last hour before a 2:30 PM settlement or a 10 AM print, a strike's ask then sits 5c or more under the probability implied by the outside price and its own recent volatility.
- **Honest alternative, expected:** Kalshi's quoters price off the same feed, as GOLDFV1 (gold) and XMAC1 (15 minute markets) found. A 5c gap is then mostly the model being wrong.
- **Known model errors, stated in advance:**
  - WTI's hour before settlement is busier than its trailing 10 hours, so the model is too confident there and leans toward buying favourites. CMD1 measured WTI's spread understated by a factor of 1.43.
  - The FX 10 AM print follows US data releases at 8:30 and 10:00 ET.
  - Yahoo's FX feed is not ICE's.
  - A loss pattern of model favourites losing more often than the model says is this bias, not a counterparty.

## Numeric prediction

- About 42 trading days (about 14 per window).
- 0 to 2 orders a day per variant where a signal fires.
- PF after fees between 0.4 and 1.1 for most variant-windows.
- No variant at PF >= 1.5 in both A and B.
- No window reaches 30 independent closes, so no variant can pass.
- Expected family verdict: FALSIFIED for most variants; NOT_ENOUGH_DATA where a variant trades on fewer than 15 days in A plus B.

## Kill criteria and verdicts (per variant, C = 1, fees x1)

- **Fewer than 15 days with an order in A plus B:** `NOT_ENOUGH_DATA`.
- **Pooled A plus B PF under 1.0:** `FALSIFIED`. It lost money on all the data it saw, so it is not a candidate whatever the sample size.
- **Otherwise:** `NOT_ENOUGH_DATA`. No window can hold the 30 independent closes the bar needs, so a variant that is not losing cannot be passed or falsified on this history.
  - For the record, if a variant still has PF >= 1.5 in A and in B, its C is read and reported. A forward read is then proposed to the lead and **not** registered here.
  - It would need PF >= 1.5 in all three windows, positive at fees x1.2, at least 30 closes in each window, and a day-clustered z at the deflated bar (about 5.17). None of these can happen with about 14 closes a window.
- **Family verdict:** FALSIFIED if every variant is FALSIFIED. Otherwise the strongest variant verdict, stated with its numbers.

## What is reported

Per variant and window:
- PF at C = 1 and C = 10, and PF at fees x1.2.
- Net, orders, independent days, markets and loss rate.
- Zero-volume share, and PF with zero-volume fills dropped.
- PF of the information fill at D.

Also:
- The day-clustered z of the pooled A plus B net (C included only after C is read).
- Orders by side and by price at or above 0.5, with their losses (the model error check).

## Data and code

- Public and keyless:
  - Kalshi `/markets` (settled) and `/markets/candlesticks`, 1 minute, from close - 92 min to close - 8 min.
  - Yahoo chart, 2 minute bars, 7 day chunks.
- Stored in the session scratchpad. Nothing under `kalshi-scalper/data/` is committed.
- Code: `kalshi-scalper/src/scalper/daily2.py`.

## Amendment 1 (2026-10-29, before any Kalshi candle was downloaded and before any model value, signal or outcome was computed)

Yahoo's 2 minute bars, fetched in 7 day chunks, start only at **2026-09-24** for `CL=F` and `CLZ26.NYM` and at **2026-09-17** for `EURUSD=X` and `JPY=X`. Earlier chunks come back empty or refused, so the "last 60 days" in the check file was wrong. That would leave about 25 WTI days and 30 FX days, about 8 to 10 a window. Sample size is the binding constraint here, so the reference changes to **5 minute bars**: one `range=60d` request, `CL=F` from 2026-08-20, FX from 2026-08-06. The rule's other parts are unchanged in meaning:

- **S:** the close of the latest 5 minute bar that ended at or before D - 60 s. Bars start on 5 minute marks and every look is on a 5 minute mark, so in practice this is the bar ending at D - 300 s. The reference is about 5 minutes old, which counts against the model.
- **Staleness limit:** 15 minutes.
- **sigma:** from the last 121 bars (10 hours, as before). A return is skipped if its bars are more than 12 minutes apart, and at least 60 returns are needed.
- **Time scaling:** s = sigma5 x sqrt(T / 300).
- **WTI before 2026-10-16** uses `CL=F` as registered. On the December days it uses `CLZ26.NYM`; its 5 minute bars cover every day it is needed, since Kalshi names December only from about 2026-10-16.
- **Days:** still from 2026-08-31, as registered.

Nothing else changes: variants, N = 8, windows, edge, universe, fill, fees, kill criteria and prediction.
