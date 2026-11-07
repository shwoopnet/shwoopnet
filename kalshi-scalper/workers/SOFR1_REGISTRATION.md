# SOFR1 registration: cheap-tail brackets of Kalshi's daily SOFR markets (KXSOFRD) against last print plus calendar effects (Strategy Research V2, research only)

Written 2026-11-07 (a Saturday), BEFORE any KXSOFRD candle price or settled result was read. Discovery lane, nothing here means trade, no promote verb,
touches no live code, `functions/`, `index.html`, L1 or OICORE. **This is a FORWARD REGISTRATION. Nothing is scored now and nothing in history is scored.**

**Plain statement of the prior.** The honest prior is **NOT_ENOUGH_DATA**, certain on history and very likely on any horizon the project will wait
(150 treated trades at an expected 2 to 5 a month is 3 to 6 years). The chance that the rule ever passes (PF 1.5 or better after fee, 150 treated, both
halves positive, named counterparty confirmed) is about **5%**, and that is generous: every official-statistic test so far (GOVSER1_RESULT.md: GAS1
-7.50c, GAS2 -5.98c, MORTGAGE1 -5.77c, ECONNEW1 +0.29c, NOWCAST1 PF 1.00, FEDIMPL1 0 of 12) found the market mid a better forecast than the free outside
series. SOFR is the most predictable number on the list (a day to day change is usually 0 to 3 bp), so the traders who are on the other side are likely
professionals pricing the same calendar, not retail guessing. The registration exists so a cheap, well specified forward line is on record, not because
anything points to an edge.

## What was seen before writing (disclosure)
- Series metadata for KXSOFRD (title "Daily SOFR", frequency daily, source Federal Reserve Bank of New York, quadratic fee, minimum tick 0.001) and the
  contract rules text of one OPEN market (event KXSOFRD-26NOV09).
- One live quote ladder of the open event KXSOFRD-26NOV09 (8 markets), seen only to learn the bracket layout. No candle, no settled price and no
  settled result of any past event was read.
- The count of settled events (65, series starts 2026-08-06; 41 before the 2026-10-03T16:00Z cut, therefore 24 after it). Counts only.
- Keyless reachability, verified 2026-11-07: NY Fed `https://markets.newyorkfed.org/api/rates/secured/sofr/last/N.json` and
  `.../sofr/search.json?startDate=...&endDate=...` (returns rate, percentiles 1, 25, 75, 99, volume in billions), and
  `https://markets.newyorkfed.org/api/rp/all/all/results/last/1.json` (overnight repo operations, offering rate, amounts). Last value seen: SOFR 3.92
  for 2026-11-05 (3.94 on 11-04, 3.97 on 11-03). The reference series is public and has history from 2018, far longer than the Kalshi series.

## Structure of the contract (read from the rules text, important for the look)
- One event per business day T. Markets (8 per event): `T<x>` "SOFR at least x" (top), `T<y>` "SOFR at most y" (bottom), and `E<z>` "exactly z"
  (between z and z, rounded to two decimals) for the middle values. Rate is the initially reported SOFR **for the previous business day E**, in the NY
  Fed table, column Rate (%), revisions ignored. Example: event 26NOV09 (Monday) asks about SOFR for Friday 2026-11-06.
- Trading closes at about 12:59Z on T (one minute before the 8:00 ET publication). So at any look before the close, the last PUBLISHED rate is that of
  the business day before E (published on the morning of E), i.e. the information gap is two business days of repo market, and a Monday event looks
  across a weekend.
- Fee: Kalshi quadratic. The study fee is 7% x C x p x (1 - p) rounded up to the cent with C = 10, stress x1.2.

## Counterparty (named, and doubted)
Retail traders guessing a funding rate that has month-end, mid-month tax and Treasury coupon settlement structure and policy-date steps, who
anchor on the last print and on round numbers. Doubt (stated now): the structure is public and regular, a daily bracket with 8 strikes is thin enough
that market makers can price it from the same NY Fed data, and Kalshi's own listing note says the economics category mid beat outside references
every time so far. If the cheap-tail ask is above the model's fair value in every class, the conclusion is that nobody is wrong here.

## Universe (fixed now, before any outcome)
Every KXSOFRD event whose trading closes **on or after 2026-11-10 (UTC)**, the first one after this registration is pushed. The 65 existing settled
events (41 before the cut, 24 after) are **not scored by this registration**: the 41 pre-cut events keep the frozen last third unread, and the 24
after the cut are held as a reserve that may be read once, for information only, at the first read date. Unit of clustering: one event (one independent
draw of one number). At most one treated trade per event.

