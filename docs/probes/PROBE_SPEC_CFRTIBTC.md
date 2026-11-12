# Probe spec: CFRTIBTC (Bitcoin 15 minute market, spot-index model, cheap side)

**Status: build-ready DRAFT, Nov 12, 2026. OFF by default. Nothing here is live, approved or deployed.** The code is on branch `claude/probe-desk`; the probe cannot trade until a reviewed edit flips its switch, and that edit is made only after the owner's own popup for this exact probe.

**UNPROVEN.** This is a tiny live test to learn from real fills: an information purchase, not an edge. It is below the research bar and the research session's own prior is about 1%.

**NOT ACTIVATABLE AS BUILT (the owner's ruling, Nov 12, relayed by the Head of R&D and the Chief of Staff).** No live probe may read two of the three spot venues the research rule uses (one needs a signed data licence for commercial use, one's terms are unread). The registered rule needs three venues; the code may now read one, so the reader returns no reading and makes no request, and the probe cannot trade even with its switch flipped (`VENUES_REQUIRED = 3`, `VENUES_ALLOWED = ["kraken"]`, test CB6). Section 13 says what the two forms that COULD run would need. Neither is registered, and no code changes until research has a result for one of them.

**CONDITIONAL ON THE READ (the Head of R&D, Nov 12). The owner has ruled out pre-evidence orders, so there is no route before the read.** This spec takes effect only if the research read clears, and a clear is not a pass:

| Step | When | What it means |
|---|---|---|
| First read | Nov 20 to 24 (50 Bitcoin rows, read once, bar profit factor 1.3) | A rule with NO edge clears this about 24% of the time, so a clear means RE-TEST, never "it works". Under 1.3: this spec is dead and the switch stays off |
| Re-test | a fresh 50 rows, about Dec 10 to 15 | A second clear is what makes a probe the honest next step |
| Honest first order | **mid December** | after both, the popup, the activation pull request and two deploys |
| Faster, only if the owner asks | Nov 26 to 30 after a first-read clear with no re-test | It buys fills, not evidence, and the popup must say so. An order before any read is ruled out |

## 1. What it is, in one paragraph

About three minutes before a Bitcoin 15 minute market closes, the bot rebuilds a Bitcoin spot index from the public trade lists of three spot venues and works out the chance the market settles YES (the settlement value is a 60 second average of a multi-venue index). If the CHEAPER side of the market costs 5c to 30c, the YES spread is 3c or less, and the model's chance for that side is at least 5c above its price, it buys ONE contract at the price seen and holds it to settlement. Most orders lose their 5c to 30c; about one in three would need to win for it to pay.

## 2. Classification card and the four uniqueness checks

`CFRTIBTC | settlement-index model, immediate entry on the cheap side + hold to settlement | low win rate (about 15% to 35%), many small losses, about $0.32 an order, $5 lifetime, crypto 15 minute group (shares it with OICORE) | stage Idea, proposed Probe`

| Check (lifecycle 7d) | Desk's reading (the Verification Analyst scores it, not this desk) |
|---|---|
| 1. Signal differs | A different data source: trade prices from three spot venues rebuilt into the settlement basis. Not a Kalshi price band. Closest existing idea: the spot-lead test, which is a VERSION of this (section 12), not a second strategy. |
| 2. Exit differs | Hold to settlement, which counts only when the entry rules differ and it does not interfere. Entry rules differ from OICORE (a model edge, not an open interest jump). It never takes the opposite side of any order (direction lock) and has its own loss budget. |
| 3. Correlation under 0.3 with every live strategy | NOT YET MEASURED, and a real risk: it buys the cheap side of the same market in the same minute as OICORE. If its daily result tracks OICORE's at 0.3 or more it is a duplicate and goes on the declined list. |
| 4. Declined list | Checked against every row of 7e on Nov 12. Not a favourite (it never pays more than 30c; the validator refuses a model entry above 50c). Not "Bitcoin as L1". The row "cheap-side price, regime and grammar sweeps without a new data source" does not cover a single pre-registered rule on a new source, but the Analyst should rule on it. |

## 3. Entry, exit, order

