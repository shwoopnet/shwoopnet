# S3 feasibility count: hand case and the threshold, written BEFORE the reader code

Head's request (Nov 14, 2026): before S3's Nov 26 read, count per day how many combos are two-sided (rule 18) inside S3's registered entry band, counts only, no result field read, reader audited by Auditor B before it runs.

## Threshold, fixed now (before any run)
S3's would-be fills per full day, counted exactly as S3 would fill them (the registered band, size, volume, legs and time-to-close rules, one per combo ticker and per event, at most 10 a snapshot, entries from 2026-11-13T00:00Z). A FULL day is a UTC day with at least 40 snapshots (of the 48 at a 30 minute cadence). Over the full days from 2026-11-13 on:
- fewer than 3 full days: "not decided yet";
- the average would-be fills per full day under 5: S3 closes as "no evidence: combos cannot be priced" without the Nov 26 read;
- 5 or more: S3 continues to its registered read.
The number 5 is the Head's suggestion and is not tuned to any count.

## What the reader reads
Only from each snapshot row: t_recv_ms, ticker, event_ticker, close_time, yes_bid, yes_ask, no_ask, yes_bid_size, volume and legs. It never opens results.csv.gz and never reads a result. It prints counts only, per day: snapshots, rows, two-sided rows (rule 18: 0 < yes_bid < yes_ask < 1 and a posted no_ask), rows that qualify before the one-per rules, and would-be fills.

## Made-up fixture (fixture_MADE_UP_DATA, written by make_fixture.py) and expected output
Snapshots: 2026-11-12T12:00Z (1 row, a qualifying combo C15, must be IGNORED: before the start), 2026-11-13T12:00Z (A: C1 to C10), 2026-11-13T18:00Z (B: C1 and C11), 2026-11-14T12:00Z (C: C13 and C14).
- A: C1 qualifies (p = .73, size 5, volume 3, 3 legs, closes in 24 h); C2 the same but the same event as C1; C3 has yes_bid 0 (not two-sided); C4 p = .91 (over the band); C5 size 2; C6 volume 0; C7 31 legs; C8 closes in 30 minutes; C9 closes in 15 days; C10 qualifies (p = .81, 2 legs, closes in 7 days).
- B: C1 again (already filled once, so no new fill) and C11 (p = .61, qualifies).
- C: C13 qualifies; C14 is crossed (yes_bid .30 above yes_ask .28), not two-sided.
Expected per day (rows, two-sided, qualifying before the one-per rules, would-be fills):
| day | snapshots | rows | two-sided rows | qualifying rows | would-be fills |
|---|---|---|---|---|---|
| 2026-11-13 | 2 | 12 | 11 | 5 | 3 (C1, C10, C11) |
| 2026-11-14 | 1 | 2 | 1 | 1 | 1 (C13) |
Ignored: 1 snapshot, 1 row before 2026-11-13T00:00Z.
With the full-day floor lowered to 1 snapshot (the fixture flag): 2 full days; with fewer than 3 full days the verdict is "not decided yet". With the floor at 1 and a third made-up day not present the average of 2 days is 2.0 (under 5), but the 3-day minimum still applies; a flag --min-days 2 gives "no evidence: combos cannot be priced (average 2.0 a day)". With the default floor of 40 snapshots no fixture day is full: "not decided yet (0 full days)".
