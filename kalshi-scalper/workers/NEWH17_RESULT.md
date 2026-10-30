# NEWH17 result (2026-10-30, research only)

Screen `workers/NEWH17_SCREEN.md`, registration `workers/NEWH17_REGISTRATION.md` (commit 191233e: zero tries). Nothing was scored because nothing
survived the screen. Verdict words below are status labels for the dated looks; no rule has a PF, an n or a z.

## What was found

- 12 candidates on untested 15 minute ground (the alt CF series, the Pyth commodity and FX series, the yields, Brent, settlement mechanics, ties,
  the strike chain, cross-duration). All 12 dropped on the cost arithmetic or on data windows before any outcome was read.
- **The bar is harder than the brief says.** On a 1c spread series a coin flip taker entry breaks even at 52.3% and needs **62.2%** (not 58%) for
  PF 1.5; the all-in price at 50c is 52.3c (ask 50.5c plus 1.8c fee). NEWH16's best cell (56.6% hit rate) printed PF 1.18, which fits the formula.
  Documented 15 minute effects are 1 to 3 points. So no trailing-feature or lead-lag coin flip entry can pass, and the entries that could (far from
  50c) are the banned favourite and cheap-side families. This is the cleanest statement yet of why the search keeps ending the same way.
- One look: TIEPERSIST (does a stale-feed tie repeat? discovery, tie flags only): 0 ties after 163 ties across 26 series. Mechanism absent.
- Series younger than the holdout have no discovery window: the four Treasury yields (12 days), Brent (10 days), AUD/USD and USD/CAD (11 days
  before the holdout).

## Verdict labels (dated looks, not tries)

| Item | Label | Why |
|---|---|---|
| ROLL (contract roll jumps on Pyth commodities) | NOT_ENOUGH_DATA | about 15 events pooled since Aug 24 against 100/50/30 trades |
| YIELDMAKE (resting bid on the 25c yield spreads, tape fills) | NOT_ENOUGH_DATA | 12 days of listing, all inside the frozen holdout; re-look about 2026-11-30 |
| everything else | not tried | best case below 62% or a reworded closed test |

## Counts

Tries: 0. Looks: 1. N unchanged, about 728,670 (Bonferroni z bar 5.27). Holdout unread.

## Step 3: weekly series census (built and wired)

`src/scalper/seriescensus.py`, wired into `autoscore.check()` after the RECORDERS block (state key `series_census` in `data/autoscore_state.json`),
`tests/test_seriescensus.py` in `run_tests.sh`. Once every 7 days it reads Kalshi's public `/series` (frequency `fifteen_min`), asks for one settled
market of each series not yet known to have settled ones, and logs one line to `AUTO_LOG.md` under id `SERIES`: `SERIES CENSUS: N fifteen_min series,
M with at least one settled market`, or `NEW SERIES <names> now settled: ...` when a series went from none to some. Counts only, errors caught, a
failed week retries on the next pass. Live check (throwaway state): 38 series, 27 with a settled market, the same as the NEWH15 inventory. The first
real run saves the baseline (no NEW SERIES). Nothing was started or deployed.

## Proposals for the owner (nothing built)

1. Treat 62% at a coin flip price as the standing arithmetic in every brief; stop spending tries on any entry whose mechanism is worth under
   10 points.
2. The only remaining places an edge can be big enough are timing (second resolution latency, RECORD1 and R6 are collecting it) and structure
   that is not a coin flip. Both are waiting on recorders already running.

## Proposed README section (for the lead to merge; I did not edit README.md)

```
## Result: NEWH17 (feasibility screen of untested 15 minute ideas; 0 tries; 2026-10-30)

Twelve candidates on series the ledger had not covered (alt CF averages, Pyth commodities and FX, the Treasury yields, Brent, ties, the strike chain,
contract rolls, cross-duration) were priced on the cost arithmetic before any outcome was read (`workers/NEWH17_SCREEN.md`). A coin flip taker entry
on a 1c spread series breaks even at 52.3% and needs 62.2% for PF 1.5 (the brief's 58% is PF 1.27); effects in the literature are 1 to 3 points, the
best case for the spot-versus-lagged-average open is 57.9% before the book prices any of it. None reached the bar, so nothing was registered (zero
tries, N unchanged about 728,670). One counted look: after a tie (stale print) the next window was a tie 0 times in 163 (26 series, discovery).
ROLL (about 15 events) and YIELDMAKE (the yields have 12 days, all of it the holdout) are NOT_ENOUGH_DATA; YIELDMAKE is a dated re-look about
2026-11-30. Also built: a weekly series census in autoscore (`scalper.seriescensus`; a series going from no settled market to one starts its
AUTO_LOG line with NEW SERIES).
```
