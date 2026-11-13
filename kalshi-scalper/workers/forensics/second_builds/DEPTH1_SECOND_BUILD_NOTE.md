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

## Next

Desk A runs the wrapper on the same fixture (or says how to, without this desk reading the wrapper) and the two outputs are compared figure by figure: windows per market, the usable-condition counts, per try n, wins, no-result count, profit factor pooled and by block and half, net per trade at both fees, z, the control and the verdict.
