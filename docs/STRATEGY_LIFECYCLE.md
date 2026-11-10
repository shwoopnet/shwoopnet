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
| Gold L1 | drawdown from gold's own cash peak (since the re-arm, 2026-11-10) | 6% of the sizing base ($58.75 at $979.25) | any time, checked every minute | **latch gold off, no auto restart** [coded Nov 10, DRAFT until merged and deployed: `docs/GOLD_KILL_LATCH.md`] |
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
