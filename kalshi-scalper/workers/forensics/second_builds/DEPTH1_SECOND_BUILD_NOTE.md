# DEPTH1: independent second build (Forensics desk, 2026-11-13), before the read

Ordered by the Head of R&D under rule 16b: DEPTH1 reads once from 2026-11-14 00:00Z through one build (V2's frozen `depth1.py` run through Desk A's wrapper), and a read cannot be recorded without an independent second build that prints the same figures. Any difference found now is a dated clarifying amendment before the read, not a spent try.

**What this build was written from:** V2's `workers/DEPTH1_REGISTRATION.md`, the frozen settings printed in `DEPTH1_FROZEN.md` (the CONFIG block and hash list), Desk A's `DEPTH1_AMENDMENT_1_DESK_A.md`, and the R6 recorder's column names in `scripts/record_15m_book.py` on main. **Not read:** `depth1.py`, its tests, `depth1_wrapper.py`, `depth1_dryrun.py`, `depth1_precheck.py`, `DEPTH1_READ_NOTES_DESK_A.md`.

**What was opened:** invented rows only. No R6 file was opened for this build and no outcome was joined to anything. Disclosure: on Nov 12 this desk read R6 gold, XRP and Dogecoin books for WHEEL0's books-only count (no result joined); those files were not reopened.

**Default-closed.** `depth1_second.py read <R6 root> <out dir>` refuses before 2026-11-14T00:00:00Z, refuses a second run (a result file) and refuses after a started marker; a HELDOUT_ path is refused. Before the read time it runs only from Python on a folder that carries the marker file `MADE_UP_DATA`.

## Files

