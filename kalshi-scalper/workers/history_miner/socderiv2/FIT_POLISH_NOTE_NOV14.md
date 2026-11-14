# SOCDERIV second build: fit polish (2026-11-14 ~03:00Z, Auditor B's request of 02:51Z; written before the code; no real run until the Head rules on the reference fit)

**Why.** The registration says only "fit by least squares" and gives no tolerance. socderiv2_model.fit (b43ce14f) is a 0.05 grid, then coordinate refinement down to step 1e-7, accepting a move only when SSE falls by more than 1e-18. In a narrow diagonal valley a coordinate search can stop short of the minimum. Auditor B saw my fit residual median above the Testing Desk's on the same objective.

**The reference fit I propose for the Head:**
- the stationary point of the registration's SSE inside [0.01, 6] x [0.01, 6], reached from the grid's best point;
- the rates converged to about 1e-10, so the reported figures are stable well inside the 1e-9 bars.

A search that only compares SSE values cannot do this: near the minimum SSE changes by about (rate error)^2, so differences below about 1e-8 in the rates are lost in rounding. So the polish steps on the gradient.

**The polish, after the existing refinement (grid and refinement unchanged):**
- Gauss-Newton on the residual vector: home, draw and away minus their mids, then each total-over strike minus its mid, in the same order as sse().
- Jacobian by central differences, h = 1e-6.
- Step solves the 2 x 2 normal equations (J'J) d = -J'r.
- The step is halved, at most 40 times, while it leaves the box or raises SSE by more than 1e-15 x (1 + SSE).
- Stops when |d| is under 1e-13 on both rates, after 100 iterations, or when J'J is near singular (determinant under 1e-14 x trace^2). In the last case the refinement point is kept and a flag is counted.
- The polished point is used only if its SSE is not above the refinement's SSE + 1e-15 (it can only hold or lower the fit).
- Deterministic, pure Python.

**Expected by hand:**
- **P1 (exact data):** mids generated from rates (1.37, 0.83), with totals at 1.5, 2.5 and 3.5. The fit returns both rates within 1e-9 of the truth and SSE under 1e-20.
- **P2 (noisy data):** the same mids with +0.012, -0.007, -0.005 on the winners and +0.009, -0.011, +0.004 on the totals. At the returned point the central-difference gradient of SSE (h 1e-6) is under 1e-10 on each rate. Its SSE is at or below the refinement-only SSE.
- **P3 (grid-off valley):** mids from rates (2.9137, 0.4071). The rates are recovered within 1e-9.
- **P4:** for every fit in the 23 made-up cases, the polished SSE is at or below the refinement SSE.
- **Effect on the 23 committed case outputs:** fit-derived figures (gaps, model values, residuals) may move by about 1e-7 or less, and counts should not change. I will re-run the 23 cases and report each changed field and its size before any output file is replaced. Expected outputs are not edited silently.

## Objective as built, and a false comment disclosed (2026-11-14 ~03:05Z, Auditor B's 02:58Z request; before any change to the objective)
- **Box:** rates in [0.01, 6] each. The grid starts at 0.05.
- **Truncation:** MAXG = 20 goals a side, in the winner probabilities. Away is computed as 1 - home - draw, so the tail lands in away. The total-goals and team-total strikes take P(X <= k) as an exact partial sum for k <= 20.
- **Disclosed:** the model's comment says the tail beyond 20 is "below 1e-12 for rates under 6". That is FALSE. Computed P(X > 20):
  - rate 3: 1.2e-11;
  - rate 4: 1.9e-9;
  - rate 6: 1.5e-6.
  - With 40 goals the tail is under 1e-15 up to rate 6 (3.3e-16 at rate 4, 0 at rate 6 in double precision).
  - So a fit with a rate above about 3.5 carries a winner-probability error above 1e-9 in the current build.
- **Proposed, pending the Head's ruling on the objective for both builds:**
  - MAXG = 40, so the tail is under 1e-15 in the box;
  - the box stays [0.01, 6] unless the Head rules otherwise.
  - The code is not changed until that ruling.

## Amendment for the Head's 02:59Z rulings (2026-11-14 ~06:40Z, written from the Head's verbatim text received 06:24Z, before the code; the Testing Desk's code and addendum not read)
The rulings, verbatim:
1. Rate box [0.01, 6.0] for both rates.
2. Poisson sums to 40 goals everywhere.
3. Polish until the step is under 1e-13 (or SSE improves by under 1e-13 relative), at most 200 iterations; print the iteration count and whether the cap was hit.
4. The one re-run also writes a per-game file: CSV named socderiv_pergame.csv, one row per game per derivative leg, floats written unrounded (Python repr). Columns: game_key (the event ticker), fit_iters, cap_hit (true/false), rate_home, rate_away, sse, leg_ticker, leg_type (btts or team_total), strike (blank for btts), model_value (probability 0 to 1), market_mid (dollars 0 to 1), gap (model_value minus market_mid), fires (true/false). Rows sorted by game_key then leg_ticker. No result field. Development windows only.
Plus Auditor B (03:24Z): the comparison figures in the main print are unrounded (repr); the verdict text keeps 6 dp; the polish check (SSE never above the refinement's) stays.

**How each is built:**
- **Box:** unchanged, [0.01, 6] (it was already this).
- **40 goals:** MAXG = 40, so P(0..40) per rate. Away = 1 - home - draw (the tail beyond 40 lands in away, under 1e-15 in the box). P(X <= k) is an exact partial sum for k <= 40, and 1.0 above.
- **Polish:**
  - Each pass computes one Gauss-Newton step and counts as one iteration.
  - It stops BEFORE moving if both step components are under 1e-13.
  - It stops AFTER an accepted move if SSE fell by less than 1e-13 x the SSE before the move.
  - cap_hit is true only when 200 passes ran with neither stop.
  - Halving, the box guard and the "not above the refinement's SSE" check are as before. A near-singular J'J keeps the refinement point (cap_hit false, the passes so far counted).
  - fit() now returns (home, away, sse, iters, cap_hit).
- **Main print:** every figure that was round(x, 6) is now the unrounded float: median, q1, q3, p90, share, filled_share, median_spread, one_way_cost_median, round_trip_median_info_only, fit_residual_median. The verdict text writes the p90 at 6 dp. Each cell adds fit_iters_max and fit_cap_hits, over every fit in the cell, placebo refits included.
- **Per-game file:** written beside the main print, as socderiv_pergame.csv. Readings I took, flagged:
  - game_key is the WINNER event ticker (KX<LG>GAME-<KEY>). The legs sit in different events; the winner event names the game.
  - One row for EVERY target leg of every kickoff-derivable sampled game (BTTS and team-total). A leg that never reached a two-sided instant, or whose team or strike is unreadable, has fit_iters, cap_hit, rate_home, rate_away, sse, model_value, market_mid and gap blank, and fires false.
  - For a filled leg the row is that leg's own instant (its own fit).
  - gap = model_value - market_mid, as ruled. fires is the registration's line: the CHEAPER side's gap is 8c or more AND the spread is 4c or less (the count_gap8_spread4 test). The two gaps differ by design; the cheaper-side gap is not written.
  - strike is floor_strike for a team total, blank for BTTS. Booleans are written true or false. Floats use repr.
  - Placebo refits have no row.

**Expected by hand:**
- **P1 to P3** still pass (exact, noisy, off-grid). Each returns cap_hit false and fewer than 200 iterations.
- **P5:** with the cap forced to 1, the noisy P2 returns iters 1 and cap_hit true, and its SSE is not above the refinement's.
- **P6:** at rates (4.0, 0.5), home + draw + away = 1 within 1e-15. Home matches an independent math.fsum over 0..80 goals within 1e-15.
- **P7:** P(total <= 2) at rate 2.2 is unchanged from MAXG 20 (an exact partial sum).
- **Per-game file, on made-up cases 15, 16, 22 and 23:**
  - rows = the sum over cells of targets;
  - non-blank model_value rows = the sum of targets_filled;
  - fires-true rows = the sum of count_gap8_spread4;
  - sorted by (game_key, leg_ticker);
  - no column named result;
  - every float column round-trips through float(repr(x)).
- **Unrounded print:** p90 equals q_lin(gaps, 0.9) exactly; the verdict quotes round(p90, 6).
- **The 23 made-up cases:** re-run with the polish check (no polished SSE above the refinement's). Every changed field is listed before any committed output is replaced.
- **The Head's settlement of the per-game readings (06:32Z, verbatim intent), before the code change:**
  1. rate_home is team1, the team with the LOWER code (alphabetical); rate_away is the other. Already so: the winner mids are taken in the order (lower code, TIE, higher code), so the fit's first rate is the lower code's.
  2. strike is empty for btts rows. Already so.
  3. fires and cap_hit are written **True** or **False** (Python bool repr), replacing "true or false" above. A blank row's cap_hit stays empty.
  4. No league column and no placebo rows. Sorted by game_key, then leg_ticker, with no other tie-break. Already so.
  - Not covered by the settlement, kept as above and flagged again: game_key is the WINNER event ticker, and every target leg has a row (blank fit fields when unfilled or unreadable).
  - **Confirmed by the Head (06:33Z):** (a) game_key is the WINNER event ticker for every row of that game; (b) every target leg of every kickoff-derivable sampled game has a row, blank fit fields and fires False when unfilled or unreadable. Both were already built this way.

## Result on the 23 made-up cases (2026-11-14 ~07:05Z, code as frozen below; outputs replaced only after this list)
- **Polish check (P4):** 16,780 fits over all 23 cases, placebo refits included. Polished SSE above the refinement's: 0. Singular: 0. Rejected: 0. fit_iters_max is 2 in every cell (1 in cases 21 and 23); cap hits 0.
- **Changed fields** (old committed output against new), every numeric change under 5.2e-7. This is the removal of the 6 dp rounding (up to 5e-7) plus the fit's last-digit moves:
  - gap and placebo median, q1, q3, p90: 44 cell values each, max 5.11e-7;
  - fit_residual_median: 44, max 3.36e-7;
  - round_trip_median_info_only: 44, max 5e-7;
  - filled_share: 8, max 3.33e-7;
  - median_spread and one_way_cost_median: 44 each, max 7e-17 (float noise only).
- New fields fit_iters_max and fit_cap_hits in every cell.
- **verdict text:** 9 cells (A_big TEAMTOTAL-type cell 1 in cases 1, 3, 4, 5, 9, 10, 15, 17, 18). Only the quoted p90 moved, -0.004794 to -0.004793, one step at the 6th decimal; the same words.
- **No count changed** (n, filled, targets, hits, flags). Case 20 is the refusal, unchanged.
- **Per-game file (all 22 cases with a print, 11,385 rows):** checked rows = sum of targets; filled rows = sum of targets_filled; fires rows = sum of count_gap8_spread4; sorted; columns exactly as ruled; no result column; floats round-trip; btts strike blank; game_key a winner event. All OK. These CSVs came from the harness before the True/False change. The frozen formatter is tested separately in test_fit_polish.py ("per-game format: ok").

## Final spec (the Head, 07:10Z, after Auditor B's differential), before the code
The Head, verbatim:
1. Box edge, for both builds: a rate that lands on a bound stays there, and the other rate is polished alone to the same stop (step or relative SSE under 1e-13, cap 200). Print the count of fits with a rate on a bound.
2. Keep gap = model_value minus market_mid, and ADD two columns after it: side (yes or no, the cheaper side the aggregate trades) and edge (that side's model value minus its ask, the figure the headline uses). fires must be consistent with edge.
3. leg_type is team_total; btts unchanged. (Already so.)

**How "lands on a bound" is built (the exact rule, flagged for Auditor B so both builds can be compared):**
- A rate equal to 0.01 or 6.0 when the polish starts is on a bound.
- In a 2-D pass, if the full Gauss-Newton step would put a rate outside [0.01, 6]:
  - that rate is set exactly to its bound; the other rate takes its full step, clipped to the box the same way;
  - if this clipped point's SSE is not above the current SSE + 1e-15 x (1 + SSE), it is accepted and the clipped rate(s) are on a bound;
  - otherwise the whole step is halved as before, without clipping.
- Once a rate is on a bound it is held there for the rest of the polish. The other rate is polished ALONE by 1-D Gauss-Newton on the same residuals, d = -(J'r) / (J'J) on that rate, with:
  - the same halving and box guard;
  - the same stops (|d| under 1e-13 before a move; SSE falling by less than 1e-13 relative after a move);
  - the cap of 200 passes shared with the 2-D passes.
- If both rates are on bounds, the polish stops.
- The "not above the refinement's SSE + 1e-15" check applies as before.
- fit() returns (home, away, sse, iters, cap_hit, on_bound), where on_bound is True if either rate ends on a bound.
- Each cell prints fit_on_bound, the count of fits (placebo refits included) with a rate on a bound.

**Per-game columns:** game_key, fit_iters, cap_hit, rate_home, rate_away, sse, leg_ticker, leg_type, strike, model_value, market_mid, gap, side, edge, fires.
- side = "yes" or "no", the cheaper side (the NO ask is 1 - YES bid; "no" only when strictly cheaper by more than 1e-9, ties to yes, as the aggregate).
- edge = that side's model value minus its ask (the aggregate's gap).
- fires = edge >= 0.08 - 1e-9 AND spread <= 0.04 + 1e-9.
- On a blank row, side and edge are empty and fires is False.

**Expected by hand (test_fit_polish.py):**
- **B1:** mids exactly from rates (0.01, 1.2) with totals 1.5, 2.5, 3.5. The fit returns home exactly 0.01 and away within 1e-9 of 1.2, on_bound True, SSE under 1e-20.
- **B2:** mids from (0.003, 1.5), where the minimum lies outside the box. Home is exactly 0.01, on_bound True. The SSE gradient on away is under 1e-10 at the result.
- **B3:** mids from (6.4, 0.8). Home is exactly 6.0, on_bound True. The away gradient is under 1e-10.
- **B4:** P1 to P3 are unchanged (interior, on_bound False, same rates within 1e-12).
- **Columns:** the format test has side and edge after gap. On a filled row fires == (edge >= 0.08 - 1e-9 and spread <= 0.04 + 1e-9). On the 23 cases, rows with fires True = the sum of count_gap8_spread4, as before.
- **One detail added while coding (before any test was run), flagged:** the stop "SSE fell by less than 1e-13 relative after a move" does not apply on the pass in which a rate newly lands on a bound. Otherwise a landing step that barely changes SSE would end the polish before the other rate was polished alone, which the Head's rule asks for.
- **Correction after the first test run (disclosed):** B2 FAILED with the clipping rule above. With mids from (0.003, 1.5), the clipped point moved the away rate by its full 2-D step, which was computed as if home went to 0.003. SSE rose, so the step was halved, and home crept to 0.0100000000000022 without ever landing (away gradient 2.9e-8).
  - **Rule now:** if the full step would put a rate outside the box, ONLY that rate moves, exactly to its bound, and the other rate stays where it is for that pass. This is accepted if SSE is not above the current SSE + 1e-15 x (1 + SSE); then the rate is held and the other is polished alone. Otherwise the whole step is halved as before.
  - Expected results B1 to B4 are unchanged.
- **Second correction after a test run (disclosed):** B3 FAILED.
  - Home landed on 6.0 and the 1-D Gauss-Newton stopped after 1 pass with the away gradient at 1.9e-10. Its step was still about 1.4e-8, but SSE fell by about 3e-18, under the 1e-13-relative stop.
  - Cause: at a bound the residuals are large against J'J (0.0069 here), so Gauss-Newton converges only linearly, and the relative-SSE stop ends it early. With the step-only stop instead, it reaches gradient 4e-13 but uses all 200 passes (cap hit).
  - **Rule now:** the 1-D polish of the free rate is a Newton step. The curvature is J'J PLUS the sum of r_i x r_i'' (r_i'' by central second difference, K = 1e-4), and the step is d = -(J'r) / that curvature. The rest is unchanged: halving, box guard, the Head's stops, the shared cap of 200.
  - The 2-D phase is unchanged (Gauss-Newton; interior fits converge in 2 passes).
  - If the curvature is not positive, the polish stops at the current point (counted as stopped, not capped).
  - Checked before the test, in scratch, on 7 noisy inputs near and beyond both bounds: the free rate's gradient is at most 6e-12, in 1 to 3 passes, with no cap hit. The held rate's gradient points out of the box in every case.
  - Expected results B1 to B4 are unchanged.

## Result on the 23 made-up cases, final spec (2026-11-14 ~07:50Z)
- 16,780 fits. Polished SSE above the refinement's: 0. Singular: 0. Rejected: 0. Cap hits 0. fit_iters_max 2.
- **fit_on_bound is 0 in all 44 cells:** no made-up fit reaches a bound, so the bound rule is exercised only by the hand cases B1 to B3.
- **Against b3920acf's outputs:** the ONLY change is the new field fit_on_bound (0 everywhere). Every other figure is byte-identical.
- **Per-game files (22 cases, 11,385 rows), all checks pass:**
  - columns in the ruled order, side and edge after gap;
  - rows = targets; filled = targets_filled; fires True = count_gap8_spread4;
  - side yes or no and edge present on every filled row; side, edge empty and fires False on every blank row;
  - fires True only where edge >= 0.08 - 1e-9;
  - leg_type btts or team_total; sorted.
