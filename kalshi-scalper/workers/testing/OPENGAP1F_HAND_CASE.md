# OPENGAP1-F hand case (new parts only), written BEFORE the code (Testing Desk, Nov 16, 2026)
The trade logic, the events and the literal price-unit haircut figures are those of OPENGAP1_HAND_CASE.md (frozen core 242f477f; the same E1 to E9). New here: (1) relative haircut r of 0.1% and 0.2%; (2) counting mode; (3) the interim kill; (4) the forward date window.
**Relative haircut** (fills: long entry ask x (1 + r), long exit bid x (1 - r); short entry bid x (1 - r), short exit ask x (1 + r); return = sign x (exit - entry) / entry):
| | r 0.001 | r 0.002 |
|---|---|---|
| E1 long 10.08 to 10.07 | entry 10.09008, exit 10.05993: -0.03015 / 10.09008 = -0.0029881 | entry 10.10016, exit 10.04986: -0.0503 / 10.10016 = -0.0049802 |
| E2 short 4.99 to 4.99 | entry 4.98501, exit 4.99499: -(0.00998) / 4.98501 = -0.0020020 | entry 4.98002, exit 4.99998: -0.01996 / 4.98002 = -0.0040080 |
| E3 long 20.03 to 20.14 | entry 20.05003, exit 20.11986: 0.06983 / 20.05003 = 0.0034828 | entry 20.07006, exit 20.09972: 0.02966 / 20.07006 = 0.0014778 |
Net at the fee 0.0012 a side (return - 0.0024): r 0.001: -0.0053881, -0.0044020, +0.0010828, PF 0.0010828 / 0.0097901 = 0.1106; r 0.002: -0.0073802, -0.0064080, -0.0009222, no win, PF 0. At the placeholder fee 0.0005 a side (return - 0.0010): r 0.001: -0.0039881, -0.0030020, +0.0024828, PF 0.0024828 / 0.0069901 = 0.3552.
**Counting mode:** over E1 to E9 the triggered events are E1, E2, E3 (traded) and E8 (triggered, no exit): count 4 (pooled and for the one name); a no_trigger, no_perp or no_underlying event is not counted; the count prints integers only.
**Interim kill:** after at least 50 triggered events, the pooled net PF at r 0.001 and the chosen fee (12 bps) under 1.0 prints KILL; at 49 events it refuses to print a PF; at 50 with PF exactly 1.0 or above it prints CONTINUE.
**Date window:** event dates from 2026-11-17 to 2027-01-31 inclusive; 2026-11-16 and earlier and 2027-02-01 and later are dropped; the build refuses any event date on or after 2027-03-14 (DST).
**Final read:** refused unless the pooled triggered count is at least 100, or the last event date is on or after 2027-01-31 (the stop date).

## Addendum 2 (Nov 16, 2026, the Head's relative sizes 0.02% and 0.05% as primary; 0.1% and 0.2% as stress lines): hand figures for the new lines, before the code change
Same E1, E2, E3 and fills as above, relative haircut r:
| | r 0.0002 | r 0.0005 |
|---|---|---|
| E1 long 10.08 to 10.07 | entry 10.082016, exit 10.067986: -0.01403 / 10.082016 = -0.0013916 | entry 10.08504, exit 10.064965: -0.020075 / 10.08504 = -0.0019906 |
| E2 short 4.99 to 4.99 | entry 4.989002, exit 4.990998: -0.001996 / 4.989002 = -0.0004001 | entry 4.987505, exit 4.992495: -0.00499 / 4.987505 = -0.0010005 |
| E3 long 20.03 to 20.14 | entry 20.034006, exit 20.135972: 0.101966 / 20.034006 = 0.0050897 | entry 20.040015, exit 20.12993: 0.089915 / 20.040015 = 0.0044868 |
Net at the fee 0.0012 a side (return - 0.0024): r 0.0002: -0.0037916, -0.0028001, +0.0026897, PF 0.0026897 / 0.0065917 = 0.4080; r 0.0005: -0.0043906, -0.0034005, +0.0020868, PF 0.0020868 / 0.0077911 = 0.2678. At the placeholder fee 0.0005 (return - 0.0010): r 0.0002: -0.0023916, -0.0014001, +0.0040897, PF 0.0040897 / 0.0037917 = 1.0786; r 0.0005: -0.0029906, -0.0020005, +0.0034868, PF 0.0034868 / 0.0049911 = 0.6986. The 0.1% and 0.2% figures above are the stress lines. The interim kill reads the 0.02% line (r 0.0002).
