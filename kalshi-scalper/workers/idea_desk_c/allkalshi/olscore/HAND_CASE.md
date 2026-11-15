# ol_score.py hand case (Idea Desk C, Nov 15, 2026; synthetic, written before any data for these cards is pulled)

Fee: ceil(7% x p x (1-p) x 100) / 100, per order, 1 contract.

## NBA_O: one market, fade

**Setup.**
- Occurrence 2026-10-25T03:00Z, so the tip proxy P is 00:00Z.
- G is 2026-10-24T23:30Z and D is 22:30Z. The 3 h anchor is 19:30Z.
- Close 2026-10-25T02:30Z. Result "no".

**Signal.**
- Mid at the anchor is .31 (.30 / .32); mid at D is .46 (.45 / .47). So m = +.15, which is at least .10.
- Fade: buy NO. The ask is 1 - .45 = .55, inside .40 to .60.
- e = .55, fee(.55) = ceil(1.7325) = .02, so the cost is .57.

**Results.**

| Try | What happens | Result |
|---|---|---|
| hold | 1 - .57 | **+43c** |
| hold, 1c line | a = .56, fee .02, so 1 - .58 | **+42c** |
| T (target min(1.10, .90) = .90) | NO bid .78 at G+1h, then .92 at G+1.5h: sold at .92, fee .01. So .92 - .01 - .57 | **+34c**, exit T |
| S (line .275) | the NO bid never falls to it: held | **+43c** |
| M (at G) | NO bid 1 - .54 = .46, fee .02. So .46 - .02 - .57 | **-13c** |

**Three more checks in the same data:**
- **NBA_L:** the 1 h move is .46 - .41 = .05, under .06. So no trade (drop no_move).
- **Window:** a market closing Nov 8 (inside PROPUNDER's reserve) is counted outside_window, and its result ("TRAP") never reaches a kept row.
- **Proxy check:** one market closing at 22:00Z, before G (23:30Z), is 100% of the kept markets, over 2%. The scorer stops before any result or candle read.

## MENT: one event, four words, the cap of 3

**Setup.**
- Occurrence 2026-06-10T18:00Z. D is 17:00Z and the anchor is 12:00Z.
- Mid moves m are .25, .15, .09 and .20. All are at least .08, and all buy YES at an ask of .46.
- The cap of 3 keeps the largest moves (.25, .20, .15) and drops 1 (event_cap 1).

**Other rows:**
- The "Event does not qualify" word is dropped.
- An Aug 10 event (TRUMPTOPIC1's cut) is outside_window, and its "TRAP" result is never read.

**Results.**

| Try | What happens | Result |
|---|---|---|
| hold | fee(.46) = ceil(1.7388) = .02. Won: 1 - .48 | **+52c** each |
| M (at O - 5 min) | YES bid .60, fee .02. So .60 - .02 - .48 | **+10c** each |

`python3 -I test_ol_score.py` checks every number above (5 tests).
