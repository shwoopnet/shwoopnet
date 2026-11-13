HISTORY (Nov 13, 2026, owner ruling): this note predates the privacy scrub; lines marked "[live figure removed, ask Main]" are blank on purpose. Read it as history, not as a current rule.

DRAFT for the owner to approve. Main places it in kalshi-scalper/README.md under SLOT-OICORE BEFORE any re-arm edit. Nothing below changes a live rule.

### SLOT-OICORE update and pre-committed re-arm rule (dated 2026-11-10, written before the drawdown stop has fired)

**1. [live figure removed, ask Main] [live figure removed, ask Main] It refuses new OICORE entries only; it writes no kill latch, and open orders are held to settlement. `reviewedAt` is still 2026-10-30 and `SLOT_LAST_REVIEWED_ON` is 2026-11-05.

**2. [live figure removed, ask Main]

**3. [live figure removed, ask Main] A re-arm never removes earlier trades from the read, and a segment result can not be used to excuse a bad whole-record result.

**4. Re-arm rule, fixed before the stop fires.** The owner picks one; the drafter does not.
- **Option A: never re-arm automatically.** If the stop fires, OICORE stays off. A re-arm needs a new dated owner entry here, written after reading the record, then the reviewedAt edit.
- [live figure removed, ask Main] If it is under 1.0 it stays off (Option A applies). After that one re-arm, no further re-arm without a new dated owner entry.

[live figure removed, ask Main] So the rule will probably be used within days. Owner choice: A or B (D after the stop, or never).

**5. [live figure removed, ask Main] No deploy. A re-arm happens only through a later reviewed pull request, "OICORE re-arm: reviewedAt to YYYY-MM-DD (owner decision, recorded in README first)", merged and deployed by the owner.