| Item | Rule (all in code, `functions/kalshiSlotLib.js` `SLOT_PROBE_CANDIDATES`) |
|---|---|
| Market | `KXBTC15M` only |
| When | 180 to 120 seconds before the close. In practice the minute run that starts 180 s before, so about 175 s left |
| Spread | YES ask minus YES bid at most 3c |
| Side | the cheaper side, only if it costs 5c to 30c |
| Signal | model chance of that side minus its price at least 0.05 (`functions/kalshiSpotIndexLib.js`) |
| Order | one immediate-or-cancel buy at the price seen, no slip, client order id `S-CFRTIBTC-<ticker>-1`; never a resting order, never a retry |
| Size | 1 contract. `SLOT_PROBE_MAX_CONTRACTS = 1` holds it there whatever the entry says |
| Exit | hold to settlement. No stop, no target. It is sold early only if it ever becomes a hedge (the slot's existing rule) |

**The model.** Index at an instant = the mean, over the venues that traded in the previous 10 seconds, of each venue's last price. Volatility = the sample standard deviation of the sixty 10 second log changes of that index over the previous ten minutes (at least 30 must exist). Chance of YES = Phi(ln(index / strike) / (volatility x sqrt(steps))), where steps is the time the settlement average still has to live through in 10 second units: (seconds left - 60 + 20) / 10. At 120 seconds left that is 8, the research rule exactly. The strike is Kalshi's own `floor_strike` on the market.

**Where live differs from the research rule (stated, not hidden).**
1. The look is about 175 s before the close, not 120 s: the second slot may not enter under 120 s. The horizon formula above adjusts for it. An earlier look is a harder forecast.
2. Price floor 5c, not 3c (the slot's floor).
3. Venue trade times, not the recorder's receive times; one venue reports whole seconds.
4. Trades come from each venue's public REST trade list, not a live stream.
5. One contract pays its fee rounded up to the cent in the bot's worst-case booking (2c on a 20c contract); the research figure used the unrounded fee. Results are booked at the cash fill and fee once Kalshi answers.

## 4. Caps, and how it stays apart from the other strategies

| Limit | Value | Where |
|---|---|---|
| Per order | 1 contract, at most about $0.32 | `SLOT_PROBE_MAX_CONTRACTS`, the price band |
| Lifetime loss budget (its own stop) | **$5**, open orders counted as lost, sticky | `SLOT_PROBE_BUDGET`, `probeState` |
| Slot caps | per order 1% of the base, window 2%, open 3%, day 2%, lifetime 6% (ceilings $20 to $60), shared with OICORE and EVENT830 | existing `slotCaps` |
| Slot's own stop | `RISK_PROFILES.SECOND`, one budget over all slot strategies | existing |
| Account | the shared 12% stop (a new order counts as lost the moment it exists) and the 5.5% window cap | existing |
| Depth | at most a quarter of the size at the touch | existing |
| Open contracts per market | the slot's cap. OICORE is listed first, so in a window OICORE trades the probe is usually skipped ("first strategy in holds the market") | existing |

- **Size lock.** L1's size lock (`maxContractsFor`) is not involved: this is a slot order, and the slot's own gate is the only way in. Bitcoin stays paused for L1.
- **Direction lock.** It can never buy the side opposite an L1 or slot order in the same market.
- **Exit watch.** The L1 exit watch iterates L1's own order documents only. The slot exit pass looks the strategy up by id: registered, it is held; if it is ever removed from the registry, an open order gets the fallback exit (25c stop, out 60 s before the close), so nothing is stranded.
- **The key.** The spot reader is handed the public `fetch`, the market, the side and the clock. It is never handed the Kalshi key, the store or the session, reaches one pinned host only, refuses redirects and sends no credential.
- **Interference (7g).** OICORE and EVENT830 share one slot stop. The $5 budget is this probe's OWN stop, so its losses stop it long before they could move the shared one.

## 5. Kill

Any one of these stops it, with no automatic restart:
1. **Budget:** its own settled record since `reviewedAt` reaches -$5 at any point, or would with every open order counted as lost.
2. **Streak:** 20 losses in a row.
3. **Profit factor under 1.0:** net below $0 at any point from 100 settled fills.
4. **Evidence:** the research held-out read (Nov 22 to 24, 50 Bitcoin rows, read once) comes back under 1.0, or the Verification Analyst measures a correlation of 0.3 or more with OICORE. These two are a reviewed edit (switch back to false), not automatic.
5. A lost order answer ends the session and latches the strategy (the slot's existing rule).

## Return

After a kill: a 14 day cool-off, then a paper or shadow run at cash profit factor 1.3 or better over 100 signals with the second half at 1.2 or better and no day over 30% of net, then the owner's approval. Re-arming is a reviewed edit that moves `reviewedAt`; nothing resumes on a date.

## 6. What a pass would look like (written first)

Probe to Live needs cash profit factor 1.3 or better over at least 100 fills in 2 of 3 windows (lifecycle 7f). At about 2 to 3 signals a day, 100 fills is five to seven weeks, and $5 buys roughly 20 to 60 tries, so **the budget ends before the proof**: the most this probe can say is "real fills look like the simulation" or "they do not". A second budget is a new owner decision. Forward read date in the registry: 2026-12-15.

## 7. New code and cost

| Piece | What | Status |
|---|---|---|
| `functions/kalshiSpotIndexLib.js` | The reader and the model. Pure functions plus one bounded public GET reader of the one allowed venue. Returns no reading as built | written |
| `functions/kalshiSlotLib.js` | The candidate, its switch (`SLOT_PROBE_SWITCH.CFRTIBTC: false`), the budget, the one-contract cap, a `modelEdgeMin` entry field | written |
| `functions/kalshiSlotRunLib.js` | Asks the reader only for a strategy with a model line; logs `modelEdge` and the model inputs on the order; two new skip codes | written |
| `functions/index.js` | One line handing the reader to the slot tick | written |
| `test/cfrtiProbeGates.test.js` | CB1 to CB10 | written |

No new function, secret, endpoint, collection or rule. **Cost:** about 96 windows a day; per window one extra public Kalshi market read, and only when the spread and band pass, 3 to 10 public reads of the spot venues (capped at 5 seconds in total) and one position read. Under $1 a month of compute; no Firestore read is added.

## 8. Failure modes

| What can go wrong | What happens |
|---|---|
| A venue is down, slow, rate limited, redirects or changes its response shape | The reading is null and no order is sent; a `model_unreadable` skip is logged. The registered rule needs three venues and one is allowed, so today every reading is null |
| The trade list does not reach back ten minutes inside the page cap | Null, no order |
| The reads are slow | Each request aborts at 1.5 s, all of them at 5 s; the engine refuses any order more than 20 s after the minute began |
| The model is wrong | Bounded by 1 contract and $5 |
| A venue feeds a bad price | It moves the index by a third at most; the edge would look large and one contract could be bought. Bounded by the price band and the budget. Not otherwise defended |
| Kalshi's answer to the order is lost | Never retried; the session ends and the strategy is latched (existing) |
| Restart or two instances in one minute | The order document and the direction lock are created in one transaction and the client order id is fixed, so the second instance cannot send (existing) |
| One-sided or partial fill | Not possible: one contract, immediate-or-cancel |
| Stranded position | Held to settlement by design; the settle sweep books it. Worst case is its cost |
| Deploy order wrong | An exit watch older than the switch flip would give the order the fallback exit (sold at 25c or 60 s before the close). `deploy-push.sh` goes first |
| The spot venues' terms | **Ruled, Nov 12:** no live probe may read two of the three venues; the third's terms are not stated. Before ANY form is switched on, the owner decides by popup on each source it reads, from the terms as read by the Executive Assistant. The research recorder's reads of these venues for research are a separate question and are not changed here |
| The response shape in the reader is wrong | Checked Nov 12 against Kraken's public documentation page for recent trades (the page only; no market data request): `error` array, `result` with the pair key and a string `last`, each row `[price, volume, time, ...]`, at most 1,000 rows a call. These match the reader. NOT stated in the documentation: the unit of `since` and of `time`, and the row order; the reader sends `since` in seconds (as the documented example does) and sorts the rows itself. A wrong shape fails closed |

## 9. Tests and gates

`node test/cfrtiProbeGates.test.js`: CB1 off by default and the production gate refuses it; CB2 the candidate's shape and the validator's bounds; CB3 the gate; CB4 the budget (reached, sticky, open counted as lost, room); CB5 the model against an independent recomputation; CB6 not activatable as built (no reading, no request, no ruled-out venue named in the server code); CB7 the one venue reader: pinned host, GET only, no credential, bounded, fails closed; CB8 and CB9 the engine end to end; CB10 no call with the switch off. The off-equivalence fixtures are untouched. Before a merge: the full suite, `/pre-ship`, the freshness gate, the security scan, and the security agent's review.

## 10. Activation checklist (a separate pull request, only after the owner's popup)

1. `SLOT_PROBE_SWITCH.CFRTIBTC: true`; set the candidate's `reviewedAt` and `SLOT_LAST_REVIEWED_ON` to that day.
2. Remove DRAFT from `kalshi-scalper/README.md#SLOT-CFRTIBTC` and record the owner's words and date.
3. Update on purpose the gates that pin the registry to two strategies (the slot gates, the wiring gates, ST6, SF3, OM1, CB1).
4. Page: `KAL_SLOT_REGISTERED`, `KAL_STRATEGY_INFO`, a Rules sentence, the Start confirmation, the Own stops label, a Strategies page tile with the budget as its kill gauge, the changelog line.
5. CLAUDE.md section. Deploys in this order: `bash functions/deploy-push.sh`, then `bash functions/deploy-sizing.sh`.

## 11. The popup the owner would see

> *(Shown only after the first read clears, and only for a form that reads allowed data. There is no popup before the read.)*
>
> **Start a tiny live probe: CFRTIBTC (unproven)?**
>
> What it does: about 3 minutes before a Bitcoin 15 minute market closes, if a model built from [the data source of the registered form] says the cheaper side (5c to 30c) is underpriced by 5c or more, the bot buys 1 contract and holds it to the close.
>
> Size and loss: 1 contract an order, at most about 32c lost per order. It stops itself for good at $5 lost in total. It also sits inside the second slot's caps and the account's 12% stop.
>
> Honest odds: UNPROVEN. In research the rule failed its bar across five coins; Bitcoin alone looked good on 36 trades picked after the fact. The read that just cleared is cleared by a rule with no edge about one time in four. $5 buys about 20 to 60 real fills, which is enough to see whether fills match the simulation, not enough to prove an edge.
>
> Still open before it can start: your decision on the data source this form reads; the Verification Analyst's score (it may turn out to be a duplicate of OICORE).
>
> Kill: $5 lost, or 20 losses in a row, or a net loss after 100 fills. Return: 14 days off, then a paper run at profit factor 1.3 over 100 signals, then your approval.
>
> - **Wait for the re-test (about Dec 10 to 15) (Recommended)**: it is free, and one clear is not evidence
> - **Yes, start it now at 1 contract with a $5 budget**, as a pre-evidence order
> - **No**

## 12. Variant arm: W-SPOTLEAD1 (a version, not a strategy)

The Chief of Staff's ruling (Nov 12, lifecycle 7g): the spot-lead rule is a VERSION of this probe. It is the same signal (a spot model against the Kalshi quote) in another price band: the 50c to 87c side on a 10c edge, Bitcoin first. It takes no slot of its own, is not registered here, and has no code: the validator on this branch refuses a model entry above 50c on purpose, because above that it is a favourite held to settlement. Turning it on would need its own read to pass (about Nov 21 to 23; it missed its bar once), the owner's written exception to the favourite-and-hold ban for this version only, and a reviewed edit of that bound. Worst loss about $0.89 an order, so the same $5 budget is about six losing orders: too few to learn from, which is a reason not to run it as a probe at all.

## 13. The two forms that could run (design only; nothing is coded, registered or scored by this desk)

Both keep everything in sections 3 to 5 (market, time, band, 1 contract, hold, the $5 budget, the kills). Only the model's input changes. **Either is a NEW rule for research purposes:** its development figure, its registration and its read are its own, and the 36 trade Bitcoin cell does not carry over.

| | Kraken-only | Kalshi-only, "CFRTI-K" |
|---|---|---|
| Input | One venue's public trade list (the reader on this branch) | Kalshi's own Bitcoin perpetual on the public margin market list: bid, ask and reference price |
| Requests at decision time | 1 to 3 public GETs to one outside host | ONE public GET to Kalshi (the host the bot already uses); no outside host at all |
| Index at the look | That venue's last price if it traded in the last 10 s | The perpetual's reference price (or its mid; research must say which) |
| Volatility | As now: sixty 10 second changes over ten minutes, from the trade list | Needs ten minutes of history. One decision-time GET gives one price, so the history must come from the perpetual's public one minute candles (a second public GET, and then the volatility is ten 1 minute changes, not sixty 10 second ones), or from a rolling record kept by the minute function. Research must register which; they are not the same number |
| Code change | Two constants (`VENUES_REQUIRED` to 1 with the registration that says so). The reader, the gates and the engine are unchanged | A second small reader beside this one (pinned to the Kalshi host through the bot's existing public request helper), the candle-based volatility, and a registry constant choosing the form. About 1 build day with tests |
| Honest weakness | One venue is not the settlement index: the settlement value averages several venues, so a one-venue model is noisier and a single bad print moves it fully. The three-venue minimum was the registered guard against exactly that | The perpetual is a Kalshi price, not spot: its reference price is itself built from an index, with its own lag and funding premium. If it lags spot it carries no information the 15 minute market does not already have |
| Terms | The owner must still rule on this venue (its terms are "not stated") | None outside Kalshi |

**Recommendation:** CFRTI-K is the only form with no terms question and no outside host, so it is the one worth building IF research shows a result for it. Until then the code stays as it is: dormant, and unable to trade.

