# PPW1 registration: three profit-per-win levers on L1 (Strategy Research V2, 2026-10-29, research only; written and pushed before any of them is scored)

Owner's question: "we need more profit per win, not just scaling". Idea list and ledger check: `workers/PPW1_IDEAS.md`. Three tries: CHEAP1-C, CHEAP1-M, SCALEIN1. Running count about 438,905 before, about 438,908 after (other workers may add in parallel).

**Common to all three.** Entries are L1's history as TIMEX1 and MKTTIME1 used them: `scalper.tstop1.load()` (32,499 entries; candle ending exactly 360 s before the close; buy the side whose ask, YES ask or 1 - YES bid, is 0.88 to 0.97; hold to settlement; `r["path"]` holds the minute candles from 300 s to 60 s left). Fill at the closing ask of the signal candle, the same convention as L1's own history (a quote you could hit at the signal candle). Fee 7% x C x p x (1-p) rounded up to the cent per order, at C = 1 and C = 10 (net per contract); stress fees x1.2 (rounded after the multiplier). Windows: `r["win"]`, close-date thirds A, B, C (as TIMEX1). C is the holdout: the script scores A and B (`ab`), the A and B numbers are written to the result file, then `c` is run once. Disclosure: L1's history has been read by many studies, so no third is a truly fresh holdout; a pass earns only a forward read on closes after 2026-10-30 00:00 UTC. Zero-volume: each result is reported twice, with all entries and with entries whose fill candle had volume 0 dropped (volume from the source candle databases). Reported for every rule and window: n, losses and loss rate, profit per win in cents (mean net of the winners), net per contract in cents, PF at C = 1 and C = 10, PF at fees x1.2, day-clustered z (US Central days).

**Bars (unchanged, plus a lever bar so the owner's question gets an answer either way).**
- Strategy bar: PF at least 1.5 in each of A, B, C after fees (at C = 1 and C = 10), positive at fees x1.2, day-clustered z at the deflated bar (about 5.17 for N about 438,908). Not expected to be met by any of the three.
- Lever bar ("better than what live does now"): the rule's PF above the comparison's PF by at least 0.03 in all three thirds at C = 1, its net per unit not lower in any third, and the day-clustered z of the per-unit difference (rule minus comparison, pooled over A to C) at least 2.0. A lever-bar pass is still only a forward read, never a live change.
- Verdict words: FALSIFIED, NOT_YET_FALSIFIED (lever bar met; strategy bar reported separately), NOT_ENOUGH_DATA (fewer than 100 units in any third where the choice differs).

## CHEAP1-C: the cheapest crypto favourite in the window instead of list order (1 try)

- **Group and comparison, chosen on what live trades (cost and rule, not quotes):** `CAPPED_SERIES` Bitcoin, Ethereum, XRP, Dogecoin. Live sends at most one crypto order per window, the first in `L1_SERIES` order (XRP, Bitcoin, Dogecoin, Ethereum). XRP is paused live since 2026-10-28; it stays in so the comparison matches the list rule, and a three-coin read (without XRP) is printed as information only.
- **Rule.** Unit = one 15 minute window (same close time) in which at least one of the four has an L1 entry. LIST buys the first in-band series in list order; CHEAP buys the in-band series with the lowest entry price (ties to list order). Both 1 order, held. Windows where LIST and CHEAP pick the same market are identical; the count of differing windows, and how often the two picks were on the same side, are reported.
- **Counterparty.** If the four coins move together, the cheaper favourite of the same bet is a quoter that priced the same outcome lower than its peers, and the sellers of it lose. Honest alternative: the cheaper one is cheaper because it really is more likely to flip (a smaller distance to its strike), and the larger win is paid for by more losses.
- **Prediction.** Profit per win up about 1c to 2c in the differing windows, loss rate up about 1 point; PF of CHEAP minus LIST within plus or minus 0.05 and of changing sign across thirds; strategy PF about 1.0 to 1.3. FALSIFIED.
- **Kill.** Fails the lever bar in any third, or the z condition.

## CHEAP1-M: silver instead of gold when silver is the cheaper favourite (1 try)

- **Group and comparison.** Gold (KXGOLD15M, the live ladder market) and silver (KXSILVER15M, the same 15 minute window; not traded live). LIST = gold's entry whenever gold has one (live today). CHEAP = in a window where gold has an entry and silver also has one at a LOWER price, silver's entry instead; otherwise gold's. Windows where gold has no entry are not units (live would not trade them).
- **Counterparty.** As CHEAP1-C: the slower or thinner of two books pricing a correlated outcome. Honest alternative: silver is cheaper because it is more volatile relative to its strike.
- **Prediction.** Fewer than 400 differing windows; per win up about 2c; loss rate up; PF difference negative or noise; FALSIFIED.
- **Kill.** As CHEAP1-C.

## SCALEIN1: add one contract on a 3c to 6c dip with 3 minutes or more left (1 try)

- **Universe (chosen on what live trades):** L1's entries on the five live series (gold, Bitcoin, Ethereum, Dogecoin, XRP), 11,424 entries.
- **Rule.** After the entry, look at the candles ending 300, 240 and 180 s before the close, in order. At the FIRST of them whose ask for the side bought (YES ask, or 1 - YES bid for NO) is between entry price - 0.06 and entry price - 0.03 inclusive, buy one more contract at that ask, hold to settlement. At most one add per entry. The owner's form ("and recovers before 3 minutes left") needs a quote from after the add, so it is not used; this is the version a bot could run.
- **Units and comparisons.** (i) The add leg alone as a strategy (its own n, PF, profit per win, loss rate). (ii) Lever bar: the position (entry plus add, net per contract over the contracts bought) against the entry alone, per entry, on all 11,424 entries; the difference comes only from entries that added.
- **Counterparty.** Sellers who push the favourite down on noise in the last minutes, if the dip is noise. Honest alternative: a dip in the last 5 minutes is information (the underlying moved toward the strike), and the add buys the flips: FWD3 found live fills more than 2c below the decision price lost 16% of the time.
- **Prediction.** About 1,400 adds (13% of entries); add leg loss rate 15% to 25% against about 6% for entries, profit per win about 9c to 14c, add PF 0.5 to 0.9; the position PF lower than the entry alone in every third. FALSIFIED.
- **Kill.** Add leg PF under 1.5 in any third fails the strategy bar; the position failing the lever bar in any third is FALSIFIED.

Script: `src/scalper/ppw1.py` (`ab` then `c`, once each). Result: `workers/PPW1_RESULT.md`.
