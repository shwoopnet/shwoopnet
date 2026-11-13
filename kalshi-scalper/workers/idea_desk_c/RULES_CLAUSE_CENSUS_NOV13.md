# Settlement-rule clauses in the landed lists (Idea Desk C, Nov 13, 2026, lane (e))

For the Head of R&D. Read from lists already on `kalshi-pull-data` (the census listing, the MAPBREAK, TESTING, ESOCTIE, INPLAYJUMP, WHEEL0, NHLOT, SPREAD and CFRTI-K lists: 394 files). No Kalshi request, no candle read, no rule registered. [research]

**Counts:**
- 606 series and 210,206 markets read.
- 78 series had at least one market settle at a value other than 0 or 1 (4,047 markets).
- Clause types found, by series:

| Clause type | Series |
|---|---|
| fair price | 210 |
| tie or draw | 71 |
| overtime or extra time | 105 |
| withdrawal, retirement or walkover | 39 |
| fixed dollar void ($0.50 or $0.33) | 10 |
| player inactive | 36 |
| abandonment | 4 |
| split payout | 4 |
| early close | 1 |

- **Candidates: 0.** Every clause family with a count large enough to matter shows, in its last trades, a market that already prices the clause.
- VOIDSNAP (Desk B) stays the only rules-text mechanism with a live gap.

## The clauses that a price could contradict, and what the lists show

### 1. Fixed-price voids: the void price is KNOWN in advance

The clause, quoted:
- **ITF singles and doubles, men and women:** "If the match does not occur (signaled by a ball being played) due to a player injury, walkover, forfeiture, or any other cancellation (all before the match starts), all markets will resolve to $0.50. If a player withdraws or forfeits after a match has started, that player will resolve to No."
- **Russia Liga Pro table tennis:** "cancelled or postponed more than 48 hours ... both markets will resolve to $0.50".
- **E-soccer:** "cancelled or postponed more than 2 weeks ... all markets will resolve to $0.33" (three contracts).
- **E-basketball:** a tie resolves to $0.50, as does a cancellation.
- **T20, ODI and Test cricket:** a tie, no result or abandonment resolves to $0.50.

This would remove VOIDSNAP's hardest condition (knowing the fair price). But the lists show nothing to buy:

| Series | Events | Voided events | Void rate | Voided markets with any trade | Last trade 10c or more from the void price |
|---|---|---|---|---|---|
| ITF men's singles | 1,304 | 19 | 1.5% | 35 | 1 |
| ITF women's singles | 1,393 | 23 | 1.7% | 43 | 0 |
| ITF doubles | 59 | 5 | 8.5% | 10 | 1 |
| Liga Pro table tennis | 1,330 | 69 | 5.2% | 4 | 4 |
| E-soccer | 7,570 | 182 | 2.4% | 13 | 8 |

- **ITF:** voided matches close quickly, and their last trades sit at the void price.
- **Liga Pro and e-soccer:** the voided markets barely traded at all. So no book exists to buy into.
- **Dropped:** count, and "listed is not quoted" (the Nov 12 lesson).

### 2. Player props that settle at a "fair price" when the player is inactive, or in the "protected" versions

The clauses, quoted:
- `KXNBAPTS` and siblings: "If a player is inactive, or active but never takes the court, the market settles to a fair price."
- The protected versions (`KXNBAPTSPROT`, `KXNBAREBPROT`, `KXNBAASTPROT`, `KXNBA3PTPROT`, `KXNBAPRAPROT`, `KXNFLRECYDSPROT`, `KXNFLTDPROT`): "If the individual player enters the game during the first half of the game but does not enter the game after the conclusion of the first half ... this Contract resolves to the fair price prior to the opening tip of the game unless the player records the required number of points."
- **Why it looked promising:** the protected clause looked like the best seed. A player hurt in the first half would see his normal prop fall toward 0, while the protected one is owed its pre-tip price.

The lists, one night (Nov 10):

| What | Count |
|---|---|
| Fair-price settlements across the NBA prop series | about 330 markets on 4 to 6 games |
| Of those that traded at all, last trade 10c or more from the fair price | 13 |
| Last trade 25c or more from the fair price | 1 |
| Protected series: traded markets among the fair settlements | 15 (of about 160) |
| Protected series: last trade 10c or more away | 1 |

