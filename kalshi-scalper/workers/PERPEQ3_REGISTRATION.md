# PERPEQ3 registration: fade the stock perp's premium to its reference, cash hours only (written 2026-11-06 about 16:20 UTC, before any outcome; shared rules `PERPEQ_COMMON.md`)

Discovery only. No live code. RV3 (same idea on six non-stock perps, 67 trades, net -48 bps, gross -23 bps, NOT_ENOUGH_DATA, information negative) and OVN1 (overnight) exist; this is the cash-hours stock version with the 21 cost-chosen perps and a fresh cut. Overnight premiums are NOT used here (the reference is frozen overnight, so a premium then is the gap, which is PERPEQ1).

## Mechanism and counterparty
In cash hours `reference_price` follows the live cash value, so the perp's premium p = mid / reference - 1 is the perp's deviation from the stock it tracks. A premium above its own spread cost is a taker paying up in a thin book; it should decay as makers and arbitrageurs lean on it. Counterparty: that taker. Honest alternative: the reference lags the perp (the perp is the first mover), so the premium is a forecast, not an error, and continuation is as likely as reversion.

## Rule (fixed, no tuning)
Sample eligible: New York time 09:50 to 15:25 on a trading day, perp active, under the 3 times median spread screen. Trigger: |p| at least max(10 bps, 3 times the sample's spread in bps). Trade: fade (p > 0: sell at the bid; p < 0: buy at the ask), one position per perp at a time. Exit: the first eligible sample at least 90 minutes later and not after 15:55 New York the same day (no exit sample means no trade, counted). Control: the reverse direction. Per-name table is information only.

## Numeric prediction
Eligible samples about 1.5 a day; with entry and an exit at least 90 minutes later in the same session about 0.5 usable a day. 21 perps x 15 days x 0.5 x P(trigger about 0.08) = about 12 trades in development (range 4 to 30). Mean gross +2 bps (range -8 to +10), spread plus fee about 30 bps, net -28 bps, PF 0.0 to 0.3. If `perps30` files exist before 2026-12-01, they are NOT used for this registered test (only the hourly rows); a 30 second version would be a new registration. Probabilities: NOT_ENOUGH_DATA 92%, FALSIFIED 7%, LEAD 1%.

## Kill, bars and cut
As the common file. Development read date **2026-12-01**; held out from 2026-12-01, read once on or after 2026-12-30 after a LEAD only. Date 100 trades is met at the observed rate is reported (about 2027-07 at 12 trades a month).

## Count
N +2.
