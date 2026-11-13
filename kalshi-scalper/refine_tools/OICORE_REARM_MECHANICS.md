HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

# OICORE drawdown stop and re-arm: mechanics (facts, Nov 9, 2026; no recommendation)

Source: origin/main cadae52e. Authority: docs/CHARTER.md lines 17 and 126, the owner decides, merges and deploys; an agent may only draft text.

1. [live figure removed, ask Main] Refusals show in the skip log as code "gate". The Bot page shows "Waiting for a signal" (no stop indicator). Open OICORE orders are held to settlement; sold early only if they become a hedge or on Flatten. [live figure removed, ask Main]
2. [live figure removed, ask Main]
3. [live figure removed, ask Main] [live figure removed, ask Main]
4. PR text: "OICORE re-arm: reviewedAt to YYYY-MM-DD (owner decision, recorded in README first)". Files: functions/kalshiSlotLib.js (OICORE reviewedAt, SLOT_LAST_REVIEWED_ON), kalshi-scalper/README.md (dated entry first), Bot page changelog line. Pins to move with it: test/kalshiSlotGates.test.js (lines 48, 59), kalshiSlotIndexWiringGates (390), kalshiSlotWiringGates (about 106), event830SlotGates (40). Must pass: kalshiSlotGates, SW0, SI0, oicoreLadderGates, kalshiSlotRunGates, event830SlotGates, siteFreshnessGates, pre-ship. offEquivalence fixtures must NOT change.
5. Deploy: bash functions/deploy-sizing.sh only.
