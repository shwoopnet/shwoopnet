# Rotation lane, "the wheel" (DRAFT v0.4, Nov 12, 2026)

**Status: a draft by the Head of R&D for the owner's OK. It binds nobody and nothing goes live under it until the owner approves the written rules.** Intended home: `docs/ROTATION_LANE.md` on main, as a docs-only pull request opened by the Chief of Staff, with a pointer line in `docs/STRATEGY_LIFECYCLE.md`. It does not edit `docs/CHARTER.md`, which only the owner changes.

Every number in this file is a rule, a threshold or arithmetic on made-up coin flips (scripts in `lane_arith/` on the `rnd-queue` branch). No live account figure is in it. [design]

v0.4 carries all eight of the owner's popup decisions of Nov 12 (section 0). Earlier drafts: v0.1 (3 live, 8 shadows, written before his target arrived), v0.2 and v0.2.1 (the wheel at 3 contracts with a lane-wide cap; the Refinement desk's review of the kill lines; the Chief of Staff's security condition on automatic returns), v0.3 (his first five decisions).

## 0. Decided by the owner (popups, Nov 12, 2026, through the EA)

1. **No maximum on live rotating strategies; 5 is the minimum target.** His words: "not capped -- if the strategies are working put them in. only a minimum of 5". The shadow list target is 20 to 30.
2. **The 30 signal confirmation step: yes.**
3. **Size: 10 contracts, at most $10 an order.**
4. **Loss lines are each strategy's own, with no lane-wide pause.** His words: "i think this should be independent for each strategy probably. otherwise it should scale accordingly to how much we're risking per trade so we don't hit it in one trade". All still inside the existing shared 12 percent account stop.
5. **Returns: automatic, up to 2 times; after a kill, or a third exit, his popup.**

6. **Seats per market.** Each market a rule runs on is its own shadow and its own seat, with its own record and its own kill. This overrides the Nov 11 copy rule (lifecycle 7g) **for the wheel only**.
7. **The premise test comes first.** "Does a hot 60 predict the next 60" is run on recorded data before any seat (section 9.5; registered as WHEEL0).
8. **Favourites at 88c or above are allowed only with 150 signals and at least 10 losses in the record.**

Not yet answered, and flagged in section 12: whether gold's own return rule takes the 10 loss guard; the account stop as the wheel's only total limit; and whether the favourite-late copies he retired on Nov 11 may come back as wheel shadows under decisions 6 and 8, or stay on the declined list (this draft assumes they stay until he says otherwise).

## Why

The owner, Nov 12, 2026 (popups, through the EA): "remember we're building for constant short term income with rotating strategies, we aren't under the impression that our holy grail will be found here (permanent profitable strategy regardless of market)". He chose "Add a rotation lane". His target: "the rotation is the ultimate goal here right, just a fully automated rotating strategy list that plays itself based on the markets conditions. Ideally we would have at minimum 5+ strategies at a time LIVE, and atleast 20-30 that are on shadow list / return. i love the like ferris wheel idea".

## 1. What does not change

1. The research bar (cash profit factor 1.5 on development and held-out, three windows, after fees, deflated) and the proven bar (1.3 or better over 100 fills in 2 of 3 windows) stay. They are what any size above the wheel's fixed size needs. [design]
2. The declined list (lifecycle 7e), the no-hedge direction lock, the data-source rules and the shared 12 percent loss stop, 5.5 percent window cap and second-slot caps apply to wheel orders as to any slot order. The wheel never re-admits a row the owner declined.
3. Gold L1 is not a wheel strategy. It keeps its own kill latch and return rule (`docs/GOLD_KILL_LATCH.md`).
4. **The owner's popup is still required for every strategy, once, at admission:** each rule joins the wheel only by the owner's popup with its exact spec (market, side, band, look window, limit, exit, size, kill lines), then the Chief of Staff's reviewed merge and security pass. After that the rule takes and leaves a seat by itself. In code that means one reviewed registry entry per rule in the second slot (and, for a rule that holds to settlement, one reviewed entry on the hold list), written at admission and armed or disarmed only by the replay. Nothing stored, requested or typed on a page may add, enlarge or re-arm a strategy; the in or out state is replayed from the rule's own rows on every run, like the gold latch.
5. **Favourites at 88c or above ride the wheel only under the owner's rule of section 0.8** (a record of at least 150 signals holding at least 10 losses; the arithmetic is in section 4). A row on the declined list stays declined whatever its price.

## 2. The wheel

