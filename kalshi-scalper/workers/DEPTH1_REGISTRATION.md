# DEPTH1 registration: order-book depth in the 15 minute gold and Bitcoin markets, recorder R6 (V2 worker, 2026-10-30, research only)

Written and pushed BEFORE any recorded row was opened. What I read to write it: the recorder's source and workflow (`scripts/record_15m_book.py`, `.github/workflows/record-15m-book.yml` on `origin/main`) for the column names, `workers/R6T_REGISTRATION.md`, `workers/GF12_NOTES.md`, `workers/RULES.md`, the README sections for GF1, GF2, MAKER5, L1Q1 and FALS3, and the **file names** on `origin/quote-data` (16 files, 4 recorder runs). I opened no `book.csv.gz`, `trades.csv.gz` or `coverage.csv.gz`, no price, size or result of R6, and no row of any candle file (for fresh.sqlite I used only the column list that `tests/test_oifeed.py` documents). Owner approval: "Brief 2 only: order-book depth", 2026-10-30, via the main session. Code: `src/scalper/depth1.py` (`freeze`, `readiness`, `read`), `tests/test_depth1.py`.

**Ledger check.** Not a reworded test. L1Q1 and MAKER5 (R6T) use the book to MODEL FILLS of a resting order. GEN9, GEN10 and GEN11 searched TAPE features for gold and Bitcoin (FALSIFIED; they had no book). No tested rule uses the book's SIZES at several levels as the signal. This is a data-structure test. It is never scored as "cheap side late": the entry is at 8 minutes left, inside the 10 to 90 cent band, on either side.

## Family, counterparty, universe

- **Family.** Five level order-book imbalance and its changes, in `KXGOLD15M` and `KXBTC15M`, read once per market window at a fixed look 8 minutes before the close, on recorder R6 (running, ends 2026-11-13 23:59 UTC).
- **Counterparty.** Resting makers who leave one side of the book thin and get swept before a price move (adverse selection against the maker). The data can support or refuse this directly: a feature that predicts direction must do so with the SWEEP FEATURE and the THIN-SIDE FEATURES agreeing in sign with the imbalance ones. If the result cannot support that (no feature passes), the entry in the result file reads **no counterparty named**.
- **Universe.** Fixed now, gold and Bitcoin only, chosen on the owner's brief and never on returns. Ethereum, Dogecoin and XRP are recorded but not read by this card.

## Prediction, written before data

Best single feature profit factor about **1.15 pooled** (after the taker fee and the quoted spread). Expected verdict **FALSIFIED**. Direction accuracy near the price paid (mean ask about 0.5), i.e. about 50%. A feature earns a second look only at 55% direction accuracy with 300 or more trades; that is a flag in the result, not a verdict and not a promotion.

## The 10 features (the budget; no generator; no feature may be added or edited)

Book of one poll in YES terms from the recorder columns: `yes_bid_px_1..5`, `yes_bid_sz_1..5` (YES bids, best first), `no_bid_px_1..5`, `no_bid_sz_1..5` (NO bids, best first). YES ask = 1 - `no_bid_px_1`; NO ask = 1 - `yes_bid_px_1`. A NO bid is a resting offer to sell YES at 1 - its price, so buyers of YES take NO bids, and sellers of YES take YES bids. Sizes are as recorded. Every feature is signed: **positive buys YES, negative buys NO, zero or undefined makes no trade**. Source is in `src/scalper/depth1.py`; the hashes below fix it.

