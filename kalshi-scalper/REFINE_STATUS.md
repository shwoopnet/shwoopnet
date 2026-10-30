# Live Strategy Refinement, status (newest first; times US Central)

Scope: refine what is live (L1 on gold and Dogecoin, the OICORE second slot). New strategy families go to V2 via the main session. Read only: no trading code, no deploy, no merge.

## Standing queue (ranked; refill when under 5; each item needs a registration here BEFORE scoring and adds its tries to N)

Counts as of 2026-10-30 2:00 PM CT: N 728,652. Status: R = registered, Q = queued.
1. R1 band edges 86 to 88c and 97 to 98c (gold, Dogecoin). R, waiting on counts-only history.
2. R2 no-fill share, limit +1c simulated on R6. R, waiting on R6 days and an order export.
3. R3 Dogecoin 20:00 to 23:59 CT block vs rest. R, waiting on counts.
4. R4 size effects by order size from the nightly report. R, running now (report already carries `allStrategies` and `secondSlot`).
5. Q: OICORE entry timing inside the 180 to 120 s window (which second inside the window fills best, from R6 Bitcoin book). Information first.
6. Q: OICORE fill rate and slippage at 5 and 10 contracts (R6 Bitcoin book depth vs the orders in `slotOrders`).
7. Q: OICORE and L1 in the same window (correlated-window risk): how often a Bitcoin slot order shares a window with a gold or Dogecoin loss. Counts only.
8. Q: L1 exit alternatives as information only (the 25c line vs hold, per market, live record). STRUCT1 and EXIT1 already say the line is neutral, so low priority.
9. Q: L1 gold ladder cap by order size once R4 has 20 orders at 16+ contracts.
Refill rule: if this list falls under 5 open items, add from: Dogecoin entry timing (6 vs 8 minute look), gold quiet hours review (due Nov 24 to 26, V2 owns the read), spread filter at 2c or more as a frequency cost count, OICORE open interest threshold sensitivity (threshold 86,300 vs the trailing percentile), OICORE side rule sensitivity.

## Entries

**2026-10-30 2:15 PM CT, REGISTRATION R1-S and R3-S: the forward scorers (written before any fresh-day outcome is read; adds 0 tries beyond R1 and R3, which already counted them).**
- **R1-S scorer.** Universe: gold and Dogecoin 15 minute markets closing after 2026-10-30 18:56Z (the R1 and R3 freeze). Entry: the candle replay used for the counts (`refine_counts.py`: look at 360 s before the close, l1Pick, one contract, taker at the ask, held to settlement, taker fee 7% x p x (1-p) rounded up per order, stress fee x 1.2). Cells: 86c to <88c and >97c to 98c, each per market and pooled over the two markets. Result per cell: entries, loss rate, net per contract at the verdict fee and at x 1.2, profit factor, day-clustered z against 0. Run by V2's scorer or any copy of it; one read per date.
- **Read dates.** Interim look at 2026-11-14 (after R6 ends), formal read when a cell reaches 150 entries or on 2026-12-31, whichever first. At the counts above a cell collects only about 30 to 50 entries a week across both markets, so 150 is likely about 4 to 6 weeks away: expect NOT_ENOUGH_DATA on Nov 14.
- **Kill (stated now):** at 150 entries, net per contract under +0.5c or loss rate above price plus fee: FALSIFIED. Pass requires profit factor 1.5 in each of three windows after deflation; nothing else counts. A pass only earns a registered live probe brief; no promote verb.
- **R3-S scorer.** Dogecoin 6 minute entries in the live band, block 20:00 to 23:59 CT versus the rest, fresh days after the freeze: net per entry difference, day-clustered z. Read at 100 block entries (about 8 weeks at 13 a week live, about 3 weeks at the candle ceiling of 32). Kill and action as in R3.
- **Ask to V2 (via main):** run both scorers on the fresh-day replay when a read date arrives and push aggregates only; outcome columns stay inside the scorer until then. Nothing for the owner.

