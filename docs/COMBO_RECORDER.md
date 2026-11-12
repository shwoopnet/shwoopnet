# Combo book recorder (Nov 12, 2026, the owner approved)

Research data only. Nothing here trades, signs or holds a key. It records Kalshi's combo (multivariate, exchange_index 1) markets so a paper test of buying either side of a combo (the cheap side or the house side) can be priced with real depth instead of the top of book alone.

**What it records.** Every 30 minutes one poll lists the open combos (`mve_filter=only`, at most 5 pages of 1,000, so at most 5,000 of the many tens of thousands), keeps every combo with a posted bid or ask at any price on the yes or the no side, or any traded volume (widened on Nov 12, 2026 from a yes price of 0.30 or more; an empty side, a bid of 0 or an ask of 1.0000, is not a price), and writes: their quotes (at most 400 rows, with the leg count), the order book of the 40 with the tightest yes spread (best 5 YES and 5 NO bids with sizes), and the public trades of the 15 most traded. The choice is deterministic: tightest yes spread first, then the most volume, then the ticker; a combo with only one side posted has no spread and ranks after every two-sided one, so it is in the quotes (while the 400 row cap allows) but rarely gets a book read. Once a day, in the 00 UTC hour, it also reads settled combos that traded (3 pages) so outcomes sit next to the depth. A coverage row per run says how many combos were listed, whether the list was complete, how many requests and refusals there were, and whether it stopped early. The listing is a sample, not a census: the exchange's order is not ours to choose, so read the coverage file before counting anything.

**Where it goes.** Gzipped CSV files on its own `combo-data` branch (under `combo/DATE/HHMM/`), pushed with the built-in token. Never main, never the other data branches, never published with the site (`_config.yml` excludes `.github`, `scripts` and `docs`).

**Safety.** Public GET endpoints under `/markets` only. No key, no secret, no auth header, no POST, no order path, no Firestore. A plain User-Agent (`shwoopnet-research-recorder`). Redirects are refused. A 429 waits 5 seconds, doubling up to 60; three refusals in a row end the run early and it says so. A hard budget of 90 requests a run.

**Stated plainly.**

| | |
|---|---|
| Cadence | one poll every 30 minutes (48 runs a day) |
| Spacing | at least 6 seconds between requests, so requests per minute never exceed 10 |
| Requests per run | at most 90 (budget); the caps are 5 list pages, 40 books, 15 trade reads, plus 3 settled pages once a day; a trial run of the widened filter used 60, three of them refused and waited out |
| Requests per day | at most 4,320; about 2,900 at the trial's size, about 2 a minute on average |
| MB per day (gzipped) | about 0.7 MB gzipped measured in the trial (about 15 KB a run, 13 KB of it the 400 capped quote rows, so the trial sits at the quote cap); under 1 MB at the caps; about 56 MB over the whole run (80 days). The old filter measured about 7 KB a run and 0.35 MB a day |
| Runner minutes | about 6 a run in the trial (6 min 3 s), 9 at the budget: about 310 to 430 runner minutes a day, 9,400 to 13,000 a month, free on a public repo |
| Ends | 2027-01-31 23:59 UTC by itself (workflow and script); sooner by deleting `.github/workflows/record-combo.yml` |

**Honest limits.** Most combos have an empty book (no bids on either side); in the widened trial 10 of the 40 tightest spreads had any depth, and 3,966 of the 5,000 listed combos had a posted price on some side (the 400 quote rows and 40 books are therefore a small slice of the selection). That is a finding about the market, not a fault. Prices are stored as the exchange returns them, nothing is computed. Gates: `test/comboBookRecorderGates.test.js` (CB1 to CB10).
