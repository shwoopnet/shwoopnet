# SPXSCALP counts-only diagnostic: expected figures, written BEFORE the code (Nov 15, 2026)

The Head ordered (Nov 15, 14:50Z): print, over the same inputs and window as build 1, (a) looks with an ES move at or over the threshold, (b) of those, looks with a candidate side whose ask is in each arm's band, (c) the distribution of that side's ask in 5c bands. Counts only, no ES value, no file written, scorer `spxscalp.py` unchanged (the diagnostic is a new file that imports its functions). Explains n = 0 as the rule or a shared bug.

Fixture: `build1/make_spxscalp_fixture2.py` (MADE-UP, windows A to E, closes 2026-11-06). Threshold 0.0005 x 7000 = 3.5 ES points. Looks are the five candles ending at window open + 60 m, m = 1 to 5, counted over ALL looks (the scorer stops at the first entry per window; the diagnostic does not). Candidate side: YES if the ES move is at least +threshold, NO if at most -threshold; its ask = YES ask for YES, 1 - YES bid for NO.

Hand derivation (look: ES move, side, candle, ask):
- A: m1 move +2 none; m2 +5 YES, candle (.20,.22), ask .22. ES missing m3 to m5.
- B: m1 -10 NO, candle (.80,.82), ask 1 - .80 = .20 (float .19999999999999996, inside the band by the 1e-9 tolerance).
- C: m1 0 none; m2 +5 YES, (.26,.28), ask .28; m3 +5 YES, (.22,.24), ask .24.
- D: m1 +6 YES, (.21,.23), ask .23.
- E: m1 ES bar missing; m2 +6 YES, (.20,.22), ask .22.

Expected printed counts:
- windows with candles 5; windows with a start bar 5; looks 25; looks with an ES bar 8; looks with move at or over threshold 6 (YES 5, NO 1); of those two-sided 6, not two-sided 0.
- ask distribution of those 6 by 5c band: [0.20,0.25) 5, [0.25,0.30) 1, every other band 0.
- looks with the candidate ask in B25 [0.20,0.25]: 5; in B30 [0.20,0.30]: 6.
- windows with at least one in-band look: B25 5, B30 5.
- cross-check against the scorer's own entry scan (run_band): entries_found B25 5, B30 5 (must equal the line above).
