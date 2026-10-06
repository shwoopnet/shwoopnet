# kalshi-scalper

Research and risk tooling for Kalshi 15 minute BTC (`KXBTC15M`) and gold
(`KXGOLD15M`) markets. Standalone on purpose: it is not part of
`shwoop-server`, which places real Alpaca orders.

## Status

Nothing here places an order, and nothing here has to stay running: this folder
is offline research over downloaded history. The bot that watches the markets
runs on the server. Order placement does not exist yet and is added only after
the bar below is cleared in paper trading.

## Build order

1. `backfill.py`  fetch Kalshi's own 1 minute history for settled markets.
2. `analyze.py`, `calibration.py`, `scalps.py`, `situations.py`  measure it.
3. Strategy       only if the measurement shows room. Declares counterparty first.
4. Paper bot      runs on the server (see below), not from this folder.
5. Live, tiny     demo env, then smallest real size, behind hard limits.

## Bar to clear before any real money (written before any result exists)

- At least 300 paper trades and 5 separate days.
- Positive net expectancy per trade AFTER fees, with fills priced at the
  ask going in and the bid going out, never the mid.
- Net profit still positive when fees are assumed 20% higher than modelled.
- Predicted probabilities calibrated (60% calls win about 60%).
- Fewer than N strategy variants tried, N recorded here as we go, because
  best-of-many crosses any bar by luck.

Strategy variants tried so far: 2 (see Verdicts). Cuts examined by the decision rule: 18, plus 3 entry times for H1.

## Facts measured, not assumed (Oct 2026)

- Market resolves on a 60 second average of CF Benchmarks index at close vs
  at open, not the last tick.
- Quotes are dollar strings; ticks are 0.1c below 10c and above 90c, 1c between.
- Fee type is `quadratic`: dearest at 50c, cheap near the extremes. A scalp
  that exits early pays it on both legs.
- Fee rate (0.07) in `fees.py` is from memory. Verify against real fills.

## Decision rule for scalping research (written 2026-10-02, before more data)

Set down before the result so it cannot be argued into shape afterward. The
thresholds live in `src/scalper/analyze.py` (`RULE_*`) and `python -m
scalper.analyze` applies them and prints the verdict. They are not to be
changed after a verdict is seen. If one is changed, the earlier verdict stands
and the new rule is a new trial, counted in "Strategy variants tried".

**What is measured.** Over a 60 second hold, the share of direction calls that
must be right to break even ("needs"), from the real spread and fees, in 9 cuts
per series (5 price levels, 4 time-left bands), so 18 buckets in all. The
horizon is fixed at 60s. Other horizons are not used to rescue a result.

**Verdicts.**

| Verdict | Condition | What follows |
|---|---|---|
| `NOT_ENOUGH_DATA` | under 72 hours of recorded market time in EACH series (about 3 days of continuous recording; gold takes longer if its market is not open around the clock) | Keep recording. No conclusion either way. |
| `FALSIFIED` | no bucket beats the bar (below) | Stop. Do not build a directional scalping strategy. |
| `NOT_YET_FALSIFIED` | some bucket beats the bar | Permission to WRITE DOWN a hypothesis only: who loses money and why, a numeric prediction, a kill criterion. Then test it on data recorded after this verdict. Not evidence of an edge. |

**The bar.** A bucket qualifies only if its break-even hit rate is **under 60%
in both halves** of the recording period (split by time), with at least 500
samples overall and at least 250 in each half. Requiring both halves is the
guard against the obvious failure: with 18 buckets one will look good by luck.

**Why 60%.** A coin flip is 50%, and calling a 60 second move correctly 6 times
in 10, repeatedly, is already ambitious. Anything needing more than that is not
a plan. The first reading (5.2 hours) needed 64% to 99% everywhere, with the
cheapest cost buckets worst, because the price barely moves where fees are low.

