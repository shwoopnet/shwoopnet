# Refinement pre-registration DRAFTS, all six (2026-11-06)

Status: DRAFTS ONLY for main and the owner to approve. Nothing is scored, built, registered or live. Combined from two worker files (OICORE drafts first, gold drafts second); every figure is quoted from REFINE_STATUS.md except where a draft says counts were added (fill shares, feasibility). None changes an order, a size, a stop or the exit watch. Adopting any of them is a separate reviewed pull request.

====================================================================
# PART 1: OICORE (S-EDGEFILT, S-NEARTHR, S-NOFILLADV)
====================================================================

# W-REGS-OICORE: three pre-registration DRAFTS (nothing scored, nothing sent, nothing live)

Status: drafts for main and the owner to approve. No outcome was computed for any of them. Every number below is quoted from kalshi-scalper/REFINE_STATUS.md (entries Nov 5 to Nov 6, 2026); I did not recompute any of it. Read only worker; no trading code touched.

Common rules for all three
- OICORE live rule as it stands: Bitcoin 15 min, cheaper side priced 0.05 to 0.50 after the bot rounds the price UP to the cent, open interest rise 86,300 or more over the 3 minutes to 180 s before the close, look 180 to 120 s before close, 10 contracts, held to settlement, limit +1c.
- Try count: REFINE_STATUS says about 385 splits in all (Bonferroni about 0.00013, no survivors) as of its line 678 entry. Each draft below adds the tries it names. Main should restate the current total from the file at registration time; I did not recount.
- History alone can never adopt a filter on OICORE: its history file overlaps the tuning data (W-THRESH1 "not out of sample"), the live era is 47 settled fills, 10 wins, +$41.79, PF 2.17 with a 90% bootstrap interval of 1.06 to 3.81 (W-OICOREPF1), and the registered kill/review dates stay as they are (the Nov 13 forward read is THE decision). A filter can therefore only be adopted on fills placed AFTER its cutoff.
- Every draft is a forward SHADOW COUNT on live fills plus candles. None changes an order. None may be wired into the bot; a promotion is a separate reviewed pull request by main and the owner.
- Cutoffs: each starts the moment main registers it (write the UTC timestamp into the file first). Orders before the cutoff never count.

---------------------------------------------------------------------------------------------

## DRAFT 1: S-EDGEFILT, skip OICORE entries whose raw cheaper price is strictly between 0.04 and 0.05

Why this and not the existing tracker: S-EDGEFWD (registered Nov 6, 16:58Z, cutoff 2026-11-06T17:00:00Z) is a READ ("do edge fills net at least 5c per contract less than the others"). It has no action line. This draft names the one action it would justify and the bar for it, so that the read and the decision are fixed together before any forward fill. It uses the SAME fills and the same cutoff as S-EDGEFWD, so it adds no new data wait and no new split to the forward arm; the split is already counted there. It adds 1 try (the filter decision itself).

Exact rule (hypothetical filter, not live): skip when the raw cheaper side price at the c-180 candle is above 0.04 and below 0.05 (raw price strictly between 0.04 and 0.05; exactly 0.05 is NOT in the set; the bot rounds the price up to 0.05, which is what these fills pay). Same definition as w_oicore_edge/e.py and edgefwd_forward.py.

Data read: the report's slotOrders (strategy OICORE, filled, settled) and the public 1 minute candles of KXBTC15M to recompute the raw price at the c-180 candle. No new Kalshi call beyond what the tracker already makes.

Fill share (W-REGS-SHARE, counts only, no outcomes): the filter removes 70 of 548 simulated triggers (13%) and 5 of the 47 live fills (about 11%). Together with Draft 2 it removes 220 of 548 (40%); overlap is 19 in the sim and 1 live.

Count needed: 20 settled edge fills after the cutoff (same as EDGEFWD). Past rate: 5 edge fills in 47 fills in 7 days (about 0.7 a day), so about 4 weeks. Under 20: print counts, NO READ.

