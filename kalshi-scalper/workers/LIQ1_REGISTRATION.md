# LIQ1 registration: is the cheap side near fair when the quote is tight or the candle is busy? (2026-11-04)

Registered before any outcome was joined. Discovery only: no live code, no `functions/`, no L1, no OICORE, no promote verb. **Owner rule (strict): CHEAP SIDE ONLY, ask 3c to 30c.** No entry above 0.30 is built, counted, scored or printed (code asserts it); no favourite-side result is computed; no 15 minute crypto or gold candle trigger. Name note: `src/scalper/liq1.py` already belongs to the earlier LIQ1-INFO liquidation check, so this code is `src/scalper/liq1_spread.py` (ledger name LIQ1 liquidity).

## Duplicate check
README and workers searched for spread, volume, liquidity, CALIB1, OVERROUND1, BOOKS1, USWEEP1/2/3, NEWLIST1, VOLSLOT1, SPIKE1 and OICORE_SHAPE_INVENTORY. Spread and volume appear only as (a) the `valid_quote` filter (spread 10c or less) and a "spread at most 1, 2 or 4c" filter inside the old 15 minute crypto/gold search grammar (favourite-style, different data), (b) NEWLIST1 reporting the quote spread as a descriptive column per cell, (c) volume surge or thin-move scalps S35 to S39 on 15 minute candles (round trips on crypto/gold, not cheap side to settlement). CALIB1 conditions on category, ask bucket, life class and time to close; OVERROUND1 on the event overround. **No cheap-side test conditioned on quote spread or candle volume has been run: not a duplicate.**

## Hypothesis and mechanism
CALIB1: the cheap side wins about 0.4 to 0.65 of its price; OVERROUND1: the loss sits in padded books and LOW overround is near fair. Hypothesis: where competitive market makers keep a tight spread (or the candle actually traded) the cheap side is near fair or better; where the quote is wide or untraded it is stale and overpriced. Counterparty: the maker or the stale quote on the other side. Prior: low. A tight spread on a longshot (1c to 2c on a 3c to 30c ask) is partly a price effect, so I expect the fee (about 0.3c to 1.5c) to eat what little there is.

## Data (no new fetch)
The CALIB1 development pool: USWEEP1, USWEEP2, USWEEP3 candle caches (`census.jsonl`, `candles.jsonl`, outcomes) and `data/newlist1.sqlite` (table `cd`: end_ts, bid, ask, vol, oi). Candle rows store (end, bid, ask, volume), so both features exist at the look. Looks are each cache's own, exactly CALIB1's (`LOOKS`, NEWLIST1 age 1/3/6 h and late). One entry per (market, look), first source wins. The frozen last third (from 2026-10-03T16:00Z; NEWLIST1 close >= `t2` dropped) is never fetched, read or joined. NEWLIST1 now holds 2,777 cheap entries (CALIB1 saw 2,617: the cache grew after CALIB1 ran), so the pool is 16,201 entries in 3,558 events, not CALIB1's 16,041.

## Definitions (fixed here)
- **Entry** = CALIB1's: for a two sided quote (0 < bid < ask < 1) at the look candle (latest candle at or before the look, at most one period old), the side whose ask is in [0.03, 0.30] (NO ask = 1 - bid), bought at the ask, held to settlement. Fee 7% x 10 x p x (1-p) rounded up to the cent per 10 contracts.
- **spread** = (ask - bid) of the YES book at the look candle, in cents (identical for the NO side). **volume** = the look candle's traded volume (contracts in that candle's period; 0 when none).
- **Fit set** = the first two thirds of EVENTS by earliest close time (ties by event id): 2,372 of 3,558. Cuts are the lower empirical quantiles (an observed value) of the fit-set entries, fixed by `fit_cuts`: spread_lo (33.3th) = **2.0c**, spread_hi (66.7th) = **5.0c**, vol_lo = **0**, vol_hi = **30.93**. They are recorded here from `extract`, which printed counts and these four cuts only.
- **TIGHT** spread <= 2.0c (trade). **WIDE** spread >= 5.0c (placebo). **HIGHV** volume > 30.93 (trade 2). **LOWV** volume <= 0 (placebo 2; 65% of entries have zero volume, so the low tercile is "did not trade"). **CONTROL** = all cheap entries.
- Each group: at most **2 entries per event**, the two with the smallest md5(market|look). Events are the cluster for every interval (2,000 bootstrap draws, seed 20261104). Halves D1/D2 = first and second half of the group's events by earliest close time. The fit set and the out-of-fit last third of events are also reported (observation, not a gate).

## Rules, kill and prediction (fixed before any outcome is joined)
Two rules: TIGHT and HIGHV. Each is `LEAD` only if mean net per contract after fees is above 0 in BOTH D1 and D2 and the profit factor of the whole group is at least 1.5. `NOT_ENOUGH_DATA` under 150 trades (census: TIGHT 3,544, HIGHV 2,754, WIDE 3,362, LOWV 4,152, CONTROL 6,515 after the cap, so the census does not stop the test). Otherwise `FALSIFIED`. Placebos (WIDE, LOWV) and control are reported with the same statistics and are not rules. Nothing else is tuned; no other feature, cut, look or bucket is tried.

**Prediction.** TIGHT cheap side is still negative after the fee, about -2c to -6c per contract, PF 0.5 to 0.9, better than CONTROL (about -5c) and WIDE (about -6c to -9c) but not above zero; HIGHV likewise. Verdict `FALSIFIED` for both (about 85%).

N: 2 rules, **+4** (tercile cuts fixed, nothing else varied).
