# OIVER-CAP30 build 2: rules as read and expected figures by hand (History Miner, Nov 13, 2026)

Written BEFORE the code, from Desk A's card 2 only: `kalshi-scalper/workers/DESK_A_OICORE_VERSIONS_NOV13.md` at 741092a7 (sha256 e7b918b0), under the Head of R&D's 19:53Z convention for the OIVER builds. Desk A's build was not read. No real row read and no run.

## Rules as built
The parent is OICORE exactly as in OIVER-SPREAD build 2 (`../oiver_spread2/EXPECTED_BY_HAND.md`, with the dated line of 19:53Z governing):
- quote from the candle ending close - 180;
- OI rise >= 86,300 inclusive;
- rule 18;
- the cheaper ask, with a tie to YES;
- the band [0.08, 0.50] inclusive;
- the price is the ask seen, assumed filled (an upper bound on fills);
- fee per order at C = 20, ceil(round(cents, 6));
- a void is a fee-only loss.

**VERSION:** the parent's trade kept only if the side's ask is <= 0.30 (+1e-9), the 8c floor unchanged. Otherwise it is counted as above_cap. No spread condition.

Printed as in OIVER-SPREAD:
- the removed share first;
- parent and version: n, PF, net, mean, halves by count (first floor(n/2)), net per contract-week over the file's development span;
- the 7g takeover check and the card's kills as information;
- "no evidence at n = x" under 60.
A held-out read is refused.

**Open reading for the Head:** the 0.30 ceiling is inclusive, as the parent's 0.50 is.

## Made-up windows: inv/windows.csv, a copy of OIVER-SPREAD's (sha256 9b89edac)
The parent is unchanged from OIVER-SPREAD's reworked figures:
- n 5, PF 1.429194, net 0.4925, mean 0.0985;
- halves 2.436508 / 1.048048;
- 41.37 per contract-week.

| W | side, ask | parent net | version |
|---|---|---|---|
| 1 | YES 0.22 | +0.7675 | keep |
| 2 | NO 0.30 | -0.315 | keep (0.30 is inclusive; the 0.05 spread does not matter here) |
| 3 | NO 0.12 | +0.8725 | keep |
| 8 | YES 0.49 | -0.5075 | above_cap |
| 9 | NO 0.31 | -0.325 | above_cap |

**Version:**
- n 3; wins 1.64; losses 0.315; PF 5.206349; net 1.325; mean 0.441667;
- halves: W1 gives inf, and W2 with W3 gives 0.8725 / 0.315 = 2.769841;
- per contract-week 1.325 x 84 = 111.3.

**Removed share:** 0.4.

**Counts:** oi_below 1, cheap_skipped 1, no_quote 2, held_out_ignored 1, above_cap 2.

**Takeover (info):** PF lift, net per week and second half all yes; 60 signals no.
**Kills (info):** no, no.
**Label:** "no evidence at n = 3".

## Refusals expected
- held mode
- a HELDOUT_ path
- an odd result text

## Dated line, 2026-11-13 21:17Z: the governing card is Desk A's 23b5bd9b (sha256 ae1f1ee6...); reworked by hand before the code
The same three changes as OIVER-SPREAD build 2's dated line:
- no_quote is renamed not_two_sided;
- weeks run over the parent's trades, at least one week, so the divisor is 1 here: parent 0.4925 per contract-week, version 1.325;
- a development row outside [2026-09-12, 2026-11-09) stops the run.
Everything else is unchanged (version PF 5.206349, the 0.30 ceiling inclusive, as the card's 21:13Z amendment confirms).
