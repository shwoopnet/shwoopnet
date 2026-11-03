# RECDAILY: the low-frequency quote recorder (2026-11-03, discovery infrastructure, N: +0)

A recorder is not a try. It adds no rule, scores nothing and has no promote verb. It exists because USWEEP1 (five daily watch items), BARRIER1 (monthly one-touch), NOWCAST1 and FEDIMPL1 (macro ladders) look at a quote hours or days before a close, and the forward ledger and a research sandbox are ephemeral and the shared Kalshi read limit makes ad-hoc pulls fail (429). Without a scheduled keyless recorder those forward tests never accrue. EVENT830 (15 minute series) is already fed and is not recorded here.

## What it does
`.github/workflows/record-daily.yml` runs `scripts/record_daily.py` at minute 7 and 37 of every hour (and by hand with workflow_dispatch). One run lists, per watched series, the open markets (one GET per series, paged) and the markets settled in the last 3 days (one GET per series), and writes:
- `daily/quotes/<date>/<HHMM>.csv.gz`: one row per watched open market: slot_ts, poll_ts (this recorder's own clock), the server Date header, tests, series, ticker, event, open_time, close_time, minutes to close, status, strike type, floor and cap strike, yes_bid, yes_ask, last, volume, open_interest. `<HHMM>` is the 30 minute slot, so a re-run of a slot replaces its file (idempotent) and a late or dropped schedule only widens the gap between polls.
- `daily/results/<date>/<HHMM>.csv.gz`: a market's result (yes or no) the first time it is seen settled; known tickers are skipped.
- `daily/runs/<date>.csv`: one line per run (calls, 429 count, errors, rows, clock skew from the Date header). The 429 count is the health check.
All on the `quote-data` branch with the built-in GITHUB_TOKEN. Never main, no key, no secret, no order, GET only.

## The watchlist: `workers/RECDAILY_WATCHLIST.json`
- USWEEP1: KXGOLDD (look 360 min before close), KXSILVERD (360), KXNATGASD (360), KXBRENTD (60), KXHIGHTSATX (1440). Open markets closing within 30 hours (a test pins that the look matches `usweep1.FWD`).
- NOWCAST1: KXCPI, KXCPICORE, KXPCECORE, KXGDP, look 24 hours before the close; markets closing within 30 hours.
- FEDIMPL1: KXFEDDECISION, KXFED; markets closing within 30 hours. The look is the last business day before the decision at the 19:00 UTC hourly candle: use `recdaily.nearest_to_time`.
- BARRIER1: the 14 monthly one-touch series (KXBTC/ETH/SOL/XRP/DOGE/BNB/HYPE MAX/MIN MON), every open market at every poll, so the open + 48 hour look is on file. The quarterly "when will" series (KXBTCMAXQ and the MAXM ones) are not polled: add them to the watchlist if wanted.
Adding a test is a watchlist edit only; the script names no ticker (gate D3).

## Reading it: `src/scalper/recdaily.py`
`load_quotes(dir)`, `load_results(dir)`, `nearest_to_look(rows, ticker, minutes_before_close=... | minutes_after_open=...)` (None when no poll is within 25 minutes, which an evaluator must count as NoData), `nearest_to_time`, and `usweep1_window(...)`, which builds the window dict `usweep1.forward_eval` expects (look candle from the nearest recorded poll, plus the settled result). The quote is the market's own bid and ask, not an order book: fills are an assumption from a quote, as the registrations already say. Check out the data branch: `git worktree add /tmp/qd quote-data` and point the reader at `/tmp/qd/daily`.

## Cost
- API calls: about 2 per series per run (open, settled), more when a series has over 1,000 markets; 25 series gives about 50 GETs a run at 0.5 s spacing, about 1 minute of wall time. 429 is retried once after 3 seconds, then that listing is skipped and counted.
- GitHub Actions: 48 runs a day, each about 1 to 2 billed minutes, so roughly 1,500 to 3,000 minutes a month. The repo is public (Pages), where Actions minutes are free; on a private repo that would exceed the 2,000 free minutes. Switch to hourly by changing the cron to `7 * * * *`, which halves it.
- Storage: tens of KB per run gzipped, under 100 MB a year on the data branch.

## Turn it off
Delete `.github/workflows/record-daily.yml`. Nothing else depends on it; the data already pushed stays on `quote-data`.

## What the owner or main must do
1. Merge branch `claude/v2-recorder-daily` into main (the workflow checks out the script and watchlist FROM MAIN, and scheduled workflows run only from the default branch). Then run the workflow once by hand from the Actions tab (workflow_dispatch) and confirm a `daily/` folder appears on `quote-data`. Scheduled starts of a new workflow are often late or dropped for a few hours.
2. Enable Actions if disabled. Nothing to configure: no secret.
3. Evaluators read the branch, not the ledger: they need a checkout of `quote-data`.

## How long until forward trades exist
- USWEEP1: the first daily markets inside the 30 hour window are captured on the first run; the first 360 minute looks (gold, silver, gas) on the first full day after the merge, BRENT 60 minute and TX high temperature (1440) likewise. The registered probes need 40 fills each at about 5 entries a day, so about 8 to 10 days per item, and the strikes of one day are not independent.
- NOWCAST1: CPI is released Nov 10 (the 24 hour look is Nov 9), core PCE and GDP Nov 25, CPI Dec 10, core PCE Dec 23. So the first forward release is Nov 10 if the recorder is live by Nov 9, and the whole forward sample is under ten releases by year end.
- FEDIMPL1: next FOMC decision, then the day before it. One meeting is one cluster, so no verdict inside this year.
- BARRIER1: the already open November markets are past their open + 48 hour look, so they give no look. The December monthly events open about Dec 1 and their look is about Dec 3. Until then it records the path only.
