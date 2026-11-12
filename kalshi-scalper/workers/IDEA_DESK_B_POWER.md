# Idea Desk B: power analysis of every card, and the retire list (Nov 12, 2026)

Asked for by the Chief of Staff (owner directive): spend Kalshi reads only on tests that can reach a verdict; retire the cards that cannot. No Kalshi read was made for this file. Cards: `workers/IDEA_DESK_B_NOV11.md`.

## 1. What the bar costs in sample size

The research bar as it is applied in this repo: cash PF 1.5 on development and held-out AND a z score that clears the deflation count (about 5.3 at N about 1.1 to 1.5 million tries). For a bet held to settlement, bought at price p with the fee 0.07 x p x (1 - p), the table gives the number of INDEPENDENT bets needed for the z score to reach 5.3, if the true profit factor is the one in the column. "80% power" means an 80% chance of clearing it; the last column is an ordinary z of 2 with no deflation, shown only for scale.

| Price paid | True PF | True win chance | Net per contract | Bets for z 5.3 (even chance) | Bets for z 5.3 (80% power) | Bets for a plain z of 2 |
|---|---|---|---|---|---|---|
| 0.20 | 1.5 | 0.287 | 7.5c | 1,012 | 1,358 | 144 |
| 0.20 | 2.0 | 0.349 | 13.8c | 337 | 453 | 48 |
| 0.20 | 3.0 | 0.445 | 23.4c | 126 | 170 | 18 |
| 0.50 | 1.5 | 0.617 | 9.9c | 675 | 906 | 96 |
| 0.50 | 2.0 | 0.682 | 16.5c | 225 | 302 | 32 |
| 0.50 | 3.0 | 0.763 | 24.5c | 84 | 113 | 12 |
| 0.75 | 1.5 | 0.829 | 6.5c | 932 | 1,251 | 133 |
| 0.75 | 2.0 | 0.866 | 10.3c | 311 | 417 | 44 |
| 0.75 | 3.0 | 0.906 | 14.3c | 117 | 156 | 17 |

A time-exit trade with a 6c standard deviation needs 340 trades at a true 2c net and 150 at 3c (80% power).

Two things follow, and they matter more than any single card:

1. **Bets that share one day or one event are not independent.** The count that matters is clusters (print days, election dates, weeks), not markets.
2. **A family with about 12 events a year cannot pass this bar in any useful time.** At a true PF of 1.5 it needs roughly 900 to 1,350 independent events: decades. Even at a true PF of 3 it needs over 110: nine years. Only two kinds of idea can reach a verdict of PASS inside a year: markets that settle every day or faster (300 or more independent clusters a year), and structural locks, whose bar is a count and not a z score. Every monthly-release, court-term and election-night card can at best be FALSIFIED quickly or sit as NOT_ENOUGH_DATA for years.

This is a property of the bar and the calendar, not of these particular ideas. **For the owner, through the Chief of Staff (not this desk's decision):** either slow event families are simply out of reach of the research bar, or the small-dollar politics program needs its own stated screen for getting ONTO a paper list (the rulebook's proof bar, PF 1.3 over 100 fills in 2 of 3 windows, is already a different and reachable number). This desk changes nothing here; it only reports the arithmetic.

## 2. Every card against that arithmetic

"Clusters" = independent units available: in history, and per year forward.