- `depth1_second.py`: the second build.
- `make_depth1_fixture.py`: an invented R6-shaped fixture, `python3 -I make_depth1_fixture.py <out dir> [seed] [edge]` (1,488 windows over both markets; seed 5; edge 0.0 = no edge anywhere, edge 0.30 = Bitcoin's result follows the touch imbalance at the look).
- `DEPTH1_SECOND_OUTPUT_fixture_seed5_no_edge_MADE_UP_DATA.json`, `DEPTH1_SECOND_OUTPUT_fixture_seed5_edge030_MADE_UP_DATA.json`: this build's output on both.

On the no-edge fixture: 534 gold and 521 Bitcoin windows with a decision poll, 806 fired windows of which 3 have no yes or no result (booked fee-only, under the 1% stop), verdict FALSIFIED. On the edge fixture the planted features pass the shuffled-book control and print profit factors well above 1; none meets the whole bar (one is short of 300 trades, one short of z 5.27), so the verdict is again FALSIFIED: both fixtures exercise the counts, the booking, the blocks, halves, z, the control and the verdict line.

## The 18 places where the text leaves a choice

They are listed at the top of `depth1_second.py` and printed with every run. The ones most likely to make two builds print different figures:

1. **Time anchors (4, 5, 6, 7).** The decision poll is the last poll in [T-490 s, T-480 s]. This build measures the 30 s and 60 s lookbacks, the 60 s tape window and the fill (first poll at or after decision + 1.0 s, within 20 s) from the DECISION POLL's own time, not from T-480 s. With 2 s polls the two readings pick different polls about half the time.
2. **Coverage times against T (2).** `first_recv_ms` and `last_recv_ms` are local receive times; this build adds the run's clock offset before comparing them with T-545 s and T-470 s.
3. **A ticker in two runs (3).** One window counts once: the usable coverage row with the most `ok_polls`, and that run's book rows only.
4. **The z (14).** Cluster-robust on US Central close dates: mean net over sqrt(D/(D-1) x sum over dates of (date sum - date n x mean)^2)/n. The plain t of daily sums is printed beside it. The registration says "date-clustered z" and gives no formula.
5. **Halves (13).** Trades in close-time order, first floor(n/2) and the rest.
6. **The shuffled-book control (15).** One permutation of the windows a market and round; the whole vector of 10 feature values moves together; the window keeps its own fill quotes and result. Two builds cannot share random draws, so the 99th percentile can only be compared approximately (on the no-edge fixture it is about 7c a trade here).
7. **f6 (9), f8 (10), f10 (11)**: the exact reading of the thin side, the missing second level and "within 0.03".
8. **Not built here (16, 17):** Bitcoin's OICORE overlap mark needs candles (every Bitcoin window is "unknown" in this build) and the history check on candles is not part of the verdict.

## First comparison with the wrapper (2026-11-13): 18 of 20 tries identical on every figure; one FAULT found

Desk A ran the wrapper on both fixtures (its output: `desk_a_verify/DEPTH1_FIXTURE_OUT_edge0.txt` and `..._edge030.txt` at c499f3f6 on `claude/idea-desk-a`) and said, as readings, where V2's code differs from this build. The wrapper and `depth1.py` were still not read here; the differences below were found from the two outputs and from variants of this build only.

### Readings where the first build differs from the text as this build first read it (now aligned; none looks like a fault, each wants a line in Desk A's clarifying amendment)

1. The coverage row's `first_recv_ms` and `last_recv_ms` are compared with T-545 s and T-470 s raw, with no clock offset.
2. A window that opened (close minus 900 s) at or after the recorder's end, 2026-11-13T23:59Z, is dropped. Not in the registration's usable-window sentence; the date is a CONFIG constant. (It matters on real data: R6 was extended for Bitcoin to Nov 20, so Bitcoin windows after that instant exist.)
3. A window with a decision poll is a scored window even if that poll's book is one-sided or empty.
4. The imbalance features need BOTH sides quoted at every poll they use (the decision poll and the lookback poll).
5. Direction accuracy is wins over all trades (a fee-only no-result trade is a miss).
6. **The date-clustered z has no small-sample factor:** sum of nets over sqrt(sum over dates of (date sum minus date n x mean)^2). With the usual D/(D-1) factor on the variance it is smaller by sqrt((D-1)/D): 3.4% at 15 dates, so the first build's 5.27 is 5.09 on the corrected scale. A choice the registration does not state; for the Head to rule, since it moves the bar's meaning by 3.4%. This build prints both.
7. The no-result count's raw values are counted per window.

### With those aligned and this build told to trade on ANY non-zero float (`ZERO_TOL = 0.0`)

On both fixtures, **18 of the 20 tries agree on all 15 figures each (270 of 270): n, profit factor pooled and in each block with the block's n, both halves, net in cents, stress profit factor, accuracy, mean ask and z.** Scored windows 539 gold and 520 Bitcoin, 3 no-result fired windows (2 empty, 1 void), verdict FALSIFIED on both fixtures: identical. The shuffled-book control's 99th percentile is 6.59c here against 6.70c there on the no-edge fixture (different random draws; Desk A is to write the exact procedure and generator so it can be reproduced digit for digit).

The two tries that differ are `f3_dwmid_minus_mid` in both markets (276 against 296 trades, 269 against 289). See the fault.

### FAULT: three features place trades on floating point residue when the registered feature is exactly zero

The registered sign rule: "feature > 0 buys YES, < 0 buys NO, 0 or undefined: no trade". Several features are differences of two quantities that are often EQUAL: the two second-level gaps (f8), the two slopes (f9), the weighted mid and the plain mid (f3). Computed in floating point, an exact zero comes out as a residue near 1e-17 for many prices, and the first build then trades on its sign.

- **Proof from the outputs.** With a zero tolerance of 1e-12 this build has 202 gold and 211 Bitcoin f8 trades on the no-edge fixture; with the tolerance off it has 251 and 259, which are exactly the wrapper's counts, with every other figure of those tries identical. So 49 of gold's 251 f8 trades and 48 of Bitcoin's 259 (19%) exist only because of residue. f9: 3 of 266 and 1 of 271. f3: this build has 7 and 6 residue trades and the wrapper 20 more than that in each market; five equivalent ways of writing f3's arithmetic give this build anything from 269 to 281 trades, so f3's count depends on the order of the arithmetic.
- **Why it matters on real books.** A liquid 1c-tick book usually has its second level 1c behind the touch on BOTH sides, so f8's two gaps are equal and the registered feature is zero: no trade. On invented whole-cent books of that shape (spread 1c to 4c, every price pair), the raw float value is non-zero for 154 of 378 pairs (41%), and its sign is tied to the price: when YES is the favourite it buys NO 61 times of 77, and when NO is the favourite it buys YES 61 times of 77. So the residue trades are a bet on the CHEAPER side four times in five. The registration says of this card "It is never scored as cheap side late". An f8 result on real data would be partly that bet.
- **What it is not.** Not look-ahead: nothing after the decision is used. It cannot be told from the fixture whether it would help or hurt f8; it is a trade the registered rule does not make.
- **Fix, for the Head and Auditor B to rule (a new audited hash before the read):** every feature whose absolute value is at or under a stated tolerance (1e-12 here) is zero, in the wrapper's patch or in the features; or f8 and f9 are computed in whole ticks. After that fix the two builds should agree on f3, f8 and f9 as well (this build's figures under the registered rule are in the `..._registered_zero_rule_...` files).

## Second comparison, after Desk A's Amendment 2 and the Head's rulings (2026-11-13): the same output on both fixtures

