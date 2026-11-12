# Long-hold paper log (Nov 12, 2026)

A general, log-only rule type for markets that are NOT 15 minute markets: look some hours before the close, choose one market per event and per arm, record what an order held to settlement would have cost and made. Phase 1 (this document, built) is the paper log. Phase 2 (a switched-off order path) is a design section only and is NOT code.

Nothing real is configured. `LONGHOLD_RULES` in `functions/kalshiLongholdLib.js` is an empty frozen list, so the deployed functions make no read and no write for it. The first real configuration (the Head of R&D's ruling, Nov 12: whichever candidate survives its measurement, TIE3, NHLOT or MAPBREAK family) is a later reviewed edit with its registration in front of it. The approval NO side was NOT configured: its main arm is the favourite side held to settlement, which the owner has banned, and no exception is requested. Politics series appear only as test fixtures in `test/longholdPaperGates.test.js`.

## Phase 1 as built

A rule has: `id`, `readme` (its registration), `series` (fixed in code, 1 to 8, never a 15 minute series), `lookMinHours` and `lookMaxHours` (2 to 72 hours before the close), `sideRule` (yes or no), `arms` (a letter and a price band each, at most 3), `contracts` (1 to 3), `limitSlip`, `hold` (settlement only), `registeredAt`, `forwardReadDate`, `rearmAt`, `kill` (`afterFills`, `netBelow`, `lossStreak`) and `returnRule` (`coolOffDays`, `pf`, `fills`). `validateLongholdRule` refuses the whole registry if any field is out of range or an id repeats.

What is read each minute, once a rule is registered (public GETs, no key, injected by the caller):
- at most 1 series list read (`GET /markets?series_ticker=...&status=open`), round robin over every (rule, series) pair, only to CHOOSE;
- at most 3 single-market reads (`GET /markets/{ticker}`) to PRICE the chosen markets;
- every 5th minute (offset 2), at most 3 single-market reads to settle closed rows.
The tick stops starting reads 20 seconds after it began (`LIMITS.tickDeadlineMs`, checked before every read), and the settle sweep keeps its 8 second guard. An event id with a slash or other unsafe character is skipped and counted, never written. So at most 4 requests in a normal minute and 7 in a settle minute, and none while an armed test order is on. L1 makes none of these reads, and a failed or slow read changes nothing else in the minute (the block is the very last step and swallows every error). With no rule, zero requests.

Choice: per event and arm, among the event's open markets inside the look window (the first 15 minutes at or under `lookMinHours`) whose side price is in the arm's band, the market whose YES mid is nearest 0.5, ties by ticker. Not chosen by result. The row is then priced from the single-market read, never the list read (the Forensics audit found the list read is a copy up to about 11 seconds old): quote seen (YES bid and ask), the touch, the would-be price (touch plus `limitSlip`), `wouldFill` (the size at the touch covers the contracts), and `source: "single-market"`. A fresh quote that left the band records nothing.

Stored: `kalshiLongholdRows/{rule}_{arm}_{event}` (created once, so two processes during a deploy cannot double-log), fields: rule, arm, event, ticker, series, side, contracts, quote, price, depth, wouldFill, secondsLeft, closeMs, atMs, and on settlement result, won, pnl (cash basis, fee 0.07*p*(1-p) per contract unrounded, times contracts) and settledAtMs. The latch is `kalshiLongholdControl/latch`. No client rule opens either; nothing that decides an order reads either.

Latch: `armVerdict` replays settled, fillable rows per arm from the rule's `rearmAt` and trips on net under `kill.netBelow` after `kill.afterFills` fills, or `kill.lossStreak` losses in a row. It is sticky (a later recovery does not lift it), stored with the `rearmAt` it tripped under, and a latched arm records nothing new. Only a reviewed edit that moves `rearmAt` re-arms it. An unreadable latch writes nothing.

Return: reported by the nightly report as numbers (`fillsSinceRearm`, `pfSinceRearm`, `statsMet`), with `ownerApprovalNeeded: true` always. The cool-off is the reviewed edit's job.

Nightly report (reads the newest 2000 rows, so it truncates older ones): `longhold.rules[].arms[]` with counts, PF, net, days, latch state and the return numbers. No ticker, event or id. Present only when a rule is registered.

Registry row: the Strategies registry (`strategies-registry.json`) has no row because no rule is registered. A first configuration adds one Shadow row in the same pull request.

## Phase 2: the switched-off order path (design only, NOT built)

What it would take, in order: (1) a first configuration that passed its registration as a paper log, with the paper record read at its date; (2) an order path that reuses the second slot's guard rails (`kalshiSlotLib`, `kalshiSlotRunLib`, `docs/SECOND_SLOT_DESIGN.md`) instead of a new one: the one entry gate, the direction lock, the shared 5.5% window cap and 12% stop, the size lock (`maxContractsFor`) extended with a per-series entry and a contracts-per-order field of at most 3; (3) caps in code for this class (per order, per day, lifetime open total) scaled from the sizing base with a hard dollar ceiling; (4) a client order id both processes compute identically (rule, arm, event), so a deploy cannot double an order; (5) kill and return rules from the paper rule carried over and latched, never re-armed by a stored value; (6) the exit watch left to sell nothing it did not open and the hold-to-settlement path never moving a stop; (7) its own off-equivalence fixture, a master switch false in code, and a nightly report section; (8) a 24 hour window for the held position in the loss stop, so a position held for days is counted as lost while open.

Owner popup content needed before any code for it is written (the owner's own popup, with an exact spec): the strategy name and its registration; series list; side and price band; look window; contracts per order (1 to 3); the dollar caps (per order, open total, lifetime); the kill rules and the return rule; the counterparty in one sentence; the paper record at the read date (n, cash PF at +1c, second half); and the words "this places real orders". Nothing in this pull request can send an order.
