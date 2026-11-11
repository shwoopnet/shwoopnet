# BFLY2 (registered Nov 11, 2026, BEFORE any true settlement result is read and BEFORE any episode is scored; research only, no live change)
Follow-up of the LADBFLY1(b) LEAD (`workers/LADBFLY1_XSER1_PROTOCOL.md`, results commit 333cbd23). Script `src/scalper/bfly2.py`. Data: `book/` on `origin/quote-data`, KXBTCD hourly ladder, 7 strikes nearest the money, top 5 YES and NO bids with sizes, every 3 s, Oct 29 to Nov 11 2026 15:59 UTC (261 events; no new events exist since LADBFLY1 was read). Only event counts and the snapshot structure were looked at to fix the split (no credit, no P&L, no outcome). Declined-list check (`docs/STRATEGY_LIFECYCLE.md` 7e): not a favourite-and-hold, not a gold or L1 variant, no row matches; it is a defined-structure 4-leg spread held to settlement on the hourly Bitcoin ladder. It still holds to settlement, so by 7d it counts as a different exit only if its entry rules differ and it hedges nothing live: it trades only the hourly KXBTCD market, which no live strategy touches.

## The rule (exact, fixed now)
- Structure: a 1 contract butterfly = buy YES K1, sell YES K2 twice, buy YES K3, ADJACENT recorded strikes with K2-K1 = K3-K2 = 100 (tolerance 0.011; the 250, 200 and 500 gaps are not used). Settlement payoff 1[S>=K1] - 2*1[S>=K2] + 1[S>=K3]: 0 below K1, +1 in [K1,K2), -1 in [K2,K3), 0 at or above K3. Cash P&L = credit - fees + payoff, with each leg's payoff from that strike market's TRUE result.
- Snapshot: as LADBFLY1 (rows of one event within 2 s, new cluster after a 1.5 s gap).
- Window: snapshots 55 to 10 minutes before the event's close_time (inclusive).
- Qualifying: for any triple at that snapshot, with the decision fill (below, first snapshot only, no haircut) the net credit after rounded fees is at least 1.0 cent per butterfly (THRESH 0.01, fixed, not tuned). If several triples qualify take the largest net, ties the lowest K1.
- ONE episode per event: the FIRST qualifying snapshot in the window; nothing else in that event is traded.
- Events with no known true result (not settled in the API, or the call fails) are left out and counted; the choice is never made on an outcome.

## Fill model (honest 4-leg, size 1 contract)
- Each leg takes the best price AFTER consuming depth (top 5 levels): buys at 1 - NO bid levels, sells at YES bid levels; K2 is one order of 2 contracts, K1 and K3 are 1 contract orders. A leg that cannot be filled in 5 levels disqualifies the triple.
- All legs are sent at the same snapshot time t. The realised fill per leg is the WORSE of the book at t and at the next snapshot (about 3 s later, same event, within 6 s, strike present; if there is none the t book is used and the episode is flagged).
- Fee per order: ceil to the cent of 0.07 * contracts * p(1-p) at that leg's average price (primary, "rounded"); also reported unrounded. Cash basis, hold all legs to settlement, no exit.
- The 3 s haircut is the only latency model; our own order does not move the book in this model (size 1, resting depth median about 150, so small).

## Split (fixed by event close time, over the 254 eligible events with a snapshot in the window)
- Development: first 169 events (two thirds), closes 2026-10-29T11:00Z to 2026-11-07T14:00Z.
- Held-out: the last 85 events, closes 2026-11-07T15:00Z to 2026-11-11T15:00Z. Read ONCE, only if development passes every gate. Events recorded after this read (closes after 2026-11-11 16:00Z) are a reserved forward set, never used in this read.

## Gates (development, all required)
1. At least 100 events with an episode and a known true result. If the data cannot give 100: NOT_ENOUGH_DATA and the date when 100 will exist (about 24 events a day at the observed rate, so the date is computed from the count).
2. Cash profit factor (sum of event wins / sum of event losses, 1 contract, rounded fees, haircut) at least 1.5. With zero losses the PF is infinite and is NOT a pass on its own.
3. Tail gate (the structural-risk gate): the one-sided exact (Clopper-Pearson) 95% UPPER bound of the event loss rate must be below the break-even loss rate (mean win / (mean win + mean loss magnitude) from development). With a break-even rate near 4% it takes about 25 events per expected loss: 169 events expect about 6.8 losses at break-even, so zero losses would be a real finding and one loss is not evidence the tail is covered. The count of losing events, the worst loss and the worst-loss share of gross losses are stated.
4. Mean cash per event is positive after rounded fees with the haircut.
5. Deflation (reported, with the skew caveat): event-mean t versus the bars z 5.34 (N 1,100,000 + 1 test) and z 4.39 (N 8,795 + 1). A t-statistic on this skew is not reliable; gate 3 is the binding one. The number of tests tried here is 1 primary (+ the unrounded fee and no-haircut figures, reported as sensitivities, not alternatives).
Held-out gates (same 2 and 4, plus: loss rate not above the development break-even rate, and PF at least 1.5). Held-out has about 85 events, so about 3.4 expected losses at break-even: a held-out with zero or one loss cannot clear the tail alone, and a pass there needs the forward set.

## Also reported (information, not gates)
- Inferred (LADBFLY1: last snapshot) outcome versus true outcome, per strike of every event used: mismatches listed.
- Daily cash P&L correlation versus the live L1 favourite-late proxy: needs at least 20 overlapping days; development spans 10 days, the whole record 14, so it is NOT computable under the 7d rule; stated as such.
- Structural risk, stated now: this is a SHORT bet on a narrow gap (the 100 dollar band between K2 and K3), a small win about 96% of the time and a loss of about 96c otherwise (negative skew). The PF can look huge until the first loss, and a clean sample of this size does not exclude a loss rate of a few percent. Also the 4 legs' 4 rounded fees take a big part of the edge.

## Rules ONLY IF everything fully passes (development, held-out and a forward set that has seen at least one expected loss worth of events)
- IMPLEMENT: recommend one owner popup for a shadow-only 1 contract slot (never live before the owner's written approval, never sized by the gold ladder, own $ cap of a few contracts).
- KILL: any shadow loss rate above 8% over the first 50 events, or cumulative shadow cash below 0 after 100 events, or a measured fill worse than the haircut by more than 1 cent a leg.
- RETURN to research: the held-out or forward set has zero losses but fewer than 75 events, or fills are unmeasured.
