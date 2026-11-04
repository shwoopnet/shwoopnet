# STRESSDAY1 registration: cheap-side entries on market-stress days vs calm days (2026-11-03)

Registered before any outcome was joined. Discovery only: no live code, no `functions/`, no L1, no OICORE, no promote verb.
**Owner rule (strict): cheap side only, ask 3c to 30c.** No favourite-side result is computed or printed; the code asserts it. No 15 minute crypto or gold candle trigger.

## Duplicate check
README and workers searched for stress, VIX, regime (VOLGAP1, VOLSLOT1, EVENT1, EVENT830, STRADDLE1, CALIB1, TODSEAS1, USWEEP1/2/3, SPIKE1, OICORE_SHAPE_INVENTORY). VIX appears only as a volatility INPUT to a fair-value model (INX1, IDXFUT1, VRP2, VT1, PUB20) or in index research. No VIX-regime split of cheap-side Kalshi entries was run. Not a duplicate. EVENT1 tested release timing, not a day-level regime.

## Design
- Entries: the CALIB1 pooled cheap-side table (16,041 rows, cached, no new Kalshi fetch), categories **Financials, Commodities, Crypto** (market categories). Economics (mostly AAA state gas price ladders) is NOT a stress-sensitive market and is excluded from the claim.
- Only T-look entries (entry time = close minus the look); A-looks and "late" have no stored entry time and are dropped. Entries with close or entry time at or after 2026-10-03T16:00Z (1791043200) are dropped (frozen, never joined).
- Regime day = UTC date of entry. Stress day = prior-session VIX close-to-close change (last two sessions strictly before that date; Yahoo chart daily, ^VIX) at or above the 67th percentile of that change over the first two thirds of development days (cut computed in code, `cut_point`), OR the date has a FOMC, CPI or JOBS row in `EVENT1_CALENDAR.csv`. SPY and BTC-USD daily data were fetched but are not in the rule.
- Trade: all cheap entries on stress days, held to settlement; control: calm days. Fee 7% x C x p x (1-p) rounded up, C = 10. Day-clustered (ISO date); halves D1/D2 = first and second half of development days.
- Numeric prediction: stress-day win rate below price by 2c to 6c, net -2c to -7c, PF 0.3 to 0.8, same sign as calm days.
- Kill: FALSIFIED if stress-day mean net after fees is not above 0 in both halves, or PF under 1.5; NOT_ENOUGH_DATA if under 150 treated stress-day entries or under 25 stress days. N +2 (rule and control; census only).

## Census gate (run first, counts only, outcomes never read)
`python3 -I -m scalper.stressday1 census` keeps only cat, series, look, t, event, ask. If stress days < 25 or stress entries < 150, the outcome join is not run.
Code `src/scalper/stressday1.py`, tests `tests/test_stressday1.py` (synthetic).
