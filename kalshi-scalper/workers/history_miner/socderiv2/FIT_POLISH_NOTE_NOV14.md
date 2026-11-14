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
