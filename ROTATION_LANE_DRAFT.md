# Rotation lane, "the wheel" (DRAFT v0.2, Nov 12, 2026)

**Status: a draft by the Head of R&D for the owner's OK. It binds nobody and nothing goes live under it until the owner approves the written rules.** Intended home: `docs/ROTATION_LANE.md` on main, as a docs-only pull request opened by the Chief of Staff, with a pointer line in `docs/STRATEGY_LIFECYCLE.md`. It does not edit `docs/CHARTER.md`, which only the owner changes.

Every number in this file is a rule, a threshold or arithmetic on made-up coin flips (scripts in `lane_arith/` on the `rnd-queue` branch). No live account figure is in it. [design]

v0.2 replaces v0.1 (3 live, 8 shadows), which was written before the owner's target arrived. It also takes in the Refinement desk's review of the kill lines.

## Why

The owner, Nov 12, 2026 (popups, through the EA): "remember we're building for constant short term income with rotating strategies, we aren't under the impression that our holy grail will be found here (permanent profitable strategy regardless of market)". He chose "Add a rotation lane". His target: "the rotation is the ultimate goal here right, just a fully automated rotating strategy list that plays itself based on the markets conditions. Ideally we would have at minimum 5+ strategies at a time LIVE, and atleast 20-30 that are on shadow list / return. i love the like ferris wheel idea".

## 1. What does not change

1. The research bar (cash profit factor 1.5 on development and held-out, three windows, after fees, deflated) and the proven bar (1.3 or better over 100 fills in 2 of 3 windows) stay. They are what any size above the wheel's fixed size needs. [design]
2. The declined list (lifecycle 7e), the no-hedge direction lock, the data-source rules and the shared 12 percent loss stop, 5.5 percent window cap and second-slot caps apply to wheel orders as to any slot order. The wheel never re-admits a row the owner declined.
3. Gold L1 is not a wheel strategy. It keeps its own kill latch and return rule (`docs/GOLD_KILL_LATCH.md`).
4. **The owner's popup is still required for every strategy, once, at admission:** each rule joins the wheel only by the owner's popup with its exact spec (market, side, band, look window, limit, exit, size, kill lines), then the Chief of Staff's reviewed merge and security pass. After that the rule takes and leaves a seat by itself. Nothing stored, requested or typed on a page may add, enlarge or re-arm a strategy; the in or out state is replayed from the rule's own rows on every run, like the gold latch.
5. **No favourite-and-hold at 88c or above on the wheel** unless the owner rules otherwise (his standing ban; and see the arithmetic in section 4).

## 2. The wheel

