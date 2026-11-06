# EVM1 result (run once 2026-11-06, development only): FALSIFIED (no perp lead of 0.05 or more)

Registration `EVM1_REGISTRATION.md`; code `EVM_score.py`, output `EVM_output.txt`. Development = 656 hourly closes, 28 dates, 2026-08-24 to 2026-09-20 (held out third from 2026-09-21 never read). Scale check: median implied level / (10000 x perp mid) = 0.9998 over 627 closes (inside 0.99 to 1.01, no amendment). 32,476 usable minute pairs.

| | dates | L_pi (perp leads) | L_ip (ladder leads) | diff | z (date clustered) |
|---|---|---|---|---|---|
| all | 28 | +0.0064 | -0.0154 | +0.0218 | 8.03 |
| D1 | 14 | +0.0100 | -0.0123 | +0.0223 | 5.07 |
| D2 | 14 | +0.0027 | -0.0186 | +0.0214 | 6.35 |

The difference is steady in sign and in both halves but is 0.02 against a registered bar of 0.05 (prediction was 0.05 to 0.15, missed on size, sign held). Both correlations are near zero: at one minute resolution the ladder's 50 percent strike and the perp move together within the same minute, so neither leads at a minute lag. Day cluster z is high only because the effect is tiny and steady; it is not a trading lead. No cost charged. N +1. Verdict by the registered rule: FALSIFIED. Read 2026-11-06 US Central 10:00 to 11:00.
