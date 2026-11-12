# Desk A verification, Nov 12, 2026: MMSIM1 development PF and CFRTI1-BTC

Asked by Main: re-derive both numbers from the raw held data without reading V2's code first; development data only; zero Kalshi calls; neither held-out read. Done that way: I wrote both scripts from the protocol TEXT (`workers/desk_a_verify/mmsim_rederive.py`, `cfrti_rederive.py`), ran them, and only then opened V2's `mmsim1.py` and `cfrti1.py` to explain the differences. Held-out rows were dropped at load in both scripts (MMSIM1: rows of events closing at or after 2026-11-07T15:00Z; CFRTI1: only run folders dated Nov 4 or earlier were copied, and result rows closing on Nov 5 or later were dropped).

## 1. MMSIM1: MATCH, with one correction to the figure as quoted and one integrity risk

**The number.** PF 1.41 at maker fee 0 belongs to the 171 development events (168 quotable), not to 176. I reproduce it exactly:

| | V2 (protocol, Amendment 1) | Desk A, same reading |
|---|---|---|
| events (quotable) | 171 (168) | 171 (168) |
| strikes quoted | 1,113 | 1,113 |
| fills YES / NO | 400 / 391 | 400 / 391 |
| pairs / singles | 174 / 443 | 174 / 443 |
| PF, maker 0 | 1.41 | 1.407 |
| PF, maker 0.0175 | 1.28 | 1.285 |
| mean per event, maker 0 / 0.0175 | +5.07c / +3.71c | +5.07c / +3.71c |

**Two readings the protocol text does not state, which the code makes and which I had to find to match exactly.** Both make the result slightly LOWER than a literal reading of the text, so neither flatters it:
- a strike is quoted only if BOTH sides show a best bid at the first snapshot in the window (63 strikes dropped; the literal reading gives 1,176 strikes and PF 1.435);
- the flatten uses the last snapshot at or before T minus 15 minutes, not the first after (literal first-after gives 1.421).
Also: 33 of the 443 singles have no bid on their side at the flatten and are booked as sold at zero (conservative), and fills use the trade's own time rather than the 30 second poll time (3 fills of difference).

**No look-ahead found.** Orders are posted from the first in-window snapshot, fills count only trades at or after the post and up to T minus 15, the flatten price is from a snapshot at or before T minus 15, a pair pays exactly 1.

**One assumption that matters (disclosed in the protocol as "unrounded", but its size was not stated).** The simulation is one contract a side with the fee unrounded. A real one-contract flatten sale pays the fee rounded up to the cent. With that rounding the same development run reads **PF 1.26 at maker 0 and 1.15 at the 0.0175 bound** (net $5.84 instead of $8.51). At 10 contracts a side, where rounding is negligible, requiring the whole 10 to trade through the queue gives PF 1.48 and 1.35; at 100 a side 1.43 and 1.30 (but then the flatten may exceed the displayed bid, which is not modelled). So 1.41 is a fair figure for a 10-lot and an optimistic one for a 1-lot. The held-out read should report both the unrounded and the cent-rounded figure.

**The "176 events, PF 1.45" figure (DOCS_CARDS_RESULT.md, the REBATE1 rerun) I did NOT re-derive, on purpose.** It says "books before 2026-11-08", which is later than the registered development cutoff of 2026-11-07T15:00Z, so it scored 5 events that Amendment 1 defines as HELD-OUT. Re-deriving it would have meant reading them. Those 5 events have been seen once already (their net was positive, since PF rose from 1.41 to 1.45).

**Integrity risk before the held-out read.** `mmsim1.py` computes its cutoff as two thirds of whatever events are on the branch when it runs (`cut = ev[2 * len(ev) // 3]`). The branch has grown since Nov 11, so running that script again as it stands would move the cutoff later and score held-out events as "development". MMSIM2 and MMPOWER1 say they pinned the 171 events; `mmsim1.py` itself does not. Recommended before Nov 24: (1) hard-code the cutoff 2026-11-07T15:00:00Z in the script that will do the read; (2) disclose in the read that the 5 events closing Nov 7 15:00Z to 19:00Z were already scored once, and report the held-out result with and without them; (3) nobody runs the unpinned script in the meantime.

**By day** (UTC date of the close, my reproduction): 8 of 10 days positive; the protocol says 7 of 10, which is probably a different day boundary. Not a mismatch that changes anything.

## 2. CFRTI1-BTC: MATCH on the Bitcoin cell; the lead is as fragile as V2 says

**V2's own script, run on the data I copied (split pinned at Nov 5), prints its published numbers exactly:** 843 cheap rows, 211 edge rows, pooled PF 1.14; Bitcoin n 36, PF 2.54, mean +15.65c, win 33.3%.

