# kalshi-pull: design for an on-demand public data pull on GitHub Actions (design only, nothing built)

Written by Idea Desk A on Nov 12, 2026 at Main's request. Status: DESIGN, approved in principle by Main the same day with three changes (now made below: `/historical/trades` added, a dry-run input added, the `heldout` field kept as required). No workflow, script or test exists.

**HOLD (the owner's condition, relayed by Main, Nov 12): nothing is built until a person has read Kalshi's Developer Agreement and Terms of Use and written down the clauses on automated access, requests from additional network addresses, publishing the data, and use by an LLC.** Both pages refused the team's fetch, so nobody on the team has read them. Running public reads from a GitHub address and storing the answers on a public branch are exactly the two things those clauses would govern, so this design assumes nothing about them.

## 1. What it is for, in one paragraph

Research pulls of Kalshi's PUBLIC market data are throttled today by one shared budget of 12 requests a minute from the research sandbox, and three teams queue behind it. A GitHub runner has its own network address, so a pull run there does not use that budget. `kalshi-pull` is a workflow a person or Main starts by hand. It reads one small JOB FILE that says which public reads are wanted, makes those reads at one a second, stops at a hard cap, and writes the raw answers, gzipped, to its own data branch. It holds no key, can send nothing but GET requests to one host, and cannot be made to ask for anything outside a fixed list of public endpoints.

## 2. The parts

| Part | Where | Who changes it |
|---|---|---|
| Workflow `.github/workflows/kalshi-pull.yml` | main | reviewed pull request, owner merges |
| Runner script `scripts/kalshi_pull.py` (standard library only) | main | reviewed pull request, owner merges |
| Gates `test/kalshiPullGates.test.js` | main | reviewed pull request, owner merges |
| Job files `jobs/<ID>.json` | branch `pull-jobs` (never main) | any R&D session commits; nothing runs on commit |
| Results | branch `pull-data` (its own orphan branch; never main, never `quote-data`) | written only by the workflow |

The script and the allowlist come from main, so what can be requested is reviewed code. The job file is data: it can only choose among what the script allows.

## 3. Trigger and inputs

`on: workflow_dispatch` ONLY. No `schedule`, no `push`, no `pull_request`, no `pull_request_target`, no `workflow_run`, no `repository_dispatch`. Committing a job file starts nothing.

Inputs (all checked by a first step before anything else runs; they reach the shell through `env:`, never by `${{ }}` inside a `run:` line):

| Input | Rule |
|---|---|
| `job` | `^[A-Z0-9_]{2,24}$` (the job id; the file is `jobs/<job>.json`) |
| `job_sha` | `^[0-9a-f]{40}$` (the exact commit on `pull-jobs` that was reviewed; the workflow fetches that commit, so the file that runs is the file that was read) |
| `dry_run` | `true` or `false` (a choice input, default `true`). With `true` the script checks the job file, builds every first-page URL and prints the list to the run log and the step summary, sends NO request and pushes nothing. A real run is a deliberate second dispatch with `false` |

Who dispatches: Main (the Chief of Staff), who holds the request budget, after reading the job file at that commit. Each dispatch is logged in `RND_QUEUE.md` (job id, commit, request count, who asked). The owner can dispatch too. Desks and testers commit job files and ask Main; they do not dispatch.

## 4. Job file schema

JSON, at most 64 KB, UTF-8, ASCII only inside values. Unknown keys are refused (the run stops before any request).

```json
{
  "id": "CLINICAL2_CANDLES",
  "owner": "V2",
  "registration": "kalshi-scalper/workers/CLINICAL2_REGISTRATION.md",
  "purpose": "daily candles for the 60 settled FDA markets of the development cut",
  "heldout": "none",
  "max_requests": 180,
  "requests": [
    {"ep": "candles", "series": "KXFDAAPPROVAL", "ticker": "KXFDAAPPROVAL-26OCT-ABC", "start_ts": 1790000000, "end_ts": 1793000000, "period": 1440},
    {"ep": "markets_list", "series": "KXFDAAPPROVAL", "status": "settled", "limit": 1000, "max_pages": 3}
  ]
}
```

| Key | Rule |
|---|---|
| `id` | equals the `job` input |
| `owner` | one of a fixed list: V2, REFINEMENT, DESK_A, DESK_B, MAIN |
| `registration` | a repo path matching `^kalshi-scalper/[A-Za-z0-9_./-]{1,120}\.md$`; the pull must belong to a registered test or a census |
| `purpose` | one line, at most 200 characters |
| `heldout` | `"none"`, or the name of the registration whose held-out this pull is the registered ONE read of. A pull that would fetch outcomes inside any unread held-out window is refused by Main at dispatch; the script cannot judge this, so the field exists to make the requester say it |
| `max_requests` | 1 to 600; the run stops when this many requests have been sent, pages included |
| `requests` | 1 to 600 entries, each an endpoint id from section 5 with its own typed fields |

There is deliberately NO free-form path or URL field. The script builds every URL from a template and typed values. That is the main defence: a job file cannot contain a path, so it cannot contain a wrong one.

## 5. The endpoint allowlist (exactly these; Kalshi host only)

Host, pinned as a constant: `external-api.kalshi.com`, base path `/trade-api/v2` (the host the recorders on main already use). HTTPS only, default port only.

| `ep` | Path built by the script | Typed fields |
|---|---|---|
| `markets_list` | `/markets` | one of `series`, `event`, `tickers` (1 to 100 tickers); optional `status` (open, closed, settled, unopened), `min_close_ts`, `max_close_ts`, `limit` (1 to 1000), `max_pages` (1 to 50) |
| `market` | `/markets/{ticker}` | `ticker` |
| `events_list` | `/events` | optional `series`, `status`, `nested` (true or false), `limit` (1 to 200), `max_pages` |
| `event` | `/events/{event}` | `event`, optional `nested` |
| `series_list` | `/series` | optional `category` (`^[A-Za-z ]{1,40}$`) |
| `series` | `/series/{series}` | `series` |
| `candles` | `/series/{series}/markets/{ticker}/candlesticks` | `series`, `ticker`, `start_ts`, `end_ts`, `period` (1, 60 or 1440) |
| `candles_batch` | `/markets/candlesticks` | `tickers` (1 to 100), `start_ts`, `end_ts`, `period` |
| `trades` | `/markets/trades` | `ticker`, optional `min_ts`, `max_ts`, `limit` (1 to 1000), `max_pages` |
| `hist_markets_list` | `/historical/markets` | as `markets_list` |
| `hist_market` | `/historical/markets/{ticker}` | `ticker` |
| `hist_candles` | `/historical/markets/{ticker}/candlesticks` | `ticker`, `start_ts`, `end_ts`, `period` |
| `hist_trades` | `/historical/trades` | `ticker`, optional `min_ts`, `max_ts`, `limit` (1 to 1000), `max_pages` |
| `mve_list` | `/multivariate_event_collections` | optional `status`, `limit`, `max_pages` |
| `mve` | `/multivariate_event_collections/{collection}` | `collection` |

Notes for the builder:
- The exact query parameter names for `candles_batch` and the two multivariate paths must be copied from the V2 scripts that already call them (`src/scalper/` on the research branch) and pinned by a test, not taken from this table. I did not call Kalshi to check them.
- `/historical/trades` was added at Main's word (Nov 12): V2's scripts use it in seven places. Its parameter names are to be copied from those scripts too.
- Deliberately absent: the order book (the recorders cover it), everything under `/portfolio`, `/margin`, `/exchange`, anything that needs a key, and every other path.

Value rules (applied to every field before a URL is built):
- `ticker`, `event`, `collection`: `^[A-Z0-9][A-Z0-9._-]{0,63}$`. `series`: `^[A-Z0-9]{2,32}$`.
- timestamps: integers from 1,500,000,000 to 2,100,000,000, and `end_ts` after `start_ts`.
- enums as listed; integers within the ranges listed.
- Any value containing `/`, `\`, `?`, `&`, `#`, `%`, `=`, `@`, `:`, `..`, a space, a control character or a non-ASCII character is refused, whatever the field.
- Path pieces are percent-encoded with no safe characters; the query is built with the standard encoder. After building, the URL is parsed again and the script asserts: scheme `https`, host exactly the pinned host, no user info, no port, no fragment, path matches the template's own compiled pattern. A URL that fails is never sent.
- The paging cursor is the only value that comes from Kalshi's answer back into a request. It goes into the query through the encoder, is capped at 512 characters, and the page count is capped by `max_pages` and by `max_requests`.

## 6. Request behaviour and caps

| Setting | Value |
|---|---|
| Pace | at least 1.0 second between request starts, one stream, no parallel requests |
| Method | GET only; the script contains no other method and no request body |
| Headers | `User-Agent: shwoopnet-research-pull` (generic, no personal details), `Accept: application/json`; no `Authorization`, no cookie, no key |
| Redirects | refused (a 3xx is recorded as a failed request and not followed) |
| Timeout | 20 seconds a request |
| 429 or 5xx | wait 5 seconds, doubling to 60; the same request is tried at most 3 times; 5 refusals in a row end the run with status `stopped_429` and what was fetched so far is still written |
| Request cap | `max_requests` from the job, never above the code constant 600; reaching it ends the run with status `stopped_at_cap` |
| Answer size | 5 MB a response (larger is cut off and marked), 200 MB a run |
| Job timeout | `timeout-minutes: 25` |
| Concurrency | one group `kalshi-pull`, `cancel-in-progress: false`: two pulls never run at once, so the pace is one a second for the whole repo |
| Day cap | at most 6 dispatches a UTC day, counted by the script from the manifests already on `pull-data` (a seventh exits before any request) |

A stop date is part of the design: the workflow's first step exits after 2027-02-28 23:59 UTC, like the recorders. A later date is a reviewed edit.

## 7. Results: how they are named and read

Branch `pull-data`, created as an orphan branch by the first run. Layout:

```
pull/<JOB_ID>/<YYYY-MM-DD>T<HHMM>Z_<run_id>/
    manifest.json      the job file as run, the job commit, the script commit, start and end time, status,
                       and one row per request: index, ep, the typed fields, page number, HTTP status,
                       bytes, sha256 of the body, the server Date header, send and receive time, file name
    0001.json.gz       the raw body of request 1, exactly as received
    0002.json.gz       ...
    STATUS             one word: complete | stopped_at_cap | stopped_429 | refused_job | failed
```

- Bodies are stored raw so every reader parses them itself and nobody depends on the puller's reading of a field.
- To read: `git fetch --depth=1 origin pull-data`, then `git show FETCH_HEAD:pull/<JOB_ID>/<run>/manifest.json`. A test's registration cites the run folder and the manifest's sha256 values.
- The push uses the recorders' six-try loop and an explicit refspec to `pull-data` only.
- This repository is public, so everything on `pull-data` is public. That is acceptable only because the script can fetch nothing but public market data: there is no key, so no account data can arrive. No order, balance or position can appear in a result.
- Size: a 600 request run of candle answers is roughly 5 to 30 MB gzipped. If the branch passes 1 GB, runs older than 60 days whose tests are closed are removed by a reviewed commit (Main's job, logged).

## 8. Who may do what

| Action | Who |
|---|---|
| Change the workflow, script, allowlist, caps or gates | reviewed pull request to main; the owner merges |
| Commit a job file to `pull-jobs` | V2, Refinement, Desk A, Desk B, Main |
| Dispatch a run | Main, or the owner. Never a desk or a tester |
| Read results | anyone (public branch) |
| Remove old results | Main, by a logged commit |

A job file is a request, not a permission. Main checks at dispatch: the registration exists, the pull is the cheapest way to get the data, it is not a repeat of data already held, and it does not read an unread held-out window.

## 9. Security checklist (each item is also a gate in section 10)

1. Host pin: one constant host; every built URL is re-parsed and compared before sending.
2. No key: no `secrets.*` other than the built-in token; no `Authorization` header anywhere; the script never reads an environment variable whose name contains KEY, TOKEN or SECRET.
3. GET only: no `data=`, no `method=`, no POST, PUT, PATCH or DELETE in the script.
4. Redirects refused.
5. Generic User-Agent, no personal details, no repository owner's name or address.
6. Token scope: `permissions: contents: write` and nothing else (it is needed to push the data branch). The built-in token cannot be limited to one branch, so three things limit it in practice: the only push command names `pull-data` explicitly; the script itself never runs git; and main must have branch protection so a workflow token cannot push to it (to be confirmed by the owner in the repository settings; this design cannot verify it).
7. Pinned actions: `actions/checkout` at a full commit hash, as the recorders do; no other action.
8. No `pull_request_target`, no trigger other than `workflow_dispatch`.
9. No shell interpolation of inputs or of anything read from the job file: inputs go through `env:` and a pattern check; the job file's path is passed to Python as an argument; nothing from the job file or from Kalshi's answers is ever placed on a command line, in a file name (file names are counters), or in a git message beyond the checked job id.
10. The job file cannot make the runner request anything off the allowlist: there is no path field; unknown `ep` values and unknown keys are refused.
11. Path traversal: `..`, `/`, `\`, encoded forms (`%2e`, `%2f`, `%5c`) and any `%` are refused in every value.
12. Query injection: `&`, `?`, `#`, `=`, and a newline or carriage return in any value are refused; the query is built only by the standard encoder.
13. Standard library only: no `pip install`, no downloaded code, so nothing new can run on the runner.
14. Bounded work: request cap, size caps, time cap, day cap, single concurrency group, stop date.
15. Kalshi's answers are stored, never executed, never evaluated, and only two things are read from them by the script: the HTTP status and the paging cursor.
16. Nothing under `functions/`, nothing on the page, no Firestore, no deploy.

## 10. Gates the test file must carry (`test/kalshiPullGates.test.js`)

| Gate | What it proves |
|---|---|
| KP1 | The workflow's only trigger is `workflow_dispatch`; the words `schedule`, `pull_request`, `pull_request_target`, `push:` and `workflow_run` do not appear under `on:` |
| KP2 | `permissions` is exactly `contents: write`; no secret other than the built-in token is named |
| KP3 | Every `uses:` is pinned to a 40 character commit hash; only `actions/checkout` is used |
| KP4 | No `${{ inputs.` or `${{ github.event.` appears inside any `run:` block; both inputs are pattern-checked in the first step |
| KP5 | The script names exactly one host and it is the pinned one; the only base path is `/trade-api/v2` |
| KP6 | The script has no POST, PUT, PATCH, DELETE, no request body, no `Authorization`, no cookie, and reads no key-like environment variable |
| KP7 | Redirects are refused (a mocked 302 is recorded as a failure and not followed) |
| KP8 | The endpoint table in the script equals the list in this document, id for id and template for template (the list is copied into the test) |
| KP9 | Traversal: for every field of every endpoint, values such as `../portfolio/balance`, `..%2f..`, `a/b`, `a\b`, `%2e%2e` are refused and no request is sent |
| KP10 | Query injection: values such as `X&status=open`, `X?x=1`, `X#y`, `X\r\nHost: evil`, `X=1` are refused and no request is sent |
| KP11 | A job file with an unknown key, an unknown `ep`, a `url` or `path` field, more than 600 requests, a bad `owner`, or a size over 64 KB is refused before any request |
| KP12 | With a mocked fetch: the pace is at least 1 second between sends; a 429 backs off and never loops; five refusals end the run; the request cap ends the run with `stopped_at_cap`; pages count against the cap |
| KP13 | Built URLs for a table of valid jobs equal an expected list byte for byte, and every one re-parses to the pinned host and its own template |
| KP14 | The only git push in the workflow names `pull-data`; `main`, `quote-data` and the other data branches are not pushed; the push uses the six-try loop; concurrency never cancels |
| KP15 | The stop date is checked in the workflow's first step and in the script, and the two dates are equal |
| KP16 | File names on the data branch are counters and the checked job id only; a hostile job id or a hostile answer cannot create a path outside `pull/<id>/<run>/` |
| KP17 | The script imports nothing outside the standard library, and the workflow has no install step |
| KP19 | Dry run: with `dry_run` true and a mocked fetch that fails the test if called, a valid job prints its URL list, sends nothing and the workflow's push step is skipped; an invalid job fails with the reason |
| KP20 | The `heldout` field is required: a job file without it, or with an empty value, is refused before any request |
| KP18 | The security scan (`.claude/skills/security-audit/scripts/scan.js`) still passes with the new workflow, and `test/recorderPushRetryGates.test.js` knows the `pull-data` loop |

The security agent reviews the pull request before the owner sees it, as for any workflow change.

## 11. Runner minutes

A run is checkout (about 20 seconds), the requests at one a second, compression and the push (about 20 seconds). GitHub bills whole minutes.

| Requests in the job | Wall time | Billed minutes |
|---|---|---|
| 60 | about 2 minutes | 2 |
| 180 | about 4 minutes | 4 |
| 300 | about 6 minutes | 6 |
| 600 (the cap) | about 11 minutes | 11 to 12 |

For comparison, 600 requests from the research sandbox at the shared 12 a minute take 50 minutes of the whole team's budget. Scheduled work is free on a public repository, but the Charter's guideline is 250 runner minutes a month for new work: that is about 20 full-size pulls a month, or about 60 pulls of 180 requests. The day cap of 6 dispatches bounds the worst day at about 70 minutes.

## 12. What this design does not do, and open points for Main and the owner

- It does not know what is held out. A pull can fetch the result of any settled market, so the held-out rule is enforced by Main at dispatch and by the `heldout` field being filled in honestly. This matters: see the held-out audit this desk is running in parallel.
- It does not check that a pull is new. Main compares the job with data already on the data branches.
- Kalshi's limit for unauthenticated reads from a GitHub address is not known. The pace is conservative and a 429 is always obeyed; if the first runs see refusals, lower the pace by a reviewed edit, do not add retries.
- Kalshi's own terms for automated reads of the public API are on Main's permitted list; this document relies on that and did not re-read them.
- The built-in token's reach (item 6 in section 9) depends on branch protection for main, which only the owner can confirm.
- Two names need the builder's check against existing code: the query parameter names of the batch candle call and of the multivariate collection calls.
- Not in this version: the perps list under `/margin`, the order book.
- Before building (in this order): the terms read above; the owner's answer on branch protection for main; then the pull request with the script, the workflow and the gates, reviewed by the security agent.
