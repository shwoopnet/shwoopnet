# Rotation lane (DRAFT v0.1, Nov 12, 2026)

**Status: a draft by the Head of R&D for the owner's OK. It binds nobody and nothing goes live under it until the owner approves the written rules.** Intended home: `docs/ROTATION_LANE.md` on main, as a docs-only pull request opened by the Chief of Staff, with a pointer line in `docs/STRATEGY_LIFECYCLE.md`. It does not edit `docs/CHARTER.md`, which only the owner changes.

Every number in this file is a rule, a threshold or arithmetic on made-up coin flips. No live account figure is in it. [design]

## Why

The owner, Nov 12, 2026 (popup, through the EA): "remember we're building for constant short term income with rotating strategies, we aren't under the impression that our holy grail will be found here (permanent profitable strategy regardless of market)". He chose "Add a rotation lane": a strategy may go live at small size after a recent shadow record, with a strict kill; it rotates out when it fades and back in when its shadow recovers; the full research bar stays for scaling up.

## 1. What does not change

1. The research bar (cash profit factor 1.5 on development and held-out, three windows, after fees, deflated) and the proven bar (1.3 or better over 100 fills in 2 of 3 windows) stay as they are. They are what scaling up needs. [design]
2. What may be traded does not change. The uniqueness check (lifecycle 7d), the declined list (7e), "a version replaces its parent" (7g), the ban on favourite-late copies, the no-hedge direction lock and the data-source rules all apply to the lane exactly as they do today. The lane lowers the evidence needed for a small first order. It does not re-admit anything the owner declined.
3. Gold L1 is not a lane strategy. It keeps its own kill latch and return rule (`docs/GOLD_KILL_LATCH.md`).
4. Every first entry needs the owner's own popup with the exact spec, then the Chief of Staff's reviewed merge and security pass. Nothing stored, requested or typed on a page may add or enlarge a strategy.
5. The shared 12 percent loss stop, the 5.5 percent window cap and the second slot's own caps apply to lane orders as to any slot order.

## 2. The pool: which rules may be shadowed for the lane

1. A rule enters the pool only by a pre-registration written before its first counted signal: entry, side, price band, look window, limit, exit, size, its classification card, the four uniqueness checks and the declined-list check.
2. **Forward signals only.** A signal counts toward entry only if it happened after the registration was committed. A record on history (a backtest, a development read, a replay of old recorder files) can nominate a rule for the pool. It can never qualify one.
3. At most 8 rules in the pool at once. At most one per underlying market within a mechanism family. One version of a rule: a changed parameter is a new rule, its count restarts, and it is counted again in the lane ledger.

## 3. The shadow record

1. It is logged by the bot's shadow logger on the quotes of the moment, or replayed from recorded order books. Never from market-list quotes (a copy up to 11 seconds old) and never from candles alone.
2. **Fillable** means more than "the size at the touch covered it". Measured on recorded gold books, an immediate order at the price seen filled about half the time a few seconds later, and about three quarters to nine in ten with one cent more. So a signal is fillable only if, at a second look within 4 seconds after the decision, the book still offers the lane size at or under the registered limit (the touch plus at most 1c). No second look is no trade. [design]
3. Cash basis: the price paid plus the fee as charged, rounded up to the cent for the lane size.

## 4. The entry bar [design]

All of these, read once at the end of a block:

1. **A block is 60 fillable signals in a row**, all within the last 21 days, on at least 7 different days, with no single day more than 30 percent of the block's net.
2. Cash profit factor 1.3 or better on the block, and 1.0 or better in each half.
3. **Skew guard:** the block must hold at least 10 of the rarer outcome (wins for a cheap-side rule, losses for a rule that buys above 50c). If it does not, the block keeps growing until it does, and its window may run to 45 days. A rule that buys at 90c therefore needs about 150 signals, not 60.
4. **Blocks never overlap.** After a block fails, the next block starts from new signals. A rolling window re-read after every signal is not allowed.
5. **Confirmation (recommended, the owner chooses):** after a block clears, the next 30 fillable signals must hold a cash profit factor of 1.0 or better before the first live order.
6. Correlation with each live strategy under 0.3 where it can be measured; where it cannot at this sample, a rule that buys the same market, side and minute as a live strategy is refused.

