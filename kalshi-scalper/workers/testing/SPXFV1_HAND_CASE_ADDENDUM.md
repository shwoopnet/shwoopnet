# SPXFV1 hand case addendum (Testing Desk, Nov 13, 2026): committed BEFORE the code change for the Head's rulings of 16:51Z to 16:53Z. Made-up numbers; test_spxfv1.py must reproduce each.
Adds to SPXFV1_HAND_CASE.md (b8d69d3f, unchanged). Nothing here comes from a landed file.

1. Duplicate ts_event: two ES rows on the bar at C - 180 for window W stop the run; the message names window W.
2. Odd result text (anything but yes, no, void; for example "scalar") on a window inside the block being read stops the run, naming the window. An empty result also stops it.
3. Ties are counted over every valid-quote window before the spread and band tests (W9 of the hand case: bid .49, ask .51: ties = 1).
4. Unrounded PF decides every kill and bar: 100 wins of +0.10 and 100 losses of -0.10004 (n 200) give PF 0.9996, which prints 1.0 and is KILLED (cash PF under 1.0 at n of 100 or more). 50 wins of +0.07498 and 100 losses of -0.025 give PF 1.4996, which prints 1.5 and is BAR NOT MET.
5. Labels (n at least 150, no kill flag set): "BAR MET (not a research-bar pass)" when the pooled PF and each of the three time-span thirds have unrounded PF at or above 1.5; "RESEARCH BAR MET" only when that holds AND the event-clustered z (scorekit: mean of per-event mean nets over its standard error) is at or above 5.46. Hand figure: 150 trades in 150 events, nets (+0.3, +0.3, -0.1, -0.1, -0.1) repeated 30 times: mean 0.06, sd (n - 1 form) 0.19662, z = 0.06 / (0.19662 / sqrt(150)) = 3.737: BAR MET, not the research bar. The same 150 trades pooled into 5 events of 30 (one mean net 0.06 each, sd 0): z undefined (sd 0), so not the research bar either.
6. Under 100 traded: "no evidence at n = x". 100 to 149: NOT_ENOUGH_DATA (plus KILLED if PF under 1.0).
7. Held-out read: a local marker file is written before any output; a second run refuses on it.

CLOSED UNREAD 2026-11-13, family declined; no value opened
