# kalshi-pull: a manual pull of Kalshi's public market data (Nov 12, 2026)

**OWNER-ACCEPTED TERMS RISK.** The owner waived reading Kalshi's Developer Agreement and Terms of Use on Nov 12, 2026 ("just go on this already -- ignore the terms"). The two pages were NOT read (HTTP 429 to every fetch, archive copy also unreachable). This is NOT a finding that automated reads are allowed. It is the same treatment as the Yahoo market strip: a known, unresolved terms question that the owner chose to carry. If Kalshi objects, delete `.github/workflows/kalshi-pull.yml` and the `kalshi-pull-data` branch.

## What it is

A workflow a person starts by hand from the Actions tab. It reads one job file from `kalshi-scalper/workers/kalshi_pull_jobs/` on main, checks every request in it, sends them one at a time to Kalshi's public API, and pushes the raw answers (gzipped) to its own branch, `kalshi-pull-data`. It exists because research pulls from the shared sandbox are throttled and three teams queue behind one budget. Nothing triggers it: no schedule, no push, no pull request. Jobs ship in this change and DO NOT RUN until a person dispatches one.

## The rate, stated plainly

| Limit | Value |
|---|---|
| Requests a second | at most 1 request a second (one stream, no parallel requests; a job file can only slow this down) |
| Requests a run | at most 1,200 (a hard constant); each job file sets its own lower cap, pages and 429 retries count |
| After a 429 | wait 5 seconds, then 10, doubling to a 60 second ceiling, ask the same request again; THREE 429s in a row end the run |
| Other failures | three in a row (5xx, a redirect, no answer) end the run; a 404 is an answer |
| Answer size | 5 MB an answer, 200 MB a run |
| Run time | 40 minutes in the script, 50 in the workflow |
| Runs a day | 6 real runs per UTC day (counted from the folders already on the data branch); a dry run does not count |
| Runner minutes | about 2 for 60 requests, about 6 for 300, about 25 to 30 for the full 1,200 (checkout and push add under a minute); free on a public repository |
| Stop date | 2027-02-28 23:59 UTC, checked in the workflow and in the script |

It never rotates addresses, never uses a proxy and never retries around a refusal. The pace is deliberately conservative: if the first runs see 429s, lower the pace by a reviewed edit, do not add retries.

## What it can and cannot ask

- Two (host, base path) pairs, pinned in code in the `ROUTES` table and nowhere else: `elections` (`api.elections.kalshi.com`, `/trade-api/v2`) and `perps` (`external-api.kalshi.com`, `/trade-api/v2/margin`), https only. A job names its pair by key (`"route"`) and can never supply a host or base path of its own. A `perps` job can read only `/markets/{KXBTCPERP|KXETHPERP}/candlesticks` (1 minute candles, one page, at most 86,400 seconds a request).
- GET only. No key, no auth header, no cookie, no body. The only secret in the workflow is the built-in token, used to push the data branch.
- Redirects are refused (a 3xx is a failed read). The User-Agent is `shwoopnet-research-pull` (honest, generic, no personal details).
- Every request in a job file must match one of the job's `allowed_endpoints` patterns, may use only the parameters that endpoint lists, and every ticker or series in a path or parameter must be in the job's allowlists. Account, portfolio, order, key and exchange paths are refused whatever the job says. Values with `/ \ ? & # % = @ :`, `..`, a space or a control character are refused. The paging cursor is the only thing taken from an answer into a later request, and only if it is a plain token.
- A body that is not a JSON object is stored and never read for anything. An answer over 5 MB is cut and marked `truncated`.

## Where the answers go

Branch `kalshi-pull-data` (an orphan branch created by the first real run), never main, never published with the site (`_config.yml` excludes the code; the branch is not the Pages source). Layout: `pull/<JOB_ID>/<UTC time>_<run id>/` with `0001.json.gz` ... (the raw body of request N), `manifest.json` (the job as run, one row per request with status, bytes, sha256, the server Date header) and `STATUS` (complete, stopped_at_cap, stopped_429, stopped_failures, stopped_time or stopped_size). The branch is public, so everything on it is public; it can only hold public market data because the script holds no key.

## How to run a job

1. Actions tab, `kalshi-pull`, Run workflow, choose the job. The default is a DRY RUN: it checks the job file, prints the URLs to the run summary and sends nothing.
2. Read the dry run. Run again with `dry_run` set to `false` to send the requests. Dispatch is for the owner or Main, one pull at a time (the concurrency group never overlaps two).

## The first jobs, in rank order