Evidence so far (history of the live era only, selftest, not a result): 5 edge fills, 0 wins, -3.42 dollars, -6.84c per contract; the other 42 fills +10.92c per contract. Sim history for the 0.05 to 0.07 bucket (W-OICORE-HIST1, 171 triggers): win 5.3%, break even 6.1%, -0.88c [-3.9, +2.6] (that is a wider bucket, shown for context only).

Yardstick (fixed now): the filter is "worth proposing" only if the edge fills net at least 5c per contract below the other fills AND are negative in both halves (halves split at the median edge fill time) AND the edge fills' own net per contract is below zero. Proposed action if all three hold: ONE brief to the owner to raise OICORE's price floor to the rounded-up 0.06 for fills whose raw price is under 0.05. Otherwise nothing.

Kill line: if at 20 settled edge fills the edge group nets at or above the other fills minus 1c per contract, or a single edge fill wins, the idea is dead; delete the tracker.

Size of the prize (stated so nobody oversells it): an edge fill risks about $0.55 at 10 contracts; at -6.84c per contract that is about -$0.68 a fill, about 0.7 fills a day, so about -$0.5 a day if the selftest rate held. It lifts profit factor mainly by removing a handful of small losses. It is a tidy-up, not a profit source, and the sample is 5 losses.

Why history cannot adopt it: 5 live fills, all from one window; the sim bucket around it is not out of sample and its interval spans zero; and the choice of the 0.04 to 0.05 band came from looking at the data (a post hoc cut).

---------------------------------------------------------------------------------------------

## DRAFT 2: S-NEARTHR, skip OICORE entries whose open interest rise is 86,300 to 100,000 (the near-threshold fills)

Why this and not RISEFWD: RISEFWD (registered Nov 6, 17:00Z) compares fills at 150,000 or more with those from 86,300 to 150,000, and its selftest on the 47 past fills went the OPPOSITE way to the sim (150k+ 16 fills +3.11c vs 86.3k to 150k 31 fills +12.11c). A lower, narrower cut asks a different question, the one the live rule is most exposed to: how many fills sit just over a threshold that W-THRESH1 found has no cliff (net moves 0.44c from 85k, 0.64c from 90k) and whose rise reading depends on candle timing (W-OICORE-0812: 5 of the 9 missing 08 to 12 CT orders had rise under 100k, and 6 of 16 no-order triggers sit within 10 percent above the threshold, lowest +0.3 percent). It adds 1 try for the split plus 0 for the threshold search (100,000 is fixed now, round number, no scan of other values; I will not scan 90k or 110k).

Exact rule (hypothetical filter, not live): group N = OICORE fills with rise at or above 86,300 and under 100,000; group H = fills with rise at or above 100,000. Rise = open interest at the candle ending 180 s before close minus the candle ending 360 s before close, recomputed from the public candle caches by ticker exactly as risefwd_forward.py does (reuse that code, same candle source).

Data read: report slotOrders (OICORE, filled, settled) plus the candle caches; no new endpoint.