| # | Card | Clusters in history | Clusters a year forward | Needed (80% power) at true PF 2 | Can it reach PASS within a year? | Decision |
|---|---|---|---|---|---|---|
| 1 | NESTCOMBO | n/a | n/a | a count | no: combos have no posted asks | CLOSED (Nov 12, Chief of Staff) |
| 2 | ECONLAG | about 70 print days | about 36 | about 340 at 2c net, 150 at 3c | no (history plus two to seven years) | DEMOTED: one falsification run only, and only through the separate pull route (about 390 reads). It can die fast; it cannot pass before about 2029 |
| 3 | BALLOTNO | 1 election date (39 states that night) | under 20 measures in 2027; about 150 in Nov 2028 | about 420 | no | FINISH the description already under way (113 reads, approved), then PARK until 2028 |
| 4 | UNRATEROUND | about 33 months | 11 | about 300 | no | RETIRED |
| 5 | FAANOTICE | 0 (forward only) | about 36 | about 300 | no, and the source's terms are unread | RETIRED (blocked and underpowered) |
| 6 | SCOTUSAUTH | 15 to 30 cases | about 12 | about 300 | no | RETIRED |
| 7 | WXCOMBO-XCITY | n/a | n/a | n/a | no: same reason as card 1, combos carry no posted asks, so a combo cannot be priced from public data | CLOSED. The correlation measurement stops; it has no use without a combo price |
| 8 | WXCOMBO-PERSIST | n/a | n/a | n/a | no, as card 7 | CLOSED |
| 9 | MOVPARITY | arm A: a count; arm B: 10 to 40 nights | few until 2028 | arm B about 300 nights | arm A only | Arm B RETIRED. Arm A PARKED: every lock scan so far found nothing, so 800 reads at a 4% prior is poor value; revisit only if reads become cheap, on a 20 race sample (about 160 reads) |
| 10 | PRESENTQ | about 11 months | 12 | about 300 | no | RETIRED |
| 11 | TARIFFDTS | 0 to 12 | 12 | about 300 | no; also the Treasury data source needs a person to read its terms (corrected below) | RETIRED |
| 12 | CPIARITH | about 28 months | 12 | about 300 | no | RETIRED |
| 13 | ROLLOFF | 68 daily events | about 365 | about 300 | **yes, if a true PF of 2 exists: about 8 months of forward days** (about 2.5 years at 1.5) | KEPT. Next step is cheap: the proxy check (about 12 reads plus Wikipedia). It dies at once if our poll table cannot reproduce the settled values |
| 14 | IMPLY1 | a count | n/a | a count | no evidence it can | RETIRED after a zero-read first look (section 3) |
| 15 | WIKIEDIT | 20 to 30 | about 10 | about 450 (cheap side) | no | RETIRED |
| 16 | SWEEPSIM | 2 to 3 nights | under 1 | n/a | no instrument exists | RETIRED |

**Left standing: ROLLOFF (kept), BALLOTNO (finish the description, then parked), ECONLAG (one falsification run, later), MOVPARITY arm A (parked).** Twelve of sixteen are closed or retired. Total reads this desk still asks for: 113 (BALLOTNO, approved) plus about 12 (ROLLOFF proxy check). ECONLAG's 390 wait for the separate route.

## 3. Zero-read first look that retired IMPLY1

From the one politics recorder snapshot held (`pol-data`, Nov 11, 19:32Z). The weekly Strait of Hormuz ladders give exact implication pairs that settle the same day, inside the hold window: a weekly total above X forces the peak day above ceil((X+1)/7) - 1. A lock needs the weekly bid above the peak ask plus fees.

| Weekly total above | Its YES bid | Implies peak day above | That YES ask | Cost of the pair (weekly NO + peak YES) | Net after fees |
|---|---|---|---|---|---|
| 23 | 0.51 | 3 | 0.96 | 1.45 | -47c |
| 30 | 0.11 | 4 | 0.88 | 1.77 | -78c |
| 35 | 0.03 | 5 | 0.72 | 1.69 | -71c |
| 50 | 0.00 | 7 | 0.24 | 1.24 | -25c |

The nearest pair is 25c away from a lock, and these books are deep and tight (1c spreads, thousands of contracts at the touch). The inequality is real but far from binding, as it should be in a market that makers watch. The strike wording ("above" or "at least") was not read from the rules text; it cannot move a 25c gap. Probability lowered to under 1%: RETIRED.

## 4. Corrections made to the cards file with this note

- **Treasury Fiscal Data: AMBIGUOUS, not PERMITTED.** The cards file took Refinement's row 79 verdict; the Chief of Staff's list puts Treasury among the sources a person must read first. Card 11 is blocked on that as well as underpowered.
- **Cards 7 and 8 (weather combos) are closed for the reason card 1 was:** a combo cannot be priced from the public book.

## 5. A data problem found on the way

The politics recorder branch (`pol-data`) holds ONE snapshot folder (Nov 11, 19:32Z, 210 quote rows, each market twice) and nothing since, as of Nov 12, 02:12Z (last commit on the branch Nov 11, 20:04Z), although the workflow has been on main since Nov 11, 19:27Z with an hourly start at seven minutes past. Six hourly starts have produced no data: either the starts are being dropped or the runs are failing (possibly the same rate limit this desk hit). Every card and test that counts on politics history accruing forward (ROLLOFF's forward days, POLPARITY1's book read, the politics program's shadow recording) is not accruing until that is fixed. Reported to the Chief of Staff; this desk did not touch the workflow.
