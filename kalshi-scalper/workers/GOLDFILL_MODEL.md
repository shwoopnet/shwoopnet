# GOLDFILL model: how often a resting gold entry fills, and what it saves (V2 worker GOLDFILL, 2026-10-30, research only, information)

**What this is.** A fill-probability model for L1's gold entry (`KXGOLD15M`, the side priced 0.88 to 0.97 at the 6 minute decision) for four order types, built from quotes and trades ONLY. No `result`, no `results.csv.gz`, no settlement price was opened: the market table is read for ticker and close time only, the recorder's result files were deleted from the working copy before any run, and R6's coverage files (which carry `result`) were never read. It scores no strategy and gives no verdict. The two tests that use it are registered in `workers/GOLDFILL_PROPOSAL.md`. Code: `src/scalper/goldfill.py` (`fetch`, `model QDIR`), engine tests `tests/test_goldfill.py`. Not L1Q1 or MAKER5 and does not touch their read (both still read on or after 2026-11-06).

## Order types (side prices; the bought side's bid b and ask a at the decision)

| Name | Price | Note |
|---|---|---|
| ASK | a, resting (not immediate-or-cancel) | marketable at once if the ask is still there when it is live |
| IN01 | a - 0.1c (one tick), or b if the spread is one tick | gold trades on a 0.1c grid mid-book |
| IN1C | a - 1c | **on gold this is usually BELOW the best bid**: the spread at the decision is 0.1c in 41% of signals, median 0.3c, 1c or more in only 26% |
| BID | b, joining the queue | |
| IOC (recorder and R6 only) | the bot's own order: immediate-or-cancel, limit = a rounded UP to the next cent (`l1Pick` in `functions/kalshiLiveLib.js`) | |

**Queue rule (MM1S / Q2B, conservative).** The order is live 1.0 s after the decision. It joins behind all displayed size at its price (history: unknown, so three cases below); only trades move it forward; it fills by taker sales AT its price past the queue (partial fills kept), or wholly at OUR price by a sale strictly through it, a taker buying our side from an ask at or under our price, or a recorded side ask at or under it. Fill times from candles are stamped at the candle's END. A quote moving away is not a fill.

## Data

- **History (the main table):** 619 gold L1 signals with the full public trade tape from the decision to T-119 s (26 windows on 2026-09-01, the rest 2026-09-22 to 2026-10-29 20:00 UTC; 28 days), the decision and the side-ask lows from the 1 minute candles in `data/{fresh,five,book,l1b}.sqlite`. 1,169 signals exist since 2026-09-01; the tape fetch (newest first) was stopped by its 2 hour limit after 619 under Kalshi's shared rate limit; `python -m scalper.goldfill fetch` resumes it. Every window had trades; the median window traded about **104,000 contracts** in the 4 minutes after the decision.
- **Quote recorder (`quotes/*/quotes.csv.gz`, gold since 2026-10-28 17:23 UTC):** 58 gold windows, top of book only, last 150 s only, so the "decision" here is the first poll (about T-150 s), not the 6 minute mark; 13 signals (2 more without tape). Horizons stop at T-20 s, so 240 s does not fit.
- **R6 (`book15r6/`):** one run so far (2026-10-29 22:03 UTC), 6 gold windows, **3 signals**. Code runs on it as it grows; nothing can be read from 3.

## 1. History, at the 6 minute decision (619 signals; lower bound, Q at the bid infinite)

