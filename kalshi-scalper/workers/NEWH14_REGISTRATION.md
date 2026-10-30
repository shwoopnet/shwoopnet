# NEWH14 registration (Strategy Research V2 worker NEWH14, 2026-10-30, research only)

Written and pushed BEFORE any NEWH14 structure was joined to a fill quote or to any outcome. Code `src/scalper/newh14.py`
(committed with this file); result `workers/NEWH14_RESULT.md`. The two approval-free cards named by `workers/CENSUS_2026-10-30.md`
item 3: (a) NOVIEW, volatility structures across the strikes of the hourly Bitcoin ladder KXBTCD; (b) the GOLD2 card, the daily gold
ladder KXGOLDD against a GVZ-implied distribution. Times are UTC in the code and US Central (CDT, UTC-5, the whole sample) in words.
Nothing here touches `functions/`, `index.html` or anything live.

## (b) GOLD2 first: the count, and NOT_RUNNABLE before any try

The brief: count the KXGOLDD events on file first (the record says both 108 and about 60); under 100 usable daily closes in discovery
plus validation, write NOT_RUNNABLE and spend no try. Counted by `python -m scalper.newh14 goldd` (close times only; no quote, no
result, no GVZ read):

- **Local files:** `ladl1.sqlite` 38 distinct KXGOLDD closes (Aug 24 to Oct 28, 2026; two quote looks per strike at 10 and 6
  minutes before the close, no candles, nothing at 14:00 ET); `flb1.sqlite` and `theta1.sqlite` 8 closes each (hourly candles for
  a few strikes). No local file holds 108 KXGOLDD events, and none holds any KXGOLDD event before 2026-08-24.
- **Kalshi's public market list** (`/markets?series_ticker=KXGOLDD&status=settled`, two pages): 1,570 settled markets, **39 distinct
  close times on 39 days, first 2026-08-24, last 2026-10-29**. By the standard windows: discovery 15 days, validation 16, holdout 8;
  **discovery plus validation 31 against the 100 needed.**
- So the record's "108 daily events from 2026-04 to 2026-09" (the GOLD2 card, 2026-10-28) is not KXGOLDD as Kalshi lists it today;
  the series' public history begins 2026-08-24. "About 60" (NEWH4, NEWH10) was an overestimate; the number is 39.
- **Verdict: NOT_RUNNABLE** (31 usable daily closes in discovery plus validation, under 100; one independent close a day cannot reach
  the trade minimum without pooling correlated strikes). 0 tries. GVZ was not read, no quote was joined to a model, nothing was scored.
  A forward recorder (`ladder.csv` on `quote-data` already polls KXGOLDD near its 21:00 UTC close) is the only path, and at about 22
  closes a month it would reach 100 closes around March 2027.

## (a) NOVIEW: the question

An hourly "above K" ladder is a distribution. Two strikes of one event make a structure with NO directional view: buy both WINGS
(YES at the upper strike K_hi plus NO at the lower strike K_lo: pays 1 if the settlement lands outside the range, 0 inside; a
strangle) or buy the MIDDLE (YES at K_lo plus NO at K_hi: pays 2 inside, 1 outside; a condor). Whether either pays depends only on
how far Bitcoin moves in the time left, not on which way. The ladder's makers set the width; the question is whether their
width is systematically wrong against the realised one hour move, either conditionally (a slow volatility input lags realised
volatility) or unconditionally (a variance risk premium: wings rich on average, as on every listed options market).

## Ledger check (what this is NOT)

- Not L1, not a favourite held in the last 6 minutes of a 15 minute market, not the cheap side late, not a round trip. Every entry
  is 45 to 30 minutes before an HOURLY close, both legs held to settlement.
- **LAD1** (6 tries, FALSIFIED): a per-strike fair value from spot and DVOL or 60 minute realised volatility, ONE leg per strike, the
  model's largest disagreements in the wings. NEWH14 trades a two-leg structure symmetric in the MARKET's own prices (the 25c and 75c
  strikes), so a single strike's shape error cancels to first order and what is left is the width.
- **NEWH4 NARROW** (NOT_ENOUGH_DATA, 27 trades): the ladder's width against its own centre's path, one cheap leg. **TAIL** (FALSIFIED):
  2c to 6c longshots, one leg. **KINK** (FALSIFIED): one strike off the curve. **NEWH10** (FALSIFIED / NOT_ENOUGH_DATA): width by the
  clock, one 30c wing or its 70c mirror. **IV1** (FALSIFIED): the 15 minute market's own mid beats a DVOL model. None traded two
  strikes of one event as one bet, and none priced the structure against realised spot moves.
- **A disclosure on the CONDOR arms:** each condor leg is a side priced about 60c to 85c and held. That is outside L1's band, 45
  minutes before an hourly close, and motivated by width, not by "favourites win"; the lead should strike them if they read the
  owner's 2026-10-28 instruction as covering any side above 50c. NEWH10's WKNDWIDE carried the same disclosure. STRANGLE-RV is not
  affected (both legs 15c to 40c).
