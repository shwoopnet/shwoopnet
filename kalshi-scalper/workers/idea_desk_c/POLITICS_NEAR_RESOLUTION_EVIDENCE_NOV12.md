# Politics within 30 days of settlement: the outside record (Idea Desk C, Nov 12, 2026)

For the Head of R&D and Desk B. Read B of the 20:26Z message. Ideas only, no Kalshi request, nothing changes a registration. [research]

**Counts:** 5 questions; 8 sources (5 verified from the text, 3 from abstracts); 1 direction with outside support (buy the favourite, sell the longshot). That direction is the owner's banned shape above about 70c, and the approval NO side read on Kalshi's own data did not reproduce it. Other results:
- 1 venue-specific gap above the round trip: PredictIt ladder sums over 110, caused by stake caps; not shown on Kalshi.
- 2 questions with nothing found: a "nothing happens" premium, and approval or polling-average markets.

## 1. Favourite-longshot bias in politics, by horizon

- **Le (2026), arXiv 2602.19520, Kalshi politics, 6,609 markets and 4.9M trades (verified).**
  - Recalibration slope by time to close: 0 to 1 h 1.34; 3 to 6 h 1.32; 6 to 12 h 1.55; 12 to 24 h 1.48; 24 to 48 h 1.52; 2 days to 1 week 1.83; 1 week to 1 month 1.83. The 1 to 3 h value of 0.93 is called a composition artefact by the paper. Intercept +0.151.
  - A slope above 1 means prices are UNDERconfident: favourites too cheap, longshots too dear. The paper's example: a 70c contract one week out implies about 83%.
  - **Calibration, not returns.** The paper reports no trading result. Large trades show a slope of 1.74, single contracts 1.19.
- **Burgi, Deng and Whelan (2026), Kalshi, politics only (verified, Table 8).**
  - Sample: 26,819 YES daily observations, from the closing price back to 10 days out.
  - Price slope 0.022, not significant. Implied pre-fee profit for a YES of about -1.7c at 10c, -0.8c at 50c and +0.1c at 90c, so **under 2c, well inside a 3c to 9c round trip.**
- **Page and Clemen (2013), Economic Journal 123, Intrade, 1,787 markets (verified).**
  - Strong longshot bias in politics, pooled over all horizons: 20c won 10.9%, 80c won 92.8%.
  - Under 100 days out it was "reasonably well calibrated" (shown in a figure only).
  - Returns vanished at a 15% to 25% discount rate.
- **Zitzewitz (2026), NBER w35845, PredictIt (abstract):** longshot overpricing "larger than in other prediction markets". No size given.

**What the Le slopes would mean as a bet, if they were returns.** This is my arithmetic, slope only and intercept ignored: buy the favourite at price p, held, with the fee and half a cent of spread.

| Price | Slope 1.34 (last hour) | Slope 1.5 (12 to 48 h) | Slope 1.83 (2 days to a month) |
|---|---|---|---|
| 55c | PF 0.98 | 1.01 | 1.08 |
| 60c | 1.05 | 1.12 | 1.28 |
| 65c | 1.12 | 1.24 | 1.52 |
| 70c | 1.21 | 1.39 | 1.84 |
| 80c | 1.44 | 1.80 | 2.85 |

So only a favourite of 65c or more, at 2 days to a month out, clears 1.5 on paper. The checks against that:
1. It is the favourite-and-hold shape, which the owner bans without a named exception.
2. Kalshi's own data disagrees. Refinement's approval NO side (arm A, NO paid 75c to 90c) read cash PF 1.03 on 127, closed today. Burgi et al. find the politics slope not significant.
3. Calibration slopes on pooled markets are not returns. The 1 week to 1 month bucket mixes many market types, and Page and Clemen show the gap vanishing once the cost of locked money is counted.
4. Politics is a slow family on Desk B's count (about 17 independent events a week in the recorded families), so about 1,200 bets takes well over a year.

## 2. "Nothing happens" premium

**Nothing peer-reviewed found.** A Substack count of 161,638 Kalshi and Polymarket contracts (72% settle NO, binaries 73.7%) says this is already in the price, and that NO on everything does not outperform. The Le slopes point to compressed prices, not to a NO tilt.

## 3. Partisan, attention or whale bias

- **Rothschild and Sethi (2016), Intrade 2012 presidential market, 6,300 accounts, about 287,000 trades (verified):** one trader long Romney held Intrade 5 to 10 points away from Betfair for months, and lost close to $7M. The gap closed when he unwound. That is above the round trip, but it was one venue and one whale, and it was a cross-venue spread.
- **Iowa Electronic Markets (Forsythe et al. 1992, 1999):** partisan traders are wishful, but marginal traders set unbiased prices. No size verified.
- **Partisan mispricing with a measured size on PredictIt or Kalshi:** nothing found.

## 4. Ladders on a vote share, seat count or number

- **PredictIt:** bid prices "often persistently added to more than 110" (Zitzewitz 2026, abstract). Chronic mispricing against Iowa (Stershic and Gujral 2020, abstract), caused by the $850 stake limit.
- **Kalshi:** nothing found. Kalshi has no such cap, and our own lock and parity scans (LADBFLY1: 0 violations in 266,302 snapshots) found nothing. The row is on the declined list.

## 5. Approval and polling-average markets

**Nothing found** on Kalshi or PredictIt.

## For Desk B's one politics rule, plainly

- **Supported direction:** buy the favourite and sell the longshot, at 2 days to a month out, at 65c and up. That is the banned shape, and Kalshi's own approval data (arm A) did not show it.
- **Mid band:** in 55c to 65c the published slopes imply PF 1.0 to 1.5 at best, which is under the bar. Whether a 55c to 65c favourite counts as "favourite-and-hold" is the Head's ruling.
- **Opposite direction:** no outside support for buying the longshot, "nothing happens" NO, or partisan fades.
- **Limit entry:** a resting entry in politics saves cost, but the published maker edge there is the second smallest of any category (+0.51% gross, Becker). So a limit-entry version gains cost, not edge.
