# OVN1: overnight perp premium to the last cash close, fade into the cash open (brief tests a and b; 2026-11-06)
Shared rules: `workers/OVN_COMMON.md` (universe on spread, cut 2026-11-01T00:00Z, halves, costs, N). Written before any premium or return was computed.

**Mechanism / counterparty.** Perp traders price news with no cash price; if they overshoot, the cash open (reference_price starts moving) pulls the perp back. The other side of the fade is the overnight perp trader who bought a premium.

**Events.** For each universe perp and each weekday cash open (09:30 ET) with open date in dev: t0 = the last recorded sample with ET time in [05:00, 09:25] that has bid>0 and ask>0; its reference ref0 must equal the reference at the first sample after 16:10 ET the day before (cash shut all night, else skip and count); t1 = first sample after t0 with ET time in [09:50, 11:30] (cash open resolved). No t0 or t1: no event (counted).
**Signal.** q = mid0/ref0 - 1 (premium to the last cash close). |q| must be at least 5 bps (below that the perp equals the close; counted).
**Trade.** Fade: short the perp if q>0, long if q<0, at t0 bid/ask, exit at t1 bid/ask, fees as common rules. Net return = s*(mid1/mid0-1) minus spread and 0.24% fee.
**Companion measurement (not a trade).** lambda = slope of (mid1/mid0 - 1) on q, day clustered.

**Numeric prediction.** Mean net per event -15 to -25 bps (fee 24 bps against a gross fade of 5 to 10 bps); lambda between -0.2 and 0.2; PF under 1. FALSIFIED about 80%, else NOT_ENOUGH_DATA.
**Kill rules.** NOT_ENOUGH_DATA if dev has fewer than 60 events or fewer than 30 clusters (the expected result: about 8 dev weekdays, 2 perps, maybe 6 to 10 events). FALSIFIED (with at least 60 events) if mean net is not above 0 in both halves, or PF under 1.5, or under 1.2 at fee x1.2, or day-clustered z under 5.27. LEAD only if all pass. With fewer events the figures are printed as information, not as a verdict.
**Enough data at the recorder's rate:** about 1 usable event per perp per weekday with the current 3 to 7 irregular samples a day (hit rate about 50% for the 05:00 to 09:25 window): 60 dev events plus a third held out needs about 5 months, about 2027-04. The 30 second recorder around the open would make it about 60 trading days from its start.
