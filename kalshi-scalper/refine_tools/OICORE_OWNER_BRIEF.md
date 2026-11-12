# OICORE decision brief for the owner (Nov 10, 2026, 09:27 UTC; drafted by the refinement chat, read only)

This is your decision. No agent changes the live rule. Nothing below was deployed or edited in code.

## 1. Where it stands (dash.sh, report 09:27 UTC)
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main] [live figure removed, ask Main]
- [live figure removed, ask Main]
- [live figure removed, ask Main]

## 2. The evidence
- [live figure removed, ask Main]
- [live figure removed, ask Main] Verdict NOT_ENOUGH_DATA (needs 40 triggers; full pull projects about 30).
- [live figure removed, ask Main] History is not far above live.
- [live figure removed, ask Main]
- [live figure removed, ask Main]

## 3. What the stop does when it fires, and the odds
- It refuses new OICORE orders on every tick. No latch is written, so nothing stays "off" by itself unless you choose that.
- Open orders are held to settlement (sold early only if they become a hedge, or on Flatten).
- The Bot page shows "Waiting for a signal" (no stop indicator). [live figure removed, ask Main]
- [live figure removed, ask Main]

## 4. The choices
- A. Leave it, never re-arm automatically. Cost: none now. [live figure removed, ask Main] Forward read: whole record kept.
- B. [live figure removed, ask Main] Cost: a reviewed edit later. [live figure removed, ask Main] Forward read: whole record kept, segments shown beside it.
- C. Step to the smallest size now. Not available: it is already at the bottom step (10). Only a code edit below 10 would cut size, which is a new rule.
- D. Pause by a reviewed code edit (PAUSED_SERIES) until the Nov 13 read. [live figure removed, ask Main]
- E. Let the Nov 13 read decide. Same as A until then; the stop is the only control in the meantime.

## 5. Refinement chat's view (not a decision)
Leave it (A or E). [live figure removed, ask Main]