**Why items 3 to 5 exist. The arithmetic, on coin flips with the real fee, 3 contracts, 20,000 runs each:**

| A rule with no edge at all clears "1.3 over 60" | at 20c | at 50c | at 90c |
|---|---|---|---|
| on one block, as the bare rule | 13 percent | 8 percent | 27 percent |
| sooner or later within 300 signals, if the window is re-read as it rolls | 67 percent | 49 percent | 91 percent |
| sooner or later within 300 signals, blocks that do not overlap, both halves at 1.0 | 39 percent | 30 percent | blocked by the skew guard at 60 |
| the same, with the 30 signal confirmation | 18 percent | 13 percent | blocked |
| on the first block, with the confirmation | 4 percent | 3 percent | blocked |

A rule that truly has a profit factor of 1.3 clears its first block only about 42 percent of the time (about 30 percent with the confirmation), and within 300 signals about 93 percent (about 82 to 87 percent with it). So the entry bar is a weak filter by itself: it lets a real rule in about five to ten times as easily as a dead one, no better. The lane's protection is small size, the kill lines and the lane-wide cap below, not the entry statistics.

## 5. Going live

1. The owner's popup with the exact spec (market, side, band, look window, limit, exit, size, kill lines, budget), then the Chief of Staff's merge. The in or out state is replayed from the rule's own rows on every run, like the gold latch, and is never a stored switch.
2. **Size: 3 contracts, fixed, at most $3 of cost an order.** No ladder, no profit add-on, no reinvestment. The registered exit cannot be changed while live.
3. **Live against shadow, first 20 live orders:** if fewer than 60 percent of them fill, or the average fill is more than 1c worse than the shadow's price for the same windows, the rule rotates out and its shadow record is marked overstated.
4. Label everywhere it is shown: "rotating (unproven)".

## 6. Rotating out [design]

Automatic, replayed from the rule's own settled orders on the cash basis. An open position is finished by the rule's own registered exit; the exit watch is not touched.

1. **Fade (out, may return by rule):** from the 60th live fill, at every 20th fill, the last 60 fills show a cash profit factor under 0.7; or the net is under minus 1c a contract at the 50th fill. (These two lines are the ones the Refinement desk calibrated on gold and OICORE; its review of them for 3 contract rules is pending and will be folded into v0.2.)
2. **Kill (latched, returns only by the owner):** a cash drawdown of $10 from the rule's own peak; or the live-against-shadow check fails; or the lane cap in section 8 trips.

What these lines do, on the same coin flips at 3 contracts: a rule with no edge is stopped after about 25 to 50 fills at an average cost of about $2.50 to $3 (one time in twenty, about $11); a rule that truly loses (profit factor 0.8) costs about $5 to $6 before it is stopped. They also stop a rule that truly has 1.3 within 200 fills about two times in three to four times in five. That is what rotating on 60 signals means: real rules are rotated out by noise too, and come back through section 7.

## 7. Cool-off and return

1. After a fade: 14 days, then a new block made only of signals after the exit date that clears section 4 again.
2. After a kill: 30 days, a new block, and the owner's popup.
3. **Open choice for the owner:** whether a return after a fade is automatic (replayed from rows, stated in the original popup, at most 2 automatic returns, each one sent to the phone) or needs a tap each time. Recommended: automatic, at most 2, then a new popup.
4. A third exit of any kind within 90 days retires the rule and adds it to the declined list. Only the owner removes a row.

## 8. How many at once, and the total at risk

1. At most 3 lane strategies live at once, at most one per underlying market.
2. They run in the second slot under its existing caps and count in the shared 12 percent stop and the 5.5 percent window cap as slot orders do today.
3. **Lane cap:** if the lane's combined cash result falls $30 from its own peak, every lane entry stops until the owner re-arms it by popup. [design]

## 9. Not just picking lucky shadows

1. Forward signals only, blocks that do not overlap, one version per rule, a pool of at most 8: sections 2 and 4.
2. **A lane ledger** on the `rnd-queue` branch, kept by the Head of R&D: every rule ever admitted to the pool, every block read, cleared or failed. Each qualification notice to the owner states how many blocks the pool has read so far and how many lucky clears that many blocks would produce with no edge anywhere (blocks times about 0.08, or 0.035 with the confirmation).
3. **The lane scorecard is the real test of the lane's premise**, which is that a good recent record says something about the next few weeks. After 150 lane fills in total, the lane's combined cash profit factor is read once; under 1.0, the lane pauses and the owner decides. It is reported in the Monday rotation review, profit factor first, with n.
4. A lane record is never quoted as a research-bar pass or as proven. Any size above 3 contracts needs the proven bar on live fills and the owner's popup.
5. **Recommended before the first entry:** one registered test of the premise on recorded books (when a block clears, what do the next 60 signals show?), reported with n. It can run on the book recorders' files without any order. The owner may open the lane without it.

