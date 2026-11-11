# Strategy lifecycle spec (Nov 9, 2026; rebuilt for the fast path)

Owner priority, Nov 9, 2026: full time algo trading; a goal of **at least one new live strategy per week**; kill conditions and return conditions for **every** strategy; quick scaling, quick turnover, quick returns and a constant R&D cycle. The owner judged the first draft's gates (400 to 600 fills, 20 or more days, then 300 more live fills) too slow ("we'll never get to live honestly"), so this version puts money behind **fast kills and tiny caps instead of slow gates**, and says plainly what that costs. This file is a SPEC; the four build pull requests that implement it are separate and each needs the owner's "merge". Profit factor (PF) means gross wins over gross losses, net of fees, on the **cash basis** (fill price plus fee, exits at the exit price and fee). All figures were reproduced by both chats on that basis; the nightly report's stored `settledPnl` is limit booked before PR 741 and must not be used for PF.

## 1. The honest frame

- **Supply, not gates, is the bottleneck.** After 1.5 million rules tried there are 0 rules above PF 1.3 with n over 200. Near misses only: NFL pair PF 1.73 (225 trades, 12 dates), tennis Monday 1.57 (116), Bitcoin ladder rule 1.43, NBA total NO 1.26 (261). A weekly launch needs 4 to 8 candidates in shadow at any time, so the pipeline is fed every week; expect 0 to 1 real edge a month and the rest to be information purchases.
- **The record we are rotating:** all L1 on cash PF 1.12, 1,008 trades, net +$43.14; gold 1.40 (307, +$61.02) but fading by period (4.91, 1.49, 1.01); OICORE 1.32 (77, +$25.09); Ethereum 1.18; Dogecoin 1.01; Bitcoin 0.84; XRP 0.49. Of six strategies a screen would have passed, 2 were clear live winners, 2 flat, 2 losers: **false positive share 33% to 50%**.
- **The cost of speed is stated, not hidden.** A shadow gate of 150 fills passes 12% (tail) to 23% (favourite) of zero edge ideas and 2% to 8% of losers, and passes only about 70% of true PF 1.5 ideas: it screens, it cannot prove. A failed incubator costs about $1.0 to $4.4 after 150 fills and $2.7 to $11.9 after 400 (a tail loss is $0.11, a favourite loss $0.94, so the $20 cap rarely binds). At one launch a week (about 13 a quarter, 8 to 10 of them failing) that is **about $30 to $70 a quarter expected, $260 worst case** (13 x $20), paid for a live, forward PF on 150 real fills per idea, the only evidence that survives decay.

## 2. Stages

| Stage | What runs | Money at risk | Who moves it |
|---|---|---|---|
| 0 Research | History scans, registered before scoring, last third held out and read once | none | research chat |
| 1 Shadow | The rule runs on live quotes and only LOGS (rule, ticker, side, price, size, `wouldFill`, the quote); no order | none | owner merges the shadow registration |
| 2 Incubator | A slot strategy: 1 contract or $5 an order, its own dollar caps | at most $20 each, $40 total, 2 at once | owner merges the registry edit |
| 3 Live | The slot size ladder step 1, then steps; or a ladder market | the existing slot caps | owner merges |
| 4 Retired / killed | Latched off; open orders still settle and are sold; the record stays in the report | none | automatic (kill rule) |

## 3. Fast path: PASS rules

| Step | Rule (cash PF, 10 contract fees) |
|---|---|
| Registration | exact rule, market, size, counterparty or "none named", numeric prediction and kill criteria, written and committed before the first shadow row |
| Shadow to incubator | 150 shadow fills, at least 7 days, PF 1.3 or better, a held-out second half at 1.2 or better, no single day over 30% of net, owner merge on the promotion packet |
| Incubator to ladder step 1 | 150 incubator fills with PF 1.3 or better, cumulative net above $0, at least 7 days; then a second 150 at PF 1.2 or better before the first size step (300 fills, two windows) |
| Each later size step | +300 fills at PF 1.2 or better on cash, inside the base needed for that step |

