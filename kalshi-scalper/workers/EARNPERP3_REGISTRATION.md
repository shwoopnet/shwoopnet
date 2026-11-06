# EARNPERP3 registration: funding versus the earnings move (written 2026-11-06 about 23:00 UTC, before any funding row was joined to any release; shared rules `EARNPERP_COMMON.md`)

## Mechanism and counterparty
Holding a perp through an earnings print pays or earns funding. The registered claims are narrow, because the funding schedule is public and checkable now: equity perps get ONE funding rate a day, stamped 21:00Z (16:00 ET in standard time), set from the day's premium to the cash reference. A POST release (filed after 16:00 ET) is therefore filed AFTER that stamp, and a hold from L to E (09:29 ET) next morning crosses no stamp; a PRE release also crosses none. Counterparty for a carry story: none while holding L to E. The one place funding could carry information is the sign of the rate stamped at 16:00 ET before the release: a persistently positive premium means longs were paying, i.e. the book was long into the print.

## Claims (fixed)
(a) **Crossings:** the number of funding stamps strictly between L and E is 0 for every event (accounting claim; one crossing falsifies it and is reported). (b) **Sign:** sign(f0) agrees with sign(m), where f0 = the funding rate stamped at 16:00 ET on the last trading day on or before the release (zero rates, which the deadband produces, are excluded and counted), m as in EARNPERP1, events as in the common file with the 150 bps trigger of EARNPERP1 but WITHOUT the cost screen (nothing is traded). (c) **Materiality:** mean |f0| divided by the mean |m| of the events. Information, never scored: the distribution of |f| of the 58 stock perps served so far (2026-11-05 and 11-06 only).

## Numeric prediction
(a) 0 crossings of about 55. (b) agreement 50% (range 42% to 62%) on about 25 events with a nonzero f0 (the deadband is 0.002%, zero rates are common). (c) mean |f0| about 1 to 3 bps against mean |m| about 400 bps: ratio under 1%.

## Verdict rules
(a) PASS if zero crossings, else FALSIFIED. (b) NOT_ENOUGH_DATA under 30 events with nonzero f0; FALSIFIED at 30 or more with agreement under 65% or a date-clustered z under the deflated bar (about 5.32); LEAD only if both hold, held out read once on or after 2027-06-01. (c) Reported as a number; the claim "funding is a first order cost or income of holding through the print" is FALSIFIED if the ratio is under 10% with at least 30 events. Development read date 2027-03-01. Scorable today: zero events; the funding magnitudes are information only.

## Count
N +2 (sign rule, materiality claim).