**2026-10-30 2:10 PM CT, wake check; queue item 6 (OICORE fill and slippage), first two orders. No threshold.** Dogecoin: still no order above 5 contracts since Oct 28 (the ladder change is not in the record). OICORE: both fills complete (5 of 5 and 10 of 10 contracts, no partial). Price against the quote seen at the decision: order 1 YES paid 6.0c against a seen ask of 5.3c (+0.7c, 13% of the price); order 2 NO paid 7.0c against a seen NO ask of 6.7c (1 minus the seen bid 0.933; +0.3c, 4%). On a 5c to 7c contract that slippage is large in relative terms and counts against a rule whose edge was measured at the signal ask +2c stress (FALS4: PF 1.44 at +2c), so +0.3c to +0.7c is inside the tested stress. Two orders only; re-run at 20. `depthAtLimit` and `shareOfDepth` are null for slot orders, so size against depth cannot be read yet (the slot path does not log them; that would be a code change for the main session to decide, not a request I am making now).

**2026-10-30 2:20 PM CT, R2 descriptive step (why attempts get no fill), from the new depth columns; 0 tries.** Rows with depth context since the columns exist: gold 111, Dogecoin 116 (the older rows have none). Outcome columns not used.

- **Gold: size against depth is NOT the cause.** 100 of 111 gold orders were under 5% of the depth at the touch, and 38% of those still got no fill. Gold depth is in the thousands (mean about 2,100 contracts), orders about 9.
- **Gold: lower price, more no-fills.** No fill share by the price the bot saw: 88c to 91c 50% (38 orders), 91c to 94c 35% (34), 94c to 97c 29% (37). Fits ask creep: a cheaper favourite is still moving up and leaves the limit behind; a 95c favourite is already priced.
- **Dogecoin: depth matters for large shares.** Order share of depth under 30%: 20% to 28% no fill (91 orders); 30% or more: 47% to 66% (25 orders). Depth is thin (mean about 100 contracts at the touch against orders of 3 to 5), so the 5 contract size and any ladder step above 5 are the places a no-fill will rise.
- **No partial fills at all:** 0 partial fills of 148 fills. Orders are all-or-nothing in practice, so a no-fill is a whole order lost, never half.
- **Prediction for the R2 registered proposal (limit +1c):** unchanged, FALSIFIED on dollars. The gold pattern (cheap, still rising favourites fail to fill) is exactly the set of orders that a +1c limit would fill, and no-fills have scored worse than fills (LIVE3, -0.82c vs +0.92c). For Dogecoin, depth is the other lever: ordering fewer contracts when share of depth would exceed 30% raises fills without raising price; that is a sizing rule and is not proposed because it cuts size.
- **Next for R2:** the simulation on R6 (fill if the ask 1 to 2 s later is within limit +1c) once R6 holds enough windows; needs V2's R6 clock rule. Nothing to the main session: no threshold.

**2026-10-30 2:15 PM CT, R4 first read (size effects, settled orders since Oct 20, information only, 0 tries). No flag.**

| Market | Contracts | Settled | Lost | Net | Cents per contract |
|---|---|---|---|---|---|
| Gold | 1 to 5 | 30 | 3 | -$2.17 | -1.66 |
| Gold | 6 to 10 | 35 | 1 | +$5.65 | +1.93 |
| Gold | 11 to 15 | 47 | 4 | -$0.99 | -0.17 |
| Gold | 16 to 20 | 6 | 0 | +$8.35 | +7.88 |
| Gold | 21 to 30 | 3 | 0 | +$4.62 | +6.08 |
| Dogecoin | 1 to 5 | 142 | 7 | +$7.38 | +1.85 |

Reading: no size bucket shows a slippage or loss pattern that is more than noise at these counts (gold 16+ has only 9 orders and no losses; the 1 to 5 bucket is mostly older, smaller orders at different prices). The report has no fill price for held orders, so slippage by size still comes only from V2's GOLDSLIP (+1.82c at 16 to 20 contracts on 6 orders). The R4 flag needs 20 orders at 16+ contracts. Dogecoin has no order above 5 contracts yet, so the ladder change is not in the record. Re-run nightly.

**2026-10-30 2:05 PM CT, R1 and R3 counts received from V2 (counts only, candle replay Aug 5 to Oct 30, about 87 days). My reading, no outcomes seen. 0 tries.**

Candidate entries a week at the 6 minute look (full weeks; V2 file `workers/REFINE_COUNTS_R1_R3.md` and CSVs on `claude/epic-ptolemy-0amjd9`). Last four full weeks in brackets:

