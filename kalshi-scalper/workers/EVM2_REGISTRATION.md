# EVM2 registration (2026-11-06): ladder-implied level minus perp mid predicts the perp's next 25 minutes (Bitcoin, N +1)

Written before any basis or return was computed. Discovery only. Data, split, definitions, scale check and held out third exactly as `EVM1_REGISTRATION.md` (dev = closing dates 2026-08-24 to **cut 2026-09-20**, 28 dates; closes on or after 2026-09-21 never read; D1 / D2 = first / last 14 dates).

**Counterparty / mechanism.** Ladder quoters who are slower than the perp: if the ladder's 50 percent strike sits above the perp mid, the ladder is "ahead" (its quoters saw something) or "stale"; the registered claim is that a gap carries information about the next 25 minutes. The counterparty on the perp is its taker flow and market makers (spread plus fee paid).

**Rule (one definition, no tuning).** At t = C - 25 min for every hourly close C: basis B = (implied level(t) - 10000 x perp mid(t)) / (10000 x perp mid(t)), in basis points. Trigger |B| >= 20 bp. Position sign = sign(B) (long the perp if the ladder is above it). Held to C (the ladder's own close, 25 minutes), exit at perp mid(C).
**Cost, charged from the recorded book:** entry crossing = half the recorded spread (ask close minus bid close) of the candle at t, exit crossing = half the spread at C, plus taker fee 12 bp per side (24 bp round trip, SNAPBACK1's assumption) plus 1 bp funding charged against the position. Variant x1.2 multiplies fee and spread by 1.2. Net in bp of notional; PF = sum of winning nets / sum of losing nets.
**Control:** the same trade at closes with |B| < 20 bp (sign of B, or none if exactly 0), and trigger minus control with a bootstrap by date.

**Numeric prediction.** Trigger rate 10 to 25 percent of closes (about 70 to 170 development trades). Gross mean about 0 +/-3 bp (25 minute Bitcoin moves have a standard deviation near 30 to 40 bp; the perp is the leading, deepest price), net about -25 bp, PF about 0.2 to 0.5. Probability FALSIFIED: 85 percent.

**Kill criteria.**
- NOT_ENOUGH_DATA: fewer than 100 development trades (state the date: closes accrue 24 a day and the ladder file is refreshed by hand, so re-read after 150 more closes at the observed trigger rate).
- FALSIFIED: with at least 100 trades, PF below 1.5 in either development half or overall, or net not positive in both halves, or PF below 1.2 at x1.2, or trigger minus control not positive in both halves.
- LEAD: PF at least 1.5 in each half and overall at x1.2, at least 100 trades, trigger minus control positive in both halves, date-cluster z of mean net per trade at least 5.27 (running N about 730,457 deflated bar), then the held out third is read once. Otherwise no LEAD.
N +1 (running about 730,457).
