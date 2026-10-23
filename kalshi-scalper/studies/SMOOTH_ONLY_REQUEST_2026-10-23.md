# Bitcoin and Ethereum "smooth climb only" (request for the build session; the owner said "1" in the research session on 2026-10-23)

This is a LIVE change, so the build session confirms with the owner before building. It replaces the Bitcoin and Ethereum entry; every other series is untouched.

## Spec
- **Series:** KXBTC15M and KXETH15M only.
- **Entry time:** both at the 6 minute decision (the candle ending about 360 s before the close; the same window the bot uses for Ethereum today). Bitcoin leaves the 10 minute early-probe list. (The public-candle forward reads of the 10 minute entry, FWD7, are scored on candle history and are not affected.)
- **Order only if the path is smooth:** `smooth` = at least 4 earlier 1 minute candles AND every minute change of the favourite side's mid (from the market's first candle through the decision candle) is at least -0.005 AND (the decision candle's mid minus the first candle's mid) is at least 0.10. The favourite side, band (ask 0.88 to 0.97) and price rules are exactly as today. If the path is not smooth, place no Bitcoin or Ethereum order.
- **Size:** 1 contract, no add-on, held to settlement, the 25c exit as today, the one-crypto-order rule and all stops and caps as today.
- **Keep the logging** (flips, flips0, earlierCandles, askAtDecision, rise3, rng5) and add the path's `minStep` and `climb`.
- Parity: `studies/smooth_parity_vectors_2026-10-23.json` (six paths with the exact `smooth`).

## Kill rules (registered in the README before any order)
Remove Bitcoin and Ethereum from live orders if: after 40 smooth fills there are 3 or more losses; or after 100 fills their combined net is under $0; or the 2026-11-12 forward read FLIPS0-F is FALSIFIED. Review at the 2026-11-17 export.

## Why
Backtest (README, "SMOOTH20", "SMOOTH2" results): Bitcoin and Ethereum at the 6 minute entry, largest one-minute pullback at most 0.5c: 258 entries over 78 days, +4.78c (Bitcoin) and +3.14c (Ethereum), loss rate 0.6% and 1.9%, profit factor 4.9; the same rule on 16 other series +1.53c over each series' own average (z 2.39). It was chosen from about 240 variants and its discovery z missed the registered bar, so it is a candidate; the forward read is 2026-11-12. Their non-smooth entries average about -0.2c, so the change removes the orders that lose and most of the slot contention with XRP and Dogecoin. About 3 orders a day, about $4 per 30 days at 1 contract if it holds.
