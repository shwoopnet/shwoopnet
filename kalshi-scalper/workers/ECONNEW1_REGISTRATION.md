# ECONNEW1 registration (Strategy Research V2, written 2026-10-31 BEFORE any claims candle was scored or any claims result was read; research only)

One angle registered: (a) weekly initial jobless claims. The other angles are in `workers/ECONNEW1_LEDGER_CHECK.md` (NOT_RUNNABLE, NOT_ENOUGH_DATA or deferred); none of them is scored.
Code `src/scalper/econnew1.py`; it is committed and pushed with this file, then run once. Nothing here means trade.

## What was looked at before this registration (honest disclosure)
Counts, dates, volumes and spreads of Kalshi's economic-release series (listing only), the stored CPI1 candles for quote availability, the FRED ICSA csv (read to check it downloads
and that its last row is 194,000 for the week ending 2026-10-24), the market list of KXJOBLESSCLAIMS (ticker, strike, close time and `result`/`expiration_value` fields came
back in the same listing; they were not used to choose the rule: the rule below is a fixed formula of the FRED series and the strike). One count of how many strikes the model
puts between 0.05 and 0.95 (377 of 611) and between 0.10 and 0.90 (262) was taken to size the download; no price and no outcome was joined to it.

## Counterparty and mechanism
Who loses: market makers and retail on weekly claims strikes who anchor on last week's print and the quoted consensus. Claims are seasonally adjusted, noisy (a typical week moves
5k to 15k) and mean reverting around a slow trend, so after an outlier week the right centre is between the last print and the 4 week mean; a book that centres on the last print
misprices the ladder next to it in a direction the 4 week mean knows. What the model is blind to, and why it can lose: the market also has the consensus forecast of economists,
Wednesday state-level hints (some states publish early) and the weather/holiday story, none of which is public here. Prior that it is already priced in: high.

## Rule (all fixed now)
Series KXJOBLESSCLAIMS only ("At least K initial claims for the week ending Saturday S"; `strike_type greater_or_equal`, strikes 5,000 apart; the old one-strike `KXJOBLESS`
2021 to 2022 listing is excluded: one strike per week, typical volume 4 to 44 contracts). Event = one release (Thursday 7:30 CT, Wednesday in a Thanksgiving week).
1. Target week S = the Saturday before the market's close date. Known at the decision: FRED `ICSA` for weeks ending S-7, S-14, S-21, S-28 and earlier.
2. Forecast f = 0.5 x ICSA(S-7) + 0.5 x mean(ICSA(S-7), ICSA(S-14), ICSA(S-21), ICSA(S-28)). No fitting.
3. Error sample: for the 104 weeks s = S-7, S-14, ..., S-728, e_s = ICSA(s) - f(s) with the same formula (an expanding, rolling past only). Fair probability that claims are at least K:
   fair = (count of e with f + e >= K, plus 0.5) / (n + 1) where n is the number of errors available. Needs at least 100 of the 104 errors.
4. Universe (fixed from the FRED series and the strike alone, before any price): strikes with fair between 0.10 and 0.90.
5. Decision time = market close minus 24 hours (Wednesday 7:25 CT, or the Tuesday-night equivalent in a holiday week). Price: the last hourly candle ending at or before it with a valid bid and ask
   (YES bid < ask) that is at most 6 hours old: buy YES at the ask or NO at 1 - bid. If no such quote exists (all history before about 2026-08-24), the last TRADE price of an hourly candle at most 48 hours old,
   with an assumed half spread of 3c each way (ask = last + 0.03, bid = last - 0.03, the live open-market median spread on claims strikes was 5.5c on 2026-10-30). **This is a different cost rule from CPI1 and it is
   stated here because most events have no quotes; any trade-price entry is a model of the fill, not a fill.** Entries by mode are reported.
6. Trigger: buy YES if fair - ask >= 0.05; buy NO if bid - fair >= 0.05. Information only: 0.03 and 0.08. One order of C = 10 contracts per qualifying strike, hold to settlement.
7. Fees: 7% x C x p x (1-p) per order, rounded up to the cent (C = 10, p the price paid), per contract = order fee / 10. Stress: fees x1.2.
8. Windows by market close date (fixed now): discovery before 2026-04-01; validation 2026-04-01 to 2026-10-16; frozen holdout 2026-10-17 onward (the latest 12 days: the Oct 22 and Oct 29 releases).
   The holdout is read once with the others (one run), not tuned on.

## Judging
Profit factor first. n is independent releases, not strikes (strikes of one release share one outcome); z is clustered by release (`calibration.cluster_mean_z`).
- `NOT_ENOUGH_DATA` if discovery plus validation hold fewer than 25 releases with a trade or fewer than 100 trades.
- `FALSIFIED` if profit factor is under 1.5 after fees in discovery or in validation, or under 1.0 pooled.
- `NOT_YET_FALSIFIED` needs all of: PF at least 1.5 after fees in discovery AND validation, pooled mean net at least +2.0c per contract, release-clustered pooled z at least 5.27 (the deflated bar at running N about 728,680),
  pooled PF at least 1.3 at fees x1.2, and holdout PF at least 1.5 if the holdout holds any trade (its n is shown; two releases cannot meet a sample minimum, so the holdout can only fail the claim).
  Reaching it would only permit a forward quote-based re-read (dated 2027-02-18, when about 25 releases with quotes exist), never a trade.
The strike rule, edge, lead, half spread, universe cut and windows are not changed after the result.
Information only (not judged): edges 0.03 and 0.08, quote-mode entries alone, model Brier against the market's, and a look-ahead control: the mean absolute difference between the FRED value of the target week and Kalshi's
first printed value (`expiration_value`) over the universe's weeks. FRED holds revised and re-seasonalised history; the prior-week value known at the decision was revised the same Thursday, so this is a small look-ahead, not a large one.
If the control shows a mean absolute difference over 3,000 claims, the result is voided as `NOT_ENOUGH_DATA` for look-ahead.

## Numeric prediction and kill criteria
Prediction: 150 to 260 trades on 40 to 55 releases, pooled profit factor 0.7 to 1.1 after fees, mean net -2c to +0.3c per contract, release-clustered z between -2 and +1. Prior of a pass under 3%.
Kill: any condition above failing = FALSIFIED. No variant is run after the result.
Not L1: a weekly macro release market held to its Thursday settlement; no 15 minute window.

## Tries
One rule (two information thresholds shown, not counted as tries): N +3, running count about 728,680 (z bar 5.27).
