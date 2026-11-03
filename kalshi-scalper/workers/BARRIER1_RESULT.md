# BARRIER1 result (run once, 2026-11-03): NOT_ENOUGH_DATA

Registration `workers/BARRIER1_REGISTRATION.md` (sha256 `512123a8ece9696c3c23cfe8d1dfc721cfe43d3e0270fc800df7809a70a5e19c`, pushed before any barrier
price or outcome). Code `src/scalper/barrier1.py`, `tests/test_barrier1.py`, raw print `workers/BARRIER1_output.txt`. Research only.

## What exists (census of the public series list, 15,679 series; touch-style crypto, gold, oil, index, rates, gas)
- Barrier / touch markets that exist with SETTLED history: only the **monthly one-touch** series. Counts of settled markets, 3 settled
  months each (Aug, Sep, Oct 2026; 8 more markets per series are still active for Nov and Dec): `KXBTCMAXMON` 37 (4 yes), `KXBTCMINMON` 34
  (2 yes), `KXETHMAXMON` 21 (2 yes), `KXETHMINMON` 22 (2 yes), `KXSOLMAXMON` 27 (4 yes), `KXSOLMINMON` 24. Other coins' monthly series
  (XRP, DOGE, BNB, HYPE, TON, NEAR, ZEC) exist but were NOT read (see limits).
- `KXBTCMAXW`, `KXBTCMAXD`, `KXDOGEMAXW`, `KXBTCMAXM`, `KXETHMAXM` returned **0 markets** (listed series, no markets). Yearly / quarterly / "above K by date" /
  "hit 100k" series (`KXBTCMAXY`, `KXBTCMAXQ`, `KXBTCABOVE*BY`, gold `KXGOLDYEAR`, oil `KXWTIMAXM`, index `KXINXMAXM`, 10Y, gas) have one event a
  year or an unreadable underlying for this model: census only, not traded.

## Limits of this run (said plainly)
- Kalshi's public API rate-limited the shared host (429 on nearly every call for the whole session), so only BTC (6 events) and one ETH
  event reached the candle stage; **77 markets carry a quote and a model, 88 had no candle yet**. ETH (5 events), SOL (6) and the other
  coins were not priced. That is a data-access gap, not a result.
- **Pre-outcome bug found and fixed (before any rule number was read):** a touched market CLOSES EARLY at the touch, so `close_time` of a YES
  market is the outcome. The first draft used it as the horizon T (which leaks the result). The final code takes the horizon from the event
  ticker's scheduled end (11:59 PM ET). The registered text said "market close"; this is the corrected, non-leaking reading of it.

## Result
- **BAR-CHEAP:** development **n = 3** trades, all in one event (Sep BTC), 0 wins, mean net -8.9c, PF 0.00; holdout n = 0. **BAR-RICH:** n = 0.
  Verdict **NOT_ENOUGH_DATA** (3 under 150), not FALSIFIED: three correlated trades say nothing.
- Information only (all 77 modelled markets, no rule): model touch probability vs the market. Model p under 0.1: 50 markets, 0 yes, mean
  model 1.4% vs mean ask **14.4%** (the lottery strikes are priced ABOVE the model, the opposite of the idea); 0.1 to 0.3: 12 markets, 0
  yes, model 18.6% vs ask 17.4%; 0.3 to 0.6: 11, 27% yes, model 44% vs ask 42%; over 0.6: 4, 50% yes, model 74% vs ask 72%. **The ask tracks
  the reflection-principle model closely**, so the premise (touch markets priced near the terminal probability) is not supported: the market
  already prices roughly 2 x N(-d). In Sep the model (14 day vol 46%) sat above the cheap asks (0.35 vs 0.18, 0.25 vs 0.12) and they
  lost, which says the market was using lower vol, not that it ignored the barrier. Stale quotes on thin far strikes (ask 0.99 / bid 0) are
  common in the Sep Bitcoin-min event and are not tradable prices.
- Internal consistency (touch <= 2 x terminal against Kalshi's terminal ladder): not run, no same-horizon terminal ladder exists at a
  monthly horizon for any coin read.

## Forward plan (dated freeze)
- Rule frozen exactly as registered (look = open + 48 h, hourly ask, 14 day OKX hourly vol, ratio 2.0, ask 3c to 30c, hold to settlement) on the
  monthly series listed in the registration plus any new monthly one-touch coin series. Every new monthly event adds 8 to 10 strikes per series.
- Qualifying rate on what was read: 3 trades in 6 BTC events (about 0.5 per coin-month), all clustered inside one event, so effective independent
  events are about 1 per coin-month. With 7 coins that is about 3 to 4 qualifying trades a month, **about 11 to 13 months to 40 forward
  trades and over 3 years to 150**, with strong within-event correlation (one price path decides a whole event). Read date if kept: the October
  2027 event or 40 fills, whichever is later. Not worth waiting for as a primary line; a cheap by-product of any monthly pull.
- Capped-probe spec: **none** (no rule is positive in both halves; nothing to probe).

N +4 (two rules). Net finding: touch markets are priced near the model; no edge found, none disproved at this n.
