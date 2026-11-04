# GOLF1 result (2026-11-04): NOT_ENOUGH_DATA (treated trades), cheap side only, no Kalshi result read

Registration `workers/GOLF1_REGISTRATION.md` (sha256 `e5058e0a3bf8c2904b5b72410192dcb059217a309763766c7118aa8bad02968e`, pushed before any candle). Code `src/scalper/golf1.py`, tests `tests/test_golf1.py` (11 synthetic, passing). Frozen third (markets closing from 2026-10-03T16:00Z) never listed, fetched or joined.

## What ran
- ESPN per-round strokes for 141 PGA events (keyless, 1 request a second). Fitted on the first 44 of 66 tournaments: shrink k 10, sigma 2.83 strokes a round.
- Kalshi candles (90 minute time box, md5-ordered tournaments, one thread, 3.3 s pause; the batch endpoint serves only live markets, 241 of 5,819 candidate markets, so 5,578 historical markets needed one request each at about 6 to 9 s with 429 backoff): **11 of 66 tournaments, 36 of 274 (tournament, series, look) groups fully fetched, 520 look quotes.**
- `golf1 project` (prices and model only; no Kalshi result and no golf result was joined): **344 cheap-side rows (ask 3c to 30c; 290 YES, 54 NO) in 11 tournaments; treated (model probability >= 3x ask, max 3 per group): 1, in 1 tournament. Projected on all 66 tournaments: about 6 treated trades** against the 150 bar. Gate says NOT_ENOUGH_DATA, so **no scored read was run: n win-versus-price and PF versus control do not exist** (by design; the registration forbids reading results below the bar).

## What the prices alone say (no outcome)
The model-to-ask ratio of the 344 cheap-side rows has median 0.99, 90th percentile 1.49, maximum 3.76; 2.3% of rows are at 2x or more and 9.9% at 1.5x or more; mean model probability 0.190 against mean ask 0.185. So a results-only stroke model agrees with the quote almost exactly on the long tail (the quoters are pricing the same leaderboard), and a 3x gap is a once-in-a-few-hundred event: about 0.1 treated trades per tournament (one event; 95% upper bound about 0.4). Even at that upper bound and one tournament a week, 150 treated trades is about 350 weeks; the registered forward plan (wait for the post-cut tournaments) cannot reach 150 in any realistic time. The count problem is the model-ratio rule, not the sample of tournaments.

## Verdict and forward plan
**NOT_ENOUGH_DATA** (power: 66 tournaments at best, all three series and both looks of a tournament dependent; about 6 projected treated trades). Not FALSIFIED: no outcome was read. Forward options, none built here: (a) a looser ratio (for example 1.5x, about 10% of rows, roughly 6 trades a tournament, 150 in about 25 tournaments) would need a NEW registration with its own N; (b) a pre-round quote recorder at the two looks for the weeks of the PGA fall series and the 2027 season; (c) drop this family: the agreement between model and quote suggests little to find with a results-only model. Prior of a pass was 2% and nothing moved it. Kalshi's historical candle endpoint is the bottleneck (about 8 requests a minute); a full 66-tournament fetch is about 12 hours polite.

N +2 (about 730,373).
