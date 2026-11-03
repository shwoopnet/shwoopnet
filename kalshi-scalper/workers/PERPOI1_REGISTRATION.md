# PERPOI1 registration: perpetual open-interest surge as the trigger for a cheap-tail trade on the HOURLY Bitcoin ladder (written 2026-11-03, before any trigger, count or outcome was computed)

Discovery only. No live code, no `functions/`, no L1, no OICORE change, no promote verb. Local caches only (nothing fetched for this: the perp 1 minute cache is SNAPBACK1's, the ladder candles are `data/conf2_lad.sqlite`).

## Duplicate check (done first)
Looked at README and workers for PERP1/2/3 (daily perp trend, dip, gold/silver: no open interest), PERPFLOW1, FUND1, SNAPBACK1 (perp OI FALL plus a big move as a FADE entry traded ON the perp itself: FALSIFIED), XOI1, XCRY1, MECHOI1, LAG15, LADLONG1, OICORE_SHAPE_INVENTORY, OICOREX1. Nobody used the Kalshi PERP's open interest RISE as a trigger for a held-to-settlement trade on the hourly ladder KXBTCD. OICORE/MECHOI1 use the 15 minute market's own open interest; XOI1/XCRY1 cross assets in the 15 minute family. **Not a duplicate. Proceed.**

## Mechanism and counterparty
New leveraged or informed positions arriving in the perp (the venue where size trades) show up first as OI rising together with price moving the same way. The hourly ladder quoters (sparse, 1c wide in the middle, thin tails) may not reprice the tails of the hour that closes 25 minutes later. Counterparty: the ladder makers selling the cheap tail. Honest alternative: the perp is a copy of spot, the ladder already prices spot, and the tail is priced fairly or rich, so the fee is the loss.

## Data
Perp: `/tmp/claude-0/cache/KXBTCPERP_1m.jsonl` (SNAPBACK1's, 1 minute candles with `open_interest` and price, 2026-06-03 to 2026-11-03), grid from `snapback1.grid_from_candles` (price close carried forward, OI carried forward). Ladder: `data/conf2_lad.sqlite`, KXBTCD hourly markets (about 1,500 closes from 2026-08-24, 1 minute bid/ask candles from 55 minutes before each close, result). **Bitcoin only**: KXETHD has only 14 days of candles (ladders.sqlite) and no ETH ladder cache over the perp's span, so ETH is not tested. Daily ladders have no cache; not tested.

## ONE trigger definition (no tuning)
For each hourly close C (a KXBTCD event), decision time t = C - 1500 s (25 minutes before). All quantities use the 1 minute candle ENDING at t or earlier.
- d(s) = OI(s) - OI(s - 10 min) for every minute end s. SURGE at t if d(t) > the 95th percentile of d(s) over the trailing 7 days of minute ends s in (t - 7 d, t]; needs at least 5 days of history and OI(t - 10 min) > 0.
- Perp price move m = close(t) - close(t - 10 min) (carried-forward trade price). Direction +1 if m > 0, -1 if m < 0, none if 0.
- TRIGGER = SURGE and direction nonzero.
## Trade (A, the registered claim)
At the ladder candle ending at t, per strike: YES ask = `ask_c`, YES bid = `bid_c`; both must be present (ask_c in (0,1), bid_c > 0). NO ask = 1 - YES bid. Direction +1 buys YES on a strike ABOVE the perp price; direction -1 buys NO on a strike BELOW it. Among such strikes keep those with the buy price in [0.03, 0.30] (**hard limit 0.30**, floor 0.03) and take the one with the HIGHEST price (nearest the money). One trade per event, 1 contract, bought at the ask (or 1 - YES bid), held to settlement (`result`), fee 7% x C x p x (1-p) rounded up to the cent per order, reported at C = 10 (verdict) and C = 1. No candle at t, or no strike in the range: no trade (counted).
## Try B (separate counted try)
On the same SURGE events regardless of price direction (price move may be zero): best YES tail (strike above the perp price) and best NO tail (below), each as in A (highest price in [0.03, 0.30]); buy the one with the LOWER price (ties YES).
## Control
Hourly closes with the history requirement met and NO surge, direction nonzero, trade built exactly as A. Trigger-minus-control = mean net per trade (C = 10) of A minus the control's, with a bootstrap by close for the difference.

## Windows
Closes from the first usable ladder close to the last, split by date into thirds: discovery, validation, HOLDOUT. The holdout is frozen and UNREAD (no trigger, count or outcome computed there) unless development passes everything below; then read once.

## Numeric prediction (written before)
Trigger rate: the 95th percentile is taken over ALL minutes while the decision minute is any hour, so SURGE at about 5% of closes, half with nonzero same-direction price (the direction field is nonzero nearly always; the surge sign is the test), about 4% of closes; with a quote and a strike in range about 3% = **40 to 60 A trades over about 1,500 closes (about 20 a month)**, development about 25 to 40. Win rate about 13% (price paid averages about 18c; tails paid near fair, slight overpay), payoff about 5x, PF 0.6 to 1.1 after fees, control similar; trigger-minus-control within noise of 0. Expected verdict NOT_ENOUGH_DATA; if enough, FALSIFIED (about 90%).

## Verdict rules (fixed)
- **NOT_ENOUGH_DATA**: fewer than 100 A trades in development (150 in all three windows would need about 7 more months at that rate; the months-to-150 at the observed rate is reported). With fewer than 100 trades PF is reported as information and no FALSIFIED is declared (a 15% win-rate trade has too much variance).
- **FALSIFIED**: with at least 100 development trades, PF under 1.5 in either development half, or under 1.5 in the whole of development, or trigger-minus-control not positive in both halves, or PF under 1.2 at fees x1.2.
- **Survives**: all of the above pass and day-clustered z at least 5.27. Only then is the holdout read once; PF under 1.5 there is FALSIFIED. A survivor gets a capped-probe spec (1 contract, hard limit 0.30, kill rule, worst-day dollars, when 40 fills would exist); nothing trades.
- Try B reported with the same rules and counted separately.

## Count
**N +4** (two rules, A and B, at +2 per rule; the control is a comparison, not a rule). The coordinator keeps the running total (about 730,003 before this; z bar about 5.27).

## Read date
Development read once on 2026-11-03 right after this commit. Forward: when 150 A trades would exist at the observed rate (reported).
