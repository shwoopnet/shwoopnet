# Result: BOOKS2 (totals and spread ladders, far cheap strikes vs a normal around the DraftKings close), 2026-11-04

Registration `workers/BOOKS2_REGISTRATION.md` (sha256 prefix dadbcb5bc64011d5, pushed before any line, score or candle was read). Code `src/scalper/books2.py`, `books2_run.py`, tests `tests/test_books2.py`. **N: +4** (T and S, +2 each). Cheap side only; no favourite-side result was computed. Frozen W3 never fetched or joined.

**Series found:** totals KXNCAAFTOTAL (8,864 settled markets in the join), KXNFLTOTAL 1,013, KXMLBTOTAL 4,862; spreads KXNCAAFSPREAD 11,327, KXNFLSPREAD 1,372, KXMLBSPREAD 3,444. NBA and NHL: no pre-W3 games in the ESPN file.
**Odds coverage:** DK total and home spread present for NCAAF 501, MLB 396, NFL 50 games (947). Fitted sd (first two thirds, 631 games with final scores): totals NCAAF 15.60, NFL 14.96, MLB 4.47; margins NCAAF 14.94, NFL 13.47, MLB 4.59 (the priors used only to trim the fetch were 14/10/3.2 and 16/13/3.3, so tails at fit sd are wider than the fetch prune assumed: harmless, the prune only drops near-centre strikes).
**Fetch economy deviation (stated):** to fit the shared API, candles were fetched for the TEST third first (Sep 19 to Oct 3) and the fit two thirds only partly (college football totals); the fit-third rows are information only and are incomplete. Test-third fetch complete (3,780 strike-markets with a candle; valid look: T NCAAF 3,642 of 4,063, T NFL 210/227, T MLB 978/1,137, S NCAAF 2,315/2,560, S NFL 272/296, S MLB 524/858 across all fetched).

**Primary (out-of-sample test third, 319 games):**
| | cheap strikes | gap model p minus ask (median, p90) | control win vs ask vs model | control net | PF | treated (p >= 3 x ask) |
|---|---|---|---|---|---|---|
| T totals | 2,530 | +1.07c, +5.79c (NCAAF +0.24c, NFL +2.81c, MLB +2.86c) | 0.150 / 0.167 / 0.181 | -2.74c, z(game) -2.62 | 0.81 | n 11 |
| S spreads | 2,931 | +0.22c, +3.80c (NCAAF +0.12c, NFL +1.89c, MLB +0.80c) | 0.151 / 0.168 / 0.174 | -2.69c, z -2.28 | 0.82 | n 0 |

Win rate vs price by ask bucket (T): 3c-10c win 0.058 vs ask 0.070 vs model 0.101; 10c-20c 0.129 / 0.148 / 0.160; 20c-30c 0.230 / 0.248 / 0.253. S similar (0.043/0.074/0.078, 0.126/0.146/0.152, 0.236/0.243/0.249). The cheap side wins LESS than its ask in every bucket, and the normal-around-the-line model overstates it more than the market does: the market is closer to the truth than my model (model p is above the realised win rate in all buckets).
**Treated T, n 11 (11 games):** win 0.091 vs ask 0.037, mean net +5.05c, PF 2.39, halves +15.9c / -4.0c (n 5/6). A handful of trades, one hit decides it; no claim. S treated: 0.
**Verdict: both families NOT_ENOUGH_DATA (11 and 0 of 150); prediction held** (gap median -0.5 to +1.5c: T +1.07c, S +0.22c; treated 0 to 40; control -1c to -3c: -2.7c). Not FALSIFIED by the rule (under 150 trades), but the control (all cheap strikes) is negative at z -2.3 to -2.6 and the model is worse calibrated than the ask, so there is nothing to follow up.
**Months to go (T):** 11 treated in the 2-week test window, about 24 a month in season, so about 6 more months for 150; S has no rate. The seasons end (MLB done) and a forward test needs a recorder of the DK close at each pre-game look; none built, and not recommended: the evidence is that Kalshi total and spread ladders are priced no worse than a normal around the book line.
Forward plan: none. One lead only if wanted: the normal is a poor tail model for football scores; an empirical residual distribution would be a new registration and would not change the finding that the cheap side wins less than its ask.
