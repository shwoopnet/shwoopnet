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