1. `f1_imb5`: (sum of the 5 YES bid sizes - sum of the 5 NO bid sizes) / their total. A thin NO side is lifted by YES buyers, so positive buys YES.
2. `f2_imb1`: the same at the touch only (level 1 sizes).
3. `f3_dwmid_minus_mid`: size-weighted mid of all recorded levels minus the plain mid, in YES price (weighted YES bid B; weighted YES ask A = 1 - weighted NO bid; (B + A)/2 - mid). Positive when the NO side's depth sits further from the touch, buys YES.
4. `f4_d_imb30`: `f1` now minus `f1` at the last poll at or before 30 s earlier (within 6 s). The book leaning more toward YES buys YES.
5. `f5_d_imb60`: the same over 60 s.
6. `f6_thin_depletion`: the side with the smaller 5 level size 60 s ago: its relative size lost by now, (size then - size now) / size then. A thin NO side emptying is positive (buys YES), a thin YES side emptying is negative (buys NO). A tie is 0 (no trade).
7. `f7_sweep_net`: from the tape, in the last 60 s before the look: a SWEEP is trades of one taker side in the same whole second at two or more distinct prices. Count of taker-"yes" sweeps minus taker-"no" sweeps. Net YES sweeps buys YES.
8. `f8_hole_asymmetry`: (gap from the NO touch to the next NO level) - (gap from the YES touch to the next YES level), a missing second level counting as a gap down to 0. A hole behind the YES touch is negative, buys NO.
9. `f9_book_slope`: slope of the NO side minus slope of the YES side, slope = (touch price - last recorded level price) / total size over the recorded levels (price given up per contract of depth; needs 2 levels per side). A steep, thin YES side is negative, buys NO.
10. `f10_imb_3c`: `f1` counting only size within 0.03 of each side's touch.

Every feature is a pure function of the book at the look (and, for 4, 5, 6, the polls 30 or 60 s earlier; for 7, the tape up to the look). No outcome, no later poll and no price after the look enters any feature. `f8` and `f9` share their logic on purpose (hole versus slope); `f1`, `f2`, `f10` are correlated. They are counted as 10 separate tries regardless.

## The look and the trade

