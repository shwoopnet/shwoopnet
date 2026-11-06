# CASHGAP1 registration: the opening 10 minutes versus the overnight gap sign (fade the gap) (written 2026-11-06, before any perps30 file or Yahoo bar of this study was read)

Discovery only. No live code, no promote verb.

## Mechanism and counterparty
A large overnight gap is set by thin pre-market trades and by opening auction imbalance; part of it tends to retrace once regular liquidity arrives in the first 10 minutes. Counterparty: the gap chaser buying into the auction. Honest alternative: gaps are news driven and continue, or retrace by less than the perp's round-trip cost. The claim is FADE; continuation is the sign-flipped readout of the same trades, not a second rule.

## Data (not yet existing)
perps30/<date>/open.csv.gz (none exists as of 2026-11-06 16:00 UTC). Cash reference: Yahoo 5 minute bars (60 day retention): the previous session's last close and the first bar's open at 09:30 of the day, gap = open / prior close - 1. Equity perps are inactive (bid 0) outside US hours, so a perp-day with no active sample within 60 seconds of 09:30 is counted and skipped.

## Rule (fixed)
Universe on cost: as CASHOPEN1 (median relative spread in 09:30 to 10:30 at most 25 bps, 15 cheapest). A perp-day triggers only if |gap| >= 30 bps. Trade the perp AGAINST the gap sign: gap up means sell at the recorded bid at the first active sample at or after 09:30:00, buy back at the ask at the first sample at or after 09:40:00; gap down means the mirror. Cost = recorded crossing plus 12 bps a side (x1.0 and x1.2). Control: every active perp-day with |gap| < 30 bps traded with the same fade rule.

## Windows and cut
Dev open files 2026-11-06 to 2026-11-30; **files on or after 2026-12-01 are held out and never read**. Halves: first 8 and last 8 dev files. z day clustered.

## Numeric prediction
About 40 to 90 triggered trades in dev (10 perps x 16 days x about 35% with a 30 bps gap), gross +2 to +8 bps (partial retrace), net -20 to -30 bps. FALSIFIED 40%, NOT_ENOUGH_DATA 58%, LEAD 2%.

## Verdict rules
NOT_ENOUGH_DATA: under 150 triggered dev trades or under 12 dev trading days. FALSIFIED: with at least 150 trades, PF under 1.5 in either half, net not above 0 in both halves, PF under 1.2 at fees x1.2, fade minus control not positive, or clustered z under 5.27. LEAD only if all pass; held-out files then read once.
**Read date: 2026-12-01**; at about 3 trades per trading day the 150 trade bar needs about 50 trading days of recording, about 2027-01-15 if the recorder is extended past its 2026-12-07 stop (a reviewed edit).

## Count
N +1 (running about 730,455 before; about 730,459 after the four tests; the coordinator keeps the total).
