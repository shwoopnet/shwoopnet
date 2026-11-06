# OVN2: after-hours to pre-open perp drift continues into the cash open (brief test a; 2026-11-06)
Shared rules: `workers/OVN_COMMON.md`. Written before any return was computed.

**Mechanism / counterparty.** News that arrives after the 16:00 ET close is priced slowly by perp traders alone; the perp keeps moving through the night, and the cash open then repriced further in the same direction (continuation) because liquidity arrives only at 09:30. The other side: market makers who took the early move.

**Events.** As OVN1 for t0 and t1. tc = the first recorded sample after 16:10 ET and before 22:00 ET the evening before, bid>0 and ask>0 (else no event). **Signal** d = mid0/midc - 1 (overnight perp move), |d| at least 5 bps, sign s = sign(d). **Trade.** Follow: go the sign of d at t0 (bid/ask), exit t1; fees as common rules.

**Numeric prediction.** Mean net -18 to -28 bps; correlation of d with the following t0 to t1 return within +-0.15; PF under 1. FALSIFIED about 80%.
**Kill rules.** As OVN1 (NOT_ENOUGH_DATA under 60 events or 30 clusters; FALSIFIED otherwise on both halves, PF 1.5, fee x1.2, z 5.27). Enough data about 2027-04 at the current recorder rate (needs both a post-close and a pre-open sample on the same night, about 40% of nights).