1. Up to 30 registered shadow rules. 5 live seats to start (more by the owner's word).
2. A rule is in exactly one state: SHADOW (logging, no money), CONFIRMING, QUALIFIED (waiting for a seat), LIVE (a seat, 3 contracts), COOLING (out, 14 days), RETIRED.
3. **Open choice for the owner, the one that decides how big the wheel can be:** whether one rule may hold a shadow place and a seat on each market it runs on (for example the price-jump rule on five sports), or only one place per mechanism. His Nov 11 rule (lifecycle 7g) says the same logic on a new market is a copy, not a new strategy. See section 10 for what each answer gives.

## 3. Admission to the shadow list

1. A pre-registration written before the rule's first counted signal: entry, side, price band, look window, limit, exit, size, its classification card and the declined-list check.
2. **Forward signals only.** A signal counts only if it happened after the registration was committed. A backtest or a development read can nominate a rule. It can never qualify one.
3. **The admit list is fixed before its window.** Rules are admitted in dated batches; nobody adds a rule because its recent past looks good, and nobody picks the best of several variants after seeing them. One version of a rule; a changed parameter is a new rule, its count restarts, and it is counted again in the lane ledger.
4. A rule with negative evidence (a falsified read at about 100 trades or more) is not admitted.

## 4. The record and the entry bar [design]

**The record.** Logged by the bot's shadow logger on the quotes of the moment, or replayed from recorded order books. Never market-list quotes and never candles alone. A signal is **fillable** only if a second look within 4 seconds after the decision still shows the wheel's size at or under the registered limit (the touch plus at most 1c); no second look is no trade. Measured on recorded gold books, an immediate order at the price seen filled about half the time a few seconds later, so a shadow that assumes a fill at the touch overstates its count by a quarter to a half. Cash basis, fee rounded up to the cent for 3 contracts.

**The bar, read once at the end of a block:**

1. A block is 60 fillable signals in a row, within the last 21 days, on at least 7 different days, no single day more than 30 percent of the block's net.
2. Cash profit factor 1.3 or better on the block and 1.0 or better in each half.
3. At least 10 of the rarer outcome in the block (wins for a cheap-side rule, losses for a rule that buys above 50c); otherwise the block keeps growing until it has them.
4. Blocks never overlap. After a failed block the next one starts from new signals. No rolling re-reads.
5. **Confirmation:** the next 30 fillable signals after a cleared block hold 1.0 or better. Then the rule is QUALIFIED.
6. **Seats:** a qualified rule takes a free seat at once. If more rules qualify than there are seats, the rule with the longest record goes first, never the one with the highest number (picking the highest number picks the luckiest). A rule that waits more than 14 days for a seat starts a new block.
7. A rule that would buy the same market, side and minute as a live strategy does not take a seat while that strategy is live.

**Why the bar is built this way, on coin flips with the real fee at 3 contracts:**

| A rule with no edge at all clears "1.3 over 60" | at 20c | at 50c | at 90c |
|---|---|---|---|
| on one block, the bare rule | 13 percent | 8 percent | 27 percent |
| sooner or later within 300 signals, if the window is re-read as it rolls | 67 percent | 49 percent | 91 percent |
| sooner or later within 300 signals, blocks that do not overlap, both halves at 1.0 | 39 percent | 30 percent | not admitted |
| the same, with the 30 signal confirmation | 18 percent | 13 percent | not admitted |
| on its first block, with the confirmation | 4 percent | 3 percent | not admitted |

A rule that truly has 1.3 clears its first block about 42 percent of the time (about 30 percent with the confirmation). So the bar lets a real rule in about ten times as easily as a dead one, no better, and **with 30 rules watching, some will clear by luck every month: about 3 a month on the bare rule, about 1 a month with the confirmation.** That is why the confirmation is part of the bar here and not an option, and why the protection is size, the kill lines, the lane cap and the scorecard, not the entry statistics.

## 5. A seat

1. **3 contracts, fixed, at most $3 of cost an order.** No ladder, no profit add-on, no reinvestment. The registered exit cannot be changed while live.
2. **Live against shadow, first 20 live orders:** fewer than 60 percent filled, or an average fill more than 1c worse than the shadow's price for the same windows, and the rule leaves its seat with its shadow record marked overstated.
3. Label everywhere it is shown: "rotating (unproven)".

## 6. Leaving a seat [design]

Automatic, replayed from the rule's own settled orders on the cash basis. An open position is finished by the rule's own exit; the exit watch is not touched.

1. A cash drawdown of $10 from the rule's own peak.
2. Net under minus 1c a contract at the 50th fill.
3. At every 60th fill, the last 60 fills under 1.0.
4. The live-against-shadow check, or the lane cap in section 8.

Alerts only, never an exit by themselves (the Refinement desk's review: on gold these fired mostly on a strategy that then kept earning, and saved nothing): a rolling 60 fill profit factor under 0.7; for a rule that exits early, 3 early sells in the last 40.

What lines 1 to 3 do on coin flips: a rule with no edge leaves after about 25 to 50 fills at an average cost of about $2.50 to $3 (one time in twenty, about $11); a rule that truly loses (0.8) costs about $5 to $6. They also turn out a rule that truly has 1.3 within 200 fills about two times in three. Real rules are rotated out by noise too and come back through section 7. A known cost of this design, from the Refinement desk: taking a rule off after its own bad stretch and putting it back after its recovery is timing its mean reversion, and on history that hurt rules that bounce.

## 7. Cooling and return

1. 14 days out, then a new block made only of signals after the exit date, plus the confirmation, both on fill-checked rows. Then the rule may take a seat again, automatically.
2. After a $10 drawdown exit: 30 days instead of 14.
3. A third exit within 90 days retires the rule and adds a row to the declined list. Only the owner removes a row.

## 8. The total at risk

1. Wheel orders run in the second slot under its existing caps and count in the shared 12 percent stop and the 5.5 percent window cap, and obey the direction lock.
2. **Lane cap:** if the wheel's combined cash result falls $50 from its own peak (five seats at $10), every wheel entry stops until the owner re-arms it by popup. [design]

## 9. Not just picking lucky shadows

1. Sections 3 and 4: forward signals only, a dated admit list, one version, blocks that do not overlap, the confirmation, fill-checked rows, the longest record first.
2. **A lane ledger** on the `rnd-queue` branch, kept by the Head of R&D: every rule ever admitted, every block read, cleared or failed. Each time a rule takes a seat the owner's notice says how many blocks the wheel has read so far and how many lucky seats that many blocks would produce with no edge anywhere (blocks times about 0.035).
3. **The lane scorecard is the real test of the wheel's premise**, which is that a good recent record says something about the next few weeks. After 150 wheel fills in total the wheel's combined cash profit factor is read once; under 1.0 the wheel pauses and the owner decides. It is reported every Monday, profit factor first, with n.
4. A wheel record is never quoted as a research-bar pass or as proven. Any size above 3 contracts needs the proven bar on live fills and the owner's popup.
5. **Strongly recommended before the first seat:** one registered test of the premise on recorded books (when a block clears, what do the next 60 signals show?), reported with n. It needs no order and no new data. Everything in this file depends on the answer.

## 10. What to expect, plainly [design]

**What it earns.** A wheel of 30 shadows and 5 seats at 3 contracts, each rule seeing about 4 signals a day, 70 percent fillable, on coin flips with the real fee:

| If the share of the 30 rules that truly have 1.3 is | wheel result a month | seats filled on average | share of live orders that come from real rules |
|---|---|---|---|
| none | about minus $2 (bare rule: minus $5) | about 0.5 | none |
| 1 in 10 | about plus $6 | about 1 | a little over half |
| 1 in 5 | about plus $21 | about 2 | about three quarters |

So at 3 contracts the wheel is not income by itself. A real 1.3 rule at mid prices earns about 19c an order. The wheel is a machine that finds, cheaply and on live fills, which rules deserve more size; more size still needs the proven bar. And five seats full at once will not happen at this bar with 30 shadows unless several rules are real: it needs more shadows, busier rules or a looser bar, and a looser bar fills seats with luck.

**What can feed it.** Research found no rule at the research bar on Nov 12. Rules with a written, registered spec today: 8 mechanisms (OICORE and EVENT830, already live under their own rules; a book-state rule on the Bitcoin and Ethereum 15 minute markets; a Kalshi-only Bitcoin model-edge rule; an esports break rule; an in-play price-jump rule; an e-soccer rematch rule; an e-soccer tie rule). In two weeks about 10 to 12. Twenty different mechanisms is about January at two or three new ones a week.

- **If one rule may hold a place on each market it runs on:** about 14 places this week (the price-jump rule on five sports, the esports break on four games, the depth rule on two markets, and the rest), and 20 to 30 within about two weeks.
- **If only one place per mechanism:** 6 new shadows this week, and a smaller wheel until January.

Shadowing a rule costs no money, only logger reads (free for the four markets the bot already reads; one public read per look elsewhere, which needs sizing for series with hundreds of events a day) and the builder's time to register it.

## 11. Who qualifies today (Nov 12, 2026; research records on public data, no live figures)

**Nobody.** No rule has 60 forward, fill-checked, book-priced signals.

| Candidate | What exists | Earliest a seat is possible after admission |
|---|---|---|
| DEPTH1 (book-state rule, Bitcoin and Ethereum 15 minute markets) | scorer frozen and audited; first read on recorded books from Nov 14 00:00Z | about 2 to 3 weeks |
| The four rules registered Nov 12 (esports break, in-play price jump, e-soccer rematch, e-soccer tie) | registered and audited; development reads on candles in the next days; they need a forward quote shadow and the non-15-minute order path that exists switched off | the e-soccer rules could fill a block and its confirmation in about one to two weeks; esports and tennis slower |
| CFRTI-K (Kalshi-only Bitcoin cheap side with a model edge) | development read under 1.3; a book replay too small to say anything | about 3 to 4 weeks; it buys the same market, side and minute as OICORE, so rule 4.7 may keep it off a seat |
| Spot-lead | missed its own bar; reads venues no live rule may read without the owner's popup | not live-able as written |
| Approval NO side, combo house side | slow markets | cannot make 60 signals in 21 days |
| EVENT830 | 15 listed windows in all | stays under its own rules |

**Closed rules that the full bar alone stopped: none.** Each had negative evidence, a development record under 1.3, or is on the declined list. The wheel brings none of them back.

## 12. Choices for the owner

1. One place per market, or one per mechanism (section 2.3). This decides whether 20 to 30 shadows is two weeks away or two months.
2. The confirmation step as part of the bar (recommended; with 30 shadows it is what keeps lucky seats to about 1 a month).
3. $10 a rule and a $50 lane cap at 3 contracts.
4. The premise test of section 9.5 before the first seat (strongly recommended).
5. Whether favourites at 88c or above may ride the wheel at all, and whether the gold return rule should also require at least 10 losses in its record ("60 trades at 1.3" is cleared by a no-edge favourite about one time in four).

## 13. Build (the Chief of Staff's plan, for reference)

Logging and reporting first, about four days: a quote budget for series the bot does not already read, the open interest and calendar fields, a rolling per-rule report with the fill check. Then the rotation controller as a replay-only dry run. Live wiring only after the owner OKs these written rules, with its own security review.
