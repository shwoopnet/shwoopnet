# CFRTI1-BTC, Kraken only (registered Nov 12, 2026, BEFORE any Kraken-only figure is computed)

Ordered by the Head of R&D on the owner's request (through the Executive Assistant, Nov 12, 2026): the owner has barred Bitstamp and Coinbase from any live probe (Bitstamp needs a signed data licence for commercial use; Coinbase's terms are unread). Question: does the CFRTI1-BTC lead survive when the index is built from **Kraken trades only**? Written by Idea Desk A. Research only: no order, no key, zero Kalshi requests. No held-out row is opened for this file or its run. Kraken's own terms are "not stated" per the Head of R&D; this registration answers a research question on data already held and is not permission to read Kraken in live code.

**What it is a version of.** `workers/CFRTI1_PROTOCOL.md` and `workers/WATCH_CFRTI1_BTC.md` on branch `claude/epic-ptolemy-0amjd9` (V2, retired), script `src/scalper/cfrti1.py`. Three-venue development figure, re-derived by this desk on Nov 12: Bitcoin, n 36, cash PF 2.54.

## 1. The rule (the registered rule and constants, with ONE change)

Everything is as `src/scalper/cfrti1.py` computes it in development mode:
- Data: `quote-data:quotes/<date>/<hhmm>/{quotes,spot,results}.csv.gz`, each run folder scored on its own files.
- Market: `KXBTC15M` only.
- Decision time t0 = close minus 120 s. Quote = the last quote row with `t_send_ms` at or before t0, no more than 3 s before it; status active; YES ask above YES bid; spread 0.03 or less.
- Index at time t: the last trade price with **receive time** (`t_recv_ms`) at or before t and no more than 10 s old.
- Volatility: the index at t0 and at each of the 60 earlier 10 second steps; log changes between neighbouring steps where both exist; at least 30 changes or no trade; sample standard deviation (n - 1), times the square root of 8.
- Model chance of YES = Phi(ln(index at t0 / strike) / that figure).
- Cheap side: YES if its ask is 0.03 to 0.30, else NO if 1 minus the YES bid is 0.03 to 0.30. Buy it when the model chance of that side minus its ask is 0.05 or more. One contract, held to settlement, fee 0.07 x p x (1 - p) unrounded, cash.

**The one change:** the index and the volatility are built from rows whose `exchange` field is `kraken` ONLY. Where the registered rule averages the venues that traded in the last 10 s, this one uses Kraken's last trade or nothing. No Kraken trade in the last 10 s at t0, or fewer than 30 Kraken log changes, means no trade (counted and reported). The 0.05 edge, the 10 s window, the 120 s lead, the square root of 8 and the price bands are NOT tuned.

## 2. Sample and count

- **Development = run folders dated before `HELDOUT_FIRST_DAY = "2026-11-05"`** (the constant already pinned in `cfrti1.py`). The script written for this registration reads only those folders and has no held-out mode.
- **One try: N +1.** One rule, one market, one figure. Reported beside it, descriptive only: the three-venue figure from the same script (to prove the script reproduces n 36, PF 2.54 before the Kraken-only line is believed), how many of the 36 three-venue trades the Kraken-only rule keeps, how many it adds, and how many decisions were lost for want of a Kraken trade.
- This cell (Bitcoin, picked after the series split) was already selected on development, so its development z counts for nothing, exactly as the watch file says of the three-venue figure. Kraken-only development can only DISQUALIFY.

## 3. Labels (fixed now)

Development, Kraken only:
- cash PF under 1.0 with n of about 30 or more = **FALSIFIED on development**; the Kraken-only version is closed and no live use of the lead is possible on a permitted source.
- cash PF under 1.0 with n under about 30 = **"no evidence at n = x"**, carried to the held-out read.
- anything else = **carried to the held-out read**. It is not a pass and is never quoted as one.

## 4. Amendment to the held-out plan of CFRTI1-BTC (committed here, before the read)

Unchanged: one read, first allowed 2026-11-20, when at least 50 held-out Bitcoin edge rows exist under the registered three-venue rule; the read-once marker in `WATCH_CFRTI1_BTC.md`; `HELDOUT_FIRST_DAY`; receive-time stamps; the three-venue assertion; the registered pass (cash PF 1.3 or better, positive mean, n of 50 or more) meaning RE-TEST and never a result.