| Market | 86c to <88c | 88c to 97c (live band) | >97c to 98c |
|---|---|---|---|
| Gold | 18.4 [15, 23, 18, 15] | 143 [139, 134, 122, 132] | 16.9 [14, 16, 17, 18] |
| Dogecoin | 27.6 [26, 27, 28, 32] | 207.7 [199, 204, 177, 170] | 38.2 [46, 49, 25, 29] |

- **R1 relative size:** the 86c to 88c cell is +13% of the live band on both markets over the full span (gold 18.4 / 143, Dogecoin 27.6 / 208) and about +11% (gold) and +16% (Dogecoin) in the last four weeks. The 97c to 98c cell is +12% (gold) and +18% (Dogecoin) over the full span. This is close to the R6 count (+17% gold, +8% Dogecoin) and replaces it, since it is 87 days and not 43 windows.
- **Translated to live fills:** live fills are about 40% to 45% of the candle ceiling (gold 61 a week live vs 125 to 150 candidates, Dogecoin 71 vs 170 to 200: no fills, the window cap, one-order-per-window, quiet hours). So the 86c to 88c cell adds about +7 gold and +11 Dogecoin fills a week, and 97c to 98c about +7 and +11; both together about +36 a week on about 132 (+27%). Estimate only; V2 warns the counts are a ceiling.
- **Dogecoin is shrinking:** its live band entries fell from about 215 to 170 a week in the last two weeks, gold from about 150 to about 125 in October. Frequency is falling on its own, which strengthens the owner's frequency concern; worth knowing before any band change.
- **R3, Dogecoin by hour:** 2,548 band entries over 87 days, roughly flat by hour (81 to 129). The 20:00 to 23:59 CT block holds 468 of them, 18.4%, so about 32 candidate entries a week and about 13 live fills. That is the frequency the Dogecoin night block costs (about 18% of its entries). It is above one sixth (16.7%) because the block hours are slightly busier than the average.
- **Next for R1 and R3:** the scored tests need fresh days after Oct 30 18:56Z, recorded by R6 (until Nov 13) and scored by V2's forward ledger or by me on the report. I will register the exact scorer for R1 cells and R3 block against the live-rule candle replay with V2, forward days only. Parity caveat: Dogecoin's band parity with live was 26 mismatches in 556 windows (4.7%).

**2026-10-30 2:05 PM CT, queue item 7 (OICORE and L1 in the same window), first count: 0 of 2.** Both OICORE orders (Oct 30 8:45 and 10:45 AM CT windows) had no L1 fill in the same 15 minute window, so no shared loss yet. Sample is 2; the count will be re-run nightly from `slotOrders` against `orders` and reported when it reaches 20 slot orders. V2 will push counts-only R1 and R3 outputs to `claude/epic-ptolemy-0amjd9`; I read them when they land. Items 5 and 6 (OICORE entry timing, fill and slippage) need Bitcoin open interest candles or an order export with `avgFill`; the report's slot orders carry no `avgFill`, so they wait for either.

