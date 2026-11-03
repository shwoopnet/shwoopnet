# SKEW1 result (run once on 2026-11-03, DEV only; registration `workers/SKEW1_REGISTRATION.md`, commit 0c7be8c, pushed before any result was read)

Code `src/scalper/skew1.py`, tests `tests/test_skew1.py`, raw printout `/tmp` only (aggregates below). Data: `conf2_lad.sqlite` then `lad2.sqlite`, 1,476 settled hourly KXBTCD closes
2026-08-24 to 2026-10-26 (spot proxy = the ladder's own 0.5 YES-mid crossing). **Frozen W3 (closes from 2026-10-27) was not loaded.** **Verdict: FALSIFIED.**

## Duplicate check
Not a duplicate. NEWH4 TAIL pooled YES and NO at 2c to 6c (no side split); LADLONG1 bought the 88c to 98c side; MAKERTAIL1 saw the side split post hoc on 175 resting orders.

## Results (C = 10, fee and spread paid, held; cents per contract)

| Side | Trades (events) | Win vs paid | Mean net | PF | PF x1.2 fee | Event z | H1 mean / PF | H2 mean / PF |
|---|---|---|---|---|---|---|---|---|
| DOWN: buy NO below spot | 1,249 (1,249) | 13.53% vs 16.77% | -4.23c | 0.72 | 0.71 | -4.43 | -4.75c / 0.70 | -3.71c / 0.74 |
| UP: buy YES above spot | 1,278 (1,278) | 14.40% vs 16.86% | -3.46c | 0.77 | 0.76 | -3.58 | -2.28c / 0.85 | -4.66c / 0.69 |

By paid band (win vs paid, PF): DOWN 3c-10c 4.9% vs 6.4% (0.71), 10c-20c 11.9% vs 14.6% (0.73), 20c-30c 19.6% vs 24.3% (0.71). UP 5.4% vs 6.8% (0.72), 12.5% vs 14.6% (0.78), 20.8% vs 24.1% (0.77).
By distance bin (d < 0.8 / 0.8 to 1.4 / 1.4+): DOWN PF 0.69 / 0.77 / 0.67 (n 736 / 441 / 72); UP PF 0.70 / 0.83 / 1.09 (n 752 / 443 / 83). No zero-volume fills at this look.

**Side difference (DOWN minus UP):** raw -0.77c overall, -2.47c in H1, +0.94c in H2 (sign flips); bin-adjusted -2.30c, -3.26c, -1.10c (negative in both halves); paired event z -0.63 (H1 -0.82, H2 -0.04).
No side reaches PF 1.5 in either half (best half is UP H1 at 0.85). Both fail the registered bars, so FALSIFIED on both conditions.

## What it says
- Both cheap tails lose the same way, about 2.5 to 3.3 points of win rate under the price paid: the ladder's cheap side is not a bargain on either side, which is the NEWH4 TAIL result extended to 3c to 30c.
- **MAKERTAIL1's side split (YES PF 0.23, NO PF 1.25) does not reproduce as a taker rule on 1,250 trades a side**: the crash tail is slightly WORSE than the rally tail here (-4.23c vs -3.46c), and the difference is within noise and changes sign across halves. It was the correlated-sample shape (strikes of one close move together) the registration warned about.
- The only positive cell, UP at 1.4+ sd, is 83 trades, PF 1.09, z 0.28: noise, not scored as a try.
- Ethereum (KXETHD, `ladders.sqlite`): not run. That file's candles end only 5 to 7 minutes before the close, so there is no 25 minute look. Information only, no try lost.

## Verdict, probe spec, ledger
FALSIFIED (registered prediction held: both sides PF 0.7 to 0.8, difference inside -1c to +2c raw). No W3 read, no probe spec warranted. Tries 2, **N +4**.
