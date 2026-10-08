# kalshi-scalper

Research and risk tooling for Kalshi 15 minute BTC (`KXBTC15M`) and gold
(`KXGOLD15M`) markets. Standalone on purpose: it is not part of
`shwoop-server`, which places real Alpaca orders.

## Status

Nothing in this folder places an order; it is offline research over downloaded history and the recorder's snapshots. Real orders exist, and live
elsewhere: `functions/kalshiLiveLib.js` in the repo root runs strategy L1 in the owner's real Kalshi account under the owner's written waiver ("Live waiver:
L1 for 24 hours", below), with hard limits, a loss stop and a halt switch. **The bar below has NOT been cleared**: L1 is the best rule found, it has never
passed its own forward test, and it is running because the owner chose to accept a thin and unproven edge, not because research approved it. Nothing
here, and no verdict word, means "trade".

## Build order (as it happened)

1. `backfill.py`  fetch Kalshi's own 1 minute history for settled markets.
2. `analyze.py`, `calibration.py`, `scalps.py`, `situations.py`  measure it.
3. Strategy       only if the measurement shows room. Declares counterparty first. Every hypothesis tried so far is `FALSIFIED`.
4. The paper bot  was built, measured and retired on 2026-10-07; the live bot replaced it (see "The paper bot (retired Oct 7, 2026)").
5. Live, tiny     L1 only, behind hard limits, on the owner's waiver. Its size is governed by the size ladder, not by this folder.

## Bar to clear before any real money (written before any result exists)

Not met by anything. Kept as the standard every forward check is judged by.

- At least 300 trades and 5 separate days.
- Positive net expectancy per trade AFTER fees, with fills priced at the
  ask going in and the bid going out, never the mid.
- Net profit still positive when fees are assumed 20% higher than modelled. (Kalshi also rounds fees up to the cent per order, which costs a
  one contract order about half a cent more than the modelled fee: see "Cost model check: fee rounding per order".)
- Predicted probabilities calibrated (60% calls win about 60%).
- Fewer than N strategy variants tried, N recorded here as we go, because
  best-of-many crosses any bar by luck.

Strategy variants tried so far: **2,567 as of 2026-10-08** (792 before P1; P1 is the 793rd; the four slot search adds 1,760; F6 and F7 two; Q1 to Q3 and two
Q1 thresholds five; F8 one; N1 and N2 two; X1 to X4 four), all `FALSIFIED` or `NOT_ENOUGH_DATA`. The running total is kept up to date in the section that last changed it.
Cuts examined by the decision rule: 18, plus 3 entry times for H1.

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

## Pre-registration: the forward check of L1 and the four overnight survivors (fixed 2026-10-08, before any rule was run on the new data)

The overnight run left L1 (a fixed rule that was never selected) and four rules that were selected on returns in older windows. A rule
chosen on returns can only be believed on days it did not choose from, so this is the first test on days that none of them has seen.
Nothing is retuned: the definitions are the ones in the code and in `search2/stageA.json` and `search2/stageB.json`.

**What I had seen when this was written (disclosed).** I downloaded the new markets and checked the schema, the count and the share
with a result. I also counted how many entries each rule makes per day on the OLD data (counts only, no outcomes) to size the test.
I had not run any rule on a market that closed after the old data ended.

**The forward window.** Markets that closed after `2026-10-07 18:30:00 UTC` (close_ts above 1791397800), the last close in the database
before the 2026-10-08 download. Both series. W3 (closes after 2026-10-05 15:00 UTC up to 2026-10-07 18:30 UTC) ends where this
window starts, so the two share no market; the run prints the overlap count (it must be 0) and W3 is NOT pooled into any forward
verdict, so nothing is counted twice. The 24 hour live L1 session trades the same markets; its fills are one more observation of L1
and are not part of this table either.

**The five rules, definitions exactly as coded** (cost: entry at the ask of the side bought, snapped to 4 places; taker fee 7% x p x
(1-p); held to settlement; one observation per market):

| Name | Definition | Code |
|---|---|---|
| F0 = L1 | 6 minutes left, favorite whose ask is 0.88 to 0.97, both series | `lstrats.hold_rule(L1)` |
| F1 | 2 minutes left, either side priced 0.03 to 0.20, Bitcoin only, spread 1c or less | `search.observe`, stageA #1 |
| F2 | 2 minutes left, NO side priced 0.03 to 0.97, YES price rose 2c or more over the last 5 minutes (the market moved away from NO), Bitcoin only, spread 4c or less | `search.observe`, stageA #2 |
| F3 | 8 minutes left, YES side priced 0.80 to 0.97, both series | `search.observe`, stageB #1 |
| F4 | F3 with spread 2c or less | `search.observe`, stageB #2 |

F3 and F4 are nested (F4 takes 2,146 of F3's 2,223 older entries), so together they are ONE effective test, not two. F0 and F3 overlap
in favorites priced 88c to 97c as well.

**Counterparty, prediction and universe for each** (prediction recorded before the run; "universe" is cost or fixed, never returns):

- **F0.** Loser: the retail buyer of the 3c to 12c side, who overpays for a small chance. Prediction: +1.0c a contract (it made +0.98c over
  68 days). Universe: fixed (both series). Prior: moderate; it is the only one of the five that was not picked from a search.
- **F1.** Loser: whoever sells the cheap side two minutes out, quoting the last-minute tail too close to zero. Prediction: +1.5c, below
  its +2.1c to +5.3c out-of-sample reads, because the best of a family shrinks. Universe: fixed (Bitcoin only), but the rule was picked on
  returns. Prior: low to moderate. The README already warns that it is positive only at exactly 2 minutes (1 minute -0.85c, 3 minutes
  -0.15c, gold -0.81c), which is the shape of a quote-refresh artifact.
- **F2.** Loser: the seller of NO after the YES price jumps, who treats a 2c YES rise as information and sells the other side too cheap.
  Prediction: +2.0c. Universe: fixed, picked on returns. Prior: low to moderate.
- **F3.** Loser: the same retail longshot buyer as F0, eight minutes out. Prediction: +1.5c. Universe: fixed, picked on returns. Prior:
  low. It buys YES favorites only; the matching NO favorites do not pass in the same search, which is an asymmetry with no stated reason.
- **F4.** As F3. Prediction: +1.5c. Same prior.

**Sample size each needs before a verdict is allowed.** At least **300 entries** of that rule inside the forward window AND entries on at
least **5 separate UTC days** (the project bar). Entries per day on the old data (counts only): F0 49.7, F3 32.7, F4 31.6, F1 26.8,
F2 20.6. At those rates 300 entries take about **6 days (F0), 9.2 (F3), 9.5 (F4), 11.2 (F1) and 14.6 (F2)** of continuous markets, so
all five can be read by about **2026-10-23**. Until then the verdict word for a rule is `NOT_ENOUGH_DATA` and its numbers are printed as
information only, which cannot be used to stop early on a good-looking number or to give up on a bad one. A rule is read once, at the
first run in which it has both 300 entries and 5 days, using every forward market up to that run. Later runs may be printed but cannot
change that verdict.

**Kill criteria (the common bar, same for all five).** `FALSIFIED` unless ALL hold: n at least 300 entries on at least 5 days; mean net
after fees positive with a day clustered z of at least 2.1; positive in BOTH halves of the forward window (split by close time at the
median entry); positive with fees 20% higher. All hold: `NOT_YET_FALSIFIED`, permission to keep testing forward and nothing more.

**Multiplicity, stated now.** Five rules at one-sided z of 2.1 (p about 0.018 each) give about a 9% chance that at least one passes on
luck alone if they were independent; they are not (F3 inside F4, F0 overlapping F3), so the true figure is lower but not 1.8%. One
pass out of five is weak evidence, and only a pass of the same rule on a second, later block would count for more. The four survivors
were also picked from 311 rules after 437 earlier ones, which is why they are tested here and not trusted.

**Information only, decides nothing:** gross cents, win rate against mean price paid, Bitcoin and gold split for F0 and F3/F4, and for
F1 the neighbouring minutes (1 and 3 minutes left) so an artifact at exactly 2 minutes shows up.

**Cost of this idea so far.** No new rule is created, so the count of variants tried does not rise; these are five forward looks at
rules already counted. Nothing may be changed after the first reading of a rule: a changed rule is a new variant and is counted.

**2026-10-08: first reading of the forward check (`python -m scalper.forward`): all five `NOT_ENOUGH_DATA`.** The database was extended with
`python -m scalper.backfill 1`: 43 new settled markets (24 Bitcoin, 19 gold; gold trades fewer hours) closing from 2026-10-07 18:45 to
2026-10-08 00:30 UTC, about a quarter of one day, same schema as before, none without a result. Overlap with W3 (402 markets): 0, by
construction and checked in the run. Entries so far: F0 18, F1 8, F2 2, F3 13, F4 13, on 1 or 2 days, against 300 entries and 5 days
needed. Their means (F0 -2.74c, F1 -11.95c, F2 -1.32c, F3 and F4 -4.44c) are printed by the program as information only and are noise
at these sizes (a single Bitcoin or gold longshot is -10c to -90c); they are neither a kill nor a confirmation and are not to be
read as either. More days needed: about 6 for F0 up to 15 for F2 at the old entry rates, so the rules can be read from about 2026-10-23.
Code `src/scalper/forward.py`, tests in `tests/test_scalper.py`.

**2026-10-08: the OPEN and NOT_RUNNABLE ledger rows reviewed against the data we hold. None can be run today, so none was run and the count
of tries is unchanged by this review.** Held: candles for 11,135 markets, Coinbase minute closes, the H3 `fills` flags, the H5 `mm`
tables and `ob.sqlite` (471 snapshots of 8 markets over 42 minutes on 2026-10-07).

| Row | Can it run today | What it needs |
|---|---|---|
| L4 maker entry when distance says cheap | No | Order books for days, not 42 minutes (the Firestore recorder snapshots, not in this container) |
| L5 quote staleness | No | Book snapshots under 10 seconds apart, for days |
| L6 Bitcoin and gold on the same window | No | Simultaneous books of both series, for days |
| L12 depth imbalance | No | Book depth for days; 471 snapshots cannot show a move within a minute with any power |
| L14 locked or crossed books | No | Simultaneous books under 10 seconds apart. Candle closes of the two sides are not simultaneous and a consistent book has ask plus other-side ask at or above 1 by construction. The goal is "one occurrence a day", which 42 minutes cannot answer |
| L10 release windows | No | A dated release calendar (CPI, jobs, FOMC) with timestamps. I did not write one from memory, since a wrong date would void the test |
| L11 taker flow | No | The trade tape. `tape.py` kept only fill flags for H3's orders, not the trades (about 28 million rows), so the imbalance cannot be rebuilt from the database. It is fetchable from the public API (a window per market, about 76 windows a minute) and is the one row worth building next; it has to be pre-registered with its decile cut and horizon before the fetch |
| L13 volatility surprise | Not run | It is H7 (`FALSIFIED`) cut by volatility, which the ledger itself calls a likely duplicate. Registering it as new would reword a falsified idea |
| L7 volatility regime gate | Not run | "The best variant" does not exist (every hypothesis is `FALSIFIED`; L1 is a different thing, one fixed rule). Regimes by spread and liquidity are already filters in the 729-rule search grammar (spread 1c, 2c, 4c), and F3 versus F4 already shows the spread cut changes nothing. Running regimes across variants would be a new parameter search, which needs the fair-market null and adds its rules to the count |

## Pre-registration: the strategy search, S01 to S42 (fixed 2026-10-08, before any strategy was run)

The owner asked for the search that was run on rules to be run on STRATEGIES: about 50 different mechanisms, all tested the same way, the
best 25 saved, and an honest report of whether any clear the bar. The owner hoped for 5 profitable rule-sets. **Fewer, including none, is a
complete result and nothing here is stretched to reach 5.** Nothing below places an order, and a survivor means permission to test forward,
never "trade this".

**How many, stated now.** 50 ideas were proposed: **42 runnable (S01 to S42)** and **8 NOT_RUNNABLE (N1 to N8)**, which are listed and not run.
A further 10 ideas were thought of and thrown out before listing because their counterparty story rewords a falsified ledger row (R1 to R10
below); they are not run and not counted. I could not find 50 runnable mechanisms that were distinct from the ledger, and I stopped at 42
rather than pad. Of the 42, **5 are adjacent to the open row L13** (makers' volatility estimate is stale: S10, S12, S13, S28, S38, each with a
different trigger) and **1 is a proxy for the open row L11** (S30); they are run, flagged, and share one mechanism cluster.

**What I had seen when this was written (disclosed).** The schema and row counts of `data/book.sqlite`; two whole markets printed to learn what
`volume`, `oi` and `price_c` mean (one Bitcoin market of 2026-10-05 10:30 and one gold market of 2026-10-06 17:00, including their candle paths
and, for the first, its result); the hour-of-day counts of markets; and which consecutive markets are missing. No signal of any strategy below was
computed, and no strategy was run on any window. I also know the README's earlier results (for example that favorites priced 80c to 97c earned
about +0.1c to +1.2c at 5 to 8 minutes left on W0 and W1/W2, and that longshots lose), and W1 and W2 were used by the earlier searches. That
knowledge is why the favorite and underdog strategies below carry a baseline control (K+). No threshold below came from a result.

### Protocol, fixed

- **Data and windows.** `overnight.windows`: W0s (design window), W0h, W1, W2 (out of sample), W3 (everything that closed after 2026-10-05
  15:00 UTC, including the days added on 2026-10-08). **Every strategy is designed on W0s in the sense that its numbers were fixed before any data
  was read and none is estimated from data; W0s results are printed as information and decide nothing.** The out-of-sample windows for every
  strategy are W0h, W1 and W2. No strategy uses W1 or W2 for design. **W3 is locked**: no code path of the search reads it. It is read ONCE, at the
  end, for the strategies that pass the survivor test, and if none does it is not read at all. The code refuses a second read.
- **Clock and fills.** Candle `j` (1 to 15) ends at `open_ts + 60 j`. A signal may use only data with `end_ts <= open_ts + 60 js` (the signal
  candle is `js`). The entry is on candle `je = js + 1`, strictly later than every candle the signal read. YES is bought at that candle's closing ask,
  NO at 1 minus its closing bid (4 places). The quote must pass `valid_quote` (real two sided book, spread 10c or less). Taker fee
  `0.07 p (1 - p)` per contract, unrounded (`scalps.fee`), on every leg; settlement pays no fee. Round trips sell at the exit candle's closing bid of
  the side bought; an exit candle with no usable quote DROPS the trade and the drops are counted. Entry price must lie in **[0.10, 0.90]** unless a
  tighter band is stated (a cost universe: the extremes are the favorite-longshot trades L1 and L3 already measured).
- **No lookahead, enforced in code.** Every feature is read through a view that raises if asked for a candle after the signal candle, a spot minute that
  closes after the signal, or a previous market that had not closed. Nothing is computed from the market's own result or final price. The result of an EARLIER
  market is used only where stated, and only if that market closed at or before the signal candle. Rolling baselines use earlier data only. The
  result of the market traded is read in one function that settles the trade.
- **Unit.** One observation per market. "First qualifying" means the earliest signal candle in the stated range at which the signal holds; if the
  entry quote at the next candle is unusable or out of band the market is simply not traded (no later candle is tried).
- **Tools.** `strategies.py` (features and the 42 specs), `stratsearch.py` (runner, tests, null, output). Spot is Coinbase minute closes, Bitcoin
  only; gold strategies use the stored strike and the market's own quotes. `strike` of the market, `oi`, `volume`, `price_c`, `bid_h`, `ask_l` are
  fields of the stored candles.
- **Signs are fixed by the counterparty story.** The mirror image of a rule is not run (that would be tuning the sign on the data).

### Decision and ranking, fixed

- **K, the kill criterion for every row.** On the pooled out-of-sample entries (W0h + W1 + W2): `FALSIFIED` unless ALL hold: n at least 300; mean net
  positive with a day clustered z (UTC day of close) of at least 2.1; positive in both halves (split at the median close time); positive with fees
  times 1.2 on every leg; AND the survivor test below. **K+, extra for S10, S12, S13, S28, S38 only:** the strategy's pooled mean must also exceed the
  mean of its unconditional baseline (same side rule, band, entry candle and series, no trigger) on the same windows. The baselines are the two
  information cuts "lower priced side in [0.10, 0.40] at candle 8" and "higher priced side in [0.60, 0.90] at candle 8".
- **Survivor test (as in the overnight run).** Mean net after fees positive in EACH of W0h, W1 and W2 with at least 50 entries in each, and pooled day
  clustered z at least 2.5.
- **Verdict words, only these.** `NOT_ENOUGH_DATA` if the pooled out-of-sample n is below 300 (the survivor flag is still printed). `NOT_YET_FALSIFIED` only
  if K, K+ (where it applies) and the survivor test all pass. Everything else `FALSIFIED`. `NOT_RUNNABLE` for N1 to N8. There is no verdict that
  means trade. The table also prints, separately, how many pass the survivor test alone and how many pass the common bar alone.
- **Ranking for the saved 25, fixed now.** Pooled out-of-sample day clustered z, descending (a strategy with fewer than 50 pooled entries ranks last). Ties
  by mean net. The 25 are saved whatever their sign, in `search3/top25.json` with every parameter, and the full table of all 42 in `search3/all42.json`.
- **The fair-market null over all 42 together.** Each strategy gets zero edge at its own decision price: every hold-to-settlement entry wins with
  probability equal to the side's mid at its entry candle, independent draws per entry, per strategy and per repeat; every round trip keeps its real
  entry and exit costs and spreads and has the sign of its realised mid change flipped with probability one half. The survivor test and the common bar
  are applied to every strategy of every repeat. 500 repeats. Reported: the distribution of the best pooled z across the 42, P(null best >= real
  best), P(null survivors >= real survivors), P(null passing K >= real).
- **The deflated bar, stated now.** Best of N crosses z 2.1 by luck somewhere between N = 20 and N = 200. For N = 42 the expected best z of pure noise is
  about sqrt(2 ln 42) = 2.73, and a family wise one sided 5% bar (Sidak) is the z with tail probability 1 - 0.95^(1/42) = 0.00122, about **3.03**. A
  strategy whose pooled out-of-sample z is below 3.03 has not beaten what the best of 42 noise strategies does; passing the survivor test (2.5) is
  permission to test forward and no more. The simulated null's 95th percentile of the best z replaces this estimate in the report.
- **Counting.** Every one of the 42 counts as a variant tried, plus the 2 baseline information cuts. Information splits by series are descriptive,
  feed no verdict and are not counted.

### The strategies

Notation: `mid_j` = (closing bid + closing ask)/2 of candle j; `ask`/`bid` are YES quotes; "lower priced side" is the side with the smaller entry price
(tie: YES). `x` is the stored strike, `r_k = ln(x_k / x_(k-1))` the strike move, which equals the previous market's realised move, and "contiguous"
means consecutive markets of one series 15 minutes apart. `s_k` is the Bitcoin spot close k minutes before the signal, `sigma1` the standard
deviation of the 60 one minute log returns ending at the signal. Prediction is the expected mean net per contract in cents, written before any run; costs
are about 2.4c for a hold at mid prices, 1.8c for the underdog band, 1.6c for the favorite band, 4.5c for a round trip, and the gross edge assumed is
at most +0.5c, so I expect every row to lose. `HS` = hold to settlement. Universe is FIXED for every row (a series or calendar set stated in the row,
never chosen on returns); the entry price band is the only cost based universe.

**A. Cross market (Bitcoin and gold, same window).** Both series must have a market with the same `open_ts`, with usable quotes at the candles used.

| ID | Mechanism and counterparty | Entry (signal at js, trade at js+1) | Exit | Prediction |
|---|---|---|---|---|
| S01 | Gold leads Bitcoin: a macro risk move shows in gold first. Loser: Bitcoin quoters who do not read the gold market. | js 5. d = gold mid_5 - gold mid_1. d >= +0.05 buy Bitcoin YES, d <= -0.05 buy Bitcoin NO | HS | net -2.4c |
| S02 | Bitcoin leads gold, the same factor read the other way. Loser: the thinner gold quoters. | js 5. d = Bitcoin mid_5 - mid_1. d >= +0.05 buy gold YES, d <= -0.05 buy gold NO | HS | net -2.4c |
| S03 | Laggard catch-up: when both move the same way the slower one has not finished. Loser: the slower market's resting quotes. | js 5. dB, dG (mid_5 - mid_1) both >= +0.05: buy YES on the series with the smaller rise (tie Bitcoin). Both <= -0.05: buy NO on the series with the smaller fall | HS | net -2.4c |
| S04 | The last Bitcoin window's outcome carries into gold. Loser: gold makers who open at 50c without it. | js 1. Side = outcome of the Bitcoin market that opened 15 minutes before this window. Trade gold | HS | net -2.4c |
| S05 | The last gold window's outcome carries into Bitcoin. Loser: Bitcoin makers. | js 1. Side = outcome of the gold market that opened 15 minutes earlier. Trade Bitcoin | HS | net -2.4c |

**B. Serial structure (per series, contiguous markets only; both series pooled).**

| ID | Mechanism and counterparty | Entry | Exit | Prediction |
|---|---|---|---|---|
| S06 | Persistence: the strike is a lagging average, so the last window's move leaves drift. Loser: makers who open at 50c. (Adjacent to L8's story; the measure is the realised outcome, not the spot gap.) | js 1. Side = previous market's outcome | HS | net -2.4c |
| S07 | Streak exhaustion: retail extrapolates streaks. Loser: whoever buys the streak side. | js 1. The previous 3 contiguous outcomes identical: buy the opposite side | HS | net -2.4c |
| S08 | Regime majority: a drift regime lasts hours. Loser: makers who treat each window as independent. | js 1. Previous 12 contiguous outcomes: YES count >= 8 buy YES, NO count >= 8 buy NO | HS | net -2.4c |
| S09 | Shock reversal: after a move at least twice the recent typical one, 15 minute moves overshoot. Loser: momentum chasers. | js 1. m = r_N (previous market's move). M = median of the 24 previous absolute moves r_(N-1) back (26 contiguous strikes needed). If abs(m) >= 2 M buy the side opposite to sign(m) | HS | net -2.4c |
| S10 | Surprise clustering (L13-adjacent): an upset marks a volatility burst the next window's quotes do not price. Loser: makers using last window's calm. | js 7. Previous contiguous market's mid_13 >= 0.85 and it resolved NO, or mid_13 <= 0.15 and it resolved YES. Buy the lower priced side if its ask is in [0.10, 0.40] | HS | net -1.8c, K+ vs baseline |
| S11 | Autocorrelation regime: windows alternate between trending and mean reverting and the sign persists. Loser: makers with one fixed view. | js 1. rho = lag 1 correlation of the 24 most recent moves r_(N-23) to r_N (contiguous). rho >= 0.2: side = sign(r_N); rho <= -0.2: side = -sign(r_N) | HS | net -2.4c |

**C. Calendar, fixed by mechanism now (UTC, never from returns).**

| ID | Mechanism and counterparty | Entry | Exit | Prediction |
|---|---|---|---|---|
| S12 | US cash open (L13-adjacent, scheduled): volume and volatility jump at 13:30 and quotes use trailing volatility. Loser: makers pricing the favorite as if calm. | Bitcoin, Mon to Fri, markets opening 13:30, 13:45, 14:00 or 14:15. js 7. Buy the lower priced side if its ask is in [0.10, 0.40] | HS | net -1.8c, K+ |
| S13 | Weekend quiet (L13-adjacent): Bitcoin trades thin and calm on Saturday and Sunday while quotes use a weekday volatility. Loser: makers who overstate the underdog. | Bitcoin, Saturday and Sunday, all markets. js 7. Buy the higher priced side if its ask is in [0.60, 0.90] | HS | net -1.6c, K+ |
| S14 | Gold reopen gap fade: a gap across the daily break is partly filled. Loser: retail chasing the gap. | Gold, a market whose previous gold market opened 45 minutes or more earlier. js 1. g = ln(x_N / x_previous). abs(g) >= 0.0005: buy the side opposite to sign(g) | HS | net -2.4c |
| S15 | London open breakout: stop orders sit beyond the Asian range. Loser: sellers fading the break. | Both series, markets opening 07:00 to 09:45. A = max and min of that series' strikes for the markets opening 00:00 to 06:45 the same UTC date (at least 20 of 28 present). js 1. x_N above A.max buy YES, below A.min buy NO | HS | net -2.4c |

**D. Bitcoin spot path shape (Bitcoin only; needs the Coinbase minutes).**

| ID | Mechanism and counterparty | Entry | Exit | Prediction |
|---|---|---|---|---|
| S16 | Acceleration: price processes extrapolate velocity, not acceleration. Loser: makers pricing a linear drift. | js 6. ra = ln(s_0/s_3), rb = ln(s_3/s_6). Same sign, abs(ra) >= 1.5 abs(rb), abs(ra) >= 0.75 sigma1 sqrt(3): side = sign(ra) | HS | net -2.4c |
| S17 | Large move fade: a 5 minute move over 2 sigma is partly liquidity. Loser: those who buy the spike. | js 7. r5 = ln(s_0/s_5). abs(r5) >= 2 sigma1 sqrt(5): buy the side opposite sign(r5) | HS | net -2.4c |
| S18 | Stretch from the hour's mean reverts. Loser: late trend buyers. | js 8. z = ln(s_0 / mean(s_0..s_59)) / (sigma1 sqrt(20)). abs(z) >= 1.5: buy opposite sign(z) | HS | net -2.4c |
| S19 | Compression breakout: a quiet 20 minutes ends with a directional break. Loser: range traders. | js 6. range20 = (max - min of s_0..s_19)/s_0 at or below the 25th percentile of range20 over the previous 10,080 minutes (at least 5,000 present). s_0 = max of s_0..s_19: YES. s_0 = min: NO | HS | net -2.4c |
| S20 | Multi scale trend agreement: when 5, 15 and 60 minute trends agree, the trend is robust. Loser: makers using one horizon. | js 8. r5, r15, r60 = ln(s_0/s_5), ln(s_0/s_15), ln(s_0/s_60) all the same sign and abs(r60) >= 0.5 sigma1 sqrt(60): side = that sign | HS | net -2.4c |
| S21 | Jump reversal: a 3 sigma one minute jump is a liquidity event that retraces. Loser: those who trade the print. | js 7. Largest abs 1 minute return r* of the last 10 minutes; sigma_b = std of the 60 one minute returns of minutes 11 to 70 before the signal. abs(r*) >= 3 sigma_b: buy the side opposite sign(r*) | HS | net -2.4c |
| S22 | Capitulation bounce: a 1% drawdown that prints a 15 minute low flushes leveraged longs (and the mirror at highs). Loser: the forced sellers. | js 8. Spot at or below 99% of its 180 minute high and s_0 = min(s_0..s_14): YES. Spot at or above 101% of its 180 minute low and s_0 = max(s_0..s_14): NO | HS | net -2.4c |
| S23 | Run exhaustion: five same sign one minute returns in a row. Loser: those who chase the run. | js 7. Count of consecutive same sign nonzero one minute returns ending now >= 5: buy the opposite side | HS | net -2.4c |
| S24 | Prior day extreme rejection: resting orders sit at yesterday's high and low. Loser: breakout buyers. | js 6. Previous UTC day's high and low of spot closes. s_0 within 0.10% below the high: NO. Within 0.10% above the low: YES | HS | net -2.4c |
| S25 | Minute autocorrelation regime: bounce and trend regimes alternate. Loser: makers with one view. | js 7. rho = lag 1 correlation of the 60 one minute returns. r3 = ln(s_0/s_3) with abs(r3) >= 0.5 sigma1 sqrt(3). rho >= 0.15: side = sign(r3). rho <= -0.15: side = -sign(r3) | HS | net -2.4c |
| S26 | Hourly open anchor: algorithms and traders anchor to the hour's open, so a stretch from it partly reverts. Loser: late trend buyers within the hour. | Bitcoin markets opening at minute :15, :30 or :45. js 7. H0 = spot close at the top of that hour; m = minutes from the top of the hour to the signal; z = ln(s_0 / H0) / (sigma1 sqrt(m)). abs(z) >= 1.5: buy the side opposite sign(z) | HS | net -2.4c |

**E. The market's own price path (both series).**

| ID | Mechanism and counterparty | Entry | Exit | Prediction |
|---|---|---|---|---|
| S27 | Spike fade scalp: a one minute mid jump of 12c overshoots and retraces. Loser: the taker who paid the jump. | First js in 3..10 with abs(mid_js - mid_(js-1)) >= 0.12: buy the side opposite the move | Sell 3 candles after entry at the bid | net -4.5c |
| S28 | Choppy market underdog (L13-adjacent, own path): a mid that crossed 50c three times is noisy and its current leader is overpriced. Loser: whoever pays up for the latest lead. | js 9. Number of sign changes of (mid - 0.5) over the valid mids of candles 1..9 >= 3. Buy the lower priced side if its ask is in [0.10, 0.40] | HS | net -1.8c, K+ |
| S29 | Wick rejection scalp: an intra minute spike that closed 10c back marks absorbed flow. Loser: the stops and takers at the extreme. | First js in 3..10: bid_h - bid_c >= 0.10 and bid_c in [0.15, 0.85]: buy NO. ask_c - ask_l >= 0.10 and ask_c in [0.15, 0.85]: buy YES (both: skip) | Sell 3 candles after entry at the bid | net -4.5c |
| S30 | Flow proxy (L11 proxy, candle level only): the last trade price against the mid shows which side is paying the spread. Loser: slow quoters facing informed takers. | js 6. Mean of (price_c - mid) over candles 4..6 with a usable quote and a trade (at least 2). >= +0.01: YES. <= -0.01: NO | HS | net -2.4c |
| S31 | Dwell reversion: a market that spent 70% of its life on one side and dipped is a dip in a persistent state. Loser: sellers of the dip. | js 10. At least 8 valid mids in 1..10, share above 0.5 at least 0.7 and mid_10 < 0.5: YES. Share at most 0.3 and mid_10 > 0.5: NO | HS | net -2.4c |
| S32 | One sided quote pull: a maker who pulls only one side fears a move that way. Loser: the unpulled side's takers. | First js in 3..10: the bid fell by 0.03 or more from the previous candle while the ask did not fall by more than 0.01: buy NO. The ask rose by 0.03 or more while the bid did not rise by more than 0.01: buy YES | HS | net -2.4c |
| S33 | Market price compression breakout: a mid that sat in a tight range then breaks. Loser: the range's fading takers. | js 9. At least 6 valid mids in 2..8 with max - min <= 0.08. mid_9 > max + 0.03: YES. mid_9 < min - 0.03: NO | HS | net -2.4c |

**F. Spread, volume and open interest.**

| ID | Mechanism and counterparty | Entry | Exit | Prediction |
|---|---|---|---|---|
| S34 | Spread shock: makers widen before a move they fear. Loser: the quoter who stays tight. | First js in 4..10: spread_js >= 0.03 and >= 3 times the median spread of the valid candles 2..js-1 (at least 3); abs(mid_js - mid_(js-2)) >= 0.03: side = sign of that change | HS | net -2.4c |
| S35 | Volume surge follow-through: a move on 3 times the usual volume carries information. Loser: slow quoters. | First js in 5..11: vol_js >= 3 x mean vol of candles 2..js-1 (at least 3), abs(mid_js - mid_(js-1)) >= 0.04: side = direction of the move | HS | net -2.4c |
| S36 | New money continuation: open interest rising with price means new positions, not covering. Loser: slow quoters. | js 8. oi_8 / oi_5 - 1 >= 0.10: mid_8 - mid_5 >= 0.05 YES, <= -0.05 NO | HS | net -2.4c |
| S37 | Thin move reversion scalp: a jump on under half the usual volume is not information. Loser: the taker who paid it. | First js in 4..10: abs(mid_js - mid_(js-1)) >= 0.08 and vol_js <= 0.5 x mean vol of candles 2..js-1 (at least 3): buy the opposite side | Sell 3 candles after entry at the bid | net -4.5c |
| S38 | Volume event underdog (L13-adjacent): a market with unusual volume is an event the stale volatility misprices. Loser: makers pricing the favorite as calm. | js 7. Total volume of candles 1..7 at or above the 90th percentile of the same sum over the previous 96 markets of the series (at least 48). Buy the lower priced side if its ask is in [0.10, 0.40] | HS | net -1.8c, K+ |
| S39 | Opening burst lean: heavy first minute volume is informed flow that the quote has not finished absorbing. Loser: the quoter at the open. | js 1. vol_1 at or above the 90th percentile of the previous 96 markets' vol_1 (at least 48); valid quote at candle 1: mid_1 >= 0.55 YES, mid_1 <= 0.45 NO | HS | net -2.4c |

**G. Strike relative, from the stored strikes (both series).**

| ID | Mechanism and counterparty | Entry | Exit | Prediction |
|---|---|---|---|---|
| S40 | Channel extreme fade: when the strike is the highest of the last 4 hours, up bettors are crowded. Loser: breakout buyers. | js 1. With 15 contiguous previous strikes: x_N above all of them: NO. Below all: YES | HS | net -2.4c |
| S41 | Efficiency ratio trend: a clean 2 hour trend persists. Loser: makers with no trend term. | js 1. 8 contiguous steps. ER = abs(x_N - x_(N-8)) / sum of abs steps >= 0.6: side = sign(x_N - x_(N-8)) | HS | net -2.4c |
| S42 | Common factor trend: when Bitcoin and gold both moved the same way over the last hour the factor persists. Loser: makers who read each alone. | js 1. Both series' 4 step strike returns (x_N / x_(N-4)) have the same nonzero sign: buy that side on each series (two trades) | HS | net -2.4c |

**NOT_RUNNABLE, listed and not run (no simulator, nothing recorded).**

| ID | Idea | What it needs |
|---|---|---|
| N1 | Book depth imbalance predicts the next move (L12) | Depth for days; 471 snapshots only |
| N2 | True taker flow from the trade tape (L11) | The tape; only fill flags are stored |
| N3 | Release windows (CPI, jobs, FOMC) (L10) | A dated calendar; not written from memory |
| N4 | Maker entry that rests only when distance says cheap (L4, L5) | Order books under 10 seconds for days |
| N5 | Sub minute index lag | A BRTI feed |
| N6 | CME gap fill for Bitcoin | CME futures closes |
| N7 | Implied volatility regime gate | Options implied volatility |
| N8 | Cross venue prediction market gaps | Other venues' prices |

**Thought of and thrown out as rewordings of falsified rows (not run, not counted).** R1 fade of the opening move (the mirror of M1, whose mid drifted
WITH the move). R2 drift of the mid between open and a fixed minute held to settlement (M1's information row). R3 the sign of spot minus strike at the
open or at 6 minutes (L8, H7). R4 spot leading the Kalshi mid (the lag study found none). R5 gating favorites by realised spot volatility (H7 cut by
volatility). R6 any price band by minutes left, or a side selector (L1, L3 and the grammar search). R7 buy cheap and sell at a target (H2, H4). R8
the mirror sign of any rule above. R9 resting orders (H3, H5). R10 stop losses (standing exclusion).

Verdicts are recorded below when the one run has happened. No threshold, minute, band or sign changes after seeing a number. A strategy changed after
the run is contaminated, says so, and is a new variant that counts.

**2026-10-08: the strategy search, run once (`python3 -m scalper.stratsearch null 500`, code commit 45632fe, output in `search3/`): no survivor. Nothing clears
the survivor test, nothing clears the common bar, and the best z of the 42 is +1.17.** The pre-registered protocol above was followed without
change: designed on W0s (printed as information only), judged on W0h, W1 and W2 pooled, W3 untouched. No threshold, minute, band, sign or ranking rule was changed
after seeing a number. A smoke run that printed only signal and trade COUNTS on W0s (no outcomes) preceded it, to catch crashes. The real run printed once and the table below is that print.

- **Headline.** 0 of 42 pass the survivor test (every out of sample window positive with at least 50 entries and pooled z of at least 2.5). 0 of 42 pass the
  common bar (n of at least 300, z of at least 2.1, both halves positive, fees x1.2 positive). 0 are `NOT_YET_FALSIFIED`. 26 are `FALSIFIED` and 16
  are `NOT_ENOUGH_DATA` (pooled out of sample entries under 300; they are not crossed off, they are too thin to judge). The owner hoped for 5; the honest count is 0,
  and nothing was stretched to reach it. The best strategy by the pre-set ranking has z of +1.17, below even the 2.1 bar.
- **What the average strategy did.** Over the 41,569 hold-to-settlement entries across the 39 hold strategies the mean gross was -0.17c and the mean net -1.66c, so
  costs (fee plus the spread paid at the ask) were about 1.5c a contract and the signals added nothing on average. The 3 round trips (S27, S29, S37; 11,743
  entries) had gross -1.18c and net -3.76c: the spike and wick fades lose about their two fees and two spreads and a little more. Net z of S27 and S29 is -14 and -16.
- **Cost is still the binding constraint.** 9 of 42 pooled means are positive (S22, S24, S19, S30, S23, S15, S16, S35, S33) and every one of them has fewer than 300
  entries or z under 1.5; the largest, S15 with 300 entries, is +0.68c at z of +0.29. The strategies with enough entries to see a 1c to 2c edge (S06, S04, S42, S36)
  are all negative.
- **The top of the ranking is small samples.** S22 (capitulation bounce) is first with +7.27c on 55 entries and z of +1.17: positive in W0h and W2 and negative in W1
  (-4.24c on 16 entries). S19 (compression breakout) had the best design window z of any strategy (+3.11 on 77 entries in W0s, which decides nothing) and fell to +2.30c, z of
  +0.86 out of sample, with W1 +7.11c and W2 -6.02c. That is what selection from a window looks like; no strategy was selected, so it is the same effect appearing without a
  selector: with 42 independent looks at tiny samples, some will be large and of either sign.
- **The valid fair market null over all 42 together (500 repeats, each entry given zero edge at its own decision price, independent draws, same survivor test).** The
  best pooled z across the 42 has median +1.31, 95th percentile +2.41, maximum +4.27. **P(null best >= real best) =
  0.596**: the real best is no better than the best of 42 strategies that have zero edge and pay these costs. The null produced
  0.014 survivors per repeat on average (0.030 passes of the common bar), so a survivor here would have been unusual; there was none.
- **The deflated bar for N = 42, stated before the run: best of N crosses z of 2.1 by luck.** Expected best z of pure noise 2.73 (sqrt(2 ln 42)); family wise
  one sided 5% (Sidak) bar 3.03. The simulated null, which includes the costs every strategy pays, gives a lower 95th percentile (2.41) because most strategies
  have a negative mean before any luck. The real best (+1.17) is under all three. A strategy would have needed z of about 3.0 pooled out of sample to be distinguishable
  from the best of 42.
- **Power, so FALSIFIED is read correctly.** The large strategies (n above 2,000) have a standard error of about 0.5c, so an edge over about 1.5c would have shown; those with 300
  entries have a standard error of about 2c to 2.5c, so only an edge over about 6c would. 16 strategies have under 300 out of sample entries (S14 has 11, S33 has 29, S17 has 56) and say
  `NOT_ENOUGH_DATA`: this search does not cross them off. Small samples come from narrow triggers on 69 days, not from a rule that was loosened.
- **The locked window.** No strategy passed the survivor test, so W3 (closes after 2026-10-05 15:00 UTC, 445 markets) was NOT read, and `stratsearch w3` refuses to run without a survivor.
  W3 is still locked for whatever is tested next.
- **Ledger effects.** L11 stays `OPEN`: S30 is only a candle level proxy for taker flow (last trade against mid) and it did not clear anything; the real tape is not held. L13 is not marked
  `FALSIFIED` by this, since its own wording (H7 cut by volatility) was not run, but five other triggers for the same stale volatility story did not clear the bar: S13 weekend quiet,
  S28 choppy price path and S38 volume event are `FALSIFIED`; S10 upset in the previous window and S12 US cash open are `NOT_ENOUGH_DATA` (133 and 61 entries) and both are below
  their baselines. K+ held for S13 (-0.03c against an unconditional baseline of -0.46c) and S38 (-2.42c against -2.98c), both negative and both far inside noise. The two baseline
  information cuts (the lower priced side in 10c to 40c and the higher priced side in 60c to 90c, at candle 8, all markets) were run and are counted; they lost 2.98c and 0.46c.
- **What could not be run.** N1 to N8 (book depth, the trade tape, a release calendar, resting order strategies, a sub minute index feed, CME closes, implied volatility, other venues).
  No gold spot exists here, so the spot strategies (S16 to S26) trade Bitcoin only; the gold strategies use gold's stored strikes and quotes.
- **Caveats.** One sample of 69 days and one regime. W1 and W2 were used by the earlier searches, so they are out of sample for these strategies' design but not unseen by the project.
  Strikes are the stored strikes, the spot is Coinbase and not the settlement index, and fills are at the candle's closing quote (the real order could fill worse). A pass would only have been
  permission to test forward.

Full table, in the pre-set ranking order (pooled out of sample = W0h + W1 + W2; per window columns are n / mean net; the survivor flag was false for all 42):

| Rank | ID | Strategy | n | Mean net | z | W0h | W1 | W2 | Fees x1.2 | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | S22 | Capitulation bounce | 55 | +7.27c | +1.17 | 17 / +10.20c | 16 / -4.24c | 22 / +13.38c | +7.03c | `NOT_ENOUGH_DATA` |
| 2 | S24 | Prior day extreme rejection | 91 | +2.87c | +0.87 | 9 / -18.30c | 53 / +4.93c | 29 / +5.68c | +2.61c | `NOT_ENOUGH_DATA` |
| 3 | S19 | Compression breakout | 214 | +2.30c | +0.86 | 55 / +5.80c | 86 / +7.11c | 73 / -6.02c | +2.04c | `NOT_ENOUGH_DATA` |
| 4 | S30 | Last trade flow proxy (L11 proxy) | 158 | +1.18c | +0.38 | 54 / +5.53c | 49 / +2.55c | 55 / -4.32c | +0.90c | `NOT_ENOUGH_DATA` |
| 5 | S23 | Run exhaustion | 117 | +1.25c | +0.36 | 39 / +6.79c | 43 / -2.31c | 35 / -0.54c | +1.02c | `NOT_ENOUGH_DATA` |
| 6 | S15 | London open breakout of the Asian range | 300 | +0.68c | +0.29 | 70 / -0.85c | 102 / +0.37c | 128 / +1.76c | +0.36c | `FALSIFIED` |
| 7 | S16 | Acceleration | 286 | +0.63c | +0.27 | 80 / -0.40c | 109 / +6.54c | 97 / -5.15c | +0.41c | `NOT_ENOUGH_DATA` |
| 8 | S35 | Volume surge follow-through | 283 | +0.04c | +0.02 | 85 / +3.07c | 96 / -1.17c | 102 / -1.36c | -0.23c | `NOT_ENOUGH_DATA` |
| 9 | S13 | Weekend quiet favorite (L13 adjacent) | 793 | -0.03c | -0.02 | 184 / +3.03c | 307 / -2.52c | 302 / +0.64c | -0.28c | `FALSIFIED` |
| 10 | S03 | Laggard catch-up | 1143 | -0.27c | -0.20 | 341 / +0.26c | 387 / +3.19c | 415 / -3.92c | -0.54c | `FALSIFIED` |
| 11 | S17 | Large 5 minute move fade | 56 | -1.11c | -0.21 | 16 / +7.14c | 21 / -8.24c | 19 / -0.19c | -1.32c | `NOT_ENOUGH_DATA` |
| 12 | S05 | Previous gold outcome carries into Bitcoin | 2904 | -0.22c | -0.33 | 887 / +0.64c | 979 / +0.06c | 1038 / -1.24c | -0.54c | `FALSIFIED` |
| 13 | S02 | Bitcoin leads gold | 2202 | -0.80c | -0.69 | 673 / -2.23c | 742 / -0.32c | 787 / -0.04c | -1.08c | `FALSIFIED` |
| 14 | S20 | Multi scale trend agreement | 676 | -1.42c | -0.77 | 184 / -0.09c | 244 / -0.21c | 248 / -3.60c | -1.67c | `FALSIFIED` |
| 15 | S21 | Jump reversal | 314 | -2.00c | -0.84 | 88 / -2.33c | 124 / +1.50c | 102 / -5.97c | -2.26c | `FALSIFIED` |
| 16 | S31 | Dwell reversion | 494 | -1.82c | -1.05 | 131 / +0.95c | 183 / -4.92c | 180 / -0.70c | -2.10c | `FALSIFIED` |
| 17 | S36 | Open interest new money | 3159 | -0.80c | -1.05 | 922 / +1.29c | 1112 / -0.70c | 1125 / -2.63c | -1.06c | `FALSIFIED` |
| 18 | S12 | US cash open underdog (L13 adjacent) | 61 | -5.42c | -1.08 | 18 / -10.40c | 22 / +1.38c | 21 / -8.27c | -5.66c | `NOT_ENOUGH_DATA` |
| 19 | S18 | Stretch from the hour's mean fade | 140 | -3.76c | -1.09 | 40 / -1.42c | 54 / +1.87c | 46 / -12.41c | -4.01c | `NOT_ENOUGH_DATA` |
| 20 | S40 | Four hour channel extreme fade | 1625 | -1.20c | -1.13 | 455 / +1.62c | 556 / -1.99c | 614 / -2.58c | -1.52c | `FALSIFIED` |
| 21 | S09 | Shock reversal | 1409 | -1.84c | -1.48 | 403 / -0.10c | 493 / -4.10c | 513 / -1.03c | -2.15c | `FALSIFIED` |
| 22 | S38 | Volume event underdog (L13 adjacent) | 506 | -2.42c | -1.51 | 145 / -2.76c | 189 / -2.51c | 172 / -2.02c | -2.66c | `FALSIFIED` |
| 23 | S01 | Gold leads Bitcoin | 2153 | -1.54c | -1.57 | 683 / -1.31c | 729 / +1.62c | 741 / -4.87c | -1.82c | `FALSIFIED` |
| 24 | S25 | Minute autocorrelation regime | 502 | -3.76c | -1.62 | 122 / -8.82c | 202 / -2.52c | 178 / -1.70c | -4.03c | `FALSIFIED` |
| 25 | S07 | Streak exhaustion | 1671 | -1.98c | -1.77 | 483 / +0.46c | 589 / -3.14c | 599 / -2.80c | -2.30c | `FALSIFIED` |
| 26 | S41 | Efficiency ratio trend | 1145 | -3.12c | -2.03 | 323 / -5.23c | 415 / -4.46c | 407 / -0.09c | -3.44c | `FALSIFIED` |
| 27 | S42 | Common factor trend | 3330 | -1.98c | -2.05 | 1060 / -3.38c | 1097 / -1.71c | 1173 / -0.98c | -2.30c | `FALSIFIED` |
| 28 | S28 | Choppy market underdog (L13 adjacent) | 611 | -3.17c | -2.06 | 195 / -6.21c | 208 / -1.28c | 208 / -2.21c | -3.43c | `FALSIFIED` |
| 29 | S34 | Spread shock | 56 | -10.04c | -2.17 | 14 / -26.41c | 18 / -13.24c | 24 / +1.90c | -10.31c | `NOT_ENOUGH_DATA` |
| 30 | S26 | Hourly open anchor | 202 | -6.87c | -2.21 | 58 / -3.19c | 71 / -11.18c | 73 / -5.60c | -7.12c | `NOT_ENOUGH_DATA` |
| 31 | S11 | Autocorrelation regime of strike moves | 2073 | -2.44c | -2.21 | 602 / -2.67c | 667 / -0.61c | 804 / -3.79c | -2.76c | `FALSIFIED` |
| 32 | S06 | Outcome persistence | 6805 | -1.17c | -2.26 | 1978 / -1.34c | 2333 / -0.85c | 2494 / -1.33c | -1.48c | `FALSIFIED` |
| 33 | S10 | Surprise clustering (L13 adjacent) | 133 | -7.55c | -2.58 | 39 / -4.56c | 49 / -6.78c | 45 / -10.99c | -7.80c | `NOT_ENOUGH_DATA` |
| 34 | S04 | Previous Bitcoin outcome carries into gold | 2875 | -2.60c | -2.64 | 882 / -0.90c | 972 / -5.05c | 1021 / -1.72c | -2.91c | `FALSIFIED` |
| 35 | S39 | Opening burst lean | 612 | -5.47c | -2.74 | 181 / -4.43c | 197 / -6.26c | 234 / -5.62c | -5.77c | `FALSIFIED` |
| 36 | S37 | Thin move reversion scalp | 371 | -2.69c | -2.78 | 141 / -0.83c | 140 / -4.51c | 90 / -2.75c | -3.15c | `FALSIFIED` |
| 37 | S08 | Regime majority | 2343 | -3.74c | -3.91 | 676 / -5.41c | 802 / -4.46c | 865 / -1.77c | -4.06c | `FALSIFIED` |
| 38 | S27 | Spike fade scalp | 5247 | -3.96c | -14.10 | 1522 / -4.17c | 1816 / -3.32c | 1909 / -4.41c | -4.47c | `FALSIFIED` |
| 39 | S29 | Wick rejection scalp | 6125 | -3.64c | -16.35 | 1794 / -3.43c | 2101 / -4.03c | 2230 / -3.45c | -4.18c | `FALSIFIED` |
| 40 | S33 | Market price compression breakout | 29 | +11.40c | +1.46 | 9 / +15.55c | 9 / +9.58c | 11 / +9.50c | +11.14c | `NOT_ENOUGH_DATA` |
| 41 | S32 | One sided quote pull | 32 | -9.61c | -1.13 | 7 / -25.85c | 12 / -1.18c | 13 / -8.64c | -9.87c | `NOT_ENOUGH_DATA` |
| 42 | S14 | Gold reopen gap fade | 11 | -13.08c | -0.81 | 2 / -54.56c | 3 / +36.62c | 6 / -24.10c | -13.39c | `NOT_ENOUGH_DATA` |

Files: `search3/all42.json` (all 42 with every parameter and every window), `search3/top25.json` (the 25 best by the pre-set ranking, saved whatever their sign),
`search3/null.json`, `search3/run_output.txt` (the printed run).

**Strategy variants tried so far: 792 as of 2026-10-08.** That is 742 before this search (13 hypotheses with a verdict, from the 60s scalp to L9, plus 729 rules from the two
parameter searches, as restated on branch `claude/research-forward-check`), plus M1 and its 5 information cuts (branch `claude/research-early-momentum`), plus the 42 strategies of this search, plus its
2 baseline information cuts. The forward check and early momentum branches named here have since been merged into `main`; this line is their union with this search; the line at the top of this file is updated to match. All are `FALSIFIED` or
`NOT_ENOUGH_DATA`; the forward check of L1 and the four overnight survivors is still open.

## The size ladder for L1 (written 2026-10-08, before the evidence exists)

Written now so that raising the size is never decided in the moment after a good week. It is a commitment device: the owner can change it, but a
change is a dated edit here, made before the size changes, never after.

**Where it stands.** L1 trades 1 to 3 contracts (size scaling, 2% of cash per order, cap 3), stop 10% of the starting cash on the bot's own
trades. The evidence is one pre-registered rule that failed its own 30 day test (z 1.45 against 2.1), replicated on older data it had not seen
(+1.10c per contract, z +2.68), +0.96c over 69 days with an uncertainty of about 0.44c, and a short live record (13 settled wins and no
losses at the time of writing, which says almost nothing). Simulations on its own history: at the measured edge a 30 day month loses money 12%
of the time at any size, and 28% of the time if the true edge is half as large.

**Step 1, cap 3 to cap 5.** All of these, read once each, in this order:
1. The forward check of L1 (rule F0) has at least 300 entries on at least 5 separate days that closed after 2026-10-07 18:30 UTC (earliest read
   about 2026-10-23), day clustered z at least 2.1, both halves positive, positive with fees x1.2. Verdict `NOT_YET_FALSIFIED` is the most it can say.
2. The live record has at least 100 settled bot trades, at least one of them a loss (a record with no loss is not evidence about the loss), and a
   settled bot P/L at or above zero.
3. The account is at least $250, so five contracts (about $4.60) are under 2% of it.
4. No session ended on its loss stop in the last 7 days.

**Step 2, cap 5 to cap 8.** A second forward read on a fresh set of at least 300 entries on at least 5 further days that also clears step 1's test
in item 1, at least 300 settled live trades, at least $400 in the account, and no loss-stop ending in the last 14 days.

**Step down.** Back to 1 contract, and the cap stays there until the owner re-reads this section, if any of these happens: the forward check
returns `FALSIFIED` (z at or below -2.1 on at least 300 entries), two sessions end on their loss stop within 7 days, or the bot's settled live
P/L is below -2% of the starting balance.

**Never.** Never raise the size on a winning streak (a streak of wins is the normal state of a rule that wins 94% of the time and loses 92c
when it does not). Never loosen the stop and raise the size in the same change. Never skip a step. A step is a pull request that pastes the
evidence it relies on, and the verdict words stay `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. The stop follows the high point only when
the session was started with that option; the ladder does not require it.

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

## Pre-registration: M1, early window momentum (fixed 2026-10-08, before any code or any signal value was computed)

Only the schema was inspected before this was written: candle `end_ts` is exactly `open_ts + 60k`, and the database holds 11,135
settled markets (6,456 KXBTC15M, 4,679 KXGOLD15M) from 2026-08-01 to 2026-10-07. No price, signal or outcome was looked at. This is
the same data every earlier test used, so a pass could only ever be permission to test forward. One hypothesis against the bar:
13 tried before, 14 after, plus the information cuts below.

- **Universe, fixed, not selected on returns or cost.** Every settled market of both series in the database (result `yes` or `no`),
  both series pooled. Series split printed for information only.
- **Signal.** YES mid = (bid close + ask close) / 2 of a candle. `D` = YES mid of the candle ending `open_ts + 300` (the close of the
  5th minute) minus YES mid of the candle ending `open_ts + 60` (the close of the 1st minute). `D >= +0.05` is UP, `D <= -0.05` is
  DOWN, otherwise no trade. One observation per market. Both signal candles must have a usable quote (`valid_quote`: real two sided
  book, spread 10c or less). A market whose first minute still shows an empty book has no signal; this is a no-signal count and is
  printed, not a drop. (Using the empty book's 50c mid would invent a move.)
- **Entry.** The candle ending `open_ts + 360`, the NEXT candle after the signal candle, so strictly later than every bar the signal
  used. UP buys YES at that candle's ask close; DOWN buys NO at `1 - YES bid close` (snapped to 4 places). That candle must have a
  usable quote, else there is no fill and the market is counted as "no entry quote". Taker fee `0.07 * p * (1 - p)` per contract,
  unrounded (the repo's `scalps.fee`), as in H2 and L1 to L3.
- **Exit.** Sell exactly 3 minutes after entry, at the candle ending `open_ts + 540`, at that side's bid (YES: YES bid close; NO:
  `1 - YES ask close`). A taker fee on the exit leg as well, as in H2 (the 4c to 5c round trip in the prediction includes both legs).
  If that candle is missing or has no usable two sided quote, the observation is DROPPED and counted, with the direction and the entry
  price of the dropped ones printed, because the drop is not random: after a continuation to an extreme the winning side's book
  empties at the top (ask above 99.9c), and after a collapse the losing side's bid is at 0.1c. Both ends of the distribution are
  exactly the ones that go missing, so the surviving mean is conditioned on the price staying in the middle, which biases it toward
  zero and cuts its variance. The direction of the net bias is not known in advance and is reported, not assumed away.
- **Counterparty.** Slow quoters or resting orders that under-react to early flow in the first minutes of a market, so the move
  continues for a few minutes after it is visible. Whoever is on the other side of our entry is quoting a price that has not yet
  absorbed the first five minutes of information.
- **Numeric prediction, stated before the run.** Average gross continuation over the 3 minute hold (exit mid minus entry mid in the
  direction of the trade) of about +1c, against a round trip cost near 4c to 5c (about 2c of spread crossed at each end combined
  plus about 3.5c of fees at mid prices). Expected net about -3c to -4c a trade. **The pre-registered expectation is that the test is
  `FALSIFIED`.** The earlier lag study found no one minute lag, and H2 (a continuation bet) lost twice its costs.
- **Kill criteria, the common bar.** `FALSIFIED` unless ALL hold: n of at least 300 markets with a completed round trip; mean net
  positive with a day clustered z (by UTC day of close) of at least 2.1; positive in BOTH halves (split by close time at the median
  of the entries); positive with fees times 1.2 (on both legs). Fewer than 300 is `NOT_ENOUGH_DATA`. Best outcome is
  `NOT_YET_FALSIFIED`, meaning permission to test on unseen data, never evidence of an edge. There is no verdict that means trade.
- **Fair-market null control, same rule.** (a) Hold-to-settlement version: each entered market wins with probability equal to the side's
  mid at its entry candle (the price at its own decision point), pays the ask and the fee; 500 repeats; the real hold-to-settlement mean is
  placed against the null's distribution. (b) Round trip version: each trade's realised change in the side's mid from entry to exit has its sign
  flipped with probability one half (keeps the real volatility, spreads and fees, removes any direction), the exit bid is that mid
  less the real exit half spread, clipped to [0.001, 0.999]; 500 repeats; the real round trip mean is placed against it. A real result that is
  not clearly above this null is not an edge.
- **Simulator guard.** A test runs the exact entry and exit code on a simulated fair game (a martingale mid with a fixed spread) and
  requires it to lose about its costs, never to profit.
- **Information only, decides nothing, may NOT be used to rescue the verdict.** The same rule with thresholds 3c and 8c (hold 3), hold 2 and 5
  minutes (threshold 5c), and hold to settlement (threshold 5c, no exit, no exit fee, so no drops). Five cuts, printed in a table labelled
  information only. They count against the bar: 1 hypothesis plus 5 cuts.
- **Cost of this idea so far.** The fourteenth hypothesis tried. Verdict words: `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. No
  threshold, minute, hold or fee changes after seeing the numbers.

**2026-10-08: M1, early window momentum: `FALSIFIED`.** One run of `python -m scalper.momentum` (commit following 0b65d16) under the rule fixed in the M1 section above. Nothing was changed after seeing it.

- **Funnel.** 11,135 settled markets (both series), 69 days. 113 had no usable quote at minute 1 or 5 (no signal), 1,783 moved less than 5c (no trade), 3 had no usable entry quote, 12 were dropped for an unusable exit quote, **9,224 completed round trips**.
- **Result.** Mean net **-2.63c** a trade (gross -0.41c, fees 2.23c, spread crossed 0.95c), day clustered z **-14.66**, first half -2.37c, second half -2.90c, fees x1.2 -3.08c. The bar was positive with z of 2.1 in both halves and under higher fees. Detectable edge at this sample is about 0.5c, so there is no continuation edge anywhere near the cost. Bitcoin -2.07c (5,428), gold -3.44c (3,796); UP -3.12c, DOWN -2.13c (information only).
- **Prediction against outcome.** Predicted continuation of about +1c and net of -3c to -4c. Measured mid continuation was +0.54c and net -2.63c, so the sign and the verdict were right and continuation was smaller than guessed, while the cost was a little lower than guessed (fees 2.2c, not 3.5c, because the entries sit at 71c on average where the fee curve is flatter).
- **Fair-market null.** Round trip with the direction removed (500 repeats): null mean -3.72c (95% interval -4.11 to -3.35); the real -2.63c is above all of it (P null >= real 0.000). Hold to settlement with each entry winning at its own mid: null -1.74c (95% -2.59 to -0.90), real -0.35c, P null >= real 0.002. So there is a small real continuation tendency (mid +0.54c over 3 minutes, and a +0.9c gross edge held to settlement), clearly distinguishable from a fair market, and it is smaller than the cost of trading it. Part of the gap between real and null is that real exits drift toward the extremes where the fee is cheaper, which the sign flipped null does not do. The simulator guard (the exact code on a simulated fair game) loses about 2c of spread plus fees, as required.
- **Drops and bias.** Only 12 of 9,236 entries (0.13%) had an unusable exit quote (9 UP, 3 DOWN, all with an entry price of 50c or more, mean 80c against 71c for the traded). That is the pattern predicted: the exit book empties after a run to an extreme. Even if all 12 had been full dollar winners the mean would move by 0.13c at most, against -2.63c and a standard error of 0.18c, so the drops cannot change the verdict.
- **Information only (decides nothing, not used to rescue anything).**

| Variant | n | Gross | Net | z | 1st half | 2nd half | Fees x1.2 |
|---|---|---|---|---|---|---|---|
| threshold 3c, hold 3 | 9,994 | -0.47c | -2.73c | -15.07 | -2.38c | -3.08c | -3.19c |
| threshold 8c, hold 3 | 8,094 | -0.34c | -2.50c | -13.02 | -2.29c | -2.71c | -2.93c |
| threshold 5c, hold 2 | 9,233 | -0.68c | -3.00c | -19.93 | -2.81c | -3.20c | -3.47c |
| threshold 5c, hold 5 | 9,206 | +0.04c | -1.97c | -7.59 | -1.84c | -2.09c | -2.37c |
| threshold 5c, hold to settlement | 9,236 | +0.88c | -0.35c | -0.80 | +0.02c | -0.72c | -0.60c |

  Longer holds lose less, and settlement is the least bad at z of -0.80, which is still negative after fees and fails the bar. That is a pattern read off an information table, and it is not a hypothesis: acting on it would need a new pre-registration and unseen data.
- **What it does not say.** One signal definition (minute 5 against minute 1 mid), minute quotes only, taker entry and exit. A resting entry, an earlier or later signal, or trade tape flow are different hypotheses. Same 69 days as most earlier tests, so even a pass would only have been permission to test forward.

Strategy variants tried so far: 14 hypotheses (the 60s scalp, H1 to H7, L1, L2, L3, L8, L9, M1), all `FALSIFIED`, plus two parameter searches, and 5 information cuts for M1 counted against the bar.

## Pre-registration: L1 in the 90c to 95c band, and resting-limit entries for L1 (fixed 2026-10-08 02:50 UTC, before any code, and before any data after this time exists)

Why this exists. L1 holds every position to settlement, so the entry price and the fee are the whole trade. Two ways to improve the
entry were proposed. Both are written down now so that every market that closes after the timestamp above is untouched test data.

**What was observed post hoc, and is therefore NOT evidence for either idea.** In the 3,400 L1 entries over 69 days, split by price
after the result was known: 88c to 90c n=518 gross +0.35c net -0.36c; 90c to 92c n=877 gross +1.89c net +1.30c; 92c to 95c n=1,119
gross +2.37c net +1.94c; 95c to 97c n=886 gross +0.44c net +0.17c. The bands were chosen by looking at those numbers. The per band
uncertainty is 0.6c to 1.3c, so the gaps between bands are not clearly more than noise. These 69 days can never count toward the
band variant, and no band edge was moved after seeing them.

### P1: L1 restricted to the 90c to 95c band

- **Rule.** Exactly L1 (about 6 minutes before close, buy the side priced at touch in the window, hold to settlement, taker fee
  `0.07 * p * (1 - p)` per contract), but only entries whose touch price is at least 90.0c and at most 95.0c. No other change.
- **Universe, fixed.** Every L1 signal in both series on markets that close after 2026-10-08 02:50 UTC. Selected on price, which is
  observable before the trade, not on returns. The comparison rule, L1 over its full 88c to 97c band, is computed on the same markets.
- **Counterparty.** Whoever sells the favourite at 90c to 95c a few minutes from close, or buys the other side, is paying for a small
  chance of a reversal. The edge exists only if that chance is priced a little too high. Same story as L1, not a new mechanism.
  Below 90c the tick is 1c so the price is coarse, and above 95c the possible gain is under 5c against a fee that does not shrink as fast.
- **Numeric prediction, stated before the run.** Net about +1.0c a contract, deliberately below the +1.66c seen post hoc because a
  band picked after looking is expected to shrink. Expected entries: about 29 a day, so 300 entries in about 10 days. If the full band
  L1 comes in near +0.96c, then this variant is predicted to be no better than L1 by more than its noise, and the pre-registered
  expectation is that the band split does not survive.
- **Kill criteria, the common bar.** `FALSIFIED` unless ALL hold: n of at least 300 entries on at least 5 different days; mean net
  positive with a day clustered z (by UTC day of close) of at least 2.1; positive in both halves split by close time at the median;
  positive with fees times 1.2. Fewer than 300 entries is `NOT_ENOUGH_DATA`. Additionally the variant must beat L1's full band on the
  same markets by a positive margin in the same data, otherwise the band adds nothing and is `FALSIFIED` as an improvement. Best
  outcome is `NOT_YET_FALSIFIED`, which is permission to keep testing, never a verdict that means size up.
- **Fair-market null.** Each entry wins with probability equal to its own touch price at its decision point, pays the ask and the fee;
  500 repeats; the real mean is placed against that distribution and must be clearly above it.
- **Live implication.** None. The live bot keeps its 88c to 97c band. Narrowing it live would also be a change of order flow and fill
  rate (fewer orders, and the 88c to 90c zone is where most live misses happened), so it needs this result first and a separate "merge".

### P2: resting-limit entries (maker) for L1 signals

Status: **`NOT_RUNNABLE` today and not recorded as a try.** The one-minute candles cannot say whether a resting order would have been
reached or where it would have stood in the queue. Fabricating a fill model on candles is the exact failure this directory exists to
prevent. It becomes runnable only on order book snapshots from the recorder (every 10 s, three levels), which started saving on
2026-10-08, and only on markets closing after the timestamp above.

- **Rule once runnable.** At an L1 signal (touch price 90c to 97c), instead of crossing, rest a buy for the favourite side one tick
  below the touch, for the rest of the 330 to 400 second window (the order is cancelled at its end), then count a fill only under the
  strictly-through model: a later snapshot shows the opposite side's best price at or through our limit (the ask at or below our bid
  limit), and at least one snapshot later than the one that showed it before any fill is counted (no same snapshot fills). Queue
  position is assumed to be the back of the visible size at our price. The fee schedule for a resting fill must be read from
  docs.kalshi.com on the day of the run and written here first; no maker fee is assumed in this note.
- **Counterparty.** An impatient seller of the favourite who crosses the spread near the close. The danger is adverse selection:
  the sellers who reach our bid are the ones who know the favourite just weakened, so fills concentrate on the losers. The earlier
  crypto maker test in `shwoopnet` showed exactly this: the skipped signals averaged more than the filled ones.
- **Numeric prediction, stated before any book data is read.** Fill rate 30% to 50%. Net per FILLED contract higher than the taker
  entry by about the saved tick and fee (about +0.8c), but win rate of the filled set lower than the missed set. Net per SIGNAL
  (unfilled counted as zero) at or below the taker entry. **The pre-registered expectation is `FALSIFIED`.**
- **Kill criteria.** `FALSIFIED` unless ALL hold: at least 300 signals with a determinable outcome on at least 5 days; net per
  signal (unfilled at zero) exceeds the taker entry on the same signals with a day clustered z of at least 2.1 on the difference;
  positive in both halves; positive with fees times 1.2; and the outcome of the unfilled signals is reported next to the filled ones
  in every table. A profit factor that improves while the fill rate collapses is not a result. Fewer than 300 is `NOT_ENOUGH_DATA`.
- **Live implication.** None. The order code uses IOC at the touch by design (a resting order that is never cancelled is exposure
  nobody is watching). A resting entry would be a new order type with a cancel path, and is out of scope until this passes.

### Not pre-registered, written down only so they are not found later by looking

Entry time inside the 330 to 400 second window; skipping a side or series with a wide spread or thin visible size; sizing larger
inside a band that has passed. Each needs its own section here, with its prediction and kill criteria, before any data is read for it.
Nothing about them has been computed.

### Count

P1 is one more variant against the bar: **793** as of 2026-10-08 (792 before, plus P1). P2 is not counted until it runs.
The fourteen hypotheses before it, and the 729 rules and 42 strategies searched, remain `FALSIFIED` or `NOT_ENOUGH_DATA`.

## Pre-registration: the four slot search, BTC and gold each in an early and a late window (fixed 2026-10-08 02:50 UTC, before any code or any result)

The owner asked to use the markets harder: one rule per series per window, so four live slots (Bitcoin early, Bitcoin late, gold early,
gold late), each acting once per market. This is a search over rules for each slot, run with the protections of the first rule search
(`search.py`) and a stricter pass mark because there are now four searches and a hundred holdout reads. It is a parameter search, so it
can never produce a verdict that means trade. Nothing below has been run. The only things looked at before writing this are the table
names of the database and the existing `search.py`.

- **Slots, fixed.** *Early*: the decision is read at 14, 13, 12, 11 or 10 minutes left (minutes 1 to 5 of the market). *Late*: 6, 5, 4,
  3, 2 or 1 minutes left (the last 6 minutes, the window L1 sits in). Each slot is one series, so a slot rule never trades the other
  series and never trades in the other window. A market can therefore have up to two entries (one early, one late), and the two
  windows never overlap in time.
- **Grammar.** The same as `search.py` (price band from the fixed edges, side either/yes/no, optional spread filter, optional move
  filter over 1, 3 or 5 minutes) with the minute drawn from the slot's own list and the series filter removed (the slot sets it). One
  new filter, `pair`: the other series' market that closes at the same time, at the same minute, has a valid quote, and its YES mid
  is at least 5c above 50c ("other up") or at least 5c below ("other down"); the rule requires the other market to point the same
  way as the side bought (`agree`) or the opposite way (`disagree`). A slot rule with a `pair` filter and no other-series quote has no
  entry. No filter reads a result. No hour of the day is a filter. Hold to settlement only, taker at the ask, fee `0.07 * p * (1 - p)`.
- **Counterparty, stated once for the family.** For the early slot: whoever quotes the first minutes of a market before the price has
  absorbed what the underlying already did. For the late slot: the same longshot-holder story as L1. For `pair`: a market that has
  not yet repriced for what the other market is already saying. No new mechanism is claimed, and a rule is not described as having an
  edge because it ranks first.
- **Search protocol, per slot.** Seed 11, 3 cycles of 50 fresh rules, 50 more fresh rules, and 50 one-filter mutants of the top 50
  (as in `search.py`), top 25 kept per round, at least 100 entries to be ranked, ranking by day clustered z of net profit per contract.
  Only the first half of the days (by day count) is read while searching. The second half is the locked holdout, read once, for the
  final 25 of each slot. For the late slots the rule L1 as live (6 minutes left, either side, 0.88 to 0.97, no filter) is scored
  as an extra information row and is not part of the ranking.
- **Control.** For every slot, the identical pipeline on the fair-market copy of its data (each result drawn from the market's own
  last price), same seed. The best z the control finds is printed beside the real best.
- **Every rule counts.** Distinct rules evaluated in the REAL runs of all four slots are added to the tally of variants tried
  (792 before P1, 793 with P1, plus the four-slot total printed by the run). The floor for a search window z is `sqrt(2 ln N)` with N
  the slot's own count. Control runs are not counted.
- **Numeric prediction, stated before the run.** In every slot the best search-window z lands within 0.5 of the control's best and
  near the floor (about 3.3 to 3.5), and the holdout of the final 25 shows a mean net below zero, as in the first search (6 of 25
  positive, mean -1.85c). **The pre-registered expectation is that all four slots are `FALSIFIED`.** If any slot shows more than 6
  of 25 rules positive on its holdout, that is reported as an anomaly, not as a finding.
- **Pass mark, fixed.** A rule is `NOT_YET_FALSIFIED` only if ALL hold: its search window z is above both the floor and the control's best
  for its slot; on the holdout it has at least 300 entries, mean net positive, day clustered z of at least **3.0** (the null
  expectation of the best of the 100 holdout reads across 4 slots, `sqrt(2 ln 100)`, so ordinary luck cannot pass), both holdout
  halves positive, and positive with fees times 1.2. A holdout with fewer than 300 entries is `NOT_ENOUGH_DATA` for that rule. Anything
  else is `FALSIFIED`. A pass is permission to run a forward test on days not yet seen, written here before it starts, and never a reason
  to change the live bot. The data is the same 69 days as every earlier test (the last half of them is not new to the project, only
  new to these rules), so a pass could never be more than that.
- **Mixing.** If at least one rule in each of two slots passes, the combination is evaluated once on the holdout as a portfolio (one entry
  per slot per market, equal size) and reported with the same measures. If fewer than two slots have a passing rule there is nothing to
  mix and none is run. No other combination is looked at.
- **Live implication.** None from this section. Four slots would need a separate order id per slot (today the id is `L1-<ticker>`, one order per
  market), a per slot stop, and the size ladder; none of that is built or proposed until a rule passes forward.

**2026-10-08: the four slot search: all four slots `FALSIFIED`, no rule passes.** One run of `python -m scalper.slots` (seed 11, 3 cycles per slot) under the section above. Nothing was changed after seeing it. 11,130 markets, search window 5,546, holdout 5,584 read once. Full rows in `search4/slots.json`.

| Slot | Rules | Best search z, real | Best search z, control | Floor | Holdout of final 25: positive | Control rules on a fair holdout | Mean net on holdout | Passes |
|---|---|---|---|---|---|---|---|---|
| Bitcoin early | 439 | 3.51 | 1.71 | 3.49 | 7 | 7 | -1.58c | 0 |
| Bitcoin late | 440 | 2.65 | 4.14 | 3.49 | 9 | 12 | -0.52c | 0 |
| gold early | 441 | 1.99 | 3.34 | 3.49 | 7 | 2 | -0.79c | 0 |
| gold late | 440 | 2.60 | 2.16 | 3.49 | 7 | 7 | -1.30c | 0 |

- **Prediction against outcome.** Predicted: every slot `FALSIFIED`, best search z near the control and the floor, holdout mean below zero, no more than 6 of 25 positive. Measured: all four `FALSIFIED`, holdout means all negative. Two slots had 7 of 25 positive and one 9 of 25, against the 6 predicted; the control produced 7, 12 and 7 in the same slots, so this is the size of luck in this pipeline, and it is reported as the anomaly the section said to report, not as a finding. Gold early's 7 against the control's 2 is the one gap worth a sentence: none of those 7 had 300 holdout entries (all `NOT_ENOUGH_DATA`).
- **Bitcoin early is the only slot whose real best (3.51) is above its floor (3.49) and well above its control (1.71).** It did not survive: the best rule (12 minutes left, either side priced 0.70 to 0.90, spread 2c or less) was +1.06c on 1,081 holdout entries with z of 0.77. A search window z at the floor that fades to 0.77 is what selection looks like.
- **Best holdout rows.** Bitcoin late: 2 minutes left, priced 0.10 to 0.20, spread 2c or less, +5.79c on 353 entries, z 2.39, below the 3.0 mark and a longshot band in which the fair-market control also scores high. Gold early: 10 minutes left, 0.90 to 0.97, price moved toward the side by 2c over 3 minutes, other market agrees, +3.23c on only 101 entries (z 1.94): `NOT_ENOUGH_DATA`, and it is the only `pair` rule that came near the top. Gold late: +2.92c on 265 entries (z 1.30).
- **L1 as live, per slot, information only.** Bitcoin late: search +0.53c (z 0.96), holdout +0.68c (z 0.70). Gold late: search +1.95c (z 2.59), holdout +0.97c (z 1.30). Positive in both halves for both series, and in both series the holdout is smaller than the search window, which is the same drift the forward check was built to watch. Neither series on its own clears z 2.1 on the holdout.
- **Mixing.** Fewer than two slots had a passing rule, so no combination was evaluated, as the section said.
- **What this does and does not say.** This grammar (one price band, one side, up to three filters, hold to settlement, taker at the ask), in these windows, on 69 days, finds nothing a fair market does not also produce. It does not say a different shape, such as a resting order or a sized ladder, has no edge. The `pair` filter (the other series pointing the same way) produced no top rule in either late slot.
- **Count.** 1,760 distinct rules evaluated in the real runs. **Strategy variants tried so far: 2,553 as of 2026-10-08** (793 including P1, plus these 1,760). The line at the top of this file is updated. All `FALSIFIED` or `NOT_ENOUGH_DATA`.

## Pre-registration: three more forward looks, F5 to F7, and a power table (fixed 2026-10-08 02:51 UTC, before any of them was run on any market)

The slot search found nothing new, and the strategy space already written down is close to exhausted: L3 covers 2 minute favorites up to 98c
(`-1.71c`), S06 and S07 cover the previous result and streaks, S01 to S05 cover the other series, R10 puts stop losses outside the program.
So the useful overnight work is making the ideas that are still alive testable on clean data, not adding rules. Three forward looks are
added to `forward.py`. Each is a subset or a variant of L1 that was named after seeing the 69 day numbers, so none of the 69 days counts for
them. Their window is markets that **close after 2026-10-08 02:50 UTC** (close_ts above 1791427800), the moment P1 was written.

| Name | Definition | Why it is here |
|---|---|---|
| F5 = P1 | L1 (6 minutes left, taker at the ask, hold) with the touch price 0.90 to 0.95 only, both series | The band split in the P1 section. |
| F6 | L1 over its full band, gold only | Gold late looked better than Bitcoin late in the slot search (+1.95c vs +0.53c in the search window, +0.97c vs +0.68c on the holdout). Named after seeing that. |
| F7 | L1 over its full band, Bitcoin only | The other half of that split, so F6 cannot be reported without it. |

- **Counterparty.** The same as L1 for all three: the buyer of the cheap side of an almost decided market. No new mechanism.
- **Numeric prediction, stated before the run.** F5 +1.0c (below the +1.66c seen post hoc); F6 +0.8c and F7 +0.8c, that is, the series split is
  not expected to matter, and the expectation is that the two are within one standard error of each other. If F6 beats F7 by more than
  its standard error on 300 entries each, that is reported, but a difference between two halves chosen after seeing a difference is not
  a finding.
- **Sample size and kill criteria.** The common bar and nothing looser: at least 300 entries on at least 5 UTC days, mean net positive with a
  day clustered z of at least 2.1, positive in both halves of the window by close time, positive with fees times 1.2. Fewer than 300 or
  5 days is `NOT_ENOUGH_DATA` and the numbers are information only. Each rule is read once, at the first run in which it has both, using
  every market since the cutoff. F6 and F7 are two tests on one population and F5 is nested inside L1's population, so the true number of
  independent tests is smaller than three, but each is counted.
- **Order of reading.** F5 may only be called `NOT_YET_FALSIFIED` if it also exceeds F0 (full band L1) on the same markets, as in P1. F6 and
  F7 are judged on their own and, if both pass, the series split is not a finding.
- **Count.** F6 and F7 are two more variants. **Strategy variants tried so far: 2,555 as of 2026-10-08** (2,553 plus F6 and F7; F5 is P1,
  already counted).
- **Power table (information only, decides nothing, not a hypothesis).** `python -m scalper.power` resamples the 69 days of L1 entries by day
  (a bootstrap over days, so the clustering is kept) and reports, for a true edge equal to what was measured and for half of it, how
  often a forward sample of N entries clears z of 2.1, so that the wait for the bar is known before it is felt. It reads no forward data.

**2026-10-08: the power table (`python -m scalper.power`, 1,000 resamples per cell).** L1: 3,400 entries over 69 days, 49.3 a day, measured mean net +0.96c.

| Forward entries (days at 49 a day) | Pass rate if the edge is the measured +0.96c | If half of it | If zero (false pass) |
|---|---|---|---|
| 300 (6.6) | 21.4% | 12.2% | 7.1% |
| 600 (12.7) | 25.6% | 13.2% | 5.7% |
| 1,000 (20.8) | 33.8% | 14.3% | 4.5% |
| 2,000 (41.1) | 52.8% | 18.2% | 2.7% |

- **What it says.** The bar is deliberately hard to pass, and a +0.96c edge on a 5c to 12c risk per contract has a per entry standard deviation of about 0.3 dollars, so even a real edge of exactly the measured size is read as `NOT_YET_FALSIFIED` only one time in five at 300 entries and one time in two at 2,000 entries. The "both halves positive" and "fees x1.2" conditions are not in this table, so the true pass rates are lower still.
- **What it does not say.** A failed reading at 300 entries is weak evidence against L1, not strong evidence: with a real +0.96c edge it fails 79% of the time. Equally a pass is weak evidence for it. The false pass rate at 300 entries (7.1%) is above the nominal 1.8% because 6.6 days is few clusters for a z statistic.
- **Consequence for the size ladder.** The ladder's first step asks for a pass on 300 entries and 5 days. That gate will usually not be met even if L1 works, so a ladder that waits for it waits for luck. Whether to read the first step at 1,000 entries (about three weeks, 34% power at the measured edge) instead is a decision for the owner, to be written down before the data is read; this note changes nothing by itself.

## Amendment to P2 (fixed 2026-10-08 02:56 UTC, before any resting-order simulation was run on any book)

Two facts changed after P2 was written, both disclosed here before use.

1. **Data source.** `scalper.recorder` (read only, public endpoints, no key) is now running in the research container, writing the top
   five levels of both series' open markets to `data/ob.sqlite` every 10 seconds, started 2026-10-08 02:52 UTC for 10 hours. P2 may use
   these snapshots as well as the Firestore recorder's. Only markets that close after 03:00 UTC count (so every window is fully recorded); the 471 older snapshots (42 minutes,
   2026-10-07) never count. A snapshot is a separate view of the book every 10 seconds, so a resting order whose price was crossed for
   less than 10 seconds can be missed. That biases fills DOWN, which is the conservative direction for a maker test.
