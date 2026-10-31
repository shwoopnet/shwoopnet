# DERIBIT-IMPLIED registration (written 2026-10-31, 2:50 PM CT, before any recorded row exists)

Owner approved the proposal at 2:45 PM CT on 2026-10-31 (relayed by the main session). Two tries. Forward only: Deribit keeps nothing of an expired option, so there is no history to score. Running count before: about 728,692 (z bar 5.27); after: about 728,694, z bar about 5.27 at the read. Nothing in this file may be changed after the first recorded row; a change is an amendment pushed before the read, with no new tries.

## Ledger check (what is NOT repeated)

- **DIGI1 / BTCDIGI-F (README strategy card DIGI1; `workers/NEWH13_REGISTRATION.md` H3):** the same idea in a narrower form: only the 08:00 UTC KXBTCD close, a model-free call-spread digital from two bracketing strikes, one trade a day, 4c threshold. It was NOT_ENOUGH_DATA and never recorded. This card widens it to all 24 hourly closes and replaces the call spread with a model (implied vol surface), because the daily 08:00 UTC expiry is the only close Deribit lists an option for. It does not replace the BTCDIGI-F rule, which stays registered.
- **LAD1 and NEWH14:** priced the ladder with REALISED volatility (and NEWH14 the ladder's own wing structure). Both FALSIFIED. The input here is Deribit's IMPLIED volatility, which neither used. IV1 used DVOL (a single 30 day number) on the 15 minute market: FALSIFIED, the market's mid was the better probability. DVOL is not used here; the surface is per strike and per expiry.
- **TAIL, KINK, CORR1:** internal-shape tests of the ladder (longshot buying, a strike 5c off its neighbours, G3H1 on a look-ahead-free file). None had an outside price. This card has one.
- **QUOTE2B and the book recorder:** the Kalshi side of a maker test on the same ladder. Different question (queue and fills). This card is a taker test held to settlement.
- **NEWH13 H3 and the Deribit probe in NEWH13:** public API probed, expired options return nothing; only a forward recorder works. That is why this is a recorder.
- **Not repeated:** any rule that uses the Kalshi ladder's own prices as the fair value, any realised-vol model, any Deribit perpetual or DVOL input.

## Question, counterparty, edge source

Does the hourly Bitcoin ladder (KXBTCD) misprice against the digital probability implied by Deribit's option surface? Loser: ladder quoters who do not read Deribit's book. Honest prior: few such quoters; prior of a survivor 5%. Edge source: Deribit's public mark_iv per instrument (keyless, no auth), from the nearest expiries, giving P(final above K) for every ladder strike at each of the 24 daily closes. This is IMPLIED vol, different from the realised-vol inputs of LAD1 and NEWH14.

## The math, fixed now

Inputs per look (all from the same poll minute): Deribit `public/get_book_summary_by_currency?currency=BTC&kind=option` (mark_iv in percent, underlying_price, underlying_index, bid/ask, creation_timestamp), `public/get_index_price?index_name=btc_usd` (S0), `public/get_instruments` once per window (expiration timestamps; a name like `BTC-13NOV26-83000-P` is the fallback, expiry 08:00 UTC that date). Kalshi: the open KXBTCD markets of the closing event (yes bid and ask, floor_strike).

1. **Expiries.** T is the Kalshi close. E1 is the first Deribit expiry at or after T; E2 is the next expiry after E1. Deribit's expiries are daily at 08:00 UTC (weeklies, monthlies, quarterlies are among them). Only the close at 08:00 UTC has an expiry equal to it; for the other 23 closes no listed expiry is at or before T that is still live at the look, so **no bracketing pair exists** and the expiry rule is extrapolation, not interpolation: the total variance is linear in time from zero at the look to E1, which is flat implied volatility from E1 down to T. E2 is recorded for an information check (forward variance E1 to E2) and is NOT used in the rule. Stated plainly: this applies a roughly one day volatility to a 45 minute horizon, ignores intraday vol seasonality, and is part of why the prior is PF 1.00.
2. **Strike interpolation.** In E1, use the out-of-the-money instrument at each Deribit strike (put below F_E1, call at or above), drop mark_iv of 0 or missing, and for a Kalshi strike K take the two adjacent Deribit strikes K1 <= K <= K2 and interpolate mark_iv linearly in strike: sigma(K). No extrapolation outside the listed strikes (no estimate, strike skipped).
3. **Forward.** F_E1 = median underlying_price of E1 instruments in the snapshot. F_T = S0 * (F_E1 / S0)^(tau_T / tau_E1) (log-linear carry from the Deribit index S0). tau_E1 = (E1 - t)/ms per year, tau_T = (T - t)/ms per year, t = median creation_timestamp of E1 instruments.
4. **Try A (no skew correction).** w = sigma(K)^2 * tau_T. d2 = (ln(F_T/K) - w/2) / sqrt(w). P_A = N(d2).
5. **Try B (skew correction).** P_B = N(d2) - vega * dsigma/dK, vega = F_T * phi(d1) * sqrt(tau_T), d1 = d2 + sqrt(w), dsigma/dK = (sigma(K2) - sigma(K1)) / (K2 - K1) with sigma as decimals, clipped to [0.001, 0.999]. (P = -dC/dK with r = 0.)
6. **Basis (stated, not corrected).** Kalshi settles on the 60 second average of CF Benchmarks' BRTI before T; Deribit's index is its own composite. They differ by tens of dollars, and near the money one dollar moves P by roughly 0.0005 to 0.0015, so 30 dollars of basis can be 1.5c to 4.5c against a 5c rule. The recorder keeps the Deribit index and every ladder quote, so the basis can be measured afterwards (the strike where the Kalshi mid is 0.50 against S0). It is an information check, never an adjustment to P.

## The look and the rule

- **Look:** the poll at 45 minutes before each hourly close (the recorded minute with 44:30 to 45:29 left). The recorder records every minute from 60 to 30 minutes before each close; only the 45 minute row selects and prices a trade. The other rows are for information.
- **Universe (cost, observable before any outcome):** strikes within 3% of S0, with a two-sided Kalshi quote (bid above 0, ask below 1) and (yes ask minus yes bid) at most 4c, at the 45 minute look.
- **Rule (per try):** edge_YES = P - yes_ask; edge_NO = (1 - P) - no_ask, no_ask = 1 - yes_bid. Trade the side with the larger edge if it is at least 5c; one trade per close (the best across strikes), fill at the quoted ask at the look, held to settlement. Fees: 7% x C x p x (1 - p), rounded up to the cent per order at C = 10; fees x1.2 sensitivity reported.
- **L1 overlap:** the ladder is KXBTCD (hourly), L1 is the 15 minute series, different tickers. Bitcoin L1 is paused, but the open interest core (REF_GEN6_OICORE) can enter 3 minutes before a quarter hour. Any hourly close whose same-instant 15 minute window had the OICORE forward evaluator fire is skipped, and every candidate from this card is marked **paper only**; a pass permits only considering a small slot that cannot hold at the same time as L1.

## Prediction and kill criteria (numeric, fixed)

- **Prediction:** PF 1.00 (0.85 to 1.15), about 140 trades in 60 days. Brier: Kalshi's mid at least as good as Deribit's.
- **NOT_ENOUGH_DATA:** fewer than 150 trades in the recorded span (checked first).
- **FALSIFIED if any:** PF under 1.3 in either half (the recorded span split at its midpoint date); Kalshi's Brier at or below Deribit's Brier (mid of bid and ask against the outcome, every universe strike at the 45 minute look, own P per try); day-clustered z under 3; or z below the deflated bar (about 5.27 at the read). A try that passes all of these is NOT_YET_FALSIFIED, never "proven"; the next step is a larger forward window.
- Tries are A and B; each is judged alone; the deflation counts both.

## Recorder, stop date, read date

Recorder: `scripts/record_deribit.py` and `.github/workflows/record-deribit.yml` on branch `claude/v2-recorder-deribit` (owner merges; nothing places an order). Public keyless endpoints only; data goes to the `quote-data` branch under `deribit/`. Built-in stop date **2026-12-31** (UTC): after it the script records nothing. Settled results are fetched later from Kalshi's public settled markets (`/markets?series_ticker=KXBTCD&status=settled`, by close time), by the recorder 5 minutes after each close and again by the scorer. **Read date: 2027-01-01 00:00 UTC**, one read, scorer written and pushed before it.

## Disclosure of what was looked at before writing

Today (2026-10-31) only the shapes of three public responses were looked at to confirm field names: one Deribit index price, the head of the option summary (one put and one call, mark_iv about 37 to 38 for a 13 November put) and the head of two open Kalshi KXBTCD markets. No implied probability was computed, no Kalshi price was compared to one, and no outcome was read. The ledger texts above are the only other input. No recorded row exists at the time of this commit.
