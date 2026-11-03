# FEDIMPL1 registration: cheap outcomes of Kalshi's FOMC markets against a rate implied by Treasury bill yields (Strategy Research V2, research only)

Written 2026-11-03, BEFORE any Kalshi FOMC candle price or any meeting outcome was read. Discovery lane, nothing here means trade, no promote
verb, touches no live code, `functions/`, L1 or OICORE. Disclosure of what was seen before writing: the series list and market metadata (tickers,
strikes, close times, rules text), one live far-dated quote (Jan 2028), and the settled result text of the Jun 2026 KXFED and Jul 2026 KXFEDDECISION
events while checking field names. No price or result of any scored meeting was used to choose anything below. The reference-yield CSVs from FRED
(DFF, DGS1MO) are outcome-free inputs and the model constants below were fixed before they were joined to any Kalshi price.

**Plain statement.** The likeliest result is NOT_ENOUGH_DATA, with a real chance of FALSIFIED. FOMC outcomes are among the best-forecast events there are
(the market is almost always priced at 90% or more on the winner a day ahead), so cheap outcomes are mostly priced at 1c to 3c and fall outside the
3c floor. Eight meetings a year cannot reach 150 trades inside the project's horizon.

## Ledger check (what is covered)
- ECONNEW1 (`workers/ECONNEW1_LEDGER_CHECK.md` row (c), `ECONNEW1_RESULT.md`): FOMC decision against the Atlanta Fed Market Probability Tracker was
  judged NOT_ENOUGH_DATA and **not run, not registered**: no model, no price, no trade was ever scored. It named KXFEDDECISION (150 markets, 30 events from
  2023-05) and KXFED (424 markets, 42 events from 2021) as NEW. Its reference was the Atlanta Fed xlsx and its bar was 25 independent events.
- EVENT1 / EVENT830 / EVT1 / CAL: 15 minute markets in the window of the 14:00 ET statement (FOMC group 0 or 2 trades). A different contract.
- CPI1, ECONNEW1 (a), ECONNEW2, XMET1: CPI, claims, gas, other metals. Not FOMC.
- `workers/OICORE_SHAPE_INVENTORY.md`: OICORE is a 15 minute shape, not rates.
- Search of README and `workers/` for FEDIMPL, FED, FOMC, KXFED, RATES: no registration, result or code for a rate-implied FOMC price test exists.
**Different here:** the reference is the Treasury 1 month bill yield against the effective fed funds rate (FRED DGS1MO and DFF, keyless), a score is
produced for every meeting that has candles, and a forward rule is frozen. Covered and NOT re-run: the Atlanta Fed tracker route (same information,
less convenient). Other rates series: Kalshi's Treasury yield markets are hourly or 15 minute and the only keyless reference (FRED DGS10 and friends)
is a once a day close, so KXTNOTE and the hourly 10 year are **NOT_RUNNABLE** here (no intraday reference); recorded, not tested.

## Universe (fixed)
Two series, one rule each. **R1 = KXFEDDECISION** (and its earlier name FEDDECISION), the five outcome markets of each meeting: Cut >25bps (C26), Cut 25 (C25),
Hold (H0), Hike 25 (H25), Hike >25 (H26). **R2 = KXFED** (earlier name FED), the "upper bound of the target range above K%" strikes of the same meeting,
restricted to the 5 strikes K = U0 - 0.25, U0, U0 + 0.25, U0 + 0.50, U0 - 0.50 (U0 below), chosen from the reference rate alone. Meeting set: every
meeting that has a KXFEDDECISION event, decision date D = the date (US Eastern) of the event's market close_time. Meetings are the unit of
clustering (one meeting is one independent draw; R1 and R2 trades of the same meeting are the same cluster, so the cluster count, not the trade count,
sets the z).

## Reference and model (constants frozen now)
- r_eff(D-1) = FRED DFF on the last date before D; r_bill(D-1) = FRED DGS1MO on the same date (percent).
- Bill-to-policy spread s = median of (DGS1MO - DFF) over the trading days in [D-40, D-33] (calendar days); needs at least 4 observations else the
  meeting is not scored (counted).
