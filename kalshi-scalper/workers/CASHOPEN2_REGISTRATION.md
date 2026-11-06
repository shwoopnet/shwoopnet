# CASHOPEN2 registration: does the index perp lag the cash open in the first minutes (index, 1 minute candles; shared rules `CASHW_COMMON.md`; written 2026-11-06 before any outcome)

**Mechanism and counterparty.** As CASHOPEN1: the 09:30 auction prints a price the perp's maker has only estimated; during the first minutes the perp quote can sit behind the cash tape. Counterparty: the maker with a stale resting quote. Honest alternative (and the alignment test already suggests it): the maker reprices within one minute and the lag is far below the 12 bps fee.

**Rule (fixed).** Event = (perp, date, slot) with slots at the candles ending 09:31 and 09:33 New York. cash_ret = cash(slot) / open of the 09:30 ETF bar - 1; perp_ret = mid at the slot candle / mid at the candle ending 09:30 - 1; g = cash_ret - perp_ret in bps. Trigger |g| at least 10 bps: trade the perp in the sign of g (buy at the slot candle's ask if g > 0, sell at its bid if g < 0), exit 120 seconds later at the candle ending slot + 2 minutes (bid for a long, ask for a short). Control: |g| under 10, same direction rule. Two slots on one date are not independent, so the cluster is the date.

**Numeric prediction.** Development events 4 dates x 2 perps x 2 slots = at most 16; triggered about 3 (range 0 to 8); gross about +1 bp (range -5 to +6); net after fee about -25 bps; PF 0 to 0.3. NOT_ENOUGH_DATA 97%, FALSIFIED 3% (needs 100 trades), LEAD 0%.

**Kill criteria and bars.** Shared file. Read date for the first formal score on forward dates: **2026-12-01** (about 16 dates, 2 perps, 2 slots: at most about 64 events, so the 100 trade bar is not reached before about 2027-01-15 at about 15% triggers; reported then).

**N** +2.