**2026-10-30 2:00 PM CT, report extension is already live; first OICORE and size read. No threshold hit.** The nightly report now carries `secondSlot`, `allStrategies` and `slotOrders` (the extension is deployed, earlier than the main session's last note). OICORE: 2 fills, both lost (Oct 30 7:42 AM CT, 5 contracts, -$0.32; Oct 30 9:42 AM CT, 10 contracts, -$0.75), net -$1.07. Expected win rate is about 28% (price 5c to 50c), so two losses in a row is about a 52% chance by luck; the streak kill is 18, the first read is Nov 13. Nothing to act on. Dogecoin counts above 5: none since Oct 28 (the 12 contract order flagged earlier). The Dogecoin ladder change has not shown in the orders yet. L1 plus slot, last 48 hours: 56 settled, 5 lost, net +$16.01, profit factor 2.0 (all strategies, paused markets quiet).

**2026-10-30 2:00 PM CT, REGISTRATIONS R1 to R4 (owner direction Oct 30 "more research going in both chats"). Written BEFORE any outcome, candle or result row is opened for these tests. Nothing run yet.**

What I read to write them: the README and V2 status text, `workers/DEPTH1_REGISTRATION.md`, `workers/DOGEFILL.md`, my own earlier counts. I have opened no outcome column of any dataset for these tests. Running count N: 728,648 (V2 after DEPTH1); these add **4 tries** (R1 two cells counted as 2 = 2, R2 1, R3 1, R4 0) so N becomes **728,652** at registration. Common rules: gold and Dogecoin only; no promote verb; no trading code; one read per registration; outcomes of the 69 day history may be used for COUNTS only, never as the verdict for a band variant (README P1), so every band verdict comes from fresh days after this commit's timestamp. Frequency is a hard requirement: every proposal states fills per week before and after, and anything that cuts fills says so.

**Data I do not have (request to the main session):** the 69 day candle history (`kalshi-scalper/data`, not committed) and `fresh.sqlite`, `workers/` outputs. Without them R1 counts and R3 can only run on R6 (a day and a half) and the live report. Please ask the research session to (a) give me read access to those files in this container (a branch with the count outputs would do, not the raw data), or (b) run the count scripts below for me and push the counts-only output.

**R1: edges of the band, 86c to 88c and 97c upper edge (gold and Dogecoin).**
- Hypothesis: more entries at the band edges without worse losers. Counterparty: none named (weakest part).
- Step 1, counts only (outcome columns hidden): windows per week at the 6 minute look with the fresh side price in 86 to <88c and in >97 to 98c, per market, on the 69 days; compared to the in-band count. 0 tries (counts).
- Step 2, registered test on fresh days only (close after this commit): net per contract after fee of the added cell and of 97c to 98c, 1 contract, held to settlement, taker at the ask. 2 tries (86 to 88, 97 to 98).
- Prediction: 86 to 88c net per contract under 0c (FALSIFIED); 97 to 98c under 0c (break-even needs a win rate above 98c plus fee; the 95 to 97c cell is already +0.17c net). Written before data.
- Kill: 150 fresh settled entries per cell, net per contract under +0.5c or loss rate above price paid plus fee: stop, no extension. Pass bar: the research bar (profit factor 1.5 in each of three windows after deflation); not expected to be reachable in two weeks of fresh days (about 25 entries a week per cell), so the likely verdict is NOT_ENOUGH_DATA.
- Fills per week: from the R6 count, 86 to 88c adds about +16 a week across both markets (range 0 to 40%); 97 to 98c to be counted.

**R2: why 28% to 35% of attempts get no fill, and a proposal that raises fills without worse losers.**
- Known: no-fills scored -0.82c a contract against fills +0.92c (LIVE3, held to settlement at the order limit), so a fill that raises fill rate by chasing price tends to ADD LOSERS (these are windows where the ask moved up). Ask creep before the order (README, 1.2 s tick delay) is the leading explanation. DEPTH1/DOGEFILL: size at the touch was above order size in the checked cases.
- Descriptive step (0 tries): from the nightly report and the order export (`depthAtLimit`, `shareOfDepth`, `entryLead`), split no-fills by order size, by gap between the attempt time and the touch read, by market. Needs a fresh Copy all orders export (the report has no depth fields). Information only.
- Registered proposal (1 try, fresh days, scored against plain L1 on the same windows): the order limit is the quoted ask PLUS 1c (still capped at 97c, same band). Prediction: fill rate rises by 8 to 15 points, but net per contract on the extra fills is under 0c, so the whole change is FALSIFIED on profit factor; the owner's frequency requirement is met by the extra fills, not the dollars. Kill: any 100 fresh extra fills with net per contract under +0.5c, or total loss rate above 8%.
- This is the same ground as V2's L1Q1 (resting entry); mine is the opposite direction (pay more, fill more). It needs a live probe to test properly (simulating it from the R6 book is possible: fill if the ask 1 to 2 s later is within limit +1c). I propose the R6 simulation first, no live order; brief for any live probe comes separately.

**R3: Dogecoin by hour (the 8 PM to midnight CT block applies to Dogecoin by consistency, unmeasured).**
- Hypothesis: Dogecoin's 20:00 to 23:59 CT block is no worse than the rest, i.e. the block is not worth removing. Prediction: block net per entry about equal to the rest (difference under 1c); the permutation p of the block among 24 hourly blocks is above 0.3 (gold's own p was 0.025 alone and 0.12 to 0.30 counting every try). Counterparty: none named.
- Universe: Dogecoin L1 entries at the 6 minute look, fixed now to the same four hour block as gold (not tuned on returns). Count first (0 tries): entries per hour on the 69 days and the live record. Then one test (1 try): block versus rest, day-clustered z, on fresh days after this commit. 
- Kill: if the block is below the rest by z 1.5 or more on at least 100 fresh block entries, propose removing Dogecoin's block (owner decision); if z under 0, the block cost nothing, no action either way beyond note. Frequency note: the block removes roughly one sixth of Dogecoin hours; I will give Dogecoin orders per week in the block (from the live record: about 12 a week if evenly spread, a guess) in the count.

