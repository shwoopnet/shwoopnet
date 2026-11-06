# OVN3: weekend gap, Friday close to Monday open (brief test c; 2026-11-06)
Shared rules: `workers/OVN_COMMON.md`. Written before any return was computed.

**Mechanism / counterparty.** Two days of news with no cash market: the perp premium to Friday's close q_w should predict Monday's cash open gap, and the perp may overshoot (fade) or undershoot (follow).
**Events.** Friday tc = first sample after 16:10 ET Friday (bid, ask > 0); Monday t0 = last sample with ET time in [05:00, 09:25] Monday with reference equal to Friday's; t1 = first sample [09:50, 11:30] Monday. Signal q_w = mid0/ref0 - 1, |q_w| at least 10 bps. Two companion trades, each counted: FADE (short if q_w>0) and FOLLOW (long if q_w>0), entered at t0, exited t1, costs common. Also the measure corr(q_w, cash gap ref1/ref0 - 1).
**Dev weekends:** one (Fri 2026-10-23 to Mon 2026-10-26; the Fri 10-30 to Mon 11-02 weekend resolves in the held-out third and is never read). Prediction: NOT_ENOUGH_DATA, by construction (1 weekend, 2 perps = at most 2 events against a bar of 30 weekends).
**Kill rules.** NOT_ENOUGH_DATA under 30 weekends. FALSIFIED (with at least 30) if net not above 0 in both halves, PF under 1.5, or z under 5.27 clustered by weekend. Enough data: about 30 weekends = 2027-05 at one weekend a week from 2026-10-23 for dev plus a third held out about 2027-07.
