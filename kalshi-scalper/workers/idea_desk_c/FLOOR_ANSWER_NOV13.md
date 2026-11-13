# Queue floor answer (Idea Desk C, Nov 13, 2026, 00:49Z request)

**Answer: none.** No published mechanism I have read meets all three tests at once: unique, at least 15 fillable signals a day on one family, and a published size near the 11 to 12 points the bar needs at mid prices. Below is the best candidate and what it would need. [research]

## The best candidate: momentum into the US close, on Kalshi's index up-or-down markets

- **Mechanism (Gao, Han, Li and Zhou, JFE 2018; Baltussen, Da, Lammers and Martens, JFE 2021):** the index's return over the trading day so far predicts the last 30 minutes in the same direction, because dealers who are short gamma hedge with the move.
- **Venue:** the S&P 500 and Nasdaq 100 intraday up-or-down series (6 series, NEVER READ in Desk B's table; spread unmeasured).
- **Decision data, permitted, and already recording:** Kalshi's own US500 and US Tech 100 perp marks, sampled every 30 seconds by the perps recorder in the 09:10 to 10:30 and 15:40 to 17:00 New York windows. No outside host is needed.
- **Why it fails today, in numbers:**
  1. **Count.** Only the window that closes at the US close qualifies, so about 2 signals a day (two indices), about 500 a year. That is about 2.4 years to 1,200 bets, against the 15 a day guide.
  2. **Size.** The published effect is an R-squared of about 1.6% on SPY. As drift it is a few basis points against a 30 minute standard deviation of roughly 25 basis points. That moves the chance of "up" from 50% to about 53% (2 bp) to 58% (5 bp); even 10 bp gives about 65%. The bar needs about 62% at 50c, after the fee. Only the largest-move days could get there, and those are rarer still.
  3. **Spread and decay.** Spread is unmeasured on these series (the index ladders were 10c to 16c, "too costly"), and nobody has measured decay since 2020.
- **What it would need to become a card:**
  - a zero-try cost read of the six up-or-down series (lists plus one candle per window, for the spread at the last hour);
  - a published or measured size for the conditional case (days with a rest-of-day move beyond about 2 standard deviations);
  - at least one more qualifying window a day (a Kalshi index series closing at 15:30 ET as well as 16:00 would double the count).
  Without all three it stays an idea, as the Head already recorded for the perps.

## Lessons from tonight that removed the other candidates

- **Thin sports books die on count:** tonight about 70 fills in six weeks on the largest esports title.
- **"Listed" is not "quoted":** pre-match e-soccer had no tradeable spread.
- **Ties are priced above base rate in the NHL**, which removes the draw-underpricing literature as a seed.
- **The combo leg-count markup** is the one sized result, and it already sits with Desk B as a cut on the registered house-side paper test.
- **A slow-family paper-list seed** would be the macro high-tail overpricing (Diercks, Katz and Wright, FEDS 2026-010: high inflation and unemployment bins "a little too" likely). It has no published return figure, so it is not offered as a card.