**R4: size effects at gold's ladder sizes (information only, 0 tries).** Slippage and loss per contract by order size for gold and Dogecoin from the nightly report's new `allStrategies` and `secondSlot` sections once deployed (needs both deploys). Buckets 1 to 10, 11 to 20, 21 to 30, 31 or more. Reported nightly. Flags: V2's GOLDSLIP rule (20 orders at 16+ contracts, over 1.0c); any Dogecoin order above 5 contracts. Wait for the deploy notice.

**Next:** (1) message main for the data request; (2) once I have counts-only data, write the count outputs here; (3) set the freeze timestamp (this commit) as the start of "fresh days"; (4) nightly report read; (5) R4 after the deploy.

**2026-10-30 2:20 PM CT, Brief 1 count-only step done: the 86c to 88c cell adds about 8% (Dogecoin) to 17% (gold) more entries, from a very small R6 sample. No outcome column was read (book prices only; trades and results files untouched). 0 tries.**

Method: for each gold and Dogecoin 15 minute window in R6 (`book15r6`, Oct 29 22:03Z to Oct 30 about 12:43Z files on `quote-data`), take the book poll nearest 360 seconds before the close (within 30 seconds); a side's ask is 1 minus the other side's best bid; a window counts as L1 (88c to 97c inclusive, either side) or as the added cell (86c up to but not including 88c, neither side in 88c to 97c).

| Market | Windows with a 6 minute poll | L1 band (88c to 97c) | Added by 86c to 88c | Increase |
|---|---|---|---|---|
| Gold | 41 | 12 | 2 | +17% |
| Dogecoin | 45 | 12 | 1 | +8% |

Applied to the live fill rate (about 61 gold and 71 Dogecoin fills a week over Oct 16 to 30): roughly +10 gold and +6 Dogecoin fills a week, about +16 a week in total, of about 132. That range is wide: the counts are 1 and 2 added windows, so the true increase could be anywhere from near 0% to 40%. Also not allowed for: the live no-fill share (35% gold, 28% Dogecoin) would apply to the added orders too, and the live rule uses the fresh quote at the bot's look, not the poll nearest 360 seconds.

Not done: the 69 day candle history is not in this container (`kalshi-scalper/data` is not committed), so I could not give the longer count. If the owner wants it, the research session or main session can run the same count there; it is still a count with outcomes hidden. Read plainly: even on the upper figure, the cell adds under 20 fills a week and the evidence nearest to it (88c to 90c net -0.36c) says those fills lose cents, so the case for widening on frequency alone is weak.

**2026-10-30 2:05 PM CT, Brief 3 CLOSED as already live; Brief 1 on hold.** Main session answer from code and README: L1 buys whichever side's fresh price is 88c to 97c inclusive, so either side already qualifies and there is nothing to add. 0 tries spent. Brief 1's count-only step waits for the owner. OICORE: an export (Copy all orders) from the owner is the way to watch it until a reviewed report extension exists.

**2026-10-30 2:00 PM CT, four band and frequency briefs for the owner to approve (owner request via the main session). Nothing has been run on any data.**

Baseline I am measuring against (live, Oct 16 to Oct 30, two weeks, from the nightly report): gold 122 fills, about 61 a week (35% of attempts got no fill); Dogecoin 143 fills, about 71 a week (28% no fill). So L1 today is about 130 fills a week on the two markets, 6 minute entry only. Net per contract live: gold +2.34c, Dogecoin +2.09c (30 days).

