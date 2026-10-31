# ECONNEW2 registration (Strategy Research V2, written 2026-10-31 BEFORE any AAA settled value was used, any candle was downloaded or any result was read; research only)

Owner decision relayed by the main session (Oct 30 evening): go on with the weekly AAA gas ladder against RBOB futures (A) and core PCE against the Cleveland Fed nowcast (B), the owner having opened economic releases.
Two angles, at most two tries. Code `src/scalper/econnew2.py` is committed and pushed with this file; `prep` (the discovery fit), `candles` and `run` come after. Nothing here means trade.

## What was looked at before this registration (disclosure)
Listing only: the settled-market listings of KXAAAGASW and KXPCECORE were downloaded (tickers, strikes, close times, `result`, `expiration_value`, volume come in the same listing). Printed: counts, event dates, the first and last four rows of each series (which show `expiration_value` for 8 AAA and 8 PCE markets; no model or price was joined to them) and the PCE rows' `expiration_value` as event-list lines (to check strike semantics: "above 0.3" with value 0.3 settles no). Yahoo RB=F daily bars were downloaded once and the first and last three bars printed. The Cleveland file already in `data/cpi1/` was inspected for series names (Core PCE Inflation, Actual Core PCE Inflation: present, 160 reference months from 2013-7). Nothing was scored.

## Ledger check (stop-if-reword)
- GAS1 (README "Pre-registration: GAS1, APP1 and CMD1", result: FALSIFIED, -7.50c, Brier 0.2351 vs market 0.0826) was the DAILY AAA ladder (`KXAAAGASD`) with a persistence model of the published number's own path and NO futures input; GAS1-F is its forward read (2026-11-22, gas persistence only, running and not touched here). **What is new in A:** the weekly ladder (`KXAAAGASW`, 138 usable weekly events, about 18,000 contracts a strike, not tested before), and wholesale gasoline (RBOB futures) as the information source: a pass-through lag from wholesale to retail. A persistence-only model is computed beside it as information so the RBOB term has to earn its place.
- CPI1 (README "Pre-registration: CPI1" and "CPI1 amendment") is the registered structure for B: Cleveland nowcast, empirical error distribution of earlier months (at least 36), vintage labelled strictly before the price candle's date, edge 5c, 24 hours before, held. **B is a reword of CPI1 on a new series (core PCE, `KXPCECORE`) with the owner's go-ahead, not a new mechanism.** CPI1 itself is VOID (parser bug, LEDGER CORRECTION) and its rerun is another worker's; this file does not touch `cpi1.py` or `ment1.py`.
- ECONNEW1 (claims, FALSIFIED) is a different series and model. Its loaders, fee and statistics functions are imported (`econnew1.fee`, `pnl`, `stats`, `line`, and `pick`, the fixed field parser: historical candles name fields `close`/`volume`).

## Counterparty and mechanism
A. Who loses: weekly AAA ladder buyers and makers who price off the posted AAA number and last week's drift, and who update slowly when wholesale gasoline has moved (retail follows wholesale with a lag of one to three weeks: "rockets and feathers"). The price they quote at the look is also set by people who see the daily AAA print and RBOB, so the prior that it is priced in is high; the model is blind to the daily AAA numbers of the days between the last settlement and the look (only the previous weekly settlement is public history here) and to the state of the retail pump, the very thing the market sees.
B. Who loses: as CPI1: traders who price a core PCE print off the previous month or the consensus and ignore what the nowcast reads from the CPI and PPI already released (core PCE is largely built from them); the nowcast is also public and widely read, so already priced in is the main risk.