Amendment 2 (`DEPTH1_AMENDMENT_2_DESK_A.md`, 61a1258d on `claude/idea-desk-a`) states what the frozen first build does at each open place, and the Head ruled that those choices stand as coded. This build (sha256 `607ed616...`) now follows it: raw coverage receive times; the recorder-end condition; a decision poll counts without a level-1 quote; both sides needed for the imbalance features; the tape window open at the start and closed at the end; accuracy over all trades; the z with no small-sample factor (the corrected one printed beside it); only an exact 0 is "no trade"; gold with no poll at T-360 s is "not held"; and the registered shuffle (numpy `default_rng(20261114)`, one permutation a try in the order gold f1 to f10 then Bitcoin f1 to f10, 1,000 rounds, 99th percentile linear).

**Against the wrapper's output (c499f3f6) on the no-edge and the planted-edge fixture:**

- **300 of 300 per-try figures identical on each fixture** (20 tries x n, profit factor pooled, profit factor and n in each block, both halves, net, stress profit factor, accuracy, mean ask, z).
- **The control p and PASS or fail identical for all 20 tries on each fixture**; gold's without-held n and profit factor identical.
- Scored windows 539 and 520, fired windows 802, no-result fired windows 3 (2 empty, 1 void), the noise description (all six features, both markets, shares and looks), the median fill delay, and the verdict FALSIFIED: identical.
- **The control's 99th percentile: 6.7010c here against the wrapper's printed +6.70c; 6.6833c against +6.68c.** Its median: 2.4722c against +2.47c on the no-edge fixture, and **2.2933c against a printed +2.30c on the planted-edge fixture**: the one figure not yet confirmed. Desk A is asked to print the control to four decimals; if the bests of a round or two differ, that is a reading still to find.

Two things had to be found from the numbers because the text could not tell them:

1. **f3's summation.** Written as a plain running sum, f3 gives 276 gold and 269 Bitcoin trades on the no-edge fixture; written with numpy array sums (the same formula) it gives the wrapper's 296 and 289 exactly. The 20 extra trades a market are floating point residue from the order of addition, turned into trades by the exact-zero rule.
2. **The noise description**: a look is any window whose feature is defined and not zero; a change is the opposite non-zero sign at either of the next two polls by order.

### The residue trades, counted (the Head's request; information, never part of the verdict)

Fired trades whose feature is within 1e-12 of zero but not exactly zero, on the invented fixture (the same on both fixtures):

| Try | Trades | Of which residue | Residue trades that bought the cheaper side / the dearer side (ask not 50c) |
|---|---|---|---|
| Gold f8 | 251 | 49 (20%) | 36 / 11 |
| Bitcoin f8 | 259 | 48 (19%) | 38 / 10 |
| Gold f3 | 296 | 27 (9%) | 14 / 13 |
| Bitcoin f3 | 289 | 26 (9%) | 7 / 19 |
| Gold f9 | 266 | 3 | 3 / 0 |
| Bitcoin f9 | 271 | 1 | 0 / 1 |

All other tries: 0. On f8 the residue side is not a coin flip: 74 of 95 on the cheaper side (78%), as the whole-cent arithmetic above predicts. On f3 it leans the other way in Bitcoin. The fixture's books are invented (random level counts and sizes), so the SHARE of residue trades on real books is not known from this; on a real 1c book with full levels on both sides f8's two gaps are equal most of the time, so the share could be far higher than 20%. This build prints the count for each try at the read.

### (d) is the looser reading, not the stricter one

Amendment 2 and the ruling say the first build's z, with no D/(D-1) factor, is the smaller and stricter of the two. It is the larger: z_corrected = z_first_build x sqrt((D-1)/D), 0.966 at 15 dates. On the no-edge fixture this build with the factor printed -1.17, +1.45 and -3.64 where the first build prints -1.21, +1.50 and -3.77. A first-build z of 5.27 is 5.09 corrected. Reported to the Head on Nov 13; this build prints both.

## Third comparison, after the fault fix (Amendments 3 and 4): the same output on three fixtures

The Head ruled both points raised above: the zero rule was a fault and the uncorrected z the looser reading. Desk A fixed them in a new audited wrapper (Amendment 3: an absolute feature value at or under 1e-12 is zero for all ten features; the verdict reads the corrected z, variance times D/(D-1), with the uncorrected one printed beside it), and Auditor B's scan of the frozen code then found two exact-tie cases fixed in Amendment 4 (the profit factor and net bars are tested in whole thousandths of a dollar; f6's thin-side comparison treats sums within 1e-9 as a tie). Wrapper sha256 `75385906...`. This build (sha256 `3db8b6df...`) was changed to the same text, from the amendments only.