## Reference and model (constants frozen now)
Inputs, all public and outcome free: NY Fed SOFR history (rate in percent, two decimals, from 2023-01-03 to the last business day before 2026-08-06
for the calibration set; the calibration window is frozen at that end date and is never extended, so no forward outcome ever enters the model),
the NY Fed business-day calendar, FRED `DFEDTARU` (the target range upper bound) for policy steps.
1. For the event's rate date E and the day before it E1 (previous NY Fed business day): L = published SOFR(E1), the last print available at the look.
2. Calendar class of E (first match): **ME** E is the last business day of a month; **FB** the first business day of a month; **TAX** E is a business
   day on or the first business day after 15 Jan, 15 Apr, 15 Jun, 15 Sep, 15 Dec (corporate tax and coupon cluster); **MID** E is a business day on or
   the first business day after the 15th of any other month (mid-month coupon settlement); **MON** E is a Monday (the weekend carry is already in E1's
   successor), otherwise **OTHER**. A class with fewer than 20 calibration days is merged into OTHER (counted in the result).
3. From the calibration set, d(E) = SOFR(E) - SOFR(E1) in whole basis points. The class shift a(class) = the median of d over the class days with no
   change in `DFEDTARU` between E1 and E. The residual r = d - a(class) over all calibration days without a policy step, in whole bp. **Policy step:** if
   `DFEDTARU` on E differs from that on E1, add the announced change in bp as a known shift (a step counts as known, it is public the day of the FOMC).
4. Predicted SOFR(E) = L + a(class) + step, and the distribution of SOFR(E) is that value plus the empirical residuals r (all calibration days, one
   pooled set, at least 400 residuals else the series is NOT_RUNNABLE).
5. Probability of a bracket: p_model = (number of residual outcomes inside the bracket + 0.5) / (n + 1) where n is the number of residuals (a half
   count of smoothing, so no bracket gets 0). Brackets are the ones Kalshi lists on the event that day.
6. **Look:** the last hourly candle of each bracket that ends at or before 11:00Z on T (the publication is at 13:00Z, so nothing from the answer is
   in the quote). Signal ask = that candle's yes ask. If the market has no two sided quote at the look it is NoData (counted, not traded).
7. **Rule (cheap tail only):** a bracket is eligible if the signal ask is from 3c to 30c AND p_model >= 3 x the signal ask AND the next hourly candle's
   ask after the look is also at or below 0.30 and at or above 0.03 (the fill, taker, limit 0.30). Buy YES at that ask, one contract, held to
   settlement. If more than one bracket is eligible for an event, trade only the one with the highest p_model, ties broken by the lower ask. Buy-the-
   favourite is excluded by the 30c ceiling, and a NO side is never bought.
8. Fee, PF and P/L per the standing rules: 7% x C x p x (1 - p) rounded up with C = 10 (x1.2 stress), PF = gross wins over gross losses after fee.

## Numeric prediction (written now)
- Eligible brackets per event: about 0.10 to 0.25 (an event usually has a 1c to 10c tail bracket two bp away that the model also rates low). About 20
  events a month, so **2 to 5 treated trades a month.** Over the 41 pre-cut events (never read) the same rule would have treated about 5 to 15.
- Win rate on treated trades: the central guess is the ask (about 8%), range 3% to 15%, so that P/L per trade is about -0.4c to -0.7c after fee and
  the central PF is **0.8 (0.3 to 1.3)**. P(PF >= 1.5 at 150 treated) about 5%, P(NOT_ENOUGH_DATA at the first two read dates) about 99%.
- Pooled baseline for cheap-side entries is about -5.5c to -6.2c per contract; this is ratio-gated and not pooled, but a result near the baseline
  (here about -0.5c on an 8c average ask) would mean the model has no information beyond the quote.

## Kill criteria
- **NOT_ENOUGH_DATA** whenever fewer than 150 treated trades exist (certain on history, and the expected state until about 2030).
- **STOPPED_EARLY** at 30 treated trades if PF is under 1.0 after fee or either half (by event date, D1 = first half of the events counted, D2 =
  second half) has a non-positive mean, with 3 to 5 trades a month expected around **2027-05**; it ends the line, it does not count as FALSIFIED.
- **FALSIFIED** at 150 treated trades if PF is under 1.5 after fee (x1.2 stress as the reading, the plain fee as the report). A pass additionally
  needs both halves positive, a z against the pooled cheap-side baseline above the project's bar (about 5.3, running count below), the last third of
  the forward events (by date, frozen from the date of the 150th trade back: the final third of the events counted at that read) read once and positive,
  and the counterparty named in a result note. Nothing here can promote anything; the owner decides.
