# Activity seats (built inert, Nov 14, 2026)

Small live trial seats on unproven ideas so the account keeps trading. Data only: no edge is expected. Site label: "Activity seat: unproven, for live data".

## Terms (constants in `functions/kalshiActivityLib.js`)

- 3 contracts, immediate-or-cancel, at most $3 an order, no entry price at 88c or above.
- Nothing from a declined or closed family (`ACTIVITY_DECLINED_FAMILIES`).
- Per seat: a $6 daily and a $20 weekly loss cap. Across all seats: one $40 weekly cap. The week starts Monday 00:00 America/Chicago (daylight saving followed), and everything resumes by itself then.
- No lifetime net floor. Instead, a seat whose last 100 settled fills have cash profit factor under 0.8 is cut. It needs all 100 fills, and only a reviewed edit that moves its `reviewedAt` returns it.
- Held to settlement. At most 3 seats at once.

## How it works

Every figure is replayed from the settled slot orders on every check (cash basis as `accountOrder` reads them, open dollars counted as lost, an order's own cost must still fit under the cap). Nothing is stored, so two instances agree and nothing can be stuck on. `kalshiSlotLib.js` calls `activityOrderCheck` right after the contracts are sized; a strategy that is not a registered activity seat is untouched. `activityFiredToday` counts a seat's filled orders on the Central day for a minimum-activity check.

## What is not built

**First seat, Nov 14, 2026: SPXOI1** (the S&P 500 15 minute market, OICORE's mechanism, a trial below the research bar; `ACTIVITY_SEATS` holds it and the slot registry has an entry of the same id). Any further seat is a later reviewed edit: add the entry, map it to a second-slot strategy (the slot validator needs a kill rule, so use its loosest, 100 fills and -$60, which the weekly caps beat; hold-to-settle needs a `SLOT_HOLD_ALLOWED` entry; `SLOT_LAST_REVIEWED_ON` moves to match), register the page text, and get the owner's popup with the exact spec. The 12% account stop, the hard stop and the window cap still apply to every seat order.

## Declined families are a reviewer's check (Nov 14, 2026)

`familyId` is a free string matched exactly, so the code list cannot catch a renamed declined idea. Rule 2 of the declined list (`docs/STRATEGY_LIFECYCLE.md` 7e) says a rename IS the declined idea: that is checked by the reviewer at admission, together with the owner's popup that quotes any earlier NO. The code list is extended by a reviewed edit and never shrunk without the owner. It also draws on the registry for MAPBREAK and the approval NO side (closed Nov 12 to 13), which the declined-list table does not carry yet.

## SPXOI1, the first seat (Nov 14, 2026)

- Market: `KXINX15M` only, weekdays about 15:00Z to 21:00Z, exchange shard 0 (may hold no money: the engine logs a skip and sends nothing). Family `cheap-side-open-interest`.
- Look: 120 to 180 seconds before the close. Rule: open interest rise (candle ending 180 s before the close minus the one ending 360 s before; a missing candle means no order) at or above 5463.9 (two builds equal, n = 140).
- Buy the side with the lower ask (a tie goes YES) if that ask is 8c to 50c; limit is the ask, no slip; 3 contracts; immediate-or-cancel; held to settlement; no scale-in.
- Kill rules in the slot registry: net below -$18 after 5 fills, or 30 losses in a row. Activity terms: $6 a day and $20 a week for the seat, $40 a week shared, cut if the last 100 fills have profit factor under 0.8, nothing at 88c or above.
- How the caps combine: the slot's own per seat caps (`SLOT_SEAT_CAPS`: $3 an order, $9 a day) and the activity limits are BOTH checked, so the tighter binds: a day stops at $6 (the activity cap), the $9 slot cap never binds first. The slot's daily and lifetime loss caps are counted from each strategy's own orders, so this seat's losses do not use another seat's room (and the reverse). The shared 12% stop, the hard stop and the 5.5% window cap still apply.
- The page has no look of its own for it: it coincides with the open interest jump look, so a second ring entry would only merge names.
