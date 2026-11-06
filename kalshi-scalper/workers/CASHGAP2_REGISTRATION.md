# CASHGAP2 registration: fade the overnight gap in the first 10 minutes after the open (index, 1 minute candles; shared rules `CASHW_COMMON.md`; written 2026-11-06 before any outcome)

**Mechanism and counterparty.** As CASHGAP1: a large overnight gap is set by thin pre-market trades and auction imbalance; part retraces once regular liquidity arrives. Counterparty: the gap chaser buying into the auction. Honest alternative: gaps are news and continue, or retrace by less than the cost. The claim is FADE.

**Rule (fixed).** gap = open of the 09:30 ETF bar / ETF cash(previous trading day 16:00) - 1. Trigger |gap| at least 30 bps. Trade the perp AGAINST the gap sign: gap up = sell at the bid of the candle ending 09:30 New York, buy back at the ask of the candle ending 09:40; gap down = the mirror. Control: |gap| under 30 bps, same fade rule. 2026-10-29 has no prior cash close and is skipped. Information (not scored): the share of perp-dates on which the perp's 09:30 to 09:40 return has the gap's sign, with each gap and return listed.

**Numeric prediction.** At most 6 events, triggered about 1 (range 0 to 3); gross about +2 bps; net about -23 bps. NOT_ENOUGH_DATA 98%, FALSIFIED 2%.

**Kill criteria and bars.** Shared file. Read date **2026-12-01**; at about 15% of perp-dates triggering, 100 trades needs about 330 perp-dates, which two perps cannot give for about 160 trading days (about mid-2027); stated honestly: this test cannot reach its bar on two index perps in 2026, it is a descriptive instrument.

**N** +2.
