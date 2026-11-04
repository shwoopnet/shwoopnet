# ESPORTM1 result (2026-11-04; registration commit 57edd4e, sha256 fdaf79a9c2a0ba1b5f66adf7c20d363d399be9de36f1c3c3133061b00d086d78, scorer committed after it)

```
K 48.0; qualified events 4142 (fetched 1063), no look 13, no cheap side 679, cheap-side rows 371, treated 68
treated: n 68 mean -5.10c win 0.059 vs mean ask 0.103 PF 0.51 z(match) -1.72 z(day) -1.68
  fees x1.2 PF 0.50
control: n 371 mean -5.30c win 0.164 vs mean ask 0.206 PF 0.70 z(match) -2.80 z(day) -3.05
  fees x1.2 PF 0.69
test third (close after the first two thirds): treated n 29 mean -8.44
halves 34/-4.54c, 34/-5.67c
VERDICT NOT_ENOUGH_DATA
fetched share of qualified 0.26; projected treated on all 265
```

**Verdict: NOT_ENOUGH_DATA** by the registered rule (68 treated in the fetched md5 prefix, under 150). Every number that exists points the same way as the kill rule: treated mean -5.10c (both halves negative, -4.54c and -5.67c, test third -8.44c), PF 0.51, win rate 5.9% against a mean ask of 10.3% (the model flagged the teams the market was right to price low), treated no better than the control (-5.30c, PF 0.70, win 16.4% vs ask 20.6%: the cheap tail loses to the favourite-longshot bias and the fee, as predicted). Had n reached 150 with these halves the verdict would be FALSIFIED. ESPORT1's verdict carries: Kalshi's quote beats a Kalshi-only Elo.

How it differs from ESPORT1: ESPORT1 priced MAP 1 (a symmetric 8c gap, both sides, after-fee edge); this is the whole MATCH, cheap side only, treated at model >= 3x ask. Same Elo family (here per series, fixed K fitted once: 48, the edge of the grid {16, 24, 32, 48}; log-loss 0.6587 on 2,753 first-two-thirds matches), same finding.

Disclosures. (1) Census 4,141 qualified by close-time order, 4,142 by the look-time rule used in the scorer. (2) Batching 8 markets per request was not used: the md5-ordered prefix scatters events across 6 months, so a batch would need a 6 month window against the endpoint's minutes x tickers limit; one request per event, 3.3 s pacing, Kalshi 429s cut the realised rate to about 7 requests a minute: 1,063 of 4,142 qualified events (26%) fetched in the 2.5 hour time box. (3) 679 of 1,050 looked-up events had no side priced 3c to 30c (most matches are close to even); 13 had no valid quote. (4) No regional effect (no field). (5) The scored read happened once; the frozen cut 2026-10-03T16:00Z was never fetched or joined. (6) Quote is not a fill. (7) The fetch loop's time box restarts on a crash restart; it ran once without a restart. (8) Nothing is promoted; no promote verb.

Forward plan. The unfetched 3,079 pre-cut qualified events (about 7 hours at the observed Kalshi rate) would project about 265 treated trades, so the pre-cut data can reach the 150 floor by extending the SAME md5 order (a registered-rule continuation, not a new variant), but the signs make a pass very unlikely. The post-cut matches (never touched) add about 160 qualified matches a week, about 10 treated a week at the observed share (68 treated per 1,063 fetched events, 160 qualified matches a week): 150 post-cut treated trades is roughly 2027-02. Not recommended while both halves and the test third are negative.

N +2, running count about 730,377 (z bar 5.27). Code `src/scalper/esportm1.py`, tests `tests/test_esportm1.py` (7 passing, synthetic). Cache outside the repo in `/tmp/e1m`.
