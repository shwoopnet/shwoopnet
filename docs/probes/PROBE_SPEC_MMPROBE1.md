# Probe spec: MMPROBE1 (resting quotes on ONE strike of the hourly Bitcoin ladder)

**Status: build-ready DRAFT, Nov 12, 2026. Not built. OFF by default when built. Nothing here is live, approved or deployed.** No code for it exists on any branch; this is the design a build would follow.

**UNPROVEN.** Its first purpose is to answer the one question the simulation (MMSIM1, MMHOUR1) cannot: do real resting orders fill the way the queue model says. It is not sized to make money and is not presented as an edge.

## 1. What it is, in one paragraph

Once an hour, 50 minutes before an hourly Bitcoin "above K" market (`KXBTCD`) closes, the bot picks ONE strike near the money and rests one contract on each side at the best bid (a YES bid, and a NO bid sent as a YES ask one cent higher). Both orders are post-only and expire by themselves at the exchange 15 minutes before the close. If both fill, the two legs cancel out for a one cent gross gain. If only one fills, the bot sells that one contract at the bid 15 minutes before the close. It never reprices, never adds, and never holds more than one contract.

## 2. Classification card and the rules it touches

`MMPROBE1 | two-sided resting quotes + time flatten (liquidity provision, no directional signal) | win-rate n/a; many 1c gains, some 5c to 30c losses on a one-sided fill; at most $1 open, $10 lifetime; group: hourly Bitcoin ladder (no other strategy trades it) | stage Idea, proposed Probe`

- **Uniqueness (lifecycle 7d, 7f rule 6).** The owner ruled that a no-signal liquidity-provision family counts as unique; its signal check is not applicable. It still needs the correlation check (not yet measured; research says about 32 overlapping days) and the declined-list check. Declined rows checked Nov 12: "maker or resting entries on gold" is a one-sided directional entry on another market, not this.
- **It needs two owner exceptions, which the popup must quote.** (1) `docs/CHARTER.md` brief checklist item 5: "no short round trips". (2) `docs/POLITICS_RULES.md` section 6: "Market making: stays on zero-fee series" and "popups 45 to 48 ... are asked only if the Nov 24 read passes". Whether this series charges a maker fee is NOT KNOWN (the research treats it as a bound); if it does, the first rule blocks the probe unless the owner excepts it.
- **Both sides of one market.** The direction lock forbids opposite sides between strategies. Here both legs are the SAME strategy's own position, which 7d allows ("paired within its own position"). The series is reserved to this probe so no other strategy can meet it there.

## 3. Entry, exit, order (every number a constant in code)

| Step | Rule |
|---|---|
| Market | `KXBTCD`, the event closing at the next top of the hour. No other series; the order builder refuses anything else |
| Strike choice, at T minus 50 min | Among the strikes with a bid on both sides, a spread of exactly 1c and a YES mid of 0.15 to 0.85: the one nearest 0.50. None qualifies: no orders this hour |
| Orders | Two, sent once: YES bid at the best YES bid `b` (`side: "bid"`, `price: b`), and a NO bid at the best NO bid `q` (`side: "ask"`, `price: 1 - q`). Each: `count: "1"`, `time_in_force: "good_till_canceled"`, `post_only: true`, `expiration_time` = T minus 15 min, `cancel_order_on_pause: true`, `self_trade_prevention_type: "maker"`, a fixed client order id (`MM-<ticker>-Y`, `MM-<ticker>-N`) |
| While resting | Each minute: read the two orders' status and fill counts. Nothing is repriced or re-sent |
| Both filled | The legs net to zero at the exchange; the gross gain is `1 - b - q` (1c). Nothing else to do |
| At T minus 15 min | The exchange has expired anything unfilled. The bot confirms, cancels any order still resting, then reads its position in that one market. One contract held: sell it with an immediate-or-cancel order marked `reduce_only: true`, limit 15c through the bid. Not filled: try again each minute to T minus 2 min, then hold to settlement (the loss is at most what was paid) |
| Size | 1 contract a side, 1 strike an hour, 2 resting orders at most, net position at most 1 contract. Constants; the body builder refuses any other count |

Field names and values are from Kalshi's public API documentation as read on Nov 12 (`create-order-v2`, `cancel-order-v2`, `get-orders`). Two things the documentation does not say, and a supervised dry run must show before any real order: what `post_only` does when the order would cross (rejected or repriced), and that a duplicate client order id is refused for a resting order as it is for the bot's immediate orders.

