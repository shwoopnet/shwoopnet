# MM1S amendment: the scorer choices MM1 leaves open (2026-10-29, V2 worker MM1S, research only)

Written and pushed BEFORE any fill or profit and loss was computed from recorded gold quotes. Before writing it I only counted windows (coverage files) and read the column names. The registration's rules and gates are not changed. Where the registration says nothing, the more CONSERVATIVE choice is taken every time, and each one says so.

## What MM1 fixes (README, "Pre-registration: MM1", 2026-10-29)

Gold's 15 minute market (`KXGOLD15M`), the quote-data recorder's last 150 seconds of each window, joined to the public gold trade tape, "with QUOTE1's rules and queue model". Gates: QUOTE1's (300 independent closes minimum, PF at least 1.5, both halves above 1, flatten losses under half the spread earned). Mid-window quoting is NOT_RUNNABLE (no depth before the last 150 s) and is not scored here.

So the rule is QUOTE1's card on gold: at the first recorded poll of a window with a bid and an ask both present, post one buy at the best YES bid and one sell at the best YES ask, one contract each, no re-quoting, net inventory at most 1 each way, flat 20 seconds before the close by crossing, nothing held to settlement.

## What is recorded, and since when (counted, not scored)

- Branch `origin/quote-data`, `quotes/<date>/<HHMM>/quotes.csv.gz`. Columns: `t_send_ms, t_recv_ms, ticker, yes_bid, yes_ask, bid_size, ask_size, strike, status`. Each row is Kalshi's REST market object (`/markets?tickers=...`): top of book only, sizes fractional (`*_size_fp`), one poll about every 0.6 s (216 to 254 polls per window) from 150 s before the close to the close. `coverage.csv.gz` gives polls, ok polls and 429s per window; `clock.csv.gz` gives the runner's clock offset to a time server (15 to 17 ms in the 10:25 run).
- Gold is in the file from the run starting 2026-10-28 17:23 UTC; the first gold window closes 2026-10-28 17:30 UTC (not 15:45, which is when the extension merged).
- Count today (2026-10-29 18:36 UTC): **48 gold windows**, last close 2026-10-29 12:00 UTC (runs 1723: 11, 2332: 18, 0403: 12, 1025: 7). Gaps: 20:00 to 23:45 UTC on 10-28 and 07:00 to 10:30 UTC on 10-29 (runs that started late or not at all).

## The trade evidence

- The recorder holds quotes only. Fills come from the public tape `GET /markets/trades?ticker=...&min_ts&max_ts` (fields `created_time`, `yes_price_dollars`, `count_fp`, `taker_outcome_side`).
- How far back it goes: the tape still returns trades for gold windows of 2026-10-01 and 2026-09-01, so every recorded window (from 2026-10-28) is covered. Fetched per window for `close - 170 s` to `close`, all pages.
- **Disclosure.** The retention check above asked for 5 trades of `KXGOLD15M-26OCT281330-30`, which is the first recorded gold window, and printed the last print (YES 0.001 at 17:29:58 UTC). No fill or P/L was computed from it, and nothing below was chosen after it. It is one window of the 48; it is said here so the reader can weigh it.
- Side mapping (as QUOTE1): `taker_outcome_side == "no"` is a taker SELLING YES, which can only hit resting YES bids (our buy); `"yes"` is a taker BUYING YES, which can only hit resting YES asks (our sell). A print is counted against our order only if its price is consistent with it (a "no" print at or below our bid; a "yes" print at or above our ask).

## Choices the scorer needs (each the conservative one)

1. **When our order is live.** From the posting poll's `t_recv_ms` plus 250 ms (an order round trip), corrected by the run's median clock offset. Trades before that cannot fill us. Conservative: QUOTE1 used `t_recv` with no delay.
2. **Queue position.** A new order joins BEHIND all displayed size at its price at the posting poll (`bid_size` for the buy, `ask_size` for the sell). No price improvement (we never post inside the spread, which would put us first). Conservative.
3. **Cancellations ahead of us never move us forward.** The displayed size ahead shrinking without trades (cancels, or the quote moving away) does NOT advance our place. Only trades do. Conservative (strict).
4. **When it fills.** Only after the displayed size ahead is gone, by either
   (a) taker trades AT our price after we are live: our order fills by the amount that the cumulative taker volume at our price exceeds the queue ahead, up to our size (partial fills are kept and become inventory); or
   (b) the price trading or quoting THROUGH ours: a taker print strictly through our price (a "no" print below our bid, a "yes" print above our ask), or a recorded quote whose opposite side has crossed our price (best ask at or below our bid, best bid at or above our ask). A real book cannot do either without our level being cleared first, so the whole remaining order fills at OUR price (never the better one).
   The quote merely moving away from our price is NOT a fill. A print exactly at our price also counts toward (a) only once.
