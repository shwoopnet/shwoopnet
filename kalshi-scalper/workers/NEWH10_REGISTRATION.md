# NEWH10 registration (Strategy Research V2 worker NEWH10, 2026-10-30, research only)

Written and pushed BEFORE any NEWH10 rule was joined to a fill quote or to any outcome. Code `src/scalper/newh10.py` (committed with
this file); result `workers/NEWH10_RESULT.md`. Markets: the hourly ladders KXBTCD (Bitcoin) and KXGOLDH (gold), with the calendar
of US macro releases. Times are UTC in the code and US Central (CDT, UTC-5, the whole sample) in words.

## The question: does the ladders' width follow the clock?

An hourly "above K" ladder is a distribution; its width says how far the makers expect the price to move in the time left. Realised
volatility is strongly seasonal: Bitcoin is quiet at weekends and busiest in US cash hours; gold is quiet in Asian hours and busiest
in COMEX hours. A maker who sets width from a slow, clock-blind input (a 30 day implied volatility such as DVOL or GVZ, or a
trailing multi-hour realised figure) quotes the quiet hours too wide and the busy hours too narrow. Too wide means the 20c to 40c
wings are overpriced (buy the other side of that strike); too narrow means they are underpriced (buy the wing).

## Ledger check (what this is NOT)

- Not L1 (no 88c to 97c favourite held), no L1 exit, size, filter, hour or throttle test, not the cheap side late (every entry here is
  45 minutes before the Bitcoin close or 14 minutes before the gold close, never in the last minutes, and never a 5c to 15c side).
- **LAD1** (option fair value per strike on KXBTCD, DVOL or 60 minute realised): a model of each strike; NEWH10 uses no model and no
  spot price, only the clock, and asks one directional question about width per arm. **NARROW** (NEWH4): the ladder against its own
  centre's recent path, any hour. **TAIL** (NEWH4): 2c to 6c longshots at 30 minutes, all hours. **KINK**: one strike off the fitted
  curve. **NEWH7 IVGAP**: 15 minute cheap side when implied sits above realised (an index gap, not the clock). **S13** (weekend
  favourite on the 15 minute markets; a favourite, and not the ladder). **REGIME1 (b)**: skipping L1 at weekends. **ASIAGOLD, NYGOLD,
  BTC10AM** (NEWH9): a DIRECTION drift at the 15 minute open in a session; NEWH10 takes no view on direction (the wing is whichever
  strike sits nearest 30c, above or below the money). **EVT1**: macro releases on the 15 minute markets (sides at 360 s and 180 s);
  the macro release here is on the hourly ladder, and only as information (below).
- **A disclosure on the "expensive side" arms (WKNDWIDE, ASIAWIDE):** they buy a 58c to 82c side and hold it. That is outside L1's
  band and is motivated by width, not by "favourites win"; the lead should strike them if they read the owner's 2026-10-28
  instruction as covering any side above 50c. The two "cheap wing" arms are not affected.
- **Holdout overlap:** LADFADE read NEWH9's frozen holdout (2026-10-18 to 2026-10-30), which included KXBTCD quotes in the first
  minute of 15 minute windows opening :15 and :30 joined to KXBTC15M outcomes. That is a different rule and a different market's
  outcome; KXBTCD outcomes in the holdout have not been scored by any rule on this clock. Stated, not hidden.

## What was looked at before this was written (disclosure)

Ledger sections listed in the brief (RULES, DIRECTOR_2026-10-30, NEWH9 registration, result and code, README NEWH1 to LADFADE,
LAD1, NEWH4 registration and result, EVT1 registration, the weekend and momentum entries). Data: `python -m scalper.newh10 counts`
(events per arm by close time only; no quote and no result read):

| Arm | discovery | validation | holdout |
|---|---|---|---|
| WKNDWIDE btc (KXBTCD events) | 192 | 167 | 72 |
| USNARROW btc | 133 | 140 | 56 |
| ASIAWIDE gold (KXGOLDH events) | 152 | 156 | 55 |
| USNARROW gold | 133 | 135 | 49 |
| I1 weekday twin of WKNDWIDE | 464 | 464 | 185 |
| I2 13:00 UTC close on a macro release day / other weekdays | 8 / 11 | 7 / 13 | 2 / 6 |

