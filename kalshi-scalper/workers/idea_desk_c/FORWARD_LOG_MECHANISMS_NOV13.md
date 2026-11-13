# Published mechanisms for the six forward logs (Idea Desk C, Nov 13, 2026)

For the Head of R&D and the idea desks. Evidence only: no card, no threshold, no Kalshi request, nothing stored. [research]

**Counts:**
- 6 sources; 31 papers and practitioner items read, 11 verified from the full text (the rest from abstracts or summaries, marked).
- Mechanisms listed: 9, at most 2 a source.
- Sources with nothing published that fits: 0 in full; 3 partly (oil and gas release days, totals pace in play, and volume spikes in politics have nothing).
- Mechanisms with a published size that plausibly clears our costs: 1 (the combo leg-count markup). It sharpens a registered paper test rather than starting a new family.

## 1. NC15: book and tape on 11 non-crypto 15 minute series

1. **Currencies weaken during their own trading hours.**
   - **Source:** Breedon and Ranaldo, J. Money, Credit and Banking 2013 (https://www.snb.ch/en/mmr/papers/id/working_paper_2011_04, abstract and working paper summary). Local residents are net buyers of foreign currency in their own hours, so the local currency drifts down.
   - **Size:** a few basis points over several hours (not retrieved exactly). A working-paper line calls a EUR/USD version "simple, profitable".
   - **Closest closed item:** none. It uses only the clock and the ticker. It is not favourite-late, not a price sweep and not a spot lag.
   - **Prior:** low. A few basis points over hours may not move a 15 minute up/down binary by a cent.
2. **Book depth imbalance across the five levels.**
   - **Source:** Cont, Kukanov and Stoikov, J. Financial Econometrics 2014 (arXiv 1011.6402); Xu, Gould and Howison 2019 (arXiv 1907.06230); Cartea, Donnelly and Jaimungal, Applied Mathematical Finance 2018. Resting volume imbalance explains or predicts price moves over SECONDS. Deeper levels add fit; the touch imbalance predicts the next market order. All on stocks; no costs.
   - **Closest closed item:** taker order flow (closed). Resting depth is a different field from buy-minus-sell flow, but every result is contemporaneous or seconds ahead, and the benefit goes mainly to makers (market making is closed).
   - **Prior:** very low at a 15 minute horizon.
- **Nothing published that I could verify:**
  - a direction after the oil inventory release (Wednesday 10:30 ET) or the gas storage release;
  - pinning of binaries at expiry;
  - book resiliency or queue depletion at a 15 minute horizon.
- **The London 4 pm fix reversal** (Evans, J. Banking and Finance 2018, 21 currencies) faded after 2013, and it is reported gone after the 2015 window change. Only the volatility remains.

## 2. Kalshi perpetuals: 30 second samples at the US open and close, 1 minute candles, funding

1. **Intraday momentum into the close.**
   - **Mechanism:** the first half hour's return (Gao, Han, Li and Zhou, J. Financial Economics 2018, SPY 1993 to 2013), or the rest of the day's return (Baltussen, Da, Lammers and Martens, J. Financial Economics 2021, 60+ futures 1974 to 2020, https://www3.nd.edu/~zda/intramom.pdf), predicts the LAST 30 minutes in the same direction.
   - **Size:** R-squared about 1.6% (SPY). The papers say it held "after reasonable transaction costs" (summaries).
   - **Mechanism and counterparty:** dealers and leveraged ETFs hedging short gamma. The effect is strong when dealers are net short gamma and absent when they are long, and it partly reverses over the next days.
   - **Replications:** 12 of 16 markets (Li, Sakkas and Urquhart 2022); Bitcoin (Shen, Urquhart and Wang 2022). A Chinese commodity futures study finds costs kill it. No evidence on decay since 2020.
   - **Closest closed item:** BASIS1, perp versus binary and FUND1 are about the gap between instruments or funding. This uses one instrument's own path and the clock.
   - **Prior:** moderate. It is the best documented item on this page and names a counterparty, but the edge per trade is small.
2. **Overnight drift in equity index futures.**
   - **Source:** Cliff, Cooper and Gulen 2008; Kelly and Clark 2011; Boyarchenko, Larsen and Whelan, NY Fed SR917.
   - **Size:** ES futures 1998 to 2018 earned about 3.1% a year overnight against 1.4% intraday (secondary summary). That is about 1 basis point a night.
   - **Prior:** low. Funding plus spread on a perp very likely exceeds 1 basis point a night.
- **Dropped:** funding-rate mean reversion. The evidence is exchange blogs and one 2019 arXiv paper, all dated and weak, and it is too close to FUND1.

## 3. The in-game recorder: NBA, NHL, NFL moneyline, two spreads and two totals at about 20 seconds

1. **Disagreement between one game's markets at one moment.**
   - **Source:** Brown, Economic Journal 2013 (verified, https://ueaeprints.uea.ac.uk/id/eprint/44399/1/ecoj12057.pdf), Wimbledon on Betfair. In play, the match winner and set score markets disagree, mostly because the less-watched market is updated less often. The winner market supplies at least 82% of price discovery.
   - **The disagreement grows when another match is played at the same time.** Our log holds how many games are live, which stands in for that distraction effect.
   - **Size:** at 2% commission a riskless lock appears "less often than simple mispricings". No cents figure.
   - **Closest closed items:** lock and parity scans, SPORTCONS1 (no lock found), in-game lag (closed). This is not a lock (one leg, held) and not a lag (the same snapshot). But it sits next to both, and the declined lock row should be checked before anyone writes it.
   - **Prior:** low. Kalshi's taker fee is about 1.75c a leg at 50c.
2. **Direction of a jump against the pre-game price** (follow a move toward the pre-game favourite, fade a move toward the underdog).
   - **Source:** Choi and Hui, JEBO 2014 (2,017 Betfair matches, abstract), and Angelini, De Angelis and Singleton, IJF 2022 (abstract). Underreaction to expected goals and overreaction to surprising ones, worst for a late longshot goal. No size.
   - **Against it:** Angelini and De Angelis (2026), arXiv 2606.07811, on Kalshi NBA itself (verified; 1,438 games, 409,512 contract-minutes). Prices move about 0.63 for each point of model probability, and a 10 point gap predicts about 4.6 points of drift over 5 minutes. **But executable returns at the bid and ask are -0.9% to -1.2% over 5 minutes, before fees, and the benchmark needs play-by-play we do not have.**
   - **Closest closed item:** INPLAYJUMP. Honestly this is a version of it (lifecycle 7g), usable only as a split if that test is read.
   - **Prior:** very low.
- **Dropped:** Whelan 2026 (Betfair, takers backing strong favourites late profit) and Page 2012 (Yogi Berra bias) are the closed favourite-late item.
- **Nothing published** on totals underreacting to pace, garbage-time spreads, or in-play price volatility as a signal.

## 4. The combo recorder: quotes, top 5 book and trades on multi-leg markets

1. **The markup over the product of the legs grows with the number of legs.**
   - **Source:** Moshrefi (2026), arXiv 2607.14430 (verified from the text), 12,639 Kalshi cross-game moneyline combos, 2 to 11 legs, Apr 29 to May 13, 2026.
   - **Size:** the median ratio of combo price to the product of the leg prices is about 1.0 up to 5 legs, then 1.037 at 7, 1.066 at 8, 1.223 at 10 and 1.305 at 11 (about +3% a leg on a log-linear fit). Win rates run 2 to 10 points under price: a 30c combo wins about 24%, a 40c combo about 30%.
   - **Costs:** fees excluded. The NO side's realised return and fillable size are not computed.
   - **Support for the mechanism:** Whelan, "The Parlay Puzzle" (2026, verified, https://www.karlwhelan.com/Papers/Parlays.pdf). New Jersey parlay hold was 17.5% to 19.2% a year (2021 to 2025) against 3.3% to 5.0% for single bets, and parlays were 65% of sportsbook revenue. Bettors pay for lottery-like long combos.
   - **Closest closed or registered item:** the combo house side (NO on high-priced combos, paper, first read Nov 26) and the closed lock and price-consistency scans. Pricing a combo against its legs' mids is a model value, not a lock. **Honestly a sharper filter (leg count and markup) for the registered house-side paper test, not a new mechanism.** Our earlier pass found almost no resting NO asks, so fillable size is the open question.
   - **Prior:** medium-low. It is the one item here with a published size large enough to matter.
2. **Same-game (correlated-leg) combos priced as if the legs were independent.** One college football paper in the Journal of Prediction Markets (abstract only) found exploitable correlated parlays. Vendor claims of 30% to 60% errors are unverified and commercially motivated. Modern same-game pricers correct for correlation. Nothing published on Kalshi same-game combos. **Prior:** low.

## 5. The politics recorder: 30 minute quotes on 42 series closing within 30 days

1. **Reversal after a large one-day move.**
   - **Source:** Clinton and Huang (Vanderbilt, SocArXiv d5yx2, 2025): 2,500+ political markets on four venues in the last 5 weeks of 2024; daily changes "weakly correlated or negatively autocorrelated" (abstract and summary). Tsang and Yang (2026), arXiv 2603.03152: on Polymarket the 2024 debate jump largely reversed, while the assassination-attempt repricing persisted (abstract). Quantpedia (2026) on three low-information Polymarket contracts: buy-the-dip variants turned negative at 0.1% a trade (verified, 12 variants, no deflation).
   - **Size:** no published coefficient.
   - **Closest closed item:** the approval NO side (closed) and favourite-and-hold (banned). This uses the quote path, not a price band.
   - **Prior:** low. Real news persists, and a 6c politics round trip likely dominates.
2. **Compression of prices toward 50, conditioned on large trades.**
   - **Source:** Le (2026), arXiv 2602.19520 (verified). Kalshi politics slopes 1.48 to 1.83 inside a month; big trades show more compression (a slope gap of about 0.5, not robust on Polymarket).
   - **Fit to the log:** our recorder logs volume and open interest, not trade sizes, so only a volume-spike proxy is possible, and that is untested anywhere. It leans toward buying favourites, banned at 88c and up for the wheel and under the Charter outside it.
   - **Prior:** low.
- **Nothing published** on open interest or volume spikes predicting direction in political markets.

## 6. The sports and esports book-and-tape recorder (9 series, being built)

1. **Large prints predict the winner.**
   - **Source:** Brown and Yang, UK horse racing on Betfair, 9,562 races 2013 to 14 (working paper, not verified): in running, bets of above-median size were 9.3% more likely to win than smaller ones, after allowing for the favourite-longshot bias.
   - **Closest closed item:** taker order flow (FLOW1, TAPEFLOW1, RESIL1). The field here is print SIZE, not buy-minus-sell direction. Whether that is "a new data source" under the declined row is the Head's ruling, and the row should be checked first.
   - **Prior:** low to moderate on mechanism, but there is no evidence for sports or esports, and the finding is in-running horse racing.
2. **Calibration of esports map prices by price band.** Sweeney, Tuttle and Berg (2021) found a normal longshot bias on real-money CS and Dota odds; Stoyan and Dagaev (2020) found a reverse bias on a parimutuel site; a 2024 paper finds both. No exchange study. The direction contradicts itself, and on Kalshi this is a price-band calibration rule, which the cheap-side and favourite rows already cover. **Prior:** low.

## Plain summary

- The one published size that matters is the combo leg-count markup. It belongs to the registered combo house-side paper test as a filter.
- The best documented mechanism with a named counterparty is intraday momentum into the US close on the perps, at a small size.
- Everything else is low or very low, or a version of something registered.