The three queue cases (Q = 0 at the bid; Q = 1,011, the recorder's median favourite bid size; Q infinite) differ by at most 8 points on BID, 5 on IN1C, 3 on IN01 and none on ASK, and **the three sizes give the same shares** to within 1 point: see the reason in section 3.

| Order | full by 30 s | full by 60 s | full by 120 s | full by 240 s (T-119 s) | missed at 240 s | saved per filled contract vs a | saved per opportunity |
|---|---|---|---|---|---|---|---|
| ASK | 91% | 100% | 100% | 100% | 0% | 0.00c | 0.00c |
| IN01 | 84% | 89% | 90 to 91% | 92% | 8% | +0.10c | +0.09c |
| IN1C | **59%** | 67% | 74% | 77% | **23%** | **+1.00c** | +0.77c |
| BID | 75% | 81% | 83% | 85% | 15% | +0.43c | +0.37c |

Upper bound (Q = 0): IN1C 64 / 70 / 77 / 80%, BID 83 / 87 / 89 / 90%, IN01 87 / 91 / 92 / 93%. Same shape in September (76 signals: IN1C 66% by 30 s, 82% by 240 s) and October (543: 58%, 76%). The 60 s jump on ASK is the first candle's ask low (timing only known to the minute).

## 2. Quote recorder (13 signals, decision about T-150 s) and R6 (3 signals)

| Order | Recorder full by 30 s / 60 s / 120 s | Recorder saved per filled | R6 full by 30 s (n 3) |
|---|---|---|---|
| ASK | 100 / 100 / 100% | 0.00c | 3 of 3 |
| IN01 | 69 / 77 / 77% | +0.10c | 3 of 3 |
| IN1C | 69 / 77 / 77% | +1.00c | 3 of 3 |
| BID | 69 / 77 / 77% | +0.30c | 3 of 3 |
| IOC (the bot's) | 100% | 0.00c | 2 of 3 |

Displayed size, recorder at T-150 s: favourite bid median 1,011 (quartiles 494 / 1,011 / 2,501), favourite ask median 2,506 (2,500 / 2,506 / 2,550). R6 at T-360 s (3 signals): bid 30 / 700 / 3,616, ask about 2,500, spread 0.1c to 1c. **A 20 contract order is under 1% of the displayed ask**, so the model finds no size effect on fills; the bot's measured +1.8c slippage at 16 to 20 contracts (`workers/GOLDSLIP.md`, 6 orders) and its 37% no-fill share are NOT explained by depth at the decision, and must come from the bot's own delay between the candle and its send (its order goes out on the next minute's tick, when the ask has moved) or from a market object that differs from the book. R6 will separate these once it has a few hundred signals; it is the one open question this model cannot settle.

## 3. Why the queue and the size barely matter on gold: the fills are the price coming down

How the full fills by 240 s came about (history, C = 1; the event that completed the order):

| Order | a taker sale strictly below our price | a taker lifting an ask at or under our price | a recorded ask at or under our price | takers selling AT our price past the queue |
|---|---|---|---|---|
| ASK | 248 | 224 | 43 | 104 |
| IN01 | 377 | 143 | 14 | 35 |
| IN1C | 324 | 139 | 7 | 4 |
| BID | 340 | 174 | 12 | 0 (Q infinite) |

At IN1C and BID over 99% of fills need the price to trade or quote down to the order; the queue is irrelevant because gold's price moves through a 0.1c level every few seconds. That is MAKER2's finding ("the fills are the dips"), now on the real tape at the real tick: a resting order on gold is a bet that the price falls 1c, and it is paid only when it does.

**Price path (not an outcome).** The bought side's bid at T-120 s minus the decision bid: BID orders filled +0.65c (n 526), BID not filled +7.08c (n 93); IN1C filled +0.22c (n 474), IN1C not filled +6.19c (n 145). **Market-implied value at T-120 s** (side bid at T-120 s minus price paid, before fees, C = 1): every signal bought at the ask +1.17c; IN1C fills at their own price +0.76c; IN1C misses had they been bought at the ask +5.79c. So per opportunity, resting at IN1C with no fallback is worth about 0.77 x 0.76 = **+0.58c against +1.17c for crossing**, at T-120 s marks. This is a market mark two minutes before the close, not a settlement, and it is history only (no R6 window), so L1Q1's read stays clean; it agrees in sign and size with MAKER2 (-0.80c against +0.10c on settlement).

## 4. What it means for the owner's choice of order type (no verdict)

1. **The cost of crossing on gold is not the spread.** The spread at the decision is 0.1c to 0.3c in most signals; resting at the best bid saves about 0.4c a contract when it fills. The 0.6c the bot pays over the candle ask (`workers/DRIFT.md`) is therefore most likely the move between the decision candle and the bot's send (not measured here), and a resting order placed at that later moment would face the same moved price.
2. **1c inside the ask fills 59% of the time within 30 s and 77% by T-2 min, saving exactly 1c**, but it fills because the price fell; the 23% it misses were worth about 5c more each at T-120 s marks than the average signal. On the model's numbers that gives up about half the market-implied edge.
3. **The fee does not change the ranking:** at p about 0.9 the formula is 0.63c a contract, so one contract pays 1c at any of these prices and 10 contracts pay 7c (6.3c rounded up) at 0.90 and at 0.89 alike; the maker fee for gold is not confirmed from public data.
4. A rest-then-cross rule (GF1) and a "did not dip in 30 s" hold rule (GF2) are registered for R6, both predicted FALSIFIED on the strategy bar, with the differences against plain L1 as the useful read (`workers/GOLDFILL_PROPOSAL.md`).

**Limits, stated.** History has no book: the queue at the bid is bounded, not measured, and a candle's ask low is known only to the minute. The recorder sees only the last 150 s. R6 has 3 signals. The tape is public prints only (no hidden or cancelled size). The 1.0 s live delay is Q2B's choice; the bot's real delay is longer and is not modelled here.

Tries: none (no strategy is scored; information).