23 release days in the calendar carry an 8:30 ET (7:30 AM Central) release (CPI, PPI, jobs, GDP, PCE, retail, claims).

## Common to every rule (fixed now)

- **Windows by close time (UTC):** DISCOVERY 2026-08-06 to 2026-09-21; VALIDATION 2026-09-21 to 2026-10-18; HOLDOUT 2026-10-18 to
  2026-10-30 (frozen: read once, ONLY for a rule that passed discovery and validation, after that result is committed and pushed).
- **Universe:** every settled hourly event in the local files, chosen by close time only: KXBTCD from `conf2_lad.sqlite` then
  `lad2.sqlite` (first file wins per close), KXGOLDH from `newh2_goldh.sqlite`. Their strike sets were fixed by the fetch rules
  (quotes 55 to 52 minutes before the close for Bitcoin; within $12 of the 15 minute strike fixed 15 minutes before the close for
  gold), before any signal time used here.
- **The wing rule (one trade per event).** Signal candle: the 1 minute candle ending L seconds before the close (Bitcoin L = 2,700,
  i.e. 45 minutes left; gold L = 840, 14 minutes left, the first candle in the gold file). Among strikes with 0 < bid < ask < 1 and
  ask minus bid at most 3c, take the cheap side's mid c = min(m, 1 - m) with m the YES mid; keep c in [0.20, 0.40]; the wing strike
  is the one with c closest to 0.30 (ties: the lower strike). No such strike: "no wing", counted.
  - **"exp" arms** buy the side whose mid is above 0.5 at that strike; fill band [0.58, 0.82].
  - **"cheap" arms** buy the other side (the wing); fill band [0.18, 0.42].
  - **Fill:** that side's ask on the candle ending L - 60 s before the close (the NEXT candle), never the signal candle's quote;
    outside the band "band", missing "no fill", both counted. Held to settlement; nothing is sold.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order. Headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose signal or fill candle had volume 0.
- **Bar (each rule):** PF at C = 10 at least 1.5 in EACH of the three windows, net positive at fees x1.2 in each, at least 100 / 50 /
  30 trades (discovery / validation / holdout), a named counterparty, and pooled day-clustered z at least the deflated bar.
  **N:** running count after LADFADE about 627,846, plus 6 here = **about 627,852**; one-sided Bonferroni z bar at 0.05 **5.24**.

## H1 WKNDWIDE-BTC (1 try): the Bitcoin ladder is too wide at weekends

- **Rule:** KXBTCD events closing Saturday or Sunday UTC (Friday 7 PM to Sunday 7 PM Central). Wing rule, "exp", L = 2,700.
- **Counterparty:** ladder makers whose width comes from a weekday-weighted input (DVOL, multi-day realised) and the takers who buy
  the 20c to 40c wings at weekend prices; at weekends realised Bitcoin volatility is lower, so those wings settle in the money less
  often than priced.
- **Honest alternative:** makers of a 24/7 product with a large weekend share know the weekend effect and set width from recent
  minutes, not a 30 day index (LAD1 found a flat model no better than the book); weekend volume is lower, spreads may be wider.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.10 at C = 10, win rate within 3 points of the price paid.

## H2 USNARROW-BTC (1 try): the Bitcoin ladder is too narrow in US cash hours

- **Rule:** KXBTCD events closing 14:00 to 20:00 UTC (9 AM to 3 PM Central), UTC Monday to Friday, not 2026-09-07. Wing rule,
  "cheap", L = 2,700.
- **Counterparty:** the same makers on the other side of the day: in US cash hours (equity open, macro data, ETF flow) Bitcoin moves
  more than a clock-blind width allows; whoever sells the wing at that price pays.
- **Honest alternative:** the favourite-longshot pattern on these ladders (TAIL, KINK) runs the other way; a 30c wing is a mild
  longshot and may be overpriced in every hour.
- **Prediction:** FALSIFIED; discovery PF 0.80 to 1.05. Funnel risk: under 100 discovery trades gives NOT_ENOUGH_DATA.

