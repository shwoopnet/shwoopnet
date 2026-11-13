# ESOCTIE development read (History Miner, Nov 13, 2026, about 02:05Z): CLOSED by its registered kill line, 0 bets

Selected on development: this read can falsify, it cannot support. One try (the registered one). The held-out (closes 2026-10-23 to before 2026-11-13) is NOT read and stays unread. [research]

**Inputs.** Lists `ESOCTIE_LISTS/2026-11-12T2031Z_43301161879`; candles `ESOCTIE_CANDLES_P1..P4` (240 of 240 requests at HTTP 200, 92.5 MB, none truncated; Auditor B checked P1 to P4: parameters equal to the jobs, no candle outside its range, nothing after the 2026-10-23 cut). Scorers: History Miner `esoctie.py` 1646f542 (NOTE 11, Auditor B CLEAN), Testing Desk `esoctie.py` 2e5faf1f (claude/testing-desk 7aa6d6d3). Series file 5c766fdd unchanged. Run once each.

**Rule 16b: both builds print the same figures** (every count, quantile, share and the kill line below). Raw outputs: `ESOCTIE_DEV_READ_OUTPUT_HM.json`, `ESOCTIE_DEV_READ_OUTPUT_TESTINGDESK.json`.

| | count |
|---|---|
| events listed | 7,120 |
| start not derivable | 37 |
| kept | 7,083 |
| not filled (no minute S-1 to S-10 with all three two-sided candles) | 5,466 |
| filled | 1,617 |
| base-building (bucket under 300 earlier events) | 1,186 |
| filled and eligible | 431 (bucket 0.45-0.55: 313; 0.55-0.65: 118; none at 0.65 and up) |

Gap (walk-forward base rate minus Tie ask), quantiles 25 / 50 / 75 / 90: -5.9c / -4.4c / -2.7c / -1.1c. Share with gap 10c or more and spread 4c or less: 0 of 431 (0.0%); placebo 0.0%. Median spread 4c; median one-way entry cost 3.5c (under the 4c kill); median Tie ask 18c (above the 15c cheap-tail line); 0 void or unsettled.

**Verdict: CLOSED, "efficient, move on"** (the registered kill line: the 10c share under 3% or under twice the placebo). No bet was booked, so there is no cash profit factor, no half and no window figure; by the label rule it is also "no evidence at n = 0". The Tie is priced above its own walk-forward base rate in about 90% of eligible events.

**Beside it, not reopening it.** 77% of kept events were "not filled" because a minute candle was missing on one of the three contracts. CANDLEGAP (CS2 only, one evening, provisional under 16b) found a missing candle meant an unchanged touch on that series. A carry-forward version would be a new try under rule (i); with every gap quantile negative it is not proposed.

**Consequences.** ESOCTIE leaves the probation pool; the forward wheel sheet (`ESOCTIE_FORWARD_WHEEL_SHEET.md`, 4bbb6e63) is withdrawn with it; ESOCTIE-R is not registered (its condition was a development read at or above 1.0); the held-out stays unread. Ledger: 1 try spent, verdict CLOSED (kill line).