**Time at those fills:** one 15 minute market (about 9 fills a day) takes 17 days per 150 (34 for two windows); a pooled basket of 8 markets (about 30 a day) 5 to 10 days; an hourly series (one entry an hour) about 6 days per 150; sports and daily strategies are weeks to a season, not weekly. So a weekly launch rate is sustainable only with several candidates in shadow at once (shadow costs nothing but needs a row writer, which does not exist yet; PR (a) below).

Deflation still applies to the research stage: every hypothesis ever scored stays in N forever (a retired strategy's whole search counts, not only its winner), no re scoring a failed candidate on the same data, held out thirds read once; total alpha 0.05 a year; **a budget of 4 incubator promotions a quarter in the formal count, with extra launches allowed as labelled information purchases** that are never presented as findings.

## 4. KILL conditions, every strategy (cash basis; [existing] = in code today)

| Strategy or stage | Metric | Threshold | Window | Action |
|---|---|---|---|---|
| Gold L1 (PF 1.40, n 307) | next 100 settled cash PF | under 1.0 | next 100 trades from Nov 9 | size step down PROPOSAL to the owner (the tripwire) |
| Gold L1 | drawdown from gold's own cash peak (since the re-arm, 2026-11-10) | $58.75 fixed (6% of the $979.25 base when written) | any time, checked every minute | **latch gold off, no auto restart** [coded Nov 10, DRAFT until merged and deployed: `docs/GOLD_KILL_LATCH.md`] |
| Gold L1 | cash net since the re-arm | under -$20 after 40 trades | | **latch gold off** (same code) |
| Gold L1 | rolling 100 cash PF; 3 early sells in 40 trades | under 1.0; 3 or more | | ALERT only (event in the notification center), same code |
| Gold L1 | rolling 60 cash PF | under 0.7 | any window ending after Nov 9 | ALERT only, coded Nov 10 (it fired once, Nov 6, and the next 50 trades were PF 99: a false kill as a latch) |
| Account (all strategies) | shared 12% stop ($117.51 at base $979.25) and 5.5% window limit | breached | rolling 24 h | latch off [existing] |
| OICORE (PF 1.32, n 77) | streak 24 or net under -$6 after 40 fills | trips | settled order history | latch off [existing] |
| OICORE | net under -1c per contract | after 50 fills | | ALERT |
| EVENT830 (5 trades, 0 wins, -$0.85) | its [existing] rules need 40 fills, unreachable at 1 trade a week | add: cumulative -$5 | any time | latch off |
| Probe (1 contract or $5 an order) | net | under -$5 | any time | latch off |
| Probe | PF | under 1.0 | after 100 fills | demote to shadow |
| Incubator | cumulative loss | -$10 | any time | demote to shadow |
| Incubator | cumulative loss | -$20 (the cap) | any time, checked after every settlement | latch off, no restart |
| Incubator | early cash PF | under 0.7 | after 40 fills | demote to shadow |
| Shadow | signals | under 40 in 30 days | | retire (not enough to judge) |
| Shadow | net | under -1c per contract | after 50 shadow fills | retire |
| Paused markets (XRP, Bitcoin, Ethereum, AUD/USD, USD/CAD, natural gas; Dogecoin removed) | stay paused | shadow cash PF under 1.0 after 100 fills, or net under -1c per contract after 50 | | stay paused and drop the candidate |

**Rolling 60 PF under 0.7 is an alert, not a kill, everywhere.** On the cash record it caught nothing useful (XRP only, and XRP's loss was small). Streak latches, loss rate tests, dollar drawdown for live strategies, 40 fill PF floors and a trailing 100 fill PF under 1.0 (net effect +$0.80 on +$43.14) are noise and are not adopted. **All thresholds are defaults untested on more than one real failure; re-check after each rotation.** Not measured: false kills the dollar kills would cause (no incubator history exists) and the shadow versus live fill gap per market (a candle shadow overstates live; live fill rate is about 65%), so the incubator is the real test.

## 5. RETURN conditions, every killed or paused strategy

**General rule (all):** after a kill, a **14 day cool off**, then a fresh shadow of **100 to 150 fills at cash PF 1.3 or better**, a held out second half at **1.2 or better**, at least 14 days, no single day over 30% of net, then the owner's approval by promotion packet. Re entry path: shadow, then incubator ($20 hard cap, 1 contract or $5 an order, 100 to 150 fills), then ladder step 1; a step up needs 100 to 300 more fills at PF 1.2 to 1.3 on cash. Only a reviewed edit (moving `reviewedAt`) re arms a latched strategy.

| Market | Cash PF (n) | Fills a week | 100 shadow fills takes | Note |
|---|---|---|---|---|
| XRP | 0.49 (86) | 30 | 3.3 weeks | first read Nov 12 (FLOOR1 and THIN1) |
| Bitcoin | 0.84 (155) | 33 | 3 weeks | |
| Ethereum | 1.17 (113) | 26 | 4 weeks | the smooth climb rule removes about 95% of windows |
| Dogecoin (removed) | 1.01 (204) | 72 | 10 days | return would be a reviewed edit of the three lists |
| AUD/USD | 1.37 (59) | 24 | 4 weeks | |
| USD/CAD | 1.00 (46) | 19 | 5 weeks | |
| Natural gas | 0.64 (38) | 14 | 7 weeks | |

**Gold (coded Nov 10, 2026, the owner):** a killed gold returns only by a reviewed edit that moves `GOLD_KILL.rearmAt`, after the shadow GOLDALL rows show PF 1.3 or better over at least 60 trades and 7 days with the second half at 1.3 or better, and the owner approves; the first 30 trades after the re-arm go at half size. Refinement warned this bar is stricter than gold's long run record (PF 1.40 on 307 trades) and may keep a normal gold out; the cost of that is idle gold, not lost money. OICORE if killed returns by the general rule above. The banned structures stay banned: no favourite and hold, no expensive entry long hold (GOLDHOLD was declined Nov 9).

## 6. Capital rules and the fast path's safety limits

- Today's slot caps at base $979.25 are SHARED across the slot (order $9.79, window $19.59, open $29.38, day $19.59, lifetime $58.75), so one incubator could eat OICORE's room. **That needs a code change: per strategy caps.**
- Incubator: order cap $5 (worst loss about $5), demote to shadow at -$10 cumulative, hard latch at -$20, checked after every settlement.
- **Fast path safety:** total incubator money at risk $40 (2 x $20), at most 2 incubators at once, a daily loss limit across all incubators of $10, open incubator dollars inside the slot open cap and counted as lost in the shared 12% stop and the 5.5% window limit (already true for slot orders), the direction lock applies, one entry gate.
- Step sizes: shadow zero money; probe 1 contract or $5 an order, under 1% of the base; ladder step 1 inside the existing caps; sums of open slot dollars stay under 3% of the base.

## 7. What can be automated, and what stays human

The line the code already draws, and this spec keeps: **nothing stored can add a strategy or enlarge one.** The registry (`SLOT_STRATEGIES`, `SLOT_HOLD_ALLOWED`) is a hard list in code; a stored value can only switch things off. So:

- **Automatic and safe: KILL and DEMOTE inside the caps.** The sticky latch (`kalshiSlotControl/killed`, `killCheck`) already exists; the new part is the dollar kills, the early PF demotion and shadow retirement. They only reduce exposure.
- **Alerts, not actions:** rolling 60 PF under 0.7 and the gold tripwire go to the owner as approval items.
- **Human: PROMOTE (shadow to incubator to ladder).** A promotion is a registry or size edit in code. The system does everything up to the merge: a nightly scorer produces the promotion packet and the chief of staff drafts the pull request; the owner types "merge N" and runs the deploy. **No Charter change is asked.** A safe speed up that does not need one: batch a week's promotions into one pull request and one deploy.

## 7b. The weekly rotation owner (Nov 10, 2026, the owner)

The Refinement chat (Head of Live Strategy Performance) is the weekly **rotation owner**. Every week, Monday morning US Central, it reviews EVERY strategy (live, probe, shadow and retired) against its IMPLEMENT, KILL and RETURN rules on the cash basis and sends ONE short rotation recommendation: keep, watch, size step, kill, return, or which shadow rule to promote, with profit factor first. The owner approves each item by popup. It also flags any strategy that is missing one of the three rules. It only recommends: nothing changes without the owner, a promotion is still a reviewed edit in code, and the owner still says "merge N" and runs the deploys. The first recommendation is due Monday Nov 16, 2026.

## 7c. The favourite-late shadow cap (Nov 11, 2026, the owner)

Favourite-late rules (buy the favourite side at 88c to 97c in the last minutes) are the same bet on different markets and bands, and they were filling the shadow list. The cap:

- **At most 3 favourite-late shadow rules at once, and at most ONE per underlying market.** Count by market, not by rule name: two rule names on gold are two rules on one market.
- **New shadow slots go to a DIFFERENT mechanism** unless a favourite-late variant states a distinct reason: a new underlying, a new look time or new information.
- **A favourite-late shadow is retired when it passes or fails its read**, which frees the slot.
- First use: GOLDHI6S (0.92 to 0.97 at 6 minutes) was a subset of GOLDALL's signals (0.88 to 0.97 at the same look), so it was folded into GOLDALL and is read there as a split by price band. The registry is now XRPYES10, GOLDALL, XRPFAV6 and LANTERN. Rows already logged stay in `kalshiShadowRows`.

Ready non-favourite candidates for the next shadow slots, in priority order. Several are not expressible as a shadow rule in the registry today (they need outside data or fields the registry does not read), so they are read at read time instead of being logged by the minute function:

1. **Polymarket Bitcoin lead filter on OICORE:** a forward, read time join of public Polymarket history; no logger.
2. **OICORE book imbalance:** `bidSize` and `askSize` are already logged on every order; read at read time.
3. **Ethereum open interest confirmation:** re-read Dec 3.
4. **Rain:** the RAINCAL recorder is already recording.
5. **Liquidation cascades:** the OKX logger is merged.

## 7d. The uniqueness check (Nov 11, 2026, the owner, a HARD RULE)

The owner, frustrated, after saying it many times: "how many times have i told you to continue finding unique strategies?" The rule, in force for every chat that proposes, ranks or admits a strategy:

1. **Every new candidate passes a UNIQUENESS CHECK before it gets a shadow slot or any test time.** It states its ENTRY reasoning, its MANAGEMENT and its EXIT, and names the existing mechanism it is closest to and why it is different. A candidate that cannot do this in a few plain lines does not get a slot.
2. **A favourite-late variant is REJECTED as a duplicate unless the owner approves it.** Same 88c to 97c late-window logic on a different market, look time or size is a duplicate, not a new strategy (this tightens the "distinct reason" exception in 7c: that exception now needs the owner's approval, not just a stated reason).
3. **The backlog is ranked by uniqueness first, then by prior.** Entries that are favourite-late variants are relabelled as duplicates, not left looking like fresh ideas.
4. **The weekly rotation review (7b) shows the mechanism family of every strategy**, so a list that is mostly one family is visible at a glance.
5. **V2 and Refinement each propose five genuinely different mechanisms** when asked for candidates, not variants of each other or of what is live. Different means a different information source, timing structure, market type, exit logic (scaling, time exits, hedges), relative value, an event or calendar setup, or another venue.
6. **Never answer "menu empty".** If the bot's own markets are exhausted, say what data or venue would be needed to test a different mechanism and what it would cost, so the owner can decide.
7. **The mechanism families today:**
   - **Favourite-late:** gold L1, XRPYES10 and KESTREL (live); GOLDALL, XRPFAV6 and LANTERN (shadow).
   - **Cheap-side open interest:** OICORE.
   - **Event or calendar:** EVENT830.
   - Every live strategy except gold holds to settlement, so there is no real exit or management diversity yet: no scaling, no time exit, no hedge. That gap is itself a place to look for unique mechanisms.
8. **The measurable test (the owner, Nov 11, 2026, popups: ADOPT, then the owner's definition of UNIQUE).** A candidate counts as unique only if ALL FOUR hold:
   1. **The SIGNAL is different:** a DIFFERENT DATA SOURCE or a DIFFERENT MARKET TYPE. Timing structure or price zone alone does NOT make it different (an 88c to 97c rule at another look time or on another market of the same type is the same signal).
   2. **The EXIT is different:** time-based, a target or scaling, or paired within its own position; AND "hold to settlement" also counts as a different exit when the ENTRY RULES are different and the strategy will NOT hedge or interfere with another market or strategy (owner: "4 counts as different if it's different entry rules and won't hedge or interfere with another market or strategy"). Signal and exit logic are the two that must differ (the owner: "primarily signal and exit logic should be different"), and the ENTRY rules must be different too. This replaces the earlier "2 of 4 axes" wording.
   3. **Correlation under 0.3 with EVERY live strategy on the cash basis.** In shadow, its daily cash P&L (US Central day, 1 contract, fill price plus fee, early sells included) has Pearson r under 0.3 against each live strategy, measured over at least 20 overlapping days; the 90% interval and the share of its signals in the same 15 minute window as a live order are reported alongside (information, not extra gates). Before that data exists the status is NOT YET MEASURED: checks 1, 2 and 4 are applied at registration and check 3 at the first read.
   4. **Not on the declined list (7e).** A renamed or near-identical version counts as the declined idea.

   **How "paired or hedged exit" and "must not hedge or interfere" fit together:** a paired or hedged exit is allowed only inside the strategy's OWN position (for example, its own two legs closed together, or its own time or scale exit). It may never take a position in another market, or against another live strategy's position, to cover it; the direction lock (a slot or L1 order may never sit on the opposite side of another order in the same market) stays as it is. FOLLOW-UP QUESTION for the owner: confirm that "paired" means legs of the same strategy, not a hedge against another strategy.
9. **Every candidate, probe and owner popup shows the four checks** (pass, fail or not yet measured, each with one line of evidence). A popup that asks for an exception quotes the earlier NO it exempts.
10. **Filters are not strategies.** A rule that only filters or sizes an existing strategy (for example a Polymarket lead, book imbalance or open interest confirmation on OICORE) is judged as a refinement of that strategy by the rotation review, and takes no shadow slot as a new strategy.

## 7e. The declined list (Nov 11, 2026, the owner)

Trigger: after an audit the owner said "we have multiple duplicates that I hard killed and said NO to very clearly and somehow they made it to live?". A NO from the owner was not written down anywhere a later candidate would be checked against it, so the same idea came back under a new name. This list is that place.

**Rules**

1. Every candidate, every shadow slot, every popup to the owner and every pull request that adds or widens a strategy is checked against this list FIRST. The check is written in the candidate's uniqueness note, naming the rows it was compared with.
2. A renamed or near-identical version (same mechanism, band, market or look time) counts as the declined idea, whatever it is called.
3. Any popup asking the owner to make an exception must QUOTE the earlier NO and name exactly what it exempts.
4. The Release Manager checks this list on every strategy pull request, and the weekly rotation review (7b) lists it.
5. Only the owner removes an entry.

A Charter line making the check explicit is proposed for the owner. `docs/CHARTER.md` says only the owner changes it, so it is not edited here.

**The list**

| Idea | Date | The owner's words or source | Status | Names it must not return under |
|---|---|---|---|---|
| Gold L1 band narrowed to 92c to 97c | Nov 10, 2026 | PR 756, closed unmerged; the owner: "kill". GOLDHI6S was merged as a shadow before the kill and folded into GOLDALL on Nov 11 | Declined | GOLDHI6S, gold-band, any gold favourite narrowed above 0.92 |
| XRP as an L1 market | Oct 28, 2026 | The owner, on the research session's read; paused in code (`PAUSED_SERIES`), resume only by a reviewed edit | Declined (paused). XRPYES10 was a later, named owner exception on Nov 10 and covers only that strategy | KXXRP15M under L1, any XRP favourite rule other than the excepted XRPYES10 |
| Probe markets AUD/USD, USD/CAD, natural gas | Oct 28, 2026 | The owner: "yeah we can" | Declined (paused). KESTREL AUD/USD was a later owner decision on Nov 10 and covers only that strategy | The three probe series under L1, any other rule on them |
| Bitcoin as L1 | Oct 29, 2026 | The owner: "we can kill bitcoin i guess" | Declined (paused). Bitcoin trades only as OICORE, a different mechanism | KXBTC15M under L1, any Bitcoin favourite or smooth-climb rule |
| Ethereum as L1 | Oct 30, 2026 | Paused in code | Declined (paused) | KXETH15M under L1 |
| Dogecoin | Nov 9, 2026 | The owner: "remove Dogecoin entirely" | Declined (removed from the bot) | KXDOGE15M, any Dogecoin strategy |
| Gold ladder cap and half-size rule | Oct 28, 2026 | The owner: "we need to achieve more profit % per win instead of just scaling up or down" | Declined | Any cap, step down or size rule whose point is only to scale the gold ladder |
| Favourite-and-hold for NEW live strategies | Charter | `docs/CHARTER.md` brief checklist item 5 | Banned unless the owner grants a named exception in writing: XRPYES10 (Nov 10), KESTREL (Nov 10) | Any buy-the-favourite-and-hold rule without a written exception |
| Maker or resting entries on gold | Nov 10, 2026 | W-MAKERREPLAY1 | Closed by evidence (not an owner NO) | Gold resting-entry variants |
| Gold 94.5c price floor | Nov 10, 2026 | W-BAND945 | Closed by evidence (not an owner NO) | Gold price-floor variants near 0.945 |
| GOLDHOLD | Nov 11, 2026 | Name given in an owner message Nov 11 | Name given in an owner message Nov 11; no definition found in the repo: the owner or the EA must supply it | GOLDHOLD, and anything the owner or EA defines it as |

## 8. Code plan (four small pull requests, each its own "merge", stacked; one deploy at the end)

What already exists: the registry and validator, per strategy kill rules and the sticky latch, slot caps scaling with the base, the shared 12% stop and 5.5% window limit, per strategy stop meters on the page, the skip log (`kalshiSlotSkips`, report `skips`), order records and the nightly report with `slotOrders`. Missing, in build order:

1. **(a) Shadow logger and stage field.** A log only path in the slot tick for rules registered as `stage: shadow` (rule, ticker, side, price, size, `wouldFill`, quote), written to a new collection after the minute's orders, never an order, every error swallowed; a `stage` field in the registry. Inert until a shadow rule is registered; the off equivalence fixtures stay byte identical.
2. **(b) Per strategy caps, incubator limits and the new kill rules.** Per strategy dollar caps in code (order $5, kills at -$10 demote and -$20 latch, total incubator $40, at most 2, daily $10), the probe and EVENT830 dollar kills, the early PF demotion, shadow retirement.
3. **(c) Nightly scorer.** A read only function (no Kalshi key, no write except its own report document) that computes cash PF per strategy and window, fills a week, fill rate and fee share, runs the pass and kill tables above and writes a lifecycle report (who passes, who is near a kill, who is dead) plus the promotion packet text. It never changes a strategy.
4. **(d) Lifecycle table on the Bot page.** Stage, trades, cash PF, distance to kill; percentages and PF only, Privacy view safe.

Deploy order as always: exit watch (`deploy-push.sh`), then the minute function (`deploy-sizing.sh`), then the report (`deploy-report.sh`); `deploy-latest.sh` picks them.

## 9. The candidate supply loop

V2 and Refinement each hand the chief of staff, **every Sunday at 6:41 PM Central (first Nov 15)**, 3 to 5 pre registered shadow candidates: exact rule, market, size, cash PF and n at 10 contract fees, held out status, counterparty, the code it needs, an honest prior, ranked by PF x n (fewer than 3 qualify means it says so and lists near misses), plus at least 2 new registered scans a week to keep the pipeline filling. The chief of staff turns accepted candidates into shadow registrations (one pull request a week, owner merge).

## 10. Honest risks

- **More rotation means more false positives and more fees.** At a bar of PF 1.5 and a million rules tried something clears it by chance; the 33% to 50% false positive share above is on strategies that were already chosen. The control is the deflation count, the promotion budget and the dollar caps.
- **A fast kill can kill a good strategy on a bad draw** (gold's rolling 60 rule fired once and the next 50 trades were PF 99); that is why the rolling rule is only an alert and the kills that act are dollar based.
- **Fast markets judge fast and also lie fast.** Gold went PF 4.91, 1.49, 1.01 across three periods on a loss rate of 2.0%, 7.0%, 8.7% (breakeven about 7.5%), mostly luck.
- **The limit is the edge, not the machinery.** A faster rotation system finds out sooner that a candidate fails; it does not create a strategy that works.
