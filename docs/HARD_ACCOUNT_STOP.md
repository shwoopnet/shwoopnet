# Hard account stop (Nov 13, 2026)

The owner's decision (via the Risk Analyst, "Yes, add it in code"): when the bot's trading result falls 40% of the account below its own best point, ALL new buys (L1 and every second slot strategy) stop and stay stopped until the owner restarts them. Exits keep running. It is a CEILING on top of the 12% 24 hour stop, not a replacement. No figure in this file is a live figure; the numbers are invented.

## The definition

1. **What is measured: cumulative cash trading equity.** The sum of the cash result of every settled or sold order, L1 and the second slot together, since the constant `HARD_STOP.rearmAt` (2026-11-13 00:00 UTC). Each order is booked on the cash basis the other stops use (`settledFields` for L1, `accountOrder` for the slot: the real fill and fee, an early sell at its stored result, an unreadable exit as what was paid). Orders closed by hand are not the bot's result and are left out. Open orders are NOT counted (the 12% stop counts them at worst case; this ceiling judges closed results, and the overshoot past the line is bounded by the 5.5% window cap and the order ceilings).
2. **The peak** is the highest value that equity has reached since `rearmAt`, starting at zero.
3. **The drawdown** is the peak minus current equity.
4. **The line** is `HARD_STOP_FRACTION` (0.40) x the **sizing base recorded at the peak**: the account value at its best, the same `base` the bot sizes on (balance minus the part skimmed to savings). The base at the peak is stored beside the peak and is refreshed ONLY when a new equity peak is made; between peaks it is frozen.
5. **Trip:** drawdown at or above the line. The latch is set, a `hard stop` event is written (critical in the bell), a phone alert goes out, and from the next minute no strategy places a buy.
6. **Deposits and withdrawals never enter the measure.** They are not orders, and the account balance is never read (the code never names it). A deposit made after the peak does not enlarge the line; a withdrawal is not a loss and does not shrink it.

**Worked example (invented numbers).** An $800 account trades and its results reach +$100: account value at the peak is $900, so the line is 40% x $900 = $360. The bot then loses $360 from that peak and all new buys stop. If the owner deposits $5,000 afterwards the line is still $360, and if the owner withdraws $500 it is still $360 and not a loss.

**Fraction validation.** The constant must be within 20% to 40% (`validFraction`). A shipped value outside that range is never used as written: above 40% is clamped to 40%, below 20% or not a number becomes 20%, so a bad edit can only make the stop stricter. A gate (HS6) fails the build if the constant is out of range. The module never throws, because the exit watch loads it too.

## Why the denominator is the base at the peak

Candidates and the tradeoff:

* **The current sizing base.** Falls as the account loses, so the line would shrink while the account fell and the stop would trip at less than 40% of the best point. Wrong.
* **The raw balance.** Moves with every deposit and withdrawal; a deposit would look like a new high and a withdrawal like a loss. Excluded on purpose.
* **A fixed dollar line** (as the gold latch). Safe but ignores a growing account until a reviewed edit. Rejected because the owner asked for a fraction of the account.
* **The base at the peak (chosen).** Frozen at the best point, so it answers "40% of the account when it was at its best". It lags: the base is refreshed by the weekly review, so on a fast rising account it is a little BELOW the true account value (a tighter line, the safe direction). A deposit made before a new peak is included in that peak's base (it is part of the account value then); a deposit after it is not.

**Fail closed.** The base at the peak is stored in the authoritative record. If it cannot be read, the SMALLEST sizing base seen since the start constant is used (a tighter line, never a looser one; it is tracked in the same record). If no base can be read at all, the record says `unreadable` and the ticks place no new buys.

## How it works (no change to the tick's reads or writes)

* `kalshiHardStopCheck` (scheduled every minute, keyless, no order) reads the L1 and slot orders since `rearmAt`, the sizing document and its own state document, replays the equity and judges.
* Authoritative record: `kalshiLiveControl/hardStopState` (only this function writes it; admin read, no client write). Cache for the ticks: the `hardStop` field on `kalshiLiveControl/sizing`, which `runL1Tick` already receives. The tick's full write of the sizing document can overwrite the cache; the checker restores it from the authoritative record within a minute, and the latch itself cannot be lost.
* `runL1Tick` looks only at that value (`hardStopBlocks`) and returns before any entry; `index.js` passes the same verdict to `runSlotTick` (`hardStopBlocked`), which skips with reason `hard_stop`. No new read or write on a normal minute: `offEquivalence.json` and `offEquivalenceIndex.json` are byte identical.
* **Exits are never gated.** The exit watch, Flatten, the slot exit pass and the settle sweeps do not look at it.
* **Fail closed:** the ticks block on a tripped latch, on a record that says `unreadable`, on a record that is not an object, and on a record of this generation whose heartbeat is older than 15 minutes (the checker went silent). Unreadable orders, an unreadable sizing document, no base, an order that cannot be priced: the checker writes `unreadable`.
* **Alert:** a critical `hard stop` event (the bell) and a field on the session document that the existing phone alert trigger turns into an issue alert, claimed once per generation in a transaction (`kalshiLiveControl/hardStopAlert`), retried until it goes out, every error swallowed. No Kalshi key.
* **Restart:** only a reviewed code edit that moves `HARD_STOP.rearmAt` to a later time (and the owner's approval). The stored latch of an older generation is then ignored and the equity peak starts again from zero. Nothing on the page, no callable and no stored value can clear or loosen it (gate HS7).

## Deploy order

`bash functions/deploy-sizing.sh` deploys the checker and the minute function in one command. If the minute function is live before the checker has ever run, the field is absent and an absent field means "not yet evaluated", which does NOT block (this keeps the recorded replays byte identical). So **the stop does not protect until the checker's first run**, normally within a minute of the deploy; check the sizing document for a `hardStop` field with `status: "ok"` after deploying. From then on a silent checker blocks buys after 15 minutes. `bash functions/deploy-push.sh` is needed for the phone alert text, and `firestore.rules` already covers the new documents (`kalshiLiveControl` is admin read, no client write). Deploy the push script first.

## What it cannot do (gaps)

* It judges closed trades. A position still open is not counted, so the account can end past the line by at most what was open (bounded by the 5.5% window cap and the order ceilings).
* It cannot see a deposit, a withdrawal or a manual trade: those never enter the measure, so a manual loss is invisible to it (by design: the stops follow the bot's trades).
* The base lags (weekly review). The first evaluation after `rearmAt` uses the base then in force.
* The tick's full write of the sizing document can overwrite the cache in the few seconds between its read and its write; if that coincides with the moment of a trip, one minute's buys can go out before the checker restores the cache. The latch itself is not lost.
* A just-started session with no sizing base yet is blocked until the first tick writes it (about two minutes).
* An armed single test order (`runArmedTick`) is a separate, owner-started act and is not gated.
* Orders are replayed in placing order, not settlement order; with a line of this size that cannot change the result materially.
* If Firestore itself is down, nothing here can act (neither can the tick).
* The read cost is the orders since `rearmAt` (a few a day of each), cached as the gold checker's are.
