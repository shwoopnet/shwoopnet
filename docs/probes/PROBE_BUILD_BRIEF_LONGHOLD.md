# Build brief for the Chief of Staff: a switched-off order path for ONE contract on a market that is not a 15 minute market (Nov 12, 2026)

**Status: a brief for a build the owner approved on Nov 12, 2026 (through the Executive Assistant, relayed by the Head of R&D): "Main builds, switched off, the order path for a 1 contract order on a non-15-minute market."** This desk wrote no code for it. Nothing here is live. Building it authorises no order: every probe that would use it is UNPROVEN, conditional on its own research read (the owner ruled out pre-evidence orders the same day), and needs the owner's own popup with its exact spec.

Every code fact below was checked against `origin/main` on Nov 12. Background and the full gap list: `PROBE_SCOPE_SPORTSSPREAD.md`.

## 1. What to build: a "named market, one shot" entry in the second slot

The smallest path that serves all three waiting uses (a sports spread single, a politics single, later a combo) is NOT a new scanning strategy. It is a registry entry that names its order:

| Field | Meaning | Bound in the validator |
|---|---|---|
| `ticker` | the exact market, written in code by the reviewed edit that admits the probe | must match a per-series pattern written from REAL tickers; the series must be on a new long-hold allowlist and reserved to this id |
| `side` | yes or no | fixed |
| `priceMax` | the most it may pay | 0.05 to 0.90; a NO above 0.50 is a favourite held to settlement and needs the owner's written exception named in the entry's registration |
| `count` | contracts | 1 (the probe-candidate cap on branch `claude/probe-desk`, `SLOT_PROBE_MAX_CONTRACTS`); 3 for a politics single only by a reviewed edit of that cap |
| `notBeforeMs`, `notAfterMs` | the window in which the one order may be sent | both required; at most 24 hours apart; both must be BEFORE the market's scheduled close as listed while it is open |
| `lookField` | which time field the window was derived from | one of the known-in-advance fields (section 3); never the realised close |

One immediate-or-cancel buy at the ask if it is at or under `priceMax`, once: the client order id is fixed per entry (`S-<id>-<ticker>-1`), so a second instance, a retry or a second minute cannot send again. No fill is not retried. Hold to settlement. This is what the Head of R&D's pipeline assumes for a politics single (3 to 4 build days).

Why not a scanner now: the sports rule needs a market chosen from many per game, and a look two days out. With a named entry, research names the market from its own read-time join and the bot only executes. A scanner (the "long look" entry mode and the per-series due-check in the scoping file, gaps 2 to 4) is a second step, worth building only if a rule passes and needs repeating.

## 2. The parts, in build order

| # | Part | File | Notes |
|---|---|---|---|
| 1 | **The stop fix, first and on its own.** An open slot order older than 24 hours drops out of the shared 12% stop: `slotRiskForBotRisk(slotOrders, since)` skips every order whose `ts` is before `since`, and `botRisk` passes the last 24 hours (or the session start). An order still OPEN must count as lost whatever its age; only settled results are windowed | `functions/kalshiSlotLib.js` (`slotRiskForBotRisk`, and so `slotRiskContract.day`) | Its own pull request. Must leave every figure for OICORE and EVENT830 unchanged (their orders settle within minutes): prove it with the existing parity gate plus a new one, and the off-equivalence fixtures must stay byte identical. The same question applies to L1's own `botRisk` loop, which reads L1 orders from `since`; L1 never holds past a window, so it is out of scope, but say so in the pull request |
| 2 | The named entry, the long-hold series allowlist and ticker patterns, the validator bounds | `kalshiSlotLib.js` | Off by default the way `SLOT_PROBE_CANDIDATES` is on `claude/probe-desk`: a complete entry outside the registry until its own switch is exactly true. Reuse that mechanism (switch, 1 contract cap, sticky budget, hold permission) rather than a second one |
| 3 | The engine step | `kalshiSlotRunLib.js` | A named entry makes a job only inside its window; it reads that ONE market (public), the position, then goes through the same transaction, direction lock and `slotOrderCheck`. The 15 minute time test (`leftMinSec`, `leftMaxSec`) must not apply to it and must stay exactly as it is for everything else |
| 4 | The quote | `functions/index.js` | No series list read: the engine reads the named market itself. Nothing is read outside the window |
| 5 | The budget | `kalshiSlotLib.js` | The candidate budget (`SLOT_PROBE_BUDGET`, `probeState`) per id. For politics and parlays also ONE shared counter replayed from the orders of every entry tagged for that budget: $200 lifetime (`docs/POLITICS_RULES.md`), and the $40 parlay stop |
| 6 | Hold and exits | `kalshiSlotRunLib.js` | Hold to settlement needs the id on the hold list (the candidate list carries this). The exit pass looks back 25 minutes only (`EXIT_LOOKBACK_MS`), so nothing would sell a long-held order if it became a hedge: that is why the series must be RESERVED to the entry, so no other strategy can take the other side. State it; do not widen the exit pass |
| 7 | The settle sweep | `kalshiSlotRunLib.js` (`runSlotSettle`) | Works today with no age limit, reading each open order's market every minute. Throttle a long-held order to every 10th minute until its scheduled close is within an hour (about 2,900 public reads per two day order otherwise) |
| 8 | Shard | none | `availableFor` already uses the market's own `exchange_index`; too little money there logs `shard_short` and sends nothing. The low-money phone alert reads only L1's shortages, so it will not fire for this: say so, or extend it |
| 9 | Page and alerts | `index.html`, `kalshiPushLib.js`, `kalshiLib.js` | Display only: gate Y31 wants every slot market on the relay (exempt long-hold entries on purpose); `kalshiCloseFromTicker` parses a 15 minute ticker's Eastern time and must show "closes <scheduled time>" from the stored field instead; names for the series; the Own stops line; the Strategies page tile |
| 10 | Report | `kalshiReportLib.js` | Slot rows already carry everything; add the entry's scheduled close so a two day hold is readable |

