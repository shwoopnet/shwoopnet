# OIVER builds 2 and the OIVER shadow replay: stopped 2026-11-13 21:37Z (owner order, rnd-queue 9dcfeee1, relayed by the Head of R&D)

Only completely unique strategies that clear cash PF 1.3, with both halves at 1.0 or better on development data, count. Versions do not. So the OIVER and OICORE shadow replay work stops. No real file was read by any of it.

Last frozen state, kept as the record:
- **oiver_shadow2.py fc913fa2:** frozen, unrun, never audited (built on sheet v1 cb45e79b, superseded).
- **oiver_spread2.py 9c6522c5, oiver_cap30_2.py ade7e090, oiver_depth2.py 54463576 (128d4c0a):** void drop at load. Auditor B: the figures agree with Desk A's build 1 on 800 invented windows. Not run on real rows.
- **oiver_rows.py a7aa5fc8:** CLEAN.
- **oiver_r6sizes.py b8535332:** CLEAN.
- **liqrev_cov.py 084f6462:** accepted by the Head. LIQREV is Desk C's card, not an OIVER version, so it is not stopped by this order.