- **Decision time: one fixed look, 480 s (8 minutes) before the close.** Not a grid. Reasons: a grid between 900 s and 150 s would multiply the tries by the grid size and make neighbouring looks the same bet; 480 s leaves 420 s of history for the 30 s and 60 s features; it is before L1's 6 minute look (360 s) and before the last 150 s that QUOTE1 and GEN9 to GEN11 already covered; and the window is far enough from the end that the favourite is rarely at 95c. The decision poll is the last poll at or before T-480 s, within 10 s of it, in exchange time (the clock rule of R6T: offset = median of Date header + 0.5 s minus `t_recv_ms` over the run's rows; no clock means the window is excluded and counted).
- **Trade.** Buy the implied side, **1 contract**, at the best ask, held to settlement ($1 if it wins, 0 if not). The fill is the first poll at or after the look + 1.0 s (R6T's "an order is live 1 s later" rule; the brief said "the decision poll", this is the conservative reading), within 20 s. The ask must be 0.10 to 0.90 and have at least 1 contract displayed; otherwise no trade (counted). **Round trips are NOT in this registration**: no exit, no resting order, no re-pricing.
- **Cost.** Taker fee 7% x C x p x (1 - p), rounded up to the cent per order, C = 1, plus the quoted spread (the ask is paid, the settlement is $1/$0); stress fee x 1.2.
- **Unit.** One window of one market counts once; at most one trade per feature per window. Features are scored separately (a window can carry up to 10 trades, one per feature, which are not independent of each other; the z is clustered by date and the bar is per feature).

## Windows, blocks and what counts as a usable window

- **Usable window** (coverage file only, fixed now): a coverage row with a ticker; `ok_polls/polls` at least 0.80; `max_gap_ms` at most 20,000; `tape_pages` at least 1 and no `tape incomplete`, `tape page cap` or `tape out of time` note; `first_recv_ms` at or before T-545 s; `last_recv_ms` at or after T-470 s; `result` "yes" or "no".
- **Dates.** US Central date of the close. Only windows with a close date from **2026-10-30 to 2026-11-13** count (windows dated 2026-10-29 are excluded and counted). Daylight time ends 2026-11-01.
- **Three blocks of 5 days, fixed now:** A = 2026-10-30 to 2026-11-03, B = 2026-11-04 to 2026-11-08, C = 2026-11-09 to 2026-11-13. C is the holdout and is read in the same single run (there is one read). Halves (by close time of the feature's trades) are also reported.

## Kill criteria and the bar

- **NOT_ENOUGH_DATA:** fewer than **300 independent windows per market** (usable windows in the dates above that have a decision poll) at the read. Nothing is scored in that case. The owner's limit was 14 days; **the recorder is not extended by this card or by me**; extending it past 2026-11-13 23:59 UTC needs the owner's decision and a new registration.
- **NOT_RUNNABLE:** the recorder schema changes, more than 20% of usable windows lack a clock, or the frozen hash does not match.
- **FALSIFIED:** the card is FALSIFIED unless at least one of the 20 tries meets the whole bar. A try (one feature in one market) meets the bar only if: at least 300 trades; **profit factor at least 1.5 in each of the three blocks** and pooled; both halves above 1.0; net per trade above 0 at the verdict fee and at fees x 1.2 with PF above 1.2 at x 1.2; date-clustered z at least **5.27** (RULES: Bonferroni on N = 728,628 + 20 = 728,648, one sided, alpha 0.05); and the **shuffled-book control**. A try under 300 trades cannot meet the bar.
- **NOT_YET_FALSIFIED** only if a try meets all of that. A pass earns only a forward-test registration; nothing here promotes anything.

## Shuffled-book control

For each market, the 10 feature values are shuffled across that market's windows (1,000 rounds, seed 20261114), keeping each window's own prices, fills and result; every shuffle round gives the **best mean net per trade over all 20 tries (10 features x 2 markets)**. A try passes the control only if its real mean net per trade exceeds the 99th percentile of those 1,000 best-of-20 values: p 0.01 after counting the tries (a per-try p of 0.0005 is not reachable with 1,000 shuffles, so the control is the family-wise maximum, as GEN10 and GEN11 did). A shuffle with under 30 trades is not counted. The per-try marginal p is printed beside it.

## Independence rule

One market window is one unit. Gold and Bitcoin windows that close together are different markets but not independent of each other in time; they are never pooled into one try (each market is its own try) and the z is clustered by US Central date within each try. A feature's trades on one window are one trade. No window is used twice for a try, at any size.

## History check (weaker evidence, stated before the read)

Candle files (`fresh.sqlite`: `bid_o/h/l/c`, `ask_o/h/l/c`, `price_c`, `volume`, `oi`, 1 minute) have **no sizes and no levels**, so 9 of the 10 features have no analogue and are NOT_RUNNABLE on history. FALS3's lesson (a recorder-only result is weak, windows can be a lucky sample) is met in the only way available: one stand-in, **price pressure**, the sign of the YES mid change between the candles ending T-540 s and T-480 s, bought at the next candle's (T-420 s) ask in the same 0.10 to 0.90 band, held to settlement, same fee, for gold and Bitcoin, on settled windows closing before 2026-10-29 (so the recorder days are not counted twice), with the pooled PF and thirds by time, and both with all candles and with only decision candles that have volume. It is 1 look per market, not a try, and it can only weaken a claim: a positive R6 feature with a history stand-in below 1 is flagged, and a positive R6 result alone is never called a finding.

## Overlap check (L1 and OICORE)

Any rule that holds the same ticker to settlement overlaps L1 on gold and OICORE (`REF_GEN6_OICORE`, Bitcoin) when they hold it. Per window the read marks **held**: for gold, L1's published signal (exactly one side's ask 0.88 to 0.97 at the poll ending 360 s before the close, from the R6 book); for Bitcoin, OICORE's rule (a side's ask 0.05 to 0.50 at the candle ending 180 s before the close and open interest up by more than 86,299.56 over the 3 minutes before, read from `fresh.sqlite`; a window without candles is "unknown"). Results are printed with all windows and **without held and unknown windows**. The verdict is on all windows. A try that passes but whose result without held windows has pooled PF under 1.5 is called **paper only (overlaps L1 or OICORE)**. Nothing is promoted either way.