**There is no "trade it" verdict.** The best outcome is `NOT_YET_FALSIFIED`.
The analyzer's code is tested to contain no verdict word that means go live.
Real money needs a separate, later bar (see "Bar to clear before any real
money" above), and paper trading on unseen data first.

**Known limits of the measurement.** "Needs" uses average cost and average
move, assuming symmetric moves, so a strategy that trades only selected moments
could beat it, and this rule cannot see that. Samples overlap (a window starts
every 2s), so row counts overstate independent trades. Part of the late-market
move is the price resolving toward 0 or 100, which is not a signal anyone can
call in advance. A single week also may not cover weekends or news days.

## Measurement fixes (logged because the rule above was already in force)

No verdict other than `NOT_ENOUGH_DATA` had been issued under either of these.
Both make the measurement stricter, and the numbers quoted before them are
superseded.

- **2026-10-05, windows across gaps.** A "60 second hold" was scored as the
  first snapshot at least 60s later, however late. After a recorder outage that
  paired an entry with a snapshot many minutes on, so the move was larger than
  a 60s move and the "needs" figure looked better than it was. Windows whose
  exit lands more than 6s late are now dropped, and the count is printed.
- **2026-10-05, hours of market time.** First-to-last snapshot credited a market
  for time the recorder was off in the middle of it. Only the intervals actually
  recorded now count. Earlier, hours were also summed across both series.

## Candle backfill: what is fixed before the first run (2026-10-05)

Kalshi serves its own 1 minute history, with the bid and ask, for settled
markets (checked to reach 45 days back, not 120). `python -m scalper.backfill`
pulls it and `python -m scalper.analyze --candles` applies the decision rule to
it. Written before any candle result was seen:

- **Window:** the last 30 days, both series. First half and second half of the
  window (by time) are the two halves the rule requires.
- **Quote:** each minute's closing bid and ask. A hold is entry at one close and
  exit at the close exactly 60s later. The rule uses the 60s hold only. 120s is
  printed for information and plays no part in the verdict.
- **Usable quote:** bid at least 0.1c, ask at most 99.9c, ask not below bid, and
  a spread of at most 10c, at BOTH ends of the hold. A freshly opened market
  shows an empty book (bid 0.1c, ask $1.00) that nothing can be traded against.
  Dropped windows are counted and printed, never repaired.
- **Everything else is unchanged:** the 18 buckets, the 60% bar, both halves,
  500 samples overall and 250 per half, 72 hours of market time per series.
- **This run counts.** Whatever verdict it gives is the verdict. Changing the
  window, the quote filter or any threshold after seeing it voids it, the
  earlier one stands, and the change is a new trial.

**What this can and cannot see.** One quote per minute, so 10s and 30s holds do
not exist here (they were already impossible: the move was below the cost). A
closing quote can be stale in a thin minute. The data is whatever Kalshi serves
now and could be revised. It cannot see a strategy that trades selected moments.

## Verdicts

**2026-10-05: 60 second directional scalping on Kalshi 15 minute Bitcoin and gold: `FALSIFIED`.**
First and only run of the candle source, under the rule and filters fixed before
it (see above). No threshold, window or filter was changed after seeing it.

- 4,871 markets, 30 days, 712.5 market hours (Bitcoin) and 505.2 (gold), against
  the 72 hours the rule needs. 11,631 windows dropped for an unusable quote.
- Share of direction calls that must be right just to break even, 60s hold:
  **76% Bitcoin, 78% gold**. 120s hold (information only): 68% and 69%.
- Cheapest buckets with enough samples: Bitcoin 2 to 5 minutes left at 67%, gold
  2 to 5 minutes left at 71%. The bar was 60%. By price level nothing was below
  75% except the extremes, which were worse (84% to "never"): fees are lowest
  there but the price barely moves.
- The late-market bucket that looked best in the live recorder's snapshots (under
  2 minutes left, about 64%) cannot be measured here: the exit quote is usually a
  resolved book with nothing to trade against, so those windows are dropped by the
  quote filter (Bitcoin has too few left to report, gold has 73). It is not an
  opportunity this data supports.
- The two sources agree: the snapshot data (about 12 market hours per series, with
  recording gaps) also put the 60s break-even at 75% to 76%.

**What this does and does not say.** It says a trade that buys at the ask and
sells at the bid 60 seconds later needs about three direction calls in four to
break even, which is out of reach, so no directional scalping strategy gets built
on it. It does not test holding to settlement (one fee and half the spread, a
different cost structure), selecting only some moments, or anything faster than
one minute. Those are new hypotheses and each must declare its counterparty, a
numeric prediction and a kill criterion before it is run.

