# Frozen definition sheet: three OIVER shadow places on Bitcoin, beside OICORE (7g versions). Idea Desk A, Nov 13, 2026.
Written at the Head of R&D's order of 21:17Z (the owner: more shadow strategies to test). A NEW file; `DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md` is not touched. Same pattern as the NC15 wheel sheet: every item is closed here; a place counts forward only from the COMMIT TIME of this file; a decision instant earlier than that commit does not count; **any later edit, however small, RE-DATES all three places** to the commit time of that edit. Auditor B's "closed" dates each place. Nothing here reads an outcome.

## 0. What a place is (7g)
Each place is a VERSION of OICORE, not a new strategy: it takes no seat, spends one try each (N +1), and is logged AGAINST THE PARENT. The parent is OICORE exactly as in `DESK_A_OICORE_VERSIONS_NOV13.md` (Bitcoin 15 minute, cheaper side 0.08 to 0.50, open interest rise >= 86,300 inclusive over the candle ending close - 180 s minus the one ending close - 360 s, no slip, limit = the ask seen, held to settlement). A version trades a subset of the parent's signals, so every parent signal is logged once and each place records pass or skip with its reason. Shadow size is 20 contracts (the scorers' C); no money, no order, no Kalshi call from any desk.

| Place | Added condition (inherited constant, no tuning) |
|---|---|
| OIVER-SPREAD | YES ask minus YES bid <= 0.03, inclusive (1e-9 tolerance) |
| OIVER-CAP30 | the cheaper side's ask <= 0.30, inclusive; the 8c floor stays |
| OIVER-DEPTH | displayed size at the touch the order would meet >= 40 contracts (2 x 20), inclusive |

## 1. Decision poll and clock
- **Source:** R6 Bitcoin books, `book15r6/<date>/<HHMM>/book.csv.gz` on `quote-data` (never a candle, never a market list copy). R6 ends 2026-11-20 23:59Z for the series it records after the 11-13 cut (Bitcoin and Ethereum are on the extension); this sheet's logging stops with it unless the Head extends R6, in which case the extension date replaces that one here by a dated line that RE-DATES the places.
- **Decision instant** D = close time minus 180 s EXACTLY, in EXCHANGE time. **Decision poll** = the last R6 poll with exchange time at or before D and at most 10 s before it; none: "no signal: no poll", counted.
- **Exchange-time offset:** from the rows up to that poll only: the MEDIAN over the 120 most recent rows of the same run folder (any ticker, by receive time, at or before the poll, readable header only) of (the header time in seconds + 0.5 - t_recv_ms / 1000). Same text as section 0 of the wheel sheet.
- **Book fields at the decision poll:** YES bid and ask are the best YES bid and 1 minus the best NO bid; the cheaper side and its ask (ties to YES); the touch size is the YES ask size (= best NO bid size) for a YES buy and the best YES bid size for a NO buy. A missing side or a book not two-sided (rule 18: 0 < bid < ask < 1, 1e-9 slack, bid of 0 or ask of 1 included) is "no signal: not two-sided", counted by reason, never carried forward.
- **The parent's trigger** (open interest rise >= 86,300) is NOT read from R6, which has no open interest. Its source is open (section 4, item 1); until it is named, NO place records a signal, and the first counted decision instant is the first one after both the source is named in a dated line and this file's latest commit.

## 2. Fill check and price
- **Fill check:** the NEXT R6 poll after the decision poll must be at most 4 s after it (R6 polls every 2 s; a later next poll: no second look, a miss, counted, not scored). That poll must offer 20 contracts at or under the limit (limit = the ask seen at the decision poll, plus 0) on the ladder the order meets; the decision poll must offer the same. Both look at the recorded levels (up to 5). Otherwise: a miss, counted.
- **Fill price:** the worse of the two polls' size-weighted walked average asks for 20 contracts (the Head's wheel ruling of Nov 13). Fee per order: fee_up_order(p, 20) = ceil(0.07 x 20 x p x (1 - p) x 100 - 1e-9) / 100, p = the fill price. Cash per contract = win - price - fee / 20.
- OIVER-DEPTH's size condition uses the decision poll's touch size ONLY (not the next poll); the fill check applies to every place equally.

## 3. Result source and the read
- **Result:** the coverage file's `result` column ("yes" or "no") at the block read. For a ticker whose result is missing then, the ONLY later read is the kalshi-pull list job that Desk A builds at each block read and the Chief of Staff runs (`GET /markets/{ticker}`, the `result` field; no desk calls Kalshi itself). A ticker still without a yes or no result 7 days after its close is VOID, booked and counted, never scored.
- **Block read:** none before **2026-11-21** (after CFRTI-K's read on 2026-11-14 and its confirmation window), so no CFRTI-K held-out signal is in front of any reader of these places. The block rule is the wheel's (n >= 60, >= 7 US Central days, 10 wins and 10 losses, PF >= 1.3 as the place's own bar), and ADDITIONALLY the 7g comparison against the parent on the same windows: cash PF beats the parent's by 0.10, net per contract-week not lower (weeks over the parent's trades, same divisor for both), second half not worse (halves by FLOOR(n/2) in date order), 60 signals. Under 100 trades: "no evidence at n = x".
- **Scorers:** the history screens are `desk_a_verify/oiver_spread.py`, `oiver_cap30.py`, `oiver_depth.py` (development range closes 2026-09-12 to before 2026-11-09, read once, never tuned). They are not the forward scorers; the forward reader reuses their `decide()` rules on the R6 poll fields above and is written after the open interest source is named.

## 4. What this sheet does not decide (named, for the Head)
1. **The open interest log source** for the parent's trigger forward (the bot logger: OICORE orders and the P3 `qualified` skip rows carry `oiRise`; or a nightly candle pull, Main's answer pending). The same answer serves the thirteen OICORE places.
2. Whether R6 is extended past 2026-11-20 for Bitcoin.
3. A place counts as shadow only; none can be promoted past what OICORE's own record earns, and nothing goes live without the owner's own popup.
