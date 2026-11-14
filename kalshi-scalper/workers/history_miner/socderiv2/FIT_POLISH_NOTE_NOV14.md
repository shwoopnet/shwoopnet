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