## H3 ASIAWIDE-GOLD (1 try): the gold hourly ladder is too wide in Asian hours

- **Rule:** KXGOLDH events closing 01:00 to 08:00 UTC (8 PM to 3 AM Central), Beijing date Monday to Friday. Wing rule, "exp",
  L = 840.
- **Counterparty:** gold ladder makers using one width across the day (GVZ or a day-long realised figure), and takers of the wings in
  the quiet Asian hours.
- **Honest alternative:** with 14 minutes left the strikes near 30c sit close to the money and the price is mostly the spot distance,
  not the width; the gold file's strikes are only the ones within $12 of the 15 minute strike.
- **Prediction:** FALSIFIED; discovery PF 0.85 to 1.10.

## H4 USNARROW-GOLD (1 try): the gold hourly ladder is too narrow in US hours

- **Rule:** KXGOLDH events closing 14:00 to 20:00 UTC (9 AM to 3 PM Central; COMEX day session and the 1:30 PM ET settle), UTC
  Monday to Friday, not 2026-09-07. Wing rule, "cheap", L = 840.
- **Counterparty:** as H3, on the busy side of the day.
- **Prediction:** FALSIFIED; discovery PF 0.80 to 1.05.

## Information looks (counted in N, never a rule, never screened)

- **I1:** H1's rule on weekday KXBTCD events (discovery and validation only): the weekend effect is the difference, if any.
- **I2, macro release hour (the brief's macro family on the ladder):** KXBTCD events closing 13:00 UTC (8 AM Central) on the 23
  release days against other weekdays; signal candle ending 12:25 UTC (35 minutes left, 5 minutes BEFORE the 12:30 UTC release),
  fill at 12:26 UTC: the median probit width s of the ladder, and the cheap wing rule's win rate against price. At most 15 release
  events in discovery and validation, so this can never be a rule (the bar needs 100); it only says whether the makers widen before
  a release. Gold's hourly file starts 15 minutes before each close (after the release), so gold has no pre-release look.

## Declined, no try spent

- **Macro releases on the 15 minute windows that contain or follow the release:** EVT1 ran exactly this (sides at 360 s and 180 s,
  containing, before and after windows, the pooled MACRO0830 group) and found 1 to 7 windows per release type: NOT_ENOUGH_DATA. A
  re-run is a variant and cannot gain data on history.
- **Gold daily and weekly ladders (KXGOLDD, KXGOLDW) implied against realised width:** about 60 daily closes in all of history (38
  held locally, two looks each in `ladl1.sqlite`) and 9 weekly; one independent close a day cannot reach 100 discovery trades without
  pooling correlated strikes (NEWH4 reached the same conclusion). NOT_RUNNABLE at this bar; a forward recorder (`ladder.csv` on the
  quote-data branch already polls KXGOLDD and KXGOLDW near their close) is the only path.
- **Implied against realised on the Bitcoin hourly ladder with a model:** LAD1 (DVOL and realised, 45, 30, 15 minutes), NARROW and
  the NEWH7 brief's family A (judged a restatement of LAD1). Not re-run.
- **Weekend Bitcoin 15 minute windows:** S13 (weekend favourite) and REGIME1 (b) cover the favourite; QUIRK1 covers every first-
  candle side pooled; the 15 minute contract at the money is insensitive to width, so the weekend-width story belongs on the ladder
  (H1), not there.

## Kill criteria (each try, no parameter changes after any score)

- Discovery: fewer than 100 trades NOT_ENOUGH_DATA (validation printed for the record). PF at C = 10 under 1.5, or net at fees x1.2
  at or below 0: FALSIFIED.
- Validation (after a discovery pass): fewer than 50 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
- Holdout (after both passes, read once): fewer than 30 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
  All PF gates met but pooled day z under the deflated bar: NOT_ENOUGH_DATA. All gates met: NOT_YET_FALSIFIED (forward registration
  only).

## Count

N tried: **4** (WKNDWIDE btc, USNARROW btc, ASIAWIDE gold, USNARROW gold) + 2 information looks (I1, I2) = **6**.
Running count about 627,846 (after LADFADE) + 6 = **about 627,852**. Deflated z bar 5.24.
