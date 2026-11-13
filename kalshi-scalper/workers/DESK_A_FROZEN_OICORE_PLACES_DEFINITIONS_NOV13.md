# Frozen definition sheet, part (3): the 13 OICORE places on the nightly open-interest candle pull (source (b)). Idea Desk A, Nov 13, 2026.
At the Head's order of 21:19Z (Main chose (b): a nightly kalshi-pull of open-interest candles, one batched candlesticks request per close covering all the places' tickers, replayed against the R6 and NC15 books; NOT the bot logger). A NEW file, so the OIVER sheet (`DESK_A_FROZEN_OIVER_SHADOW_DEFINITIONS_NOV13.md`) and the wheel sheet keep their dates. Same version rule: **any later edit to this file RE-DATES every place it defines** to the commit time of that edit; a place counts forward only from the commit time of the latest version, and a decision instant earlier does not count. The places and their shared parameters are in `DESK_A_OICORE_PLACES_NOV13.md` (thirteen places: XRP, ETH, silver, copper, WTI, EUR/USD, GBP/USD, USD/JPY, HYPE, BNB, AUD/USD, USD/CAD, natural gas). Nothing here reads an outcome.

## 1. Decision instant and the open interest rise
- **Decision instant** D = close time minus 180 s EXACTLY, in exchange time. The close time is the market's `close_time` from the coverage file.
- **Open interest rise** = the `open_interest` of the 1 minute candle ENDING at close - 180 s, minus the `open_interest` of the candle ENDING at close - 360 s, both from the nightly pull's batched candlesticks answer for that ticker (the same two candles as OICORE's own rule, so 3 minutes apart). A candle's end is its `end_period_ts`. The rise must be >= T, inclusive (1e-9 tolerance).
- **T per market:** the 90th percentile (nearest rank) of that market's own window rises (this definition, one rise per window, the same two candles) over its previous 20 TRADING DAYS of windows, from the same pull; it uses no price, quote or result. A trading day = a US Central calendar day with at least one window whose two candles exist. **Not seated until 20 trading days of rises exist**; before that no signal is recorded and none is back-filled. T is frozen for a day at its 00:00 US Central value (the 20 days before that day), so a day's signals use one T. T of 0 or fewer than 5 contracts: NOT seated, reported (gate 0).
- **The pull is the only source of the rise.** The book (R6, NC15) carries no open interest and plays no part in the rise.

## 2. Quote, side and fill check (from the book, replayed after the pull)
- **Book source and clock:** R6 (`book15r6/`, 2 s polls) for XRP and ETH; NC15 (`nc15/` on `nc-data`, 5 s polls) for the other eleven. Exchange time and the 120 row rolling median offset exactly as in section 0 of the wheel sheet.
- **Decision poll** = the last poll with exchange time at or before D and at most 10 s before it (R6 or NC15 alike); none: "no signal: no poll", counted. The book must be two-sided (rule 18: 0 < YES bid, YES ask < 1, bid < ask); else "not two-sided", counted.
- **Side and price:** the cheaper side's ask at the decision poll (ties to YES), from the shared rule: 0.08 to 0.50 inclusive; outside: no signal.
- **Order and fill check:** 1 contract in shadow, limit = the ask seen (plus 0). The NEXT poll after the decision poll must be at most **4 s** after it on R6 or at most **6 s** on NC15; a later next poll: no second look, a miss, counted, not scored. Both polls must offer 1 contract at or under the limit; fill price = the worse of the two polls' asks (the wheel ruling). Fee per order = fee_up_order(p, 1) = ceil(0.07 x p x (1 - p) x 100 - 1e-9) / 100. Cash = win - price - fee.

## 3. Missing items (never carried forward, never interpolated, counted by reason)
- **A missing candle:** if the candle ending at close - 180 s OR the one ending at close - 360 s is absent from the pull's answer, or its `open_interest` is null or blank: "no signal: no candle", counted, scored as nothing. No neighbouring candle is substituted, no earlier or later one is used. The same missing-candle windows are left OUT of T's sample (a window with a missing candle has no rise).
- **A truncated or failed pull** for a night: that night's closes are "no signal: no pull", counted; they are not re-pulled except by the same job on a later night if Main chooses, and a late answer does not count for a decision instant that was already past its pull time (the pull is a record, and a row with `body_kind` other than a normal candlesticks body is not usable).
- **Result:** the coverage file's `result` column ("yes" or "no") at the block read; if missing, the ONLY later read is the kalshi-pull list job that Desk A builds at each block read and the Chief of Staff runs (`GET /markets/{ticker}`, the `result` field). A ticker with no yes or no result 7 days after its close is VOID, booked and counted, never scored.

## 4. OIFIELD withdrawal and the book sources' dates
- **Withdrawal:** any place on a market whose candles do not carry populated `open_interest` per tonight's OIFIELD check is WITHDRAWN (its place is removed from the thirteen, with the reason written in a dated line that RE-DATES this file). I do not know which markets pass; the check is not mine and I have read no data.
- **R6 ends 2026-11-20 23:59Z for Bitcoin and Ethereum only; the other R6 series (including XRP) stop 2026-11-13 23:59Z.** So **OICORE-XRP has no book source after tomorrow** unless R6 is extended for XRP; it cannot be seated in practice and is reported as withdrawn-by-source unless the Head orders otherwise. OICORE-ETH's book source is R6 to 2026-11-20 23:59Z (not 2026-12-31 as the Nov 13 line in the places file says; that line was wrong and a dated correction follows it). NC15 runs to 2026-12-31.
- **Seating date:** a place cannot count a signal before it has 20 trading days of rises, so the earliest first signal is 20 trading days after the first pull night for that series (the pull's start date is Main's and not known here). Nothing is read before then.

## 5. The read
Per place, the wheel block rule (n >= 60, >= 7 US Central days, 10 wins and 10 losses, PF >= 1.3) with "no evidence at n = x" under 100, no promotion claim, labels as in the places file ("research doubts carry-over" on ETH). A place has no value of its own beyond what OICORE's record earns.

## 6. Not decided here (for the Head)
1. Main's pull start date and its time of night (it sets when T first exists).
2. Whether R6 is extended for XRP (otherwise OICORE-XRP is withdrawn by source).
3. Which places OIFIELD withdraws.