**My independent version, written from the text, across the eight ways the text can be read** (venue trade time from the exchange stamp or the receive stamp; standard deviation with n or n minus 1; decision time at the quote or at exactly T minus 120 s): Bitcoin **n 35 to 40, PF 2.18 to 2.51, mean +12.3c to +15.6c, win 30% to 33%**. One reading gives n 36, PF 2.513, mean +15.55c, win 33.3%. So the Bitcoin cell is real in the data and does not depend on one implementation choice. Pooled over the five series my versions give PF 1.14 to 1.19 on 240 to 255 rows against V2's 1.14 on 211.

**Why the pooled counts differ (mine 1,032 cheap rows, V2's 843).** Four choices in V2's code that the protocol text does not state. None is a look-ahead:
- a window needs at least 30 ten-second index changes, which drops thin windows, mostly Dogecoin (V2 keeps 43 Dogecoin rows, I keep 189);
- the spread of 0.03 or less is applied to the baseline sample too;
- quotes, trades and results are joined inside one recorder run folder only, so a window at the start of a run with too little spot history is dropped;
- the "day" is the run folder's date, not the close date, so a run started late on Nov 4 puts a few closes of early Nov 5 UTC in development. The held-out plan uses the same folder rule, so there is no overlap, but the write-up's "days before 2026-11-05" is by folder, not by clock.

**A trap worth knowing.** The three venues write their trade time in three formats (ISO text, epoch seconds, epoch microseconds). My first pass silently dropped two venues and produced n 55 to 60 for Bitcoin. V2's code avoids it by using the receive time. Anyone re-implementing this for the held-out read should use the receive time or parse all three.

**No look-ahead found.** The index and the volatility use trades received at or before T minus 120 s; the quote is the last one sent at or before T minus 120 s; the fee is as registered.

**What the number does and does not say.** 36 trades, 12 wins, picked as the best of five series after the split was seen (V2 says this). Under the cent-rounded one-contract fee it is slightly lower. The pooled test failed and three of the other four series are under 1.0. The held-out plan (Bitcoin only, 50 rows, read once, about Nov 22) is the right test and nothing here changes it.

## 3. Verdict line

| Number | Verdict | Note |
|---|---|---|
| MMSIM1 development PF 1.41, maker fee 0 | CONFIRMED on 171 events (168 quotable), not 176 | 1.26 with one-contract fee rounding; the 176 event rerun read 5 held-out events; the script's cutoff is not pinned |
| CFRTI1-BTC PF 2.54, n 36 | CONFIRMED | Independent range PF 2.18 to 2.51 on n 35 to 40; no look-ahead; a picked cell of 36 trades |

---

## 4. BASERATES1 executive order counts (V2): MATCH (added Nov 12)

Asked by Main: check V2's GovInfo count claims, in particular "executive orders per week, mean 1.56 since Sep 2025". Two independent checks, zero Kalshi calls.

**Arithmetic, from V2's held list (`workers/baserates1/eo_list.csv`), with my own week counter (Sunday to Saturday):**

| Claim in BASERATES1_TABLES.md | Mine | Verdict |
|---|---|---|
| Since Sep 2025: n 59 weeks, mean 1.56, variance 1.91 | n 59, mean 1.559, variance 1.906, 92 orders | MATCH. The 59 weeks run from the week starting Aug 31, 2025 to the week of Oct 11 to 17, 2026 |
| Trump II: n 90, mean 2.82, variance 8.24 | n 90, mean 2.822, variance 8.238 | MATCH. Starts with the week of Jan 26, 2025 |
| Trump I: n 208, mean 1.01, variance 1.67 | n 208, mean 1.014, variance 1.666 | MATCH |
| "2025 H1": n 31, mean 5.23 | 162 orders over the 31 weeks Jan 26 to Aug 30, 2025, mean 5.226 | MATCH on the number; the LABEL is wrong. It is Jan 26 to Aug 30, 2025 (everything before the "since Sep 2025" block), not the first half of 2025. A true first half (to the week of Jun 22) is 22 weeks, mean 5.82 |
| Numbers 14147 to 14438, 292 orders, no gaps | 292, no gaps, no duplicates, dates in order | MATCH |

**Source check, my own extraction.** I downloaded GovInfo's Federal Register bulk files for September, October and November 2026 (three zip files, 50 daily issues through the Nov 12 issue; govinfo.gov bulk data, no key, three requests plus two listings) and pulled every Executive Order heading with my own pattern. Result: 17 orders, numbers 14422 to 14438, every number and signing date equal to V2's list; none in the list is missing from the issues and none in the issues is missing from the list.

**Three things a reader of the 1.56 figure should know (none is an error):**
1. **The inauguration week is excluded.** The week of Jan 19 to 25, 2025 had 38 orders and is left out as a partial week. With it, Trump II is mean 3.21 with variance 21.7 instead of 2.82 and 8.24. The table says "complete weeks only" but does not say what that removes.
2. **The list is current, not stale.** The newest order in the list is 14438, signed Oct 22. No later order appears in any issue through Nov 12. Publication has been running 3 to 6 days after signing, so the weeks of Oct 25 to 31 and Nov 1 to 7 look like zero-order weeks (the second with a small chance of a late publication). V2 left out the week of Oct 18 to 24 as "possibly not yet published"; it is complete, with 2 orders.
3. **Extended to today the figure is slightly lower:** adding the weeks of Oct 18 (2 orders), Oct 25 (0) and Nov 1 (0) gives 62 weeks, mean 1.52. The histogram for the 59 weeks starting Sep 7, 2025 is 0 orders in 19 weeks, 1 in 10, 2 in 15, 3 in 11, 4 in 3, 5 in 1.

Not checked: the bills tables (A3, A4), the conditional tables (A2), and the "96 of 96 Kalshi markets reproduced" line, which needs Kalshi results I do not hold.

---

## 5. Gold latch numbers (Refinement): MATCH (added Nov 12)

Asked by Main: re-derive gold's cash figures since the re-arm (2026-11-10 00:00 UTC) per `docs/GOLD_KILL_LATCH.md`. The order documents are not on a branch, so Refinement sent me its 30 order rows from the nightly report pulled at 2026-11-11 23:14 UTC (ticker, side, count, ordered count, price, average fill, average fee, result, stored result, early-sell time and price, order time; no ids). I asked for no per-row cash figures and computed them myself. The order rows themselves are not committed here.

| Figure | Refinement | Desk A | |
|---|---|---|---|
| Settled gold trades since the re-arm | 30 | 30 (25 wins, 5 early sells) | MATCH |
| Cumulative cash net | -$33.96 | -$33.96 | MATCH |
| Cash peak | +$4.07 | +$4.07 (after the 4th trade) | MATCH |
| Drawdown from the peak | $38.03 | $38.03 | MATCH |
| Room to the $58.75 line (rule 1) | | $20.72 | |
| Rule 2 (net under -$20 once 40 trades have settled) | not yet at 40 | 30 of 40 trades; net already -$33.96 | see below |

**How I computed it.** A trade settled at the close: contracts filled x (1 minus price paid minus fee per contract) for a win, minus contracts x (price paid plus fee) for a loss, with the price paid taken from the average fill (which is a YES price, so a NO order pays 1 minus it). All 25 equal the stored result to the cent. An early sell keeps its stored result under the latch rule; I also rebuilt each of the 5 from scratch (contracts x the price sold at, minus the sale fee rounded up to the cent, minus what the contracts cost) and all 5 equal the stored figure to the cent. So the stored results are on the cash basis, at the real sale price, not at the 25c line. The one partial fill (10 of 18 contracts) is booked on 10.

**Independent check of the rows against public data.** For 23 of the 30 markets the 15 minute recorder on `quote-data` holds the public result; every one agrees with the row (0 mismatches). The other 7 fall in recorder gaps and could not be checked.

**What the numbers imply, by arithmetic only (not a forecast):**
- **Rule 2 is close to certain to trip at trade 40.** The net has to be back above -$20 when the 40th trade settles, which needs +$13.96 over the next 10 trades. The average win in these 30 trades is $1.13, so ten wins out of ten at that size add $11.32 and leave the net near -$22.6. Gold avoids rule 2 only with ten straight wins at larger than average size (about $1.40 a win, which means entries nearer 88c to 90c than 95c).
- **Rule 1 has room for about one more early sell.** The five early sells cost $9.12 to $15.01 each. From a drawdown of $38.03, two more of typical size with few wins between them cross $58.75.
- **The early-sell alert condition is already met:** 5 early sells in the last 30 trades against the alert line of 3 in 40.
- Loss rate since the re-arm is 5 in 30 (16.7%) against a break-even near 7.5%. Cash profit factor 0.45.

**Two details for whoever reads the early sells:**
- The sale price was below the bid that triggered the sale in 4 of the 5 (bid 16c sold 10c; 22c sold 15c; 21c sold 10c; 14c sold 6.4c) and above it once (25c sold 34c). On average the sale filled about 4.5c a contract under the trigger bid.
- From the public results, one of the three early sells I could check (the market closing 11:00 ET on Nov 11, booked at -$15.01) would have won if held to the close; the other two would have lost. This is information only: holding gold to settlement is on the declined list.

**Limit of this check.** It verifies the arithmetic and the cash basis on the rows Refinement exported, and 23 of the 30 outcomes against public data. It does not verify that the export contains every gold order (I cannot read the order store), nor whether the latch function is deployed.
