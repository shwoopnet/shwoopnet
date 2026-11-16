# In-game counters: hand case (History Miner, Nov 16, 2026 ~18:40Z, before any run; the Head's 18:22Z order, Auditor B's rulings of 17:22Z)

Three counters, all COUNTS ONLY (no result, no outcome, no price figure printed):
1. cadence_by_hour: for ingame obs rows of the dates given, same-ticker gaps by UTC hour: pairs, pairs of 60 s or less, pairs of 25 s or less. It reads ONLY columns 0 (t_recv_ms) and 4 (ticker); no price column is touched. Auditor B accepted this as a timestamp count (17:22Z). Any date may be given.
2. fade2_signals: IGFADE2 decisions (a pair of one ticker's polls no more than 60 s apart, both two-sided, mid move of 0.10 or more, the fallen side's ask 0.15 to 0.60) per UTC day, per league and kind. It reads prices, so it has a wall: rows with t_recv_ms before 1794873600 (2026-11-17T00:00Z) or at or after 1797292800 raise on any column but the first (time first), and the ticker wall is the signed six series. Output is a label: "provisional, fewer than 7 tip days, not the stored gate" until 7 distinct days exist.
3. latedrift_signals: IGLATEDRIFT1 decisions per UTC day from loader events (the forward loader, after the results listing exists, because the tip comes from the schedule field); no spreads.
Neither signal counter publishes any price, result or edge; they print decision counts only. They import the signed ingame_events.py (4698bae0, pinned).

Hand case (invented rows):
- Gaps for ticker A at seconds 0, 20, 140, 160 in hour H, and 3,600 + 10 in hour H+1: pairs in hour H: 3 (20, 120, 20), of which 2 are 60 s or less and 2 are 25 s or less; the pair 160 to 3,610 spans the hour boundary and is counted in H+1 (its later poll's hour): 1 pair, 0 of 60 s or less.
- fade2: ticker T rows (t 0: 0.40/0.42), (t 30: 0.52/0.54) on day D: one decision on D, kind total, league NHL. Gap 70 s: none. A move of 0.08: none.
- A row at t_recv 1794873599000 passed to the signal counter raises on any column but the time.
- latedrift: the loader event of the IGLATEDRIFT1 hand case (T + 5300: 0.40/0.42, T + 7100: 0.50/0.52) gives one decision on the tip day; a spread event gives none.