## N accounting

Running N about 728,628 (after GEN11). This card adds **20 tries** (10 features x 2 markets), counted at the read, so N at the read = 728,648 and the z bar is 5.27. Looks that are not tries: the shuffled-book control (1 family look plus 20 marginal p values), the history stand-in (2 looks), the overlap split (reported, not a verdict), the second-look flag. The decision time is fixed, so there is no grid to add.

## Coverage finding (from file names only, 2026-10-30 16:09 UTC)

R6 started 2026-10-29 22:03 UTC. The recorder ("a 30 minute cron, up to the next 4 hour boundary") has produced **4 runs** on `quote-data`: 2026-10-29 22:03, 2026-10-30 00:02, 05:37 and 12:43 UTC. **GitHub fired no scheduled run from 08:00 to 12:43 UTC (4.7 hours, no data) and from 04:00 to 05:37 UTC (1.6 hours).** File names give runs, not windows, so windows per market are ESTIMATED as recorded hours x 4, an upper bound (a run may stop early), from `python -m scalper.depth1 readiness`:

- Recorded: about 11.6 hours of 18.0 elapsed, **64% coverage**.
- Eligible so far (closing on or after 2026-10-30 Central): about **24 windows per market**, both gold and Bitcoin (gold's market is closed Friday 17:00 to Sunday 18:00 Central, which the projection takes into account; its daily break is not modelled, so gold is an upper bound).
- Projected to 2026-11-13 23:59 UTC at 64% coverage: **Bitcoin about 901 windows, gold about 646**. With a 70% share surviving the usable-window rule: **Bitcoin about 630, gold about 452**.
- **The 300 per market minimum is on track**, with a margin of about 2.1x for Bitcoin and 1.5x for gold. Break-even: the recorder must record **at least 29% (Bitcoin) and 41% (gold) of the hours from now** to the end; it is recording 64% now. If the cron stalls like 08:00 to 12:43 for a few more days, gold is the market that falls short first. **The expected outcome is not NOT_ENOUGH_DATA today.** The readiness line in the AUTO log re-computes this every pass; if it turns OFF TRACK, the expected outcome becomes NOT_ENOUGH_DATA and I will not extend the recorder: the owner decides.

## The read

**One read, once**, by `python -m scalper.depth1 read`: refuses before **2026-11-14 00:00 UTC (6:00 PM Central on 2026-11-13: daylight time ended on 2026-11-01, so this is 6 PM, not 7 PM)**, refuses a second run (`data/depth1_result.txt`), and a started marker without a result refuses again (a crashed run is never quietly read twice; the lead decides). `autoscore.py` fires it from **2026-11-14 02:00 UTC** (two hours after the earliest allowed time, for the recorder's last 4 hour job to push its final windows; the run still refuses before 00:00 UTC by itself), or from 2026-11-15 00:00 UTC whatever the count. This is a scheduling choice, not a rule; the brief said "the first AUTO pass after 2026-11-14 00:00 UTC" and a read at 00:00 UTC would miss the last job's windows. It writes `workers/DEPTH1_RESULT.md` and `data/depth1_result.txt`.

## Frozen hashes

The feature sources and fixed settings are hashed in `workers/DEPTH1_FROZEN.md` and `workers/DEPTH1_frozen.json`; `tests/test_depth1.py` fails if the source differs. Total sha256 at registration:

`8eb6aa3842fa4bb50cebbe2f1b2f87df726296e0d0b16964cc7e9b45a8deeb69`

(Written by `python -m scalper.depth1 freeze` before any R6 row was opened; the registration text was finished right after. The frozen settings are the `CONFIG` block; this document describes them in words, and the code is the exact version.)
