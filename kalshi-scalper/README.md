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

**2026-10-07: H7, how far spot sits from the target vs the market's price: `FALSIFIED`.**
One run of the rule fixed in H7 above, on the half of the data that had not been looked at. Nothing changed after seeing it.

- 2,843 Bitcoin markets with a usable quote at 6 minutes left. Estimation half 1,421, test half 1,422. The rule entered
  **879** test markets and lost **2.69c** each (z of -2.06, so it is reliably negative, not just flat): -4.23c in the
  first half of the test half, -1.14c in the second, -2.89c with fees 20% higher. The bar was +0 with z of 2.1.
- Decomposition: gross -1.64c, fees -1.04c. YES entries won 36.7% at a mean price of 38.3% (548 of them), NO entries won
  34.1% at 35.9% (331). In-sample, on the half that set the buckets, the same rule lost 1.79c, so there was nothing there
  to lose out of sample either. My prediction was -1c to -3c, and it landed at -2.69c.
- **The owner's question, answered from the estimation half (how often the market finished above its target, by how far
  spot sat above it at 6 minutes left, in units of typical Bitcoin movement over those 6 minutes):**

  | z bucket | markets | finished YES | YES ask charged |
  |---|---|---|---|
  | below -2 | 81 | 4.9% | 4.5% |
  | -2 to -1 | 232 | 10.3% | 11.7% |
  | -1 to -0.5 | 219 | 26.5% | 24.9% |
  | -0.5 to 0 | 218 | 38.5% | 43.4% |
  | 0 to 0.5 | 228 | 61.4% | 65.7% |
  | 0.5 to 1 | 189 | 82.0% | 82.2% |
  | 1 to 2 | 190 | 95.3% | 91.2% |
  | above 2 | 64 | 98.4% | 96.5% |

  So spot at 1 to 2 typical moves above the target finished above it 95% of the time, and Kalshi was already charging
  about 91c for it. Across every bucket the price sits within about 4c of how often the outcome happened. The market
  prices the distance to the target about as well as these buckets can.
- **What it says.** Distance to the target is information the market already uses. The cheap-looking side the rule
  bought lost its price plus fee more often than the bucket rate suggested, which is what picking the cheapest asks inside
  a bucket does: it selects the quotes that are cheap because something else in the market (a recent move, a wide
  spread) justified them.
- **What it does not say.** One decision per market, at 6 minutes left, with one fixed margin and fixed buckets. Other
  decision times, a finer distance measure or the settlement source itself (CF Benchmarks' 60 second average, not the
  Coinbase closes used here) were not tested. Gold has no spot series here and was not tested.

**2026-10-06: H5, quoting both sides as a market maker: `FALSIFIED`.**
One run, on the sample and rules fixed before any code (see H5 above). Nothing was changed after seeing it.

- 1,219 markets (every 4th per series by close time), z of -36.9, mean **-41.3c a market**, -40.6c and
  -42.0c in the two halves, -45.6c with fees 20% higher. The bar was +1c and z of 2.1.
- Decomposition: round trips **-16.6c**, leftover inventory **-3.4c**, fees **-21.3c**. About 8 fills a
  side per market, 24% of markets ended flat.
- **The prediction (adverse selection bigger than the spread) was right, but not where I expected it.**
  The leftover was a small part. The loss is in the paired buys and sells: the quote follows the price, so
  in a trending minute it buys at the old level and sells at the new, lower one. Fills are not independent
  of direction, which is the same adverse selection arriving as a loss on completed pairs.
- Information only: with no fee at all it is still -20.0c, with fills also on a print AT our price -22.2c,
  inventory cap 1 -35.3c, cap 4 -44.1c. So the fee is about half of it, and removing it does not rescue it.
  It does not depend on the cap.
- **What it does not say.** The fee was charged at the taker formula on every fill, which a resting order
  may not pay (unconfirmed). Quotes were refreshed once a minute and one contract each side; a quoter that
  re-prices within the minute or skips quoting after a move is a different strategy and was not tested.
  Fills are the conservative strictly-through model.

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

