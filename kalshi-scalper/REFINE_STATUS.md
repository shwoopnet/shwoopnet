# Live Strategy Refinement, status (newest first; times US Central)

Scope: refine what is live (L1 on gold and Dogecoin, the OICORE second slot). New strategy families go to V2 via the main session. Read only: no trading code, no deploy, no merge.

## Entries

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
