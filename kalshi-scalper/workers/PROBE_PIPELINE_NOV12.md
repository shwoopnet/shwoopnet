# PROBE PIPELINE ASSESSMENT (Nov 12, 2026): which V2 lead is nearest a tiny live probe
Documentation only. No code was edited, nothing was deployed, no Kalshi call was made, no live account figure is in this file. Owner order via main: "We need MORE live strategies. We can't let this hit 0 live." Written from `origin/main` (docs/STRATEGY_LIFECYCLE.md sections 2, 3, 6, 7d to 7g; docs/CHARTER.md; docs/RND_CHARTER.md; docs/POLITICS_RULES.md; docs/SECOND_SLOT_DESIGN.md; functions/kalshiSlotLib.js, kalshiLiveLib.js, index.js, kalshiExitAlarmLib.js) and the V2 workers files listed in the brief. Today is Thu Nov 12, 2026.

## Read this first: what a probe is and is not
- A probe is evidence about FILLS, SLIPPAGE and OPERATIONS (does the order rest, fill, cancel and settle the way the model says). It is NOT evidence about profitability. At 1 contract and a few dollars of daily noise, no probe here can tell a profitable rule from an unprofitable one inside a month (power per candidate below).
- Nothing here lowers the research bar. Every probe is labelled UNPROVEN, is a labelled information purchase (lifecycle section 3, "extra launches allowed as labelled information purchases"), is never a finding, and never counts toward "Live" (the 7f proven bar, cash PF 1.3 over 100 fills in 2 of 3 windows, is unchanged).
- Every probe needs the owner's own popup with an exact spec (RND charter section 7; Charter decision rights). Nothing below is permission.
- Caps used (lifecycle section 6, the incubator): order cap $5, demote to shadow at -$10 cumulative, hard latch at -$20 (only a reviewed edit that moves `reviewedAt` re-arms), total incubator money $40, at most 2 incubators at once, daily limit $10 across incubators, open dollars inside the slot open cap and counted in the shared 12% stop and 5.5% window limit, the direction lock applies, one entry gate. The $200 lifetime politics and parlay budget (POLITICS_RULES) is a separate budget and is not used by any candidate here.

## Ranked table

