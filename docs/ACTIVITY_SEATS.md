# Activity seats (built inert, Nov 14, 2026)

Small live trial seats on unproven ideas so the account keeps trading. Data only: no edge is expected. Site label: "Activity seat: no edge expected, data only".

## Terms (constants in `functions/kalshiActivityLib.js`)

- 3 contracts, immediate-or-cancel, at most $3 an order, no entry price at 88c or above.
- Nothing from a declined or closed family (`ACTIVITY_DECLINED_FAMILIES`).
- Per seat: a $6 daily and a $20 weekly loss cap. Across all seats: one $40 weekly cap. The week starts Monday 00:00 America/Chicago (daylight saving followed), and everything resumes by itself then.
- No lifetime net floor. Instead, a seat whose last 100 settled fills have cash profit factor under 0.8 is cut. It needs all 100 fills, and only a reviewed edit that moves its `reviewedAt` returns it.
- Held to settlement. At most 3 seats at once.

## How it works

Every figure is replayed from the settled slot orders on every check (cash basis as `accountOrder` reads them, open dollars counted as lost, an order's own cost must still fit under the cap). Nothing is stored, so two instances agree and nothing can be stuck on. `kalshiSlotLib.js` calls `activityOrderCheck` right after the contracts are sized; a strategy that is not a registered activity seat is untouched. `activityFiredToday` counts a seat's filled orders on the Central day for a minimum-activity check.

## What is not built

No seat is registered (`ACTIVITY_SEATS` is empty). Admitting one is a later reviewed edit: add the entry, map it to a second-slot strategy (the slot validator needs a kill rule, so use its loosest, 100 fills and -$60, which the weekly caps beat; hold-to-settle needs a `SLOT_HOLD_ALLOWED` entry; `SLOT_LAST_REVIEWED_ON` moves to match), register the page text, and get the owner's popup with the exact spec. The 12% account stop, the hard stop and the window cap still apply to every seat order.

## Declined families are a reviewer's check (Nov 14, 2026)

`familyId` is a free string matched exactly, so the code list cannot catch a renamed declined idea. Rule 2 of the declined list (`docs/STRATEGY_LIFECYCLE.md` 7e) says a rename IS the declined idea: that is checked by the reviewer at admission, together with the owner's popup that quotes any earlier NO. The code list is extended by a reviewed edit and never shrunk without the owner. It also draws on the registry for MAPBREAK and the approval NO side (closed Nov 12 to 13), which the declined-list table does not carry yet.
