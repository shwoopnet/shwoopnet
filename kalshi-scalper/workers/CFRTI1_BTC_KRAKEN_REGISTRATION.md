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