## 4. Caps and isolation

| Limit | Value |
|---|---|
| Open exposure | at most 1 contract net, about $0.85, plus one unfilled resting order |
| Lifetime loss budget (its own stop) | **$10**, open counted as lost, sticky, replayed from its own records |
| Daily loss | $3, then no new quotes until the next Central day |
| Length | stops by itself after 150 quoted strike-hours or 21 days from its review date, whichever is first |
| Hours | all hours (the research leads on the 12 to 18 Central block and deep queues are read from the records afterwards, not used to choose) |

- **Its own function.** `kalshiMmProbeTick`, every minute, with its own constant switch `MM_PROBE_ENABLED = false` AND the server's live switch. It is not inside the bot's minute function, so a slow or failing probe can never delay or fail an L1 or slot order, and the off-equivalence fixtures are untouched. It holds the same two Kalshi secrets as the bot (a third function with the key; the security agent must weigh that).
- **Its own records.** Collection `kalshiMmProbe` (admin read, no client write): one document per strike-hour, created in a transaction BEFORE the orders are sent (the claim), holding both client order ids, prices, queue sizes seen, fills, fees and the flatten.
- **Shared 12% stop.** The bot's stop reads L1 and slot orders only. The probe is NOT added to it (that would change the bot's tick and its fixtures). Instead the probe checks the account stop itself before quoting each hour (it reads the last 24 hours of orders once and refuses if less than $2 of room is left), and its own exposure the stop cannot see is bounded at $1 open and $10 lifetime. That gap is stated here, not hidden.
- **Size lock, slot caps.** Not involved: it is neither an L1 order nor a slot order, and `KXBTCD` is on neither list. Its own constants are its lock.
- **Stop and Flatten.** The probe reads the halt first every minute: halted, or the session not running, means cancel its resting orders and sell its contract. Flatten gets one hook that cancels the probe's resting orders BEFORE it reads positions (otherwise a resting order could fill after Flatten finished). The hook is behind the probe's switch.
- **Exit watch.** Untouched. It works from L1's and the slot's own order documents and would never see this market.
- **Money.** The series' exchange shard is read from the market object; under $3 there means no quotes and a skip record. The bot cannot move money; the owner does.

## 5. Kill

No automatic restart after any of these:
1. $10 lifetime budget reached (or would be with open exposure counted as lost).
2. Any order whose answer was lost, or any state the bot cannot reconcile (an order it did not record, a position larger than 1): cancel everything in that market, sell what is held, latch off.
3. The flatten failed to sell on 3 strike-hours (the "sell at the bid" assumption does not hold).
4. 150 strike-hours or 21 days reached (the measurement is complete).
5. By reviewed edit: the Nov 24 research read is FALSIFIED (under 1.0 on about 400 events).

## Return

After a kill by rules 1 to 3: a 14 day cool-off, a written account of what went wrong, a simulation rerun on the same strike-hours showing why, then the owner's approval and a reviewed edit of the review date. After rule 4: the result is read (section 6) and any larger version is a NEW probe with its own popup.

## 6. What is measured, written first

The book recorder (`record-book.yml`) records the same market, so the MMSIM1 queue model can be run afterwards on exactly the strike-hours the probe quoted. Compared per strike-hour and side: did the simulation say "filled", did the real order fill, and the result of each one-sided fill.

| Outcome over 150 strike-hours | Label |
|---|---|
| Real fills at least 70% of simulated fills AND the mean result of real one-sided fills within 1c of the simulated | "Fills as simulated": the simulation's evidence stands as it is |
| Real fills under 50% of simulated, or one-sided fills worse by 2c or more | "Simulation overstates": every MM simulation figure is discounted and said so |
| Between | No call |

Also recorded, because nobody knows them yet: the maker fee actually charged per fill, whether `post_only` orders are ever rejected, and how often the flatten finds a bid. None of this can show a profit: at one strike the expected result is a few cents a day either way.

## 7. New code and cost