Cuts examined: 18.

**2026-10-05: H1, favourites underpriced when held to settlement: `FALSIFIED`.**
One run of `python -m scalper.calibration` under the rule fixed before it (commit
e4f4d87). 4,871 markets, 30 days, no threshold or band changed after seeing it.

| Entry | n | Mean net per contract | z (day clustered) | 1st half | 2nd half | Fees x1.2 | Detectable |
|---|---|---|---|---|---|---|---|
| 10 min before close | 764 | +1.13c | 1.34 | +0.88c | +1.33c | +1.00c | 2.35c |
| 5 min | 1,857 | +0.53c | 0.90 | +0.30c | +0.79c | +0.42c | 1.65c |
| 2 min | 1,320 | -2.73c | -4.20 | -3.37c | -2.03c | -2.83c | 1.82c |

- No entry time clears the bar (z of 2.2 or more, both halves, positive after
  stressed fees). The sign changes with the entry time (+1.1c, +0.5c, -2.7c), the
  pattern of noise around zero.
- The test could see an edge of about 1.7c to 2.4c, better than the 2.5c predicted.
  So: no favourite edge that large, at any of the three entry times.
- The 2 minute result is significantly NEGATIVE (z of -4.2, negative in both
  halves): favourites bought two minutes before close lost 2.7c a contract. That is
  the opposite of H1. It is a pattern found in the data it was measured on, so
  acting on it needs a new hypothesis stated first and tested on data this run has
  not seen (the history reaches at least 45 days, so days 31 to 45 back are unseen).
- The descriptive calibration table is not evidence for anything. It is 15 cells
  with no verdict attached, and some cells look dramatic at small n (for example
  90c to 100c at 10 minutes: priced 93.0%, won 98.1%, n of 160).

Strategy variants tried so far: 2 (the 60s scalp and H1). Cuts examined: 18, plus
3 entry times for H1.

**2026-10-06: does Kalshi lag spot Bitcoin? No lag visible at one minute (exploratory, no verdict).**
One run of `python -m scalper.leadlag` under the definitions fixed before it (commit
b44a19a). 30 days, 15,101 Bitcoin market minutes with a mid between 30c and 70c and at
least 5 minutes left. Nothing was changed after seeing it. Gold is not covered: there is
no free gold spot series here.

- **The clocks line up.** The market strike and Coinbase's price at the open differ by
  0.012% on the median market (the bar was 0.1%), over 2,850 markets.
- **Kalshi tracks spot inside the same minute.** The contemporaneous coefficient is
  large and stable (z of 23.9; 15.2 and 18.1 in the two halves). A 0.1% Bitcoin move in
  a minute moves the mid by about 22c, which is what a 50c binary 15 minutes from
  settlement should do.
- **There is no lag to trade.** One minute of lag is -2.6% of the contemporaneous effect
  (z of -2.7, small, and the wrong sign for a lag: it looks like a little bid and ask
  bounce). The lead term, the clock check, is 1.2 z, noise. After a top-decile spot
  move, Kalshi's next-minute move in that direction is +0.09c, against a 4c round trip.
- **What it says.** The professional quoters on these markets price the live index
  within a minute, so a bot that looks at prices once a minute has no information
  advantage over them. Beating them needs sub-second data and execution, which is a
  different business from this one.
- **What it does not say.** Not tested: gold, anything faster than one minute, or
  whether resting orders earn the spread (candles cannot show fills).

## Hypothesis H1: favourites are underpriced, held to settlement (fixed 2026-10-05, before any calibration data was looked at)

The scalping verdict above says nothing about holding to settlement, which costs
one fee and half the spread instead of two fees and a full spread. H1 is the
simplest hypothesis with an economic reason behind it. Code and thresholds are in
`src/scalper/calibration.py`; run `python -m scalper.calibration`.

- **Claim.** Buying the favourite side at 85c to 97c (YES at its ask, or NO at 1
  minus the YES bid) and holding it to settlement earns more than it costs.
- **Counterparty.** Whoever sells us the favourite is buying the cheap longshot
  (3c to 15c) as a lottery ticket. If longshots are overpaid for, favourites are
  underpriced by the same amount.
