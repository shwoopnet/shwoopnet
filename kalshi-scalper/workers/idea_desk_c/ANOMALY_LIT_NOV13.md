# Literature pass: anomalies with a named counterparty and 4c or more after fees (Idea Desk C, Nov 13, 2026, about 19:45Z)

For the Head of R&D's 19:22Z request. Two workers read papers and abstracts only; no Kalshi request and no data. Excluded as closed: favourite-longshot, in-play lag, lock or parity, and outside fair value. [research]

**Counts:** about 10 sources read (3 in full text, the rest abstracts or snippets); **0 clear 4c after fees with a named counterparty**; 0 cards. The top 3, none passing:

| Rank | Anomaly and source | Size | Counterparty | Can our recorders test it? |
|---|---|---|---|---|
| 1 | **First hour after a new listing.** Jörnell, Perez and Saguillo, "Opening Wide, Moving Fast", IMDEA/Lund 2026, about 160,000 new Polymarket contracts: the first-minute median taker half-spread is 12c to 16c in non-sports categories and drops about 10 times within an hour. A maker keeps about 3c at the median (economy 3.5c, 86% kept; geopolitics 12c, 25% kept) | About 3c GROSS, under the bar before Kalshi's maker fee (up to about 0.44c); descriptive medians; 16% to 38% of early fills lose for the maker | The first takers in a new non-sports market | Partly. NEWLIST1 (V2, registered and read) already tested Kalshi new listings. A one-sided "quote in the first hour" rule is market making (declined) unless it passes its own uniqueness check. The combo and politics recorders see listings only at 30 minute steps |
| 2 | **Left-digit bias at round prices.** "Does the left-digit bias affect prices in financial markets?" (abstract only; authors and venue unconfirmed), Nadex binary FX options, 2016 to 2017: the chance of winning jumps at round price thresholds, strongest among less sophisticated traders | No cents or after-fee figure | Less sophisticated retail (inferred) | Yes in principle: R6 and NC15 books (2 to 5 second polls) show prices and depth at round cents on Kalshi. It would be a new test, not a replication, and nothing says it reaches 4c |
| 3 | **Weekend noise traders.** Flepp, Nüesch and Franck (Zurich WP 2013), Betfair soccer: more liquidity but weaker efficiency at weekends, as recreational bettors join; Brown (Economic Journal) finds mispricing rises with distraction | No return per bet after commission | Weekend recreational bettors | Partly: R6 (Bitcoin and gold to Dec 31) and NC15 books run through weekends, so a weekday-against-weekend spread and staleness count is possible. Any edge rule would be a version of the 15 minute families unless the signal is new |

**Others, not ranked:**
- Bürgi, Deng and Whelan, and Becker: makers beat takers by 1c to 3c, mostly the favourite-longshot pattern.
- Gebele and Matthes 2026: a settlement wedge on 90c-and-up contracts is gross carry, not an edge, and on the favourite side.
- Kalshi's fee rounding: the docs (seen in search results only) say fees are rounded to $0.0001 with whole-cent rebates, so the "round up to the cent" jump may be largely refunded; no study of fee-driven clustering exists.
- A Management Science paper on sportsbook line overreaction: not a Kalshi-style venue, and no size obtained.

**Verdict:** no brief. The nearest is the first hour after a non-sports listing, at about 3c gross, unreplicated, and inside the declined market-making family. A recorder-side count, not a card, could check the left-digit and weekend effects on Kalshi's own books if the Head wants one, with zero tries.
