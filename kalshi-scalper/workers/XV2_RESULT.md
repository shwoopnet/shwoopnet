# XV2 result (2026-11-06, feasibility census only, no price or outcome of any matched event read): NOT_ENOUGH_DATA

Family: cross-venue price disagreement (other venue's price far above Kalshi's cheap-side ask 3c to 30c).

Registered intent (written before any price or outcome was fetched, this file is both): non-sports, non-release, non-crypto pairs (primaries, state elections, politics, culture) matched by title and close date; trigger = other venue price at least 6c above the Kalshi ask, buy the cheap side at the ask, held, fee 7% x C x p x (1-p) rounded up, C = 10; frozen last third (cut 2026-10-03T16:00Z) never fetched. Counterparty: slow Kalshi makers on thin political markets. Prior of a pass 2%. Kill: under 150 independent matched triggers = NOT_ENOUGH_DATA; z under about 5.32 = FALSIFIED. N +1 (running about 730,491 plus 500,000 PERPGEN).

## Feasibility (what the sandbox allows)
- Polymarket gamma and CLOB: reachable (gamma 200 with redirect, CLOB 200).
- Manifold API (api.manifold.markets/v0): reachable (200). Play money, no sensors behind its price.
- Metaculus: HTTP 403 from here. Treated as BLOCKED, no workaround tried.
- Kalshi events list: reachable; 8,000 settled events listed (Sports 2,882, Elections 1,249, Crypto 932, Financials 723, Commodities 594, Politics 466, Entertainment 397, Mentions 271, Economics 197, Weather 164); 2,418 in Politics, Entertainment, Elections, Science, Companies, Economics.
- Polymarket closed-event listing is capped at 100 rows per window query (offset past it errors 422), so a full census needs per-day windows; the sample window 2026-08-06 to 2026-10-03 returned 100 events, 69 non-sports, mostly primaries.

## Matching census (titles only, outcomes not read)
Loose title match (4+ shared words, Jaccard over 0.6) of the 2,418 Kalshi non-sports events against the 69 sampled Polymarket events: 8 matches, of which only 2 (Berlin and Mecklenburg-Vorpommern state elections) are true same-event pairs; the rest pair a Kalshi "4th place" or "2nd place" market with a Polymarket "winner" event (different question, not matchable unambiguously). Scaled to a full census the true pairs are primaries and state or national elections: tens of independent events, each with a few cheap candidates, correlated by state and night, against the 150 independent triggers needed.

## Why not run it
1. Count: clearly under 150 independent triggers; elections cluster on a handful of nights (ELECT1 had 33 states on one night).
2. Prior evidence: PM1/PM2/PM3, XVENUE1 and FAMXV found the two venues are one price (sports median gap 0.5c, 1.2% of games with a 4c gap, identical Brier). Political markets are arbitraged by the same desks.
3. Overlap: Kalshi election cheap sides were covered by ELECT1 (65 of 65 lost, -1.02 per trade).
4. Manifold is a different kind of counterparty (play money), and matching its markets to Kalshi's by title is looser still.

Verdict: **NOT_ENOUGH_DATA** (not runnable at a powered size). Killed assumption: another venue's price for the same event carries information Kalshi's quote lacks. Smallest live probe: none. Scratch: scratchpad/xv (census only).