**2026-10-06: H3, resting buy orders earn the spread H2 pays: `FALSIFIED`.** One run of
`python -m scalper.makers` under the rules fixed before it (commit 4e9f3ec, README section "Hypothesis
H3"), on the trade tape for every simulated order: 5,907 orders over the same 4,871 markets and 30
days. No rule, band, window or fee was changed after seeing it.

| Band | Orders | Filled | Fill rate | Net on filled | z | 1st half | 2nd half | Fees x1.2 | Missed would have earned |
|---|---|---|---|---|---|---|---|---|---|
| 40c | 3,317 | 3,024 | 91.2% | -4.34c | -5.20 | -3.97c | -4.70c | -4.68c | +17.90c |
| 50c | 2,590 | 2,349 | 90.7% | -3.83c | -3.39 | -5.21c | -2.35c | -4.18c | +16.67c |

- **The selection check, as pre-registered, tells the story.** Resting at the bid did save the spread:
  taking the ask on the same signals earns -3.5c and -3.0c, against -2.4c and -1.9c for resting
  (all orders, filled or not). But the orders that FILLED lost -4.3c and -3.8c, while the roughly 9% that
  did not fill would have earned +17.9c and +16.7c. A bid fills when the price falls through it and
  is left behind when the price rises, which is adverse selection: the fills are the losers and the
  winners get away. It is the same trap crypto's maker test fell into, now measured here.
- **Not rescued by any generous reading.** Counting a print AT our price as a fill gives -2.6c and
  -2.3c; a 5 minute window -4.2c and -3.8c; no entry fee at all -2.7c and -2.1c. Every variant loses.
  The fill model understates fills by design, but the optimistic count is still negative.
- **What it says.** The spread is real money but smaller than the damage from being filled only when
  the price is about to fall. Cost is not the only barrier: the entry itself carries no edge.
- **What it does not say.** One contract orders on a 2 minute window at the first qualifying minute.
  Placing a resting ASK (selling into strength) or quoting both sides as a market maker is a different
  strategy with its own inventory risk and was not tested.

**2026-10-06: H4, buy at 30c and sell at 80c: `FALSIFIED`.** One run of `python -m scalper.bandscan`
under the rule fixed before it (commit 68192ec). The same 4,871 markets and 30 days as H2. No
threshold, band or fee was changed after seeing it.

| Band | Entries | Mean net per contract | z | 1st half | 2nd half | Fees x1.2 |
|---|---|---|---|---|---|---|
| 30c to 80c | 3,112 | -6.36c | -10.15 | -6.31c | -6.42c | -6.73c |

- **It lost about 6.4c a contract, in both halves.** The test could see an edge of about 1.8c, so
  there is no 30c edge anywhere near that size. 31.9% of trades reached 80c (a fair game gives 37.5%
  from 30c; as in H2, a touch counted only on a minute's CLOSE misses intra-minute touches), 68.0%
  settled as losses. Average win +47.3c, average loss -31.6c, so break-even needed 40.0% winners and
  got 32.0%.
- **Cheaper entry helps a little and not enough.** The information table (not used to choose
  anything) shows the same rule by entry price: 20c -6.2c, 30c -6.4c, 40c -8.0c, 50c -7.9c, 60c
  -7.2c per contract. 40c and 50c reproduce H2's printed result exactly, a check that H4 ran H2's
  simulator unchanged. The fee is lower away from 50c (1.47c at 30c against 1.75c), which is about the
  1.5c difference seen, but every entry price loses in both halves. Entry price is not the lever.
- **What it does not say.** Other targets, entries chosen by a signal, or anything faster than a
  minute are still untested, as for H2. This stays inside the cost problem: a 4c round trip against
  prices set by professional quoters.

Strategy variants tried so far: 5 (the 60s scalp, H1, H2, H3, H4), all FALSIFIED, plus one exploratory
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

## Hypothesis H4: buy at 30c and sell at 80c (fixed 2026-10-06, before it was run on any data)

Raised by the owner: the bot and H2 buy only near 40c or 50c, so the whole 30c range is never
traded. This asks whether H2's rule works from a cheaper entry. Same machinery as H2, one new
band. `python -m scalper.bandscan` (to be written after this commit).

- **Rule, identical to H2 except the band.** Buy a side whose ask is in [0.28, 0.32] ("30c"), at
  the FIRST minute close with at least 5 minutes left and a usable quote (YES then NO). Sell at 80c
  when that side's bid first closes at 80c or more on a LATER minute; otherwise hold to settlement.
  Entry at the ask, a taker fee on both legs (7% unrounded per contract), no stop, one entry per
  market. Unit: a market. Statistic: net profit per contract.
- **Why the prior is the same as H2's.** In a fair market a price at 30c reaches 80c before 0c
  with probability 30/80 = 37.5%, a win of +50c against a loss of -30c, so the expected profit is
  zero before costs at any entry or target. Costs are a little lower than at 40c to 50c (the fee
  is 7% of p times 1 minus p, so 1.47c at 30c against 1.75c at 50c), about 3.5c to 4c a round
  trip. So H4 can only work if prices CONTINUE more than a fair game from low prices, and the
  earlier path study found no continuation.
- **Counterparty.** Whoever sells at 30c, or buys at 80c, on a view that a market moving up from a
  low price keeps going.
- **Prediction.** Mean net profit of at least +1c a contract. My honest expectation is the opposite:
  about -4c to -8c, as H2 lost at 40c and 50c.
- **Kill criteria.** FALSIFIED unless ALL hold: n of at least 300 markets; mean net profit positive
  with a day clustered z of at least 2.1 (the bar H2 used, kept so the three bands are held to the
  same standard); positive in BOTH halves of the 30 days; positive with fees 20% higher. Best
  outcome `NOT_YET_FALSIFIED`, meaning permission to test on days 31 to 45 back, which neither H2
  nor this has seen. It is never evidence of an edge, and no verdict means "trade".
- **Same data as H2, so the bar is not lowered for it.** The 30 days H2 used are reused. 30c was
  chosen because it is the gap in what H2 and the bot cover, not from a result, but a pass here
  would still have to survive the unseen days before anything is built on it.
- **Descriptive only, affects nothing above.** The same rule at 20c, 40c, 50c and 60c, to show how
  the result moves with the entry price. It is printed as information and is NOT used to pick a
  band: choosing the best-looking cell afterwards is the thing this process forbids.
- **Cost of this idea so far.** It is the fifth strategy variant tried (the 60s scalp, H1, H2, H3,
  H4); the spot lag study was exploratory and is not counted. Cuts examined for the verdict: 1 band.

## Hypothesis H5: quote both sides as a market maker (fixed 2026-10-06, before any code or data)

Chosen by the owner after H1 to H4 and H3 were falsified. H3 tested a resting BUY (a YES bid or a NO
bid, which is the same act as a resting ask) held to settlement and lost to adverse selection. A market
maker differs in what it does after a fill: it quotes BOTH sides every minute, a fill on one side invites
a fill on the other that closes the position at a profit equal to the spread, inventory is capped, and
only the leftover is held to settlement. Whether the spread captured on completed round trips beats the
adverse selection on one-sided fills is the question. `python -m scalper.marketmaker` (to be written
after this commit).

- **Rule.** At every minute close from the first usable quote until 5 minutes before close (a real two
  sided book, spread 10c or less): rest ONE contract at the YES bid and ONE at the YES ask, replaced at
  the new touch each minute. Inventory is the YES contracts held, capped at 2 either way: no new bid at +2,
  no new ask at -2. Quoting stops 5 minutes before close and the inventory is held to settlement ($1 per
  contract if YES, else 0).
- **Fill model, conservative, as H3.** A bid fills only when the tape prints strictly THROUGH it inside the
  next minute: a taker buying NO at a YES price below our bid. An ask fills only when a taker buying YES
  prints at a YES price above our ask. Both can fill in one minute (a round trip). A print AT our price does
  not count: our queue place is unknown. This understates fills.
- **Costs.** Every fill pays Kalshi's taker fee formula (7% of p times 1 minus p per contract), even
  though a resting order may pay less: the schedule for these markets is not confirmed, and assuming a
  discount would flatter it. A run with no fee is printed for information only.
- **Counterparty.** Impatient takers on both sides, who pay the spread to trade now. The usual reason
  this does not simply work is adverse selection: you are filled on the side the price is about to move
  through, which H3 measured at about 4c a filled contract against about 1c of spread.
- **Prediction.** Mean net profit of at least +1c a market. My honest expectation is negative: a
  contract's spread is about 1c to 2c, a fee is about 1.5c to 1.75c a fill, and adverse selection is
  larger than the spread.
- **Unit and sample.** One market, net profit in cents per market (all fills, fees and the settled
  inventory). The sample is fixed in advance: for each series, the markets sorted by close time and every
  4th of them (about 1,200 markets over the 30 days), chosen by position and never by result. The full tape
  for a market is about 30,000 trades, so a full run is days; a quarter keeps the detectable edge near
  1c to 2c.
- **Kill criteria.** FALSIFIED unless ALL hold: at least 300 markets; mean net profit per market positive
  with a day clustered z of at least 2.1 (the bar H2 to H4 used); positive in BOTH halves of the period; and
  positive with fees 20% higher. Fewer than 300 markets is NOT_ENOUGH_DATA. Best outcome is
  `NOT_YET_FALSIFIED`, meaning permission to test on days 31 to 45 back, never a trade. No verdict means
  "trade".
- **The decomposition that says what a result means.** Always printed beside the verdict: profit from
  completed round trips (the spread captured), profit from the leftover inventory held to settlement (the
  adverse selection), fills on each side, and the share of markets that ended flat. A profit made on round
  trips and given back on leftovers is the whole story and is reported as such.
- **Printed for information only.** No fee, fills counted when a print is AT our price, and inventory cap
  of 1 and of 4.
- **Cost of this idea so far.** It is the sixth strategy variant tried (the 60s scalp, H1, H2, H3, H4, H5).
  Cuts examined for the verdict: 1 configuration.

## Hypothesis H7: how far spot sits from the target predicts the outcome better than the market's price does (fixed 2026-10-07, before any code or data was looked at)

Asked by the owner: Kalshi stores each market's target (the strike, "to beat"). Every test so far used the market's
price and result, and none conditioned on how far Bitcoin spot sits from the target. The owner's question: of the
times spot is X above (or below) the target with T minutes left, how often does the market finish above it, and does
the price Kalshi charges match that? Bitcoin only: there is no free gold spot series here. Gold is not tested.

- **Mechanism and counterparty.** If the market charges, say, 65c for YES when spot is far enough above the target that
  YES wins 75% of the time, the sellers of that 65c are people pricing the distance badly (stale quotes, slow
  repricing as spot moves, a flat price near 50c that ignores a large lead). The usual reason it fails: the
  professional quoters on these markets already price the live index, and the lag study found no lag.
- **Observation, one per market.** At the minute close `t = close_ts - 360` (6 minutes left), a market counts if it
  has a usable two sided quote (spread 10c or less), spot closes exist for `t` and the 60 minutes before it, and the
  strike is stored. One decision per market means the observations do not overlap, and there is no choosing of the
  minute afterwards. Spot at `t` is the close of the 1 minute Coinbase candle that ends at `t` (the same alignment the
  lag study used).
- **Distance, in units of how far Bitcoin typically moves.** `z = ln(spot / strike) / (sigma * sqrt(6))` where `sigma`
  is the standard deviation of the 1 minute log returns of spot over the 60 minutes before `t`, and 6 is the minutes
  left. Fixed z buckets: below -2, -2 to -1, -1 to -0.5, -0.5 to 0, 0 to 0.5, 0.5 to 1, 1 to 2, above 2.
- **Split.** The markets are ordered by close time. The first half is the ESTIMATION half and the second is the TEST
  half. `p(bucket)` is the share of estimation-half markets in that bucket that resolved YES (buckets with fewer than
  20 markets are not traded). The test half is not looked at until the verdict run.
- **Descriptive output, labelled as such (no verdict, affects nothing).** For the estimation half only: for each z
  bucket, the number of markets, how often they resolved YES, and the mean YES ask Kalshi was charging then. This
  answers the owner's "how many times out of X" question in plain numbers.
- **Rule (the only configuration run).** On the test half, at `t`, with `ask` the YES ask and `bid` the YES bid:
  buy YES at `ask` if `p(bucket) - ask - fee(ask) > 0.02`; buy NO at `1 - bid` if `(1 - p(bucket)) - (1 - bid) -
  fee(1 - bid) > 0.02`; otherwise do nothing. One contract, held to settlement, fee `0.07 * p * (1 - p)` per
  contract (unrounded, because the measured real fee on 2026-10-07 was 1.67c for a 40c contract, which is exactly
  that formula; a run with fees times 1.2 is the stress). The 2c margin, the buckets and the 6 minutes are fixed here
  and are not tuned.
- **Prediction, recorded before the run.** Negative: the market already prices distance within the minute, so I
  expect a mean net of about -1c to -3c per entered market and a z below 2. If it comes out positive, suspect the
  alignment first: Kalshi settles on the CF Benchmarks RTI average of the last 60 seconds, and this uses Coinbase 1
  minute closes, so a spot figure that already contains information the strike does not is a lookahead to rule out.
- **Unit and kill criteria.** One entered market, net cents. FALSIFIED unless ALL hold: at least 300 entered markets
  in the test half; mean net positive with a day clustered z of at least 2.1; positive in BOTH halves of the test half;
  positive with fees times 1.2. Fewer than 300 entered markets is NOT_ENOUGH_DATA and crosses nothing off. Best outcome
  is `NOT_YET_FALSIFIED`, meaning permission to test on unseen days, never a trade.
- **Decomposition, always printed.** Entries by side, win rate against the average price paid, mean gross and fees, and
  the same table for the estimation half run through the rule, labelled in-sample so the gap between the halves is
  visible.
- **Known limits, stated up front.** Spot is not Kalshi's settlement source. One observation per market throws away
  most minutes on purpose. Thirty days is one market regime. The estimation half decides the buckets' probabilities,
  so the test is out of sample but the whole sample is one month.
- **Cost of this idea so far.** The eighth variant tried. Cuts examined for the verdict: 1 configuration.

## Idea ledger (written 2026-10-07, before any idea below was run)

One line per idea, recorded BEFORE it is built, so a tried idea cannot be quietly retried
and a rewording of a dead idea is visible as one. Status is only `OPEN`, `RUNNING`,
`FALSIFIED`, `NOT_YET_FALSIFIED` or `NOT_RUNNABLE` (no simulator, nothing recorded).
Strategy variants tried before this ledger: 8 (the 60s scalp and H1 to H7; the no-lag
study was exploratory and does not count). Every idea that gets a verdict raises that count, and the bar rises with it.

| # | Idea | Counterparty (who loses) | Prediction | Needs | Status |
|---|---|---|---|---|---|
| L1 | Favorite-longshot bias in the two markets we trade (Bitcoin and gold 15 minute only; the owner chose to keep the universe to these two) | Retail buyers overpaying for longshots | Cheap side loses more than its price implies by more than the fee | Settled history we hold (30 days, both series) | FALSIFIED 2026-10-07 |
| L2 | H2 entered only when the first 30 seconds put spot within reach of the strike | Sellers who price the move as luck | Hit rate in the chosen bucket beats the price by at least 3c | Spot and candles (have; Bitcoin only, no gold spot) | FALSIFIED 2026-10-07 |
| L3 | Settlement edge: buy the side already far from the strike at 90c or more, last 2 to 3 minutes | Holders who sell near-certainties early | Win rate above price plus fee (fee is smallest at extremes) | Candles (have) | FALSIFIED 2026-10-07 |
| L4 | Maker entry that rests only when distance says the price is cheap | Takers crossing the spread | Net after maker fee above zero | Recorded order books | NOT_RUNNABLE until the recorder has data |
| L5 | Quote staleness: list price lags the single-market read by about 2c | Stale resting orders | A stale-side fill beats its fee | Recorded order books at under 10 seconds | NOT_RUNNABLE until the recorder has data |
| L6 | Bitcoin and gold on the same window, or related ladders, priced inconsistently | Slow quoters | Gap beats two fees | Recorded books, both series | NOT_RUNNABLE until the recorder has data |
| L7 | Volatility regime gate on the best variant, regimes set by spread and liquidity, never by profit | Whoever misprices fat tails | Touch rate shifts by at least 5 points | Candles (have) | OPEN |
| L8 | Averaged strike at the open (Bitcoin). The market compares the average of the last 60 seconds of BRTI before the close with the average of the last 60 seconds before the open, so the strike is a LAGGING average and spot minus strike at the open is recent drift | Makers who open near 50c without pricing the gap | At the open, in the top decile of gap size, price is off the model by at least 3c | Strike, spot minute closes, first minute quotes (have) | PRE-REGISTERED 2026-10-07 |
| L9 | Final minute averaging (Bitcoin). With a 60 second average at the close, the settlement value is less uncertain than a single end price (one third of the variance), so prices should be more extreme near the end than a point-to-point model says | Holders pricing the last minute as a terminal price | With 1 minute left the favorite wins at least 2 points more often than its price after the averaging adjustment | Spot minute closes (have); sub-minute spot would sharpen it | PRE-REGISTERED 2026-10-07 |
| L10 | Scheduled release windows (gold and Bitcoin): dates fixed in advance by calendar (CPI, jobs, FOMC), never by past returns | Quoters slow to widen around a release | Price error or spread in release windows is at least twice the normal level | A dated release calendar (not in the repo), candles | OPEN, calendar needed |
| L11 | Taker flow momentum: net buying by takers in the last few minutes predicts the outcome | Slow quoters facing informed takers | Taker imbalance in the top decile shifts the outcome rate by at least 3 points beyond the price | The trade tape from H3 (check what it stores first) | OPEN, tape check needed |
| L12 | Book depth imbalance: the share of size on one side of the top levels predicts the next price move | Quoters that do not read their own depth | Imbalance in the top decile predicts a move of at least 1c within a minute | Recorded order books | NOT_RUNNABLE until the recorder has data |
| L13 | Volatility surprise: after a jump in short term realized volatility, makers' volatility estimates lag. This is H7's calibration cut by volatility regime, so it is H7 conditioned, not a new mechanism | Makers using stale volatility | Calibration error doubles in the top volatility decile | Spot minute closes (have) | OPEN, overlaps H7, likely duplicate |
| L14 | Locked or crossed books: buy both sides when the two asks sum to less than 1 minus both fees. An arithmetic arbitrage, not a directional bet | Stale quoters on one side | At least one occurrence a day with net of at least 0.5c after both fees | Recorded order books at under 10 seconds | NOT_RUNNABLE until the recorder has data |

**Settlement rules, verified from the live markets on 2026-10-07.** Bitcoin: the simple average of the 60 seconds of CF Benchmarks' BRTI before the close, against the same average before the open. Gold: the close of the 1 minute Pyth GOLD candle at the close, against the one at the open. Gold has no averaging and no free spot series here, so L8 and L9 are Bitcoin only.

Standing exclusions, so they are not re-proposed:

- **Exit by a dead-trade stop.** H2 already ran a stop 20c below entry (-6.9c and -6.7c, against
  -8c without one). A stop does not change the expected profit of a fair game.
- **Hours chosen by profit.** Selecting a window on returns fits noise. Hours may be chosen on
  liquidity or spread only.
- **Half-price entry with a lock hedge.** A fair-game identity gives zero edge before cost.

Rules for every row above: its counterparty, numeric prediction and kill criteria are written
in its own section before any code runs; day-clustered z of at least 2.1, both halves positive,
fees x1.2, at least 300 observations; verdicts only as above.

## Pre-registration: L1, L2 and L3 (fixed 2026-10-07, before any code or any price was looked at for these rules)

Run on the data we hold: 30 days of KXBTC15M (2,850 markets) and KXGOLD15M (2,026 markets). The owner chose to keep the
universe to these two markets, so a broader survey is not used. **This is not unseen data.** H2, H4 and H7 were already run on
these same days, so a pass here could never be more than permission to test forward on the recorder's data. Three rules means
three more variants against the bar: 8 tried before this, 11 after.

Common to all three, fixed now. Entry at the ask of the side bought (YES at its ask, NO at 1 minus the YES bid, snapped to 4
places), real two sided book only (spread 10c or less, `valid_quote`). Held to settlement unless the rule says otherwise.
Taker fee 7% x p x (1-p) per contract on the way in; settlement has no fee. One observation per market. Statistic: net profit
per contract, day clustered z. Kill criteria: FALSIFIED unless n is at least 300 markets, mean net is positive with a day
clustered z of at least 2.1, positive in BOTH halves (split by close time at the median), and positive with fees 20% higher.
Fewer than 300 entries is `NOT_ENOUGH_DATA`. There is no verdict that means "trade". A simulator guard test runs the exact
code on a simulated FAIR game and requires it to lose about its costs; a profit there means the simulator invents an edge.

**L1. Favorite-longshot bias, 6 minutes left.**
- **Rule.** At the minute close with 6 minutes left (the same decision point H7 used, not tuned), buy the side whose ask is in
  [0.88, 0.97] (the favorite). Hold to settlement. Both series together; the split by series is printed for information only.
- **Counterparty.** Whoever buys the cheap side (3c to 12c) and overpays for the small chance, the retail longshot buyer.
- **Prediction.** Mean net at least +0.5c per contract. The fee at 90c is only 0.63c, so a small bias could survive it.
- **Prior, stated honestly.** Low. At the ask the spread (1c to 2c at the extremes) is paid on entry, and these are liquid
  markets whose price already reflects spot distance. It would need the favorite to win a few points more often than its
  price says.

**L2. H7's entries with H2's exit (sell at 80c).**
- **Rule.** Take exactly the markets H7 would enter (its decision at 6 minutes left, its estimation half builds the bucket
  table, its second half is the test), and instead of holding, sell at 80c on the first LATER minute close where that side's
  bid is 80c or more, otherwise hold to settlement. Fee on the exit as in H2. Bitcoin only: gold has no spot series here.
- **Counterparty.** The same as H7 (a market that prices spot distance badly) plus H2's (someone buying at 80c on momentum).
- **Prediction.** Mean net at least +0.5c. The exit changes the payoff shape, not the information, and H7 itself lost 2.69c,
  so the prior is very low. This is H7's signal wearing H2's exit, and it is recorded as that, not as a new mechanism. It is
  run because the owner asked, and it may well return `NOT_ENOUGH_DATA` since only H7's test half is used.

**L3. Settlement edge, 2 minutes left.**
- **Rule.** At the minute close with 2 minutes left, buy the side whose ask is in [0.90, 0.98]. Hold to settlement.
- **Counterparty.** Holders who sell a near-certain contract early to lock in a gain and free their money.
- **Prediction.** Mean net at least +0.5c per contract.
- **Overlap with L1, stated.** This is the same favorite-longshot bias measured later in the market's life, where the fee is
  smallest and information is mostly in. If L1 is falsified, this has the same prior and is nearly the same trade; it is
  registered because the timing differs, and it counts as its own variant.

Verdicts are recorded below when the one run each has happened. No threshold, band, decision minute or fee changes after seeing them.

**2026-10-07: L1, L2 and L3 each ran once (`python -m scalper.lstrats`, commit 962459f), all `FALSIFIED`.** 4,871 markets, 30 days.
Nothing changed after seeing the numbers.

| Rule | n | Gross | Mean net | z | 1st half | 2nd half | Fees x1.2 |
|---|---|---|---|---|---|---|---|
| L1 favorite 88c to 97c, 6 min left | 1,447 | +1.44c | +0.97c | +1.45 | +0.71c | +1.22c | +0.87c |
| L3 favorite 90c to 98c, 2 min left | 1,374 | -1.38c | -1.71c | -2.94 | -1.91c | -1.50c | -1.77c |
| L2 H7 entries, sell at 80c (Bitcoin) | 879 | -5.51c | -7.00c | -8.30 | -8.24c | -5.76c | -7.30c |

- **L1 is the first rule here with a positive mean in both halves and under higher fees, and it still fails.** Its z is 1.45
  against a bar of 2.1, so the data cannot tell +1c from zero. Bitcoin (+1.04c, 854) and gold (+0.85c, 593) agree in sign, which
  is printed for information and decided nothing. Passing the pre-registered bar was the rule, and it was not met. At this
  noise level a z of 2.1 would need about twice the sample (roughly 60 days), and the days we hold have already been
  used by H2, H4 and H7. Any follow-up has to be a forward test on days not yet seen, with the band fixed as it is here.
- **L3 lost 1.71c while L1 won 0.97c, from the same favorites bias measured at 2 minutes instead of 6 minutes.** The two are
  the same trade at different times, so the sign flip says the favorites premium is not stable across the market's life:
  early favorites were underpriced a little, late ones overpriced a little, and neither survives the bar. I registered them as two
  variants and they count as two.
- **L2 is H7's signal wearing H2's exit and it lost 7c.** The exit swaps a chance of a larger settlement win for a sure 80c,
  and pays a second fee. It was registered as a duplicate of H7's information and the result agrees.

Strategy variants tried so far: 11 hypotheses (the 60s scalp, H1 to H7, L1, L2, L3), all `FALSIFIED`, plus one parameter search of 437 rules, which counts against every bar as 437 more tries. The lag study was exploratory and does not count.

## Live waiver: L1 for 24 hours in the live account (terms fixed 2026-10-07, before any code for it)

The owner asked for the live account to run L1 automatically for 24 hours. L1 FAILED its own pre-registered bar (z +1.45 against
2.1), so this is a waiver of that bar by the owner, recorded here with its terms. It is not evidence of an edge, and nothing in a
24 hour run can become evidence of one: at about 55 trades a day, one trade's standard deviation of roughly 27c and an
expected mean of +1c or less, a day's profit has a standard deviation of about $2 against an expected +$0.55. What the run does
test is the plumbing at volume: fills, fees, rejections, shards, timing.

- **The rule is L1 exactly as pre-registered, nothing tuned.** Bitcoin and gold 15 minute markets only. About 6 minutes before the
  close (accepted window: 330 to 400 seconds left), buy ONE contract of the side whose fresh price is 88c to 97c inclusive, at the
  touch, immediate-or-cancel. Held to settlement. No exit, no stop, no second try on the same market.
- **Hard limits, in code, changed only by a reviewed change.** One contract per order and at most $2.00 including the fee. At most
  80 orders in the session. The session switches itself off after 24 hours, on the first order whose answer is lost or refused,
  and when the account's cash falls more than $7.00 below its level at the start (a $5.00 loss allowance plus the at most $2.00 that
  can legitimately sit in the two open positions). At most one open position per series, so open exposure stays under about $2.
- **Gates that always apply.** Server switch `KALSHI_LIVE_ENABLED` must be on. The halt switch blocks it (a missing halt setting
  counts as halted). An unresolved earlier order blocks it. The balance on the market's own shard must cover the cost plus $0.50.
  Production host only. Never retried.
- **Worst case.** 80 orders that all lose is impossible inside the loss stop: the stop trips at about $7 of loss, about 8 losing
  trades, and one more order can already be in flight. The honest worst case is therefore roughly $9.
- **How the result is read, written now.** Net result after fees, and the count of fills, no fills and rejections. It is recorded
  as one forward observation of L1 with n of about 55. It does not re-run the verdict, and no band or minute changes afterwards.
  A positive day proves nothing; a negative day is within the expected noise unless it hits the stop.

## Pre-registration: L8 and L9 (fixed 2026-10-07, before any code or any price was looked at for these rules)

Both use the settlement rule verified on 2026-10-07: Bitcoin settles on the simple average of the 60 seconds of BRTI before the
close, against the same average before the open (the stored strike). Bitcoin only, since gold has no spot series here. The same
30 days that H2, H4, H7 and L1 to L3 already used, so a pass is permission to test forward and nothing more. Two more variants:
11 tried before, 13 after.

**Model, fully fixed, nothing fitted.** At the decision minute, S is Bitcoin spot (the close of the 1 minute candle that STARTED a
minute earlier, as in H7), K the stored strike, and sigma the sample standard deviation of the 60 one minute log returns ending
there (H7's volatility). The settlement value is an average over the last minute, so with tau minutes before that minute begins,
its variance is sigma squared times (tau + 1/3), not tau + 1 as for a single end price. The model probability of YES is
Phi(ln(S/K) / (sigma x sqrt(tau + 1/3))).
- **Entry rule, same as H7's, margin fixed now at 2c.** Buy YES at the ask if p minus the ask minus the fee exceeds 0.02. Buy NO at
  1 minus the YES bid if (1 - p) minus that price minus its fee exceeds 0.02. Real two sided book only. One observation per
  market, held to settlement, taker fee 7% x p x (1-p) on entry.
- **Judged by the common bar:** n of at least 300 markets, day clustered z of at least 2.1, positive in both halves (split by close
  time at the median), positive with fees 20% higher. Verdicts only `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`.
- **Simulator guard:** on a simulated fair game the exact code must lose about its costs.
- **Information only, decides nothing:** how well the model's own p matches outcomes in deciles, gross profit, and the split of
  entries into favorites (price 80c or more) and the rest.

**L9. Final minute averaging.** Decision at the candle that ends 1 minute before the close, so tau = 0 and the variance factor is
1/3. Counterparty: holders who price the last minute as a single end price, who leave the far side too cheap and the near side
too dear. Prediction: mean net at least +0.5c per contract. Prior, stated honestly: low to moderate. L3 (favorites at 2 minutes,
no distance) lost 1.7c, but this conditions on the actual distance, and the averaging effect is real arithmetic: at 0.6 sigma
a single end price gives 73% and the averaged value gives 85%. Whether any trader leaves that on the table is the question.

**L8. The averaged strike at the open.** Decision at the candle that ends 14 minutes before the close (one minute after the open),
so tau = 13 and the variance factor is 13 and 1/3. The strike is a lagging average of the last minute, so spot minus strike at the
open is recent drift, and the model prices it. Counterparty: whoever opens the market near 50c without pricing the gap.
Prediction: mean net at least +0.5c. Prior, stated honestly: very low. H7 found the price well calibrated to distance at 6 minutes,
the same quoters set the open, and spreads are widest right after an open, which is the cost this rule pays.

Verdicts are recorded below when the one run each has happened. No margin, decision minute, variance factor or fee changes after seeing them.

## Pre-registration: the automated rule search (fixed 2026-10-07, before any code or any result)

The owner asked for a loop: make 50 rules and test them, keep the top 25; make 50 more, keep the top 25; take those top 50, add or
remove ONE rule from each, rerun, keep the top 25; then repeat. This is a parameter search, not a set of hypotheses, and it is the
exact "automated loop" the deflation notes say a bar of 1.5 means nothing against: the best of N noise strategies always looks good.
So the search is run with these protections, fixed now:
- **Locked holdout.** The loop only ever sees the first 15 days. The last 15 days are read ONCE, at the end, for the saved survivors,
  and a result printed there is the only out-of-sample number. Anything tuned after reading it is contaminated and says so.
- **A shuffled-outcome control.** The identical pipeline, same seed and rules, is run with each market's result shuffled among the
  markets of its own day. The best z it finds on pure noise is printed beside the real best, so the selection effect is visible.
- **Every configuration counts.** The total number of rules evaluated is recorded and the null expectation for the best of N,
  about sqrt(2 ln N) in z, is the floor a search-window z must beat to mean anything at all. Beating it is still only permission to
  look at the holdout and, after that, to test forward on days not yet seen.
- **Fixed grammar.** A rule is a decision minute (1, 2, 3, 4, 5, 6, 8, 10, 12 or 14 minutes left), a price band for the side bought
  (taker at the ask, fee 7% x p x (1-p), held to settlement), a side selector (either, YES only, NO only), and up to three optional
  filters: spread at most 1c, 2c or 4c; one series only; the market's own price having moved toward or away from the side by 2c or
  5c over the last 1, 3 or 5 minutes. No filter reads a result. No hour of the day is a filter, because hours chosen by profit fit
  noise. Add or remove one rule means adding or removing one filter, or changing nothing else.
- **Ranking.** By the day clustered z of net profit per contract in the search window, with at least 100 entries; a rule with fewer is
  not ranked. Both series are in the pool, since the owner chose these two markets and nothing else.
- **What is saved.** Each round's top 25 with its search-window statistics, in `search/`, and nothing from the holdout until the
  final step. Verdict words stay `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`; this search can never produce a "trade".

**2026-10-07: the first run of the search (`python -m scalper.search`, seed 7, 3 cycles, commit d9746a5): nothing survives.**
437 distinct rules evaluated on the first 15 days (2,346 markets); 2,525 markets locked as the holdout. The saved top 25 of every
round are in `search/`.

| | Search window, best z | Holdout of the final 25 |
|---|---|---|
| Real data | +2.99 (3 minutes left, either side priced 20c to 30c, Bitcoin, spread 4c or less: +9.63c on 167 entries) | 6 of 25 positive, mean net -1.85c, best z +1.62. That best rule fell from +9.63c to -0.90c |
| Fair market control (same prices and costs, outcomes drawn from each price) | +2.44 | 7 of 25 positive, mean net -1.44c, best z +1.85 |

- **The survivors look exactly like the survivors of a fair market.** Real and fair-market results are the same size, in both the
  search window and the holdout. The best real rule's +9.63c was selection: the same pipeline finds z of about 2.4 to 3 in a market
  where no edge can exist, and a z of 2.99 is under the 3.49 that the best of 437 is expected to reach by luck alone.
- **The first control was invalid and is replaced.** Shuffling results among markets of one day broke the link between price and
  outcome, so buying a 5c longshot won half the time and the control showed z of 25 and +27c. That is a flaw in the control, not
  a finding, and it is why the control now draws outcomes from each market's own price. The real-data numbers did not change
  between the two runs; the holdout was printed twice (the second time only to fix the control) and no rule was changed in between.
- **Cost still decides it.** The 6 holdout winners are within what 25 fair-market rules produce (7), and none has a search-window z
  that a real edge would explain.
- **What the search can and cannot do.** It found nothing beyond noise on 30 days, which is a statement about this universe and these
  rule shapes, not a proof that nothing exists. Running it again with more cycles would not help: the holdout is now read, and any
  rule tuned after seeing it is contaminated. The only clean next data is forward data (the live session and the recorder).

## Pre-registration: the overnight run on older data (fixed 2026-10-07, before the older history was downloaded or looked at)

The first search spent its holdout (see the 437 rule result above). The owner gave permission to pull more history and asked for
five solid rule-sets. Kalshi keeps candles about 66 days back, so the markets of roughly Aug 2 to Sep 5 are NEW data, older than
anything used so far. Only that, and nothing newer, can serve as a clean test. The rules for using it, fixed now:

- **Windows, by date.** W0 = the older history (Aug 2 to Sep 5). W0s is its first two thirds of days (search), W0h its last third
  (locked until the very end). W1 = Sep 5 to Sep 20 and W2 = Sep 20 to Oct 5 are the windows of the first search; they were used to
  pick the first search's rules, so they are out of sample ONLY for rules found on W0s.
- **Stage A. Do the first search's winners generalize?** Every rule saved in `search/` (all nine top-25 lists, deduplicated) is
  scored once on W0s. Nothing is tuned.
- **Stage B. A new search of at least 200 rules,** the same grammar and the same loop (50 and 50 and 50 mutants, 25 kept, repeated),
  run on W0s only, beside a fair-market control run on the same window (outcomes drawn from each market's own price).
- **Survivor test, fixed now.** A saved rule is a survivor only if ALL hold on windows it was NOT selected on: mean net after fees is
  positive in each of them, each with at least 50 entries, and the pooled day-clustered z is at least 2.5. For a Stage B rule the
  windows are W0h, W1 and W2. For a Stage A rule they are W0s, W0h and W2 (W1 was its search window). W0h is read once, for the saved
  rules of both stages together. A null rule passes this with probability about 0.1%, so with 50 saved rules the chance that
  luck alone produces one survivor is about 5%. The same test is run on the fair-market control's saved rules, so the false
  survivor rate is measured, not assumed.
- **No second pass.** After the one read of the out-of-sample windows, a rule that is changed and retested is contaminated and is
  labelled so. More searching on W0s alone is allowed and counts in N; it does not make the windows clean again.
- **What a survivor means.** Permission to test it forward (the live session and the recorder), never "trade this". Fewer than five
  survivors, including none, is a complete and valid result and is reported as such.

**2026-10-07: the overnight run on older data (`python -m scalper.overnight`, seed 11, 2 cycles; commit 4be67f3).** The history now runs
Aug 1 to Oct 7 (11,092 markets: 6,432 Bitcoin, 4,660 gold; 97,624 minutes of Bitcoin spot). Windows: W0s 3,826 markets, W0h 1,988, W1 2,346,
W2 2,525, W3 (Oct 5 to 7) 402.

- **L1 replicated on data it never saw.** L1 is one fixed pre-registered rule with no selection. On the older W0 (1,810 entries) it made
  **+1.10c net, z +2.68**, positive in both halves of that window (+0.92c and +1.46c), after losing its own bar on W1 and W2 at z 1.45.
  Over all 68 days: 3,382 entries, +0.98c, z +2.76, about 50 trades a day. W3 (125 entries) is -0.47c, z -0.20, which is noise at that size.
  A win rate of 94.1%, average win +6.8c, average loss -92.0c. Per contract: +$0.49 a day, standard deviation $1.47, 25 of 68 days losing,
  worst day -$3.11, maximum drawdown $4.84. Bootstrapped from the days: over 30 days at one contract it ends positive 96% of the time.
- **L3 (favorites at 2 minutes) lost on every window**, -1.22c on W0 (z -2.42): the reverse of L1, consistent with the profile below.
- **L8 and L9 (averaged settlement) were run once and are `FALSIFIED`:** L9 -1.79c (z -2.31), L8 -2.38c (z -2.31), both halves negative.
  The market's own price tracks the YES rate decile by decile far better than the averaged-variance model does.
- **Exploratory profile (no verdict).** Favorites priced 80c to 97c: +0.1c to +1.2c at 5 to 8 minutes left in BOTH periods, -2.6c to -3.2c at 2
  minutes left in both (z -3.4 and -4.2). Longshots priced 3c to 20c: -1.5c to -3.1c at 4 to 10 minutes in both periods (z -3 to -6), +1.0c at
  2 minutes in both. A real favorite-longshot pattern that changes sign over the last minutes; L1 harvests its small positive side.
- **The search.** Stage A: of the first search's 179 saved rules, 2 survive the fixed test on W0s, W0h and W2. Stage B: of 132 new rules found
  on W0s, 2 survive on W0h, W1 and W2. The four: (1) 2 minutes left, either side priced 3c to 20c, Bitcoin only, spread 1c or less
  (+2.1c, +5.3c, +2.1c out of sample, pooled z +3.46, and +4.35c on the newest 67 entries); (2) 2 minutes left, NO side, Bitcoin, the market moved
  away from the side by 2c over 5 minutes, spread 4c or less (pooled z +2.87); (3) 8 minutes left, YES side priced 80c to 97c (pooled z +2.88);
  (4) the same with spread 2c or less.
- **The first control was invalid, twice.** The shuffle control broke the price-outcome link. The fair-market control that drew outcomes from
  the last-minute price kept the real price dynamics, so it behaved like a resample of the real data (survivors in about half its runs) and
  proves nothing; it is withdrawn. The valid null gives every rule zero edge at its OWN decision price: each entry wins with probability equal to
  the side's mid, independent draws per rule, paying the ask and the fee, with the fixed survivor test applied to all 311 rules.
  Over 500 repeats the best pooled z in that null has median +1.79, 95th percentile +2.75, maximum +4.25. **The real best, +3.46, beats it:
  P(null best >= real best) = 0.008, and P(null survivors >= 4) = 0.000 (mean 0.11).** Independent draws across rules is the strict direction.
  So at least one of the four is unlikely to be luck. That is a statement about the family, not about which one.
- **A warning on the strongest.** The first rule earns +3.04c (z +4.11, n=1,822) only at exactly 2 minutes left on Bitcoin; at 1 minute it is
  -0.85c, at 3 minutes -0.15c, and on gold -0.81c. A sharp spike at one minute on one series is what an artifact looks like, and also what a
  quote refresh cadence would look like. Its wins exceed its price by 2 to 9 points in every price band (6.1% against 4.2%, 9.8% against 7.8%,
  21.3% against 12.3%, 21.6% against 17.2%). Treat it as a hypothesis for the forward test, not a result.
- **Combining.** Daily profit correlations are low between the favorites rules and the 2 minute rules (+0.08 and +0.01). Per contract of each:
  L1 alone +$0.49/day; L1 with the 2 minute longshot rule +$1.30/day, sd $2.32, max drawdown $6.11; those two plus the 8 minute YES favorites
  +$1.59/day, max drawdown $8.48; all four +$2.22/day, max drawdown $7.79. The 2 minute rules and the 8 minute rule were selected on the same
  data, so those figures are optimistic. Fills are assumed at the ask on the decision minute; a live fill can be worse.
- **What this does and does not support.** The pre-registered L1 is a small, replicated, out-of-sample positive of about +1c a contract (about
  1.1% a trade): worth running forward at small size, which the 24 hour session is doing. The 2 minute rules are the most interesting and the
  least trustworthy. Nothing here is a reason to size up. The overall power is low: with about 500 entries per window, an edge under about 5c is
  hard to see, which is why every candidate here shows up as "survives" at z of 2.5 to 3.5 and not 6.

## The order-book recorder (`recorder.py`, read only)

Records the public order book of the open Bitcoin and gold 15 minute markets every few
seconds into `data/ob.sqlite` (table `ob`), so L4 to L6 can be tested on real depth rather
than a minute candle. It places nothing, needs no key, and reads only the public
`/markets` and `/markets/{ticker}/orderbook` endpoints. It describes; it never judges.

## The paper bot (retired Oct 7, 2026)

The simulated server bot is removed from the code. It ran H2 on $100 of pretend money as plumbing, lost money as H2's
verdict predicted, and nothing it did counts as evidence. The server keeps only H2's entry rule (as the signal the live test
uses) and the halt switch. The bar near the top of this file was written for paper trading and is not met; the owner chose a
small live plumbing test on Oct 7, which is a decision and not evidence of an edge.

## How real orders work on Kalshi (read from docs.kalshi.com on 2026-10-05)

Nothing below is implemented. It is what the live version will have to do.

- **Hosts.** Production `https://external-api.kalshi.com/trade-api/v2`. Demo has separate
  accounts and separate API keys, mock funds, and prices that "may not be reflective of
  those in real markets" ([demo environment](https://docs.kalshi.com/getting_started/demo_env)).
  It tests the plumbing, not the strategy. Demo endpoints (confirmed by the owner 2026-10-06):

  | Surface | Recommended demo endpoint | Also supported |
  |---|---|---|
  | REST Trade API | `https://external-api.demo.kalshi.co/trade-api/v2` | `https://demo-api.kalshi.co/trade-api/v2` |
  | WebSocket API | `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2` | `wss://demo-api.kalshi.co/trade-api/ws/v2` |

  Checked from the research container on 2026-10-06: both REST hosts answer unauthenticated
  reads, and the demo lists open `KXBTC15M` and `KXGOLD15M` markets, the two series the bot
  uses. Orders, balance and positions need a demo API key (separate from any real key).
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
- **The demo has two front doors, and one can fail alone (measured 2026-10-06 20:30 to 20:53 UTC).**
  `external-api.demo.kalshi.co` (the recommended host) answered HTTP 503 with `trading_active: false` on
  every call, while `demo-api.kalshi.co` answered 200 with all four shards trading, and a signed order
  placed through it was accepted and cancelled. Kalshi's published schedule showed the demo open at the
  time (its only daily closure is a 15 minute gap) and production was fine. So "the demo is down" can mean
  one hostname is down. Both the website's test trader (since removed, Oct 7, once live testing began; this CLI stays) and `python3 -m scalper.demo` now try the second
  host when the first fails transiently (5xx, 429 or no answer), with the same order id. That is safe
  because they front one exchange and a repeated `client_order_id` is refused with 409, which the trader
  reads as "an earlier attempt landed".
- **Other demo facts measured the same day.** A create returns **HTTP 201**, not 200, with
  `order_id`, `client_order_id`, `fill_count`, `remaining_count` and `ts_ms`. A cancel needs the market
  ticker and shard (`DELETE /portfolio/events/orders/{id}?market_ticker=...&exchange_index=...`).
  Markets are listed ahead of time as "initialized" and open on the quarter hour, so a call in the last
  seconds before the next quarter hour finds no open market.

**Owner's decision, 2026-10-07: real money as a test phase.** The bar below (a strategy that passed its
pre-registered test plus 300 paper trades) has NOT been met: no strategy has passed (the 60s scalp, H1 to H6
were all `FALSIFIED`) and the paper bot has not reached 300 trades over 5 days. The owner chose to put $100
to $150 behind it anyway, with the risk per trade kept small. That is recorded here as a decision, not as
evidence of an edge. Step 1 is the one-contract live test (`kalshiLiveLib.js`): production signing, a real
fill, the real fee, and the real duplicate `client_order_id` behaviour. Step 2, a live bot, is not built and
needs its terms written first: 1% per trade, the existing 3% and 5% daily limits, a total loss stop the owner
names in advance, an arming switch that is off by default, and the halt button in front of it.

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