| Fixture (invented rows) | Per-try figures | Z BESIDE | Zero-rule counts | Control 99th percentile / median | Noise lines, scored windows, fired and no-result counts | Verdict |
|---|---|---|---|---|---|---|
| No edge, seed 5 | 360 of 360 | 80 of 80 | 20 of 20 | 7.0468c / 2.5972c here; +7.05c / +2.60c there | identical | FALSIFIED both |
| Planted edge 0.30, seed 5 | 360 of 360 | 80 of 80 | 20 of 20 | 7.0265c / 2.4768c; +7.03c / +2.48c | identical | FALSIFIED both |
| Tie fixture, seed 5 (run through Desk A's harness by this desk, wrapper not read) | 360 of 360 | 39 of 40 | 20 of 20 | 1.1746c / -0.9294c; +1.17c / -0.93c | identical | NOT_YET_FALSIFIED both |

"Per-try figures" are, for each of the 20 tries: n, profit factor pooled, profit factor and n in each block, both halves, net, stress profit factor, accuracy, mean ask, the corrected z, the control p, PASS or fail and (gold) the without-held n and profit factor.

**The tie fixture** (`make_depth1_tie_fixture.py`) plants the two cases Amendment 4 fixes. Bitcoin f7 has a profit factor of exactly 1.5 in whole cents, pooled and in every block (260 wins of +0.48 and 160 losses of -0.52 a block); in floating point the pooled figure reads 1.4999999999999998. Both builds print `BAR MET` for it, with identical lines (n 1260, 1.50 in every block, net +9.90c, z 70.28, control p 0.001). Five gold windows have 60-second-old size sums of 0.10 + 0.20 against 0.30; both builds give f6 no trade there (gold f6 n 1367 in both).

**One figure differs, information only:** on the tie fixture the wrapper prints an uncorrected z of -4053239664633446.00 for gold f8, a try with five trades that all fall on one date; this build prints 0.00. With one date the cluster variance is zero, and the wrapper's "variance 0 gives 0" test on the uncorrected figure is an exact comparison that a floating point residue slips past. The corrected z, which the verdict reads, is 0.00 in both builds there (D under 2 gives 0). It cannot arise on a try with 300 trades over 15 dates, so it changes no verdict; it is the same class of exact-zero test and wants one line of text or a guard.

The earlier open point (the control's median on the planted-edge fixture) is closed: under Amendment 4 both control figures agree at printed precision on all three fixtures.

### Last notes applied (Desk A's dated note under Amendment 4, f8858783; the Head's grid check)

- f3's weighted sums are a plain left-to-right sum, as in the first build (the order no longer changes any count under the 1e-12 rule).
- Gold's overlap mark: no poll at T-360 s within 10 s is "unknown"; a poll with a missing side is "not held".
- **Grid check, printed by this build at the read (information):** how many level-1 bid prices and how many fill prices are NOT on the 0.001 grid. Whole thousandths of a dollar are exact only on that grid; if either count is not zero, both builds recompute the bars in exact fractions before any verdict is recorded. On the fixtures both builds count 0 (Desk A's `depth1_grid_check.py`: 195,200 and 404,736 book rows read; this build: the same rows, 0 off the grid, and 0 of 5,099 and 0 of 12,744 fill prices).

With these applied the three-fixture match is unchanged: 360 of 360 per-try figures on each, the control at printed precision, and the one information-only figure (the uncorrected z of a one-date try) still the only difference. `depth1_second.py` sha256 `0092b363...`.

## Files added

`DEPTH1_SECOND_OUTPUT_fixture_seed5_{no_edge,edge030}_A4_MADE_UP_DATA.{json,txt}` and `DEPTH1_SECOND_OUTPUT_tie_fixture_seed5_MADE_UP_DATA.{json,txt}` (this build under Amendments 1 to 4); `DEPTH1_WRAPPER_OUTPUT_tie_fixture_seed5_MADE_UP_DATA_run_by_forensics.txt` (Desk A's harness run on the tie fixture); `make_depth1_tie_fixture.py`. `depth1_second.py` sha256 `0092b363...`.


## Nov 13, about 02:05Z: the gold overlap mark aligned to the first build (Desk A's note of 01:16Z)

- **What changed, one line of `depth1_second.py`:** at the poll at T minus 360 s, a missing side has no ask and is "not in band"; if the other side's ask is 0.88 to 0.97 the
  window is HELD. Before, my build called any poll with a missing side "not held". No poll within 10 s of T minus 360 s is still "unknown" in both builds.
- **It is information only:** the mark feeds the "without windows L1 / OICORE holds" split, not a verdict line.
- **Re-run on the three made-up fixtures:** every printed figure is unchanged (the no-edge and edge outputs are byte for byte the same; the tie fixture's 20 try lines are
  the same). No traded gold window in the fixtures has that case, so the fixtures do not exercise the change; it is aligned by reading, not by a test.
- **New hash of my build:** `93212179...` (was `0092b363...`). The wrapper is untouched (`75385906...`).
- **The Head's ruling on the one-date z (01:16Z):** a sentence, no guard. Any z that differs between the builds or is larger than 1,000 in size is recomputed exactly by both
  before anything is recorded.
