# POWER TABLE: calendar time to a decidable test for the forward-only ideas (Nov 12, 2026)

Offline desk analysis. No network, no Kalshi read, no held-out script read or run, no live account figure. Inputs are only the counts and rates written in IDEA_BACKLOG.md, CARDS_NOV11_ROWS_74_93.md, POLITICS_CARDS_NOV11.md, POLITICS_STEP2_RESULTS (the copy in the folder holds a removed figure, nothing usable), NEWS_FADE_REGISTRATION.md, ELECTIONS_CENSUS.md, DERIBIT_LADDER_REGISTRATION.md, ROW75_WXREVISE_REGISTRATION_AND_RESULT.md, NO_ARM_APPROVAL_REGISTRATION.md and POLITICS_APPROVAL_CAL_RESULT.txt. Where a file does not state a rate the cell says UNKNOWN; nothing was invented. Scratch: scratchpad/w_power/calc.py.

## Formulas and assumptions

1. Per-trade standard deviation s = 35c per contract for every idea (the instruction's default; no file gave a better public-data figure). The real s of a mid-priced binary is near 50c and of a 90c favourite is about 30c, so 35c is a middle value.
2. Edge e = mean net cents per contract per trade after fee. Profit factor from a mean e under a normal approximation: mean absolute result A = s * sqrt(2/pi) = 27.9c; PF = (A + e) / (A - e). So e = 5c gives PF 1.44, e = 10c gives PF 2.12, and PF 1.5 needs e = 0.2 * A = 5.6c. The 5c and 10c rows therefore bracket the PF 1.5 target (5c is a little under it, 10c well over it).
3. Trades needed for a mean test: n = ((z + z_power) * s / e)^2. Columns use z_power = 0 (a true edge of exactly e only just clears the bar, 50 percent power; the minimum, not a comfortable n).
   - Shared Bonferroni bar: z = 4.55 (N about 9,459, two-sided 0.05; the files also quote 4.553 at N 9,465 and 5.2 in older text).
   - Plain 90 percent interval above zero: two-sided 90 percent lower bound above 0, z = 1.645.
4. Resulting n (trades, independent units): Bonferroni 5c = 1,015, Bonferroni 10c = 254, 90 percent 5c = 133, 90 percent 10c = 34. With 80 percent power (z_power 0.842): 1,425 / 357 / 304 / 76. Use these if you want a test that usually finds a real edge.
5. Weeks = n / events per week. The unit must be an independent trade (one per event, night, city-month or hour); correlated trades shrink the effective n, so every weeks figure is a floor.
6. Minimum rate to decide inside 26 weeks = n / 26: Bonferroni 10c needs 9.8 a week, Bonferroni 5c 39.0, 90 percent 10c 1.3, 90 percent 5c 5.1.
7. FLAG rule: "effectively untestable on Kalshi alone" if the weeks exceed 26 for the Bonferroni bar at a 10c edge (the best case for the shared bar). A second flag, "weak bar also untestable", is added if even the 90 percent bar at 10c exceeds 26 weeks.
8. Rates marked (derived) come from arithmetic on counts in the files (stated in the cell); rates marked (stated) are written in the file; UNKNOWN is UNKNOWN.

## Table

Columns W-B10 / W-B5 / W-C10 / W-C5 are weeks of forward logging at the stated rate for: Bonferroni at 10c, Bonferroni at 5c, 90 percent interval at 10c, 90 percent interval at 5c. "min rate" is the events a week that would be needed for W-B10 to be 26.

| Idea (file) | Status in the files | Events/wk and source | W-B10 | W-B5 | W-C10 | W-C5 | Flag |
|---|---|---|---|---|---|---|---|
| NEWSFADE (NEWS_FADE) | REGISTERED, FORWARD ONLY; jump count unknown; no headline history exists | UNKNOWN. Its own kill rule (under 40 matched events per third within 12 weeks) implies it needs about 10 a week to survive step 0 (derived). Cells are split 36 ways, so a single cell sees far fewer | UNKNOWN (needs 9.8/wk in one cell) | UNKNOWN | UNKNOWN | UNKNOWN | Not decidable until step 0 gives a rate; with 36 cells, likely untestable |
| NO-arm approval (NO_ARM_APPROVAL, POLITICS_APPROVAL_CAL_RESULT) | UNDERPOWERED (no cell reached n 30 in both thirds; 8 of 263 KXAPRPOTUS events and 0 of 143 KX538APPROVE events had candles) | UNKNOWN. File gives event counts per series (development 306 events; newest third frozen) but no events a week. Limit is the candle pull and the cut, not only the calendar | UNKNOWN (needs 9.8/wk) | UNKNOWN | UNKNOWN | UNKNOWN | Not a forward-rate problem; unlocks only by a larger pull, then the frozen held-out read |
| DERIBIT ladder, W-DERIBIT1 (DERIBIT_LADDER) | DATA_LIMITED if n under 80 (bar n 80 independent hours); not a verdict yet | at most 168 hourly closes a week (stated: 24 a day, one trade per hour); real coverage and the 6c edge hit rate UNKNOWN (the file removed it) | 1.5 at the 168 ceiling | 6.0 at ceiling | 0.2 | 0.8 | At the ceiling it is fast; the real rate is likely well under 25 percent of that and consecutive hours are not independent. Bar fixed at n 80 in the file; its PF 1.3 bar is not the z bar |
| Row 75 WXREVISE (ROW75) | DATA_LIMITED and DROPPED by the card's own existence test | 2.6 revisions of 2 F or more a week (derived: 3 in 8 days = 0.4 a day), but 0 of 3 were lagged, so tradable events observed = 0 | 98 (at 2.6) | 390 | 13 | 51 | Untestable on Kalshi alone: even at the unlagged 2.6 a week it needs 98 weeks, and the lag test needs 10 minute looks the held data lack |
| Row 87 ECONFADE (IDEA_BACKLOG) | DATA_LIMITED, forward shadow only | 0.15 events a week implied by the file's own "about 5 years" for 40 events (derived). Observed rate is worse: 1 shock event in 26 print days | 1,700 | 6,800 | 227 | 890 | Effectively untestable on Kalshi alone |
| Row 89 QUAKE-M7 (CARDS) | NOT_ENOUGH_DATA, forward shadow; 5 settled, 12 a year | 0.23 (stated: one a month) | 1,100 | 4,400 | 148 | 580 | Effectively untestable on Kalshi alone (the card itself says about 7 years for 40 per half) |
| Row 91 ENSO-CPC | NOT_ENOUGH_DATA; about 12 events a year | 0.23 (stated) | 1,100 | 4,400 | 148 | 580 | Effectively untestable on Kalshi alone |
| Row 90 GSTORM-KP | NOT_ENOUGH_DATA; 9 settled | UNKNOWN (markets are monthly in the text, so at most 0.23 a week by inference, not stated) | UNKNOWN (at most 0.23: 1,100) | UNKNOWN | UNKNOWN | UNKNOWN | Effectively untestable on Kalshi alone even at the upper bound |
| Row 93 LMARENA-HIGH | NOT_ENOUGH_DATA; 2 settled; PARKED on terms | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Parked; 2 settled events, effectively untestable |
| Row 77 CPIGAS-EIA | NOT_ENOUGH_DATA expected; 16 settled | 0.23 (stated: forward shadow of 1 a month) | 1,100 | 4,400 | 148 | 580 | Effectively untestable on Kalshi alone (card: about 6 months for n 40, which matches only a weak bar) |
| Row 78 MORT30-FRED | NOT_ENOUGH_DATA expected; 11 settled | 1.0 (stated: about 52 a year) | 254 | 1,015 | 34 | 133 | Effectively untestable for the Bonferroni bar; 34 weeks for the weak bar at 10c |
| Row 79 TGA-DTS | NOT_ENOUGH_DATA expected; 5 settled | 1.0 (stated: about 52 a year) | 254 | 1,015 | 34 | 133 | Same as 78 |
| Row 92 OPENROUTER-SHARE | NOT_ENOUGH_DATA, forward shadow; 3 settled | 1.0 (derived: weekly market; card says about 10 months to n 40) | 254 | 1,015 | 34 | 133 | Effectively untestable for the Bonferroni bar |
| Row 76 SNOWRUN | registered, forward log, season limited | at most 5.8 (derived: about 25 city series, one bracket per city-month, 25 a month, correlated by storm; "a few usable brackets each month" so the real rate is lower). Season is about Dec to Mar only | 44 (at ceiling) | 175 | 5.9 | 23 | Effectively untestable for the Bonferroni bar (and a season is only about 17 to 21 weeks, so one winter cannot reach n 254) |
| Row 80 DEBTPENNY | settled count unverified | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Closes if under 15 settled events |
| Row 84 MENTION-PERSIST | DATA_LIMITED on request budget (8 of 193 series pulled) | UNKNOWN calls a week; the limit is the pull (about 600 more requests), not the calendar. Unit must be a call, not a word | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | After the pull the history may reach n 30 to 40 calls; Bonferroni n 254 calls is unlikely |
| Row 22 Debounced exit | likely NOT ENOUGH DATA (n 40 exits) | UNKNOWN (gold exits, figure removed) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Replay on R6 data, not a forward wait |
| Row 2 post-release window (EVENT830) | NOT_ENOUGH_DATA (needs about 3 more release days) | UNKNOWN. 17 trades from 3 release days so far (derived about 5.7 per release day); release days a week UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | At 5.7 per release day, Bonferroni 10c needs about 45 release days |
| POL-b2 approval up/down | NOT_ENOUGH_DATA likely; settled counts UNVERIFIED | 1.0 (stated: "one a week") | 254 | 1,015 | 34 | 133 | Effectively untestable for the Bonferroni bar |
| POL-b3 elections vs polls (ELECTIONS_CENSUS) | thin; unit is an election night, not a market | historical average about 1.4 a week (derived: 109 election dates in 2026 over about 45 weeks = 2.4, times the 60 percent usable share). Forward: ZERO, since no election closes before 2027-01-01 | 181 | 725 | 24 | 95 | Effectively untestable on Kalshi alone: the whole history holds 152 nights (about 60 to 90 usable), fewer than the 254 needed |
| POL-c2 deadline markets | NOT_ENOUGH_DATA near certain | about 0.01 (derived: "a handful per decade") | 25,000 | 100,000 | 3,400 | 13,000 | Effectively untestable on Kalshi alone |
| POL-c1 votes, POL-n1, POL-n2, POL-i2 | NOT_ENOUGH_DATA, forward log possible; counts UNVERIFIED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Needs a count before any time can be stated |

Not in the table on purpose: POL-k1 and the other favourite-and-hold ideas (barred by the owner rule), rows 81, 82, 83, 85, 88 (parked on terms, no rate), row 1 (a replay on held R6 data, not a forward wait).

## Ranking by weeks to a decidable test (Bonferroni bar, 10c edge; shortest first)

1. DERIBIT ladder: 1.5 weeks at the 168 a week ceiling (real rate UNKNOWN, so treat as best case).
2. Row 76 SNOWRUN: 44 weeks at the ceiling (and the season is only about 17 to 21 weeks).
3. Row 75 WXREVISE: 98 weeks at the unlagged ceiling, DROPPED.
4. POL-b3 elections: 181 weeks (history only holds 152 nights; none open before 2027).
5. Rows 78, 79, 92, POL-b2: 254 weeks each (about 4.9 years).
6. Rows 77, 89, 91 (and 90 at its bound): about 1,100 weeks. ECONFADE 1,700. POL-c2 25,000.
7. UNKNOWN rate: NEWSFADE, NO-arm, rows 2, 22, 80, 84, 93, POL-c1/n1/n2/i2; each needs its rate counted before it can be ranked.
Every row above 26 weeks is "effectively untestable on Kalshi alone" at the Bonferroni bar. Against the weak 90 percent bar at 10c (34 independent trades) only DERIBIT (0.2 weeks), SNOWRUN (6), WXDAYEND (below) and 1 a week ideas (34 weeks, just over) get near 26 weeks.

Also: Row 74 WXDAYEND, rate (derived from the card's "about 45 days forward" for n 40 per half, so n 80) about 12 a week at most 21 (3 cities times 7 days): W-B10 about 21 weeks, W-B5 82, W-C10 2.7, W-C5 11. It is the only non-recorder idea that fits inside 26 weeks at the Bonferroni 10c bar, and only if 3 cities' days count as independent (they are weather-correlated), and only if a bracket below 97c exists after midnight, which the card's existence check has not answered.

## What this table does not say

It says nothing about whether any of these ideas has an edge, only how long a fair test takes if the assumptions hold. A real edge below 5c needs far more trades (the n scales with 1 / e squared: 2.5c needs 4 times the 5c figure). Nothing here changes a registration, a bar or a trading rule.
