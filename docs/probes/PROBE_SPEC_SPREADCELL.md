# Probe spec: SPREADCELL (sports spread, YES at 5c to 14c, held to settlement)

**Status: build-ready DRAFT, Nov 12, 2026. OFF by default. Nothing here is live, approved or deployed.** The code is on branch `claude/slot-non-quarter` (stacked on `claude/probe-desk`). It cannot trade until (1) the research read W-SPREAD-CELL1 passes, (2) the owner approves this exact probe and the exact markets in a popup, and (3) a small reviewed edit flips `SLOT_PROBE_SWITCH.SPREADCELL` and fills `SLOT_HORIZON_NAMED`. No order before its own research read.

**UNPROVEN.** The rule is the best of about 58 cells in an earlier test (a lead, not a finding). A cell with no true edge shows this much about 2 percent of the time. It is not presented as an edge anywhere.

## 1. What it is

For a sports spread market the owner has named, about one to two days before the game's scheduled time, if the YES ask is 5c to 14c, the bot buys ONE contract of YES at the ask and holds it to settlement. Most orders lose their 5c to 14c; a few pay about 86c to 95c.

## 2. Rule, in code (`SLOT_PROBE_CANDIDATES`, entry type "horizon")

| Item | Rule |
|---|---|
| Series | exactly KXMLBSPREAD, KXNBASPREAD, KXNCAAFSPREAD, KXNCAAMBSPREAD, KXNFLSPREAD, KXNHLSPREAD (the 15 minute list is separate and unchanged) |
| Market | only a ticker NAMED in `SLOT_HORIZON_NAMED` (empty now; nothing is discovered); strict ticker shape per series |
| Look | the market's scheduled time: `expected_expiration_time`, else `occurrence_datetime`; more than 24 h and at most 48 h ahead (hard bound 72 h). Missing, in the past, or `close_time` more than 1 h before it or more than 7 days after it: no order |
| Side, price | YES only; the YES ask 5c up to 14c (the registered bucket is ask under 15c) |
| Choice | one order per event; of an event's named markets the one whose YES mid is nearest 0.5 |
| Order | one immediate-or-cancel buy at the ask seen, id `S-SPREADCELL-<ticker>-1` (fixed, so a second instance is refused by Kalshi); never retried |
| Size | 1 contract (`SLOT_PROBE_MAX_CONTRACTS`) |
| Exit | none. Held to settlement. The slot exit pass holds it even if the strategy is later removed from the registry |

## 3. Limits

| Limit | Value |
|---|---|
| Lifetime loss budget (its own stop) | $10, open orders counted as lost, sticky (`SLOT_PROBE_BUDGET`, `probeState`) |
| Open positions | at most 5; one per event |
| Shared stop and window cap | the slot caps, the shared 12% stop and 5.5% window cap. An open order older than 24 h still counts as lost in the stop (it would otherwise leave the 24 hour look-back while open) |
| Direction | YES only, so it can never sit against another order's opposite side |
| Shard | an order with no readable shard is refused; the money on the shard is checked like any slot order; a refusal from Kalshi switches only this probe off and logs that the shard may be wrong or short. The shard of these series is NOT known in code and must be checked in Kalshi before activation |
| New read | one public market list per named series every 5th minute, only while registered and naming a market. With the switch false nothing is read |
| Flatten | still closes any position when the owner presses it |

## 4. Kill

1. Budget: its own record reaches minus $10, or would with every open order counted as lost (this binds first).
2. 30 losses in a row.
3. Net below $0 at any point from 100 settled fills.
4. The research read, or the shadow record S2, comes back FAIL: a reviewed edit switches it off.
5. A lost answer to an order ends the session and latches the strategy (the slot's existing rule); a plain refusal latches only the probe.

## 5. Return

After a kill: 14 days off, then a new registration and the owner's approval. Re-arming is a reviewed edit that moves `reviewedAt`; nothing resumes on a date.

## 6. Activation checklist (in order, each its own step)

1. The research read passes: W-SPREAD-CELL1 with n of 100 or more events, profit factor 1.5 or better at +1c, and a one-sided z of 3.1 or more. A LEAD or UNDERPOWERED result is not a pass.
2. The owner answers the popup below for the exact markets.
3. A small activation pull request: set the switch to true, put the approved tickers in `SLOT_HORIZON_NAMED`, set the candidate's `reviewedAt`, `forwardReadDate` and `SLOT_LAST_REVIEWED_ON` to that day, update on purpose the gates that pin the registry to two strategies, add the page text and a changelog line.
4. Confirm in Kalshi which exchange shard these series use and that it holds money; confirm the scheduled-time fields and the `close_time` gap on the real listing (not done: the fields and the 7 day tolerance are unverified against live data).
5. Deploys, in order: `bash functions/deploy-push.sh`, then `bash functions/deploy-sizing.sh`.

## 7. The popup the owner would see

> **Start a tiny live probe: SPREADCELL (unproven)?**
>
> What it does: one to two days before a sports spread game you name, if YES costs 5c to 14c, the bot buys 1 contract of YES and holds it to the end of the game.
>
> Size and loss: 1 contract an order, at most about 17c lost per order, at most 5 open, one per game. It stops itself for good at $10 lost in total, and sits inside the account's 12% stop.
>
> Honest odds: UNPROVEN. The rule was the best of about 58 cells in an earlier test and passed only if the new research read does.
>
> Still open: the exchange shard of these markets must be checked; the named markets: (list).
>
> Kill: $10 lost, 30 losses in a row, or a net loss after 100 fills. Return: 14 days off, a new registration, your approval.
>
> - **Wait for the research read (Recommended)**
> - **Yes, start it for the named markets at 1 contract with a $10 budget**
> - **No**

## 8. Tests

`node test/slotNonQuarterGates.test.js`: SN1 off by default and no call; SN2 the validator bounds; SN3 tickers and the named list; SN4 the gate and the budget; SN5 end to end and one shot; SN6 the pick; SN7 the scheduled-time look; SN8 the listing read; SN9 the loss stop past 24 hours; SN10 no sell path; SN11 refusal and shard; SN12 nothing stored can enable it.