| Rank | Job | Requests (cap) | State |
|---|---|---|---|
| 1 | `NOSIDE1_CANDLES` (the approval NO-side pull, W-NO-ARM1, development events only) | 1,034 requests, about 18 minutes at 1 a second | active; the lists stage `NOSIDE1_LISTS` is retired because the universe is frozen in `NO_ARM_CUTS.json` |
| 2a | `SPREADLISTS` (W-SPREAD-CELL1, time fields only) | 11 requests, `GET /markets?tickers=` of up to 100 tickers each; run first. Whether Kalshi accepts 100 tickers a request is unverified; the runner cannot batch smaller, so a short answer leaves those events without a time | active |
| 2 | `SPREADCELL1` (W-SPREAD-CELL1) | 274 batched candle requests, up to 55 tickers each, about 5 minutes | active; runs first in rank |
| 3 | `ROLLOFF_PROXY` (ROLLOFF proxy check) | 6 requests, at most 9 pages, cap 12 | ready |
| 4 | `COMBO1_OPENBOOK` | 3 | retired: its reads were made and COMBO1 is closed |
| 5 | `PERPBTC1M`, `PERPETH1M` (Kalshi's own Bitcoin and Ethereum perpetual, 1 minute candles, 2026-06-03 to 2026-11-12) | 163 each (one UTC day per request, 1,440 candles at most), 326 in all, about 3 runner minutes each | `PERPBTC1M` ready, not run; `PERPETH1M` paused for later (no registered test uses it; the runner refuses it) |

Not included: `ECONLAG` (demoted by its own power analysis) and `BALLOTNO`. A job that is not `active` is refused by the script before any request, which is how the two retired jobs are kept from running. Every change to a job file is security-relevant (it names the exact URLs the runner may send) and needs a security look.

Stage 1 of the NO-side pull asks for market lists, not events, because the cuts file holds event tickers only. Stage 2 uses the registered rules: development events only (the oldest two thirds of each series, the held-out third is never requested), round robin over the series, hourly candles from two days before the close.

## Files

`scripts/kalshi_pull.py`, `.github/workflows/kalshi-pull.yml`, `kalshi-scalper/workers/kalshi_pull_jobs/` (the job files, `NOSIDE1_CUTS.json` and `build_noside1_candles.py`), `test/kalshiPullGates.test.js`. The request checks follow V2's `pullrunner.py` (host rule, path patterns, allowlists, 429 stop); the pace, 429 limit and output differ on purpose.

## The perps route (Nov 12, 2026)

`PERPBTC1M` and `PERPETH1M` use `"route": "perps"`. 163 UTC days from 2026-06-03 to 2026-11-12 inclusive, one request per day per ticker, so 163 requests each. The windows are midnight to midnight (86,400 seconds, the size `scripts/record_perps_candles.py` already asks for); the last day is partial and adjacent windows may share a boundary candle, so de-duplicate on `end_period_ts`. The per-request candle limit is not written down in this repository and is not assumed to be higher. The runner stays one reviewed file; a changed route table or perps rule is security-relevant. Same terms position as above: the owner waived the terms read, which is accepted risk and not a finding that automated reads are allowed.

`PERPETH1M` is paused for later: its status is `paused`, which the runner refuses, so it cannot run until a reviewed edit sets it to `active`. Size watch: 1,440 candles a day x 163 days may reach the 200 MB per-run cap (a clean `stopped_size`, what was fetched is kept); read the first real run's manifest before any further ticker. The owner confirmed on Nov 12, 2026 that the terms waiver covers BOTH Kalshi hosts (`api.elections.kalshi.com` and `external-api.kalshi.com`).

## Jobs v3 (Nov 12, 2026)

Six more `active` jobs from Desk A and Desk B, plus the CFRTI-K stage 2 builder. Every job-file diff here is security-relevant: each names the exact URLs the runner may send. All six passed `python3 -I scripts/kalshi_pull.py <JOB> --dry-run`; the runner script is unchanged. All are measurements with zero tries or development-only lists (no held-out outcome is read). Minutes are at 1 request a second (runner minutes add under a minute for checkout and push).

| Job | Owner | Requests (cap) | Minutes | Registration |
|---|---|---|---|---|
| `CFRTI_K_R6SLICE` | Desk A | 20 (20), the 407 windows with a full R6 book, batches of at most 9,000 minutes x tickers | under 1 | `CFRTI_K_REGISTRATION.md`; for Forensics' CANDLEVSBOOK1 |
| `CFRTI_K_PROBE` | Desk A | 1 (1), 24 consecutive tickers | under 1 | `CFRTI_K_REGISTRATION.md`; one pre-cutover batch, decides builder mode `all` or `live` |
| `CFRTI_K_LISTS` | Desk A | 2, up to 28 pages (30) | up to 1 | `CFRTI_K_REGISTRATION.md`; development markets only, closes before 2026-11-05 |
| `INGAMELAG_M1A` | Desk B | 108 (123) | about 2 | `IDEA_DESK_B_INGAME_CARD.md`; first half of the rebuilt 215 game list |
| `INGAMELAG_M1B` | Desk B | 107 (122) | about 2 | the second half; M1A and M1B are one measurement, read once |
| `INGAMELAG_M1` | Desk B | 215 (235) | n/a | retired Nov 12: one job of 1 minute candles risked the 200 MB a run cap; replaced by M1A and M1B, no workflow choice |
| `NHLOT_LISTS` | Desk B | 4, up to 9 pages (10) | under 1 | `IDEA_DESK_B_WAVE3.md` |
| `ECONLAG_CALENDAR` | Desk B | 10 (10) | under 1 | `IDEA_DESK_B_PROTOCOLS.md` (amendment 2) |

Dispatch order (Head of R&D): (1) `CFRTI_K_R6SLICE`, whose answer gates two other reads; (2) `CFRTI_K_LISTS` and `CFRTI_K_PROBE`; (3) the CFRTI-K candle job, built later from the lists answer; (4) `INGAMELAG_M1A`, `INGAMELAG_M1B` and `NHLOT_LISTS`; (5) `NOSIDE1_CANDLES` (already here); (6) `ECONLAG_CALENDAR`.

`build_cfrti_k_candles.py` is an OFFLINE script (it sends nothing): it builds the CFRTI-K candle job from the `CFRTI_K_LISTS` answer (modes `all`, `live`, `hist`). It packs batches to at most 9,000 minutes x tickers (the endpoint answers HTTP 400 above 10,000), about 216 requests in live mode and about 624 in all mode. Its output is a new job file and needs its own reviewed pull request before it can run. Not included: `ECONLAG_CANDLES`, `NHLOT_CANDLES` (built later) and the candle stage itself.
