# PROVEN-bar read for OICORE, second build: hand case addendum (Testing Desk, Nov 13, 2026), committed BEFORE the code change for the Head's 19:22Z ruling
Supersedes the per-window n >= 100 of PROVEN_OICORE_HAND_CASE.md (0fb56893). Invented rows only.
1. The bar is 100 fills IN TOTAL, split into 3 windows by fill order; PROVEN if at least 2 of the 3 windows are at cash PF 1.3 or better (unrounded, inside 1e-9). The windows are NOT 100 each: there is no per-window n minimum. Total n under 100: NOT_ENOUGH_DATA (windows still printed with their n beside the PF). Otherwise PROVEN or NOT YET with the figures.
2. Set A (300 rows, windows 1.5195, 1.1818, 1.3788): PROVEN, unchanged.
3. Set C (299 rows, windows of 99, 100, 100 at 1.5415, 1.5195, 1.1818): the 99-row window now COUNTS: 2 of 3 at 1.3 or better: PROVEN (it was NOT YET under the withdrawn per-window rule).
4. 99 rows in all (windows 33, 33, 33, every window at PF infinity): NOT_ENOUGH_DATA. The same rows with a 100th row: PROVEN.
5. An empty input: NOT_ENOUGH_DATA (n 0). A window of 5 rows with PF 2.0 counts as a window at 1.3 or better.
6. The exclusion counts are always printed, zero included: excluded_unreadable_fill_or_fee (avgFill or avgFee unreadable) and excluded_exit (result 'exit'; OICORE holds, so 0 is expected), plus the other buckets.
