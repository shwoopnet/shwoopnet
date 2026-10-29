# STABILITY: L1 as live trades it, on public candles (newest first; aggregates only; `python -m scalper.stab week`)

## 2026-10-29 15:48 CT: 7 days 2026-10-22 to 2026-10-28 CT, previous 4 weeks 2026-09-24 to 2026-10-21 CT

| Market | Markets in the 7 days | 7 days: n, losses, loss rate, PF, net/contract | Previous 4 weeks: n, losses, loss rate, PF, net/contract | Long-run tstop1 (6 min, all history): n, losses, loss rate, PF, net/contract | This rule's history before the 7 days: n, losses, loss rate, PF, net/contract | p (7 day losses vs tstop1 / vs rule history) |
|---|---|---|---|---|---|---|
| gold | 447 | 118, 6, 5.1%, 1.25, +1.20c | 535, 28, 5.2%, 1.24, +1.17c | 1726, 91, 5.27%, 1.22, +1.07c | 1592, 85, 5.3%, 1.20, +1.01c | 0.6092 / 0.6067 |
| Bitcoin | 664 | 6, 0, 0.0%, no loss, +4.10c | 43, 0, 0.0%, no loss, +4.47c | 2417, 158, 6.54%, 0.97, -0.17c | 154, 1, 0.6%, 8.12, +4.16c | 1.0000 / 1.0000 |
| Dogecoin | 664 | 192, 10, 5.2%, 1.24, +1.13c | 760, 43, 5.7%, 1.12, +0.62c | 2531, 128, 5.06%, 1.23, +1.09c | 2258, 117, 5.2%, 1.20, +0.98c | 0.5128 / 0.5388 |
| Ethereum | 664 | 3, 1, 33.3%, 0.06, -29.67c | 18, 0, 0.0%, no loss, +3.82c | 2469, 160, 6.48%, 0.96, -0.23c | 50, 0, 0.0%, no loss, +4.36c | 0.1759 / 1.0000 |

**Flags:** none (no 7 day loss rate above its long-run rate at p < 0.01; no 4 week PF under 0.8 on 100 or more entries)

L1 as live trades it on 2026-10-29: gold, Bitcoin, Dogecoin, Ethereum at the 6 minute look, band 88c to 97c, held to settlement; Bitcoin and Ethereum on the smooth climb only (pathShape, at least 4 earlier candles, worst minute >= -0.005, climb >= 0.10); one order per window among Bitcoin, Dogecoin, Ethereum in that order; XRP and the probes paused. 1 contract, rounded fee, every order assumed filled; decision candle ends 360 s before the close; window cap, loss stop and 25c exit not modelled. The tstop1 column has no smooth gate and no window rule (so for Bitcoin and Ethereum it is a different, ungated rule); its loss rate before the 7 day window is the flag baseline, and so is the rule's own history (from 2026-08-05). Public candles (fresh_update ran). Information only; nothing here changes a live rule.

