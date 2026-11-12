# Combo book recorder (Nov 12, 2026, the owner approved)

Research data only. Nothing here trades, signs or holds a key. It records Kalshi's combo (multivariate, exchange_index 1) markets so a paper test of buying NO on high priced combos can be priced with real depth instead of the top of book alone.

**What it records.** Every 30 minutes one poll lists the open combos (`mve_filter=only`, at most 5 pages of 1,000, so at most 5,000 of the many tens of thousands), keeps the high priced ones (a yes bid or yes ask of 0.30 or more, or any traded volume), and writes: their quotes (at most 400 rows, with the leg count), the order book of the 40 best priced (best 5 YES and 5 NO bids with sizes), and the public trades of up to 15 that have traded. Once a day, in the 00 UTC hour, it also reads settled combos that traded (3 pages) so outcomes sit next to the depth. A coverage row per run says how many combos were listed, whether the list was complete, how many requests and refusals there were, and whether it stopped early. The listing is a sample, not a census: the exchange's order is not ours to choose, so read the coverage file before counting anything.

**Where it goes.** Gzipped CSV files on its own `combo-data` branch (under `combo/DATE/HHMM/`), pushed with the built-in token. Never main, never the other data branches, never published with the site (`_config.yml` excludes `.github`, `scripts` and `docs`).

**Safety.** Public GET endpoints under `/markets` only. No key, no secret, no auth header, no POST, no order path, no Firestore. A plain User-Agent (`shwoopnet-research-recorder`). Redirects are refused. A 429 waits 5 seconds, doubling up to 60; three refusals in a row end the run early and it says so. A hard budget of 90 requests a run.

**Stated plainly.**

| | |
|---|---|
| Cadence | one poll every 30 minutes (48 runs a day) |
| Spacing | at least 6 seconds between requests, so requests per minute never exceed 10 |
| Requests per run | at most 90 (budget); the caps are 5 list pages, 40 books, 15 trade reads, plus 3 settled pages once a day; a trial run used 61 |
| Requests per day | at most 4,320; about 2,900 at the trial's size, about 2 a minute on average |
| MB per day (gzipped) | about 0.35 MB gzipped measured in the trial (about 7 KB a run); under 1 MB at the caps; about 30 MB over the whole run |
| Runner minutes | about 6 a run in the trial, 9 at the budget: about 310 to 430 runner minutes a day, 9,400 to 13,000 a month, free on a public repo |
| Ends | 2027-01-31 23:59 UTC by itself (workflow and script); sooner by deleting `.github/workflows/record-combo.yml` |

**Honest limits.** Most combos have an empty book (no bids on either side); in the trial 4 of the 40 best priced had any depth. That is a finding about the market, not a fault. Prices are stored as the exchange returns them, nothing is computed. Gates: `test/comboBookRecorderGates.test.js` (CB1 to CB10).