Count needed: 30 settled fills in group N after the cutoff, and 30 in group H (both). Fill share (W-REGS-SHARE, counts only, no outcomes): the filter removes 169 of 548 simulated triggers (31%; 170 by w_oicore_rise, a one trigger set difference) and 17 of the 47 live fills by w_oicore_rise (14 by the sim's rise). Together with Draft 1 it removes 220 of 548 (40%) in the sim and 18 to 21 of 47 live (about 40% to 45%); overlap is 19 in the sim and 1 live. Pace: either filter alone cuts the OICORE fill rate by 13% to 31%, both by about 40%, which would push the 100 fill read (about Nov 18) to about Nov 25 to 30. If the group N rate implies more than 8 weeks to 30 fills, drop the draft rather than relax the count.

Yardstick (fixed now): worth proposing only if group N nets at least 5c per contract LESS than group H AND is not above group H in either half AND group N's own net per contract is at or below +1c. Proposed action if all hold: one brief to raise oiRiseMin to 100,000. Otherwise nothing. Prediction written now: the gap is small and unsigned (W-THRESH1 monotonic in history, RISEFWD selftest opposite in live), so the most likely outcome is NO ACTION.

Kill line: if at 30 and 30 group N nets within 2c per contract of group H or higher, delete it. Also dead if the tracker cannot reproduce the 47 past fills' rise from the candles (selftest first, as RISEFWD did).

Cost note: it would remove about a third of fills (31% in the sim) (all but the larger rises), and OICORE is a thin 47-fill record with the kill rules based on fill counts (kills at 40 fills net under -$6, streak 18). Fewer fills means a slower read of the Nov 13 decision. Main should weigh that before approving.

Why history cannot adopt it: the 86,300 threshold itself was tuned on the same history (W-THRESH1: "history overlaps the tuning data"); any higher cut is selection on a smaller tail; and live sign is already opposite to the sim for the nearby 150k cut.

---------------------------------------------------------------------------------------------

## DRAFT 3: S-NOFILLADV, forward measure of no-fill adverse selection (what OICORE's unfilled orders would have made), no filter

Why: it is the one lead with no forward record. W-OICORE-ADVERSE1: unfilled orders won 40.0% (4/10) to 44.4% (4/9 sim) against 21.3% (10/47) to 24.2% for filled, intervals overlap heavily. W-OICORE-SLIP1 saw the same direction in the sim (unfilled 51 to 55 percent win vs filled 14 to 15 percent) but its result swings from +6c to -3c per contract with the pricing assumption, so history cannot settle it. Selection is not randomised and no-fills skew above 0.15 in price. If real, it means the live fills are the worse half of the triggers (live win 21% vs sim 26.5%), and an extra limit slip (the owner already runs +1c, S-LIM1-LIVE reviewed Nov 6: tagged net +17.62, no revert) might buy more of the good half. It adds 2 tries (win-rate gap; hypothetical-net gap).

Exact measurement (no rule, no filter, nothing live): for every OICORE order after the cutoff with count 0 (status no fill), fetch the market result from public data and record whether the order's side would have won; also compute the hypothetical net per contract if it had filled at its own limit price with the fee 0.07p(1-p) rounded up to the cent. Compare with the filled OICORE orders in the same days: win rate and net per contract.

Data read: the report's slotOrders rows with count 0 (ts, ticker, side, price, orderedCount, and kalshiStatus where present, since #712 deployed on Nov 4) plus the public market result (one GET per ticker, once settled; the same pull W-OICORE-ADVERSE1 used). No private endpoint, no order.

Count needed: 40 no-fill orders after the cutoff (past rate about 10 in 7 days, so about 4 weeks) AND at least 40 filled orders in the same days for the comparison. Under 40: print counts, NO READ.

Yardstick (fixed now): adverse selection is called real only if the no-fill group's win rate exceeds the filled group's by at least 15 points AND its hypothetical net per contract exceeds the filled net per contract by at least 3c AND the same sign holds in both halves. The permitted next step is ONLY a brief to the owner proposing a further forward test of limit +2c (its own registration, its own kill line, as S-LIM1-LIVE was); this draft changes nothing. Also record, separately and as information only, the reason class from kalshiStatus on no-fills (ask moved above the limit vs no size), which W-NOFILLINFER1 found cannot otherwise be inferred.

Kill line: if at 40 no-fills the win rate gap is under 8 points or the hypothetical net is at or below the filled net, adverse selection is not supported: close the question and say so in the file.

Honest limits: the hypothetical net assumes a fill at the limit price that never happened (queue and size at the touch are unknown); no-fills are not randomised; and the same finding is reported both as supportive (the 51 to 55 percent proxy) and weak (40 percent, wide interval). It cannot change any order, so even a positive result is a lead for a separate test, not a rule.

Why history cannot adopt it: fills cannot be reconstructed from candle closes (W-OICORE-SLIP1: +6c vs -3c depending on the assumed fill price), the live no-fill set is 10 orders, and the live limit rule changed (+1c) during the window.

---------------------------------------------------------------------------------------------

Not chosen, with the reason: (a) the cheap 0.05 to 0.07 bucket and floor05 are already registered forward (S-BUCKET1 B5 at 40 settled, floor05 at 20, with B5 at 8 fills, 0 wins, -6.10) and overlap Draft 1; (b) a rise threshold scan (90k, 110k, 120k) would multiply tries for no added evidence (W-THRESH1: no cliff, monotonic and selection-driven).
Overlap warnings: Draft 1 and S-BUCKET1/floor05 use some of the same fills (floor05 is a subset of B5, and an edge fill is a 0.05 fill), so they are not independent evidence; say so if both reach a read.


====================================================================
# PART 2: GOLD (S-GFLOOR92, S-GCHEAPCAP, S-GHOLD120)
====================================================================

# W-REGS-GOLD: three pre-registration DRAFTS for gold L1 forward shadows (2026-11-06)

Status: DRAFTS ONLY. Nothing here is scored, built, registered or live. Written from kalshi-scalper/REFINE_STATUS.md entries since Nov 5 (no new data read). Every shadow below reads forward fills only, never changes an order, a size, a stop or the exit watch.

SIZING IS THE OWNER'S DECISION. Draft B touches the idea of size. It is a shadow what-if on recorded fills; it never sends, caps or resizes an order. The size ladder, the 15 contract cap, the 12% stop and the 25c exit stay exactly as they are. Adopting any of these is a separate reviewed pull request the owner asks for.

Already registered, so not repeated here: S-GOLDEXIT180 (sell at close minus 180 s), S-GPB1 (gold fills below 0.90, flag PF under 1.0 at 40), goldfwd (all gold fills since 2026-11-05T16:27:35Z, 100 fills, interval vs break even), C2 (skip negative rise3). Dropped from the four candidates: the fixed 8 or 10 contract what-if (W-CAP15-1) is a pure size comparison that W-GOLDSIZE2 and W-CAP15-1 already answer with arithmetic (smaller size lowers trip odds and lowers gain; this span lost at every size), has no yardstick a forward count can settle, and Draft B covers the part of it that has a stated reason.

Shared rules for all three:
- Cutoff: first gold fill whose order time is after the registration commit time (hard coded in the script, as goldfwd did). Nothing before it counts, including the fills that suggested the idea.
- Data: the nightly report (`?orders=1`), gold only (KXGOLD15M), filled and settled orders, recorded settledPnl and count. After #729 is deployed use avgFill and avgFee when present, and say which was used.
- Unit: cents per contract (settledPnl over count) and loss rate. Break even loss rate = 1 minus price paid, recomputed forward as in goldfwd.
- Interim reads are information only. The only flag is the one written below, printed by wake.sh, sent to main, never acted on by the shadow.
- Fresh gold market regime caveat: the last 8 days are gold's worst stretch (W-GOLDDD1: drawdown $45.74 from a $55.87 peak; 5 of 20 early sells since Nov 5). A forward read inside this stretch is a read of the stretch.

---------------------------------------------------------------------------
## Draft A: S-GFLOOR92 (gold fills priced below 0.92, what a 0.92 floor would have skipped)

Why it is worth registering: W-GOLDBAND1 (287 settled gold, size weighted dollars): loss rate falls with price. Below 0.92: 0.88 to 0.90 had 6 losses in 46 (13.0%, break even 11.7%, -$1.85); 0.90 to 0.92 had 7 in 67 (10.4%, break even 9.2%, -$1.79). Above 0.92: 0.92 to 0.94 5 losses in 62 total with net +$2.25; 0.94 to 0.97 2 in 112, +$14.06. W-GOLD-MARGIN1: live cents per contract -0.43 and -0.24 in the two low buckets, +0.39 and +1.29 above; after the 0.33c cost gap and 0.2c entry slip the 0.90 to 0.92 bucket has +0.04c of history margin left.

The exact rule (shadow only): every forward gold fill with price paid below 0.92 is tagged "would skip". Report two arms: SKIP (price below 0.92) and KEEP (0.92 and above). A price is the order price field (limit) until avgFill is in the report.

Data it reads: forward gold orders, price, count, settledPnl, exit flag.

Count needed: 40 SKIP fills settled (the 0.88 to 0.92 share of gold fills is 113 of 287, about 39%; at gold's 8 to 13 fills a day that is about 3 to 5 SKIP fills a day, so about 8 to 14 days; the S-GPB1 shows the same shape). Read once at 40 SKIP fills and again at 80, nothing between.

Yardstick, fixed before any score: SKIP arm net cents per contract at or below +0.2c AND SKIP arm cents per contract below KEEP arm cents per contract. "Would have helped" means skipping the SKIP arm raises total net AND the SKIP arm's loss rate exceeds its own forward break even rate. Dollar net is shown at recorded counts, but the verdict uses cents per contract so the 15 cap does not decide it.

Kill line (stop tracking, not a bot kill): SKIP arm has 40 fills and cents per contract above +0.8c (the 0.92 to 0.94 live level was +0.39, 0.94 up +1.29; if cheaper fills pay more than 0.8c the floor would only drop earners). Then the idea is closed.

Interim flag: wake.sh prints one line at 40 SKIP fills with the two arms, no other alert.

Tries already spent: the 0.92 cut was chosen after seeing W-GOLDBAND1's four buckets. Honest count: bucket boundaries seen 3 (0.90, 0.92, 0.94), S-GPB1 already spent the 0.90 cut on the same fills (so this draft overlaps it: S-GPB1 below 0.90 is a subset of SKIP; they share the 0.88 to 0.90 fills and must not be counted as two independent confirmations). Also the gold shadows share the same fills with goldfwd, S-GPB1, S-GQH1 and C1 (W-INVENTORY1). Deflation: count N as 3 here and say N at read time; the Bonferroni style bar is p under 0.05 over N, so at least 0.017.

Why history alone cannot adopt it: the bands were drawn after the losses were seen (W45 said so for 0.90), the cells hold 6, 7, 3 and 2 losses, the live cost gap (0.33c per contract) and slippage are not in the history yardstick, history already had the opposite risk (the highest bucket carries the profit, so a floor halves the number of orders and trades the add-on size ladder's profit for fewer chances), and a floor changes how often the bot trades, which interacts with the 5.5% window cap and the 12% stop. Only fills priced after the cutoff, taken at the real counts, can say what the cheap bucket does now.

---------------------------------------------------------------------------
## Draft B: S-GCHEAPCAP (what-if: count capped at 8 contracts on gold fills below 0.92; shadow arithmetic only, sizing is the owner's)

Why it is worth registering: W-GOLD-MARGIN1 and W-GOLDBAND1 show the thin margin is concentrated below 0.92 while the ladder sizes every price alike. W-GOLDSIZE2 and W-CAP15-1 show size moves dollars, not the edge: fixed 8 contracts cut the 30 day trip odds from 6.2% / 4.3% / 2.6% to 0.01% and cut this stretch's loss from -$47.6 to -$32.7, while giving up gain when the span is good (+$26.13 at 8 vs +$49.00 at 15 since Oct 7). W61: 11 to 15 contracts had PF 0.95 against 6 to 10 contracts 2.59, but that is confounded with the period. The question this draft isolates: is the extra size on cheap fills paying for its risk.

The exact rule (arithmetic on recorded fills, nothing sent): for each forward gold fill with price paid below 0.92 and count above 8, compute the what-if net as settledPnl x 8 / count (same cents per contract, smaller count). Fills at 0.92 and above and fills of 8 or fewer are unchanged. The cap of 8 is a single pre-set number, not searched. The shadow is NOT a proposal to change `l1Count`, `L1_ORDER_CEILING` or the ladder.

Data it reads: forward gold orders: count, price, settledPnl, exit flag, plus the day's rolling 24h combined net (to count how many hours the what-if would have stayed above the stop line).

Count needed: 40 forward fills below 0.92 with count above 8 settled (about 3 to 5 SKIP-type fills a day and most are above 8 contracts at the present base, so about 8 to 14 days) AND at least 1 early sell among them, else the read is "no loss seen" and does not count. Reading earlier than 2 early sells is information only.

Yardstick: (a) the what-if loss of the worst day and worst rolling 24h versus the actual; (b) the dollars of gain given up on winning days; (c) a loss-to-gain ratio. Pass would be: what-if cuts the worst rolling 24h loss on these fills by at least a third AND gives up at most 25% of the net gain of the capped fills. Fail: either side. Since dollars scale linearly with count, (a) and (b) will always move in proportion; the shadow's only information is whether the cheap fills' cents per contract is lower than the rest. So the verdict must be written as a cents per contract comparison (cheap bucket vs rest) with the dollar what-if shown beside it, and the owner decides the size.

Kill line: at 40 fills the cheap bucket's cents per contract is at or above the rest's (it is earning at least as much per contract, so the cap would only cut gain) then the idea is closed.

Tries already spent: 1 cap value (8) and 1 price cut (0.92). The 8 comes from the W-CAP15-1 what-if (already shown, not searched here), the 0.92 from Draft A (same price cut, same fills: Draft A and B are the same data and must be read together, not as two tests). Together with A, N tried counts as 3 bucket cuts and 1 cap value, 4.

Why history alone cannot adopt it: gold's size ladder grew over the same days the bad stretch happened, so size is confounded with period (W61 says so); the history has only 18 losses (16 early sells) in 287 orders; the W-CAP15-1 resample has 98 fills and 9 early sells over 8 days and says its negative nets are the span's; and the real cost of a size cap is lost gain when gold is working, which only forward fills can show. SIZING IS THE OWNER'S DECISION: this prints a what-if and stops.

---------------------------------------------------------------------------
## Draft C: S-GHOLD120 (gold: if the 25c trigger fires inside the last 120 seconds, what holding to settlement would have paid)

Why it is worth registering: three reads say the 25c exit is a wash or a small drag: EXIT1 (all markets: hold 0.961 / 0.928 / 0.898 against the live 25c line 0.921 / 0.897 / 0.869 per contract in three windows), W-GOLDEXIT-REAL1 (gold history: hold 1.19c, ideal exit 1.34c, pessimistic exit 1.13c, so about 0.06c under hold), and W-GOLDEXIT-DEPTH1 (15 of 16 live early sells sold below 25c, median 0.18, $15.63 or 11% more loss than a clean 25c sale). S-GOLDEXIT180 already tests a different rule (sell at close minus 180 s regardless); its audit says the edge over hold disappears at about 0.05 of slippage. The gap this draft fills: no forward shadow of the narrowest hold rule, "the exit watch does nothing in the last 2 minutes of a window", which is the situation where a bid is thin, a sale lands far below the line, and little time is left for recovery.

The exact rule (shadow only): for each forward gold order that the live exit watch sells (exit flag true, result exit), find the sale time T. If T is within 120 seconds of the market close, record two outcomes: ACTUAL (settledPnl as recorded) and HOLD (the order held to settlement: count x (1 - price paid) on a win, minus count x price paid on a loss, after the formula fee, using the market result from the report or the settled ticker). Orders sold earlier than 120 seconds before the close are not part of it. No entry, size or other rule changes.

Data it reads: forward gold orders with an exit, exit time, market result. The close time comes from the ticker's Eastern time (`kalshiCloseFromTicker`).

Count needed: 15 forward gold exits inside the last 120 seconds. Feasibility result (W-GHOLD120-FEAS, descriptive count of the condition only, no outcome scored; proxy, not the real sale time): the 16 live gold early sells were matched to public 1 minute candles, and the first minute in the last 7 minutes where the bid side fell to 0.25 or below was taken as the trigger time. 7 of 16 had such a minute; of those 5 fell within the last 120 seconds and all 7 within the last 180. 9 of 16 had no candle in that window (the trigger came earlier or a candle is missing), so the true share inside 120 seconds is between 5 of 16 (31%) and 14 of 16. At 5 of 16 in about 30 days that is about 5 a month, so 15 qualifying exits take about 3 months (about February); not shelved by the rule below (5 is at least 4 of 16), but slow, so main should decide whether the wait is worth it. Honest warning: gold has 16 early sells in 288 orders over 30 days and the share inside the last 2 minutes is not counted in any entry I read. A descriptive count of exit times (how many of the 16 sold in the last 120 seconds) is allowed before registration, since it counts the condition and not the result; if the count is under 4 of 16, the forward pace is under 1 a month, so the read is infeasible before February and the draft should be shelved, not forced into a smaller bar. Read once at 15, nothing between.

Yardstick: HOLD net minus ACTUAL net, in cents per contract, over the qualifying exits; pass is at or above +0.5c per contract (S-GOLDEXIT180's own bar, kept the same so the two are comparable) with HOLD better in at least 10 of 15. Also report the average sale price against the 0.25 line.

Kill line: at 15 qualifying exits HOLD is below ACTUAL in a majority, or net difference below 0. Then the idea is closed.

Tries already spent: 0 for this exact rule, but it is the fourth look at "exit vs hold" on gold (EXIT1, W-GOLDEXIT1, W-GOLDEXIT-REAL1, W-GOLDEXIT180-1 and its PESS correction): all are history on the same fills, so N for deflation is at least 5 on the idea, and the 120 second cut is one number I chose, not searched, from the entry window (the bot enters 180 to 120 s before the close for OICORE; gold's own look is at 6 minutes, so 120 s is arbitrary, state it).

Why history alone cannot adopt it: the candle history has no real exit price (W-GOLDEXIT-REAL1 had to assume one: next minute bid else 0.18), the live exit sells a median 7c below its trigger so the candle model overstates the exit, 72 exits in history and 16 live are too few, and the hold side has a tail (a full loss of up to 0.97 per contract at 15 contracts is about $13.6, vs about $10 to $11 per live early sell). The exit watch is the safety feature (it only ever reduces exposure); a change to it is the owner's and a separate reviewed pull request; this draft changes nothing in it.

---------------------------------------------------------------------------
Next, if the owner approves: write each as a `README.md#S-...` entry with the cutoff, a read only script on the model of `goldfwd_forward.py` with a synthetic test, and one wake.sh section. Nothing in `functions/` or `index.html` is touched by any of them.

## Open discrepancy on S-GHOLD120 (Nov 6 2026)
The feasibility counts above come from the merge worker's reading of res2.json (7 of 16 with a bid at or below 0.25 in a minute candle, 5 within the last 120 s, about 5 a month). The worker that ran the check reported 3 of the 7 in the last 120 s and about 1 a month, and leaned toward shelving. The two use different readings of the same proxy, so the true share is between about 3 and 14 of 16. Treat the feasibility as unsettled and the idea as slow either way; nothing is started.

## Update on S-GHOLD120 feasibility (Nov 6 2026, later)
In gold history 62 of the 72 triggers of the 25c line (86%) fall in the last 120 s, so the live exit rate (16 in about 30 days) gives roughly 10 to 14 qualifying exits a month and 15 are reachable in about 5 to 6 weeks, not months. The shelve lean above is withdrawn; history alone shows no edge (hold +2.4c per contract on 2 wins of 62), so it stays a forward shadow draft only.