| Rank | Candidate | Status | What is missing | Earliest first order, fast path | Earliest, safe path |
|---|---|---|---|---|---|
| 1 | MMSIM1 as a 1-lot live fill test on the hourly Bitcoin ladder (KXBTCD), quote 7 (or 4) strikes both sides, flatten at T-15 | NEEDS CODE + NEEDS DECISION | Resting limit orders and a cancel path do not exist in the live code (every order today is immediate-or-cancel; no DELETE anywhere). KXBTCD is outside the slot ticker regex and the slot validator cannot express two-sided quotes; the direction lock forbids the opposite side in one market. Owner exceptions for a short round trip (Charter checklist item 5) and a two-sided position. Unverified: whether the bot's Kalshi key may rest and cancel orders (it was refused HTTP 403 on a shard request once); the real maker fee; which shard KXBTCD sits on | Fri Nov 20 to Mon Nov 23 (before the held-out read, as a labelled fill test) | about Tue Dec 1 to Thu Dec 3, after the Nov 24 read (and the gold correlation, Nov 29) |
| 2 | W-SPOTLEAD1 (spot lead, KXBTC15M and KXETH15M, buy the 50c to 87c side at close-180 s, hold) | NEEDS DATA + NEEDS CODE + NEEDS DECISION | The registered bar (n 80, both halves above 1) was MISSED on Nov 11 (n 58, halves 0.85 and 3.43, leaning FAIL, prior 5 to 8 percent). A read on the extended recording is due about Nov 21 to 23. Code: spot reader, sigma and Phi model at close-180 s, a Coinbase host in a function allowlist, a new signal type the slot validator does not have. Correlation with live strategies unmeasured (gold -0.27 on 11 days, not meaningful) | Mon Nov 24 or Tue Nov 25, only if the Nov 21 to 23 read PASSES its registered bar | about Dec 8 (a fresh 80 fire forward read) to Dec 29 (150 shadow fires at 4 to 5 a day) |
| 3 | CFRTI1-BTC (three-venue index model at close-120 s, cheap side ask 0.04 to 0.30, 1 contract) | NEEDS DATA + NEEDS CODE | The held-out read is not allowed before Nov 20 and needs 50 BTC edge rows (about Nov 22 to 24). A pass means RE-TEST, not a result (a rule with no edge passes about 24 percent of the time). Code: live three-venue index, a model with no slot registry equivalent, three outside hosts, a precise timer at close-120 s | about Nov 26 to 30 (only on a pass, skipping the re-test) | about Dec 10 to 15 (after a fresh 50 row re-test) |
| 4a | MMHOUR1 12 to 18 Central block and high-depth variants | NOT READY (a parameter of #1, not separate) | They are restrictions of MMSIM1 (quote only 12 to 18 CT, or only high touch depth). PF 2.59 and 2.11 on 46 and 142 development events, best of 92 looks, z 3.28 under the 4.39 bar. Same code as #1 | with #1 | with #1 |
| 4b | MMMAP1-qualified non-crypto series (NC15 and R6) as versions of MMSIM1 | NOT READY | MMMAP1 itself runs on or after Nov 15; a qualifier only registers a NEW simulation AFTER the Nov 24 MMSIM1 read; then 100+ events. 15 minute books are a different shape (no T-50) | not before January | not before January |
| 4c | COMBOPRICE1 politics-leg combos | NOT READY | Design only; 0 of 34 sampled combos had a resting ask to buy at (COMBO1), POLCOMBO1B retired. Any placement is by the owner by hand per POLITICS_RULES | never as designed | never as designed |

Ranking logic: #1 is the biggest build but the only one where a week of live data gives a strong answer to a real question (fill rate and adverse selection against the queue model, with no outside host and no overlap with L1's 15 minute markets). #2 is the smallest build (an immediate-or-cancel buy that the slot already knows how to place) but the signal is leaning FAIL and the probe would add almost nothing. #3 is a soft bar and a tiny sample. If the owner must have something live soonest, #1 is the honest choice; it is not a profit machine.

---

## 1. MMSIM1, 1-lot live fill test (KXBTCD)

STATUS: NEEDS CODE + NEEDS DECISION.

### What MMSIM1 actually requires (and a correction to the brief's "every 3 seconds")
The 3 second cadence is the RECORDER's polling rate, not the strategy's. As registered (workers/MMSIM1_PROTOCOL.md) the strategy posts ONE contract at the best bid of each side of each strike at the first book poll from T-50, never reprices, and cancels or flattens at T-15. So the live work is: post once, watch for fills, cancel and flatten at one fixed time. That fits a 1 minute cadence. A live version that reprices or reacts inside a minute would be a different strategy (V1 and V7 are separate registered variants) and would need a worker.

Deviations the live version will have from the simulation, to be stated in the spec: fills are seen at the next 10 second or 1 minute poll (the simulation timed fills to a 30 second tape poll, so this is no worse); the flatten sale happens in the minute after T-15, not exactly at T-15; queue position is real, and a real order can be skipped by price priority or have cancels ahead of it (the model ignores cancels, which is conservative on fills).

### Cadence: what 1 minute cadence can and cannot do
- Cloud Scheduler's minimum interval is 1 minute; every scheduled function here is "every 1 minutes".
- There is already a precedent for sub-minute work inside a minute function: `kalshiLiveExit` is scheduled every minute with `timeoutSeconds: 58` and runs a loop for about 47 seconds with a 10 second sleep (`stopAt = now + 47000`, `setTimeout 10000`). A quoting pass could run in that same loop, or in its own function with the same shape. 10 second polling of fills is therefore available with no new infrastructure.
- Not available at 1 minute cadence: reacting inside a few seconds to a book move (a repricing market maker), and quoting 14 orders on a 3 second clock. Not needed for the registered rule.

### Where it could run
| Option | Fit | Notes |
|---|---|---|
| New scheduled Cloud Function (minute loop, same pattern as `kalshiLiveExit`) | Best | Reuses the key in Secret Manager, the live switch, the heartbeat pattern, the alarm. One run per minute during minutes about 10 to 45 of each hour; post at about T-50, poll fills at 10 s, cancel and flatten from T-15. Compute is a real but small addition: the exit watch already skips idle minutes and would stop skipping minutes 10 to 45 of every hour while an MM order rests (the repo's own estimate for the earlier widening of the exit watch was roughly $3 a month; expect the same order, to be measured in the first week, not promised) |
| One longer scheduled invocation per hour | Possible, not recommended | Newer scheduled Cloud Functions can run longer than 60 s (I recall up to 30 minutes; verify before relying on it), but T-50 to T-15 is 35 minutes, so it needs two chained runs; one crash would leave resting orders and no process watching them |
| GitHub Actions runner | Not recommended for orders | Fine for recorders (all the V2 recorders run there). Using it to trade would put the Kalshi trading key into GitHub secrets, outside Secret Manager, on a PUBLIC repo's workflow surface the security scan is built to distrust, and the recorder pilot already found scheduled jobs start late |
| Cloud Run with a minimum instance (persistent worker) | Not needed for MMSIM1 as registered | New service, new deploy path and a monthly bill (the repo's own estimate for an always-on worker is about $5 to $10 a month, FIVE_MECHANISMS_NOV11). Needs the owner's spend popup. Only worth it if the rule ever reprices on a 3 second clock |

### New code it needs (none exists today)
1. **A resting limit order and a cancel.** All live orders today are `time_in_force: "immediate_or_cancel"` (`kalshiLiveLib.js` lines about 190, 1247, 1383); there is no cancel call. docs/ROADMAP.md already says resting orders must be "their own pull request with a cancel path". Needed: a good-till-cancelled buy at the bid (ideally post-only, so it can never cross and pay a taker fee), a cancel by order id, a batch cancel, and a read of order status and fills. The exact Kalshi fields for post-only and an exchange-side expiration time must be checked against Kalshi's documentation; I did not call Kalshi. If an expiration timestamp is supported it is the best safety: set it to T-15 so the exchange cancels the order even if every function is down.
2. **A separate MM module and registry**, not a slot entry. `SLOT_STRATEGIES` entries are one-shot, one-side, one-ticker-shape (`SLOT_TICKER_RE` lists only the 11 fifteen minute series; `ENTRY_KEYS`, `EXIT_KEYS` and `validateSlotStrategy` have no concept of two-sided or resting). Forcing it into the validator would weaken the one entry gate. A small `kalshiMmLib.js`, frozen constants, `MM_ENABLED = false` until a reviewed edit, an own ticker regex for `KXBTCD-...`, and gates in `test/`.
3. **Direction rule exception.** `directionDecision` blocks the opposite side in one market, and holding YES and NO of the same strike is the strategy. The owner's rule (Oct 29) says only HEDGING is wrong; 7f allows a paired position inside a strategy's OWN legs. It needs the owner's explicit yes and a narrow code path (own legs only, never against an L1 or slot order; KXBTCD is not an L1 series so there is no L1 order to collide with, but Bitcoin 15 minute orders share a time part at the top of the hour, so the window cap bookkeeping must key on the MM ticker). Kalshi nets YES and NO of one market, so a filled pair realises $1 at once; the engine must treat the net position per ticker.
4. **Quote selection:** list the open KXBTCD event closing at the next top of the hour, take the 7 (or 4) strikes with mid nearest 0.5, read each top of book.
5. **Flatten:** at T-15 cancel every resting order, read each strike's net position, sell a one-sided inventory at the bid with an immediate-or-cancel order under the existing `claimClose` lease (reusing the exit watch's close order shape). The exit watch only sells what the bot's own orders opened (`runExitWatch` iterates the bot's order documents); MM orders need their own order documents in the same shape so the watch, the loss stop (`botRisk`), the settle sweep and the nightly report see them.
6. **A watchdog in a different process** (the alarm pattern of `kalshiExitAlarmLib.js`): the exit watch or the minute function cancels any MM order still resting after T-14 and alerts; a heartbeat document for the MM pass.
7. Tests for each gate, the security scan updated for the new function, and the nightly report taught about MM orders. Estimated build: 4 to 6 working days including review. The owner merges and deploys (`deploy-sizing.sh` or a new deploy script).

### Keys, secrets, fail-closed controls
- Reuses `KALSHI_LIVE_KEY_ID` and `KALSHI_LIVE_PRIVATE_KEY` (Secret Manager). No new secret, no new outside host (Kalshi only). Unknown until tried: whether this key's permissions allow resting orders and cancels. A one-lot dry run on a far strike is the first test; a refusal is harmless and is the answer.
- Honours `KALSHI_LIVE_ENABLED`, a new `MM_ENABLED=false` code constant, and the shared loss stop. Fail closed: any unreadable order list, position, lock or clock, any cancel that fails, any fill count above the quote count, any position that does not match the records stops quoting for the rest of the hour and raises the alert; nothing stored can enlarge a quote or add a strike.
- Kalshi money lives per shard (CLAUDE.md "Money across Kalshi's shards"); which shard KXBTCD uses is not in the repo, and the owner tops it up by hand. An unfunded shard would silently stop the probe.

### Cost
- Compute: see above, measured not promised.
- Fees: maker fee is UNKNOWN (the simulation reports bounds 0 and 0.0175 x p x (1-p)); the first live fills settle it, which is itself a result. Taker flatten fee 0.07 x p x (1-p) per contract, rounded up to the cent at 1 lot. Desk A's rounding check (MMSIM1 Amendment 1, item 4): at one contract with the fee rounded up the development PF reads 1.26 at maker 0 and 1.15 at the 0.0175 bound, against 1.41 and 1.28 unrounded. So a 1-lot probe starts from a thinner number than the registration headline.
- Dollars at risk: each order is 1 contract at most 0.97, far under the $5 order cap. The danger is correlated: a Bitcoin drop fills all the YES bids as price falls through them, then the one-sided inventory sells lower. Worst event at 7 strikes is roughly the sum of the YES bids, about $3 to $4 if all fill and the market gaps to zero; at 4 strikes (variant V5, PF 1.26 against 1.28, registered) about $2 to $2.5. Two bad events could reach the daily $10 limit, so 4 strikes is the safer spec.

### Kill rules inside the incubator caps (draft for the owner's popup)
Money (caps from lifecycle section 6): order cap $5 (enforced as 1 contract, price at most 0.97); cumulative realised cash result at or below -$10 after fees: demote (cancel all, stop quoting, keep logging as shadow); at or below -$20: hard latch, only a reviewed edit that moves `reviewedAt` re-arms; daily limit -$10 (US Central day, open orders counted as lost, shared with every incubator); total incubator money $40; at most 2 incubators.
Operational (sticky, fail closed): a resting MM order alive after T-14; a cancel or sell that errors; any fill beyond one per side per strike; a net position that disagrees with the records; the key refused for resting orders; the MM pass heartbeat silent for 2 minutes with an order resting.
Evidence (labelled, so the probe cannot run forever on a broken model; numbers to be confirmed by the owner): after 300 quote-sides, a fill rate under 15 percent or over 60 percent (the model's development rate is about 36 percent per side-quote: 791 fills on 2,226 side-quotes); after 150 fills, a mean 60 second markout worse than -1.5c; after 40 single-leg flattens, a mean flatten loss worse than -4c. Any of these demotes to shadow and sends an approval item.

### What the probe would learn, and the power
- Rate: the development run had 79 fills a day over about 17 quoted events a day at 7 strikes; a live run across all hours may be 80 to 120 fills a day, so about 550 to 800 fills in a week at 7 strikes, about 55 percent of that at 4 strikes.
- Real fill rate against the queue model: 1,600 side-quotes a week gives a standard error of about 1 percentage point, so a 5 point gap between live and model is clear within a week. This is the strongest thing the probe delivers.
- Adverse selection: the 30 and 60 second markout of each live fill against the model's, about 500 fills, standard error well under 0.5c. Also the real maker fee and the real flatten cost and depth.
- Profitability: NOT answerable. Per event sd is about 42c, a week is 140 or fewer events, standard error about 3.5c against a development mean of +3.7c (unrounded) or less (rounded). In dollars a week is roughly +$1.8 to +$4 expected against about $3 of noise (development day sd $1.23). The probe cannot tell +PF 1.3 from 1.0 in a month. State this in the popup.
- Risk that the probe tells us nothing: moderate. Fills could be fewer than modelled (queue depth is large at the money: the high-depth tercile is the better one in MMHOUR1 because it fills late and rarely), the key may refuse resting orders, or the shard may be empty. The first two days answer these.
- Power of the Nov 24 read it sits beside: 0.46 unshrunk, 0.19 shrunk (POWER2); a PF pass is unlikely, so a fill test is the only way the family gets live evidence soon.

### Must happen first
- Fast path: the owner's popup (spec below), the owner's exception to Charter checklist item 5 (no short round trips) and to the direction lock, the build and review, a one lot dry run. It bypasses the Nov 24 read. That is acceptable only because it is labelled an information purchase on FILLS; if the owner prefers not to put money behind a rule that may be falsified on Nov 24, take the safe path.
- Safe path: wait for the Nov 24 read under Amendment 2 labels. CONFIRMED (PF 1.3 or better with a positive day mean) or NO CALL: the owner may open the probe the next week. FALSIFIED (PF under 1.0 on about 400 events): do not open it. The gold correlation (needs about 32 days, Nov 29) is required for the uniqueness check (7d check 3) but not for a labelled fill test.

### Owner popup fields
Name and label "MMSIM1-LIVE-1LOT, UNPROVEN, information purchase on fills"; family (two-sided resting quotes, time flatten) and risk class; series KXBTCD only; strikes (7 or 4, V5 rule), side rule (post at the best bid, both sides, one order per side per strike, never reprice); hours (all, or 12 to 18 Central only); T-50 post, T-15 cancel and flatten; size 1 contract, price at most 0.97; order type (post-only good-till-cancelled with exchange expiration at T-15 if supported); caps and kill rules above; max dollars at risk per event and per day; the real maker fee unknown, bounds; the four uniqueness checks (signal NOT APPLICABLE, exit time flatten and paired inside its own position, correlation not yet measured with the date it can be, not on the declined list); the two exceptions asked; the Nov 24 read dates and what each label means for the probe; review date (suggest 7 days and 14 days); expected output (fill rate, markout, fee, flatten cost) and the sentence "this cannot show profitability".

---

## 2. W-SPOTLEAD1 (spot lead)

STATUS: NEEDS DATA + NEEDS CODE + NEEDS DECISION. This is Refinement's lead, registered on `origin/claude/refine-live` (`kalshi-scalper/refine_tools/SPOTLEAD1_REGISTRATION_AND_RESULT.md`, `FIVE_MECHANISMS_NOV11.md`), mechanism 5. It is not on `origin/main` as a registration; `origin/main` CLAUDE.md records only the recorder extension. `origin/rnd-queue` has no SPOTLEAD file.

### What it is
At close minus 180 s on KXBTC15M and KXETH15M, p_yes = Phi(ln(S/K)/(sigma x sqrt(3))) with S the spot, K the 15 minute strike and sigma from the 60 latest 1 minute Coinbase returns; buy the side whose p minus its ask is at least 0.10 and whose ask is 0.50 to 0.87; one trade per window per asset; hold. The 88c to 97c band is excluded on purpose (not a favourite-late variant; the uniqueness check still has to be scored by the independent check).
First read (Nov 11): n 58, PF 1.58 at +0c and 1.51 at +1c slip, 74 percent wins, but halves 0.85 and 3.43; bar MISSED (n at least 80, both halves above 1); prior 5 to 8 percent; leaning FAIL. The read used a Coinbase 1 minute candle as spot and a Coinbase candle open as the strike proxy, not Kalshi's CF Benchmarks strike.

### Missing
- Data: a read on the extended BTC and ETH recording. Main's CLAUDE.md says R6 for Bitcoin and Ethereum runs to Nov 20 23:59 UTC; the brief says an approval to Dec 15 (not seen in the repo by me; the first read does not depend on it). At 4 to 5 fires a day, n passes 80 around Nov 16 and about 95 to 100 by Nov 20; read about Nov 21 to 23. Note the first 58 were already read, so only the post Nov 11 windows are fresh.
- Code: the model must be rebuilt live. Spot reader (Coinbase public candles, one call for 60 minutes plus the latest, per asset per window), the sigma and Phi step, the strike from the live market object (a different K than the proxy the test used, so a parity check on logged windows is needed), a decision at close-180 s, a buy at the ask. The buy is an immediate-or-cancel at the ask, which the slot already does for OICORE (limit with slip, held). What the slot does not have: a model signal. OICORE's open interest rise (`oiRiseMin`) is the precedent for a computed entry signal, so this is a new reviewed entry key plus a new signal reader, and a new outside host (`api.exchange.coinbase.com`) in a function allowlist with its exact-list gate (the pattern is `ALLOWED_HOSTS` plus a pinned test, docs/MARKET_TAPE_SOURCES.md and `test/noYahooMarketTapeGates.test.js`). A Kalshi-only function has no such list today.
- Latency: the minute function wakes at the top of the minute with scheduler jitter and cold start. The registered bar already requires PF above 1.0 at +10 s delay (it read 1.67 at n 60), so a few seconds is tolerable. A sleep until close-180 s inside the function is possible.
- Decision: the owner's popup; an incubator slot (1 contract, cap $5 order, ask at most 0.87 so cost at most 0.87 plus fee); the 7d scoring of the four checks; correlation under 0.3 against gold and OICORE needs at least 20 overlapping days of fires and is not available.
- No external-signal shadow logger exists (`kalshiShadowLib.js` carries Kalshi price rules only, RND charter section 4). So the lifecycle path Shadow then Probe needs either that logger built or the offline R6 replay as the shadow.

### Power and what a probe gives
About 4 to 5 fires a day pooled means roughly 30 fills in a week. Per fill sd about 0.45, so the week's mean has a standard error near 8c. Tells us: the real ask at the decision, slippage against the recorded ask, whether a spot-computed edge still shows 3 minutes before close under real latency. Tells us nothing about profit. A 5 to 8 percent prior and an unstable half split mean the most likely outcome of the Nov 21 to 23 read is no probe at all.

### Must happen first
The Nov 21 to 23 read PASSES the registered bar as written (no new variant: edge 0.05 gave 1.35 with halves 1.05 and 1.77 but is not the registered rule and counts as a new try). Code can be written in parallel from Nov 13 at low priority; it should not be merged until the read passes.

### Earliest first order
Fast: Mon Nov 24 or Tue Nov 25, only if the read passes and the owner approves a straight-to-probe. Safe: a fresh forward read of 80 fires (about Dec 8) or a 150 fire shadow (about Dec 15 to 29), then the probe.

Owner popup fields: name and UNPROVEN label; series KXBTC15M and KXETH15M; the exact formula and constants (look 180 s, edge 0.10, band 0.50 to 0.87, sigma window 60 minutes, strike source); 1 contract, limit at the ask plus 1c slip, hold; caps and kill rules; the Coinbase host and its terms; the four checks with the gold and OICORE correlation "not yet measured"; the failed first read quoted as the earlier NO it is exempting; what it cannot show.

---

## 3. CFRTI1-BTC as a probe

STATUS: NEEDS DATA + NEEDS CODE. Card in workers/WATCH_CFRTI1_BTC.md; script `src/scalper/cfrti1.py`.

### What it is
At close minus 120 s on KXBTC15M, build a three-venue index (Coinbase, Kraken, Bitstamp, each venue's latest price within 10 s, averaged), compute sigma from 61 index points on a 10 second grid (scaled by sqrt(8)), p_yes = Phi(ln(index/K)/sigma), and buy the CHEAP side (ask 0.03 to 0.30 in the test, 0.04 to 0.30 in the brief) if the model edge is at least 0.05 and the YES spread is at most 3c; hold. Development: n 36, PF 2.54, win 33 percent, mean +15.6c, z +2.11, a cell chosen after seeing the series split, so its z does not count. Pooled over 5 series PF 1.14 (n 211, z 0.67).

### Missing
- Data: the single held-out read, allowed on or after Nov 20, runs when 50 held-out BTC edge rows exist (about 3 a day, about Nov 22 to 24). Pass bar PF 1.3, positive mean, n 50, one try. POWER2: power 0.75 for the shrunk effect, 0.37 if the pooled 1.14 is the truth, and a rule with NO edge passes about 24 percent of the time. A pass means RE-TEST on a fresh sample, never a candidate for live use. A re-test of 50 rows takes about another 17 days at 3 a day.
- Code (the slot registry shape cannot express it): a live rebuild of the index needs the last 10 minutes of trades from three venues. Public REST reads of each venue's recent trades or candles, around three calls per window at close-125 s, or a persistent tick worker; a REST design fits a minute function that sleeps until close-120 s. It must reproduce the script exactly (latest price within 10 s, 61 points, the 3 second quote freshness check, the active status and the 3c spread rule), including receive-time stamping for every venue (Amendment 1: a timestamp-format bug had silently dropped two venues and turned n 36 into 55 to 60). A parity test against logged windows is required. Strike K from the live market object.
- Outside hosts: Coinbase, Kraken and Bitstamp public APIs. New function allowlist entries, a pinned exact-list gate, the terms-of-use rule (POLITICS_RULES: only sources whose terms allow automated reads), and a failure rule (any venue missing means no order).
- Latency: the model is evaluated at close-120 s and the order must reach Kalshi before the window closes; the registered test used the quote at or before close-120 s within 3 s, so the live order should be sent inside about 5 s. Feasible; a cold start could miss it, so the function should be warm or start early and sleep.
- Decision: owner popup; the slot's `leftMaxSec` and `leftMinSec` window (120 to 840 s) permits close-120 s, and the price band 0.04 to 0.30 fits the entry price bounds (0.05 to 0.97, so 0.04 itself is outside `SLOT_MIN_PRICE` 0.05: the band must start at 0.05 or the constant must change by reviewed edit).

### Power and what a probe gives
About 3 fires a day, 20 a week; win rate near 33 percent. Per fill sd about 0.40 against a claimed mean of +15.6c: 20 fills have a standard error near 9c, so a week cannot distinguish the claim from zero. Value of a probe: confirm the live three venue index agrees with the recorded one, the order reaches Kalshi in time, and slippage against the displayed ask. The right order of work is the held-out read, then (on a pass) the re-test, then a probe.

### Earliest first order
Fast: about Nov 26 to 30, skipping the re-test (not recommended: 24 percent false pass). Safe: about Dec 10 to 15, after a fresh 50 row re-test.

Owner popup fields: UNPROVEN label; series KXBTC15M; exact formula and constants (edge 0.05, 10 s window, sigma scale sqrt(8), 61 points, spread at most 3c, price 0.05 to 0.30); 1 contract at the ask with 1c slip, hold; three hosts and their terms; caps and kills; the held-out result and the 24 percent false pass note; the four checks (different data source, hold with different entry, correlation unmeasured); what it cannot show.

---

## 4. Anything else nearest to live

- **Already live in the slot registry (not counted here):** OICORE and EVENT830, plus gold L1. This assessment is for additions.
- **MMHOUR1 blocks and depth terciles** are parameters of #1. If the owner approves #1, the narrowest version is MMSIM1 quoted only 12 to 18 Central at high depth: the best development cell (n 43 events, PF 6.78, z 3.20) is also the most selected; it would cut worst-event exposure and compute, but it is 1 of 92 looks and carries no extra evidence.
- **MMMAP1** (run on or after Nov 15) may name a non-crypto series where a maker's realised spread is positive. A qualifier is a lead and a NEW registration after Nov 24, then 100+ simulated events: not before January.
- **Retire list (POWER2 notes):** 9 of 16 queued cards cannot reach a verdict; none is a probe candidate. COMBOPRICE1 and the combo cards have no ask to buy at.
- **A supply warning, not a recommendation:** none of the three leads clears the research bar; all three have a prior at or below 8 percent for the bar and the false-positive share of past screens was 33 to 50 percent (lifecycle section 1). Opening probes keeps something in the pipeline and buys operational facts (resting orders, a model signal at a live host, real latency); it does not replace gold's edge. The honest path for "not zero live" is to build the capability once (resting orders with a cancel path, a model-signal entry type, a host-gated reader) so a survivor goes live in days, and to run #1 as the cheapest fill test.

## Decisions the owner is asked for (pop-ups to be built by main)
1. Build the resting-order and cancel path now (PR, no live use), yes or no. It gates #1 and any future maker work.
2. MMSIM1 fill test: fast (about Nov 20 to 23) or safe (after Nov 24), 7 or 4 strikes, all hours or 12 to 18 Central, and the exceptions to Charter item 5 and the direction lock.
3. Whether to build the model-signal entry type and the host-gated spot reader in parallel for #2 and #3 (merged only after a pass).
4. Confirm the evidence kill numbers in section 1.

No bar was lowered, nothing was deployed, nothing here authorises an order.
