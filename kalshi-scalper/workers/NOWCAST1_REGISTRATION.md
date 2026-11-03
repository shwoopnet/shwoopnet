# NOWCAST1 registration: macro release ladders against a public nowcast, cheap side only, ratio rule (Strategy Research V2, discovery lane, research only)

Written 2026-11-03, BEFORE any GDP candle was fetched and before any NOWCAST1 trade was formed. No live code, no `functions/`, no L1, no OICORE, no promote verb. Nothing here means trade.

## Ledger check (what is covered, where it died)
- **CPI1** (README, "Pre-registration: CPI1"; rerun result 2026-10-31): Cleveland Fed nowcast against Kalshi CPI and core CPI month-over-month strikes, 47 independent releases, 240 trades, PF 1.11, z +0.46: FALSIFIED. Rule there: BOTH sides, edge of 5c or more, any price. Its data (hourly candles, nowcast vintages) is cached in `data/cpi1/`.
- **ECONNEW2 angle B** (core PCE against the Cleveland core PCE nowcast, same 5c both-sides rule): NOT_ENOUGH_DATA (26 releases, about 1.5 trades a release pair). Data cached in `data/econnew2/`.
- **ECONNEW1**: weekly claims against a persistence model (not a nowcast): FALSIFIED. Payrolls and unemployment: NOT_RUNNABLE (no free consensus or nowcast; the Cleveland Fed publishes none for jobs).
- **EVENT1 / EVT1 / EVENT830**: the 15 minute series around 8:30 ET releases; a different object (no outside price).
- **MORTGAGE1** (weekly mortgage ladder from the 10 year yield) and **PUB20**/**XMET1**: other ladders, other sources.
- **Not tested before:** (1) **GDP** (KXGDP, quarterly) against **Atlanta Fed GDPNow**. (2) The **cheap-side ratio rule** (ask 3c to 30c, nowcast probability at least 3 times the ask, hard limit 0.30, one trade per release-series) on any of these. CPI1 and ECONNEW2 priced both sides at any price against a 5c edge; the cheap-side rule is the OICORE shape (a longshot priced low against an outside reference). Because (2) re-uses CPI1 and ECONNEW2 data with a different rule, it is a NEW try on seen data: its outcome is not independent of CPI1's, and that is disclosed, not hidden.

## Mechanism and counterparty
A nowcast encodes high-frequency inputs (gasoline, oil, food, weekly claims, trade, inventories) that a ladder priced off the last print under-uses. The loser would be a retail buyer or maker anchored on the last print or on a round consensus, who sells the tail strike too cheaply. **Prior of a pass: under 3%.** CPI1 found the quotes fairly priced; the ordinary longshot bias on a cheap side (a 10c ask wins less than 10% of the time, EVENT1 controls, SWING1 control) is the strong contrary evidence, and a GDP ladder is watched by the same desks that publish GDPNow.

## Universe (fixed now)
Four release-series, "greater than T" strikes only (`strike_type == greater`), reference value printed to one decimal so YES means value >= T + 0.05:
1. `CPI` / `KXCPI` headline month over month; nowcast Cleveland Fed `CPI Inflation`, exactly as `src/scalper/cpi1.py`.
2. `CPICORE` / `KXCPICORE` core month over month; Cleveland `Core CPI Inflation`.
3. `KXPCECORE` core PCE month over month; Cleveland `Core PCE Inflation` (as `src/scalper/econnew2.py`).
4. `KXGDP` / `GDP` quarterly GDP growth (advance estimate; events with "greater" strikes, 2023-04 on); nowcast = FRED series `GDPNOW` (Atlanta Fed GDPNow, last update of the quarter, public CSV, `fredgraph.csv?id=GDPNOW`, fetched with curl --http1.1).
Year-over-year CPI, jobs, unemployment: left out (no public nowcast; the Cleveland YoY file exists but YoY strikes are not on the ladder list found, and payrolls/unemployment have no nowcast).

## Nowcast and error sd (fixed)
- CPI family: the last Cleveland vintage labelled strictly before the price candle's date (cpi1 rule); probability = Normal(nowcast, sd), P(x >= T + 0.05); **sd = standard deviation of the expanding history of (actual minus final nowcast) for earlier reference months**, at least 36 earlier months else the release is skipped (cpi1/econnew2 rule), floor 0.04.
- GDP: Normal(GDPNow, **sd = 1.2 percentage points, fixed ahead of looking** (the Atlanta Fed's published RMSE of the final nowcast against the advance estimate is about 1.2); the sd actually observed on the settled brackets is information only). Honest caveat: FRED holds only the LAST GDPNow value per quarter, which is the update on the day before the advance release; the price look is 24 hours before the close, so the nowcast can include up to about one update that came after the price. That flatters the GDP leg slightly (no way to remove it from FRED); the forward run has no such issue.

## Look (ONE, registered)
The last hourly candle ending at or before **24 hours before the market's close_time** (the release), with a two-sided quote 0 < bid < ask < 1 at most 6 hours old, spread (ask minus bid) at most 0.10. (The 60 minute look was not registered: the cached candles stop 20 hours before the close.)

## Rule (ONE)
For each release-series, among its strikes: YES candidate if the ask is 0.03 to 0.30 and nowcast probability p >= 3 x ask; NO candidate if (1 - bid) is 0.03 to 0.30 and (1 - p) >= 3 x (1 - bid). **Hard limit 0.30**: a candidate priced above 0.30 is no trade. If several qualify, take the one with the highest ratio (tie: lower price); **one trade per release-series**. Fill at the quoted ask (an assumption from a quote, not a fill; no volume check: reported as information only), held to settlement.

Fee 7% x C x p x (1-p) rounded UP to the cent per order, **C = 10**, also fees x1.2 shown. Net per contract in cents.

## Windows (dates only, fixed before any price)
Eligible release-series (market listing, nowcast and 36 error months exist) sorted by release close time: first two thirds = DEVELOPMENT, split into **H1 and H2 by count**; **last third = FROZEN HOLDOUT, unread** (the run refuses to compute it; the cutoff date is printed by `prep`, which uses no price, and pushed before the run). A holdout read needs a new registration.

## Numeric prediction (before any outcome)
Eligible release-series about 100 to 115 (CPI1 had 47 releases for headline and core, ECONNEW2 26 for core PCE, about 12 for GDP; `prep` prints the exact count), cheap-side qualifying rate 25% to 45%, so **n of 20 to 45 development trades on 20 to 40 distinct release dates**. Win rate 8% to 18% against an average price near 14c (win rate minus price between -6c and +4c). **PF central 0.8, range 0.4 to 1.4**; mean net -2c per contract (range -8c to +6c). Probability PF >= 1.5 in development: 8%. Probability mean net above 0 in both halves: 18%. Probability of passing the deflated bar (z 5.27): under 1%. With wins of 15c to 40c on a 10 to 20c price the PF is driven by one or two lucky releases (clustered: headline CPI, core CPI and core PCE of one month share an outcome driver).

## Kill rules
- **FALSIFIED**: mean net after fees not above 0 in BOTH halves of what exists (development H1 and H2), or pooled development PF under 1.5.
- **NOT_ENOUGH_DATA**: under 150 trades (or under 100 development trades) regardless of PF; the output then states months to 40 forward fills and a forward freeze line.
- NOT_YET_FALSIFIED only if 150 trades, PF >= 1.5 in each half, release-clustered z >= 5.27 (deflated) and a named counterparty survives. Not reachable on this sample; the honest ceiling is NOT_ENOUGH_DATA or FALSIFIED.

## Tries counted
One rule scored once. **N +2** (running about 730,010 before; about 730,012 after). Information-only cuts (per series; ratio 2 and 5; spread cap off; fees x1.2) are shown, not tried. Expected read date: 2026-11-04 (cached data plus about 170 GDP candle downloads).

## Forward plan if NOT_ENOUGH_DATA
Release dates (US Central, 7:30 am; GDP 7:30 am): CPI Nov 10 (October CPI), core PCE and GDP (Q3 second estimate) Nov 25 (Q3 advance already settled 2026-10-29), CPI Dec 10, core PCE Dec 23 (to be confirmed from BEA). A candidate JSON in `workers/candidates/NOWCAST1.json` (EVENT830 pattern) freezes the rule; the forward look is 24 hours before each release. Releases per month 2.6 (CPI head+core, core PCE), GDP 0.33 a month.
