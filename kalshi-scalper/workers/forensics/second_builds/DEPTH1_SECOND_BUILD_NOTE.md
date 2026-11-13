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

## Files added

`DEPTH1_SECOND_OUTPUT_fixture_seed5_{no_edge,edge030}_registered_zero_rule_MADE_UP_DATA.{json,txt}` (zero tolerance 1e-12, the registered sign rule) and `..._like_for_like_any_nonzero_float_MADE_UP_DATA.{json,txt}` (tolerance off, to compare with the first build as it stands). `depth1_second.py` sha256 `0872493a...`.

