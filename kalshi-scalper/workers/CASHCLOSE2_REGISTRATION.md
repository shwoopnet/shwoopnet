# CASHCLOSE2 registration: last 20 minutes drift into the 16:00 close (index, 1 minute candles; shared rules `CASHW_COMMON.md`; written 2026-11-06 before any outcome)

**Mechanism and counterparty.** As CASHCLOSE1: index and leveraged-ETF rebalancing and market-on-close flow are directional and cluster in the last 20 minutes, so the day's direction so far should continue into the close. Counterparty: liquidity providers fading the day's move. Honest alternative: the effect is a few bps against a fee of 24 bps and a spread near 1 bp.

**Rule (fixed).** d = cash(15:40) / cash(previous trading day 16:00) - 1 (ETF, convention in the shared file), direction = sign(d), no threshold. Entry at the candle ending 15:40 New York (ask for a long, bid for a short); exit at the candle ending 16:00 (bid for a long, ask for a short) (amendment to CASHCLOSE1's "15:59:30 sample": a 1 minute candle has no 15:59:30, 16:00:00 is the nearest instant). One trade per perp-date. A date with no prior cash close (2026-10-29: Yahoo starts that day) or a missing candle is skipped and counted. Control: always long, same entry and exit.

**Numeric prediction.** At most 3 dates x 2 perps = 6 trades; gross about +1 bp (range -8 to +8); net about -25 bps; PF 0 to 0.4. NOT_ENOUGH_DATA 98%, FALSIFIED 2%.

**Kill criteria and bars.** Shared file; the momentum minus always-long control must be positive in both halves. Read date **2026-12-01** (about 19 dates, 2 perps: about 38 trades, 100 trades about 2027-01-20, 30 clusters about 2026-12-14).

**N** +2.