1. A shadow list of 20 to 30 registered rules as the target. **No maximum on live seats; at least 5 is the target** (the owner, section 0).
2. A rule is in exactly one state: SHADOW (logging, no money), CONFIRMING, QUALIFIED (waiting for a seat), LIVE (a seat, 10 contracts), COOLING (out, 14 days), RETIRED.
3. **One place per market (the owner, section 0.6).** A rule that runs on several markets holds a separate shadow place, record, seat and kill on each, for example the price-jump rule on five sports. Each market version is admitted with its own spec line. Outside the wheel the Nov 11 rule is unchanged: the same logic on a new market is a version of its parent, not a new strategy, and is never counted as a new unique idea in research.

## 3. Admission to the shadow list

1. A pre-registration written before the rule's first counted signal: entry, side, price band, look window, limit, exit, size, its classification card and the declined-list check.
2. **Forward signals only.** A signal counts only if it happened after the registration was committed. A backtest or a development read can nominate a rule. It can never qualify one.
3. **The admit list is fixed before its window.** Rules are admitted in dated batches; nobody adds a rule because its recent past looks good, and nobody picks the best of several variants after seeing them. One set of parameters per rule, the same on every market it runs on; a changed parameter is a new rule, its count restarts, and it is counted again in the lane ledger. Markets differ, parameters do not: nobody tunes a band or a look time market by market.
4. A rule with negative evidence (a falsified read at about 100 trades or more) is not admitted.

## 4. The record and the entry bar [design]

**The record.** Logged by the bot's shadow logger on the quotes of the moment, or replayed from recorded order books. Never market-list quotes and never candles alone. A signal is **fillable** only if a second look within 4 seconds after the decision (one extra public read a row; the Chief of Staff confirms it is buildable inside the read budget) still shows the wheel's size at or under the registered limit (the touch plus at most 1c); no second look is no trade. Measured on recorded gold books, an immediate order at the price seen filled about half the time a few seconds later, so a shadow that assumes a fill at the touch overstates its count by a quarter to a half. Cash basis, fee rounded up to the cent for 10 contracts.

**The bar, read once at the end of a block:**

1. A block is 60 fillable signals in a row, within the last 21 days, on at least 7 different days, no single day more than 30 percent of the block's net.
2. Cash profit factor 1.3 or better on the block and 1.0 or better in each half.
3. At least 10 of the rarer outcome in the block (wins for a cheap-side rule, losses for a rule that buys above 50c); otherwise the block keeps growing until it has them. **For a rule that buys at 88c or above (the owner, section 0.8): the block is at least 150 signals and runs on until it holds at least 10 losses.** On the coin flips a no-edge favourite clears that about 9 to 10 percent of the time, and about 5 percent with the confirmation, which puts it level with the other prices instead of the 27 percent of the bare rule.
4. Blocks never overlap. After a failed block the next one starts from new signals. No rolling re-reads.
5. **Confirmation (decided by the owner):** the next 30 fillable signals after a cleared block hold 1.0 or better. Then the rule is QUALIFIED.
6. **Seats:** a qualified rule takes a seat at once; there is no maximum number of seats. (If the owner ever sets one, the rule with the longest record goes first, never the one with the highest number: picking the highest number picks the luckiest.)
7. A rule that would buy the same market, side and minute as a live strategy does not take a seat while that strategy is live.

**Why the bar is built this way, on coin flips with the real fee (the shares below barely move with the size):**

| A rule with no edge at all clears "1.3 over 60" | at 20c | at 50c | at 90c |
|---|---|---|---|
| on one block, the bare rule | 13 percent | 8 percent | 27 percent |
| sooner or later within 300 signals, if the window is re-read as it rolls | 67 percent | 49 percent | 91 percent |
| sooner or later within 300 signals, blocks that do not overlap, both halves at 1.0 | 39 percent | 30 percent | not admitted |
| the same, with the 30 signal confirmation | 18 percent | 13 percent | not admitted |
| on its first block, with the confirmation | 4 percent | 3 percent | not admitted |

A rule that truly has 1.3 clears its first block about 42 percent of the time (about 30 percent with the confirmation). So the bar lets a real rule in about ten times as easily as a dead one, no better, and **with 30 rules watching, some will clear by luck every month: about 3 a month on the bare rule, about 1 a month with the confirmation.** That is why the confirmation is part of the bar, and why the protection is each rule's own kill lines, the account stop and the scorecard, not the entry statistics.

## 5. A seat