Fixed rules for all four: gold and Dogecoin only, both with identical rules; public recorders only (R6 15 minute books from Oct 29, and the quote recorder on `quote-data`); only markets that close AFTER the freeze timestamp I write into the registration commit before any row is read; the 69 days of history cannot count toward a band variant (README P1), so history is used only for the count of entries, never for the verdict. Deflation: README N is about 627,838 (V2, Oct 30); these four add 4 tries, plus 1 for the 86c to 88c sub-split if it is read as two cells. Bar is the research bar already in CLAUDE.md: profit factor 1.5 or better after fees in each of three windows, deflated for N; I do not expect any of these to reach it in the first read, and they are not promotable on that alone (nothing here has a promote verb). Information needed from the owner for a live probe is a separate, later decision.

**Brief 1: lower edge 88c to 86c (add the 86c to 88c cell).**
- Hypothesis: the 86c to 88c cell is a continuation of the band's cheap end and adds fills.
- Counterparty: none named. This is the weakest part of the case.
- Prediction (written before any read): the added cell nets under 0c a contract after fees, FALSIFIED. Reason: the known history already has 88c to 90c at gross +0.35c and net -0.36c (n 518), and the trend into cheaper prices is down, with break-even needing a win rate above the price paid plus fee.
- Kill: after 150 fresh settled entries in 86c to 88c, net per contract under +0.5c or a loss rate above (price paid + fee); stop at 150, no extension.
- Orders per week: unknown until counted. Cost-free step I propose first, with owner approval: COUNT entries with outcomes hidden from the first look on the 69 day candles and the R6 files (a count, not a result). Expect roughly 15% to 25% more entries (my guess from the 88c to 90c cell being the thinnest-priced cell; stated as a guess, to be replaced by the count).
- Plain statement: widening adds orders but the nearest evidence says the added orders lose. Frequency is bought with expected dollars here.

**Brief 2: a second look at 8 or 10 minutes for entries missed at 6.**
- Hypothesis: a market inside the band at 8 or 10 minutes left that has left the band by 6 minutes (or never fills) can be taken earlier, adding fills without changing the rule.
- Counterparty: none named. Earlier evidence is mixed: natural gas +3.19c at 10 minutes vs +0.52c at 6, XRP +2.91c vs +1.47c, but pooled over 18 series 10 minutes missed its bar (z 1.71), and XRP's live 10 minute entries lost 12 of 75 (-$7.20). Gold at the 10 minute look was 0.89 profit factor (GOLD1D).
- Prediction: gold FALSIFIED (net per contract under 0 at 10 minutes, consistent with GOLD1D); Dogecoin not-passing (below the 6 minute look, PF within 0.1 of 1.0). I expect the cleanest result to be "adds fills, loses cents".
- Kill: any look must show net per contract at least +0.5c on 100 fresh entries, and the loss rate must stay under 8%.
- Orders per week: from the TWOSTAGE log already on every live order (`ask10`, `inBand10`, `ask8`, `inBand8`, `twoStageLeft`), the count of markets in band at 8 or 10 minutes but with no L1 fill can be read from the order export with no new live data. Needs the owner to paste a fresh Copy all orders export; not available to me.
- Plain statement: V2 owns the earlier-entry family (Oct 28 closure of L1 filter, exit and sizing tests); this brief stays only because the owner asked, and I lean toward not running it.

**Brief 3: either side vs favourite-only.**
- Hypothesis: L1 already takes whichever side is in the band, so this is about the market where both sides are out of band at the same time. I could not find a rule to extend, so this is a clarification question for the owner and the main session: is the live rule "the side whose price is in the 88c to 97c band" (so both sides is impossible, one side is always at most 12c) or "the favourite only"? If the former, there is nothing to add and this brief is withdrawn. I am not spending a try on it until that is answered.
- Orders per week: zero change under either reading unless the band is also widened.

**Brief 4: a filter that adds orders without adding losers.**
- I could not name one. Every filter tested so far REMOVES entries (REGIME1, NEWH5, MKTTIME1, the smooth climb gate) and the only information-only effect found is that entries with a spread of 2c or more do worse (removed entries 0.798 / 0.753 / 0.716 in REGIME1), which cuts count. The honest answer to "adds orders without adding losers" is that fills come from the other end: the 35% (gold) and 28% (Dogecoin) of attempts that got no fill.
- Alternative I propose instead (counts as 1 try): L1Q1 and MAKER5 are already registered by V2 on R6 (resting entry instead of paying the ask, read from Nov 6). If resting entries raise the fill rate without worse losers, that is the one live frequency lever with a mechanism (the no-fill share is order count thrown away). I recommend waiting for L1Q1 rather than registering a duplicate.
- Kill and prediction belong to L1Q1's registration; I will quote its read when it runs.