- **Prediction.** Mean net profit of at least +1.0c per contract at one or more of
  three entry times (10, 5 and 2 minutes before close), after entering at the ask
  and paying fees (7% rate, unrounded, per contract).
- **Unit.** One entry per market per entry time. A minute-by-minute version would
  count one outcome dozens of times.
- **Kill criteria.** FALSIFIED unless, for at least one entry time, ALL hold:
  n of at least 300 markets; mean net profit positive with a day-clustered z of
  at least 2.2 (Bonferroni for three entry times; clustered by UTC day because
  adjacent markets share a regime); positive in BOTH halves of the 30 days; and
  still positive with fees 20% higher.
- **Best outcome is `NOT_YET_FALSIFIED`.** That is permission to test on data
  recorded after the verdict, never evidence of an edge. No verdict means "trade".
- **Prior: low.** These are liquid markets priced off live indices by
  professional makers. I expect FALSIFIED.
- **Power.** With about a thousand markets per entry time only an edge of roughly
  2.5c or more is visible (the run prints the figure as "detectable"). FALSIFIED
  here means "no edge that large", not "priced perfectly". A smaller edge is also
  barely worth the risk.
- **Descriptive table.** The calibration table printed after the verdict (did YES
  win as often as its price said, by price band and entry time) affects nothing.
  Anything interesting in it is a new hypothesis and needs data it was not fitted
  on. It must not be used to pick a cell after the fact.
- **No change after seeing it.** Any change to a band, entry time, threshold or
  fee after the first run voids that run, the earlier verdict stands, and the
  change is a new trial.

## Exploratory: path situations (definitions fixed 2026-10-05, before the first run)

Question asked: when a side reaches 70% in the first 2 or the last 2 minutes of a
market, how often does it flip, and how often does it close the same way?
`python -m scalper.situations`. **Exploratory: no verdict, no kill criterion, and
nothing in it licenses a trade.**

- **The baseline is the price, not 50%.** A side priced at 70% flips about 30% of
  the time if the market is fair. Each row prints the same-direction rate next to
  the price that side traded at when it triggered, and the gap between them.
- **Definitions.** Probability is the mid of a minute's closing bid and ask. A side
  hits T when its mid is at least T (NO when the YES mid is at most 1 - T). First
  window: the closes 1 and 2 minutes after open. Last window: the closes 2 and 1
  minutes before close. One event per market per window, at the first checkpoint
  that qualifies. Usable quotes only (real two sided book, spread 10c or less).
  Tradable reading: buy that side at its ask at the trigger, hold to settlement,
  7% fee unrounded.
- **Thresholds.** 70% is the question. 60% and 80% are printed as sensitivity.
  Cuts examined: 3 thresholds x 2 windows x 3 groupings.
- **What follows a gap.** A gap that looks real is a hypothesis. It is written down
  first (counterparty, number, kill criterion) and tested on days 31 to 45 back,
  which this has not seen, before anyone trades it. Reading it off this table and
  acting on it is the thing this process exists to prevent.

**Exploratory result, 2026-10-05 (30 days, 4,871 markets; no verdict).** A side
reaching 70%:

| Window | Events | Same direction | Flipped | Priced at trigger | Gap | Buy at ask, hold, net |
|---|---|---|---|---|---|---|
| First 2 min | 1,123 | 74.8% | 25.2% | 75.4% | -0.6 pts (95% interval for same: 72.2% to 77.3%) | -2.41c a contract |
| Last 2 min | 4,580 | 91.9% | 8.1% | 92.9% | -1.1 pts | -1.73c a contract |

- **First 2 minutes:** it kept going about three times in four, which is what the
  price said. The gap is inside the noise. Buying either side costs about the
  spread and fees and nothing else.
- **Last 2 minutes:** flips are rare (about 8%), but sides won slightly LESS often than the
  price said, 1.8 points less
  for Bitcoin and about 0 for gold. This is the same effect the H1 run found at its
  2 minute entry (the two overlap heavily in the same markets), so it is the same
  evidence counted twice, not a second confirmation.
