# Conditional probe specs (Head of R&D, Nov 12, 2026)

**State on Nov 12, 17:28Z: ONE conditional spec is left (Spec 2, CFRTI-K). Spec 1 is WITHDRAWN: its read failed.** This file was written as two specs, not three, because a third would have been padding; it is now one, for the same reason.

Every spec here is UNPROVEN and CONDITIONAL. The owner ruled on Nov 12: no pre-evidence orders. So neither spec can be approved as an order today. Each has a gate; the popup is put to the owner only after the gate is met and the Verification Analyst has re-checked the read. A probe is a tiny live test to learn from real fills. No live account figure is in this file. [research]

## Spec 1. SPREADCHEAP (sports spread, cheap side): WITHDRAWN Nov 12

**The one read of W-SPREAD-CELL1 FAILED on both lines on Nov 12 (n 172 and 173, cash PF about 0.55 to 0.64 at +1c against a bar of 1.5; reproduced by the Verification Analyst). Gate item 1 is not met and cannot be met: no popup, no probe, no forward shadow. The text below is kept only as the record of what was specified before the read.**

- **One line:** buy 1 YES contract on a sports spread market priced 5c up to 15c, two days before the game, and hold to settlement.
- **Gate, all of it, before the popup:**
  1. The one read of W-SPREAD-CELL1 returns "cleared its registered bar" on line 1 (n 100 or more, cash PF 1.5 or better at +1c, event-clustered lower bound above 0, z 3.1 or better). LEAD and UNDERPOWERED are not enough.
  2. Line 2 of the same read (the look taken from the time known in advance) is PF 1.3 or better at +1c on 100 or more. Line 1 measured its look from the realised close of each game, which nobody knows two days ahead; line 2 is the rule a live order would actually follow.
  3. The Verification Analyst reproduces the read.
  4. The four uniqueness checks are scored by the Verification Analyst.
  5. An order path exists: the switched-off long-hold path Main is building (owner-approved Nov 12), or the owner places it by hand.