1. **10 contracts, fixed, at most $10 of cost an order (the owner, section 0).** No ladder, no profit add-on, no reinvestment. The registered exit cannot be changed while live. The second slot's existing caps still apply to each rule and scale with the sizing base; where a cap is smaller than a 10 contract order the cap wins, and the Chief of Staff checks that against the real figures before admission (no figure is written here).
2. **Live against shadow, first 20 live orders:** fewer than 60 percent filled, or an average fill more than 1c worse than the shadow's price for the same windows, and the rule leaves its seat with its shadow record marked overstated.
3. Label everywhere it is shown: "rotating (unproven)".

## 6. Leaving a seat [design]

Automatic, replayed from the rule's own settled orders on the cash basis. An open position is finished by the rule's own exit; the exit watch is not touched.

1. **A cash drawdown of $60 from the rule's own peak (a KILL: latched).** This is six times the most one order can lose ($10), as the owner asked: it cannot trip on one trade, or on five losses in a row at the most expensive price. Why six and not four or eight, on the coin flips: at four ($40) a real 1.3 rule is killed about two times in three within 200 fills; at six about one time in two; at eight barely less than at six, while a truly losing rule costs about a tenth more. A dead rule usually leaves on lines 2 and 3 before it reaches this one.
2. Net under minus 1c a contract at the 50th fill (a performance exit).
3. At every 60th fill, the last 60 fills under 1.0 (a performance exit).
4. The live-against-shadow check (a KILL: latched).

