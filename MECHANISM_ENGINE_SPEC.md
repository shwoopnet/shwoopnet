# Mechanism engine (MECH1), spec for the owner, Nov 17, 2026

The owner: "where's the search engine for unique strategies, NOT RULES." Today's engines (ENGINE1, GEN12/13) tune thresholds on mechanisms we already know, so what they find are versions. MECH1 searches over mechanisms instead, and scores each mechanism once, at fixed settings.

## 1. Mechanism signature (the unit of search)
Every strategy, tested or live or declined, gets one signature with six fields:
- market family (15 min crypto, 15 min non-crypto, hourly ladder, stock perp, index perp, metal perp, crypto perp, combo, politics, sports, weather);
- signal field (price level, price change, spread, book depth or imbalance, open interest, volume, funding rate, settlement mark, trade-tape flow, a spot price elsewhere, an event calendar, a cross-market residual);
- clock (fixed time to close, time of day, a scheduled event, a print such as funding, a reopen, any minute);
- entry type (taker, maker at the touch);
- exit type (hold to settle, fixed time, take profit as a multiple, stop, the next print);
- side rule (favourite, cheap side, follow, fade).
The registry (`MECH_REGISTRY.json`) holds the signature of every strategy in the README, the declined list (7e) and the ledger. A declined row is stored as a pattern (for example lead-lag = signal "another market's move", clock "any minute"). Uniqueness is automatic: a new signature is NEW only if it differs from every registry entry in its signal field or clock, and matches no declined pattern. The Verification Analyst audits the tool, not each idea.

## 2. Generator
It crosses the data we hold (perps books, funding, candles, the perps trade tape, Coinbase spot, ladders, open interest, event calendars, politics and combo books) with the market families and clocks, keeps only NEW signatures with data behind them, and writes each with ONE canonical setting: the threshold is the SEARCH-half 10% tail, the hold is one fixed value per exit type, and there are no grids. At most 3 settings per signature, all counted.

## 3. Screen, then the multiple-testing count, then shadow
- Development window fixed by date in the registration; held-out data never opened by the screen.
- Screen 1, cheap: gross edge above the round-trip cost and an expected 3 or more trades a day. Most signatures die here.
- Screen 2: net PF at 1c (or 12 bp a side on perps) in both halves.
- BH at 5% over the number of SIGNATURES tried (carried into the ledger), then the held-out read once, then forward shadow automatically, then the usual CANDIDATE rule (100 forward trades, PF 1.3 at 1c, 1.0 at 2c, both halves) and the owner's popup.

## 4. Daily output
One table: the top mechanisms by income a week (signals a day x net edge x 5 contracts x 7), their stage, forward n, and the date each reaches 100 forward trades at its signal rate. This replaces lists of failures as the headline.

## 5. Who builds what
- Desk A: the signature schema, the registry from existing records, and the generator (Nov 18 to 19).
- Verification Analyst: audits the registry's signatures and declined patterns (Nov 19).
- Testing Desk: the blind second build of the screen (Nov 20).
- Auditor B: code audit and the 1e-9 compare (Nov 20).
- Main: allow lines, and adds screen survivors to the shadow runner (PR, owner's typed merge).
- First run: Nov 21, 2026. First daily table: Nov 22.

Honest expectation: most signal fields on these markets have been mined already. The value of MECH1 is that it stops versions from being counted as new, prices the search honestly, and spends test time only on mechanisms nobody here has tried.