**My recommendation:** approve only the count-only step of Brief 1 (no outcomes, 0 tries) and the question in Brief 3; skip Brief 2 and Brief 4 as written because V2's L1Q1/MAKER5 already cover the only frequency lever with a mechanism. If the owner values frequency above expected cents, Brief 1 is the only one that adds orders, and its predicted result is negative, so it would be a deliberate cost.

**2026-10-30 1:45 PM CT, first read of the live record (nightly report, 30 days, 855 settled). No kill rule has triggered. No flag for the main session.**

Live, per market (dollars after fees, settled only):

| Market | Window | Settled | Lost | Loss rate | Net | PF | Cents per contract |
|---|---|---|---|---|---|---|---|
| Gold | 30 d | 215 | 10 | 4.7% | +$42.48 | 1.66 | +2.34 |
| Gold | last 100 | 100 | 5 | 5.0% | +$20.24 | 1.45 | +1.83 |
| Dogecoin | 30 d | 143 | 7 | 4.9% | +$8.61 | 1.53 | +2.09 |
| Dogecoin | last 100 | 100 | 4 | 4.0% | +$9.63 | 1.94 | +2.93 |

All markets, 7 days: 362 settled, 30 lost, net +$8.25, PF 1.10 (paused XRP, AUD/USD, USD/CAD and natural gas are still inside it and net -$8.04 between them; gold and Dogecoin together +$16.07).

Rule checks:
- **Dogecoin at 5 contracts** (since the 21:05Z Oct 29 deploy): 12 settled at 5 contracts, 1 lost, net -$0.84 (-1.5c a contract). The kill rule (last 100 at 5 lose more than 8%, or net under +0.5c) cannot be read until 100 exist and the review is at 250 settled; nothing to report. Fill rate: 9 of 21 attempts no fill (43%) against the 60% over 20 flag in DOGEFILL, so no flag, but it is above the 26% before the deploy and worth watching.
- **Dogecoin on gold's ladder (Oct 30 change):** the newest Dogecoin order in the report is still 5 contracts, so the ladder is not visible in the record yet (or not deployed yet). Check the next report for any Dogecoin count above 5; the size lock allows up to 50.
- **Gold quiet hours (20:00 to 23:59 CT):** the last gold order in that block is Oct 29 02:54Z (Oct 28 9:54 PM CT), before the Oct 29 live date. No gold order in the block since. Interim review is still MKTTIME1-F (V2), about Nov 24 to 26. Nothing to do.
- **Oversize:** none since Oct 29 16:00 CT. (The 374 listed over 30 days are old Bitcoin, XRP and probe orders measured against today's limits.)
- **Paused markets:** no new fills on Bitcoin, Ethereum, XRP or the probes since Oct 30 00:00 UTC.

Early signs, not findings (small counts):
- Gold since the Oct 29 deposit marker: 11 settled, 1 lost, net -$0.37. Gold at 11 to 15 contracts: 9 settled, 1 lost, -$3.42 (-2.9c a contract); at 21 to 28 contracts: 2 settled, both won, +$3.05. V2's GOLDSLIP (+1.82c slippage at 16 to 20 contracts, 6 orders) is the better watch for size effects; I add nothing until that has 20 orders.
- Entry lead: 10 minute entries (XRP, now paused) were the loss: 75 settled, 12 lost, -$7.20, PF 0.55. 6 minute entries: 286 settled, 18 lost, +$14.22, PF 1.22.

**Not done yet:** OICORE (second slot) is not in the nightly report (it only reads the L1 collection `kalshiLiveOrders`). The forward read is Nov 13, and I have no read path for `kalshiSlotOrders` from this container. Needs a decision from the owner or main session: either a report extension (a reviewed code change, not mine to make) or the Bot page export of the slot orders pasted in.

**Next:** nightly read of the report each pass; check Dogecoin counts above 5 and the first Dogecoin loss at the new size; first OICORE fills when the owner shares an export. No brief drafted: no refinement idea has a hypothesis that is not already a V2 test (L1 filter, exit and sizing tests are closed by the Oct 28 instruction; STRUCT1 and EXIT1 already say the 25c exit is neutral to slightly helpful).