Added: in the SAME single sitting the Kraken-only figure is computed on the same held-out run folders and reported beside the three-venue figure, with its own n. **Any live use is judged on the Kraken-only figure, because it is the only version that could go live.** Kraken-only labels at the read: cash PF 1.3 or better with a positive mean and n of 50 or more = RE-TEST lead (forward shadow, lifecycle gate); cash PF under 1.0 at n of about 30 or more = falsified; anything else, or n under 50, = no call at n = x. The read is not repeated when Kraken-only rows later reach 50: the forward shadow (start Nov 23) carries the record from there. A three-venue pass beside a Kraken-only fail is written up as "an edge that needs barred sources", not as a lead.

## 5. Limits

Kraken alone is one venue of the several the settlement index averages, so its last trade is a noisier and sometimes staler estimate of the index than the three-venue mean; fewer decisions will have a trade inside 10 s. Receive time is the recorder's clock. 14 development days is one regime.

---
## Result (Nov 12, 2026; development only, run once after the registration commit 870f36a; no held-out folder opened)

Script `workers/desk_a_verify/cfrti_kraken.py` (`python3 -I cfrti_kraken.py <folder holding quotes/>`; it opens only run folders dated before 2026-11-05). 61 run folders, 14 days, Bitcoin only.

| Index built from | Cheap rows with a model | Edge trades (n) | Cash PF | Mean per trade | Win rate (wins) | Mean ask | PF by halves |
|---|---|---|---|---|---|---|---|
| Three venues, as registered (the check that the script is right: matches n 36, PF 2.54) | 222 | 36 | 2.54 | +15.65c | 33.3% (12) | 0.168 | 3.31 / 1.90 |
| **Kraken only (the one registered try)** | 215 | **32** | **1.33** | **+4.31c** | **21.9% (7)** | 0.166 | 1.12 / 1.56 |

- Of the 36 three-venue trades, Kraken only **keeps 22**, drops 14 and adds 10 new ones.
- The 22 kept: PF 1.71, mean +9.0c, 6 wins. The 14 dropped: PF 5.27, mean +26.1c, 6 wins. The 10 added: PF 0.54, mean -6.0c, 1 win.
- Decisions lost for want of Kraken data: 3 cheap rows with no Kraken trade in the last 10 s, 9 with under 30 changes (5 are lost that way with three venues too).
- Baseline (every cheap row, no model): PF 0.99 on 215.

**Label by section 3: carried to the held-out read. It is not a pass.** Plainly: on Kraken alone the lead mostly goes. Half of the three-venue wins sat in the trades Kraken alone does not take, and the trades it adds lose. 7 wins in 32 at a mean ask of 16.6c is about one and a half wins above break-even (break-even is about 17.6% with the fee); a rule with no edge shows 7 or more wins in 32 about one time in three. So development gives **no evidence of an edge on Kraken alone, and no evidence against one at n = 32.**

**Two looks beyond the registration, disclosed.** The script also printed the same rule on Coinbase alone and on Bitstamp alone, which section 2 did not list. They are information about where the signal comes from, on two venues the owner has barred, and cannot become a rule here: Coinbase only n 55, PF 2.94, mean +17.1c, 18 wins; Bitstamp only n 32, PF 2.07, mean +10.2c, 8 wins (Bitstamp has too few trades for the volatility step on 90 cheap rows). Reading: the signal is mostly Coinbase's. If the Head of R&D counts these, N is +3 for this file, not +1.

**What follows.** A live probe on Kraken alone would rest on a development figure that is indistinguishable from nothing. The held-out read (from Nov 20) reports both figures as amended in section 4; the Kraken-only one will probably have under 50 rows when the three-venue count reaches 50 (it produced 32 against 36 here), so expect "no call at n = x" and a forward shadow.

## Amendment (Nov 12, 2026, committed BEFORE the held-out read; at the Head of R&D's request after Forensics' FILLHAIRCUT1, `claude/forensics-desk`, 7ca3aeb)

