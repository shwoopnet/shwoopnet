# CFRTI-K (registered Nov 12, 2026, BEFORE any Bitcoin perp candle is read or scored)

Kalshi-only rebuild of CFRTI1-BTC. Ordered by the Head of R&D (Nov 12, 2026) after the owner barred Bitstamp and Coinbase from any live probe. Written by Idea Desk A. Research only: no order, no key, zero Kalshi requests from this desk. The perp candles arrive only through Main's pull, and only once the pull route is cleared on Kalshi's terms. Nothing has been scored and no Bitcoin perp candle has been opened to write this.

**Version of / not a version of.** It reuses the entry rule of `workers/CFRTI1_PROTOCOL.md` (V2's branch) but replaces the INPUT (outside spot) with Kalshi's own Bitcoin perpetual. That is a new rule, **one new try**. It is not the PERPBIN1 card (premium and open interest terciles), which stays held.

## 1. The rule (everything as the Kraken-only file, except the index and the volatility)

- Market `KXBTC15M`. Decision time t0 = close minus 120 s. Quote = the last quote row from `quote-data:quotes/` with `t_send_ms` at or before t0, no more than 3 s before it, status active, YES ask above YES bid, spread 0.03 or less (unchanged).
- **Index = the Bitcoin perpetual `KXBTCPERP`, 1 minute candles, field `reference_price`** (the perp's reference price, the mark it is held to the index by; the hourly and 30 second files carry the same field by that name). Only candles whose WHOLE minute lies at or before t0 are used; t0 is a whole minute, so the index is the last full minute before it. **Fixed field fork, decided from the schema alone before any scoring:** if the candle rows carry `reference_price` in at least 95% of minutes, use it; if the candle endpoint carries only OHLC, use the candle close. Written down now so it cannot be chosen after seeing a result. Which was used is printed in the write-up.
- **Volatility (a STATED change, because 1 minute candles cannot give the registered 10 second steps):** the index at t0 and at each of the 10 earlier one-minute marks (the same 10 minute look-back as the registered 60 steps of 10 s); log changes between neighbouring marks where both exist; at least 6 changes or no trade; sample standard deviation (n - 1); **times the square root of 4/3** (the registered scaling to an 80 s horizon is sqrt(8) on a 10 s step, and 80 s is 4/3 of one minute). Minute steps hide intra-minute moves, so this volatility is coarser than the registered one and is expected to read lower at the same moment; it is NOT tuned.
- Model chance of YES = Phi(ln(index at t0 / strike) / that figure). Cheap side: YES if its ask is 0.03 to 0.30, else NO if 1 minus the YES bid is 0.03 to 0.30. Buy it when (model chance of that side minus its ask) is 0.05 or more. One contract, held to settlement, fee 0.07 x p x (1 - p) unrounded, cash. The 0.05 edge, the bands and the 120 s lead are NOT tuned.
- **Known gap, stated before the run:** the perp's reference price tracks an index, not Kalshi's `KXBTC15M` settlement source. A persistent basis between the two shows up as a bias in the strike distance. It is measured, not corrected: the write-up prints the median and the 5th to 95th percentile of (perp reference minus the Kraken last trade) where both exist in the overlap.

## 2. Sample, cutoff, count

- **Development = quote run folders dated before `HELDOUT_FIRST_DAY = "2026-11-05"`**, the constant already pinned for CFRTI1-BTC (so the held-out is the same days). Held-out rows are dropped at load. The perp candles reach back to June, but the Kalshi quote recorder starts in late October, so the trade windows come from the quote folders and the candles only supply the index.
- Reported beside it, descriptive only: how many of the 36 three-venue and 32 Kraken-only development trades the perp rule also takes, how many it adds, and decisions lost for want of a candle.
- **Try count.** One rule, one market, one figure: **N +1**. The Head of R&D's ledger (`DEFLATION_LEDGER.md` on `rnd-queue`, 6f813de3) gives the shared strict N of about 2,113,000 and the research bar z 5.46 (one-sided), and CFRTI-K is already a row in it. This file does not recount it. The Bitcoin cell was picked after a series split in CFRTI1, so the development z counts for nothing; development can only DISQUALIFY.

## 3. Labels (fixed now)

Development: cash PF under 1.0 with n of about 30 or more = **FALSIFIED on development** (the Kalshi-only version is closed); under 1.0 with n under about 30 = "no evidence at n = x", carried to the read; anything else = carried to the held-out read, never a pass. Below about 100 trades nothing is called a FAIL beyond the above.

## 4. Held-out plan

One read, first allowed **2026-11-20**, when at least 50 held-out Bitcoin edge rows exist, in the SAME sitting as the CFRTI1-BTC read, so one held-out set is read once for both rules. The read-once marker is a committed line in this file when it happens (`READ ON <date>, commit <hash>`). Registered bar: cash PF 1.3 or better, a positive mean, n of 50 or more = **cleared its registered bar** (a re-test lead into the lifecycle's shadow gate, never a research-bar pass); cash PF under 1.0 at n of about 30 or more = falsified; anything else = no call at n = x. Any live use is judged on this Kalshi-only figure or the Kraken-only one, never on the three-venue figure. A live probe would read `KXBTCPERP` from Kalshi itself, so this is the only version of the lead whose source is the venue's own.

READ-ONCE MARKER: not yet read. Development not yet scored (waits for Main's candle pull).

## 5. Amendment (Nov 12, 2026, still before any perp candle is read; after the Head of R&D's three points)

- **What it asks, plainly.** The Kraken-only run (n 32, cash PF 1.33, no evidence either way) says the three-venue lead's signal sits mostly in Coinbase trades. CFRTI-K asks whether Kalshi's OWN Bitcoin perpetual carries that same information about where `KXBTC15M` settles. What one minute candles cannot reproduce: the 10 second index steps and the 10 second volatility, and any move inside the last minute before t0 (the last full minute ends at t0 exactly, but its path is invisible). A flat result here would not show that fast spot data is useless; it would show that this coarser, Kalshi-only input is.
- **One specification, no grid.** Price = candle `reference_price` (fallback: close, per the 95% rule in section 1). Volatility window = 10 one-minute steps. Scaling = sqrt(4/3). Edge 0.05, bands 0.03 to 0.30. No other mid, last or window is tried, now or after the result. One try.
- **Cutoff** stays `2026-11-05`; development is before it.

## 6. Added measurement (Nov 12, 2026, at the Head of R&D's request; scores no rule, counts ZERO tries; committed before the candles are opened)

On development days only (before 2026-11-05), the write-up prints the lead or lag between KXBTCPERP's 1 minute `reference_price` (or close, by the section 1 fallback) and the Kraken last trade: the correlation of one-minute log changes at lags of -2, -1, 0, +1 and +2 minutes (Kraken trades taken at receive time, last trade at each whole minute), beside the basis already planned (median and 5th to 95th percentile of perp reference minus Kraken last). If the perp lags Kraken by a minute or more (the peak correlation sits at a lag of one minute or more), the write-up says so plainly next to the development figure: a lagging perp tells the model nothing the 15 minute market does not already show.

**Live note.** A live version would take its volatility from the same ten 1 minute candle changes as research, at the cost of one extra public read at decision time, so research and a live reader use the same numbers.

## Amendment (Nov 12, 2026, committed BEFORE the held-out read; at the Head of R&D's request after Forensics' FILLHAIRCUT1, `claude/forensics-desk`, 7ca3aeb)

Forensics measured real taker fills on the recorded Bitcoin books at the same look: an immediate-or-cancel buy at the ask seen fills about 67% of the time at 2 to 10 seconds; the misses are the rows where the price then ran. For a rule whose edge is the quote lagging a model, the misses are likely its best rows, so the registered figure (every signal filled at the ask seen) is an upper bound.
- **Applies to all three versions** (three-venue, Kraken-only, CFRTI-K). Read date (2026-11-20), cutoff (2026-11-05) and marker do not change.
- **Added in the same single sitting, beside each registered figure: a BOOK-REPLAY line.** The same signals priced at the first recorded quote at least 2 seconds after the decision, and again at 6 seconds, with the registered limit (the ask seen, no slip): a signal whose ask is gone (above the limit, no active quote within 30 s) is no trade; a lower ask fills at that lower ask. Implemented in `desk_a_verify/cfrti_heldout.py` (`BOOK-REPLAY +2 s` / `+6 s`).
- **Labels are taken from the registered line as registered. Any LIVE use, and any probe gate, is judged on the 6 second replay line** (the bot sends several seconds after the minute).
- **Adds no try:** same rule, an execution model.
- **Disclosure:** Forensics' ENTRYREPLAY1 read the no-model cheap-side baseline outcomes for closes Nov 5 to 8, which is public; no CFRTI row was formed from it.

## Amendment (Nov 12, 2026, before any held-out folder is opened): venue loss
If the owner rules that the research recorder stops reading Bitstamp and Coinbase, later folders hold Kraken only. The one held-out sitting then computes the three-venue line on the folders that hold all three venues and states how many folders and rows that is (under 50 rows = "no evidence at n = x", not a stop); the Kraken-only line and CFRTI-K are computed on every held-out folder. Implemented in `desk_a_verify/cfrti_heldout.py` (`--due` runs the read when the Head of R&D says it is due with under 50 three-venue rows).

## Amendment (Nov 12, 2026, before any held-out folder is opened): stale-ask count
Printed beside each version's lines in the one sitting, no new try, no change to any label: how many signal rows have an R6 book at the decision (a poll at least 0.25 s and at most 4 s before t0, in exchange time) and, of those, how many show a book ask more than 1c above the ask the rule saw ("ask not on the book"). Rows whose close falls in the DEPTH1 freeze (closes 2026-11-09 to 2026-11-13) are NOT opened and are counted as not opened. Implemented in `desk_a_verify/cfrti_heldout.py` (`--r6 <root holding book15r6/>`). The count tells the reader how much of the registered figure rests on an ask that was not on the book; the 6 second replay line, which refuses those rows, is the line that judges live use. Development check: three-venue 5 of 16 rows with a book (Forensics counted 4 with its own clock alignment), Kraken-only 4 of 12.