Alerts only, never an exit by themselves (the Refinement desk's review: on gold these fired mostly on a strategy that then kept earning, and saved nothing): a rolling 60 fill profit factor under 0.7; for a rule that exits early, 3 early sells in the last 40.

What lines 1 to 3 do on coin flips at 10 contracts: a rule with no edge leaves after about 50 fills at an average cost of about $10 to $13 (one time in twenty, about $50 to $60); a rule that truly loses (0.8) costs about $24 to $31. They also turn out a rule that truly has 1.3 within 200 fills about one time in two; such a rule earns about $55 to $95 over those fills. Real rules are rotated out by noise too and come back through section 7. A known cost of this design, from the Refinement desk: taking a rule off after its own bad stretch and putting it back after its recovery is timing its mean reversion, and on history that hurt rules that bounce.

## 7. Cooling and return

1. After a performance exit: 14 days out, then a new block made only of signals after the exit date, plus the confirmation, both on fill-checked rows. Then the rule takes a seat again automatically, **at most 2 times** (the owner, section 0).
2. **Never automatic after a kill.** A rule that left on its $60 drawdown or on the live-against-shadow check returns only by a reviewed re-arm: at least 30 days, a fresh block and confirmation, the owner's popup and the Chief of Staff's merge. The automatic return of line 1 is for a performance exit only (lines 2 and 3 of section 6). This is the Chief of Staff's security condition: an automatic return is acceptable only where the rule's registry entry already exists from admission, the state is replayed from rows, and size, shared stop and kill latches are unchanged.
3. **A third exit** of any kind: the rule stays out until the owner's popup (section 0). Research's recommendation is that a rule with three exits inside 90 days is retired to the declined list unless he says otherwise.

## 8. The total at risk

1. **There is no lane-wide pause (the owner, section 0).** Each strategy stands on its own $60 kill.
2. Wheel orders run in the second slot under its existing per-strategy caps, count in the shared 12 percent account stop and the 5.5 percent window cap, and obey the direction lock.
3. **The plain consequence, which the owner should see before he OKs this:** with no seat maximum and no lane cap, the thing that limits the wheel's total loss on a bad day is the shared 12 percent account stop, and when that stop trips it ends the whole bot's session, the non-wheel strategies included, until it is started again. On the coin flips (30 shadows, 10 contracts, section 10) the wheel's worst single day in six months is typically about minus $35 to minus $45 and its worst week about minus $70, with worse seen in one run in forty (a day near minus $80, a week near minus $190). The Chief of Staff compares those with the real stop figure privately. If they are too close, the two fixes that keep his decisions intact are a smaller size until the account grows, or letting the 5.5 percent window cap do more of the work; a lane cap is the third, and he has declined it. [design]

## 9. Not just picking lucky shadows

1. Sections 3 and 4: forward signals only, a dated admit list, one set of parameters, blocks that do not overlap, the confirmation, fill-checked rows. **Seats per market multiply the looks:** thirty places on a dozen mechanisms are not thirty independent ideas, and two markets of one rule can look hot together because they share a cause. The ledger therefore counts every market place as its own row, and the notice for a seat names the sibling markets of the same rule and how they stand.
2. **A lane ledger** on the `rnd-queue` branch, kept by the Head of R&D: every rule ever admitted, every block read, cleared or failed. Each time a rule takes a seat the owner's notice says how many blocks the wheel has read so far and how many lucky seats that many blocks would produce with no edge anywhere (blocks times about 0.035). With 30 shadows that is about one lucky seat a month.
3. **The lane scorecard is the real test of the wheel's premise**, which is that a good recent record says something about the next few weeks. After 150 wheel fills in total the wheel's combined cash profit factor is read once; under 1.0 the owner is told at once and decides. Nothing pauses by itself, since he chose no lane-wide pause. It is reported every Monday, profit factor first, with n.
4. A wheel record is never quoted as a research-bar pass or as proven. Any size above 10 contracts needs the proven bar on live fills and the owner's popup.
5. **The premise test comes before the first seat (the owner, section 0.7).** WHEEL0, one registered test with its templates, blocks and verdict lines fixed before any outcome is joined: when a block is hot, what do the next 60 signals show, against blocks that were not hot? It is run by the Forensics desk on the recorded order books, with public one-minute candles over the longer window for power, since two weeks of books hold only a handful of hot blocks; the label is "premise supported", "premise not supported" or "no evidence at n = x hot pairs", and no seat is taken before it is read. Everything in this file depends on the answer.

## 10. What to expect, plainly [design]

**One order.** At 10 contracts a rule that truly has 1.3 earns about 37c to 65c an order (most at mid prices, least near the ends). A losing order costs about $2 at 20c, about $5 at 50c and about $8 at 80c.

**One lucky fake.** A rule with no edge that reaches a seat costs about $10 to $13 before its own lines turn it out (one time in twenty, $50 to $60).

**The wheel.** 30 shadows, no seat maximum, 10 contracts, each rule seeing about 4 signals a day with 70 percent fillable, on coin flips with the real fee:

| If the share of the 30 rules that truly have 1.3 is | wheel result a month | bad month (1 in 20) | seats filled on average | share of live orders from real rules |
|---|---|---|---|---|
| none | about minus $12 | about minus $36 | about 1 | none |
| 1 in 10 | about plus $44 | about minus $20 | about 2 | about half |
| 1 in 5 | about plus $113 | about minus $5 | about 3 to 4 | about two thirds |
| 2 in 5 | about plus $247 | about plus $115 | about 6 | most |

Two things follow. First, the wheel earns in proportion to how many of its rules are real, and research found none at the research bar on Nov 12, so the honest starting expectation is the top row or the second. Second, **five seats filled at once needs about two rules in five to be real** at this bar; with fewer, the wheel will often show one to three seats, and the only ways to fill five regardless are a looser bar (which seats luck) or many more shadows.

**What can feed it.** Research found no rule at the research bar on Nov 12. Rules with a written, registered spec today: 8 mechanisms (OICORE and EVENT830, already live under their own rules; a book-state rule on the Bitcoin and Ethereum 15 minute markets; a Kalshi-only Bitcoin model-edge rule; an esports break rule; an in-play price-jump rule; an e-soccer rematch rule; an e-soccer tie rule). In two weeks about 10 to 12. Twenty different mechanisms is about January at two or three new ones a week.

- **With seats per market (decided):** about 14 places this week from the six mechanisms that are not already live (the price-jump rule on five sports, the esports break on four games, the depth rule on two markets, and the rest), and 20 to 30 within about two weeks as the hourly temperature, period-tie and non-crypto depth rules are written. That is 20 to 30 places on about a dozen mechanisms, not 20 to 30 different ideas.
- A rule with negative evidence is still not admitted on any market, and a development read that falsifies a rule removes all of its market places at once.

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

## 12. Still open for the owner (defaults in force in this draft until he answers)

1. **The account stop as the wheel's only total limit** (section 8.3): he should see the worst-day figures against the real stop before the first seat.
2. **The favourite-late copies retired on Nov 11** (the XRP, AUD/USD and gold shadow variants on the declined list): decisions 6 and 8 would let favourites and market versions ride the wheel in general, but those rows were declined by name. Default: they stay declined; only he removes a row.
3. **Gold's own return rule and the 10 loss guard.** Default: unchanged; flagged because "60 trades at 1.3" is cleared by a no-edge favourite about one time in four.
4. **A third exit.** Default: his popup, as he decided; research recommends retiring a rule with three exits inside 90 days.

## 13. Build (the Chief of Staff's plan, for reference)

Logging and reporting first, about four days: a quote budget for series the bot does not already read, the open interest and calendar fields, a rolling per-rule report with the fill check. Then the rotation controller as a replay-only dry run. Live wiring only after the owner OKs these written rules, with its own security review.
