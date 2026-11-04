# TENNIS1 result (2026-11-04): NOT_ENOUGH_DATA (prices-only census; no outcome was ever joined)

Registration: `workers/TENNIS1_REGISTRATION.md` (sha256 `986786be6be818d89e9e464c495710a94f971d37fc6adaf47e612cbdc92df5c3`, commit eb03b9d). Code `src/scalper/tennis1.py`, tests `tests/test_tennis1.py`. Cheap side only; no favourite-side figure was computed. The frozen third (matches from 2026-10-03T16:00Z) was never listed, fetched or joined.

## What was run
- ESPN results (ATP and WTA feeds, 2024-01-01 to the cut, 41,248 completed singles rows) gave a walk-forward Elo per gender (no surface; Sackmann files are blocked in this sandbox).
- Universe: 7,281 Kalshi ATP and WTA tour-level events (4,778 + 4,760 listed; 4,082 + 3,925 matched by both names; 3,489 + 3,591 with both players ready, less events with no result field) before the cut.
- Candle fetch (look = last two-sided 1 minute quote 10 minutes before the ESPN start) for the first 1,279 events in time order, then stopped: Kalshi's rate limit on this shared egress (HTTP 429 on 40% of calls at 2 s spacing; about 4 requests a minute sustained) puts the remaining 6,000 events at about 25 hours.

## Prices-only census (no result read)
1,279 events fetched: 29 had no valid look, 794 had no side with ask 3c to 30c, 456 cheap-side rows, **13 treated** (Elo >= 3x ask, ask <= 0.30). Treated share 1.02% of events (95% interval 0.47% to 1.57%). Projected on all 7,281 events: **about 74 treated trades (interval 34 to 114)**, below the registered 150 even at the top of the interval. Rule 3 of the registration: under 150 treated trades is NOT_ENOUGH_DATA, decided without reading any outcome.
Why so few: the market and a results-only Elo rarely disagree by 3 times on a cheap side, and 62% of matches have no side at 3c to 30c (the favourite is above 70c and the other side above 30c is rare in tennis, mid-priced matches dominate).

## Verdict and forward plan
`NOT_ENOUGH_DATA` for ATP and WTA tour level. `NOT_RUNNABLE` for Challenger, ITF and darts (no free results source reachable: Sackmann and tennis-data blocked, ESPN is tour level). `NOT_ENOUGH_DATA` for UFC (643 events, a few treated), PGA head-to-head, table tennis, MMA, boxing. Treated accrues about 2 per 100 tour events: at about 400 tour events a week the post-cut third gives about 8 treated a week, so 150 needs about 18 more weeks of post-cut data plus the 74 pre-cut, roughly **mid-March 2027**, and only if the cut-date third is used as the forward read (candles for 5 treated a day are cheap; no fetch of a full universe is needed, only events whose ask is already 3c to 30c). Reopening the other sports needs the Sackmann CSVs (allow the host) for Challenger and ITF, where the event count is 10 to 20 times larger. Resume the fetch with `python -m scalper.tennis1 fetch` (cache `/tmp/t1/tennis1`, outside the repo and lost on container restart). No outcome was joined, so the count N is +2 as registered.