## Angle A rule (all fixed now)
Series KXAAAGASW, `strike_type greater` ("above $K"; result yes when the AAA national average at settlement is above K). Event = one weekly settlement (close time; the old 2023 to 2024 format closes Monday 13:55 UTC, the new format Sunday 23:59 Eastern). The expiration_value of an event is the AAA settled value A(S).
1. Eligible event: the two previous events exist and their close dates are 5.5 to 8.5 days apart (so A(S-7) and A(S-14) are the previous two weekly settlements), and the RBOB bars exist. 138 events with a strike, 126 eligible (gaps in 2024 and early 2025 drop the rest).
2. Decision look L = close minus 24 hours. RBOB(d) = last Yahoo RB=F daily close with bar date (Eastern) strictly before the date d. x1 = RBOB(date of L) - RBOB(date of L - 14 days) (dollars a gallon; the Friday close for the weekend looks); x2 = A(S-7) - A(S-14).
3. Model, form fixed now: A(S) - A(S-7) = a + b1 x1 + b2 x2 + e. Coefficients by least squares on DISCOVERY events only, then frozen (never refitted in validation or holdout). Centre c = A(S-7) + a + b1 x1 + b2 x2. Residual set = the discovery residuals scaled by sqrt(n/(n-3)). Fair P(A(S) > K) = (count of residuals with c + e > K, plus 0.5) / (n + 1).
4. Universe (from the model and the strike, no price): strikes with fair between 0.10 and 0.90 of eligible events.
5. Quote: the last hourly candle ending at or before L with a valid bid and ask (0 < bid < ask < 1) at most 6 hours old. **Two-sided quoted spread at most 10c (registered now).** No trade-price fallback; no quote means no trade. Buy YES at the ask if fair - ask >= 0.05, buy NO at 1 - bid if bid - fair >= 0.05. Information only: 0.03 and 0.08.
6. One order of C = 10 contracts per qualifying strike, held to settlement. Fees 7% x C x p x (1-p) rounded up to the cent per order; stress fees x1.2.
7. Windows by market close date (first 60% / next 20% / last 20% of the 126 eligible events, 76 / 25 / 25): discovery closes before 2025-11-14 (events to 2025-11-10); validation 2025-11-14 to before 2026-05-08 (2025-11-17 to 2026-05-04); frozen holdout 2026-05-08 onward (2026-05-11 to 2026-10-26). The holdout is read only if both discovery and validation pass.
Known weakness, stated: RB=F is a continuous front-month series, so a monthly roll can put a contract-change gap into x1. It is not corrected (a fixed form decided before looking); the fit would show it as noise.

## Angle B rule (all fixed now; the structure of CPI1)
Series KXPCECORE, `strike_type greater`; reference month from the event ticker; release = market close (about 7:30 Central on the release day). 25 events with a strike (2022-12-23 to 2026-10-29; the series has gaps).
1. Nowcast: Cleveland Fed `nowcast_month.json` (public, no key), series "Core PCE Inflation"; vintage = the nowcast labelled with a date strictly before the date of the price candle. Actual = "Actual Core PCE Inflation" (unrounded). sha256 of the file is printed.
2. Error sample: (actual - last nowcast) over all EARLIER reference months in the file (expanding, at least 36). Fair = share of errors with vintage + e >= K + 0.05 (the print is rounded to one decimal and "above K" needs the rounded value over K).
3. Universe: every strike of an event (no model filter, as CPI1). Quote and rules 5 and 6 of A (24 hours before the release, spread at most 10c, edge 5c, YES at ask or NO at 1 - bid, C = 10, fee rounded per order, fees x1.2).
4. Windows by release date (first 15 / next 5 / last 5 of the 25 events): discovery releases to 2025-12-19; validation 2026-01-29 to 2026-05-28; holdout 2026-06-25 onward (2026-06-25 to 2026-10-29).
Information only: look-ahead check (nowcast RMSE by vintage age, as CPI1).

## Judging (both angles)
Profit factor first. n is independent releases (z clustered by event: `calibration.cluster_mean_z`), not strikes. Verdict words only.
- `FALSIFIED`: PF under 1.5 after fees in discovery (with at least 100 trades) or in validation (with at least 50 trades), or not positive at fees x1.2 in either, or pooled z under 5.27 (deflated bar at running N about 728,688) or pooled mean under +2.0c, or holdout PF under 1.5.
- `NOT_ENOUGH_DATA`: fewer than 100 trades in discovery or fewer than 50 in validation (and not already FALSIFIED by the line above). The PF is reported either way. Then the rule is registered forward-only below.
- `NOT_YET_FALSIFIED`: all of the above pass, then the holdout read. It would only permit a forward quote-based re-read, never a trade.
Windows, edge, spread cut, lead and universe are not changed after the result.

## Numeric predictions and kill criteria
A: model coefficients on discovery with b1 between 0.2 and 0.8 and R-squared under 0.4 (retail is noisy week to week); 150 to 400 trades; pooled PF 0.5 to 1.1; mean net -4c to +0.5c per contract; z between -3 and +1; model Brier worse than the market's. Prior of a pass under 3%. The market at 24 hours before sees the daily AAA print the model never has.
B: about 10 to 40 trades (130 markets, 5c edge, 10c spread cut), NOT_ENOUGH_DATA with PF anywhere; prior of a pass under 2%.
Kill: any line in Judging. No variant is run after the result.

## Forward-only registration (if B, or A, ends NOT_ENOUGH_DATA)
The same rule, unchanged, scored only on releases after 2026-10-31, read when the trades reach the minimum or on 2027-06-30, whichever is first; one-sided information only. Upcoming dates: claims are a different angle; PCE (October) Nov 25, then about monthly; the weekly gas ladder settles every Monday (next Nov 2, 9, 16, 23, 30).

## Tries
Two angles, one rule each (the information thresholds, the 72-hour and volume splits are shown, not tried). N + 2: running count about 728,690 (z bar 5.27).
Not L1: weekly and monthly economic and commodity-price markets held to their settlement days; no 15 minute window.
