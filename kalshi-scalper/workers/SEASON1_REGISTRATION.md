# SEASON1: season-long win-total and standings ladders (NFL, MLB, NBA team wins) against a public standings calculator, cheap side, held to settlement

Written 2026-11-05 BEFORE any SEASON1 candle was fetched and before any result, price or standings figure was read. Worker ID SEASON1, session "Strategy Research V2". Research only: no order, no live code, no `functions/`, no promote verb. No em dashes. No credentials.
**Owner rules:** CHEAP SIDE ONLY (YES ask 3c to 30c, fee 7% x C x p x (1-p) rounded up, C = 10, taker at the ask, held to settlement). No favourite-and-hold, no NO on a likely-NO outcome, no 15 minute crypto or gold trigger. Never read the frozen last third (cut 2026-10-03T16:00Z).
**N: +1** (one rule, one try; running count about 730,443 before, so about 730,444; deflated z bar about 5.27).

## 1. Duplicate check (done before registering)
README and workers searched for: standings, season wins, KXNFLWINS, KXMLBWINS, KXNBAWINS, playoff, seed, relegation, MVP, Heisman, bracket. Only March Madness bracket one-offs (ELECT1 and earlier calibration lines) and CALIB1 category calibration touch season markets; no season win-total or standings ladder was ever tested. Other workers now running cover ladder coherence, weather sibling, stale quotes, maker on dailies, scheduled releases: not this.

## 2. Question and counterparty
Season-long ladders ("team X wins at least K games") resolve from a public scoreboard with a hard intermediate state: the team's record and games remaining. Outside fact: ESPN standings (keyless) give wins, losses and games left at any look date, so each strike has a known requirement (needs R more wins from G games). Counterparty: a casual holder of a long-dated future who does not update a cheap far strike as the standings tighten, and who over-prices miracle strikes (favourite-longshot bias). Model: P(reach K) = Binomial tail of G games with p = the team's own win rate to date shrunk 50/50 to 0.5 (NFL and NBA) or to .500 (MLB), a plain standings calculator, fitted on nothing.

## 3. Universe (chosen now, from the series list, before any outcome)
KXNFLWINS-<team> (32), KXMLBWINS-<team> (30), KXNBAWINS, KXNFLEXACTWINS-<team> ignored (exact bins). Settled events closing before the cut. Look: the last candle with a two-sided quote at least 21 days (MLB, NBA) or 14 days (NFL) before the market's close, one look per market. Cheap rung: ask 3c to 30c, YES only. At most 3 rungs per event, chosen by sha1 of the ticker (not by price or result).

## 4. Arms
- TREATED: model >= 3 x ask.
- CONTROL: every cheap rung at the same look, no model.
Statistic: net after fee per contract, event-clustered bootstrap, halves D1/D2 by close date, fees x1.2.

## 5. Numeric prediction
Census events before the cut across the three leagues about 100 to 130 with quotes at the look fewer (60 to 100). TREATED 15 to 50. Control net -4c to -7c per contract (the pooled cheap-side baseline). TREATED net -6c to +2c. P(pass) 3%.

## 6. Kill criteria
- NOT_ENOUGH_DATA: fewer than 100 settled events with a two-sided quote at the look, or fewer than 150 treated trades. I expect this verdict; the result then states the accrual needed (the 2026-27 NBA and NHL seasons end April 2027; a recorder of every win-total ladder from the start of the season would give 31 NBA events a year, so about 3 seasons to 100 events from NBA alone, which is why this family is not worth building a recorder for unless pooled with MLB and NFL, about 90 events a year).
- FALSIFIED: profit factor under 1.5 after fee, or net not above 0 in both halves, or treated not above control.
- LEAD only if all three pass with 150 or more treated and the lower bootstrap bound above +6c.