- **Exact rule:** the six sports SPREAD series of W-CAT-SPORTS1 (MLB, NBA, NCAAF, NCAAMB, NFL, NHL). One market per event: the one whose YES mid is nearest 0.50 at the look. Look: expected_expiration_time (else occurrence_datetime) minus 48 hours, read while the market is open; the engine refuses to send if the schedule has moved. Enter only if the YES ask is 0.05 up to but not including 0.15. Limit: the ask seen plus 1c, immediate or cancel, once. Never NO.
- **Size:** 1 contract an event. At most 10 open at once.
- **Worst loss:** about 16c an order (price plus fee). About $1.60 with 10 open.
- **Budget (the popup must name one; no existing budget covers a sports single):** proposed $20 lifetime, $3 a day.
- **Kill:** net under -$6 after 60 settled fills, or 25 losses in a row. The win rate at this price is about 1 in 8, so a streak of 15 is ordinary and must not kill it.
- **Return after a kill:** 14 day cool-off, then a paper record of 100 fills at cash PF 1.3 or better, then the owner's approval.
- **Hold and lock-up:** about 2 days an order. No early exit.
- **Uniqueness, for the analyst to score:** signal is Kalshi price only, on a market type nothing live trades; exit is hold with different entry rules; correlation with OICORE and EVENT830 is expected near zero and is measured at the first read; it buys the cheap side, so it is not a favourite rule; it is not a 15 minute series sweep. Family: calibration cell, cheap side, hold. **Named counterparty: none yet.** That is a gap against the research bar and is said to the owner.
- **Missing today:** the read (jobs SPREADLISTS then SPREADCELL1, about 285 requests, waiting on the owner's merge of PR 804); the order path; the exchange shard sports markets use and money on it (the owner moves it).
- **Earliest first order:** by hand, 1 day after the gate is met; by bot, 1 to 2 days after if the long-hold path is already built and reviewed, otherwise 6 to 8 working days.
- **Honest odds:** 3 to 5 percent that it clears line 1 (Refinement agrees), a little less for both lines. A clear is NOT a pass of the research bar: this is one cell chosen as the best of about 58, and about 320 observations cannot reach z 5.46 whatever they show. After a clear it still has to earn the proven bar (PF 1.3 over 100 fills in 2 of 3 windows) on its own fills.

## Spec 2. CFRTI-K (Bitcoin 15 minute market, cheap side, priced from Kalshi's own Bitcoin perpetual)

- **One line:** 2 minutes before a Bitcoin 15 minute market closes, buy 1 contract of the cheap side (5c to 30c) when a model fed by Kalshi's own Bitcoin perpetual says it is underpriced by 5c or more; hold to settlement.
- **Update, Nov 12 (after this spec was written):** the recorder that supplied Kalshi's quote for the original lead returns a copy refreshed about every 11 seconds, so the original lead's figure was priced at a stale copy and is not tradable. This spec's rule is being re-specified, before any scoring, to take both prices from Kalshi's 1 minute candles; the exact rule below changes accordingly (decision price = the market's own candle ask close at close minus 120 seconds). Odds unchanged: low single digits.
- **Why this form:** the original lead used trades from three spot venues. The owner barred two of them from any live probe on Nov 12 (one needs a signed data licence, one has unread terms). On the third alone the lead shows no evidence (development: n 32, cash PF 1.33). Kalshi's own perpetual needs no outside source. It is a new rule and has NOT been scored.
- **Gate, all of it, before the popup:**
  1. The development read of CFRTI-K (registered at 9bb9c0f2 on claude/idea-desk-a, one specification, cutoff 2026-11-05) is not FALSIFIED. It waits on the pull of the perpetual's 1 minute candles (job PERPBTC1M, 163 requests, waiting on the owner's merge of PR 810).
  2. The held-out read (first allowed Nov 20, one sitting with the other two versions) clears its bar: cash PF 1.3 or better with a positive mean on 50 or more rows.
  3. A re-test on the next 50 rows clears it again (a rule with no edge clears one such read about 24 percent of the time).
  4. The Verification Analyst reproduces each read.
  4b. The gate is judged on the book-replay line at 6 seconds (the same signals priced at the first recorded quote 6 seconds after the decision, a vanished ask is no trade), not on the figure that assumes every signal fills at the ask seen.
  5. Correlation with OICORE under 0.3 on daily cash results. This is at risk: same market, same cheap side, same minutes.
  6. PR 799 merged so the recorder that supplies the rows runs to Dec 15.
  7. A reader for the perpetual reviewed and merged by Main, switched off. The three-venue code on claude/probe-desk is dormant and cannot be activated.
- **Exact rule:** as registered in workers/CFRTI_K_REGISTRATION.md: index = KXBTCPERP reference_price from 1 minute candles (fallback: close), volatility from ten 1 minute changes scaled to the 80 second horizon, decision at close minus 120 seconds, quote spread 3c or less, edge 0.05, no tuning. Limit: the ask seen, immediate or cancel.
- **Size:** 1 contract a window, one position at a time.
- **Worst loss:** about 32c an order.
- **Budget:** proposed $20 lifetime, $3 a day. It would share the Bitcoin market with OICORE: same side only (the direction lock) and it needs its own stop budget first (lifecycle 7g).
- **Kill:** net under -$6 after 40 settled fills, or 18 losses in a row (win rate about 1 in 3 if it is real).
- **Return after a kill:** 14 day cool-off, a paper record at cash PF 1.3 or better on 100 rows, the owner's approval.
- **Hold and lock-up:** 2 minutes.
- **Known weaknesses, stated before any result:** the perpetual's reference price is not the index the market settles on; 1 minute data cannot reproduce the 10 second steps the original lead used; if the perpetual lags spot it adds nothing (measured in the write-up); professional market makers already price this market off spot; a buy limit 1c above the ask misses about a quarter of the time at a 5 second delay (Forensics, on recorded books), and the bot sends several seconds after the minute.
- **Earliest first order:** mid December.
- **Honest odds:** low single digits that it ever reaches a popup.

## Changes to Spec 2 since it was written (Nov 12)

- Forensics' CANDLEVSBOOK1 (confirmed by the Verification Analyst) found the 1 minute candle's bid and ask on the Bitcoin 15 minute series is the book at the minute's end, so the candle-priced rebuild has a current price; its development read waits only on its candle sample. The fill haircut still applies and the gate is still judged on the 6 second line.
- The book-replay convention for the Nov 20 sitting is fixed in writing (walk the levels to the limit for 1 contract, first poll within 4 s after the delay, no poll is no trade).
- The recorder that supplies the held-out rows (R6) stops on Nov 20 as merged; a re-test on a further 50 rows (gate item 3) would need an extension, which is asked of the owner only if the Nov 20 read clears.

## Why there is no Spec 3

- Two-sided market making: closed on Nov 12 (five failures; the last two confirmed or being confirmed by the Verification Analyst).
- ROLLOFF: closed on Nov 12 (the proxy matched the settled value on 0 of 33 days).
- Approval NO side: what is held leans against it; the development pull has not been scored.
- In-game lag: closed Nov 12 (no lag at one minute resolution). Stocks: nine of ten registered tests retired unread or deferred, one held behind a schema pilot. Census cards TIE3 and SOCDERIV: zero-try measurements only, odds 4 and 2 percent by their own author.
- Combo house side: paper first by the owner's rule; one qualifying combo in the first snapshot of 400; first read Nov 26.
- Spot-lead: missed its own bar at n 58; its re-read is judged only on unseen windows; it would also need the owner's written exception to the favourite-and-hold ban.