- No parameter, window, class or probability rule may be changed after the first forward trade. A change is a new registration and a new N.

## Data the forward read needs, and the read dates
- NY Fed SOFR and `DFEDTARU` (keyless, verified reachable), Kalshi KXSOFRD historical hourly candles (`yes_bid.close` and `yes_ask.close` fields on
  the historical endpoint, not `close_dollars`, per the 2026-10-31 ledger correction) and the settled result of each event. Candle fetches go to
  api.elections.kalshi.com (the external-api host 429s), spaced at least 1.2 s.
- **Known risk:** FEDIMPL1 found 71 of 168 registered markets had no candle on the day before; thin 1c to 10c brackets may have no hourly two sided
  quote at the look. If more than 50% of the cheap brackets are NoData the verdict is NOT_RUNNABLE on candles and the recorder proposal below is the
  only route.
- Read dates (decide nothing, informational unless a kill fires): **2027-02-01** descriptive count of forward events, brackets, NoData and eligible
  trades (no P/L printed); **2027-05-01** STOPPED_EARLY check at 30 trades (or the count if under 30); then every quarter. The final read is at
  150 treated trades. At 20 events a month the event count passes 100 around 2027-04 and 200 around 2027-09.

## N accounting
SOFR1 is one rule on one series, **N +1**. Running count about 730,441 after GOVSER1 (README) becomes about **730,442**, z bar about 5.27 to 5.3.

## Second registered try: KXTXERCOTPEAKD (ERCOT daily peak load), own count, CONDITIONAL
Contract (seen from the open event KXTXERCOTPEAKD-26NOV07): "the highest hourly total system load reported for the ERCOT grid on <day> is above X MW",
ladders of strikes in 500 MW steps, closing at 05:55Z of the following day (23:55 Central of the measured day, so the question is about a day that is
almost over at the close). 35 settled events before the cut (the brief). **Not runnable yet:** the only reference that was reachable in this session is
Open-Meteo's keyless temperature forecast (HTTP 200); ERCOT's own dashboard JSON path tried (`ercot.com/api/1/services/read/dashboards/daily-prorated.json`)
returned 404, and no keyless source of hourly ERCOT load history was verified, so the load model cannot be frozen. Registered as: ERCOT1 is **NOT_RUNNABLE
until a keyless load history and a keyless forecast are named and verified**, the rule form is fixed now (persistence of the same weekday peak of the
last 4 weeks plus a temperature regression, cheap tail 3c to 30c, model probability at least 3x the ask, one trade per event, held), its look would be
the last hourly candle at least 12 hours before the close, and the kill rules are the same as SOFR1's with its own count. **Because nothing is frozen,
no N is added for it.** If a source is verified, the constants are written in an amendment BEFORE any ERCOT quote is read and N +1 is added then.
Counterparty (doubted): retail guessing weather driven load; market makers and the grid's own day-ahead forecast (ERCOT publishes one) are likelier
to be better informed.

## Proposal for the owner (nothing built): what recording would make this readable sooner
Recording cannot make it readable sooner in event count: KXSOFRD produces one event a business day and 150 treated trades are a property of that rate,
not of the tooling. It can only make sure that every forward event is read at the registered look, which history cannot (hourly candles for thin
brackets are often missing, and the shared API limit makes ad hoc pulls fail).
- **What:** add KXSOFRD (and KXTXERCOTPEAKD if ERCOT1 ever becomes runnable) to the daily recorder on the review branch `claude/v2-recorder-daily`
  (`scripts/record_daily.py`, its watchlist and `workflow record-daily.yml`; the watchlist file is not on this branch). One public GET of the series'
  open markets per half hour on business days from 09:00Z to 13:00Z.
- **Cadence and fields:** every 30 minutes, 8 markets per event, fields: UTC timestamp, market ticker, yes bid, yes ask, bid size, ask size, last
  price, volume, open interest, close time. Plus one daily row of the NY Fed SOFR table (rate, 1st, 25th, 75th, 99th percentiles, volume) and the
  repo operation results, which are outcome free inputs.
- **Cost:** 1 request per half hour per series, about 9 per business day, 8 rows each, about 1,500 rows a month, a few hundred KB gzipped a year; GitHub
  Actions minutes are negligible beside the quote recorders; no key, no secret, no order. Off switch: delete the workflow.
- **What it would NOT do:** it would not shorten the 3 to 6 years to 150 trades. If the owner wants a decision sooner, the honest choice is to drop the
  line (kill at 30 trades) rather than record more.