- **Thresholds of 60% and 80% show the same shapes**, so it is not an accident of 70%.
- **What this does not show.** It uses only Kalshi's own prices. Any edge would need
  information the price does not already contain, for example the live spot price
  against the strike with the 60 second averaging rule. That is a different
  hypothesis and needs data this study does not have.

**2026-10-05: H2, buy at 40c or 50c and sell at 80c: `FALSIFIED`.** One run of
`python -m scalper.scalps` under the rule fixed before it (commit ed8e869). 4,871
markets, 30 days. No threshold, band or fee was changed after seeing it.

| Band | Entries | Mean net per contract | z | 1st half | 2nd half | Fees x1.2 |
|---|---|---|---|---|---|---|
| 40c to 80c | 3,162 | -7.96c | -13.1 | -7.71c | -8.22c | -8.39c |
| 50c to 80c | 2,593 | -7.94c | -11.3 | -7.68c | -8.21c | -8.41c |

- **The "50/50" question.** At 40c to 80c the target was reached 42.4% of the time,
  and 52.6% was needed to break even (average win +37.4c, average loss -41.4c). At
  50c to 80c it was reached 55.1% against 65.2% needed (+27.4c against -51.4c). A
  fair market gives 50% and 62.5% as touch rates, and the payoff is lopsided to
  match, so the expected profit is zero before costs at any target.