## 10. What to expect, plainly [design]

1. At 3 contracts a rule that truly has a profit factor of 1.3 at mid prices earns about 19c an order. At a few signals a day that is a few dollars a week for each rule. The lane at this size is a cheap live test bench and a feeder for scaling; it is not income by itself.
2. By the arithmetic above, if about 1 pool rule in 20 is real, a lane entrant is real about 1 time in 4 and the lane as a whole runs close to break-even; at 1 in 10 it earns a little; at 1 in 50 it loses a little, slowly, inside the caps. Research found no rule at the bar on Nov 12, so the honest prior is at the low end.
3. A rule that buys favourites clears "1.3 over 60" by luck about one time in four. The skew guard is the fix. The gold return rule (60 or more trades at 1.3) has the same weakness and the owner may want the same guard there; that is the owner's rule to change.

## 11. First ranking against the entry bar (Nov 12, 2026; research records on public data, no live figures)

**Qualifies today: none.** No rule has 60 forward, fillable, book-priced signals at 1.3.

| Candidate | What exists | What it would need | Earliest a block could be read |
|---|---|---|---|
| DEPTH1 (a book-state rule on the Bitcoin and Ethereum 15 minute markets) | scorer frozen and audited; first read on recorded books from Nov 14 00:00Z | a clear on its registered read nominates it; then pool registration and a forward book shadow (the R6 recorder runs to Nov 20; the bot's logger after that) | about 2 to 3 weeks after a clear |
| The four rules registered Nov 12 (esports break, in-play price jump, e-soccer rematch, e-soccer tie) | registered, scorers audited, development reads on candles in the next days | candles only nominate; a forward quote shadow on those series (one public read per look; e-soccer has hundreds of matches a day, so the logger's read cost needs sizing), and the non-15-minute order path that exists switched off | e-soccer rules could fill a 60 signal block within about a week of a clearing development read; esports and tennis slower |
| CFRTI-K (Kalshi-only Bitcoin cheap side with a model edge) | development read below the bar and below 1.3; a book replay of 53 signals, 38 filled, under 1.3: no evidence at that n | pool registration, a logger field for the perpetual's reference price; correlation with OICORE is at risk (same market, side and minute) | about 3 weeks of forward signals |
| Spot-lead (Refinement) | missed its own bar at n 58; re-read on unseen windows about Nov 20 | it reads Coinbase and Bitstamp, which no live rule may read without the owner's popup naming the source | not live-able as written |
| Bitcoin settlement-index lead, three venues | a small development record above 1.3 that sits mostly in a barred venue's trades; Kraken-only shows no evidence at n 32 | venue terms read and allowed, or a licence, which is the owner's call | not before the Nov 20 to 24 read |
| Approval NO side | development read near 1.0 with unstable halves | a slow market cannot make 60 signals in 21 days | does not fit the lane |
| Combo house side | paper only, first read Nov 26 | the owner's written exception covers paper first | not before December |
| EVENT830 (live probe) | 15 listed windows in all | cannot reach 60 signals | does not fit the lane; keeps its own rules |

**Closed rules that the full bar alone stopped: none.** Every closed rule either had negative evidence (the sports spread cell, PERPBIN1, two-sided market making, the generators, the order-flow family), or a development record under 1.3 (CFRTI-K, the approval NO side, the stock test), or is on the declined list (the favourite-late copies). The lane does not bring any of them back.

## 12. Open choices for the owner

1. Confirmation step: yes (recommended) or the bare 60.
2. Returns after a fade: automatic up to 2 (recommended) or a tap each time.
3. Lane cap $30 and per-rule drawdown $10 at 3 contracts: accept or change.
4. The premise test in section 9.5 before the first entry: yes (recommended) or skip.
5. Whether the gold return rule should take the skew guard of section 4.3.
