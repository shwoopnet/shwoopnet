# Idea Desk C: published effects screened against the bar (Nov 12, 2026)

Idea Desk C (outside research), reporting to the Head of R&D. Nothing here was scored and no Kalshi request was made. Every figure is a published or practitioner figure on public data, quoted with its source. [research]

**Counts: 16 published effects read; 13 dropped on arithmetic, duplication or the owner's bans; 1 card written (PROPUNDER); 2 pending a third literature read (tennis, table tennis and esports model edges).**

## The arithmetic used for every line

A bet held to settlement at cost c (price paid plus the 7% x p x (1 - p) fee plus half a cent of spread) that wins with true probability w has cash PF = w(1 - c) / ((1 - w) c). PF 1.5 needs:

| Price | Win rate needed for PF 1.5 | Edge needed over the price |
|---|---|---|
| 30c | 41.3% | 11.3 points |
| 40c | 52.3% | 12.3 points |
| 50c | 62.1% | 12.1 points |
| 60c | 71.1% | 11.1 points |

So a published effect smaller than about 11 points in win probability cannot reach the bar, however many events exist. This agrees with Desk B's table in `IDEA_DESK_B_WAVE3.md`.

## Dropped (with the number that drops each)

| # | Published effect | Source | Size | PF it implies at 50c | Why dropped |
|---|---|---|---|---|---|
| 1 | Unders on high NFL totals | Paul and Weinbach (2002), J. Sports Econ 3(3); Kelly and Chen, Research in Business and Economics Journal 14 (https://mobile.aabri.com/manuscripts/193138.pdf) | 59.7% (2001 to 2009); 47.1% (2010 to 2018) | 1.35 at its peak; 0.81 since 2010 | Below 1.5 even at its peak, and decayed. 285 games a year |
| 2 | NFL home underdogs against the spread | Levitt (2004), Economic Journal 114 | 57.7% on contest picks | 1.25 | Below 1.5; gone after about 2005 (Humphreys, Paul and Weinbach 2013) |
| 3 | Reverse favourite-longshot bias, MLB and NHL moneylines | Woodland and Woodland (1994, 2001, 2003); Gandar et al. (2002) | Too small to beat the vig, in the authors' own words | under 1.1 | Below 1.5; Kalshi game winners already match Polymarket's Brier (FAMXV) |
| 4 | Betting against NBA and NFL winning streaks | Camerer (1989); Paul and Weinbach (2005); Paul, Weinbach and Humphreys (2014) | Not profitable after costs | about 1.0 | Below 1.5; S07 streak exhaustion FALSIFIED here |
| 5 | Draw underpricing in soccer | Pope and Peel (1989); Whelan (2026) Betfair, 200,622 matches (https://www.karlwhelan.com/Papers/Betfair.pdf) | None on exchanges today | 1.0 | No effect left; TIE3 covers the listed tie |
| 6 | Favourite-longshot bias by tennis tier | Lahvicka (2014), AEL 21(2), 45,000 matches | Stronger at low tiers | not computed | The edge is on favourites: the owner's ban |
| 7 | Kalshi favourite-longshot bias | Burgi, Deng and Whelan (2026), https://www.karlwhelan.com/Papers/Kalshi.pdf | Contracts at 10c or less lose over 60%; above 70c small positive | not computed | Favourite side: the owner's ban; cheap side: CALIB1 closed |
| 8 | YES overpricing in single-name and mention markets | Bartlett and O'Hara (2026), SSRN 6615739 (https://conference.nber.org/conf_papers/f243677.pdf) | 4.5 points on average; about 8.6 points in the 40c bucket | 1.09 at the average; 1.33 at the 40c bucket (NO at 60c) | Below 1.5 at its best bucket; the authors' worst deciles are informed YES flow; MENT1 and MENTPERSIST1 already cover the family; NO at 70c and up is favourite-and-hold |
| 9 | NO beats YES across Kalshi | Becker, https://www.jbecker.dev/research/prediction-market-microstructure | +0.83% dollar-weighted for NO | 0.94 | Far below 1.5 |
| 10 | Long-dated prices too close to 50 | Page and Clemen (2013), Economic Journal 123; Le (2026), arXiv 2602.19520 | Slope 1.32 beyond a month; politics 1.73 to 1.83 | not computed | Implies buying the favourite (ban); politics is a slow family |
| 11 | Kalshi macro high tails overpriced | Diercks, Katz and Wright (2026), FEDS 2026-010 | "a little too frequently", no return figure | not computed | No size; macro is a slow family (about 44 a year) |
| 12 | Losing side priced too high late in games ("Yogi Berra") | Page (2012), cited in Burgi et al. | not seen | not computed | Buys the late leader: favourite-late ban; in-game lag closed |
| 13 | Cross-venue gaps and Polymarket leading Kalshi | Ng, Peng, Tao and Zhou, SSRN 5331995; QuantPedia | Seconds to minutes | not computed | Polymarket reads parked by the owner; FAMXV found a 0.5c median gap on games |

Also read, not usable as written: PredictIt calendar effects (Physica A 523, 2019, 3,385 markets: none in price); the 80 minute Polymarket repricing claim (no verifiable source).

## What this says, plainly

The published crowd biases that do not buy the favourite are 1 to 9 points, and almost all have decayed since the papers. None of the peer-reviewed ones reaches the 11 to 12 points the bar needs at mid prices. The only figure above the line is a practitioner one (row PROPUNDER in the cards file), and it is unverified.