## 3. The time field (the Head of R&D's instruction)

The look and the entry window are computed ONLY from a field known in advance and stored on the order: the market's scheduled close as listed while it is open, or `expected_expiration_time`, or the event's `occurrence_datetime`. Never the realised close. The engine checks, at send time, that the market still lists the same scheduled time the entry was written against (within a tolerance in the entry); a market whose schedule moved sends nothing and logs a skip. Why: the sports research look was measured from close times that look like the moment each market closed after its game, which cannot be known two days ahead; Refinement is fixing that definition before the read.

## 4. What must not change

- L1, the exit watch, the size lock, OICORE and EVENT830: no behaviour change; both off-equivalence fixtures byte identical in every pull request of this build.
- The 15 minute entry gate: unchanged for every existing strategy.
- No resting orders, no cancel path, no request-for-quote flow: none is needed for a single, and the Chief of Staff has ruled them out.
- No new host. No stored value can add an entry, raise a count or flip a switch.

## 5. Gates the build should ship with

Off by default and the production gate refuses the id; an entry outside its window, past its scheduled close, above `priceMax`, on an unlisted series or with a moved schedule sends nothing; exactly one order ever per entry (second instance, second minute, after a no fill); the stop counts a three day old open order in full and counts settled ones only inside the window; OICORE and EVENT830 figures identical before and after; the budget is sticky and the shared politics counter sums across entries; the settle sweep books an old order; the series is reserved; the page shows the stored scheduled close.

## 6. Size, days, and what it does not give

About 3 to 4 build days for parts 1 to 8, 1 for the page, 1 to 2 for the security review; three pull requests (the stop fix; the entry and engine, off; the page). Deploy order as always: `deploy-push.sh`, then `deploy-sizing.sh`.

A combo needs more and is NOT in this brief: fractional contract counts (dollars over price), the combo exchange shard, and possibly the request-for-quote flow, whose 3 second confirm window a one minute function cannot serve. By hand remains the only route for a combo.

## 7. The conditional probes that would use it (none approved; each needs its read and its popup)

| Probe | Entry it would be | Condition | Honest odds |
|---|---|---|---|
| Sports spread cheap cell | research names one market: YES, `priceMax` 0.14, 1 contract, window about 45 to 46 hours before the scheduled start | Refinement's read is PASS (n 100 or more, profit factor 1.5 at +1c, lower bound above 0, z 3.1) AND the look definition is fixed to a known-in-advance time | 3% to 5% to pass. $5 budget, about $0.17 an order. Needs a named loss budget: none in the rulebook covers a sports single |
| Approval NO side / nothing happens | NO, `priceMax` 0.88, 1 contract, at most $5 at risk per market, one market per story, settling within 30 days | Paper evidence first (`docs/POLITICS_RULES.md` sections 1 and 5). The paper read so far leans AGAINST it, so this desk does not expect to write its popup. A NO above 50c held to settlement is the favourite side: the rulebook allows it for this family only, and the popup must quote that | No evidence for it; evidence against |
| Politics single | either side, 10c to 90c, 3 contracts, inside the $200 budget, kill at net under -$15 after 20 fills or 5 losses in a row | A paper edge and the owner's popup for the exact market | None yet |