- **It lost about twice its costs, in both halves and in both bands.** Costs are
  about 4c a round trip; the primary result is about -8c. Letting a touch count
  only on a minute's CLOSE misses intra-minute touches, and selling at 80c when the
  price has jumped past it leaves the overshoot behind. I have not separated those
  two effects. The optimistic fill (touch by the minute's high) is -4.9c and -4.4c,
  which is about the costs and still negative.
- **Neither a maker exit (-7.5c, -7.3c) nor a stop 20c below entry (-6.9c, -6.7c)
  rescues it.** A stop does not change the expected profit of a fair game.
- **What it does not test.** Other targets, other entry prices, entries chosen by
  any signal, or anything faster than one minute. Each is a new hypothesis.

Strategy variants tried so far: 3 (the 60s scalp, H1, H2), plus one exploratory
study with no verdict.

## Hypothesis H2: buy at 40c or 50c, sell at 80c (fixed 2026-10-05, before it was run on any data)

The owner's own idea, stated as a rule. `python -m scalper.scalps`.

- **Rule.** Buy a side at about 40c (ask 38c to 42c) or about 50c (48c to 52c), at the
  first minute close with at least 5 minutes left and a usable quote (YES tried
  first, then NO). Sell at 80c when that side's bid first closes at 80c or more on a
  LATER minute. Otherwise hold to settlement. Fee on the way in and out, 7%
  unrounded per contract. No stop. One entry per market per band.
- **Why it feels like 50/50 and why the prior is zero.** In a fair market a price at
  40c reaches 80c before 0c half the time (40 over 80), and 50c does so 62.5% of the
  time. The payoff is lopsided to match, so the expected profit is zero before costs
  at ANY target. Costs are about 4c a round trip. It can only work if prices
  continue more than a fair game. The earlier path study found no continuation.
- **Counterparty.** Whoever sells at 40c to 50c, or buys at 80c, on a view that
  prices lag a move.
- **Prediction.** Mean net profit of at least +1c a contract in at least one band.
- **Kill criteria.** FALSIFIED unless, for at least one band: n of at least 300
  markets; mean net profit positive with a day clustered z of at least 2.1
  (Bonferroni for two bands); positive in BOTH halves of the 30 days; positive with
  fees 20% higher. Best outcome `NOT_YET_FALSIFIED`, meaning permission to test on
  data not yet seen, never evidence of an edge. No verdict means "trade".
- **Simulator guard.** A test runs the exact code on a simulated FAIR game and
  requires it to lose roughly the costs. A profit there would mean the simulator
  invents an edge.
- **Printed for information only.** Touching by the minute's high, a maker exit with
  no exit fee, a stop 20c below entry, and the hit rate needed to break even.
- **Cost of this idea so far.** It is the third hypothesis tested. Strategy variants
  tried before it: 2.

## Exploratory: does Kalshi lag spot Bitcoin? (definitions fixed 2026-10-06, before the first run)

Why this question. Every test so far used only Kalshi's own prices, and the path study
said so: "any edge would need information the price does not already contain, for
example the live spot price against the strike". This asks the cheapest version of that
question, and it decides whether any information strategy is reachable for a bot that
looks at prices once a minute. **Exploratory: no verdict, no kill criterion, and nothing
in it licenses a trade.** It is not a strategy variant and does not count toward the 3.

- **Data.** Bitcoin only (`KXBTC15M`). Spot is Coinbase's public 1 minute BTC-USD
  candles. Gold has no free spot series here, so it is out of this study. Kalshi's index
  is not Coinbase's price, so spot is a proxy: a gap between them is noise this study
  cannot remove.
- **Alignment check first.** A Kalshi candle's `end_ts` is matched to the Coinbase candle
  that CLOSES at that instant. The check is the market's strike against Coinbase's price
  at the market's open: it must agree to within 0.1% on the median market. If it does
  not, the clocks are off and nothing below is read.
- **Unit and filters.** One row per market per minute. Mid = (bid + ask) / 2 of the
  minute's closing quote. Keep rows where both this and the next minute have a usable
  quote (real two sided book, spread 10c or less), the mid is between 30c and 70c (so
  the price's sensitivity to spot is roughly constant), and at least 5 minutes remain.
- **Measurement.** Regress the change in Kalshi's mid over minute t+1 on Bitcoin's
  log return in minute t+1 (contemporaneous), minute t (one minute of lag, the
  coefficient that matters), minute t-1 (two), and minute t+2 (a lead, a clock check).
  Day clustered standard errors. Fixed: no other lags, filters or splits.
- **What would justify a formal hypothesis.** Only if ALL hold: the one minute lag
  coefficient is at least 15% of the contemporaneous one, with z of at least 3, in BOTH
  halves of the 30 days; AND the expected next-minute Kalshi move after a top-decile
  spot move is larger than the 4c round trip cost. Anything less is reported as "no
  lag visible at one minute" and information strategies are crossed off for this bot,
  since beating professional quoters needs sub-minute data.
- **If it passes.** A hypothesis is written down first (counterparty, number, kill
  criterion) and tested on days 31 to 45 back, which this has not seen.
- **Prior: low.** I expect the one minute lag to be about zero: these prices are set by
  professional makers off the live index.

## Hypothesis H3: resting buy orders earn the spread that H2 pays (fixed 2026-10-06, before any trade tape was fetched)

H2 lost about twice its costs, and most of the cost is crossing the spread and paying a
fee on both legs. A resting order does not cross. This asks whether posting the bid
instead of lifting the ask turns H2's entry from a cost into an earning. Kalshi's public
trade tape (every trade with price, size, taker side and time) lets fills be simulated,
which candles could not. `python -m scalper.makers` (to be written after this commit).

- **Rule.** At the first minute close with at least 5 minutes left and a usable quote,
  if a side's BID is in the 40c band (38c to 42c) or the 50c band (48c to 52c), rest a buy
  of one contract at that bid (YES tried first, then NO), for 2 minutes, then cancel.
  If it fills, hold to settlement. No exit order, no stop. One order per market per band.
- **Fill model, conservative.** Our bid fills only when the tape prints strictly THROUGH
  our price on our side inside the window: for a YES bid at p, a trade with taker side
  "no" at a YES price below p (everything ahead of us was eaten); for a NO bid at q,
  taker side "yes" at a NO price below q. A print AT our price does not count, because
  our place in the queue is unknown. This understates fills and is stated as such.
- **Counterparty.** Whoever sells into our bid is an impatient seller paying the spread
  to leave. We collect it. The usual reason that does not simply work is adverse
  selection: a bid is filled when the price is about to fall.
- **Prediction.** Mean net profit of at least +0.5c per filled contract in at least one
  band, against H2's primary entry at the ask. The honest prior is low. I expect the
  spread earned to be about the size of the adverse selection, so a net near zero.
- **Costs.** Entry fee at Kalshi's taker formula (7% of p times 1 minus p, per contract,
  rounded up per order), even though a resting order may pay less: the schedule for these
  markets is not confirmed, and assuming a discount would flatter the result. A run with
  no entry fee is printed for information only.
- **Kill criteria.** FALSIFIED unless, for at least one band: at least 300 FILLED
  orders; mean net profit positive with a day clustered z of at least 2.1 (Bonferroni for
  two bands); positive in BOTH halves of the 30 days; positive with fees 20% higher. Fewer
  than 300 fills is NOT_ENOUGH_DATA and crosses nothing off. Best outcome is
  `NOT_YET_FALSIFIED`, meaning permission to test on days 31 to 45 back, never a trade.
- **The selection check that decides what a result means.** Always printed beside the
  verdict: the fill rate, and what the orders that did NOT fill would have earned if held
  to settlement from the same price. Crypto's maker test looked better and was selection,
  not execution, because the unfilled signals were the winners. A profit on the filled
  orders next to a strongly positive result on the missed ones is that same trap and is
  reported as such, whatever the headline says.
- **Printed for information only.** Fills counted when the tape prints AT our price
  (optimistic), a 5 minute window, and the same rule entering at the ask (H2's entry
  taken to settlement) as the comparison.
- **Cost of this idea so far.** It will be the fourth strategy variant tried. Cuts
  examined: 2 bands. The lag study was exploratory and is not counted.

## The paper bot (starts with $100, cannot place a real order)

It runs on the SERVER: a Firebase scheduled function (`functions/kalshiBot*` in
this repo), once a minute, with its state in Firestore, watched and halted from
the Bot tab of the Kalshi page. It depends on no computer being awake. Deploy
and monitoring steps are in `functions/DEPLOY.md`. There is no copy of it in this
folder: the Python version was retired so there is one implementation, not two
that can drift.

- **Strategy: H2, as plumbing.** H2 (buy near 40c or 50c, sell at 80c) was
  falsified on 30 days of history and expects to lose roughly its costs. It is
  there because it is simple and fully specified, so it exercises the whole loop
  and gives a forward check of the verdict.
- **$100 capital.** 1% a trade ($1.00), a 2 hour break at -3% (-$3), done for the
  day at -5% (-$5). Kalshi rounds each order's fee up to a cent, so the fee is a
  larger share of a small trade.
- **Kill switch:** the Halt button on the Bot tab stops new entries. It does NOT
  freeze positions already open, which keep being managed.
- **Safety rules, each with a test in `test/kalshiBotGates.test.js`:** one position
  per market from an id every process computes identically; no new entry on an
  unreadable or partly unreadable feed, an inactive exchange, no bankroll, under 5
  minutes left, a wide book or after the hard stop; never more contracts than the
  touch shows; never an exit on the entry tick.

## How real orders work on Kalshi (read from docs.kalshi.com on 2026-10-05)

Nothing below is implemented. It is what the live version will have to do.

- **Hosts.** Production `https://external-api.kalshi.com/trade-api/v2`, demo
  `https://external-api.demo.kalshi.co/trade-api/v2` ([demo environment](https://docs.kalshi.com/getting_started/demo_env)).
  Demo has separate accounts and separate API keys, mock funds, and prices that
  "may not be reflective of those in real markets". It tests the plumbing, not the strategy.
- **Authentication** ([signing guide](https://docs.kalshi.com/getting_started/quick_start_authenticated_requests)).
  Three headers: `KALSHI-ACCESS-KEY` (the key id), `KALSHI-ACCESS-TIMESTAMP`
  (milliseconds) and `KALSHI-ACCESS-SIGNATURE`: the base64 of a signature over the
  timestamp, then the HTTP method, then the path without its query string. RSA keys
  use RSA-PSS with SHA-256 and a salt length equal to the digest length. This needs
  the `cryptography` package, the first dependency outside the standard library. The
  private key lives only on the bot's machine (never in git, never pasted into chat).
- **Placing an order** ([Create Order V2](https://docs.kalshi.com/api-reference/orders/create-order-v2)).
  `POST /portfolio/events/orders` with `ticker`, `side` (`bid` buys YES, `ask` sells
  YES, which is economically buying NO at 1 minus the price), `count` and `price` as
  strings (fixed-point dollars), a required `time_in_force`
  (`fill_or_kill`, `good_till_canceled`, `immediate_or_cancel`) and a required
  `self_trade_prevention_type`. `client_order_id` is optional. The response gives
  `fill_count`, `remaining_count`, `average_fill_price` and `average_fee_paid`,
  which lets the bot check its own fee model against every real fill.
- **Rate limits** ([tiers](https://docs.kalshi.com/getting_started/rate_limits)). A new
  account gets 200 read and 100 write tokens a second, far above what the bot needs.
  A 429 carries no `Retry-After`, so the bot backs off exponentially, as the backfill does.
- **The one thing the docs do not say, now measured (demo, 2026-10-06).** The Create Order
  page does not say what happens when the same `client_order_id` is sent twice. The 15 duplicate
  orders in shwoop-server were stopped from happening again by the broker refusing a repeated id,
  so this had to be tested. On the demo exchange the second identical create returned
  **HTTP 409 `order_already_exists`** and only one order existed (`python3 -m scalper.demo dup`).
  So Kalshi protects against a duplicate the way Alpaca does, provided the id is deterministic
  (derived from the signal, never random). The recovery path must treat a 409 as "already sent",
  look the original order up, and carry on. Not yet confirmed on production, and a production
  check is part of any first real order.
- **Shards, explained and fixed (docs read and demo tested, 2026-10-06).** Kalshi runs several matching
  engines, called exchange shards. A market is assigned to a shard for life by its category: index 0 is
  the default catch-all, 1 exotics and combos, 2 crypto and commodities, 3 sports. On the demo the
  Bitcoin series trades on shard 2 and gold on shard 0. **Each shard holds its own funds**: collateral is
  checked inside the matching engine, so "programmatic traders must preallocate collateral on a given
  exchange shard before order placement" (the Kalshi app and website move it for you; the API does not).
  An order needs the shard (`exchange_index`, or auto-routing with `market_ticker`), and a cancel needs
  the same, because an order id alone cannot identify the shard. This account started with $200 on shard
  0 and $0 on shard 2, so a Bitcoin order had nothing to draw on. Two ways to fix it:
  `POST /portfolio/intra_exchange_instance_transfer` moves funds once, and
  `POST /portfolio/target_balance_allocation` (percentages that total 100) makes Kalshi rebalance
  automatically every 10 seconds, which is the right tool once trading is automated. A transfer is not
  atomic across shards (up to three steps, and a later step failing can leave funds in the primary
  account), and a transfer returned a transient `503 service_unavailable` once, then succeeded on retry.
  **Measured unit surprise:** the docs say the transfer `amount` is in cents, but on the demo 5000 moved
  $0.50 and 495000 moved $49.50, so the field is 1/10,000 of a dollar. Never reuse that unit on
  production without a tiny test first. Result: $150 on shard 0 and $50 on shard 2, and a Bitcoin demo
  order on shard 2 was created and cancelled (`python3 -m scalper.demo order`).
- **Other demo facts measured the same day.** A create returns **HTTP 201**, not 200, with
  `order_id`, `client_order_id`, `fill_count`, `remaining_count` and `ts_ms`. A cancel needs the market
  ticker and shard (`DELETE /portfolio/events/orders/{id}?market_ticker=...&exchange_index=...`).
  Markets are listed ahead of time as "initialized" and open on the quarter hour, so a call in the last
  seconds before the next quarter hour finds no open market.

**Order of work to real orders (each step gated on the one before):**

1. Create a Kalshi demo account and a demo API key. Read the demo balance (read-only).
2. Implement signing; check it by reading the demo balance and positions.
3. Place and cancel a one-contract demo order. Probe the duplicate `client_order_id` behaviour.
4. Reconcile: every minute compare the bot's own positions with Kalshi's, and halt on a mismatch.
5. Real money only after a strategy has passed its pre-registered test AND 300 paper
   trades (see "Bar to clear before any real money"), starting at the $1 a trade the
   limits allow, with a hard-coded maximum order size and the kill switch in front.

## Analyse

    ./run_tests.sh
    cd src
    python3 -m scalper.backfill      # download settled markets' minute history
    python3 -m scalper.analyze       # then calibration, scalps, situations

Data lands in `kalshi-scalper/data/` (not in git). It only reads Kalshi's public
prices: no account, key or password.