Desk B found the same for ruled-out players.
- **Dropped:** priced correctly where traded, rarely traded where it might not be, and no forward log records props.

### 3. Cricket: abandonment and no result at $0.50

- **Mechanism:** rain makes "no result" likely, which pulls both sides toward 50c, so the underdog gains.
- **Count:** only 6 settled T20 markets in the lists (CRICT20 had 10 treated of 150).
- **Information:** it would need a weather source for venues outside the US. NWS covers only the US, and Open-Meteo is barred.
- **Dropped.** What it would need:
  - a permitted national weather service per cricket country, with terms read;
  - a count of T20 matches and no-results from Kalshi history (CRICT20's lists).

### 4. Other clauses read, not usable

- **NHL totals:** "the shootout result will be recorded as one goal". This is standard in sportsbooks too, so it is not a mispricing seed.
- **NHL overtime:** "played if and only if ... the opening faceoff" is a definition, not a price gap.
- **Crypto "lead" 15 minute markets:** ties split $1 among the tied coins. Ties to three decimals are rare.
- **Rates, FX and 15 minute markets:** "corrections" clauses only.
- **The S&P 15 minute market:** the single early-close clause, inside a closed family.

## What would make lane (e) produce a candidate

A clause whose trigger is visible on Kalshi's own screen before settlement, and where the lists show traded prices away from the rule's payout. The landed lists show that only for esports "fair market price" voids (VOIDSNAP, with Desk B). The next places to read are series that are not yet in any landed list: golf, motorsport, combat sports and award shows. Their clause types (withdrawal, disqualification, a tie for a placing, dead heat rules) are where sportsbooks themselves differ most. A one-page lists job for those series is the cheapest next step; this desk does not request it.

## Addendum (Nov 13, 2026): golf tie rule, and how others settle voids

### Golf: Kalshi pays boundary ties in full; sportsbooks apply a dead heat

**The clause.** Kalshi's GOLFFINISH contract terms (https://kalshi-public-docs.s3.amazonaws.com/contract_terms/GOLFFINISH.pdf, read in full):
- "If <player> is tied for a position at the boundary of <count>, the market resolves to Yes", with a settlement value of $1.00.
- GOLFCUT counts "top 65 and ties" as made the cut.
- A withdrawal before tee-off settles at the last fair price; after tee-off it is a No.

**The sportsbook rule.** Sportsbooks apply a dead heat. Caesars' FAQ: stake x (places available / players tied), so four tied for 10th pay a quarter (https://www.caesars.com/sportsbook-and-casino/ks/support/dead-heat-faq). Some books pay ties in full at worse odds.

**The arithmetic, if Kalshi's price copied a dead-heat price exactly.** The tie inputs are my estimates, not measured:

| Player | Chance of a top-N finish | Chance of finishing tied at the cut-off place | Kalshi price under a dead heat | PF |
|---|---|---|---|---|
| Top-10 contender | 15% | 3.5% | about 12.9c | 1.07 |
| Top-20 contender | 40% | 8% | about 34.4c | 1.16 |
| Top-20 contender, more ties | 40% | 12% | about 31c | 1.35 |

**Dropped.** It does not reach 1.5 even if the market ignored the rule entirely. It is a slow family (about 45 tournaments a year), and no forward log records golf. One public article reportedly says a tie for 10th paid all eleven tied players on Kalshi (search summary only), so traders may already know.

### How exchanges and books settle a cancelled or walked-over match (evidence for VOIDSNAP)

- **Pinnacle:** forfeits and walkovers are void "regardless of how the governing body ... scores it". An esports match not started within 30 hours is void.
- **DraftKings table tennis** (MA house rules 8.1.24): void on retirement, disqualification, walkover or cancellation unless already decided.
- **Betfair and Bet365:** not verified (403 and nothing found).
- **The norm:** stakes are returned. No house found pays a pre-play walkover as a win.
- **Price moves on forfeit or walkover news:** no published measurement found. The nearest is a fixing investigation noting pre-match drift when a player is injured warming up (one 2010 match moved from about 69% to 47%).
- **Possible source of confusion:** a third-party guide says an ATP walkover on Kalshi "will resolve to 50-50". Kalshi's tennis set-score terms say "last fair price". Our own landed rules text says $0.50 for ITF and fair price for ATP and WTA challengers. So the rule differs by series, which itself could confuse traders.
- **How Kalshi sets a "fair price":** not published.
  - ESPORTSMAPS.pdf: "may resolve to the last fair price as determined in the sole discretion of the Exchange".
  - The help center says only "fair market value" or "a non-standard value such as 50-50".
  - NCAAB terms allow Kalshi to reject the last trade as unfair.
  - The Rulebook's definitions chapter is the next place to read.
- **Cancellation rates for tier 2 and 3 esports and Russian table tennis:** none published. Single cases only. Our own list counts (Desk B's and this page's) are the only rates we have.

**For VOIDSNAP:** sportsbooks return stakes, Kalshi pays a discretionary price. A trader who carries the book convention ("void, money back") onto Kalshi has no reason to sell a team rumoured not to show. A trader who thinks a no-show is a loss does have reason to sell. Nothing published says which is more common, so the card's own measurement remains the only evidence.

## RULESREAD_LISTS read (Nov 13, 2026, 06:50Z; pull/RULESREAD_LISTS/2026-11-13T0637Z_43379966481, status complete, no list left on a cursor)

Rules text, and counts of settlements at a value other than 0 or 1, for the 26 series closing Aug 1 to Nov 12, 2026. Results were read only as counts of those settlements, as the job's purpose states; no price path and no rule was scored. [research]

| Series | Markets | Events | Settled at a set price | Of those, traded | Last trade 10c or more from the settlement |
|---|---|---|---|---|---|
| Golf 3-ball (KXPGA3BALL) | 1,518 | 506 | 163 | 111 | 34 |
| UFC method of victory | 1,036 | 148 | 21 | 13 | 1 |
| UFC fight | 302 | 151 | 14 | 14 | 0 |
| MotoGP race | 133 | 6 | 18 | 18 | 1 |
| MMA fight | 52 | 26 | 6 | 6 | 5 |
| PGA top 10 | 696 | 7 | 17 | 5 | 0 |
| PGA make cut | 622 | 6 | 15 | 6 | 0 |
| DP World Tour top 10, top 20, make cut | 1,067 / 1,067 / 1,003 | 8 / 8 / 7 | 3 / 3 / 9 | 0 | 0 |
| F1, NASCAR, IndyCar, PGA winner, head-to-head | 1,326 in all | | 0 | | |

**What the clauses say.**
- **Golf 3-ball:** a tie for the lead pays "$1/N, rounded down to the nearest cent". A three-way tie pays $0.33 each, so the three sum to $0.99. A withdrawal before tee-off settles at "fair market value". Of 506 three-ball events, 65 ended in a two-way tie (0.5, 0.5, 0) and 2 in a three-way tie; about 7 settled at fair values (withdrawals).
- **MMA:** a tie or no contest resolves "50/50 for both fighters"; a cancellation beyond two weeks settles at a fair price.
- **Golf top-N and make-cut:** boundary ties pay in full (GOLFFINISH, as read earlier). The few set-price settlements are withdrawals before tee-off.
- **Motorsport and the PGA winner:** no set-price settlements in the window.

**Candidates: 0.**
- **Golf 3-ball** is the only fast family here: about 1,700 events a year at this pace, not a slow family. The tie split is the standard dead-heat convention the books use too, so a price that ignores it would show as the three prices not summing to about $1. That is a parity scan, a closed row.
- **The 34 traded markets with a last trade 10c or more from 50c** are mostly trades made mid-round, before the tie was known. A last trade is not a book that could be bought at the time.
- **MMA:** 5 of 6 set-price settlements traded 10c or more away. That is 6 events in three and a half months, too few to measure.
- **Golf top-N:** the full payout on boundary ties stays dropped on its own arithmetic (PF 1.07 to 1.35 even if wholly unpriced).
