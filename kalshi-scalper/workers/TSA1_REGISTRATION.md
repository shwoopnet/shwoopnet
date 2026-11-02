# TSA1 registration (Strategy Research V2, written 2026-11-02 BEFORE any candle was downloaded, any price read or any result computed; research only)

Owner decision relayed by the lead: test new non-L1, non-OICORE families in parallel on existing public data; no further approval needed. Family: Kalshi TSA checkpoint markets. Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
`grep -i -E "TSA|passenger" README.md` found nothing before this file. Not a duplicate. Not L1 (no 15 minute window, held for days), not OICORE.

## What was looked at before this registration (disclosure)
Listing only: Kalshi market listings (live and `/historical`) for series KXTSA, KXTSAW, TSA, TSAW, saved to a scratch file. Printed: counts by series and status, event dates, strike types, open and close times, the number of strikes per event, and `expiration_value` (the settled number) for 8 sample markets plus one 2021 daily market. No bid, ask, price or candle was downloaded and no model was built.
Findings that shape the design:
1. **tsa.gov is not reachable from this sandbox** (HTTP 403 to tsa.gov/travel/passenger-volumes and the FOIA csv, with and without a browser User-Agent). The task's information source (the TSA daily table) is therefore NOT_RUNNABLE here.
2. **Every Kalshi TSA market carries the number TSA published as its own `expiration_value`.** So the settled history of the weekly series IS the TSA published number, week by week, from 2021-07. The model below uses only those settled values of EARLIER weeks, each published (by TSA, then by Kalshi's settlement) before the look. This replaces the daily table with a weekly one; disclosed as a deviation from the brief ("same weekday last year x trailing-4-week YoY" becomes "same week last year x trailing-4-week YoY ratio", the weekday alignment is exact because 364 days is 52 weeks).
3. **The daily series KXTSA has no listed market at all** (live and historical listings empty; the only daily markets are 81 old `TSA-21...` bracket markets from 2021, a handful of events). Daily is NOT_RUNNABLE and is not tried. KXTSAW (weekly, "Above X million" greater-than strikes, settled on the average daily checkpoint number of the week Monday to Sunday) and its predecessor TSAW (2021-07 to 2024-09, same structure) are the universe: about 276 weekly events listed with gaps (2021-08, 2022-03, 2025-11).

## Counterparty and mechanism
Who loses: retail takers on the weekly ladder who anchor on last week's or the headline number and ignore the strong yearly seasonality (school calendars, holidays that move by weekday) and the year-over-year growth trend. Honest prior that this is priced in: high. The ladder is a transparent public statistic, market makers have the same history, and holidays that move (Easter, Thanksgiving week, July 4th falling mid-week) are exactly where the same-week-last-year model is wrong. Prior of a pass 3%.

## Model (fixed now; no fitted parameter except the error sample)
Let A(s) = the settled value of the weekly event whose Sunday date is s (the average daily checkpoint count, from `expiration_value`; an event with conflicting non-empty values is ineligible).
For event week s, using ONLY weeks <= s-14 days (the week ending s-7 is excluded: its Sunday number is published Monday morning, the same morning as the look):
- last year: Y = A(s-364d);
- trailing YoY ratio r = mean over k = 2, 3, 4, 5 of A(s-7k) / A(s-7k-364);
- centre c = Y x r.
All nine values must exist or the event is ineligible.
Fair P(A(s) > K) = (count of earlier errors e with c x exp(e) > K, plus 0.5) / (n + 1), where the error sample is ln(A(s_j) / c_j) over ALL earlier eligible events j (expanding; events j are older than s so their value was already settled), at least 30 errors, else the event is a burn-in and is not traded.

## Universe (cost and metadata only)
Series KXTSAW and TSAW, strike_type greater (or a "Above X" yes_sub_title when strike_type is empty, parsed as the number). Events with a model prediction (eligible and past burn-in). Strikes with model fair between 0.10 and 0.90 (no price). At the look: a valid two-sided quote (0 < bid < ask < 1) in the last hourly candle ending at or before the look and at most 6 hours old, and a quoted spread of at most 10c. No quote, no trade. No trade-price fallback.

## Entry rule and time
Look L = Monday 16:00 UTC of the event's week, i.e. (Sunday date s minus 6 days) 16:00 UTC, which is after the market opens (14:00 or 15:00 UTC Monday) and after Monday's morning publication of the previous Sunday. Nothing published after L is used.
Buy YES at the ask if fair - ask - 0.07 x ask x (1 - ask) >= 0.08; buy NO at 1 - bid if bid - fair - 0.07 x bid x (1 - bid) >= 0.08. (The gap is net of the unrounded per contract fee, per the brief: "gap >= 8 cents after the fee".) Information only: gaps of 0.05 and 0.12. One order of C = 10 contracts per qualifying strike, taker at the quoted ask, held to settlement. Fee 7% x C x p x (1-p) rounded UP to the cent per order; stress line at fees x1.2. Historical candles name fields `close` (live `close_dollars`); the shared `candlefield`/`pick` parser reads both. A quote is not a fill; stated.

## Windows
Eligible events past burn-in, sorted by date, split into three EQUAL thirds by event count: W1 earliest, W2 middle, W3 latest. W3 is the frozen holdout: it is not scored unless W1 and W2 both pass, and the rule above is frozen before W1 is scored (it is frozen by this file).

## Numeric prediction (written before scoring)
The model's Brier score on the traded-universe strikes is WORSE than the market mid's (the market sees the daily numbers of the current week's first days and the calendar); profit factor in each window 0.4 to 1.1; pooled mean per contract -6c to +1c; 150 to 500 trades; pooled z between -3 and +1. The registered numeric claim under test (from the brief) is the opposite: model Brier better than the market and profit factor >= 1.5 in each of three windows.

## Kill criteria
- `FALSIFIED`: profit factor under 1.5 after fees in ANY of the three windows (W3 read only if W1 and W2 pass), or the model Brier no better than the market mid's (same strikes, same look), or not positive at fees x1.2 in any window, or pooled day-clustered z (clustered by event) under the deflated bar 5.27 (running N about 728,698), or pooled mean under +2.0c.
- `NOT_ENOUGH_DATA`: fewer than 150 settled trades pooled over the windows (the PFs are reported anyway).
- `NOT_YET_FALSIFIED`: all of the above pass. It would permit only a forward quote re-read, never a trade.
- `NOT_RUNNABLE`: candles unreachable. Windows, thresholds, look and universe are not changed after the result; no variant is run.

## Overlap with L1
None. L1 buys 15 minute crypto, gold and similar markets 6 or 10 minutes before the close. These are weekly TSA contracts held for a week, a different underlying, series, horizon and information source; they cannot be the same position or window. Nothing here touches `functions/`, live code, L1 or OICORE.

## Tries
Two (the weekly KXTSAW/TSAW rule; the daily KXTSA is NOT_RUNNABLE and costs no try; information-only gap thresholds are shown, not tried). N + 2: running count about 728,700 (z bar about 5.27). Every result is quoted with window, n, cost and N.

## Forward read (not built)
New weekly events settle every Monday; the rule can be scored on events after 2026-10-25 using Kalshi's historical or live candles, which are retrievable after the fact, so no recorder is needed. The date depends on the pace of qualifying trades (stated in the result).
