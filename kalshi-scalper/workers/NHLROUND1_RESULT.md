# NHLROUND1 result (2026-11-04): NOT_ENOUGH_DATA (92 treated trades of 150), scored once

Registered rule (commit ffa6086, E 3.9085, margin m 0.3): buy the cheap YES rungs (ask 3-30c) of a game only when its sum of 1+ YES asks is at most 3.6085. Read once, read-only, on the NHLALL1 cache after its Amendment 2 (75 games with a valid ladder; the 25 NHLG1 events and the 225 frozen post-cut events excluded).

- Treated: 46 of 75 games, n 92 trades, win 28.3% at a mean price of 18.9c, net +8.24c per contract, PF 1.58; game-clustered SE 4.75c, z 1.73, lower 95% bound -1.07c; date-clustered (32 dates) z 1.76, lower bound -0.93c; fees x1.2: +8.02c.
- Halves: H1 n 46 +14.52c PF 2.27 (z 2.06, lower bound +0.67c); H2 n 46 +1.96c PF 1.12 (z 0.32, lower bound -9.95c).
- Untreated games (information only): n 58 in 29 games, +5.67c, PF 1.39.
- Verdict by the registered bar: NOT_ENOUGH_DATA (92 of 150; H2 not distinguishable from zero; lower bound below 0). Not a lead: the filter does not separate treated from untreated (+8.2c vs +5.7c, the same sample as NHLALL1, which it reads read-only, so it is NOT independent evidence); it only shows the filtered subset is not worse. N +2 (charged at registration).
- Forward: nothing separate; its definition (E 3.9085, m 0.3) is frozen and can be applied once to any new NHL goal-scorer games alongside the NHLALL1 forward read.