- **The mirror of TAIL** (buy the 94c to 98c side) is not what CONDOR is: CONDOR's legs are the 60c to 85c sides of the two strikes
  that bracket the money, chosen symmetric in price, and the structure's result is the width, not a favourite's calibration.
- **Gold ladders (the brief's "where quoted"):** NOT_RUNNABLE for this shape, 0 tries. KXGOLDH candles exist only from 900 s before
  each close (no 45 to 30 minute entry exists), those candles are mostly zero volume (NEWH4, NEWH10), and there is no public gold spot
  series at minute resolution for the sample (GC=F keeps 30 days; Pyth needs a key: GOLDPYTH-H). KXGOLDD and KXGOLDW: see (b).

## What was looked at before this was written (disclosure)

The ledger sections and files named in the brief (RULES, README cards NOVIEW and GOLD2, LAD1, KINK, TAIL, NEWH10, NEWH13, GLADH,
CENSUS, NEWH10's registration and code, `studies/NOVIEW_MECHANISMS_2026-10-28.md`); table layouts, close counts, strike grid ($100)
and which minutes have candles (3,300 s to 60 s before each hourly close) for `conf2_lad` and `lad2`; per close at the 45 minute
candle, the NUMBER of strikes quoted two-sided within 6c with a mid of 5c to 95c (median 7, minimum 1), no mid or result joined to
anything; spot coverage in `newh7.sqlite`. `python -m scalper.newh14 counts` (events per stage by close time only):

| | discovery | validation | holdout |
|---|---|---|---|
| KXBTCD hourly events (conf2_lad then lad2, first file wins per close) | 656 | 631 | 257 |

Spot: Coinbase BTC-USD 1 minute closes (public, `newh7.sqlite`, 2026-08-03 to 2026-10-28 00:00 UTC). Holdout closes after
2026-10-28 00:00 UTC have no model and are counted as "no spot" for the two model arms (the holdout is read only after two passes).

## Common to every rule (fixed now)

- **Windows by close time (UTC):** DISCOVERY 2026-08-06 to 2026-09-21 (the file starts 2026-08-24); VALIDATION 2026-09-21 to
  2026-10-18; HOLDOUT 2026-10-18 to 2026-10-30 (frozen: read once, ONLY for a rule that passed discovery and validation, after that
  result is committed and pushed).
- **Universe:** every settled KXBTCD hourly event in the local files, chosen by close time only (strike sets were fixed by the fetch
  rules from quotes 55 to 52 minutes before the close, before any signal time used here).
- **The wings (one structure per event).** At a signal candle, among strikes with 0 < bid < ask < 1 and ask minus bid at most 6c:
  K_hi is the strike whose YES mid is nearest 0.25 (mid inside 0.15 to 0.40); K_lo is the strike whose YES mid is nearest 0.75
  (inside 0.60 to 0.85); K_lo must be below K_hi, else "no wings". Chosen from the market's own prices, so the structure is symmetric
  in the market's eyes and carries no directional view.
- **STRANGLE** = YES at K_hi plus NO at K_lo; pays 1 if the settlement is above K_hi or at or below K_lo, 0 otherwise.
  **CONDOR** = YES at K_lo plus NO at K_hi; pays 2 if the settlement is inside (K_lo, K_hi], 1 otherwise.
- **Signal candles:** the model arms scan the candles ending 2,700 s down to 1,800 s before the close (45 to 30 minutes left), one
  minute steps, FIRST signal wins; the unconditional arms look once, at the candle ending 2,700 s before the close.
- **Fill:** both legs at that side's ask on the candle ending 60 s AFTER the signal candle (the NEXT candle), never the signal
  candle's quote; if either leg is unquoted or wider than 6c at the fill candle, "no fill", counted. Held to settlement; nothing is sold.
  **The one-minute ladder candles carry no sizes, so a two-leg fill of 10 contracts a leg is modelled, not observed**; the real
  structure would also need both legs to fill in the same minute.
- **Pricing model (the model arms):** S = the Coinbase BTC-USD 1 minute close of the last bar ended at or before the signal candle
  (none within 2 minutes: "no spot"); sd1 = the standard deviation of the trailing 1,440 one minute log returns (at least 1,200);
  sigma for the time left T (seconds from the FILL candle's end to the close, so lead minus 60 s) = sd1 x sqrt(T/60 minus 2/3)
  (the settlement is a 60 s average); P_model(inside) = Phi(ln(K_hi/S)/sigma) minus Phi(ln(K_lo/S)/sigma), zero drift.
  Fair value of a STRANGLE set = 1 minus P_model(inside); of a CONDOR set = 1 plus P_model(inside).
- **Edge (the model arms):** fair value minus the set's price at the signal candle (sum of the two asks) at least 5c per set.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order PER LEG. Headline C = 10 a leg; C = 1 and fees x1.2 at C = 10
  reported. Net per set = C x (payoff minus the sum of the legs) minus the two fees.
- **Zero volume both ways:** PF with all trades and without trades whose signal or fill candle had volume 0 on either strike.
- **Bar (each rule):** PF at C = 10 at least 1.5 in EACH of the three windows, net positive at fees x1.2 in each, at least 100 / 50 /
  30 trades (discovery / validation / holdout), a named counterparty, and pooled day-clustered z at least the deflated bar.
  **N:** running count after GEN11 about 728,623, plus 5 here = **about 728,628**; one-sided Bonferroni z bar at 0.05 **5.27**.

## H1 STRANGLE-RV (1 try): buy the wings when the ladder is narrower than realised volatility

- **Rule:** as above, STRANGLE, model arm, edge at least 5c.
- **Counterparty:** ladder makers whose width comes from a slow input (a 30 day implied index, a multi-hour realised figure) in hours
  where the last day's realised volatility runs above it, and whoever sells the wings to them at that width (sellers of "the range":
  retail condor-like positions, and the longshot sellers TAIL's result rewards on average); they lose when the hour moves more than
  the slow input allows.
- **Honest alternative:** LAD1 found a trailing realised model no better than the book strike by strike; the makers read the same
  public spot; and a 24 hour realised window is itself a slow input, so the model's "edges" may be its own lag.
- **Prediction:** FALSIFIED; discovery PF 0.80 to 1.10 at C = 10; the structure settles outside about as often as its price says.

## H2 CONDOR-RV (1 try): buy the middle when the ladder is wider than realised volatility

- **Rule:** CONDOR, model arm, edge at least 5c.
- **Counterparty:** buyers of the wings paying for a move that the last day's realised volatility does not support (lottery buyers,
  the counterparty TAIL already measured at 2c to 6c, here at the 25c wings), and makers who widened after a volatility spike and are
  slow to narrow.
- **Honest alternative:** as H1, and the two legs are 60c to 85c sides, so two fees of about 1.3c to 1.6c each a contract plus two
  spreads cost about 4c to 5c a set against a premium that TAIL puts at about one point at the far wings.
- **Prediction:** FALSIFIED; discovery PF 0.90 to 1.20.

## H3 CONDOR-ALWAYS (1 try): the variance risk premium, unconditional

- **Rule:** CONDOR, no model, one look at the 45 minute candle, every event.
- **Counterparty:** the wing buyer, every hour: if the ladder's makers hedge or price off listed options (where implied exceeds
  realised on average) or simply charge for the risk of a jump, the 25c wings are rich on average and the middle is cheap, and the
  structure collects the premium without a view. The far-wing evidence (TAIL: 2c to 6c sides win 2.9% to 3.3% against 4.2% paid) says
  the sign is this way; the size at 25c is the question.
- **Honest alternative:** the bias measured at the far wings is about one point of probability and the two 75c legs pay about
  2.9c of fees and about 2c of spread a set at C = 10; a one point premium cannot cover 5c of cost.
- **Prediction:** FALSIFIED; discovery PF 0.95 to 1.15; inside share within 2 points of the market's own P(inside).

## Information looks (counted in N, never a rule, never screened)

- **I1 STRANGLE-ALWAYS:** the mirror of H3 (buy the wings every hour at 45 minutes). Printed so the premium's sign is read from both
  sides; its PF is about the inverse of H3's before costs and is not a rule.
- **I2 calibration:** at the 45 minute candle, the market's P(inside) = mid(K_lo) minus mid(K_hi) in four buckets against the settled
  inside frequency, with the realised-vol model's P(inside) beside it, discovery and validation events. It says whether the ladder's
  width is right on average and whether the model disagrees with it in a consistent direction.

## Declined, no try spent

- **Three-leg or four-leg structures (butterflies, ratio spreads):** every extra leg adds a fee and a spread; a two-leg structure is
  the cheapest no-view bet the ladder allows, and if it fails on cost the wider ones fail further.
- **A DVOL-implied model (LAD1's sigma source):** LAD1 ran it per strike at 45, 30 and 15 minutes (FALSIFIED); the realised model is
  the one that read +0.10c there, so it is the one tried as a structure.
- **Hedged structures against the perpetual or Deribit (CENSUS item 5):** the record holds no mispricing a hedge would lock (IV1,
  LAD1, XM1, BLADX, NEWH13), so the hedge has nothing to carry; not registered.
- **The gold ladders:** see the ledger check (NOT_RUNNABLE, 0 tries).

## Kill criteria (each try, no parameter changes after any score)

- Discovery: fewer than 100 trades NOT_ENOUGH_DATA (validation printed for the record). PF at C = 10 under 1.5, or net at fees x1.2
  at or below 0: FALSIFIED.
- Validation (after a discovery pass): fewer than 50 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
- Holdout (after both passes, read once): fewer than 30 trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0: FALSIFIED.
  All PF gates met but pooled day z under the deflated bar: NOT_ENOUGH_DATA. All gates met: NOT_YET_FALSIFIED (forward registration
  only; the forward ledger has no KXBTCD candle source, so that registration would name the book recorder's `book/` files).

## Count

N tried: **3** (STRANGLE-RV, CONDOR-RV, CONDOR-ALWAYS) + 2 information looks (I1, I2) = **5**. GOLD2: 0 (NOT_RUNNABLE on the count).
Running count about 728,623 (after GEN11) + 5 = **about 728,628**. Deflated z bar 5.27.
