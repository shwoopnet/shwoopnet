# OICORE decision brief for the owner (Nov 10, 2026, 09:27 UTC; drafted by the refinement chat, read only)

This is your decision. No agent changes the live rule. Nothing below was deployed or edited in code.

## 1. Where it stands (dash.sh, report 09:27 UTC)
- Booked (what the code counts): 81 settled fills, 14 wins, 67 losses (17.3%), PF 1.11, net +$11.00. Peak was +$50.33.
- Cash basis (real fills, recomputed Nov 10 03:30 CT, 81 fills): PF 1.30, net +$26.15, rolling-60 PF 0.86 (the Nov 9 figure was 1.27 on 78 fills).
- Drawdown from own peak: $39.33. The stop is $50 at ladder step 10, so room is $10.67 (21% of the stop).
- Ladder step: 10 contracts, the bottom step. Loss streak now 2 (longest 13; kill at 24 in code).
- Net kill (under -$6 after 40 fills): booked net is +$11.00, so about $17 away.
- Last order 08:12 UTC today. Forward read is Nov 13 (FALSIFIED if PF under 1.0 on 100+ fills, or net under 0 on 150+).

## 2. The evidence
- Live, cash basis: last 40 fills PF 0.51 (net -$30.49); before Nov 5, PF 3.86 (36 fills, +$54.03). Since Nov 5 the edge is gone or hiding.
- Independent window, June to July (w_indep4, rerun now on 781 of 1,536 markets): 15 triggers, PF 0.99 at +0c (-0.10c a contract), 0.87 at +1c. Verdict NOT_ENOUGH_DATA (needs 40 triggers; full pull projects about 30).
- Trade-by-trade candle check (w_candlevalid2): on matched windows history at c-180 (+0c) PF 1.15 against live 1.43. History is not far above live.
- Fees: about $5.93 on 81 fills, 63% of the net after fees (the edge is thin against its cost).
- Tagged fills (paid 0.95c+ above the first seen ask): 34 fills, PF 0.39, -$31.02. Untagged: 47 fills, PF 1.88, +$42.02.

## 3. What the stop does when it fires, and the odds
- It refuses new OICORE orders on every tick. No latch is written, so nothing stays "off" by itself unless you choose that.
- Open orders are held to settlement (sold early only if they become a hedge, or on Flatten).
- The Bot page shows "Waiting for a signal" (no stop indicator). L1 and EVENT830 are unaffected.
- Monte Carlo (w_stopsim, 20,000 paths, resampling the record, true uncertainty wider): chance the stop fires before Nov 13 is 25 to 27% if the future looks like all fills, 70 to 74% if it looks like the last 40.

## 4. The choices
- A. Leave it, never re-arm automatically. Cost: none now. Risk: up to $10.67 more loss before the stop, then it stays off until you write a dated entry. Forward read: whole record kept.
- B. Leave it, re-arm once 3 days after the stop fires (bottom step, only if whole-record booked PF is 1.0 or better). Cost: a reviewed edit later. Risk: a second drawdown of up to $50. Forward read: whole record kept, segments shown beside it.
- C. Step to the smallest size now. Not available: it is already at the bottom step (10). Only a code edit below 10 would cut size, which is a new rule.
- D. Pause by a reviewed code edit (PAUSED_SERIES) until the Nov 13 read. Cost: it takes no signals for 3 days, so the read has fewer than 100 fills. Risk: removes the $10.67 room risk. Forward read: whole record kept, but it will stay short of 100 fills.
- E. Let the Nov 13 read decide. Same as A until then; the stop is the only control in the meantime.

## 5. Refinement chat's view (not a decision)
Leave it (A or E). Reasons: the stop already caps the loss ($10.67 room, the net kill and shared 12% stop also apply); the whole-record result is still positive; the independent window has only 15 triggers, too few to read; pausing now would shrink the Nov 13 sample. The one thing that would change this view: the independent window reaching 40 triggers with PF under 1.0, which would point to D.
