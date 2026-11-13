# W-WXPRIOR1 registration (Nov 11 2026, written BEFORE any wxens quote was joined to a result or scored)

Mechanism 1 of FIVE_MECHANISMS_NOV11: forecast prior vs Kalshi daily-high brackets, hold to settlement. Shadow candidate only, no trading code, no repo file touched. Rain (KXRAIN) is NOT scored here: raincal holds only quotes at the 6 to 8 AM look and NWS PoP, no ensemble, and is a separate registration if this one has signal.

## Which test and why
PRIMARY (A): wxens forward data (V2 recorder, since 2026-11-04). The probability is the Open-Meteo ensemble (GEFS, ECMWF IFS, ICON members, all three models pooled) at a look BEFORE the quote is read, and the ask is the Kalshi quote recorded at the SAME slot_ts. No timing gap, no lookahead: both are stamped at the same poll. This is the only dataset where forecast time and entry price time coincide in the morning. SECONDARY (B): my row 49 history (W-ROW49 REGISTRATION, Amendment 1, score.py as written) for the 4 cities. It pairs a morning NBS forecast with an EVENING ask (close minus 5h, about 19:00 local, after the day's high is mostly printed), because the candles pulled cover only that hour. The market there already knows the high, so B is a weak test of "stale forecast vs informed price". It is run as a labelled sanity read, not as the pass test. A 10:00 local history variant would need a re-pull (not started: pull.py is not mine to start). Choice reason: A can reach an honest PF read sooner on the right question; B has more n now but tests the wrong timing.

## Rule A (fixed now, nothing tuned after)
- Unit: one city-day = (city, target_date) with a recorded quote slot that has ensemble members at the same slot_ts, city, target_date, and a settled result.
- One look per city-day: the EARLIEST slot_ts that has quotes for the city and target date (so a day-before look is used when it exists). Later looks are ignored (no re-entry).
- Universe: the 14 cities in WXENS1_WATCHLIST (daily-high series only; low-temperature series not used). Not narrowed to the 8 later.
- Model probability of a bracket: mean over all ensemble members (all models) of a normal centred on the member's tmax_f with sd 2.0F (fixed, not fitted; the ensembles are known to be under-dispersed), integrating the settled whole-degree integer value: between [f,c] -> Phi((c+.5-x)/sd)-Phi((f-.5-x)/sd); greater K -> 1-Phi((K+.5-x)/sd); less K -> Phi((K-.5-x)/sd).
- Both sides allowed. YES: edge = p - yes_ask, price = yes_ask. NO: edge = (1-p) - (1-yes_bid), price = 1 - yes_bid. Take an order if edge >= 0.08 and price in (0.10, 0.95]. A missing, zero or one-sided quote (yes_bid 0 for a NO buy) is skipped.
- At most 2 orders per city-day, largest edge first; at most one per bracket; hold to the market result.
- Cash basis at the ask, +0c and +1c slip on the price, unrounded fee 0.07*price*(1-price), 1 contract.
- N tried: this is 1 rule, 1 sd, 1 threshold, 1 look rule (no grid). Added to the family count: 5 variants counted for the family this session (W-ROW49 5 cities, this one).

## Pass bar (shadow candidate)
PF >= 1.3 at +0c AND +1c, n >= 80 city-days, first and second chronological half both PF > 1.0. Fewer than 80 city-days = DATA_LIMITED (no verdict on the edge). PF < 1.0 with n >= 30 city-days = FAIL for this rule. Also report: win rate vs mean price, p-hat calibration (mean model p vs result) to see if a threshold or sd is the problem, as a description only, no retuning.

## Counterparty
Not established. Candidate: casual bettors on thin books pricing round numbers; the ensemble could also be no better than the market's own forecast source. Not claimed.


Dated clarification Nov 13, 2026 (Head of R&D ruling): rule words restored from commit 44dda69f^ (the version before the privacy scrub); nothing re-decided. line 19 restored verbatim; lines 12 and 15 still carry a marker, to be done by hand.


Dated clarification Nov 13, 2026, second pass (Head of R&D ruling): from commit 44dda69f^ (the version before the privacy scrub); nothing re-decided; lines 12 and 15 restored verbatim (model probability and cash basis).

Dated clarification 2 Nov 13, 2026 (Auditor B finding): one rule sentence was missing from the restore and is put back verbatim from commit 44dda69f^: Replacement of gold needs daily P/L correlation under 0.3 with gold L1 on overlapping days.