2. **Maker fee.** The series endpoint reports `fee_type: quadratic, fee_multiplier: 1` for both series, which fits the taker formula used
   everywhere here. I could not find a maker rate in the pages I could fetch (docs.kalshi.com fee rounding says only that the fee accumulator
   carries across taker and maker fills), and I will not write one from memory. So the pre-set verdict is judged with the **maker fee set
   equal to the taker fee**, `0.07 * p * (1 - p)` per contract. Any saving from a lower maker rate is printed as a separate information
   line with 0 and 0.0175 coefficients, and cannot create a pass. The only thing a pass can then come from is the entry price.
- Everything else in P2 stands: back of the visible queue at our price, a fill only on a LATER snapshot whose opposite side's best price is at or
  through our limit, the window is the 330 to 400 seconds before close, the outcome of unfilled signals is reported next to the filled
  ones, kill criteria and 300 signals on 5 days unchanged. At 10 hours of recording there will be far fewer than 300 signals, so the
  result will be `NOT_ENOUGH_DATA` and printed as information only.

**2026-10-08: P2 simulator built (`python -m scalper.bookmaker`), not yet run on a settled market.** Code and tests exist before any result: the signal is the first snapshot 330 to 400 s before close with a side's ask at 0.90 to 0.97; the limit is one tick below that ask (0.1c above 90c, 1c at or below); a fill needs a LATER snapshot inside the window whose own side's ask is strictly below the limit. One deliberate departure from the P2 wording, in the conservative direction: P2 said "at or through"; the verdict counts only STRICTLY through, because a touch at our price says nothing about our place in the queue (H3's rule), and the touch rate is printed as a separate information column. The maker fee in the verdict equals the taker fee; coefficients 0 and 0.0175 are information only. A planted adverse selection test (every filled order loses, every missed one wins) must come out `FALSIFIED` with maker per signal below taker, and it does. At 10 hours of recording the result will be `NOT_ENOUGH_DATA` and printed as information only.

## Pre-registration: three filters on L1, Q1 to Q3 (fixed 2026-10-08 03:12 UTC, before any code or any filtered result)

The slot search tried rules from a grammar. This is the other direction: take the one rule that has held up best, L1, and ask whether a stated
reason to distrust some of its entries removes the bad ones. Each filter is one fixed definition, with no threshold searched. The only things
looked at before writing this are `distance.py` (H7's spot distance code, reused as is) and the table layout of the database.

**Base.** L1 as `lstrats.hold_rule(L1)`: the candle ending 6 minutes before the close, the favourite whose ask is 0.88 to 0.97, taker at the ask,
fee `0.07 * p * (1 - p)`, held to settlement. Both series unless stated. All 69 days. Every one of these days has been seen by L1 itself, so a
pass could only ever be permission to test forward on days not yet seen, written down before it starts.

| Name | Arm (entries kept) | Complement (entries removed) | Excluded from both and counted |
|---|---|---|---|
| Q1 spot support | Bitcoin only. `z = ln(spot / strike) / (sigma * sqrt(6))` exactly as `distance.z_score` at the decision minute; the arm is YES with `z >= +1.0` or NO with `z <= -1.0` | Bitcoin entries with a `z` that does not support the side | Entries with no `z` (missing spot or strike); gold entirely |
| Q2 previous result | The previous market of the same series (it closed exactly 900 s earlier) resolved to the side bought | Resolved to the other side | Entries with no previous market in the data |
| Q3 other series agrees | The other series' market with the same close time, at the same candle, has a valid quote with mid at least 5c on the side bought's side of 50c | Mid at least 5c on the opposite side | Twin missing, no valid quote, or mid within 5c of 50c |

- **Counterparty, per filter.** Q1: the longshot buyer on the other side is least wrong when spot sits close to the strike and most wrong when it sits
  a full sigma away, so entries with spot support should keep the edge and the rest should not. Q2 and Q3: the opposing buyer is more likely
  to be wrong when the recent market or the other market is pointing the same way as the favourite. Q2 is adjacent to S06 (outcome persistence,
  `FALSIFIED`): S06 asked whether the previous result predicts the next one, Q2 asks whether it improves the odds only on entries already priced 88c to 97c.
- **Numeric prediction, stated before the run.** Q1: arm net about +1.2c a contract on about 700 entries, complement about 0c; arm and
  complement differ by about 1c. Q2: arm and complement within 0.5c of each other (S06 found no persistence). Q3: the same, within 0.5c. **The
  pre-registered expectation is that none of the three passes**: the arms hold 500 to 1,700 entries, where one standard error is 0.7c to 1.3c.
- **Pass mark, fixed.** Three filters are tried, so the arm's day clustered z must be at least **2.4** (the one sided level for three tries at 5%),
  not 2.1. A filter is `NOT_YET_FALSIFIED` only if ALL hold: at least 300 arm entries on at least 5 days; arm mean net positive with day clustered
  z of at least 2.4; both halves of the arm positive (split by close time at the median); positive with fees times 1.2; the arm's mean exceeds the
  complement's, with the day clustered z of the per day difference at least 2.0; and the arm's real mean sits above the 95th percentile of the
  fair-market null (500 repeats; each arm entry wins with probability equal to its own ask, pays the ask and the fee). Fewer than 300 arm
  entries is `NOT_ENOUGH_DATA`. Anything else is `FALSIFIED`.
- **Information only, no verdict, may not rescue anything.** The base L1 on the same markets; each arm's price mix and its Bitcoin and gold split;
  Q1 at `K = 0.5` and `K = 2.0`. Those two extra thresholds are printed to show how steady the result is and are counted as tries.
- **Count.** Q1, Q2 and Q3 are three variants and the two extra Q1 thresholds are two more: **2,560** as of 2026-10-08 (2,555 plus five).

**2026-10-08: Q1 to Q3: all three `FALSIFIED`.** One run of `python -m scalper.filters` under the section above (commit after the pre-registration and the tests). Nothing was changed after seeing it. Base L1: 3,400 entries, +0.96c, z +2.71, 69 days.

| Filter | Arm n | Arm net | z | Halves | Fees x1.2 | Complement n / net | Arm minus complement (z) | Fair market 95th pct | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Q1 spot support (Bitcoin) | 1,653 | +0.86c | +1.43 | +0.63c / +1.08c | +0.77c | 331 / -0.64c | +1.16c (+0.64) | +0.55c | `FALSIFIED` |
| Q2 previous result agrees | 1,694 | +0.49c | +1.03 | +1.10c / -0.12c | +0.40c | 1,698 / +1.41c | -0.83c (-1.00) | +0.61c | `FALSIFIED` |
| Q3 other series agrees | 1,653 | +0.87c | +1.70 | +1.09c / +0.64c | +0.77c | 992 / +1.14c | -0.45c (-0.43) | +0.56c | `FALSIFIED` |
| Q1 at K=0.5 (information) | 1,967 | +0.58c | +1.02 | | | 17 / +4.02c | | | `FALSIFIED` |
| Q1 at K=2.0 (information) | 317 | +0.33c | +0.24 | | | 1,667 / +0.66c | | | `FALSIFIED` |

- **Prediction against outcome.** Predicted: none passes. Right on the verdicts. Q1 was predicted at about +1.2c with a difference of about 1c; it
  measured +0.86c with a difference of +1.16c, the right sign and size but nowhere near the z of 2.4 or the 2.0 on the difference (arm and
  complement have 1,653 and 331 entries). Q2 and Q3 were predicted within 0.5c of their complements; Q2 came out 0.83c BELOW it and Q3 0.45c below.
- **What it says.** The Bitcoin entries that spot does not support lost 0.64c a contract and those it does support made 0.86c, which is the shape
  the mechanism predicts, but the gap is inside its noise (z +0.64), and K=2.0 (the strongest support) is the weakest arm (+0.33c), the opposite
  of a dose response. So there is no evidence that the spot filter removes the bad L1 entries. Entries where the previous market agreed with the
  favourite did worse than those where it did not (Q2). That is a pattern read off an information table (z -1.00); acting on it would need
  its own pre-registration and unseen data, and it is consistent with S06/S07 finding no useful persistence either way.
- **Count.** Five variants (Q1 to Q3 and the two Q1 thresholds): **2,560 as of 2026-10-08** (2,555 plus 5). The top line of this file is updated.

## Pre-registration: a forward look at the Q2 complement, F8 (fixed 2026-10-08 03:13 UTC, before it was run on any market after 03:25)

Q2 was `FALSIFIED` as registered (the previous result AGREEING with the favourite). Its table also showed the complement, entries where the previous
market in the same series resolved to the OTHER side, at +1.41c on 1,698 entries against +0.49c for the agreeing half. That was seen after the
fact, so the 69 days cannot count for it. It is registered here as a forward look only, so that days after this time are clean.

- **F8.** L1 (6 minutes left, 0.88 to 0.97, taker at the ask, hold) restricted to entries whose side differs from the result of the previous market in
  the same series (it closed exactly 900 s earlier). Entries with no previous market are excluded and counted. Markets that close after
  **2026-10-08 03:25:00 UTC** (close_ts above 1791429900) only.
- **Counterparty.** The same longshot buyer as L1. The only new claim is a mean reverting residue after a result in the opposite direction; it is
  adjacent to S07 (streak exhaustion, `FALSIFIED`) and is not expected to be a separate mechanism.
- **Numeric prediction, stated before the run.** +0.9c a contract, below the +1.41c seen post hoc. **The pre-registered expectation is that it does
  not pass**: the two halves of Q2 differ by 0.9c with a day clustered z of -1.00, so a regression to the L1 average (+0.96c) is the likeliest outcome.
- **Kill criteria, the common bar.** At least 300 entries on at least 5 days; mean net positive with day clustered z at least 2.1; both halves
  positive; positive with fees times 1.2; and the mean exceeds F0's mean on the same markets. Fewer than 300 is `NOT_ENOUGH_DATA`.
  About 25 entries a day, so 300 entries need about 12 days.
- **Count.** One more variant: **2,561 as of 2026-10-08**.

## Cost model check: fee rounding per order (2026-10-08, information only, no hypothesis, no verdict)

Every backtest in this file charges the fee as `0.07 * p * (1 - p)` per contract, unrounded (`scalps.fee`). Kalshi's fee-rounding page
(docs.kalshi.com, getting started, "Fee Rounding", fetched 2026-10-08) says a non-direct member's balance moves in whole cents, and the exchange
charges a rounding fee to restore that: a fill's trade fee is rounded up to $0.000001, then the balance change is floored to the cent, and the
difference is the rounding fee. For a buy that means the order costs `ceil_to_the_cent(count * (price + fee))`. The fee accumulator only
refunds rounding across several fills of one order, so a single fill gets none back. `fees.py` already had a cent-rounded per-order fee and the
backtests did not use it.

`python -m scalper.feerounding` prices L1's 3,400 entries both ways (cents per contract, hold to settlement):

| Contracts per order | Unrounded fee (every table above) | Cent-rounded order | Difference | Fee per contract, rounded |
|---|---|---|---|---|
| 1 | +0.96c | **+0.49c** | -0.48c | 0.95c |
| 2 | +0.96c | **+0.70c** | -0.26c | 0.73c |
| 3 | +0.96c | **+0.79c** | -0.17c | 0.64c |
| 4 | +0.96c | +0.85c | -0.11c | 0.58c |
| 5 | +0.96c | +0.86c | -0.11c | 0.58c |

- **What it says.** If this is how the account is charged, a one contract L1 order has been earning about half of what the backtests say, and the
  live bot's two contracts earn about 0.7c, not 0.96c. Larger orders lose less to rounding, which is an argument for fewer, larger orders over many
  one contract ones (but it does not change the ladder: size is still earned by the forward check, not by this).
- **What is not established.** The page describes the rule; it does not say which kind of member this account is. A direct member rounds to
  $0.0001 and would pay almost exactly the unrounded fee. The P/L shown on the Kalshi page cannot tell the two apart (it displays whole cents).
  The order diagnostics export now carries `avgFee` (the fee Kalshi charged, per the order response, on branch `claude/diag-fee`), so one paste of
  real orders settles it: a one contract order at about 92c charging 0.01 means non-direct; 0.0052 means direct.
- **Effect on the forward checks.** `forward.py`, `filters.py` and the rest still use the unrounded fee, so their nets are the optimistic column. The
  bar's "fees times 1.2" stress is not the same thing as this (1.2 times 0.47c is 0.56c; the one contract rounding adds 0.48c). If the account is
  non-direct, a pass of a forward check at the unrounded fee should be re-read at the rounded cost for the order size actually used before
  anything is sized up. Nothing was changed in the existing code or the pre-set bars.

By price band (information only, the same post hoc bands as P1, so the same caution applies), net per contract, cents:

| Band | n | Unrounded fee | 1 contract, rounded | 2 contracts, rounded | 3 contracts, rounded |
|---|---|---|---|---|---|
| 88c to 90c | 518 | -0.36 | -0.65 | -0.65 | -0.65 |
| 90c to 92c | 877 | +1.30 | +0.83 | +1.01 | +1.17 |
| 92c to 95c | 1,119 | +1.94 | +1.42 | +1.70 | +1.76 |
| 95c to 97c | 886 | +0.17 | -0.37 | -0.08 | +0.03 |

Read with the rounding in mind, the 95c to 97c band is about zero after costs even at three contracts, and the 88c to 90c band loses at any size. That does
not change P1 (which is still to be judged on days after 02:50 UTC with its pre-set bar), but if P1 passes its forward look, the rounded cost is the
number to size it on.

## Book study, night of 2026-10-08, information only

First look at the order book recorder (`scalper.recorder`, top five levels, about every 10 s). No hypothesis, no verdict, nothing here decides anything.

- **How little data this is.** The recorder runs only while a command is active in the research container; between turns the container idles and the process
  stops. It wrote 02:52 to 03:20 UTC and then, in foreground chunks, about 05:30 to 07:00 UTC: 18 distinct markets (9 Bitcoin, 9 gold) and 49
  snapshots inside the 330 to 400 s L1 window with a side priced 0.88 to 0.97. The Firestore recorder (a scheduled Firebase function) is the only
  source that runs unattended; this container's copy cannot give days of data.
- **Ask persistence in the L1 window (37 consecutive pairs, 10 s apart, both series).** The favourite's ask at the next snapshot: up 62.2%,
  the same 5.4%, down 32.4%. Median spread 0.1c, median size at the touch 1,006 contracts. With n=37 the up share has a wide margin (roughly
  47% to 78%), but the direction fits the live no-fills: a favourite's ask tends to creep up as the close approaches, so an IOC at a touch read a
  second or more earlier can be left behind by one tick.
- **P2 on the 6 signals it found (3 filled).** Fill rate 50% (strictly through and touch-counted agree). On the filled ones the resting entry earned
  +5.80c against +5.70c taking the same signals; the missed signals earned +6.61c taken. Per signal, unfilled counted as zero: maker +2.90c, taker +6.16c.
  Six signals say nothing; the shape, however, is the one P2 predicted (the missed ones are not worse than the filled ones, so the resting entry gives
  up winners). The verdict is `NOT_ENOUGH_DATA`.
- **Not computed.** Spread and touch size by price band, and how often the touch disappears between snapshots, need hundreds of snapshots per band; there are 49
  in all, so no band has enough to report.
- **What would settle it.** The Firestore recorder's 24 hour download (Kalshi page, "Download book snapshots") has days of snapshots at the same cadence. P2, `obstats`
  and this section should be re-run on that file, not on this one.

## Pre-registration: N1 and N2, H7's distance rule near the settlement boundary (fixed 2026-10-08 07:02 UTC, before any code or result for them)

H7 (spot distance from the strike, in units of typical movement, at 6 minutes left) was `FALSIFIED`. What it did not do is look where distance matters most:
with 2 or 1 minutes left the remaining movement is small, so a spot that sits a fraction of a sigma from the strike is a near certain outcome, and the market's
price (a coin flip to a favourite) may lag. Nothing was run at these times. This is the same machinery and the same rule as H7 at a different decision minute, so it
is one mechanism tried at two times, not a new mechanism.

- **N1:** `distance.py` with the decision at 2 minutes left (`DECISION_LEFT_S = 120`, `MINUTES_LEFT = 2`). **N2:** the same at 1 minute left (60 s, 1). Everything else
  is H7 as coded: Bitcoin only, sigma the standard deviation of the previous 60 one minute log returns, markets ordered by close time, the first half estimates the YES
  share in each z bucket, the second half tests the single fixed rule (buy a side only when the bucket's rate beats the price, the fee and a margin of 2c).
- **Counterparty.** Quoters who do not reprice a near-settled market for the last minute or two of spot movement. **Numeric prediction, stated before the run:** net
  about -1c a contract for both, with 100 to 300 entries in the test half; the fee at prices near 50c is about 1.75c a contract and the information gain is small
  once the market already reflects spot. **The pre-registered expectation is `FALSIFIED` or `NOT_ENOUGH_DATA`.**
- **Kill criteria.** Two tries at the bar: at least 300 entered markets in the test half, mean net positive with a day clustered z of at least **2.4**, both
  halves of the test half positive, positive with fees times 1.2. Fewer than 300 is `NOT_ENOUGH_DATA`. Anything else is `FALSIFIED`. The universe is fixed (every
  Bitcoin market with a usable quote and 61 spot minutes).
- **Count.** Two variants: **2,563 as of 2026-10-08**.

**2026-10-08: N1 and N2: both `FALSIFIED`.** One run of `python -m scalper.boundary` under the section above (after its tests). Nothing changed after seeing it.

| | Bitcoin markets usable | Test half | Entered | Gross | Net | z | Halves | Fees x1.2 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| N1, 2 minutes left | 6,143 | 3,072 | 1,439 | -1.60c | -2.37c | -2.55 | -3.25c / -1.49c | -2.53c | `FALSIFIED` |
| N2, 1 minute left | 4,450 | 2,225 | 906 | -1.55c | -2.31c | -2.36 | -2.38c / -2.24c | -2.47c | `FALSIFIED` |

- **Prediction against outcome.** Predicted about -1c with 100 to 300 entries; measured about -2.3c with 906 to 1,439 entries (more entries than predicted because the rule
  trades whenever a bucket's rate beats the price by the 2c margin). The sign and the verdict were right and the loss was larger. A negative z of -2.5 means the
  estimation half's rates did not hold in the test half: the market's price at 1 to 2 minutes left already reflects spot better than a bucket table built on the
  first half of the days.
- **Count.** Two variants: **2,563 as of 2026-10-08**. The top line of this file is updated.

## Pre-registration: exits for L1, X1 to X4 (fixed 2026-10-08 13:55 UTC, before any code and before any exit was priced on any entry)

The owner asked for an exit strategy backtest, in the light of L1's payoff: about 93c risked to make 7c, so one loss costs about 13 wins. **R10 (stop losses) was a
standing exclusion in the idea ledger, because a stop on a fair market has no edge before costs; it is lifted for this one family at the owner's request**, and it is tested
here as exactly that question: does selling a collapsing favourite early beat holding it to the close, after paying for the exit?

- **Entries (fixed).** Every L1 entry exactly as `lstrats.hold_rule(L1)`: the candle ending 6 minutes before the close, favourite whose ask is 0.88 to 0.97, taker at the
  ask, both series, all 69 days (3,400 entries). The baseline, HOLD, is the same entries held to settlement.
- **The exit rule.** After entry the position is watched at each later candle close: those ending 5, 4, 3, 2 and 1 minutes before the close (strictly later than the entry
  candle). At the first of them where the BID of the side held (YES: the YES bid close; NO: 1 minus the YES ask close) is at or below the threshold `X`, and that bid is a real
  bid (at least 0.1c), the position is sold at that bid. No spread filter: a sale takes whatever the bid is. A taker fee `0.07 * p * (1 - p)` is paid on the exit leg as
  well as the entry leg. If no candle triggers, the position is held to settlement as HOLD. A position is checked at candle closes only (a minute poll), never at an intrabar low.
- **Variants, fixed now, four tries.** `X` = 50c (X1), 60c (X2), 70c (X3), 80c (X4). No other threshold, minute or rule is tried.
- **Counterparty.** The seller who dumps a favourite near the end, or the buyer who takes the other side of a collapse: a favourite whose price has fallen from about 93c to under 70c
  is, on average, already priced as the loser it is about to become, so selling it does not beat holding it before costs. Whoever is buying our early exit is paying its fair price.
- **Numeric prediction, stated before the run.** The exit rule changes the VARIANCE a lot and the MEAN a little, and the mean change is negative: costs of the exit leg (a wide
  bid-side spread on a collapsing book plus a fee) and the winners cut short that would have recovered. Predicted mean difference (exit minus hold, per entry) between -0.2c and
  -1.0c for all four, and the worst single loss per contract falling from about -0.97 to about -0.50 or better at X3 and X4. **The pre-registered expectation is that all four
  are `FALSIFIED` as an improvement in the mean**, with a real reduction in the size of the worst loss as the one thing they buy.
- **Kill criteria.** Four tries, so the bar is stricter: a variant is `NOT_YET_FALSIFIED` only if ALL hold: at least 300 entries on at least 5 days; the mean net per
  entry of the exit rule exceeds HOLD's on the same entries, with a day clustered z of the per day difference of at least **2.5**; the exit rule's own mean is positive; positive in
  BOTH halves of the entries (by close time); positive with fees times 1.2 on both legs; and the difference is above the 95th percentile of the fair-market null (same entries and
  prices, outcomes drawn from the price at 1 minute left, the same exit rule applied, 500 repeats), because the rule would cost roughly that much even in a market with no edge.
  Anything else is `FALSIFIED`. A pass is permission to test forward on days not yet seen, and never a reason to change the live bot.
- **Reported beside the verdict, information only, may not rescue anything.** For HOLD and each variant: mean, standard deviation, worst single loss per contract, worst day, deepest
  drawdown of the running total, share of entries stopped, and of those stopped how many would have won if held (the winners the rule cuts). The cent-rounded cost for two
  contracts (each leg rounds up to a cent, so an exit costs about a cent more than the model).
- **Count.** Four variants: **2,567 as of 2026-10-08** (2,563 plus four).

**2026-10-08: X1 to X4: all four `FALSIFIED` as an improvement in the mean.** One run of `python -m scalper.exits` (after its tests). Nothing changed after seeing it. 3,422 L1 entries (the database gained 22 markets since the 3,400 quoted elsewhere), 69 days. HOLD: mean +0.94c, standard deviation 23.5c, worst loss -97.2c, worst day -311c, deepest drawdown 699c, +0.68c a contract with the cent rounding at two contracts.

| Sell when the side's bid is at or below | Entries stopped (of those, would have won if held) | Mean | Difference vs HOLD (z) | Fair-market 95th pct of the difference | Std dev | Worst loss | Worst day | Drawdown | Two contracts, rounded | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| X1 50c | 6.2% (32%) | +0.83c | -0.11c (-0.65) | +0.16c | 21.1c | -97.2c | -224c | 544c | +0.55c | `FALSIFIED` |
| X2 60c | 7.6% (41%) | +0.78c | -0.16c (-0.75) | +0.13c | 20.1c | -96.6c | -254c | 606c | +0.49c | `FALSIFIED` |
| X3 70c | 10.3% (53%) | +0.83c | -0.11c (-0.44) | +0.15c | 18.2c | -96.6c | -280c | 530c | +0.53c | `FALSIFIED` |
| X4 80c | 15.6% (66%) | +0.77c | -0.17c (-0.57) | +0.09c | 15.7c | -95.2c | -312c | 441c | +0.46c | `FALSIFIED` |

- **Prediction against outcome.** Predicted: every variant `FALSIFIED` as an improvement, mean difference between -0.2c and -1.0c, and the worst loss falling to about -50c at X3 and X4. The verdicts were right. The
  mean cost was smaller than predicted (-0.11c to -0.17c, none distinguishable from zero) and **the worst loss prediction was wrong: the worst single loss barely moves (-97c to -95c)**. The reason is in the data, not
  a bug: the biggest losses are markets where the side's bid falls from the 90s to near zero between two minute checks (a move inside a minute), so the rule sells at an already collapsed bid. A stop cannot cap a loss that gaps.
- **What the stop does buy.** It narrows the spread of results: the standard deviation falls from 23.5c to 15.7c (X4) and the deepest drawdown from 699c to 441c, at the cost of about 0.17c a contract of mean (more once cent
  rounding of the exit leg is counted: +0.46c against +0.68c at two contracts). Earlier stops (X1) shorten the worst day (-311c to -224c) with less loss of mean. This is information only: the pre-set verdict is on the mean
  and the stop does not improve it.
- **It cuts winners.** At X4, 66% of the entries the rule sold would have won if held, and at X3 53%; those are the recoveries it gives up, which is the same trade-off as the failed-breakout exit found earlier.
- **What this does not say.** One rule shape (a bid threshold checked once a minute). A resting stop order at the broker would react inside the minute, but Kalshi has no stop order type for these markets, so a faster check
  would need the recorder's 10 second books (this day's snapshots could be used to ask how much a 10 second check would catch; that would be a new, pre-registered test). Nothing here changes the live bot.
- **Count.** Four variants: **2,567 as of 2026-10-08**.
