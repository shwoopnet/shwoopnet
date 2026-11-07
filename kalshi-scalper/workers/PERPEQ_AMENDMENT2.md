# PERPEQ_AMENDMENT2: move the PERPEQ development end one trading day later, to 2026-12-21 (Strategy Research V2 worker; written 2026-11-07; owner decision relayed by main, made together with the same move for STOCKPERP; before any held-out read and before any PERPEQ outcome was computed)

Nothing is scored in this step. No PERPEQ return, gap, premium or ratio exists; no PERPEQ scorer exists (only `workers/perpeq/costmap.py`, no date cap, no outcome), so no code cap changes. This amendment supersedes `PERPEQ_AMENDMENT1.md` only where the two differ (the dates below); everything Amendment 1 says it does not change stays unchanged.

## Calendar count (US market calendar; closed 2026-11-26, 2026-12-25, 2027-01-01, 2027-01-18; 2026-11-27 and 12-24 are early closes and count as trading dates)
- **Development: 2026-11-09 to 2026-12-21 inclusive = 30 trading dates** (Nov 9 to 13: 5; Nov 16 to 20: 5; Nov 23 to 25: 3; Nov 27: 1; Nov 30: 1 = 15; Dec 1 to 4: 4; Dec 7 to 11: 5; Dec 14 to 18: 5; Dec 21: 1 = 15).
- **Held out: 2026-12-22 to 2027-02-01 inclusive = 27 trading dates**, the same length as Amendment 1's window (2026-12-21 to 2027-01-29 is 27 trading dates by the same calendar: Dec 21 to 24: 4; Dec 28 to 31: 4; Jan 4 to 8: 5; Jan 11 to 15: 5; Jan 19 to 22: 4; Jan 25 to 29: 5). Dec 22, 23, 24 (3), Dec 28 to 31 (7), Jan 4 to 8 (12), Jan 11 to 15 (17), Jan 19 to 22 (21), Jan 25 to 29 (26), Feb 1 (27).

## What changes (only these)
- **Development:** trading dates 2026-11-09 to **2026-12-21** (was to 12-18). The development read loads dates up to and including 2026-12-21 only. **First development read: 2026-12-22 after the close** (was 12-19).
- **Halves:** D1 = 2026-11-09 to 11-30 (15 dates), D2 = 2026-12-01 to 12-21 (15 dates). (Amendment 1 had D2 to 12-18, 14 dates.)
- **Held out:** **2026-12-22 to 2027-02-01**, never read before its date, read ONCE on or after **2027-02-02** (the first calendar day after the last held-out date) and only for a LEAD (was 2026-12-21 to 2027-01-29, read on or after 2027-01-30).

## Can PERPEQ1's 30 cluster bar now be met?
Yes, but with no slack. PERPEQ1 development now has exactly 30 trading dates (the registration still excludes the 2026-11-06 afternoon, so its first date is 11-09, which is why it had 29 under Amendment 1). The bar (30 trading-date clusters, a cluster being a date with at least one trade) is met only if EVERY one of the 30 dates yields at least one PERPEQ1 trade. The registered rate is about 8 trades a date across 19 names, so a date with no trade needs a market-wide quiet gap morning or a candle outage; the probability that all 30 dates have a trade is about 80% on that rate. If one date has none, the verdict at the first read is NOT_ENOUGH_DATA on clusters, as registered; the bar is not lowered. PERPEQ2, 3 and 4 cannot reach 30 clusters in development at their rates.

## What does NOT change (explicitly)
Every bar and verdict rule in `PERPEQ_COMMON.md` (100 trades, 30 trading-date clusters, PF 1.5 in each half, net above 0 in both halves, PF 1.2 at fee x1.2, trigger better than control, day-clustered z 5.27, LEAD then one held-out read with PF 1.5), the cost assumption (recorded close bid and ask plus 0.12% a side, x1.2 stress, break-even fee reported), the universe rule and the 21 names, the screens, every trade definition, trigger, grid, hold and control of PERPEQ1 to PERPEQ4, the N accounting (N +15, running about 730,471 to about 730,486; no try added), and the original registration files and Amendment 1 (unchanged on disk).
sha256 (all verified unchanged on 2026-11-07): PERPEQ_COMMON.md fa1f2153cd6925a3438649822ef7b26c7117557b6e42793d234689cfcc536b1d; PERPEQ1_REGISTRATION.md 7874d2743c30eab89d0b122bcdf311b0093ee691985bc5d989ecf5823acffed3; PERPEQ2_REGISTRATION.md b23b97ae5d8eadf9d45d8b7ef66c8ce16ab46fc039f306c532a98fcba984703c; PERPEQ3_REGISTRATION.md 0b379bcc91c59c917f6c341cb2a3364f7d1ab5c76d9f7b334b9dd57b79b52581; PERPEQ4_REGISTRATION.md c64a102c135ca3412132054a3c02ee7421cf61c9b40606533aa3dcaf40ac8f70; PERPEQ_AMENDMENT1.md 77050be09ccc2030293694f164d4054f69bab0bd6fb52226e42f45d677372d2a. The sha256 of THIS file is in the README ledger entry. The `PERPEQ[1-4]_RESULT.md` files and Amendment 1's dates are superseded by this file.

## Read dates (registration-day rates; no PERPEQ outcome used)
One development read, 2026-12-22 after the close, on 30 dates; a later read inside the window needs a further amendment.
- **PERPEQ1:** about 8 trades a date, about 240 by 2026-12-21, the 100 trade bar about 2026-12-01; the cluster bar can be met at the 12-22 read only with a trade on every date (above). Held-out read on or after 2027-02-02 (27 dates).
- **PERPEQ2:** about 1.3 a date, about 40 by 12-21; 100 trades about 2027-03; NOT_ENOUGH_DATA at 12-22 (about 93%).
- **PERPEQ3:** about 0.8 a date, about 24 by 12-21; 100 trades about 2027-05 (about 150 in the window if the 5 minute cash-hours snapshots of `PERPEQ_RECORDER_REQUEST.md` item 2 run from 2026-11-09); NOT_ENOUGH_DATA (about 93%).
- **PERPEQ4:** about 0.4 a date, about 12 by 12-21; 100 trades about 2027-11; NOT_ENOUGH_DATA (about 97%), the deviation-versus-cost readout is the output.
