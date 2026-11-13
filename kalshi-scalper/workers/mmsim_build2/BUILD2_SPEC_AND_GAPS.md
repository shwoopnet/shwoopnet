# MMSIM1 build 2 (independent Rule P build): reading of the text, gaps, and hand case. Idea Desk B, Nov 13, 2026, written 19:56Z by this desk's clock.
Written from MMSIM1_PROTOCOL.md (sha256 e800152f, with Amendments 1 and 2) and MMSIM1_AMENDMENT_3.md (sha256 cb681eae) ONLY. I did not read `mmsim1.py`, Desk A's port, `mm_probe_prio2.py` or `mmsim_rederive.py` (the Head's order). I read the recorder's column layout (`scripts/record_book.py`). DEVELOPMENT events only: the loader keeps only rows of events closing before `PINNED_CUTOFF = 2026-11-07T15:00:00Z`, and it refuses any file dated after 2026-11-08. No data has been read.

## The rule as I read it (the part the text fixes)
Per hourly event (close time T, from the `close_time` column) and per recorded strike (a ticker), per side:
- **Post:** at the first book poll at or after T-50 min, one contract at that side's best bid (YES side: `yes_bid_px_1`, NO side: `no_bid_px_1`), queue ahead = the size at that price (`yes_bid_sz_1` / `no_bid_sz_1`). Never repriced; cancelled at T-15.
- **Fill, Rule Q:** a YES bid at p fills when cumulative contracts traded at yes price p by takers with `taker_outcome_side` "no" after the post time reach queue + 1; a NO bid at q fills when cumulative contracts at yes price 1 - q with taker side "yes" reach queue + 1.
- **Fill, Rule P:** at OUR price, at the EARLIEST of (1) the Rule Q condition; (2) a taker print through our price (YES bid at p: taker "no" at a yes price strictly below p; NO bid at q: taker "yes" at a yes price strictly above 1 - q), `created_time` after the post time and not after T-15; (3) the first book poll after the post and before T-15 at which that side's best bid is below our price or absent.
- **At T-15:** unfilled orders cancelled; a strike with exactly one filled leg sells it at that side's best bid (taker fee 0.07 x s x (1 - s)); a strike with both legs filled is held to settlement and pays exactly 1 (cost = the two fill prices).
- **Maker fee:** 0 and 0.0175 x p x (1 - p) per filled leg (p the leg's own price). Event P&L = the sum over its strikes; PF = sum of positive event P&Ls over the absolute sum of negative ones; events counted from the first posted order.

## Text gaps (each needs a dated amendment request; until ruled, build 2 uses the stated DEFAULT, switchable by a named option, and the figures are labelled with the option)
| # | Gap | Default in build 2 | Why it matters |
|---|---|---|---|
| G1 | Which strikes are the "7 recorded strikes" when the recorder's set can differ between files of one event (the recorder picks the 7 nearest 50c at discovery) | every ticker present in the event's book rows, in file order | the reproduction count (1,113 strikes) |
| G2 | The clock for "post time" and for book poll times: `server_date_header` (seconds) or `poll_ts_local_ms` (local, ms); trades carry the exchange's `created_time` | `server_date_header` | trade vs post ordering within a second; skew |
| G3 | A side with no bid at the first poll at or after T-50: no order (first poll only) or post at the first later poll with a bid | no order (literal "first book poll") | number of orders |
| G4 | "After the post time": strict or inclusive for a trade with the same timestamp | strict (created_time > post) | edge |
| G5 | The time of a Rule Q fill: the trade's `created_time` or the poll that shows it ("fills are timed to the poll that shows them", protocol) | `created_time` | the T-15 cut and the "earliest of" in Rule P |
| G6 | The T-15 sale "at that moment": first book poll at or after T-15, or the last one before | first at or after | sale price |
| G7 | No bid on that side at the T-15 poll | sale price 0, no fee (the leg is lost) | tail losses |
| G8 | Rule P (3) "absent": the row exists only if at least one side has a bid (the recorder drops empty books); a side is absent when its level 1 is empty on an existing row | as stated | frequency of cond 3 |
| G9 | Fee rounding for the "rounded up to the cent" report: each maker leg and each taker sale separately | each separately | the rounded PF |
| G10 | The 10 contract report: queue and fill rule for a 10 lot (partial fills? queue + 10?) | NOT implemented | cannot report it |
| G11 | "Quotable": at least one posted order in the event | as stated | 168 of 171 |
| G12 | "Fractional-size share of the fills" (Amendment 2): the filling trade's `count_fp` non-integer; a book-condition fill has no trade | share of fills (Rule Q and Rule P cond 2) whose filling trade is fractional; cond 3 fills counted apart | the extra report |
| G13 | "Daily results": which day (UTC or Central) | event close date in UTC | positive-mean test |
| G14 | Ties in the trade tape (same created_time) and trade-id order | by created_time then trade_id | cumulative queue |
Not built here: the gold correlation clause (needs live nightly report data).

## Hand case (made up; expected figures written by hand and committed BEFORE the build is run)
One event E1, close 2026-11-01T15:00:00Z (T-50 = 14:10:00Z, T-15 = 14:45:00Z), two strikes; plus E2 closing at the cutoff, which must be DROPPED at load unread.
- **K-A** (book polls on the server clock): 14:10:00 YES px1 0.40 size 5, NO px1 0.55 size 3; 14:20:00 YES 0.40 size 5, NO 0.54; 14:45:00 YES 0.38, NO 0.56. Trades: 14:15:00 taker "no" at yes price 0.40 count 6.0; 14:30:00 taker "yes" at yes price 0.45 count 2.0.
- **K-B**: 14:10:00 YES px1 0.60 size 2, NO empty; 14:45:00 YES 0.58. Trades: 14:30:00 taker "no" at yes price 0.59 count 1.0.
