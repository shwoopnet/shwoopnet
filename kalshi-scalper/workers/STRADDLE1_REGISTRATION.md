# STRADDLE1 registration: pre-earnings straddle run-up on US equity options (Gao, Xing, Zhang, JFQA 2018), 2026-11-03

Written and pushed BEFORE any option price, earnings date or return was downloaded or computed. Discovery only; no live code, nothing in `functions/`, no promote verb. N: +2 (one primary, one fees-x1.2 view is NOT a second try; the 3 percent and 5 percent universe views are not run). Data source is a placeholder until the owner chooses (see Data); the rules below do not change with the source.

## Mechanism and counterparty
Implied volatility rises into a known announcement as the event gets closer ("run-up"); a straddle bought 3 trading days before and sold the close before the announcement collects that rise without holding the jump. Counterparty hypothesis: option sellers and market makers who quote the straddle off a flat volatility term structure and do not charge for the run-up. "None named" is the outcome if the data does not show it. Literature gross effect is large in-sample; a bid-ask of 3 percent of mid each way eats most of it, which is why the prediction is near zero.

## Universe (fixed on cost before entry, no return seen)
US common stocks with a quarterly earnings 8-K (Item 2.02) in the window, listed options, and the ATM straddle (nearest strike to the entry-close underlying, first monthly expiry at least 10 calendar days after the announcement) with bid-ask spread / mid at most 3 percent at the entry close (4 trading days before the announcement day, measured one day before entry so it is known before the decision). Also straddle mid at least $0.50 and both legs bid > 0. No other filter. Events failing it are dropped and counted.

## Timing (exact)
Announcement day A comes from the 8-K Item 2.02 acceptance time (America/New_York) on SEC EDGAR, the earliest 2.02 filing in the quarter (press release date = event date). If acceptance is before 09:30 ET on trading day D, or after 16:00 ET on D-1 and before 09:30 on D, the announcement is BEFORE-OPEN on D: exit at the close of D-1. If acceptance is 09:30 to 16:00 on D, treat as DURING DAY: exit at the close of D-1 (the same rule, never hold into D). If acceptance is after 16:00 ET on D, AFTER-CLOSE on D: exit at the close of D (the announcement has not happened yet at the 16:00 close; the straddle is sold at that close). Entry: the close 3 trading days before the exit close (NYSE calendar). Weekend or after-hours acceptances roll to the next trading day as BEFORE-OPEN. Holding period is therefore 3 trading days for after-close, 3 for before-open measured to the prior close. The announcement jump is never held. Events where acceptance time is missing are dropped and counted.

## Fills and fees
Buy at the ask of both legs at the entry close, sell at the bid of both legs at the exit close (the end of day NBBO from the source). Fee $0.03 per contract each way (4 transactions per straddle: $0.12 per straddle, per share $0.0012). Return per event = (bid_exit_call + bid_exit_put - ask_entry_call - ask_entry_put - 0.0012) / (ask_entry_call + ask_entry_put). If either exit bid is zero it is 0 (no assumed fill better than the bid). Fees x1.2 view: multiply the fee and spread-paid is unchanged (spread is already in the fill).

## Numeric prediction (written before any data)
Net mean per trade between -1 percent and +1 percent of premium (point estimate -0.3 percent), win rate 45 to 52 percent, sd per trade about 12 percent of premium. FALSIFIED with probability about 85 percent. At sd 12 percent and 300 events the standard error of the mean is 0.7 percent, so only a mean of about +2 percent would clear the bar; I expect none.

## Bar and kill rules (frozen)
Events sorted by announcement date. The FINAL THIRD (by date) is frozen and unread until the first two thirds are scored and written down. Needs at least 300 events in total (otherwise NOT_ENOUGH_DATA, nothing called). Net mean per straddle above 0, day-clustered (by entry date) z of 2.9 or more (a lower bar than the coordinator's z about 5.27 for N; STRADDLE1 reports both and only 5.27 counts as a pass for promotion talk, 2.9 as NOT_YET_FALSIFIED), mean positive in both halves and at fees x1.2. FALSIFIED if: net mean at or below 0 on the first two thirds, OR either half negative, OR fewer than 300 events cannot be fixed by more history, OR the final third's net mean is below 0 when read once. Window split: halves of the first two thirds in time order; the final third is the out-of-sample read. No parameter is tuned (3 trading days, 3 percent, ATM, first monthly are fixed now).

## Data (placeholder)
Needs end of day bid and ask for the two ATM legs at entry and exit closes, plus underlying close and chain strikes/expirations. Candidate sources are in `workers/STRADDLE1_DATA_FEASIBILITY.md` (ThetaData free EOD from 2023-06-01 or Value 1 minute from 2020, via the `thetadata` Python package over HTTPS port 443, works from this container in principle). Earnings dates: SEC EDGAR submissions API (keyless, with acceptance time). Nothing is downloaded until the source and the credential (Claude environment secret `THETADATA_API_KEY` or email/password, never chat) exist.

## Expected read
About 3 to 5 days after the data exist; not before. Skeleton: `src/scalper/straddle1.py`, `tests/test_straddle1.py` (synthetic data only; scores nothing).