- Expected change **E = 100 x ((r_bill - r_eff) - s)** in basis points. (The one month bill spans the whole month after the meeting, so its yield above the
  spread-adjusted funds rate is the market's expected move. The spread s removes the usual bill-over-policy gap measured before the meeting could matter.)
- Realised change Δ ~ Normal(E, sigma = 10 bps). Cells: C26: Δ <= -37.5; C25: -37.5 < Δ <= -12.5; H0: -12.5 < Δ < 12.5; H25: 12.5 <= Δ < 37.5; H26: Δ >= 37.5.
- Current upper bound U0 = L0 + 0.25 where L0 = 0.25 x floor((r_eff - 0.04) / 0.25). For R2, P(upper bound after > K) with K - U0 = 25j bps is
  1 - Phi((25j + 12.5 - E)/10).
sigma 10 and the 12.5 cell edges are the standard two-point (FedWatch style) approach with one noise term; they are not tuned.

## Look, signal, trade (one look, fixed)
- Look: the **last business day before D** (the day before the decision). Signal = the last hourly Kalshi candle ending at or before **19:00 UTC** that day, with
  0 < bid < ask < 1 and ask - bid <= 0.10 (else the market is skipped, NoData, counted). Fill = the next hourly candle (ending at or before 20:00 UTC) at its
  ask, **HARD LIMIT 0.30**: a fill ask above 0.30 or below 0.03 is no trade.
- Buyable contract = the YES side if its signal ask is 0.03 to 0.30, else the NO side if its signal ask (1 - YES bid) is 0.03 to 0.30 (at most one side per market,
  YES first). Model probability p_model of that contract (YES: cell probability; NO: 1 minus it).
- **Rule: buy if p_model >= 3 x signal ask.** Held to settlement. Taker at the ask. **Fee 7% x C x p x (1-p) rounded up to the cent per order**, C = 10 contracts,
  also priced at C = 1; fees x1.2 shown. The banned buy-the-favourite-and-hold family is NOT tested: the cap of 0.30 on the ask is the cheap side only.

## Frozen holdout
Meetings are sorted by D. The **first two thirds** (rounded up) are scored; the **last third is a frozen holdout, unread** by this registration and
by `fedimpl1 run`. It is read once, later, only after a pre-registered amendment, and its first meeting date is printed by the run.

## NUMERIC PREDICTION (before any price)
- Meetings scored (first two thirds): about 19 to 21 of about 30.
- Trades in the scored set (R1 and R2 together, C counted per order): **9 to 40, central 20** (the 3c floor and the 3x rule remove most meetings).
- Win rate **10% to 25%**, mean net per contract -3c to +4c, central -1c, PF **0.4 to 1.6, central 0.8**. P(PF >= 1.5) at this size: 12%. P(both halves positive
  mean) 20%. P(verdict FALSIFIED) 45%, P(NOT_ENOUGH_DATA) 55% (NOT_ENOUGH_DATA takes precedence when n < 150, so the written word is NOT_ENOUGH_DATA with a
  STOPPED_EARLY flag if the early rule fires).
- Months to 40 forward trades, from the scored trades per meeting t: 40 / (t x 8 / 12) months; central 15 to 30 months. 150 trades: 4 to 8 years.

## KILL RULES (fixed)
- **NOT_ENOUGH_DATA** under 150 trades (clustered on meetings, with months-to-go printed).
- **STOPPED_EARLY (FALSIFIED)** at 30 or more trades if PF (C = 10, after fees) is under 1.0, or if the mean net is not above 0 in both halves of the scored meetings.
- **FALSIFIED** at 150 trades if PF is under 1.5, or mean net not above 0 in both halves, or fees x1.2 PF at or under 1.0.
- A pass would need the deflated bar: N about 730,044 tried, one-sided z bar about 5.27 on the meeting-clustered mean; below it the word is NOT_YET_FALSIFIED, never a pass.
- A positive result in both halves only earns a capped-probe SPEC (below); no promote verb.

## N tried
Two rules (R1, R2): **N +4** (+2 per rule). Running count about 730,040 -> 730,044. Per-meeting, per-outcome tables are reports. Re-running the scorer is refused
(`fedimpl1 run` writes `data/fedimpl1_result.txt` once).

## Forward plan (frozen with the rule)
Meetings after the freeze (2026-11-03): **2026-12-09** (Wed), then 2027-01-28, 2027-03-17, 2027-04-28, 2027-06-16, 2027-07-28 per Kalshi's listed
events (decision date = close_time date; checked against the live listing, not from memory). For each, the look is the business day before, and `python -m
scalper.fedimpl1 forward` prints the signal and trade at that look (fetching the candles then) for the ledger. Nothing is placed.

**Amendment 1 (2026-11-03, before any price read; dates only, rule unchanged).** The forward list above had dates from memory in three places. The live listing's
close_time dates are: 2026-12-09, 2027-01-27, 2027-03-17, 2027-04-28, 2027-06-09, 2027-07-28, 2027-09-15, 2027-10-27, 2027-12-08. These replace the list above (the README line already has them).