Forensics measured real taker fills on the recorded Bitcoin books at the same look: an immediate-or-cancel buy at the ask seen fills about 67% of the time at 2 to 10 seconds; the misses are the rows where the price then ran. For a rule whose edge is the quote lagging a model, the misses are likely its best rows, so the registered figure (every signal filled at the ask seen) is an upper bound.
- **Applies to all three versions** (three-venue, Kraken-only, CFRTI-K). Read date (2026-11-20), cutoff (2026-11-05) and marker do not change.
- **Added in the same single sitting, beside each registered figure: a BOOK-REPLAY line.** The same signals priced at the first recorded quote at least 2 seconds after the decision, and again at 6 seconds, with the registered limit (the ask seen, no slip): a signal whose ask is gone (above the limit, no active quote within 30 s) is no trade; a lower ask fills at that lower ask. Implemented in `desk_a_verify/cfrti_heldout.py` (`BOOK-REPLAY +2 s` / `+6 s`).
- **Labels are taken from the registered line as registered. Any LIVE use, and any probe gate, is judged on the 6 second replay line** (the bot sends several seconds after the minute).
- **Adds no try:** same rule, an execution model.
- **Disclosure:** Forensics' ENTRYREPLAY1 read the no-model cheap-side baseline outcomes for closes Nov 5 to 8, which is public; no CFRTI row was formed from it.
- **Disclosure:** Forensics' ENTRYREPLAY1 read the no-model cheap-side baseline outcomes for closes Nov 5 to 8, which is public; no CFRTI row was formed from it.

## Amendment (Nov 12, 2026, before any held-out folder is opened): venue loss
If the owner rules that the research recorder stops reading Bitstamp and Coinbase, later folders hold Kraken only. The one held-out sitting then computes the three-venue line on the folders that hold all three venues and states how many folders and rows that is (under 50 rows = "no evidence at n = x", not a stop); the Kraken-only line and CFRTI-K are computed on every held-out folder. Implemented in `desk_a_verify/cfrti_heldout.py` (`--due` runs the read when the Head of R&D says it is due with under 50 three-venue rows).

## Amendment (Nov 12, 2026, before any held-out folder is opened): stale-ask count
Printed beside each version's lines in the one sitting, no new try, no change to any label: how many signal rows have an R6 book at the decision (a poll at least 0.25 s and at most 4 s before t0, in exchange time) and, of those, how many show a book ask more than 1c above the ask the rule saw ("ask not on the book"). Rows whose close falls in the DEPTH1 freeze (closes 2026-11-09 to 2026-11-13) are NOT opened and are counted as not opened. Implemented in `desk_a_verify/cfrti_heldout.py` (`--r6 <root holding book15r6/>`). The count tells the reader how much of the registered figure rests on an ask that was not on the book; the 6 second replay line, which refuses those rows, is the line that judges live use. Development check: three-venue 5 of 16 rows with a book (Forensics counted 4 with its own clock alignment), Kraken-only 4 of 12.

## Amendment (Nov 12, 2026, ruling of the Head of R&D): the R6 freeze at the held-out read
At the held-out read (Nov 20 or later, the one sitting), the script MAY open the R6 books for closes 2026-11-09 to 2026-11-13, for the replay lines and the stale-ask count only: it reads quotes at CFRTI's own signal instants and no outcome of any depth rule. Before the read those folders stay unopened for CFRTI, as every held-out folder does. Development and selftest modes keep the freeze (`desk_a_verify/cfrti_heldout.py`).

## Amendment (Nov 12, 2026, ruling of the Head of R&D after QUOTEVSBOOK1, `claude/forensics-desk` 836d9fa; before any held-out folder is opened): what the registered lines mean
The quote recorder reads the market LIST endpoint, a copy refreshed about every 11 seconds (0 to 11 s old, about 5.5 on average). The Nov 20 read still happens once as registered, but its meaning is fixed now: **the registered lines (three-venue and Kraken-only, priced at the quote recorder's ask) are reported as "priced at a stale copy, not tradable". The 6 second book-replay line and the stale-ask count are the only lines that can support anything.** Labels from the registered line are unchanged; none of them can support live use.


## Amendment (Nov 12, 2026, ordered by the Head of R&D after Forensics' audit): the BOOK-REPLAY line is an R6 order-book replay, nothing else
The lines `BOOK-REPLAY (R6) +2 s` and `+6 s` fill each signal row from the R6 ORDER BOOK at the first poll at or after the decision plus 2 s and plus 6 s (within 30 s), limit = the ask seen (a lower ask fills at that ask), at least 1 contract displayed at the ask; a vanished ask is no trade; rows with no R6 book at the decision are counted as "no book" and never scored. The earlier wording "the first recorded quote" is replaced by this: no row of the quote recorder's `quotes.csv` list is used to fill a row. Implemented in `desk_a_verify/cfrti_heldout.py` (`r6_replay`, tested by `replaytest`). Any forward shadow for CFRTI is built on R6 or not at all. Corrected development figures: see the Head of R&D's message and `CFRTI_DEV_REPLAY_JOIN_NOV12.md`.