| Piece | What | Size |
|---|---|---|
| `functions/kalshiMmProbeLib.js` | Pure parts: strike choice, order bodies, the state machine for one strike-hour, the budget replay, reconciliation | the largest part; about 2 build days with tests |
| Store and wiring | The claim transaction, the records, the scheduled function, the Flatten hook, `firestore.rules` for the collection | about 1.5 days |
| Kalshi calls new to this repo | a resting order (`good_till_canceled`, `post_only`, `expiration_time`), cancel (`DELETE /portfolio/events/orders/{order_id}`), list orders (`GET /portfolio/orders`), `reduce_only` on the flatten | each needs a gate and a dry run |
| Tests | see section 9 | about 1.5 days |
| Review | the security agent, a supervised dry run with the owner watching the Kalshi order page | about 1 to 2 days |

**Monthly cost:** one more scheduled function, 1,440 runs a day, most returning at once; about $1 to $3 of compute and a few hundred Firestore writes a day. Kalshi request load is a few requests a minute, far inside any tier.

## 8. Failure modes

| What can go wrong | Containment |
|---|---|
| **Stranded resting order** (the function dies, a deploy, an outage) | Every order carries `expiration_time` at T minus 15 min, so the exchange removes it without the bot. `cancel_order_on_pause` covers an exchange pause |
| **One-sided fill** | The normal case, about 4 in 10 strike-hours in simulation. Sold at T minus 15 min; worst case the price paid (under $0.85) |
| **Flatten finds no bid** | Retried each minute to T minus 2 min, then held to settlement. Counted; three such hours kill the probe |
| **Flatten opens the opposite side** | `reduce_only: true` on an immediate-or-cancel order; and the position is read first |
| **Restart between the claim and the send, or two instances** | The claim document exists before any send and the client order ids are fixed, so a second sender is refused; on start the bot reads its orders in that market and adopts what it finds |
| **Lost answer to a resting order** | Not retried. The bot lists its orders in that market, cancels them, sells any contract, and latches off |
| **Both legs fill at different sizes** | Not possible at one contract |
| **Fast market** | One strike, one contract. This is why the probe is one strike and not the simulation's seven |
| **Self trade** | The two legs are one cent apart and cannot cross; `self_trade_prevention_type: "maker"` is set anyway |
| **Stop or Flatten pressed** | Halt is read first every minute; Flatten's hook cancels the resting orders before it reads positions |
| **Fee is not what research assumed** | Recorded per fill; the budget bounds the cost of being wrong |
| **No money on the shard** | No quotes, a skip record |

## 9. Tests and gates a build must ship with

Off by default and the production path makes no call; the body builder refuses any series, count, price or time in force but the ones above; every order carries the expiry and post-only; the claim comes before the send; a second instance sends nothing; a lost answer cancels, sells and latches; the flatten is reduce-only and never larger than the position; the budget is sticky; the halt cancels; Flatten's hook runs before its position read; nothing in the bot's tick, the exit watch or the slot libraries imports the probe; the off-equivalence fixtures are byte identical; the security scan knows the new function.

## 10. Days to a first order

8 to 12 working days from an owner YES: 5 to 6 to build and test, 1 to 2 for review and the dry run, then the merge, the rules deploy and the function deploy, and money on the shard. The owner's two exceptions (section 2) come first.

## 11. The popup the owner would see

> **Build and run a tiny market-making probe: MMPROBE1 (unproven)?**
>
> What it does: once an hour, on ONE strike of the hourly Bitcoin market, the bot rests 1 contract on each side at the best bid. If both fill it makes 1c. If one fills it sells that contract 15 minutes before the close. Orders expire at the exchange by themselves.
>
> Size and loss: never more than 1 contract held, at most about 85c at risk at a time. It stops for good at $10 lost, and stops by itself after 150 hours of quoting or 21 days.
>
> Why: the simulation shows a small profit, but nobody knows whether real orders fill the way it assumes. This measures that. It cannot show a profit at this size.
>
> It needs two exceptions from you. Your rule "no short round trips" (Charter checklist, item 5), and your Nov 11 answers "market making stays on zero-fee series" and "first-live questions only if the Nov 24 read passes". We do not yet know whether this series charges a maker fee; the probe would find out.
>
> Cost: about 6 days of build and review, about $1 to $3 a month to run, one more function holding the trading key.
>
> - **Wait for the Nov 24 read, then decide (Recommended)**: research expects that read to fall short, and the build is the most complex of any lead
> - **Yes: grant both exceptions for this probe only and build it now**
> - **No**
