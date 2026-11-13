# W-DERIBIT1 registration (Nov 11, 2026, written before any result was scored by this worker)

Mechanism 2 of FIVE_MECHANISMS_NOV11. Data is V2's recorder (quote-data branch, deribit/), same data and same math family as V2's DERIBIT_IMPLIED_REGISTRATION.md, so this is a SHADOW re-score, not a new data source. Nothing here changes trading code.

Disclosure: before this file I looked only at column names, row counts and the first rows of each file. No implied probability was computed, no price was compared to one, no outcome was joined.

Ledger check: not LAD1/NEWH14 (realised vol), not IV1 (DVOL single number), not W-ROW59 (flat VIX sigma on S&P; here a per strike smile). Not a repeat of V2's tries except as the same two tries (A, B) scored independently by a second implementation; N tried counted as 2 here (running ledger plus 2).

## Fixed rule
- Hours: every hourly KXBTCD close with a look row 44:30 to 45:29 before the close AND a settled result for the strike. Look = that poll.
- Universe: strikes within 3% of Deribit index S0 at the look, two-sided Kalshi quote (yes_bid>0, yes_ask<1), yes_ask - yes_bid <= 0.04.
- Fair probability: take the nearest Deribit expiry E1 at or after the close (rank 1 in the file). OTM instrument per strike (put below forward, call at/above), mark_iv>0. sigma(K) linear in strike between adjacent strikes, no extrapolation. Flat in time from E1 to the close (an assumption, no bracketing expiry exists except at 08:00 UTC). Forward F_T = S0*(F_E1/S0)^(tau_T/tau_E1), r=0.
  Try A: P = N(d2), w = sigma^2 tau_T. Try B: P = N(d2) - vega*dsigma/dK (smile slope correction), clipped to [0.001,0.999].
- Edge: edge_YES = P - yes_ask, edge_NO = (1-P) - no_ask. Threshold 6c. Trade the larger side if >= 6c, one trade per hour (best strike), buy at the ask at the look, hold to settlement. Cash basis: pay ask, unrounded fee 0.07*p*(1-p) per contract, sensitivities +0c and +1c extra slippage. Win pays 1.
- Profit factor = gross cash won / gross cash lost per contract, unit contract.
- Brier check: Kalshi mid vs P on all universe strikes at the look.

## Bar (fixed now)
- PASS (shadow candidate only): PF >= 1.3 at +1c on n >= 80 independent hours (one trade per hour), and the first half and second half of hours both PF > 1.0, and Brier(P) < Brier(mid).
- Otherwise FAIL if n >= 80 and bar missed; DATA_LIMITED if n < 80 (a number under 80 is not a verdict).
- Prediction (prior, stated now): PF 1.00 (0.85 to 1.15); survivor probability 5%.
- Pace: at 24 hourly closes a day the count of usable hours is limited by the recorder's actual coverage, measured in step 2 and extrapolated to n = 80.
- Gold correlation: daily shadow cash P/L vs gold L1 daily cash P/L (L1 gold history as available), reported only if >= 10 overlap days; gold-replacement needs |corr| < 0.3.


Dated clarification Nov 13, 2026 (Head of R&D ruling): rule words restored from commit 44dda69f^ (the version before the privacy scrub); nothing re-decided. lines 10 and 14 (look and edge rule) restored verbatim; line 23 still carries a marker, to be done by hand.


Dated clarification Nov 13, 2026, second pass (Head of R&D ruling): from commit 44dda69f^ (the version before the privacy scrub); nothing re-decided; line 23 restored verbatim (gold correlation rule).