5. **Adverse selection.** Nothing is added or removed for it: it is in the replay, because fills only happen when takers trade into us or the price runs through us, and the inventory is then marked at the real later quote. No "would have been filled anyway" credit and no fill on a quote touch.
6. **Inventory and exit.** Net at most 1 contract each way. When one side fills, the other keeps resting to complete the cycle at its price. At 20 s before the close all resting orders are cancelled and any open inventory (including a partial fill) is flattened by crossing at the last recorded opposing quote at or before `close - 20 s` (the bid to sell a long, the ask to cover a short), taker fee. If that poll's opposing side is missing, the flatten price is the worst case (0 for a long's sale, 1 for a short's cover). Nothing is held to settlement. Conservative: held inventory near the close is what QUOTE1 lost on, and holding to settlement would make this a direction bet.
7. **Fees.** The series object says `fee_type: "quadratic"`, `fee_multiplier: 1`; the public field does not state a maker fee by itself, so it is not relied on. **Verdict: every maker fill pays the taker formula 7% x C x p x (1-p), rounded up to the cent per order** (conservative; the task's rule). Crossing (flatten) fills pay the same taker fee. Information only: the maker schedule 1.75% x C x p x (1-p) rounded up, and zero maker fee. Fee stress: the verdict fee x1.2.
8. **Size per quote.** C = 1 contract per side (QUOTE1's lot). Also C = 10 per side, which needs 10 more contracts of trades past the queue to fill fully and has its fee rounded per order at 10. **The verdict must pass at BOTH sizes** (conservative). Prices are dollars on Kalshi's deci-cent tick near the extremes (`tapered_deci_cent`); we post at the displayed price exactly.
9. **Which windows count.** Chosen on coverage only, before any fill: a window is usable if its first recorded poll with both sides is at least 120 s before the close, its ok polls are at least 80% of polls, it has a poll at or before `close - 20 s`, and its tape was fetched without error. A window with no two-sided quote at all is reported and is NOT counted as a posted window.
10. **Independent windows.** Gold has one window per close time, so each window is one observation. Windows of the same US Central date are not independent of each other in practice, so z is clustered by Central date. The 300 minimum: `run` refuses below 300 usable recorded windows, and the verdict is NOT_ENOUGH_DATA if fewer than 300 windows had an order posted (conservative: both, not either).
11. **Windows with no trades.** Reported both ways: included (P/L 0 unless the quote crossed us) and excluded.
12. **Three windows by date.** By close time, thirds of the usable windows (RULES.md; QUOTE1 had halves). The last third is the holdout, read in the same single run.

## Verdict rule (registration gates plus RULES.md, not loosened)

`NOT_YET_FALSIFIED` only if, at the verdict fee, at BOTH C = 1 and C = 10: PF at least 1.5 in each of the three date windows and pooled, both halves above 1, net per window above 0, PF above 1 at fees x1.2, flatten and inventory losses under half the spread earned, and the date-clustered z at least 5.17 (N about 439,000). Fewer than 300 posted windows: `NOT_ENOUGH_DATA`. Any gate failed with at least 300: `FALSIFIED`. A pass earns only a forward test registration; a live design would also have to avoid holding gold inventory while L1 holds a gold position in the same window (L1 buys gold at about 6 minutes left and holds it to settlement).

**Tries (N).** 2 sizes x 3 fee assumptions = 6, of which the 2 verdict-fee rows decide. Running count about 439,006.

**Prediction (unchanged from MM1/QUOTE1).** FALSIFIED once 300 windows exist: the spread on gold's last 150 s is a tick against a fee of at least 1c per order at C = 1, and one-sided fills are adverse.

Run once with `PYTHONPATH=src python -m scalper.mm1 run` from `kalshi-scalper/` (refused a second time). `count` only counts.
