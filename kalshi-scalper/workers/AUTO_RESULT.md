# AUTO result: forward reads that run themselves, plus a nightly live watcher (2026-10-29, V2, research only)

No new hypothesis, no registration, no try added to N. Nothing here trades, deploys or changes a registration; every read is run by its own registered command.

## What was built

| File | What it does |
|---|---|
| `src/scalper/autoscore.py` | `python -m scalper.autoscore check`: one pass. Refreshes public data at most every 6 hours (`scalper.fresh_update`; `scalper.conf2 fetch 1793059200 <now>`, skipped while another conf2 fetch is writing the same file). Checks each read's readiness with a COUNT only, runs a ready read's registered scorer once as a subprocess (done = result file exists), logs to `workers/AUTO_LOG.md`. |
| `src/scalper/mkttime1f.py` | MKTTIME1-F exactly as registered: `count` (block entries and losses only, no PF) and `read` (once; refused below 15 block losses; refused a second time). |
| `src/scalper/livewatch.py` | `python -m scalper.livewatch run`: reads the nightly report (720 hours, order rows) with `KALSHI_REPORT_TOKEN` from the environment inside Python, saves raw rows to the scratchpad only, writes aggregates to `workers/LIVEWATCH.md` (newest first, Central time). |
| `workers/autoscore_loop.sh` | `autoscore check` then `sleep 3600`, forever; the live watcher once a day on the first pass at or after 00:30 Central. Log: `data/autoscore_loop.log` (git-ignored). |

## Readiness rules (each a count; nothing scored before it is due)

| Read | Ready when | Runs |
|---|---|---|
| LOCK2 | 25 closes per asset (`scalper.lock2 count`) | `scalper.lock2 run` (writes `data/lock2_result.txt`) |
| MKTTIME1-F | 15 losses in gold's 20:00 to 24:00 CT block, closes after 2026-10-30 00:00 UTC | `scalper.mkttime1f read` (writes `data/mkttime1f_result.txt`) |
| MM1 | 300 recorded gold 15 minute windows (distinct KXGOLD15M tickers in `quotes/*/quotes.csv.gz` on origin/quote-data) | built as "log MM1 ready, scorer needed"; the lead then added `scalper.mm1` (MM1S amendment) and wired `scalper.mm1 run` in (commit 8e1edd7; it refuses below 300 usable windows, writes `data/mm1_result.txt`) |
| RECORD1 | (the daily scheduled task reads it) | logs the count line of `scalper.record1 look` once a day; the look's mean and z are kept out of the log |
| CONF2 C | 30 kept window C closes (from 2026-10-27) AND `data/conf2_A_done` exists (the lead writes it) | `scalper.conf2 holdout`, output saved to `data/conf2_C_result.txt` |

## MKTTIME1-F choices the registration does not spell out (fixed before any forward entry exists)

- Every `lstrats.hold_rule` entry is kept (L1 at the candle ending exactly 360 s before the close, 88c to 97c, held, 1 contract, fee rounded up per order); no extra candle-history filter like `tstop1.load`'s.
- Day-clustered z = the cluster-robust z of (mean of the rest minus mean of the block), clustered by the entry's Central date, with the within-day covariance between the two means included.
- Net rule as MKTTIME1's check: net without the block at least 70% of net with it when net with it is positive, otherwise net without at least net with.
- Fees x1.2 and the block's own PF are printed as information only.

## Live watcher method

- Per market (gold, Bitcoin, Ethereum, Dogecoin, XRP): settled, losses, win rate, PF, net (dollars at real sizes, after fees), last 7 days against the 23 days before.
- PF by price paid: the report's `avgFill` is empty, so the price is solved from `settledPnl` and the filled count (the whole cent p for which C(1-p) - fee or -Cp - fee matches to the cent). Exits cannot be solved (two unknowns), so the band columns cover held orders only and read high. Exits are most of the losses.
- Flags, only these: the last 7 days' loss rate above the history loss rate with a one-sided binomial p under 0.05; or a last-7-day PF under 0.8 with at least 30 settled. History loss rate per series comes from `scalper.tstop1.load()` (6 minute look), restricted to markets closing before the report window so the two do not overlap. Live includes 10 minute entries; the history is the 6 minute look only.

## First run (2026-10-29, by hand)

Readiness: LOCK2 BTC 11, ETH 11 (25 needed). MKTTIME1-F 0 entries (the population starts 2026-10-30). MM1 48 gold windows (300 needed). RECORD1 132 qualifying trades on 8 dates (300 on 10 needed). CONF2 C 18 window C entries, 0 kept closes, 18 without ladder (window C's ladder not fetched yet; `data/conf2_A_done` absent).

Live watch flags: **XRP only**. Last 7 days 9 losses in 62 (14.5%) against a history loss rate of 5.18%, one-sided binomial p 0.0045; and last-7-day PF 0.53 on 62 settled. XRP is already paused in code since 2026-10-28. No other market flagged. 30-day PF: gold 1.73 (+$40.60, 200 settled), Bitcoin 0.72 (-$22.39, 155), Ethereum 0.92 (-$2.42, 113), Dogecoin 1.74 (+$9.04, 129), XRP 0.41 (-$13.10, 86).

## Caveats

- The loop runs in this container. It stops when the container ends; restart it with `cd kalshi-scalper && nohup bash workers/autoscore_loop.sh >/dev/null 2>&1 &`.
- The loop does not commit. `workers/AUTO_LOG.md` and `workers/LIVEWATCH.md` change on disk and need committing by the lead.
