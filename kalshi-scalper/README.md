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

Strategy variants tried so far: **2,591 as of 2026-10-10** (X8 is registered, not run: it needs fresh data). Earlier today: **2,590 as of 2026-10-10** (T5, E1, E2 and B4 added after the 2,586 below; all `FALSIFIED`). Earlier tally: **2,586 as of 2026-10-09** (T1 to T4 added to the 2,582 of 2026-10-08; (792 before P1; P1 is the 793rd; the four slot search adds 1,760; F6 and F7 two; Q1 to Q3 and two
Q1 thresholds five; F8 one; N1 and N2 two; X1 to X7 seven; B1 to B3 three; F9 one), all `FALSIFIED` or `NOT_ENOUGH_DATA`. The running total is kept up to date in the section that last changed it.
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

## Book study 2: the Firestore recorder's first 12 hours (2026-10-08, information only)

The owner downloaded the page's "book snapshots" file: **6,813 snapshots, 82 markets, 01:47 to 13:50 UTC on 2026-10-08, median gap 10.0 s (90th percentile 20 s)**. This is the unattended
recorder working, with the six snapshots a minute fix from `claude/logic-check` not yet deployed when it was taken (so a hole in each minute remained). `python -m scalper.bookfile` parses it (as data only) and runs the
same P2 and ask-drift code as for the container recorder. 80 of the 82 markets are settled in the database. P2 is applied to markets closing after 03:00 UTC (the amendment's rule); it stays `NOT_ENOUGH_DATA`
(30 signals on 1 day against 300 on 5), so everything below is information only and decides nothing.

- **P2 on 30 signals.** A resting buy one tick below the touch was strictly traded through on 53% of them (57% counting a touch). The signals that filled lost **-5.77c** a contract; the same signals taken lost
  -6.02c. The signals that did not fill, taken, earned **+6.08c**. Per signal with unfilled counted as zero: **resting -3.08c against taking -0.38c.** (Lower maker fees move the resting figure only to -2.83c and -2.89c.) By ask
  band: 90c to 92c, 9 signals, 5 filled; 92c to 95c, 11 signals, 6 filled; 95c to 97c, 10 signals, 5 filled. Thirty signals is far too few to read a band, but the **shape is the one P2 predicted**: the resting
  order is filled disproportionately by the markets that then fall (someone selling to you is selling because it is falling), and misses the ones that rise. That is adverse selection, not a saving.
- **Ask drift in the L1 window (108 consecutive pairs about 10 s apart).** The favourite's ask at the next snapshot: up 60.2%, the same 7.4%, down 32.4%; median spread 0.1c; median size at the touch about 1,141
  contracts. The ask tends to creep up as the close approaches, so a touch read a second or more before the order can be left behind by a tick, which fits the live no-fill pattern. The size at the touch is large, so
  thin books are not the reason.
- **What this does and does not say.** One day, 30 signals. It does not test the maker idea; it shows that on this day the resting orders would have been filled mostly on the losers. The
  full test is the 300 signals on 5 days P2 asks for, from this same recorder.

## Pre-registration: lower exit thresholds, X5 to X7 (fixed 2026-10-08 14:10 UTC, before any of them was priced)

The first exit family (X1 to X4) started at 50c, and the owner asked, rightly, what happens lower: a stop that only fires on a near total collapse costs less and cuts fewer winners, so
the answer is not obvious from 50c to 80c alone. It should have been in the first registration; it is registered now, on the same rule and the same entries, before any result exists for it.

- **Variants, fixed now, three more tries.** Sell when the held side's bid is at or below **40c (X5), 30c (X6), 20c (X7)**. Everything else is exactly as registered for X1 to X4: the same 3,422 L1 entries,
  checks at the candle closes 5, 4, 3, 2 and 1 minutes before the close, a real bid of at least 0.1c, taker fee on both legs, no spread filter, HOLD as the baseline. The code is unchanged except for the
  threshold table.
- **Counterparty and numeric prediction, stated before the run.** Same counterparty story as X1 to X4 (the buyer on the other side of a collapse is paying a fair price). Predicted: the share of entries
  stopped falls to about 5% (40c), 3% (30c) and 2% (20c); the mean difference against HOLD moves toward zero as the threshold falls, between -0.10c and +0.05c; the standard deviation falls only a little (to about
  22c at 40c and about 23c at 20c) and the worst loss stays near -95c, because the large losses gap straight through these levels inside a minute. **The pre-registered expectation is that all three are
  `FALSIFIED` as an improvement in the mean**, and that no threshold below 50c gives a worse deal than X1 or a better one.
- **Kill criteria.** The same as X1 to X4 with the bar made stricter for seven tries in total: n at least 300 on at least 5 days; the exit rule's mean above HOLD's with a day clustered z of the per day
  difference of at least **2.7** (X1 to X4 keep the 2.5 they were registered with); its own mean positive, positive in both halves, positive with fees times 1.2, and the difference above the 95th percentile of the
  fair-market null. Anything else is `FALSIFIED`.
- **Count.** Three variants: **2,570 as of 2026-10-08** (2,567 plus three).

**2026-10-08: X5 to X7: all three `FALSIFIED`; the whole exit family is now X1 to X7.** One run of `python -m scalper.exits` (after the tests for the lower thresholds), same rule and entries. The database had grown by 10 markets since the X1 to X4 run, so the table below is the one run of all seven together on 3,432 L1 entries (HOLD +0.92c, standard deviation 23.5c, worst loss -97.2c, worst day -311c, drawdown 699c; X1 to X4 moved by at most 0.02c from the numbers above and none changed verdict).

| Sell when the bid is at or below | Stopped (of those, would have won if held) | Mean | Difference vs HOLD (z) | Fair-market 95th pct | Std dev | Worst day | Drawdown | Two contracts, rounded | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| X7 20c | 3.4% (9%) | +0.92c | -0.00c (-0.02) | +0.06c | 22.9c | -295c | 706c | +0.65c | `FALSIFIED` |
| X6 30c | 4.5% (16%) | +0.87c | -0.05c (-0.36) | +0.07c | 22.4c | -273c | 669c | +0.60c | `FALSIFIED` |
| X5 40c | 5.2% (25%) | +0.76c | -0.16c (-0.97) | +0.10c | 22.0c | -287c | 647c | +0.49c | `FALSIFIED` |
| X1 50c | 6.2% (32%) | +0.83c | -0.10c (-0.59) | +0.14c | 21.1c | -224c | 544c | +0.55c | `FALSIFIED` |
| X2 60c | 7.6% (41%) | +0.77c | -0.15c (-0.71) | +0.17c | 20.1c | -254c | 606c | +0.49c | `FALSIFIED` |
| X3 70c | 10.3% (52%) | +0.83c | -0.09c (-0.36) | +0.17c | 18.2c | -280c | 530c | +0.54c | `FALSIFIED` |
| X4 80c | 15.6% (66%) | +0.77c | -0.15c (-0.50) | +0.05c | 15.7c | -312c | 441c | +0.47c | `FALSIFIED` |

- **Prediction against outcome.** Predicted: the share stopped falls to about 5%, 3% and 2%, the mean difference moves toward zero, the standard deviation falls little and the worst loss stays near -95c.
  Measured: 5.2%, 4.5% and 3.4% stopped (a little more than predicted), the mean difference falls to -0.16c, -0.05c and -0.00c, the standard deviation 22.0c to 22.9c, the worst loss exactly -97.2c. All as predicted except the share stopped.
- **What it says.** The difference from HOLD is never distinguishable from zero at any of the seven thresholds (z between -0.02 and -0.97), the worst single loss never drops below about -95c, and the risk reduction is
  real only for the higher thresholds (X4 cuts the standard deviation by a third and the drawdown by 37%) at the cost of selling mostly winners (66%). Below 50c the rule almost never fires and almost changes nothing. 20c
  is the only threshold that does not lose to holding, and it does so by being HOLD.
- **Count.** Three more variants: **2,570 as of 2026-10-08**.

## Pre-registration: the entry side, price bands for L1, B1 to B3 (fixed 2026-10-08 14:18 UTC, before any code and before any band selection was run)

The exit family (X1 to X7) found that a stop cannot fix L1's payoff. The other lever is which entries to take. The post hoc band table in this file (88c to 90c negative after costs, 90c to 95c best, 95c to 97c about zero) was read off all 69 days after
the fact, so it cannot be used as evidence. What can be tested honestly on these days is whether **choosing bands from half the days and applying the choice to the other half** generalizes, which is what a live rule would
have to do. Nothing below was run.

- **Bands, fixed.** By the price paid: 88c to 90c, 90c to 92c, 92c to 95c, 95c to 97c (the last includes 97c). Entries are every L1 entry (`lstrats.hold_rule(L1)`), both series, taker at the ask, held to settlement.
- **B1, the walk-forward rule (the one real test).** Split the days in half by count (first half of the days, second half). Fold 1: choose bands on the first half, trade the chosen bands on the second half. Fold 2: choose on the second half, trade on the first.
  A band is chosen if, in the choosing half, its net per contract is above zero AFTER the cent rounding at two contracts (`feerounding`) and it has at least 100 entries there. The trades are the union of the two folds' test entries. No band edge,
  threshold or count is tuned. The baseline is every entry over the same days (each in its own test half).
- **B2 and B3, fixed rules (information about the post hoc bands, counted as tries).** B2: trade only 88c to 95c (skip 95c to 97c). B3: trade only 90c to 97c (skip 88c to 90c). Evaluated on all 69 days and on each half, against the baseline. (P1, 90c to 95c, is
  already registered and is being measured forward, so it is not repeated here.)
- **Counterparty.** The same longshot buyer as L1; the claim is only that the edge is not uniform across the price range, because the fee is largest in the middle of it and the possible gain smallest at the top.
- **Numeric prediction, stated before the run.** B1: the chosen set earns less than the post hoc bands suggest and not clearly more than the baseline: difference per trade between -0.3c and +0.5c, day clustered z below 2.4.
  B2 and B3: each a little better than the baseline on all 69 days (+0.1c to +0.5c) and neither distinguishable from it. **The pre-registered expectation is that all three are `FALSIFIED`.**
- **Kill criteria.** Three tries, so the bar is z of **2.4**. A rule is `NOT_YET_FALSIFIED` only if ALL hold: its trade set has at least 300 entries on at least 5 days; its mean net per trade is above the baseline's with a day clustered z of the per day difference of at least 2.4;
  its own mean is positive; positive in BOTH halves (for B1, in both folds' test halves); positive with fees times 1.2; and the difference is above the 95th percentile of the fair-market null (outcomes redrawn from each market's late price, the same selection rule applied to
  the redrawn outcomes, 500 repeats). Anything else is `FALSIFIED`. A pass is permission to test forward only; the forward look F5 (90c to 95c) is already running.
- **Information only, printed with the verdict, may not rescue anything.** For each band: entries, mean price, the actual win rate, the win rate needed to break even (price plus fee) and the margin between them with its standard error, net per contract unrounded
  and cent-rounded at two contracts, and net per dollar risked. This is the "how high must the win rate be" view.
- **Count.** Three variants: **2,573 as of 2026-10-08** (2,570 plus three).

**2026-10-08: B1 to B3: all three `FALSIFIED`.** One run of `python -m scalper.bands` (after its tests). Nothing changed after seeing it. 3,432 L1 entries over 69 days, baseline mean +0.92c (+0.66c at two contracts, cent rounded).

| | Trades | Mean | Baseline | Difference (z) | Fair-market 95th pct of the difference | Halves | Two contracts, rounded | Verdict |
|---|---|---|---|---|---|---|---|---|
| B1 walk-forward | 2,302 | +0.69c | +0.92c | -0.08c (-0.24) | +0.55c | +0.82c / +0.59c | +0.43c | `FALSIFIED` |
| B2 88c to 95c | 2,533 | +1.17c | +0.92c | +0.29c (+1.45) | +0.43c | +1.57c / +0.77c | +0.90c | `FALSIFIED` |
| B3 90c to 97c | 2,911 | +1.18c | +0.92c | +0.26c (+0.93) | +0.39c | +1.58c / +0.75c | +0.92c | `FALSIFIED` |

- **The selection did not hold up from one half to the other, which is the main result.** Choosing on the first 34 days kept 90c to 92c and 92c to 95c; choosing on the last 35 days kept 88c to 90c, 92c to 95c and 95c to 97c. The only band chosen both ways is 92c to 95c. Bands that look
  clearly good or bad on the full 69 days are, half by half, decided by noise except that one. The walk-forward set earned less than trading everything (-0.08c, z -0.24).
- **The skip-a-band rules are a little better than the baseline and not distinguishably so.** B2 and B3 each add about +0.3c a contract (+0.24c to +0.26c once cent rounded) with day clustered z of +1.45 and +0.93, below the bar and below the fair-market 95th percentile (+0.39c to +0.43c): in a market with no edge,
  dropping the cheapest or the dearest band for fee reasons alone already adds a few tenths of a cent, so a gain of that size is not evidence.
- **Prediction against outcome.** Predicted: all three `FALSIFIED`; B1 difference between -0.3c and +0.5c; B2 and B3 each +0.1c to +0.5c and indistinguishable. All as predicted.
- **Information only: win rate against the win rate needed (all days, post hoc).** 88c to 90c: 88.7% against 89.2% needed (margin -0.5 points, standard error 1.4). 90c to 92c: 92.5% against 91.3% (+1.2, 0.9). **92c to 95c: 95.7% against 93.9% (+1.9, 0.6), about 3 standard errors above break even.**
  95c to 97c: 96.6% against 96.3% (+0.2, 0.6). Per dollar risked: -0.56%, +1.37%, +2.02%, +0.24%. 92c to 95c is the one band with a margin well outside its noise, and it is also the band the walk-forward kept in both folds, but it was singled out
  by looking, one of four, so it is a candidate for a forward look and not a finding (see F9).
- **Count.** Three variants: **2,573 as of 2026-10-08**.

## Pre-registration: a forward look at 92c to 95c, F9 (fixed 2026-10-08 14:21 UTC, before it was run on any market after 14:30)

B1 to B3 left one band standing out on all 69 days (92c to 95c: win rate 95.7% against 93.9% needed, about 3 standard errors) and kept by the walk-forward in both folds. It was singled out after looking, so the 69 days cannot count for it.

- **F9.** L1 (6 minutes left, taker at the ask, hold) restricted to entries priced 0.92 to 0.95, both series, on markets that close after **2026-10-08 14:30:00 UTC** (close_ts above 1791469800). It is nested inside F5 (90c to 95c) and F0, so it is not an independent test of them.
- **Prediction, stated before the run.** Net about +1.0c a contract (below the +1.88c seen on 69 days, which was selected by looking). **The expectation is that it does not pass.**
- **Bar.** The common one: at least 300 entries on 5 days, z at least 2.1, both halves positive, fees times 1.2 positive, and above F0 on the same markets. About 16 entries a day, so 300 take about 19 days.
- **Count.** One more variant: **2,574 as of 2026-10-08**.

## Risk cap per trade (information only, no verdict, no variant counted)

`python -m scalper.riskcap` replays the 3,432 L1 entries over 69 days in time order at a 60% fill rate (a round number between the 50% and 70% seen, not fitted), 40 fill draws per day. An order buys 1, 2 or 3 contracts and costs the cent-rounded `order_cost`. The loss stop is applied as the bot applies it: before each order, settled profit minus the whole cost of orders still open must be above minus the stop, otherwise the day ends. Bitcoin and gold overlap in the data as they do live.

| Contracts | Mean/day | Std dev | 5th pct | Worst day | Stop trips at $10 | Worst single order |
|---|---|---|---|---|---|---|
| 1 | +$0.12 | $1.20 | -$1.99 | -$4.19 | 0% | -$0.98 |
| 2 | +$0.37 | $2.41 | -$3.84 | -$8.27 | 0% | -$1.95 |
| 3 | +$0.60 | $3.69 | -$6.08 | -$12.41 | 2.6% | -$2.92 |

- **The stop level barely matters to the mean.** $7, $10 and $15 give means within a few cents of each other. At 3 contracts a $7 stop trips on 9.6% of days and only removes good days along with bad ones.
- **A stop cannot cap a gap loss.** The worst single order is its whole cost, and the 3 contract worst day (-$12.41) passes the $10 stop because open orders settle together.
- **Size scales the spread faster than the mean.** Typical bad day (5th percentile) against expected day: about -$2.0 against +$0.12 at 1 contract, -$3.8 against +$0.37 at 2, -$6.1 against +$0.60 at 3. Mean per day depends on the 0.6 fill rate and on 69 days; neither is a measurement of the live bot.
- Count: unchanged at **2,574 as of 2026-10-08**.

## Amendment to the size ladder: weekly scaling and reinvest-and-skim (2026-10-08, written before the size changes, at the owner's direction)

The owner chose to scale size with the balance instead of waiting for step 1's evidence gates (forward check, 100 settled trades with a loss, $250). This is an override of those gates, made knowingly, and it is written here before it ships, as the ladder asks.

- **The rule (`functions/kalshiLiveLib.js`: `reviewSizing`, `foldSkim`, `skimAddon`).** Cap on contracts per order = balance without savings / $85, one step up at most once a week, down at once if the balance falls, hard ceiling 10. A loss stop pauses step-ups and the add-on for a week. The loss stop is 10% of the balance at the last weekly review. Reinvest-and-skim splits only NEW net profit highs: half to a pool that buys extra contracts (no fixed limit, one per full contract cost, still under the 2% of cash rule), half to savings that are not sized on. The first review starts at 3, the cap the owner was running, so a $341 account reaches 4 after the first weekly review.
- **Evidence it relies on (`python -m scalper.sizing`, 10 weeks resampled from the 69 days, 60% fills, loss stop NOT applied).** Cap 3 flat: +$46, 5th percentile -$3.8, deepest drawdown (95th) $42. The chosen rule: +$59, 5th percentile -$6.4, drawdown $49, 7.4% of paths lose money, end cap 3.7 on average (it ramps up over the weeks). Cap 4 flat for comparison: +$67, 0.0, $55. The chosen rule is a little below flat 4 because it ramps and because the add-on pool is lost on a bad run.
- **What this does not change.** The edge is about +0.7c a contract and failed its own bar (z 1.45 against 2.1). Size scales both the gain and the loss; a loss still costs the whole price and no stop can cap a gap. The forward checks (F0 to F9) still decide whether the edge is real, and the step-down rules above still apply: if the forward check returns `FALSIFIED`, the cap goes back to 1 contract.
- **A flaw found on the way, kept so it is not rebuilt.** Skimming half of every WIN looked natural and is wrong here: wins are 6c and losses 90c, so it banked $150 of "savings" on a net of -$6 in a replay while the base shrank. Only new net highs are skimmed now, and a test asserts savings never exceed half the best net profit reached.
- Count: unchanged, **2,574 as of 2026-10-08** (sizing, not a strategy variant).

## Fee rounding, measured on the owner's own fills (2026-10-08, information only, no hypothesis, no verdict)

The cost model check above assumed a buy costs `ceil_to_the_cent(count * (price + fee))`, which would make one contract at 92c pay about 1c of fee. The "Copy order diagnostics" export (the bot's own order records, 60 rows from Oct 7 and 8) settles it for the fee that Kalshi reports.

- **`average_fee_paid` is the fee rounded up to $0.0001 over the whole order, not to the cent.** 21 fills checked (`observed_fee_per_contract`): a one contract buy at 7.1c reports 0.47c, the same price at three contracts reports 0.46c, a one contract buy at 4.4c reports 0.30c against an exact 0.294c. Whole-cent rounding fits 1 of 21; the sub-cent rule fits all 21.
- **Prices are sub-cent too** (average fills such as 0.9599 and 0.0420), so this account moves in fractions of a cent. Nothing here shows the whole-cent balance alignment that `order_cost` models.
- **What is not shown.** The export has the fee Kalshi reports, not the balance move. It does not prove the balance is never aligned to the cent; a one contract order's balance before and after would. The evidence leans against it.
- **Consequence for earlier numbers.** `order_cost` (whole cent) was used by `feerounding`, `riskcap` and `sizing`. If this account is not charged whole cents, those numbers understate the edge slightly: the +0.49c (1 contract), +0.70c (2) and +0.79c (3) per contract move toward the unrounded +0.96c, and one contract orders stop being worse than three. Nothing about sizing decisions flips; every figure there is a little conservative.
- Count: unchanged, **2,574 as of 2026-10-08**.

## Pre-registration: the cheap side, scalped early, C1 to C3 (fixed 2026-10-08 16:19 UTC, before any code and before any cheap-side trade was priced)

The owner asked for "the opposite end of the spectrum" from L1: instead of buying the 88c to 97c favorite late and holding, buy the side that is only 8c to 15c in the first five minutes and take a few cents.

- **What was and was not tried.** H2 and H4 bought 30c to 50c sides and sold at 80c (both `FALSIFIED`). L1 bought the favorite late. The 8c to 15c side with a small target, early in the market's life, is a price band and an exit not covered by any row above.
- **Counterparty.** Whoever sells us the longshot early: a quoter whose early price lags a spot move, or a seller who accepts a few cents for a lottery ticket. If early quotes are slow, the cheap side should tick up toward its true value before the close.
- **Why the prior is negative.** In a fair market a cheap side's price is its probability, so buying and selling for a small target earns zero before costs. Costs here are the fee in and out (about 0.6c each at 10c, quadratic) and the spread (0.1c to 1c). L1's +0.96c a contract on the favorite means the longshot side loses about that much on average, so the mirror image starts about -1c behind before costs.
- **Rule, fixed.** Entry: the first minute close in the first five minutes of the market (candles ending 840, 780, 720, 660 or 600 seconds before the close) at which either side's ask (YES at its ask, NO at one minus the YES bid, snapped to 4 places) is 0.08 to 0.15 and the quote is real (`valid_quote`). One entry per market. Exit: the first LATER minute close at which that side's bid is at least the entry ask plus the target T, sold at that bid, taker fee on both legs.
  - **C1:** T = 5c; otherwise held to settlement.
  - **C2:** T = 5c; otherwise sold at the bid at the minute close 6 minutes before the close (no settlement risk; a bid under 0.1c counts as 0).
  - **C3:** T = 10c; otherwise sold at 6 minutes left as in C2.
- **Numeric prediction, stated before the run.** C1 mean between -2.5c and -0.5c a contract; C2 and C3 between -1.5c and -0.2c. All three expected `FALSIFIED`. The count of entries is unknown (early 8c to 15c needs a big spot move in the first five minutes); fewer than 300 entries reports `NOT_ENOUGH_DATA`.
- **Bar.** The common one, for three tries: at least 300 entries on at least 5 days, day clustered z at least 2.5, both halves positive, positive with fees x1.2. Verdict words only `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. Passing is permission to look at later data, never a reason to trade.
- **Information only, printed beside the verdict and unable to rescue a failure:** the hit rate of the target, the average win and loss, by series, and the same rule with a 3c target.
- **Count.** Three variants: **2,577 as of this entry** (2,574 plus three).

**2026-10-08 16:38 UTC: C1 to C3: all three `FALSIFIED`.** One run of `python -m scalper.cheapscalp` (after its tests), under the rules fixed above. Nothing changed after seeing it. 11,220 markets over 69 days; 1,701 entries (933 Bitcoin, 768 gold).

| | Entries | Mean | Day clustered z | Halves | Fees x1.2 | Verdict |
|---|---|---|---|---|---|---|
| C1 5c target, else hold | 1,701 | -3.28c | -8.62 | -3.16c / -3.40c | -3.54c | `FALSIFIED` |
| C2 5c target, else sell at 6 min left | 1,701 | **-2.27c** (first run said -1.00c, withdrawn) | -9.51 | -2.14c / -2.41c | -2.56c | `FALSIFIED` |
| C3 10c target, else sell at 6 min left | 1,701 | **-2.33c** (first run said -0.40c, withdrawn) | -8.66 | -2.07c / -2.60c | -2.61c | `FALSIFIED` |

- **CORRECTION, found the same afternoon (the C2 and C3 rows above are the corrected ones).** The first run searched for the target on every later candle, including the ones after the 6 minute mark where C2 and C3 had already sold, so a late bounce counted as a win the rule would not have realized. Every error found in this project so far has flattered the result, and that is how this one was caught: a result better than the registered prediction. Fixed against the rule as registered (the target is looked for only up to and including the 6 minute candle), with a test, and re-run once. C1 is unaffected (it has no time exit). Corrected: **C2 -2.27c, C3 -2.33c** (first run -1.00c and -0.40c). The verdicts did not change; the size of the loss did, and the paragraph below that read the first run is withdrawn.
- **Prediction against outcome.** Predicted C1 between -2.5c and -0.5c, and C2 and C3 between -1.5c and -0.2c, all `FALSIFIED`. The verdicts were right. C2 (-1.00c) and C3 (-0.40c) fell inside their ranges; **C1 was worse than predicted (-3.28c against a floor of -2.5c)**, because holding to settlement from 8c to 15c loses the whole price more often than the early bounce pays: 41.2% hit the target, but holding the rest averaged -13.2c a loss against +10.9c a win.
- **Information only: the target is hit often and the edge is still negative.** A +5c bounce arrives 41% of the time and a +10c bounce 31.5%, so cheap sides do tick up. Sold at the 6 minute mark instead of held, the loss shrinks from -3.28c to -1.00c (C2), and a larger target shrinks it again (C3). Stops and exits cannot create profit in a fair game; what they change is how much of the fee and spread is paid.
- **WITHDRAWN (computed on the buggy first run): "it is cost, not signal".** It said that with the fee set to zero the same trades make -1.99c (C1), **+0.45c (C2) and +1.05c (C3)**. Both legs' fees (about 0.6c each at 10c) turn a small positive gross into the net above, which is the same conclusion as the dispersion study: cost, not an absent signal, is the binding constraint. A gross of +1.05c on a 10c target is not distinguishable from zero here and the registered bar is net. The corrected gross figures are **-1.99c (C1), -0.85c (C2) and -0.94c (C3)**: with no fees at all these trades still lose, so for the cheap side there is no hidden edge being eaten by cost.
- **Same in both series.** Bitcoin and gold net within a few tenths of a cent of each other in every variant.
- **Count.** Three variants: **2,577 as of this entry** (2,574 plus three).

## Idea ledger addendum: the opening window, O1 to O50 (written 2026-10-08, before any of them was built or run)

The owner asked for about 50 ideas for the first 9 minutes of each market, which the live bot leaves unused (it enters at 6 minutes left). **Listed here BEFORE any is run, so none is quietly retried.** Status of every row is `OPEN` unless its tag says otherwise. Tags: `NEW` = no ledger row covers it; `OVERLAP <id>` = its counterparty story rewords a ledger row or a falsified result, so it is NOT a new try and should not be run as one; `NOT_RUNNABLE` = no free data.
Counts: **22 NEW, 26 OVERLAP, 2 NOT_RUNNABLE.** The binding constraint found so far is cost (a taker round trip costs about 1c to 3c), so the NEW rows are mostly resting (maker) entries, which pay no taker fee, and ideas that improve or extend L1, whose measured edge is positive. Anything needing book snapshots waits for the Firestore recorder to hold several days of data (it started 2026-10-08). No strategy variant is counted until it is run.

| # | Family | Idea | Who pays us or why it should work | Needs | Tag |
|---|---|---|---|---|---|
| O1 | resting entries at the open | Bid at the best bid on the side spot leans toward, minutes 1 to 4, cancel at 5 | Takers who sell into a dip pay the spread to us; no taker fee | books | NEW (L4 adjacent) |
| O2 | resting entries at the open | Penny the bid (+0.1c) when the best bid is under 50 contracts, exit resting at the ask | Takers crossing a thin book | books | NEW |
| O3 | resting entries at the open | Lowball bids at 30c on both sides the moment a market opens, exit resting at 45c | Panic sellers into an empty opening book | tape | NEW |
| O4 | resting entries at the open | Two sided quote only when the spread is 3c or more, 1 contract a side, 3 minute life | Takers crossing a wide spread | books | OVERLAP H5 (narrowed) |
| O5 | resting entries at the open | Resting sell above the mid after a jump of 8c or more in the first 3 minutes (maker fade) | Late momentum chasers | books | NEW |
| O6 | resting entries at the open | Resting bid 5c under the minute 1 ask on the cheap side, 4 minute life, hold if filled | Sellers who accept a discount | candles | OVERLAP P2 (resting fills landed on losers) |
| O7 | resting entries at the open | Resting bids at round prices (25c, 75c) where size clusters | Takers who hit round numbers | books | NEW |
| O8 | resting entries at the open | Join the bid and bid again one tick up each minute until filled, max 3 ticks | Sellers who give way over time | books | NEW |
| O9 | structure and arbitrage | YES ask plus NO ask under $1 less both fees in the first 3 minutes | Stale quoters on one side | books | OVERLAP L14 |
| O10 | structure and arbitrage | YES bid plus NO bid over $1 plus both fees: sell both sides | Stale bids on both sides | books | OVERLAP L14 |
| O11 | structure and arbitrage | Stale quote: spot moves 0.1% in 10 seconds while the book is unchanged for 20 | Slow quoters | books under 10 s | OVERLAP L5 |
| O12 | structure and arbitrage | Buy after the spread narrows from 6c or more to 2c or less within 2 minutes (liquidity arrival) | Impatient early sellers | books | NEW |
| O13 | structure and arbitrage | First traded price of the market against the distance-implied fair price | Open price takers | tape and spot | OVERLAP H7 (distance) |
| O14 | structure and arbitrage | Bitcoin and gold both open: trade the series whose first quote is farther from 50c | Slow quoters in the later series | books | OVERLAP L6 and S01 to S02 |
| O15 | use the window to improve L1 | Retry a missed L1 fill at 5 minutes left if still in band (41% of signals miss) | More volume of an edge that averages +0.9c | candles and live | NEW |
| O16 | use the window to improve L1 | Hybrid: rest a bid 1c under the touch from 9 to 6 minutes left, IOC at 6 as fallback | Cheaper entries on the ones that come back | books | OVERLAP P2 and hybrid result |
| O17 | use the window to improve L1 | Size L1 up when the favorite was already 85c or more at minute 5 | Long-run favorites are not repriced | candles | NEW |
| O18 | use the window to improve L1 | Skip L1 when the market mid crossed 50c three times or more in minutes 1 to 8 | Choppy markets end randomly | candles | OVERLAP Q filters |
| O19 | use the window to improve L1 | Skip L1 when Bitcoin's realized volatility over the first 8 minutes is in its top decile | Fat tails break favorites | spot | OVERLAP L7 and L13 |
| O20 | use the window to improve L1 | Skip L1 on days with a scheduled release (CPI, jobs, FOMC) | Slow quoters around releases | calendar | OVERLAP L10 |
| O21 | use the window to improve L1 | Skip L1 when the spread at 6 minutes left is wider than 2c | A wide book is a thin book | candles | NEW |
| O22 | use the window to improve L1 | Hold L1 but sell at 99c when it is offered before the close (free exit of the last cent) | Takers who pay up for certainty | books | NEW |
| O23 | scalps on favorites | Buy a 70c to 90c favorite at minute 3, sell at +3c, else sell at 6 minutes left | Slow repricing of a trend | candles | NEW |
| O24 | scalps on favorites | Same with a +5c target | Same | candles | NEW |
| O25 | scalps on favorites | Buy a 55c to 70c side at minute 2 when spot confirms, sell at +4c | Slow repricing | candles and spot | OVERLAP M1 and H2 |
| O26 | scalps on favorites | Buy a favorite at minute 4 and hold to settlement (the four slot grammar, early) | Favorite-longshot bias | candles | OVERLAP four slot search |
| O27 | scalps on favorites | Buy the favorite on a dip of 3c in minutes 3 to 6, sell at the pre-dip price | Panic sellers in a stable market | candles | NEW |
| O28 | scalps on favorites | Sell a favorite short-term when it exceeds 97c before minute 8 (buy the other side at 3c or less) | Overpaying for certainty | candles | OVERLAP L3 |
| O29 | spot signals (Bitcoin) | Spot crosses the strike by 0.05% in minutes 2 to 4: buy that side | Slow repricing of spot | candles and spot | OVERLAP H7 and L2 |
| O30 | spot signals (Bitcoin) | Spot reverses back through the strike after a 0.1% excursion: fade the excursion | Overreaction | candles and spot | OVERLAP S09 and S21 |
| O31 | spot signals (Bitcoin) | Spot acceleration (second difference) over minutes 1 to 4 | Trend followers | candles and spot | OVERLAP S16 |
| O32 | spot signals (Bitcoin) | Spot against its own last 60 second average at minute 5 (the settlement is an average) | Holders pricing a point, not an average | candles and spot | OVERLAP L9 |
| O33 | spot signals (Bitcoin) | Spot move in the previous market's last 3 minutes against the new opening mid | Open price lag | candles and spot | OVERLAP L8 |
| O34 | spot signals (Bitcoin) | Perpetual futures funding or basis as a lean | Slow quoters | external data | NOT_RUNNABLE (no free feed) |
| O35 | cost-gated entries | Run any registered rule only in the 3 hours with the tightest opening spreads (chosen on cost) | Cost is the binding constraint | candles | NEW (allowed: selection on cost) |
| O36 | cost-gated entries | Run only when the opening depth on both sides is 200 contracts or more | Thin books cost more | books | NEW |
| O37 | cost-gated entries | Weekend against weekday opening spreads (a measurement first) | Wider weekend spreads | candles | NEW (measure) |
| O38 | cost-gated entries | Gold only when Bitcoin's spread is also tight (a liquidity regime flag) | Shared liquidity cycles | candles | NEW |
| O39 | calendar and settlement | Gold reopen after the daily break: first market's opening mid against the last price | Stale gold quotes | candles | OVERLAP S14 |
| O40 | calendar and settlement | Bitcoin at the London and New York opens, first 5 minutes | Session opens | candles and spot | OVERLAP S15 and S12 |
| O41 | calendar and settlement | Quarter-hour that includes the hourly mark (:00) against the other three | Hourly index effects | candles | OVERLAP S26 |
| O42 | calendar and settlement | Last market before a settlement-day roll or maintenance window | Operational gaps | calendar | NOT_RUNNABLE (no calendar) |
| O43 | hedges and portfolios | Straddle: buy both sides when the asks sum to $1.02 or less and sell the leg that moves | Whoever pays for volatility | books | NEW (cost likely binding) |
| O44 | hedges and portfolios | Bitcoin and gold opposite sides when both open favorite-heavy | Correlation mispricing | candles | OVERLAP S01 to S05 |
| O45 | hedges and portfolios | Buy a 5c longshot at minute 2 as insurance beside an L1 position in the other market | Reduces variance, not expectation | candles | NEW (variance only) |
| O46 | hedges and portfolios | Scale in: half at 9 minutes left, half at 6 if the price held | Average entry price | candles | NEW |
| O47 | book shape | Microprice (size weighted mid) against the plain mid at minute 3 | Quoters who ignore size | books | OVERLAP L12 |
| O48 | book shape | Share of size on one side of the top 3 levels at minute 2 | Quoters who do not read depth | books | OVERLAP L12 |
| O49 | book shape | A large resting order appearing and disappearing (spoof-like) as a signal | Slow reactors | books | NEW |
| O50 | book shape | Time since the last book change as a staleness gauge | Slow quoters | books | OVERLAP L5 |


## Pre-registration: favorite scalps and the dip buy, F1 to F3 (ledger rows O22, O23 and O26; fixed 2026-10-08 17:23 UTC, before any code and before any of these was priced)

First three rows of the opening window ledger to run, because they need only the minute candles we hold. Named `OP1` to `OP3` in code to keep them apart from the forward looks F0 to F9.

- **Counterparty.** Whoever sells a trending favorite too cheaply in the first minutes (a quoter whose price lags the move), or sells into a 3c dip in a market that is about to hold.
- **Why the prior is negative, stated.** A fair price earns zero before costs. At 70c to 90c the fee is 1.1c to 1.9c a leg, so a scalp pays about 2.5c to 3.5c in fees and spread to earn a 3c or 5c target. All three are expected to lose, as C1 to C3 and M1 did.
- **Rules, fixed.** Prices are the closing quotes of minute candles; the quote must pass `valid_quote`; YES is bought at its ask, NO at one minus the YES bid (4 places); taker fee both legs; one entry per market; exits are strictly later candles; a bid under 0.1c counts as 0.
  - **OP1:** entry at the first candle close in the first 3 to 5 minutes (ending 720, 660 or 600 seconds before the close) where a side's ask is 0.70 to 0.90. Exit at the first later close with that side's bid at or above the entry ask plus **3c**, else sold at the bid 6 minutes before the close (a missing 6 minute candle holds to settlement, and is counted).
  - **OP2:** as OP1 with a **5c** target.
  - **OP3 (the dip):** entry at the first candle close in the first 3 to 6 minutes (ending 720, 660, 600 or 540 seconds before the close) where a side's ask is 0.70 to 0.90 AND at least 3c below that side's ask one minute earlier (the earlier candle must also be a real quote). Exit at the first later close with that side's bid at or above the earlier (pre-dip) ask minus 1c, else sold at the 6 minute bid as in OP1.
- **Numeric prediction, before the run.** OP1 mean between -3.0c and -0.5c a contract; OP2 between -2.5c and -0.3c; OP3 between -3.0c and -0.5c. All three `FALSIFIED`. OP3 may have too few entries; fewer than 300 reports `NOT_ENOUGH_DATA`.
- **Bar.** The common one for three tries: at least 300 entries on at least 5 days, day clustered z at least 2.5, both halves positive, positive with fees x1.2. Verdict words only `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`.
- **Information only, unable to rescue a failure:** target hit rate, gross with the fee set to zero, by series, and a measurement (no verdict, not a variant): the median spread of the first five minutes by UTC hour and weekday against weekend, which is what ledger rows O36 and O38 asked for first.
- **Count.** Three variants: **2,580 as of this entry** (2,577 plus three).

**2026-10-08 17:25 UTC: OP1 to OP3: all three `FALSIFIED`.** One run of `python -m scalper.openscalp` after its tests and after the correction below, under the rules fixed above. 11,220 markets over 69 days; 6,756 entries for OP1 and OP2, 1,886 for OP3.

| | Entries | Mean | Day clustered z | Halves | Fees x1.2 | Gross of fees | Verdict |
|---|---|---|---|---|---|---|---|
| OP1 +3c, else sell at 6 min left | 6,756 | -3.19c | -16.49 | -3.18c / -3.20c | -3.65c | -0.90c | `FALSIFIED` |
| OP2 +5c, else sell at 6 min left | 6,756 | -3.00c | -13.15 | -2.99c / -3.01c | -3.45c | -0.74c | `FALSIFIED` |
| OP3 dip of 3c, sell near the pre-dip price | 1,886 | -3.04c | -6.18 | -2.35c / -3.74c | -3.50c | -0.78c | `FALSIFIED` |

- **CORRECTION, and why it is in this entry.** The first run of this file (and of `cheapscalp`) looked for the target on every later candle, including those after the 6 minute mark where the position had already been sold. That run showed OP2 at +0.54c (z 2.40, both halves positive) and OP3 at +0.81c (z 1.98), better than the registered predictions, and the habit here is that every earlier error flattered the result, so it was audited before being believed. The bug was against the rule as registered; it is fixed, tested, and the numbers above are from the corrected run. The first run is withdrawn. Lesson, kept: **a result better than its own pre-registered prediction is a reason to audit, not to celebrate.** The same bug had also flattered C2 and C3, corrected above.
- **Prediction against outcome.** Predicted OP1 between -3.0c and -0.5c, OP2 between -2.5c and -0.3c, OP3 between -3.0c and -0.5c, all \`FALSIFIED\`. The verdicts were right and the losses came out a little larger than the ranges (-3.19c, -3.00c, -3.04c). Hit rates are high (OP1 76.6%, OP2 71.4%, OP3 68.6%) and the average loss is large (-26c to -30c against +4.9c to +6.5c wins): the same lopsided shape as L1, without L1's favorite-longshot premium.
- **No gross edge either.** With the fee set to zero these trades still lose (-0.74c to -0.90c). Selling a favorite early gives up the late favorite premium that L1 collects by holding to the close.
- **Measurement, no verdict (ledger rows O36 and O38).** The median spread of the candles 1 to 5 minutes in is 1.0c in every UTC hour and for both weekdays and weekends. There are no cheap hours to select on; the spread is the same everywhere, so gating entries by hour cannot lower cost. Row O36 is closed by this measurement.
- **Count.** Three variants: **2,580 as of 2026-10-08**.

## Amendment to the size ladder: reviews every 3 days, and a look at cheaper contracts (2026-10-08, information only, written before the change ships)

- **The change.** Size reviews, and at most one step up, now come every **3 days** instead of weekly (`SCALE_REVIEW_MS`). A loss stop still holds the cap and the profit add-on for a **full week** (`SCALE_STOP_PAUSE_MS`), so a bad run slows the climb more than a good one speeds it. The cap still falls at once when the balance falls. Overrides the ladder's evidence gates, as the earlier amendment did, at the owner's direction.
- **"Cheaper contracts" read as a lower dollar figure per contract** (more contracts per dollar of balance). `python -m scalper.sizing` now prints the last table. 10 weeks resampled from the 69 days, start $344, 60% fills, skim on, with the live loss stop modelled (10% of the balance at the last review, the day ends and the owner restarts next morning, a week's pause on step-ups after a stop):

| Dollars per contract | Steps | Mean | 5th pct | Deepest drawdown (95th) | Paths that lose | End cap |
|---|---|---|---|---|---|---|
| $100 | 3 days | +$47.8 | -$4.8 | $43 | 6.9% | 3.0 |
| $85 (live) | 3 days | +$62.3 | -$6.8 | $50 | 7.6% | 3.9 |
| $70 | 3 days | +$76.6 | -$2.0 | $60 | 5.9% | 4.8 |
| $60 | 3 days | +$91.4 | -$2.2 | $71 | 5.8% | 5.8 |
| $50 | 3 days | +$113.0 | -$3.7 | $85 | 5.7% | 7.3 |

- **Steps barely matter; the dollar figure per contract does.** Weekly against 3 day steps at $85: +$60.8 against +$62.3. The cap reaches the balance's limit within a couple of reviews either way, so the speed of the steps changes little over 10 weeks. The dollars per contract set where it ends up.
- **Each $10 cheaper adds roughly $14 to $20 of mean and about $10 to $14 of deepest drawdown.** The 5th percentile stays near break-even at every row, because most of the downside sits in the 1% tail, not the 5th (1st percentile -$27 at $85, -$45 at $50).
- **The modelled loss stop never trips (0.00 stop days).** 10% of a $344 balance is $34, and a bad day at 4 to 7 contracts loses well under that in this history (one loss is $3 to $6). At this size the stop is a guard against a failure of the system, not a limit on a bad day of normal trading.
- **Cheaper in the other sense, a lower price band, is worse per dollar.** From B1 to B3: the 88c to 90c band returned -0.56% per dollar risked, 90c to 92c +1.37%, 92c to 95c +2.02%, 95c to 97c +0.24%. More contracts per dollar by buying the cheapest contracts concentrates risk in the weakest band.
- **What this does not say.** Resampled history with a made-up fill rate; the edge (+0.9c a contract) is unproven and failed its own bar, and a size that doubles the mean also roughly doubles the loss if the edge is zero. Forward checks F0 to F9 still decide whether any of this is real.
- Count: unchanged, **2,577 as of 2026-10-08**.

## Pre-registration: two more filters on L1, OP4 and OP5 (ledger rows O17 and O19; fixed 2026-10-08 17:46 UTC, before any code and before either split was computed)

Same method as Q1 to Q3: take L1 as live and ask whether a stated reason to distrust some entries removes the bad ones. Each filter is one fixed definition, with no threshold searched.

**Base.** L1 as `lstrats.hold_rule(L1)`: the candle ending 6 minutes before the close, the favourite whose ask is 0.88 to 0.97, taker at the ask, fee `0.07 p (1 - p)`, held to settlement, both series, all 69 days. Every one of these days has been seen by L1, so a pass would only be permission to test forward.

| Name | Arm (entries kept) | Complement (entries removed) | Excluded from both and counted |
|---|---|---|---|
| OP4 early favorite | The side bought already had an ask of **0.85 or more** at the candle ending 600 seconds before the close (10 minutes left, a real quote) | The same side's ask was below 0.85 at that candle | No valid quote at that candle |
| OP5 tight book | The entry candle's spread (YES ask minus YES bid) is **0.02 or less** | The spread is wider than 0.02 | none |

- **Counterparty.** OP4: whoever sells a favorite that has been a favorite for minutes is the longshot buyer, least wrong when the market agreed early and most wrong in markets that only became lopsided late. OP5: a wide book at 6 minutes left is a thin book where the favorite premium is smaller.
- **Numeric prediction, before the run.** OP4: arm net about +1.2c a contract on about 1,500 entries, complement about +0.3c, difference under 1c. OP5: arm about +0.9c, nearly all entries, the complement too small to judge. **The pre-registered expectation is that neither passes.**
- **Bar.** Two filters, so: the arm has at least 300 entries on at least 5 days, mean above zero with day clustered z at least 2.3, both halves positive, positive with fees x1.2, above the fair-market 95th percentile (each entry winning with probability equal to its own price), AND the arm minus the complement is positive with a day clustered z of at least 2.0. Verdict words only `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. Passing is permission to test forward and nothing more.
- **Size, stated.** The ledger row says "size up". A size rule does not change the per contract mean; it is only worth considering if the arm's per contract mean is clearly above the complement's, which is what the difference test checks. No sizing change is proposed here.
- **Count.** Two variants: **2,582 as of this entry** (2,580 plus two).

**2026-10-08 17:48 UTC: OP4 and OP5: both `FALSIFIED`.** One run of `python -m scalper.l1filters2` (after its tests), under the rules fixed above. Nothing was changed after seeing it. Base L1: 3,432 entries, +0.92c, z +2.61, 69 days.

| Filter | Arm | Arm net (z) | Halves | Fees x1.2 | Complement | Arm minus complement (day clustered z) | Fair-market 95th pct | Verdict |
|---|---|---|---|---|---|---|---|---|
| OP4 early favorite (ask 0.85 or more at 10 min left) | 863 | +1.84c (+2.62) | +2.27c / +1.42c | +1.76c | 2,561, +0.63c | +0.18c (+0.12) | +1.03c | `FALSIFIED` |
| OP5 tight book (spread 0.02 or less) | 3,350 | +1.02c (+2.90) | +1.32c / +0.72c | +0.92c | 82, -2.95c | +7.73c (+1.31) | +0.24c | `FALSIFIED` |

- **OP4: the arm looks good and the filter does not work.** The arm clears every arm test (z 2.62, both halves, fees x1.2, above the fair-market 95th percentile) and L1 as a whole nearly does too (z 2.61), so the arm test does not tell the filter apart from L1. What the filter has to show is that the arm beats its complement, and per day it does not: +0.18c, z +0.12 (pooled over all entries the gap is +1.21c, which shows how much of it is a few days). The prediction was an arm at about +1.2c and a gap under 1c: the arm came out higher (+1.84c), which is why the construction was audited (the candle read is 10 minutes before the close, earlier than the entry, and no result is read); nothing was wrong, it is selection and noise on 863 entries.
- **OP5: nearly every L1 entry is already a tight book.** 3,350 of 3,432 entries have a spread of 2c or less, so the arm is L1 itself (+1.02c against +0.92c). The 82 wide-book entries lost 2.95c on average, which sounds like the filter helping, but on 82 entries the day clustered z is +1.31. Skipping them would have added +0.10c to L1's mean.
- **No sizing change.** The arm's per contract mean is not reliably above the complement's (OP4), so "size up on an early favorite" has no support beyond this noise.
- **Count.** Two variants: **2,582 as of 2026-10-08**.

## Live fills study: the signals the order misses are where the losses are (information only, no hypothesis, no verdict; 2026-10-08 17:59 UTC)

The owner asked about the 41% of L1 signals that do not fill. `python -m scalper.fillstudy` reads `studies/fills_2026-10-08.csv`: all 57 L1 orders in the owner's own diagnostics export from 2026-10-07 and 2026-10-08, each scored at the price the bot SAW whether or not it filled (a miss is scored on what it would have made, not on a fill it never got), with the settled result taken from Kalshi's public market data afterwards. The 40c and 50c test orders are not included.

| | Orders | Lost | Mean per contract at the decision price |
|---|---|---|---|
| Filled | 35 | 0 | +6.27c |
| Missed (no fill) | 22 | 4 | -10.83c |

- **The losses are concentrated in the misses.** All 4 losses were signals that did not fill; none of the 35 fills lost. One sided Fisher exact p = **0.019**. Bitcoin: 17 filled (0 lost), 13 missed (3 would have lost). Gold: 18 filled (0 lost), 9 missed (1 would have lost).
- **The misses are not a limit price or size problem.** In the 37 orders that carry a book snapshot, every miss was marketable at the limit on the book the bot saw, and most had hundreds to thousands of contracts at the touch (the two with almost none were Bitcoin yes orders at an ask size of 0.02). The book moves in the roughly half second between the read and the order's arrival, and the misses are the ones where it moved away. Six of the 23 filled orders filled at 1c to 4.4c BETTER than the quote, and all six won.
- **What it suggests, and does not prove.** An immediate-or-cancel order at the touch fills when the quote is stable and misses when it is flickering, and flickering quotes sit in the markets that end badly. So the 41% miss rate may be a free quality filter, and chasing the misses (a higher limit, a retry at 5 minutes left, a resting order) would add the worse trades. That agrees with the earlier finding that resting orders filled on losers (P2). It would also mean the backtest, which fills every signal at the ask, understates the per fill edge and overstates the volume.
- **Why it is weak.** 57 orders, 4 losses in all, a pooled loss rate of 7.0%, found by looking, once. It is not a pre-registered test and a p of 0.019 from one look at one sample is a lead, not a result. The right next step is to keep recording: a pre-registered version (misses lose more than fills, on at least 150 further orders) can be written now and read when the forward check reads, about 2026-10-23.
- **Decision rule until then.** Do not raise the limit, add a retry or add a resting order to "fix" the fill rate. Count: unchanged, **2,582 as of 2026-10-08**.

## Sizing replay at the deployed rule: 1% per position, $509, trailing stop (information only, no hypothesis, no verdict, no variant counted; 2026-10-08)

`python -m scalper.sizing current` after the history was re-downloaded (11,050 markets, 69 days). Rule as deployed: cap starts at 3 with the stop base at $344 and reviews every 3 days, $85 a contract, only new net profit highs are skimmed (half to the pool), a position never risks more than 1% of cash, the stop is 5% of the balance at the last review. 10 weeks resampled by day, 60% fills, 3,000 paths, starting from $504.82.

| Rule | Mean | 5th pct | 1st pct | Deepest drawdown (95th) | Paths that lose | End cap | Stop days |
|---|---|---|---|---|---|---|---|
| Old: add-on max 2, ceiling 10 | +$82.6 | -$7.6 | -$42.0 | $73.4 | 6.5% | 5.8 | 0.00 |
| Deployed: add-on uncapped | +$82.6 | -$7.6 | -$42.0 | $73.4 | 6.5% | 5.8 | 0.00 |
| Deployed + trailing stop | +$82.6 | -$7.2 | -$44.4 | $73.6 | 6.4% | 5.8 | 0.00 |
| Sized on the usable shard only (before the shards were merged) | +$59.9 | -$10.3 | -$29.9 | $52.1 | 8.7% | 3.9 | 0.00 |
| 3 contracts flat (the stake until this morning) | +$43.8 | -$6.1 | -$27.1 | $44.4 | 7.3% | 3.0 | 0.00 |

- **Removing the add-on limit changes nothing at this balance.** Rows one and two are identical, because the 1% per position rule is what binds (about 5 contracts at $509). The uncapped add-on only matters once the balance, and so the 1% cap, rises well past the target of 5 or 6 contracts.
- **The trailing stop changes nothing measurable either.** The stop trips on 0.00 days a path in all rows: in this model a day's losses almost never reach 5% of the base. Its mean is the same; its 1st percentile is a little worse in this sample (-$44.4 against -$42.0), inside the noise of 3,000 resampled paths. Whether it helps in a real gap (one bad cluster of orders) is not something this replay can show.
- **What the 1% size costs.** Against 3 contracts flat: about +$39 more over 10 weeks, and the bad cases roughly 1.6 times as deep (1st percentile -$42 against -$27, drawdown $73 against $44, about 14% of the account). That is the trade, stated plainly: more money in the average path, a larger hole in the bad ones.
- **Limits of the replay.** The 69 days were all seen by L1's design, the edge is thin (z 1.45 against a bar of 2.1 on the first test), fills are a round 60%, and the loss stop is modelled by day, not by a rolling 24 hours. Treat the mean as an upper bound and the drawdown as a floor.
- Count: unchanged, **2,582 as of 2026-10-08** (sizing, not a strategy variant).

## Pre-registration: T1, early taker flow (ledger row L11; fixed 2026-10-08, before any trade was fetched and before any imbalance or result was computed)

The owner asked for more ideas for the first 5 to 10 minutes of each market. Every NEW ledger row that can run on candles is already run or overlaps a falsified one (O21 is OP5 reworded: 3,350 of 3,432 entries already had a tight spread; O35 to O38 only gate rules that are already `FALSIFIED`; O46 changes the average entry, not the expectation). The rows that remain NEW need books (resting entries, depth, staleness), and the recorder has had under a day. **L11 is the one row that is new and can be built now**, because Kalshi's trade tape is public and not login gated. Nothing below has been run.

- **Counterparty.** Whoever quotes the market in the first minutes (the market maker side), which can be run over by informed takers. If takers in minutes 0 to 4 lean one way and that lean is information, the quote at minute 5 is late. If the lean is only noise, takers lose the spread and the rule loses.
- **Rule (all of it fixed now).** For each market, over the first 5 minutes after open, signed flow I = (YES taker contracts minus NO taker contracts) divided by total taker contracts, from the trade tape (`taker_side`, `count`, `created_time`). Signal at the end of minute 5 when total taker contracts is at least 50 and |I| is at least 0.60. Buy the side the flow favors at its ask on the first candle that STARTS after minute 5 (never the signal bar), hold to settlement. Both series, one contract. No other threshold is tried.
- **Universe.** The most recent 30 days of settled KXBTC15M and KXGOLD15M markets (about 3,800 markets), chosen by recency to bound the fetch, not by return. Selected on **fixed** (not cost).
- **Numeric prediction.** Mean net **+1.0c per contract** after fees, with a win rate at least 2 points above the average price paid.
- **Kill criteria.** Any one gives `FALSIFIED`: fewer than 300 signals; fewer than 5 distinct days; day clustered z below 2.1 (the bar the earlier tests were held to); mean net at or below 0 after fees times 1.2; either half of the days negative; the result flips sign when the 50 contract minimum is raised to 100. A result better than +1.0c is an audit trigger before it is believed, not a win: check that the fill bar starts after the signal and that no trade after minute 5 is in I.
- **Deflation.** Counts as ONE variant when it runs (tally 2,582 now, 2,583 after). One threshold, one horizon, one entry rule: no grid.
- **What a pass would still not be.** A pass here is `NOT_YET_FALSIFIED`, not an instruction to trade. It would need its own forward window before any live size, like every earlier rule.
- **Build order.** `tapeflow.py` fetches the first-5-minute trades for each market in the universe (resumable, one SQLite table, public endpoint only), with a test that no trade stamped after minute 5 can enter I. Then it runs once.

**Rows left, and why they wait.** Resting entries (O1 to O3, O5, O7, O8), depth (O36, L12, O47 to O49) and staleness (L5, O11, O50) need days of recorded books, and the recorder started 2026-10-08. They are `NOT_RUNNABLE` today and not counted.

## Pre-registration: T2, early taker flow, closed before L1 (fixed 2026-10-08, before the T1 fetch finished and before any T1 or T2 result was computed)

The owner's design goal for the opening window is trades that **open and close inside it**, so they add to L1 instead of replacing it: L1 enters 6 minutes before the close (its window is 400 s to 330 s left) and must find the market and the cash free. T1 holds to settlement, which breaks that goal. T2 is the same signal with a time exit.

- **Rule.** Same signal, universe and entry as T1 (README, "Pre-registration: T1"): at least 50 taker contracts and |YES minus NO| / total of at least 0.60 over the first 300 s, buy the favoured side at its ask on the candle ending 360 s after the open. **Exit:** sell at that side's bid on the candle ending 480 s after the open (7 minutes left, strictly later than the entry, a real two sided quote required; no quote means no observation). Taker fee on both legs, 7% unrounded. No target, no stop, one exit time. The position is flat 60 s or more before L1's window opens.
- **Counterparty.** Same as T1: the market maker who quotes the first minutes and is late to a one sided flow.
- **Prediction, before the run: it does not pass.** Every earlier round trip in this window (M1, C1 to C3, OP1 to OP3) was negative after cost, and opening spreads are 1.0c, so a round trip costs about 2c to 3c in spread and fees before any move. The registered point estimate is **-0.5c per contract**; it needs a gross drift above that cost to reach zero.
- **Kill criteria.** Identical to T1: any one gives `FALSIFIED` (fewer than 300 signals, fewer than 5 days, day clustered z below 2.1, mean at or below zero, at or below zero with fees x1.2, either half negative, or negative at the 100 contract volume bar).
- **Count.** One more variant when it runs: **2,584 after T1 and T2** (2,582 now). A result better than the prediction is an audit trigger first: check the exit candle starts after the entry candle and that only trades before 300 s are in the imbalance.
- **Not a live proposal.** Even a pass would be `NOT_YET_FALSIFIED`: a forward window comes first, and running it live would also need the bot to hold a second position type and keep its cash and loss stop accounting separate from L1's.

## Pre-registration: T3, the early drift scalp at tick level (the owner's own trade, fixed 2026-10-08, before any trade bar was fetched and before any result was computed)

The owner showed a screen recording of a manual scalp: BTC 15 min, about 52 seconds after the open, spot already $17 under the target and falling, bought Down for $1 at about 62c (the chance read 61%), sold about a minute later at 68.5% for $1.09. That is the "buy the side spot is leaning toward early, sell a few cents higher" idea, which the ledger already holds as O25 and O29 (`OVERLAP` M1 and H2, falsified on one minute candles, about -2c to -3c a trade). **What is different, and the only reason to run it:** candles could not see a trade that opens and closes inside a minute. The trade tape can: every print has a timestamp to the microsecond and the price a taker paid, so entries and exits can be priced at prints that actually happened, one second at a time. This resolves one question, whether sub-minute timing changes the verdict, and it is disclosed as a re-test of a falsified family, not a new mechanism.

- **Data.** The same fetch as T1 and T2, now also stored as one row per second of the first 300 s (`tape_s`): the first print by a taker buying YES (the ask paid), the first print by a taker buying NO (where the YES bid was), the last price and contracts by side. Nothing after second 299 is stored or used. Universe: the most recent 30 days of settled KXBTC15M and KXGOLD15M markets, chosen by recency, not return.
- **Rule (all fixed now, one parameter set).** Signal: the price (last print) at the end of second 60 minus the price at the end of second 20, using prints before second 60 only. A drift of **3c or more** up means lean YES, 3c or more down means lean NO; anything smaller is no signal. Entry: the first print by a taker buying the leaning side at second 61 or later (one second of latency), at that print's price, which must be **55c to 70c** (the owner's trade was at about 62c). Exit: the first later second whose opposite taker print puts our bid at **entry plus 5c or better**, else the first opposite taker print at or after second **240** (11 minutes left, flat before L1's window). A market that never prints an exit has no observation and is counted. Taker fee on both legs, 7% unrounded, one contract.
- **Counterparty.** The market makers who quote the open and are slow to move their quotes as spot drifts away from the strike: they sell us the leaning side at a stale price, then reprice.
- **Numeric prediction, before the run: it does not pass.** Registered point estimate **-1.5c per contract** after fees, a median hold under 2 minutes. A round trip costs about 3c in fees and about 1c in spread; the candle versions averaged -2c to -3c. It would need an average gross drift of more than 4c in the first minutes to reach zero.
- **Kill criteria.** The same as T1 and T2, any one gives `FALSIFIED`: fewer than 300 observations, fewer than 5 days, day clustered z below 2.1, mean at or below zero, at or below zero with fees x1.2, either half of the days negative, or negative among markets with at least 100 taker contracts in the first 300 s. A better result than -1.5c is an audit trigger before it is believed: check that no print before second 61 is the entry and none at or before the entry second is the exit.
- **Count.** One more variant: **2,585 after T1, T2 and T3** (2,582 now). No grid and no re-run with other thresholds; if it fails, the thresholds stay failed.
- **Limits, stated now.** A taker print is a real fill at that price, but it is not our fill: it ignores that our own order would also move the book and that the first print in a second may not be the one we would have caught. The spot the owner watched is not in this data (candles are one minute); the market's own price drift is the proxy for spot's lean. A pass would be `NOT_YET_FALSIFIED` only, with a forward window and the bot changes (a second position type, its own cash and stop accounting) still ahead.

## Pre-registration: T4, the cheap side scalped at tick level (the owner's idea, fixed 2026-10-08, before any trade bar was read and before any result was computed)

The owner showed a Kalshi screen with Up priced at 6.2% (14.88x) and asked for a strategy that snags a couple of low priced contracts and sells a few cents higher. This is the family already measured as C1 to C3 (the cheap side scalped early, corrected means -3.28c, -2.27c and -2.33c, `FALSIFIED`), so it is disclosed as a **re-test at tick level of a falsified family, not a new mechanism**. The one thing it adds is the same as T3's: candle closes could not see entries and exits inside a minute, and the trade tape can. The reason to expect it to look better than it is: a 6c contract pays only about 0.4c in fee a side, so the fee is small, but the spread is not (a 1c spread is 17% of the price), and a 3c rise on a 6c contract is a 50% move.

- **Rule (all fixed now, one parameter set).** Data as T3 (`tape_s`, the first 300 s). No signal. Entry: the first print from second **61** up to but not including second **180** by a taker buying a side that costs **4c to 10c** (YES at its print price, NO at 1 minus the YES price of a NO taker print), at that print's price. Exit: the first later second whose opposite taker print puts our bid at **entry plus 3c or better**, else the first opposite taker print at or after second **240**. A market that never prints an exit has no observation and is counted. Taker fee on both legs, 7% unrounded, one contract.
- **Counterparty.** Whoever sells a cheap contract just before spot moves toward the strike: a cheap side near the strike is convex, so a small spot move reprices it by several cents, and the market makers who quote it are slow.
- **Numeric prediction, before the run: it does not pass.** Registered point estimate **-1.0c per contract**, with a win rate (exit above entry) under 40%. The cheap side mostly decays to zero (a 6c side loses its 6c about 94% of the time at settlement); the bet is that a few small repricings before the time exit pay for the rest. The spread alone is about 1c a round trip.
- **Kill criteria.** The same as T1 to T3, any one gives `FALSIFIED`: fewer than 300 observations, fewer than 5 days, day clustered z below 2.1, mean at or below zero, at or below zero with fees x1.2, either half of the days negative, or negative among markets with at least 100 taker contracts in the first 300 s. A better result than -1.0c is an audit trigger first: check the entry print is inside seconds 61 to 179 and the exit print is later than the entry second.
- **Count.** One more variant: **2,586 after T1 to T4** (2,582 now). One parameter set; no re-run with other bands, targets or times.
- **Limits.** A taker print is a real price but not our fill, and our own order would move a thin book; cheap sides are the thinnest part of the book, so a print at 6c may not be there in size. A pass would be `NOT_YET_FALSIFIED` only, with a forward window, and the bot changes (a second position type, its own cash and stop accounting) still ahead. A loss at settlement on a 6c contract is the whole 6c, so size stays at one contract per position until a forward window says otherwise.

## Amendment to T1 to T4: the fetch is far slower than estimated, so the sample is an even 1,240 markets (fixed 2026-10-08 22:20 UTC, before any T1, T2, T3 or T4 result was computed)

**What happened.** The plan was to fetch the first 5 minutes of trades for all 4,964 settled markets of the last 30 days, which I estimated at 1 to 3 hours. Measured over the first hour it stored 100 markets, about 40 seconds each, because Kalshi's public trade endpoint answers 429 (rate limited) most of the time and a Bitcoin market's first 5 minutes holds 5 to 10 pages. That is about 55 hours for the full universe. No result of any kind had been computed; the 100 markets stored so far were deleted so the sample would be clean.

**The change (nothing about any rule, threshold, prediction or kill criterion changes).**
- **Fetch order.** Markets are fetched as every 8th market of the 30 days, then the next offset (offsets 0, 4, 2, 6, 1, 5, 3, 7), so any stopping point is an even sample of every day, not the oldest block.
- **Stopping point, stated now.** The result is read ONCE, at **1,240 markets** (offsets 0 and 4, about 620 each) or when the fetch ends if that is sooner. No look at partial results, no extension if the sample disappoints.
- **What this costs.** Power. With fewer markets, fewer observations: T1 needs 300 signals out of the markets with at least 50 taker contracts and a 60% imbalance, and may not reach it, in which case it is `FALSIFIED` by the pre-registered rule and says nothing about the idea. Each run prints the signal count first so an underpowered run is not mistaken for a real failure. T2 uses the same signals as T1 and has the same problem. T3 and T4 produce an observation for a larger share of markets and are more likely to reach 300.
- **Counts.** Unchanged: T1 to T4 are four variants, **2,586 once run**.

## Amendment: the profit-funded add-on sits outside the 1% rule (2026-10-08 evening, at the owner's direction; information only, no variant counted)

The owner asked that contracts bought with reinvested profit have **no cap**, a hard cap on the rest being acceptable. The earlier change removed the add-on's own limit of 2 but left the 1% of cash rule on the whole order, so at $511 (cap 5, 1% of cash about 5 contracts) a pool of any size added nothing: the replay rows "old" and "now" were identical for that reason. The code now holds only the account-funded part to 1% of cash (`l1Count(cash, cost, cap, addon)`); the add-on is added on top, still bounded by the pool (one extra contract per full contract cost, a loss comes out of the pool first) and by the single order guard of 50.

Replay, `python -m scalper.sizing current` (10 weeks from $504.82, 60% fills, the 5% stop, 3,000 paths):

| Rule | Mean | 5th pct | 1st pct | Deepest drawdown (95th) | Paths that lose | Stop days a path |
|---|---|---|---|---|---|---|
| Add-on inside the 1% rule (deployed earlier) | +$82.6 | -$7.6 | -$42.0 | $73.4 | 6.5% | 0.00 |
| Add-on outside the 1% rule (this change) | +$86.7 | -$10.1 | -$47.4 | $86.5 | 7.5% | 0.12 |

- **The cost is real and small now.** About +$4 more in the average path, and the bad cases about 15% deeper (drawdown $86 against $73, 17% of the account). The stop trips on about one path in eight over the 10 weeks, where before it almost never did.
- **It grows with success, which is the point and the risk.** The pool only grows after new profit highs, so early on it is a few extra contracts; later it can be a large share of an order. The pool bounds the add-on's risk to profit already made, but a run of losses empties the pool first and then eats into the account-funded part.
- Count: unchanged, **2,582 as of 2026-10-08** (sizing, not a strategy variant).


## Results: T1 to T4, one run each, read once at 1,240 markets (2026-10-09 05:50 UTC; the rules, thresholds, predictions and kill criteria are those registered above and in the amendment; nothing was changed after seeing them)

`python -m scalper.tapeflow run` over an even sample of 1,240 of the last 30 days' 4,964 settled BTC and gold markets (interleaved fetch, stopping point fixed in advance). Signal counts first, as promised:

| Test | Markets read | Observations | Days | Mean net per contract | Day clustered z | Halves | Fees x1.2 | Predicted | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| T1 early taker flow, held to settlement | 1,240 | **13** | 10 | -8.92c | -1.03 | -3.90c / -13.22c | -9.08c | +1.0c | `FALSIFIED` |
| T2 the same, sold 7 minutes before the close | 1,240 | **13** | 10 | -6.52c | -2.54 | -6.46c / -6.57c | -6.81c | -0.5c | `FALSIFIED` |
| T3 early drift scalp (the owner's recorded trade) | 1,240 | **780** (460 with no observation) | 31 | -4.11c | -10.22 | -3.72c / -4.52c | -4.74c | -1.5c | `FALSIFIED` |
| T4 cheap side scalp, seconds 61 to 179 | 1,240 | **19** (1,221 with no observation) | 14 | +1.07c | +1.22 | +0.52c / +1.57c | +0.82c | -1.0c | `FALSIFIED` |

Count: four variants, **2,586 as of 2026-10-09**.

- **T1 and T2 are underpowered, and the verdict says nothing about the idea.** Only 13 markets had at least 50 taker contracts and a 60% one sided flow. The reason is in the data: the typical market's first 5 minutes holds about 250,000 contracts a side, almost evenly split, so a 60% imbalance is rare. The 13 that qualified paid an average of 15.8c for the side bought (win 7.7%), which shows the registered flow measure counts CONTRACTS, and contracts are dominated by cheap lottery-ticket buying, not by money. That is a flaw in the pre-registered metric, found after the run; a dollar weighted flow is a different variant and would have to be registered as one. Nothing was re-run.
- **T3 is a decisive, large sample failure, worse than predicted (-4.11c against -1.5c).** It wins most of the time (69.2% of trades sold above entry, median hold 61 seconds, a +5c target) and still loses 4c a trade: many small wins, and a minority of exits at the time limit far below entry that outweigh them. Both halves negative and z -10 make this the clearest result of the day. Fees alone are about 3c of it. It tells us the owner's recorded trade, taken as a rule at tick level with real trade prices, loses money on average; a single winning trade is inside the noise of that.
- **T4 almost never fires, and that is a finding about the design, not an edge.** Only 19 of 1,240 markets had a taker print on a 4c to 10c side between seconds 61 and 179 and a later exit print. At the open the market is near 50 to 50, so a 6c side does not exist yet. **The owner's own examples were at about 5.6 and 8 minutes into the market**, outside this window; the window was set to "early" without checking that against the examples. A later window (for example minutes 4 to 9 after the open) is a different question and would be a new variant (2,587) registered before it runs; the +1.07c on 19 trades is not evidence of anything.
- **Audit triggers.** None fired: no result was better than its prediction except T4's, which has 19 observations (far under 300). The invariants held by test: the entry print is after the signal second and the exit print after the entry in T3 and T4; only trades before second 300 enter the first-5-minute flow.

## Amendment: the loss stop does not count profit-funded losses (2026-10-09, at the owner's direction; information only, no variant counted)

**The problem.** The stop trips when the bot's own trades over the last 24 hours, settled losses plus open orders counted as lost, are down by 5% of the balance at the last review (about $25 at $509). The profit-funded add-on has no count cap. If the pool ever bought enough extra contracts (about 25 at $0.95 each, or about $28 for one order), a single loss, or even one such order merely sitting open, would reach the stop by itself and end the session. The stop is checked at the start of each minute, so the open order alone would have been enough.

**The rule.** Each order now records how many of its contracts were bought with reinvested profit (`addon`, `addonCost`). The stop becomes **5% of the balance at the last review plus the profit-funded cost of the orders that are lost or still open** in the 24 hour window. In words: the stop counts only the account's own share of a loss. A $28 order whose add-on cost $23.80 can lose in full without stopping the bot (only $4.20 was account money), and a loss that eats the profit and then more than 5% of the account still stops it. Orders from before this change carry no add-on fields and behave as before. Winning orders add nothing to the allowance. It applies to the trailing stop the same way.

**Why it is consistent.** The pool holds only profit already banked, and a loss comes out of the pool first. The widened stop is exactly the profit that was staked plus the same 5% of capital as before, so the account's exposure to a stop-level loss is unchanged.

**Replay (`python -m scalper.sizing current`, 10 weeks from $504.82, 60% fills, 3,000 paths), add-on outside the 1% rule:**

| Stop | Mean | 5th pct | 1st pct | Deepest drawdown (95th) | Paths that lose | Stop days a path |
|---|---|---|---|---|---|---|
| Plain 5% | +$86.7 | -$10.1 | -$47.4 | $86.5 | 7.5% | 0.12 |
| 5% plus the profit-funded share of a lost order | +$86.8 | -$8.4 | -$44.6 | $88.6 | 6.9% | 0.00 |

The widened stop almost never fires in the model, which is what it is for: it keeps the bot running through the one bad order that the add-on's own size would otherwise end it on. The deeper drawdown is about $2, inside the noise of the sample. Count: unchanged, **2,586 as of 2026-10-09** (a stop rule, not a strategy variant).

## Sizing replay: 2% base per position instead of 1% (information only, no hypothesis, no verdict, no variant counted; 2026-10-09)

The owner chose a 2% base per position (ladder $43 a contract, ladder ceiling 25) over the 1% set the day before. `PYTHONPATH=src python -m scalper.sizing base2`, same 69 days of history, from $547.96 with the base re-seeded to it (what Start does), 60% fills, 5% stop, pool add-on outside the base rule.

| Rule | Mean (10 wk) | 5th pct | 1st pct | Deepest drawdown (95th) | P(loss) | Stop days |
|---|---|---|---|---|---|---|
| 1% base, $85 | +$95.1 | -$12.6 | -$45.9 | $94.3 | 8.5% | 0.00 |
| 2% base, $43 | +$157.7 | -$9.5 | -$90.6 | $146.3 | 6.3% | 0.84 |

- **About 1.7 times the mean for about 2 times the bad tail.** The 1st percentile doubles (-$45.9 to -$90.6) and the bad drawdown goes from about 17% to about 27% of the account. That is the trade the owner chose, written down so it is not rediscovered.
- **The stop starts to bind.** 0.84 stop days over the window against none at 1%: two losses at this size reach 5% of the base.
- **A replay of the past, not a forecast.** The win rate it replays is the tape's, and the 73 of 74 live record is a small sample (the one loss was the early 40c test order).

## Pre-registration: T5, the cheap side scalped at tick level in minutes 5 to 8 (the owner's idea, a corrected window for T4; fixed 2026-10-09, before any trade after second 299 was fetched and before any result was computed)

**Why this exists.** T4 was meant to test the owner's cheap-side scalp but its window (seconds 61 to 179) was set without checking it against the owner's own examples, which were about 5.6 and 8 minutes into a market. At second 61 to 179 the market is near 50 to 50, so a 4c to 10c side almost never exists (19 observations in 1,240 markets). T5 is the same rule in the window the examples came from. It is disclosed as a **re-test at tick level of a falsified family (C1 to C3, T4), not a new mechanism**; what it adds is a window in which the cheap side exists.

**Data, and what was found before writing this.** The stored tape (`tape_s`, the 1,240 markets T1 to T4 used) covers only seconds 0 to 298, so it cannot test this window. A new table `tape5` is fetched for the SAME 1,240 markets, seconds 300 to 599 (a timing probe on one Bitcoin market: 12 pages, 11,552 trades, 23 s; about 8 hours for all 1,240). Nothing from seconds 300 to 599 has been read.

- **Rule (fixed now, one parameter set, identical to T4 except the clock).** No signal. Entry: the first print from second **300** up to but not including second **510** by a taker buying a side that costs **4c to 10c** (YES at its print price, NO at 1 minus the YES price of a NO taker print), at that print's price. Exit: the first later second whose opposite taker print puts our bid at **entry plus 3c or better**, else the first opposite taker print at or after second **570** (the end of L1's window, 330 s left). A market that never prints an exit has no observation and is counted. Taker fee on both legs, 7% unrounded, one contract.
- **Counterparty.** Whoever sells a cheap contract just before spot moves toward the strike: a cheap side near the strike is convex, so a small move reprices it by several cents, and the market makers quoting it are slow. Same story as T4; it is not a new one.
- **Numeric prediction, before the run: it does not pass.** Point estimate **-1.0c per contract**, win rate (exit above entry) under 40%. The same reason as T4, plus one that matters more here: by minutes 5 to 8 a 4c to 10c side usually means the market has already decided, so the cheap side decays toward zero rather than bouncing. Expected observations: **100 to 400** (a guess; T4's 19 is no guide because the window differs), so the 300 minimum may well not be reached.
- **Kill criteria.** The same as T4, any one gives `FALSIFIED`: fewer than 300 observations, fewer than 5 days, day clustered z below 2.1, mean at or below zero, at or below zero with fees x1.2, either half of the days negative, or negative among markets with at least 100 taker contracts in the first 300 s. **If fewer than 300 observations is the only thing that fails, the report says so first**, because that is `FALSIFIED` by the rule and says nothing about the idea (the T1 and T2 situation). A better result than -1.0c is an audit trigger first: check the entry print is inside seconds 300 to 509 and the exit print is after the entry second.
- **Stopping point, stated now.** Fetch order is the T1 to T4 order (every 8th market, then the next offset) restricted to those 1,240 markets, so any stopping point is an even sample. The result is read ONCE, at all 1,240 or when the fetch ends. No look at partial results, no extension if the sample disappoints.
- **Count.** One more variant: **2,587 as of 2026-10-09**. One parameter set; no re-run with other bands, targets or times.
- **Limits.** A taker print is a real price but not our fill, and cheap sides are the thinnest part of the book. Seconds 300 to 570 overlap L1's window (500 to 570), so a pass would also need its own cash and stop accounting next to L1. A pass would be `NOT_YET_FALSIFIED` only, with a forward window; the bot is not changed by this section.

**Correction to the table above (2026-10-09, same day).** The first run left the cap starting at 3 and the ladder ceiling at 10, so it did not model what Start and the deployed ceiling of 25 do (the cap goes straight to the target, 12 at this balance). `sizing.path` now takes `cap0` and `cap_ceiling`. Re-run with the deployed settings (70 days, from $547.96, 60% fills, 5% stop, 3000 paths):

| Rule | Mean (10 wk) | 1st pct | Deepest drawdown (95th) | P(loss) | Stop days |
|---|---|---|---|---|---|
| 1% base, $85, ceiling 10, cap 6 | +$100 | -$44 | $97 | 8% | 0.01 |
| 2% base, $43, ceiling 25, cap 12 | +$223 | -$103 | $187 | 8% | 2.68 |

So the 2% base is about 2.2 times the mean for about 2 times the bad tail, and the bad drawdown is about 34% of the account (not 27%) with a stop day about once every 26 days (not 0.84 in the window). The first table understated both the gain and the risk; the direction of the conclusion (more return for proportionally more risk) is unchanged. The same replay, 2% base, at three horizons from $550: mean $638 / $738 / $842 at 30 / 60 / 90 days (5th to 95th percentile $486 to $829, $509 to $1,044, $545 to $1,252); from $1,000: $1,163 / $1,342 / $1,522. About the same percentage growth, about 1.8 times the dollars.

## Pre-registration: S1, size 2x for the first 10 filled trades after a start or a loss (the owner's idea; fixed 2026-10-09, before any code for it and before any result; information only, no verdict word that means trade, no variant counted)

**The idea, as the owner put it.** "Start huge, scale down after x winners": back-to-back losses look unlikely, so be big right after a start or a loss and scale back as wins accumulate.

**Premise check, done before this section from the history (not a result for S1).** Over 3,379 L1 entries the chance the next entry loses after a loss is 5.4% against a 6.0% base rate; the 192 losing runs were 181 singles, 11 doubles and no triples; days with 3 or more losses were 43 against about 38 expected if independent. So adjacent losses are rare and nearly independent, with a mild day-level clustering.

**Rule (fixed now, one parameter set).** In the `sizing.path` replay, a countdown starts at 10 at the start of a path and is reset to 10 by every filled order that loses. While it is above zero, each filled order is sized at **2 times** what the deployed rule would send (base plus pool extras), still capped at the 50 contract order ceiling; each filled order counts it down by one. The boosted contracts are account funded: only the pool add-on counts as profit funded for the stop's allowance. Everything else is the deployed rule (2% base, $43 ladder, ceiling 40, cap starting at the balance target, 5% stop, 3 day reviews, 60% fills, 3000 paths, the real 67 days drawn with replacement). The baseline is the same run with no boost. Both at the $1,000 account and at $550.

**Counterparty / mechanism.** None new. The only claim is statistical: if losses are close to independent, the size schedule changes dollars at risk per trade, not the odds, so the average should move in proportion to the average size and the bad tail should move with it or worse (a loss is more likely to land in a boosted trade, because the boost always sits right after a loss).

**Numeric prediction, before the run.** The mean 10 week gain rises by less than 25% over baseline, while the 1st percentile outcome and the 95th percentile drawdown each worsen by more than 25%, so the mean per dollar of drawdown falls. Stop days rise. I expect the boost **not** to improve the mean gain per dollar of 95th percentile drawdown.

**Reading rule.** Reported side by side: mean, 5th, 1st and 95th percentile ending balance, 95th percentile drawdown, mean gain divided by that drawdown, stop days. The boost is called not helpful if the mean per dollar of drawdown is lower than baseline. A better ratio is reported as an audit trigger first (check the boost applies only after a loss or at the start, and that the stop's allowance is not counting boosted contracts), and as a replay of the past only. Nothing here changes the bot.

**Limits.** The replay's loss rate comes from the 67 days; the live run so far is 74 wins in 74. A 2x boost doubles the size of a single order, and the market's depth at that size is unmeasured.

**Results: S1, one run, read once (2026-10-09; the rule, prediction and reading rule are those registered above; nothing was changed after seeing them).** `PYTHONPATH=src python -m scalper.sizing s1`, 70 days, 60% fills, 3000 paths, the deployed rule with the 5% stop.

| Account | Run | Mean gain | 5th pct end | 1st pct end | Drawdown (95th) | Gain per $ of drawdown | P(loss) | Stop days |
|---|---|---|---|---|---|---|---|---|
| $1,000 | baseline | +$411 | $960 | $820 | $322 | 1.28 | 7% | 2.84 |
| $1,000 | 2x for 10 after a start or loss | +$536 | $881 | $703 | $505 | 1.06 | 10% | 9.71 |
| $550 | baseline | +$223 | $526 | $447 | $187 | 1.19 | 8% | 2.68 |
| $550 | 2x for 10 after a start or loss | +$293 | $477 | $362 | $293 | 1.00 | 11% | 10.15 |

- **Reading rule: not helpful.** The mean gain per dollar of 95th percentile drawdown falls (1.28 to 1.06, 1.19 to 1.00), and stop days rise about 3.5 times (a stop roughly every 7 days, each one emptying the pool and switching the add-on off for a week).
- **Prediction against outcome.** Predicted: the mean rises by less than 25%, the bad tail worsens by more than 25%, the ratio falls, stop days rise. Measured: the ratio fell and stop days rose as predicted; the 1st percentile worsened 65% and the drawdown 57%, as predicted. **The mean rose 30% at both account sizes, not under 25%**, so that part of the prediction was wrong; the boost does add average profit, it just adds more risk than profit.
- **Audit triggers.** No result was better than the baseline on the ratio, so none fired. The boost sits only after a start or a loss by construction, and the stop's allowance counts the pool add-on only.
- **Caveat.** A replay of the past at the history's loss rate; the live record (74 of 74) is far better, and a doubled order is double the depth this market has been measured to fill (nothing measured yet).

## Pre-registration: E1 and E2, L1 unchanged on the ETH and SOL 15 minute markets (the owner's idea; fixed 2026-10-09, before any ETH or SOL market was downloaded and before any result)

**The question.** Does the rule that runs live on Bitcoin and gold (L1) work on the other 15 minute crypto series with enough volume to hold size? The owner wants, if it works, to expand there: first a simulated run, then a small live stake that scales up faster than BTC and gold did until it matches their dollar amounts. This section is only the first step, the test on history.

**Why ETH and SOL, and nothing else.** A check of Kalshi's public data on 2026-10-09 (median contracts traded per settled market, sample of 20): Bitcoin 3,503,802; gold 458,140; ETH 174,633; SOL 90,434; XRP 71,986; DOGE 33,609; the rest 12,000 to 19,000. ETH and SOL are the only ones with enough depth to be a candidate at 20 to 40 contracts, and even they are 5% and 2.6% of Bitcoin's volume. XRP is next and is **not** included, to keep this to the two the owner named.

**Data.** `python -m scalper.altseries fetch`: every settled KXETH15M and KXSOL15M market that closed in the last 66 days (Kalshi keeps candles about that far back) with its 1 minute bid/ask candles, into a **separate database, `data/alts.sqlite`**, so the Bitcoin and gold history and every earlier result are untouched.

**Rule (fixed now, one parameter set, identical to L1).** One observation per market, from the candle that ENDS exactly 360 s before the close; buy the favourite when its ask is 0.88 to 0.97 (either side), hold to settlement, taker at the ask, the same fee model as `lstrats.net`. Nothing is tuned, no filter, no other band or minute. A market with no candle at that minute, no quote in the band, or no result has no observation.

**Counterparty.** The same as L1's, and no new one is claimed: whoever holds the 3c to 12c longshot side near the close and sells it to the favourite buyer for less than it is worth. ETH and SOL are partly the same bet as Bitcoin (they move with it), so a pass would not be independent evidence of a different edge.

**Numeric prediction, before the run.** ETH lands near Bitcoin's thin figure, **+0.5c per contract net**, z between 0 and 1.5; SOL lower, **at or below 0.0c**, because its spread is wider and the favourite's ask costs more of the edge. **Expected verdict: both `FALSIFIED`.** If either shows a mean above +1.5c it is an audit trigger first (check the entry candle ends 360 s before the close and the settlement side).

**Pass bar, fixed (the same as every earlier test).** Each series is `NOT_YET_FALSIFIED` only if ALL hold: at least 300 observations; at least 5 days; day clustered z of net per contract at least 2.1; mean net above zero; both halves of the days positive; mean above zero with fees times 1.2. Anything else is `FALSIFIED`. A pass is permission for the next stage only, and never a reason to change the live bot.

**Information, not part of the verdict.** For each series: observations and per day, win rate against the mean price paid, mean net by half, and the **median traded volume of the entry minute's candle in contracts**, against the order sizes the bot would send (about 12 to 40), as a first look at depth. The book recorder's data (from about Oct 12 to 13) is the proper depth test and is not replaced by this.

**The stages after a pass, written now so they are not invented later.** (1) A forward shadow run on days not yet seen: the would-be entries are logged with no orders (needs a server change and a deploy, which the owner has asked not to do for another strategy yet, so none is built); (2) only after a shadow run that stays above the same bar, a small live stake with its own cash accounting and stop, scaled by the same review rules as BTC and gold but with an evidence gate for each step; (3) matching BTC and gold sizes only at the pace those gates allow. Nothing in stages 1 to 3 is built or started by this section.

**Count.** Two variants, one parameter set each: **2,589 as of 2026-10-09** (2,587 with T5). The control, as in the earlier searches, is not needed here because nothing is searched.

**Limits.** Candle asks are quotes, not our fills: the live bot fills about 56 to 59% of its signals (the misses are where the losses are), and the replay assumes the quote is available. Thin books fill less at size. The 66 day window is the same one L1 was measured on.

## Results: E1 and E2, one run, read once (2026-10-09; the rule, bar and prediction are those registered above; nothing was changed after seeing them)

`python -m scalper.altseries run`, 12,506 markets (6,253 each), 66 days, `data/alts.sqlite`. Signal counts first, as promised.

| Series | Observations | Days | Mean net per contract | Day clustered z | Halves | Fees x1.2 | Win rate vs mean price paid | Entry-minute volume (median) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| E1 ETH | 2,001 (29.9/day) | 67 | +0.57c | +1.21 | +0.95c / +0.15c | +0.48c | 93.8% vs 92.8% | 4,377 contracts | `FALSIFIED` |
| E2 SOL | 2,011 (30.0/day) | 67 | +0.54c | +1.24 | +0.57c / +0.52c | +0.45c | 93.8% vs 92.8% | 1,623 contracts | `FALSIFIED` |
| reference: Bitcoin | 1,955 | 67 | +0.43c | +0.75 | +0.35c / +0.51c | +0.33c | 93.5% vs 92.6% | not read | `FALSIFIED` |
| reference: gold | 1,424 | 63 | +1.47c | +2.80 | +1.99c / +0.91c | +1.38c | 94.7% vs 92.7% | not read | `NOT_YET_FALSIFIED` |

- **Both fail the bar on z (1.21 and 1.24 against 2.1), as Bitcoin does.** Everything else holds: both are positive, positive in both halves, positive with fees x1.2, with plenty of observations. The edge is the same thin one as Bitcoin's, about +0.5c a contract, with the same shape (a win rate about one point above the price paid).
- **Prediction against outcome.** ETH: predicted about +0.5c with z between 0 and 1.5; measured +0.57c, z +1.21. **SOL: predicted at or below 0.0c; measured +0.54c, so that prediction was wrong** (the wider spread did not eat the edge in this window). Predicted verdict for both, `FALSIFIED`, as measured.
- **Gold is what carries L1.** It is the only one of the four that clears the bar on its own.
- **Information, not part of the verdict: ETH and SOL are mostly the same bet as Bitcoin.** In windows where both had an entry, when Bitcoin's entry lost, ETH's lost **51%** of the time (base rate 6.4%) over 70 cases, and SOL's 43% (base 6.1%) over 51; ETH and SOL lost together 56% of the time one of them lost. Bitcoin and gold: 6% against a 6.1% base. Adding ETH and SOL would not diversify the account, it would triple the size of the loss on the days Bitcoin loses.
- **Depth, first look only:** the median 1 minute candle at the entry minute traded 4,377 contracts (ETH) and 1,623 (SOL), so a 12 to 40 contract order is 0.3% to 2.5% of it. The order book recorder's data is the real depth test.
- **Count.** Two variants: **2,589 as of 2026-10-09** (with T5's 2,587). Both `FALSIFIED`. The bot, the site and the Bitcoin and gold history are unchanged; the stages after a pass (a forward shadow run, then a small stake) do not start.

## Results: T5, one run, read once at all 1,240 markets (2026-10-10; the rule, bar and prediction are those registered above; nothing was changed after seeing them)

`python -m scalper.tapeflow run5` over `tape5` (seconds 300 to 599 of the same 1,240 markets T1 to T4 read). Signal count first, as promised: **444 observations** (796 markets with no observation), on 31 days. That is above the 300 minimum, so this is **not** an underpowered result.

| Test | Observations | Days | Mean net per contract | Day clustered z | Halves | Fees x1.2 | Exit above entry | Mean price paid | Median hold | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| T5 cheap side scalp, minutes 5 to 8 | 444 | 31 | **-1.52c** | **-5.16** | -1.70c / -1.35c | -1.74c | 51.4% | 9.2% | 88 s | `FALSIFIED` |

- **Prediction against outcome.** Predicted: about -1.0c per contract, win rate under 40%, 100 to 400 observations, `FALSIFIED`. Measured: **-1.52c** (worse), **51.4% up (the win-rate prediction was wrong)**, 444 observations (just above the range), `FALSIFIED`.
- **Same shape as T3.** It wins more than half the time (51% of trades sold above entry, a median hold under a minute and a half) and still loses 1.5c a trade, with both halves negative and z of -5. Many small wins and a minority of exits at the time limit far below entry, plus a fee and spread on both legs of a 9c contract (a 1c spread is 11% of the price).
- **What the owner's idea needed and did not get.** The window the examples came from (5.6 and 8 minutes in) now exists in the data, 444 times, and the cheap side scalped there loses. The two windows tried (T4 at seconds 61 to 179, too early for a cheap side to exist; T5 here, where it does) bracket the idea at tick level.
- **Audit triggers.** None: no result was better than predicted. The entry print is inside seconds 300 to 509 and the exit print after the entry second, by test.
- **Count.** One variant: **2,587 after T5**, and **2,589 with E1 and E2**. The bot and the site are unchanged.

## Rule for adding money to the account (written 2026-10-09, before any further result, at the owner's request; information only, no hypothesis, no variant counted)

Decided now, while the live record is 74 wins in 74 and nothing makes a deposit feel urgent, so a good week is not what decides it. This is a rule for the owner's own money, not advice, and the owner can override it; the point is that an override is then a visible choice.

**Why a rule.** The live record is about 2.5 days. The 67 day history of the same rule shows about a 94% win rate and +0.87c per contract, which is close to break even at the current size, and every earlier strategy here looked good early and faded as the window grew. L1 itself failed its own pre-set forward test (z 1.45 against 2.1). Extra capital scales dollars and risk by the same factor (the 10 week replay: about 1.8 times the dollars and about 1.7 times the bad drawdown for $1,000 against $550); it does not improve the edge.

**An add is allowed only when ALL of these hold.**
1. At least **200 settled live bot trades** have accumulated since the last add (or since Oct 7 for the first one).
2. **At least one real loss** has been seen at a size of 10 contracts or more, and the stop and the pool behaved as designed. A record with no loss has never tested the stop.
3. The win rate over those trades is **96% or better**, and net profit after fees is positive over the last 100.
4. At least **14 days** since the last add.
5. No loss stop has ended a session in the **last 7 days**.
6. The Oct 23 fill study has been read.

**Size of an add.** At most **25% of the current account** per add (at $550, no more than about $140), and only money whose loss would not change the owner's life.

**Stop adding, with no exceptions made in the moment, when any of these happen.** The win rate over the last 100 trades falls below 94%; a loss stop trips twice in 30 days; the account is down 15% from its high.

**Where extra capital stops helping.** With the ladder at $43 a contract and a base ceiling of 40, size stops growing near **$1,720**. Until the order-book recorder shows the touch can fill that many contracts at about 93c, do not add past about **$1,700**.

**Savings.** The savings half of new profit highs is never traded. Withdrawing it is a decision for the owner at any time; it does not change the bot's sizing, because sizing already excludes it.

**Records.** Each deposit is written down with its date and the account balance and bot profit on that day, so the results can be read separately from the deposits.

**Replacing a salary.** At the history's +0.87c per contract and 30 trades a day, $240 a day needs about 900 contracts per order and an account of about $43,000 at the 2% rule, far beyond the depth and ceiling here, and the edge would likely shrink as size grows. This strategy should be treated as a side income. If that view is ever to change, it should change on a forward read of many weeks, not on a week.

## Simulated ETH and SOL run, and the risk settings that must scale if it ever goes live (the owner's requirement, 2026-10-09)

**What was built.** `functions/kalshiSimLib.js` and the scheduled `kalshiSimTick`: L1 unchanged on KXETH15M and KXSOL15M, on live prices, with no order. It follows the live bot's path (same market list, same 6 minute window, same fresh read, same 88c to 97c pick, same stake) and replaces the order with a second read of the book half a second later, judged as an immediate-or-cancel buy at the touch (fills only if the price is still inside the limit, and only up to the size resting there). It is keyless by construction (no signing, no key, no `/portfolio`, no POST; the function is declared with no secrets) and writes only `kalshiSimOrders` and `kalshiSimControl`. Bitcoin and gold are simulated too, flagged `calibration`, only so the sim's fill can be compared with the real bot's on the same markets.

**The requirement.** If the simulation is ever promoted to real orders, the risk settings must scale with it, not be left sized for two markets. Written down now so it is a condition, not an afterthought:

1. **One stop for the account, not one per series.** The loss stop must count Bitcoin, gold, ETH and SOL together (the same `botRisk` rule: open orders counted as lost, the profit-funded part of a loss not counted).
2. **ETH and SOL are treated as part of the Bitcoin position.** In the 66 day history, when Bitcoin's entry lost, ETH's lost 51% of the time and SOL's 43% (base rate about 6%); gold's lost 6%. A window in which all three crypto series fire is closer to one bet three times the size than three bets. The per-position 2% base would otherwise become up to 6% of the account on one outcome.
3. **A combined cap on exposure per window, and on what one correlated loss can cost.** Set from the correlated loss, not the number of series.
4. **Position size per series ramps by evidence.** A small stake first, with its own gate for each step, until it matches Bitcoin and gold in dollars.
5. **Cash accounting per shard and the order ceiling are per series and total.** The second and third positions in a window are sized on the cash left after the first, as the live bot already does for two.

**What the simulation records so this can be checked before any real order.** Every simulated order keeps `maxCost`, `addon` and `addonCost`, the fields the loss stop reads, so the real stop rule can be run over Bitcoin and gold's live orders together with ETH and SOL's simulated ones, and the page can show what the combined stop would have done over the 24 to 72 hours.

**Stages, unchanged.** Nothing here moves the bot. A simulated result is read after 24 to 72 hours; real orders for ETH or SOL need the owner's go-ahead and a separate change.


## The exit watch was built (the owner's decision, 2026-10-10; information only, no variant counted)

After the exploratory read of the first 24 hours of 10 second books (Friday's loss slid for four minutes and an exit at 70c would have kept about three quarters of it), the owner asked for the stop loss to be implemented. It is built (`runExitWatch`, `kalshiLiveExit`, `kalshiExitMode`) behind a three way switch on the page that defaults to **log only**, so the first thing it produces is evidence: each time a position's bid falls to 70c it records what it would have sold. Turning it to **sell** is the owner's choice and is not a research verdict: the registered fresh-data test (X8) is still the way to find out whether a 70c exit pays for the winners it stops, and the 67 day test of exits (X1 to X7) found that it did not. The log-only records on real orders are a second, live source for that question.

## The exit is now fixed at 50c and always sells; the pool always rebuilds after every win (the owner's decision, 2026-10-12; information only, no variant counted)

The owner removed both switches from the page and the server. The exit watch now sells at **50c** with no log only or off mode, and the reinvest pool always rebuilds from half of every win. The stated aim is an anti-degen site: neither setting can be flipped in a bad hour. What this file already says about the line, so the choice is made with it in view: on the 31 entries of the exploratory read below, HOLD averaged -2.96c a contract, an exit at 70c +2.24c, at 60c +1.71c and **at 50c +0.65c**; on Friday's loss (22 contracts) a 50c exit sold at 0.40 for -$11.82, against -$5.17 at 70c and -$20.25 held. A 50c line stops fewer winners (on that day none touched 70c or lower) and keeps less of a slide. That read was three losses, so it is a lead and not a verdict, and a triggered exit at 50c still costs about 44c a contract on an entry near 93c.

**X8 is no longer the live record.** X8 is registered at 70c with "no other threshold is run", and the live bot does not exit at 70c any more. The page's "Exit at 50c" block (More stats) therefore answers a different question and is not the second source the X8 runbook describes. It counts only positions whose trigger bid was 50c or lower, and says how many earlier records, taken at the 70c line, it left out. The X8 test itself is unchanged and still runs on the recorder's snapshots.

## Exploratory read: the first 24 hours of 10 second books, and Friday's loss (information only, no hypothesis, no verdict, no variant counted; 2026-10-10)

The owner downloaded the order-book recorder's snapshots (`kalshi-books-202610091257.csv.gz`: Bitcoin and gold, one snapshot about every 10 seconds, 2026-10-09 12:58 UTC to 2026-10-10 12:56 UTC, 130 markets). **This is the first time L1's own entries could be watched second by second instead of minute by minute.** Everything in this section is read after the fact on 31 entries and 3 losses, so it is a lead and not evidence, and the file is excluded from the registered test below.

**L1's rule on that day (6 minutes left, a side priced 88c to 97c at the ask):** 31 entries (23 Bitcoin, 8 gold), 28 wins, 3 losses.

- **Friday's loss (Bitcoin, 21:38 CDT, YES bought at 91.5c, 364 s left) was not a gap.** The bid stayed at 0.91 to 0.92 for about 70 seconds, then slid: 0.85, 0.71 (235 s left), 0.70 (185 s), 0.54 (175 s), 0.40 (155 s), 0.15 (125 s), 0.03. At 22 contracts: held to settlement **-$20.25**; exiting at the first 10 second check at or below 80c would have sold at 0.71 for **-$4.95**; at 70c, 0.70, **-$5.17**; at 60c, 0.54, **-$8.75**; at 50c, 0.40, **-$11.82**.
- **The other two losses:** Bitcoin 12:24 CDT, NO bought at 0.90, bid 0.92 then 0.60 (221 s left), 0.41 (180 s), 0.06 (109 s): also a slide, an exit at 60c to 70c would sell at 0.60 (-30c against -92c). Gold 13:38 CDT, NO at 0.89: a **gap**, the bid went 0.83 to 0.36 in one 10 second step (173 s left), an exit at 70c still sells at 0.36 (-55c against -89c).
- **The winners:** the lowest bid any of the 28 winners touched after entry was 0.71; **none touched 0.70 or lower**, six touched 0.80 or lower (so an 80c exit would have stopped six winners).
- **Depth was not the problem.** At every one of these triggers the best bid held hundreds to thousands of contracts (the largest requirement here is 22), so the sell fills at the bid.
- **On these 31 entries** (poll every 10 s, sell at the bid seen, fee both legs): HOLD mean -2.96c a contract (worst trade -92c); exit at 70c +2.24c (worst -55c); at 60c +1.71c; at 50c +0.65c; at 80c -1.25c; at 30c -1.43c.

**What this changes, and what it does not.** It corrects a line written earlier in this file and repeated to the owner: that a stop cannot cap L1's losses because they gap (X1 to X7, 1 minute candles). On this day two of three losses slid for minutes and one gapped, and on the one that matters most an exit at 60c to 80c would have kept about three quarters of the loss. It does **not** overturn X1 to X7: over 67 days of minute candles, a 70c exit stopped 10.3% of entries and 53% of those would have won if held (X3), where here no winner touched 70c; 31 entries is one calm day for winners; and the threshold ranking above was read off these same 3 losses. Which of the two is right is what the registered test below is for.

## Pre-registration: X8, an exit at 70c on 10 second books (fixed 2026-10-10, before any fresh day of 10 second data has been read)

**The question.** Does selling a position as soon as its side's bid falls to 70c or lower, checked at the recorder's cadence (about 10 seconds), improve L1 net of what it costs by stopping winners that would have recovered?

**Data (fresh only).** The recorder's snapshots with a timestamp **at or after 2026-10-10 12:57 UTC**, i.e. every snapshot after the exploratory file above. Nothing before that moment enters the test, so the three losses that suggested the rule cannot also confirm it. The recorder keeps 10 days, so a first read is possible about 2026-10-20 and the owner can download more than one file; files are merged and de-duplicated on (timestamp, ticker).

**Rule (fixed now, one parameter set).** Entries are L1's: one per market, the snapshot nearest 365 s before the close inside the 330 s to 400 s window, the side whose ask is 0.88 to 0.97 (either side), taker at the ask. **Exit:** the first later snapshot, up to the close, at which the side's best bid is **0.70 or lower**; sold at that bid, fee on both legs (7% of p(1-p), unrounded). Otherwise held to settlement. The settled side is the one whose last bid before the close is 0.90 or more; a market whose last bid is between 0.10 and 0.90 is unresolved and left out of both arms. No other threshold is run.

**Counterparty / mechanism.** None new. The claim is statistical: a favourite that has lost 20c to 25c of its value with minutes left is, more often than not, one that will lose, and the book it sells into is deep enough to take the size.

**Numeric prediction, before the data.** Over the first read the exit stops **60% to 90% of the losses** before settlement and **3% to 10% of the winners**, and the mean per entry difference (exit minus hold) is between **-0.3c and +0.6c**, not distinguishable from zero. In plain terms: I expect it to cut the size of the bad days a lot and to cost about what it saves in the mean. **A result better than +1.0c is an audit trigger first** (check the exit is a LATER snapshot than the entry and sells at that snapshot's bid).

**Reading rule, fixed.** The test is on the per entry difference (exit minus hold, same entries), reported with the day clustered z. `NOT_YET_FALSIFIED` only if ALL hold: at least **300 entries** on at least **5 days**; the mean difference is above zero; day clustered z of the difference at least **2.1**; both halves of the days positive; and positive with fees times 1.2. Fewer than 300 entries is `NOT_ENOUGH_DATA` and says nothing about the idea; anything else is `FALSIFIED`. **Reported beside the verdict, because a pass on the mean is not the whole question:** losses stopped and winners stopped (counts), worst entry, worst day and deepest drawdown with and without the exit, and the largest 10 second gap loss. The owner may reasonably prefer a smaller worst day to a slightly lower mean; that is a choice about risk, made with these figures, and is not a verdict.

**Count.** One variant, **2,591** (2,590 after B4). No re-run with another threshold or cadence.

**Limits.** Snapshots every 10 seconds can step over a gap; the sell is assumed at the bid of the snapshot that first shows 0.70 or lower, not a later and worse one, and a live bot would be a second or two slower (no resting stop order exists on Kalshi; the bot would have to watch and sell by itself). A winner that dips and recovers between two snapshots is not seen. At roughly 30 entries a day a 10 day read is about 300 entries and about 18 losses: enough to pass `NOT_ENOUGH_DATA` and too few to be sure of a small mean difference. A pass would not change the bot; building a selling path on a live-money bot is a separate, careful step (a sell must never touch the owner's manual trades, must not double-sell, and needs its own gates).

**How to read it (a runbook, added 2026-10-10; it changes nothing registered above).**

1. On the Kalshi page, Tools, "Download book snapshots". The recorder keeps 10 days, so download again every few days and keep every file: the reader merges and de-duplicates them.
2. `cd kalshi-scalper/src && python -m scalper.exit10s FILE1 FILE2 ...` (`.csv` or `.csv.gz`). Snapshots before 2026-10-10 12:57 UTC are dropped by the code, not by the reader.
3. Read the verdict line once. `NOT_ENOUGH_DATA` is a normal first answer, not a failure: at about 30 entries a day the 300 entry minimum is about ten days of data, so a read around Oct 20 may land just short. Wait and read again with more days; do not change the threshold, the cadence or the bar to get a verdict sooner.
4. The owner has the exit set to Sell on the real account, so the page's "Exit at 70c" block (More stats) is the live record of the same question: positions that fell to 70c, what the sells got, and what holding paid. It is a second source with few events, not a replacement for this test.

## Pre-registration: B4, L1 one band lower, 84c to 88c (the owner's idea; fixed 2026-10-10, before any code for it and before any 84c to 88c result)

**The question.** A live Bitcoin market sat at "Below 86%" six minutes from its close and the bot, whose floor is 88c, correctly took nothing (the real price of the Below side was about 87c). The owner asked whether the same rule one band lower, 84c to 88c, is worth taking. This is the first test of anything below 88c on this rule; every earlier band test (B1 to B3, P1) was inside 88c to 97c.

**Rule (fixed now, one parameter set, identical to L1 except the band).** Bitcoin and gold only (the markets the bot trades), the 67 day history in `data/book.sqlite`. One observation per market from the candle that ENDS exactly 360 s before the close; buy the side whose ask is **0.84 up to but not including 0.88** (`band = (0.84, 0.8799)`, so an ask of exactly 0.88 stays with L1 and nothing is counted twice), either side, hold to settlement, taker at the ask, the same fee model as `lstrats.net`. Nothing is tuned: no filter, no other band edge, no other minute. A market with no candle at that minute, no quote in the band or no result has no observation.

**Counterparty.** The same as L1's and not a new one: whoever holds the longshot side near the close and sells it to the favourite buyer for less than it is worth. The mechanism weakens as the favourite gets cheaper, because the longshot being sold is then worth more (a 14c to 16c side, not 3c to 12c).

**Numeric prediction, before the run: it does not pass.** Mean net per contract between **-0.8c and +0.3c**, day clustered z under 1.0, win rate within 1 point of the mean price paid (about 86%). The reasons: the weakest band L1 already takes (88c to 90c) was negative after costs in the post hoc table, a pattern that continues downward is the default, and the fee is largest near 50c (about 0.07 x p x (1-p), about 0.8c a side at 86c against 0.3c at 95c). **Expected verdict: `FALSIFIED`.** A result above +1.0c is an audit trigger first (check the entry candle ends 360 s before the close and the band excludes 0.88).

**Pass bar, fixed (the same as every earlier test).** `NOT_YET_FALSIFIED` only if ALL hold: at least 300 observations on at least 5 days; day clustered z of net per contract at least **2.1**; mean net above zero; both halves of the days positive; above zero with fees times 1.2. Anything else is `FALSIFIED`. A pass is permission for a forward test on days not yet seen, never a reason to change the live bot (which has a fixed 88c floor).

**Information, not part of the verdict.** Observations and per day; by series (Bitcoin and gold separately); the two sub-bands 84c to 86c and 86c to 88c (read-only, so the edge is not chosen); win rate against mean price paid; and, for scale, the same read on L1's own band over the same days.

**Count.** One variant: **2,590 as of 2026-10-10** (2,589 before). No re-run with another band edge.

**Limits.** Candle asks are quotes, not our fills (the live bot fills about 56% of its signals, and the misses are where the losses are). The same 67 days as every earlier test. A pass would not change the bot: it would need its own band logic and sizing, and the size ladder, stop and pool were all built around 88c to 97c entries.

## Results: B4, one run, read once (2026-10-10; the rule, bar and prediction are those registered above; nothing was changed after seeing them)

`python -m scalper.band84`, Bitcoin and gold, 67 days. Signal count first: **953 observations** (14.2 a day), well above the 300 minimum, so this is not underpowered.

| Test | Observations | Days | Mean net per contract | Day clustered z | Halves | Fees x1.2 | Win rate vs mean price paid | Verdict |
|---|---|---|---|---|---|---|---|---|
| B4 84c to 88c, both series | 953 | 67 | **-0.05c** | **-0.05** | -0.40c / +0.32c | -0.22c | 86.4% vs 85.5% | `FALSIFIED` |

- **Prediction against outcome.** Predicted: mean between -0.8c and +0.3c, z under 1.0, win rate within 1 point of the price paid, `FALSIFIED`. Measured: -0.05c, z -0.05, 0.9 points, `FALSIFIED`. All of it inside the registered ranges.
- **The band is break-even before costs of being wrong about fills.** The mean is zero, one half is negative and one positive, and it is negative with fees x1.2. There is nothing to take.
- **Information only (not part of the verdict, and the edges were not chosen from it).** Bitcoin: -0.90c (z -0.70, 581 entries). Gold: +1.29c (z +0.76, 372 entries, halves -0.72c / +3.50c). Sub-band 84c to 86c: -1.09c; 86c to 88c: +0.99c (z +0.76, halves -0.69c / +2.87c). The 86c to 88c figure is exactly the kind of cell that is tempting to cut out after the fact and would be a new, separately counted try; it is not significant and one of its halves is negative.
- **For scale: L1's own band on the same days.** 3,379 entries, +0.87c, z +2.42, positive in both halves and with fees x1.2 (`NOT_YET_FALSIFIED` on these days, which are the same days it was found on).
- **What it means for the live bot.** Nothing changes. The 88c floor stays. The Bitcoin market at 86% that prompted the question was correctly skipped, and the history says skipping the 84c to 88c band costs nothing.
- **Count.** One variant: **2,590 as of 2026-10-10**, counting T5, E1 and E2 (PR 367) ahead of it. `FALSIFIED`.

## Pool rebuilds after every win (the owner's request, 2026-10-10; information only, no hypothesis, no verdict, no variant counted)

The owner asked for the reinvest pool to restart building on each loss instead of waiting for new profit highs. `PYTHONPATH=src python -m scalper.sizing pool`, from $750 with the deployed sizing (2% base, $43 ladder, ceiling 40), 60% fills, 5% stop, 3000 paths over the real 67 days:

| Rule | Days | Mean gain | 5th pct | 1st pct | Deepest drawdown (95th) | End savings | Stop days |
|---|---|---|---|---|---|---|---|
| Original: pool from half of each new high | 30 | +$121 | -$82 | -$133 | $187 | $90 | 1.38 |
| Literal restart of the high-water mark on every loss | 30 | +$131 | -$127 | -$177 | $222 | **$581** | 0.31 |
| Pool refills from half of every win | 30 | +$181 | -$154 | -$225 | $287 | $147 | 0.84 |
| Original | 90 | +$403 | -$12 | -$113 | $269 | $238 | 3.42 |
| Literal restart on every loss | 90 | **+$188** | -$98 | -$167 | $226 | **$873** | 0.31 |
| Pool refills from every win | 90 | +$591 | -$132 | -$284 | $438 | $368 | 1.86 |

- **The literal version is a trap.** Restarting the high-water mark on every loss makes half of every win a saving, and savings never absorb a loss and are not counted in the sizing balance. The savings figure explodes ($873 on a $750 account over 90 days) while the account is flat, size stops growing, and the 90 day gain falls to less than half of the original. This is the flaw the file already recorded when skimming each win was first tried.
- **What the owner asked for, kept: the pool refills right after a loss.** Rebuilt as "half of every win goes to the pool, a loss comes out of the pool, savings only take half of a NEW high" (`pool_every_win`), it keeps the profit and raises it: about +47% at both horizons.
- **The price is risk, about in proportion.** The bad percentiles roughly double (90 day 1st percentile -$284 against -$113), the deepest drawdown is about 60% larger ($438 against $269), and the mean per dollar of drawdown is slightly lower (1.35 against 1.50). It is the same trade as a larger size, because the pool's extra contracts are back in play sooner after each loss. Stop days fall because the pool is full of contracts again but each stop trips later in the run, not because the risk is lower.
- **Built as a switch** (`session.poolRule`, `foldSkim`'s `everyWin`), default the original rule, so the owner decides when it starts. It applies only to orders settled after it is switched. A replay of the past, not a forecast; the live record (82 of 83) is far better than the history it replays.
## Ethereum live: built behind a size switch, and the ramp it must follow (the owner's decision, 2026-10-10; information only, no variant counted)

**What was built.** L1, unchanged, can trade the Ethereum 15 minute markets with real money when the owner sets a size for them (`session.liveExtra.KXETH15M`, 0 or absent is off, the default). The page's "Ethereum live, largest order" select offers named presets (off, 1, 2, 3, 5, 10 contracts, "same as Bitcoin and gold"); the server maps the name to a number, caps it at the Bitcoin and gold stake on every order (`min(stake, preset)`), turns it on only with the server's own live switch, and refuses any series that is not on a hard list in the code (`EXTRA_LIVE_SERIES`, Ethereum only; Solana is deliberately not on it). An Ethereum order is an ordinary L1 order (same rule, band, window, ids, loss stop, pool and exit), so one stop and one pool cover the whole account. Its market must have the money on its own shard; the tick skips it with the reason otherwise.

**What the evidence is, said plainly.** The history test (E1) found Ethereum thin and short of the bar (z +1.21 against 2.1, +0.57c a contract, positive in both halves), and its losses coincided with Bitcoin's 51% of the time against a 6% base rate. The simulation (`kalshiSimTick`) is the forward look; its results are the owner's to read on the card and are not part of this section. Going live is the owner's decision and not a research verdict.

**The ramp (decided now, before any live Ethereum trade).** One step up the presets at a time, by the owner, never automatic:
1. Start at **1 contract**. Stay until there are at least **40 filled Ethereum orders at that size** or 7 days, whichever is later.
2. To step up: no loss stop in the last 7 days; Ethereum's fill rate within 15 points of Bitcoin's over the same orders (so the fill model and the depth hold); Ethereum's realised result over those orders not worse than -1% of the account; the simulation still agrees with the live fills (the card's fidelity line).
3. Do not select **"same as Bitcoin and gold"** until the loss stop has been re-scaled for correlated exposure. At today's size three positions open at once (Bitcoin, gold, Ethereum) put about $33 of base-funded risk against a stop of about $37 at a $750 balance, and an open order counts as lost, so there is almost no headroom, and the three crypto-and-gold windows coincide often. A combined cap per window is the missing piece and is not built.
4. A loss stop that ends the session, or Ethereum losing together with Bitcoin twice in a week, sends the preset back to a lower step; so does any change to the rule.

**Not built, on purpose:** Solana; a size that follows the account automatically; a combined cap per window.

## Pre-registration: OW1, the opening window, two lanes (the owner's request; fixed 2026-10-12 before any paper record existed and before any rule was run on a market that closes after 16:00 UTC)

**Why this exists.** On 2026-10-12 the owner asked for a strategy for "the first 5 to 10 minute window" of each market, to sit beside L1 under the same risk limits with its own profit and loss, and said they love "catching the 30% flips or lower". Both instincts are turned into rules below and tested on paper. **This is not a search for an edge and it is not a new mechanism.** Lane F rewords H1, B4 and ledger row O26 (a favourite bought earlier than L1 and held); lane U rewords C1 to C3, T4 and T5 (the cheap side bought early). In ledger terms both are `OVERLAP`, and they are counted anyway so the tally stays honest. What OW1 adds is a forward test on days after the rules were fixed, and a paper scoreboard the owner can watch instead of trading the instinct.

**Disclosure: what was looked at before this was written.** An exploratory read (`python -m scalper.ladder`, information only, no hypothesis, no verdict, no variant counted) priced every side-price bucket at 10, 8 and 6 minutes left over 4,560 settled markets (Bitcoin 2,656, gold 1,904, 29 days to 2026-10-12). The lane bands were drafted from the owner's words ("30% or lower"; a favourite earlier than L1's 6 minutes) and from L1's own 88c floor, but **that read was already in view when F's floor was set**, so F is not a blind choice. F was first 78c to 87c and overlapped U (a 78c favourite has an other side near 22c, so both lanes bought both legs of one market, a guaranteed small loss); it became 82c to 87c with a one-leg rule, on that design ground. U's 20c floor keeps it a flip and not a lottery; the read shows every 5c bucket from 5c to 30c negative, so no other floor would have changed the sign. The read's result is therefore known and cannot be the test: lane F, 549 entries, **-0.05c** a contract, z -0.03, win 85.4% at a mean price of 84.6c; lane U, 1,170 entries, **-3.90c**, z -4.11, win 22.5% at 25.1c, both halves negative. **Only markets that close after 2026-10-12 16:00 UTC are judged.**

**The rules (fixed now, one parameter set per lane).**
- **Decision:** the market's fresh book 570 s to 640 s before the close (the recorder), which the research readout takes as the minute candle that ends 600 s before the close. The recorder covers Bitcoin, gold and Ethereum; the readout covers Bitcoin and gold (Ethereum history is kept out of `book.sqlite`).
- **Lane F, the early favourite:** the side whose ask is 0.82 to 0.87, bought at the ask, held to settlement.
- **Lane U, the early underdog (the flip):** the side whose ask is 0.20 to 0.30, bought at the ask, held to settlement.
- **One leg per market:** if a book fits both lanes, F takes it and U is not recorded.
- **No exit.** L1's 50c exit was chosen for 88c to 97c entries; at 20c to 30c it would sell a flip at the first dip and the lane would measure the exit, not the flip.
- **Costs and size:** taker fee 7% of p(1-p) unrounded on the entry, nothing on settlement. Size is what L1 would send today (`l1Count`; one contract when sizing is off), at most $2.00 a contract. The recorder simulates the fill from a second read of the book 500 ms later; a price past the limit, no size at the touch or a crossed book is a "no fill", never a guess.
- **Paper only. Nothing in the recorder can place an order:** no signing, no key, no portfolio call, no POST, no secrets on its scheduled function (`kalshiOpeningTick`), and a test pins each. The live limits that tie orders together (the 24 hour order count, the per window cap shared with L1) are worked out and recorded on every paper record but not enforced, so the research sample is not cut by the clock.

**Counterparty.**
- **F:** whoever sells a favourite at 82c to 87c with 10 minutes left. The favourite-longshot bias says favourites are slightly underpriced and longshots overpriced. Same story as H1; it is not new.
- **U:** nobody, on the evidence. The claim OW1 tests for U is that flip buyers have an edge, and the prior is that they pay one: C1 (8c to 15c early, held) -3.28c z -8.6; C2 and C3 about -2.3c; T5 (4c to 10c, minutes 5 to 8) -1.52c z -5.16 on 444 observations. L1's own edge is the other side of this trade, since it buys the favourite that flip buyers sell against. U exists as a measured scoreboard of the instinct, not as a candidate.

**Numeric predictions, before the first record.**
- **U:** net **-4c a contract** (between -6c and -2c; the standard error at about 850 entries is about 1.1c), win rate 20% to 24% against a mean price of 25%, average win about +73c and average loss about -26c. Verdict at the first read: `FALSIFIED`.
- **F:** net **0c a contract** (between -3c and +3c; the standard error at about 400 entries is about 1.5c, so the sample cannot separate it from zero), win rate 83% to 87%, average win about +15c and average loss about -85c, z between -2 and +2. Verdict at the first read: `FALSIFIED`, or `NOT_ENOUGH_DATA` if fewer than 300 entries have arrived.
- **A better result than predicted is an audit trigger first:** check the entry candle is the one that ends 600 s before the close, the settled side is read only to settle, and no market is counted twice.

**Kill criteria** (the common bar, per lane, any one gives `FALSIFIED`): fewer than 300 entries or fewer than 5 separate days (these two give `NOT_ENOUGH_DATA`, which says nothing about the idea); day clustered z below 2.1; mean at or below zero; at or below zero with fees x1.2; either half of the days negative.

**Reading rule.** `python -m scalper.backfill` then `python -m scalper.opening`, forward markets only. **One read:** the first on 2026-11-03 00:00 UTC, with the data clipped at that date so the answer cannot change afterwards (21 full days: lane U expects about 850 entries, lane F about 400 on Bitcoin and gold). A lane that is `NOT_ENOUGH_DATA` then gets one more, final, read on 2026-11-16 and nothing after it. Before 2026-11-03 the code prints numbers and **no verdict**, because the page already shows a running paper tally and nobody should read a verdict into it. The page's tally uses the recorder's simulated fills (it can miss a fill the candle readout counts), so the two will differ a little; the readout is the number that counts, and a gap of more than 1c a contract between them is checked in the recorder first. `tests/test_opening.py` pins the lanes against the recorder's source so the two cannot drift apart.

**What happens after.** A `FALSIFIED` lane stays on the page as a paper scoreboard until the owner removes it. `NOT_YET_FALSIFIED` means keep testing forward and nothing more. **There is no path to real money in this section.** A live OW1 would be a separate change under its own written waiver, reviewed like L1's. It must carry every gate `runL1Tick` has (the halt switch, an unresolved order, the loss stop shared with L1, one limit per window shared with L1, the 24 hour order cap, $2.00 a contract, the size ladder) and its own code gate that is **not** `CODE_KILL_SWITCH`, so restarting L1 can never start it.

**Count.** Two variants, one parameter set each: **2,593 once run** (2,591 as of 2026-10-10). Registered, not yet run.

**Limits.** The candle readout prices every entry at the ask of a minute candle and always fills; the recorder shows what fills. "10 minutes left" is a clock, not a state of the spot. Half of lane F's entries (274 of 549) sit in markets where L1 enters later, so a live F would stack on L1's exposure in the same window. Bitcoin and gold move together, and 29 days is one regime.

## Pre-registration: OW2, the opening scalp that is flat before L1 buys (the owner's request; fixed 2026-10-12 before any OW2 rule was run on any market)

**Why this exists.** The owner wants an opening-window trade that is opened, managed and closed within a few minutes and never holds a position while L1 does. L1 buys 5.5 to 6.7 minutes before a close (minute 8.3 to 9.5 of the quarter hour) and holds to settlement. OW1 holds to settlement and therefore overlaps it, which is why this is a separate rule and OW1 is left exactly as registered.

**Disclosure: what was looked at before this was written.** The cost arithmetic only. Kalshi's fee is `0.07 p (1 - p)` per contract on each leg: about 1.3c each way at 25c, 1.75c at 50c, so a round trip costs about 10% of a 25c stake and 7% of a 50c stake before the spread. A 10% target at 25c therefore nets about zero. The earlier opening scalps OP1 to OP3 (favourites at 70c to 90c, targets of 3c and 5c) were all `FALSIFIED` on 11,220 markets. No OW2 number had been computed when this section was committed. The 30 day history it runs on was backfilled after this commit.

**The rules (fixed now).**
- **Entry:** the market's first two minutes only: the minute candle that ends 840 s before the close, else the one that ends 780 s before. The side whose ask is inside the variant's band is bought at the ask. One leg per market, YES tried before NO, taker.
- **Exit:** a later minute candle whose closing BID is at least entry ask times (1 + target); a candle's high or low is never used. If none, the position is sold at the closing bid of the candle that ends 480 s before the close. **Nothing is ever held past that candle**, which is 80 s before L1's earliest buy. A market with no valid candle at 480 s is not counted and is reported as unresolvable (never settled as if held).
- **No stop** other than that time exit: a stop is a second parameter and nothing here is tuned.
- **Costs:** taker fee `0.07 p (1 - p)` unrounded on both legs.

**The four variants (the whole family, no others will be run).**

| Variant | Band (ask) | Target |
|---|---|---|
| OW2-A | 0.20 to 0.40 | +10% |
| OW2-B | 0.20 to 0.40 | +15% |
| OW2-C | 0.40 to 0.80 | +10% |
| OW2-D | 0.40 to 0.80 | +15% |

**Counterparty.** The taker who paid an early opening move at the open, before the market had settled on a price. The claim is that early prices overshoot and the 10% to 15% retrace is paid back inside five minutes. The prior is against it: spike-fade scalps (S27 to S37) and the opening favourite scalps (OP1 to OP3) were falsified, and the cost per round trip is the same size as the target.

**Numeric predictions, before the first run.** Net per contract **-2c to -5c** for A and B (fees and spread are about the size of the gross move), **-1c to -3c** for C and D, a target hit rate of 25% to 45% for the 10% targets and 15% to 35% for the 15% targets, and **no variant passes**. A passing variant is an audit trigger first: check the entry candle ends 840 s or 780 s before the close, the exit never reads a candle that ends before the entry, and no exit is after the 480 s candle.

**Kill criteria** (the common bar, per variant, any one gives `FALSIFIED`): fewer than 300 entries or fewer than 5 days is `NOT_ENOUGH_DATA` (says nothing about the idea); a day-clustered z below 2.5; a mean not above zero in BOTH halves of the history split at the midpoint; a mean not above zero with fees 20% higher. Verdict words: `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. There is no `promote`.

**Reading rule.** `python -m scalper.backfill 30` then `python -m scalper.ow2`. **One read on the 30 day history.** If a variant is `NOT_YET_FALSIFIED` it earns a forward paper test in its own recorder and its own collections (never `kalshiOpeningOrders`, never L1's), read once on a date written down then. It earns nothing else: there is no path to real money from this section.

**Isolation from L1, written now.** Any recorder for this idea has its own scheduled function, its own collections, no Kalshi key, no signing, no portfolio call and no POST, and shares no document with L1. It cannot hold a position during L1's buy window by construction, because the rule above closes it first.

**Count.** Four variants: **2,597 once run** (2,593 after OW1). Registered, not yet run.

**Limits.** Minute candles hide what happens inside a minute, so an intrabar touch of the target is never credited (conservative), and a fill at the candle's closing ask or bid is assumed (optimistic where the book is thin). A taker round trip crosses the spread twice; the closing quotes already include that.

**2026-10-12: OW2 ran once (`python -m scalper.ow2`, commit afbb3e0, 4,831 markets, 31 days): all four variants `FALSIFIED`.**

| Variant | n | Net a contract | z | 1st half | 2nd half | Fees x1.2 | Target hit | Gross before fees |
|---|---|---|---|---|---|---|---|---|
| OW2-A (20c to 40c, +10%) | 3,086 | -4.49c | -13.95 | -4.53c | -4.45c | -5.06c | 57.9% | -1.62c |
| OW2-B (20c to 40c, +15%) | 3,086 | -4.46c | -13.32 | -4.37c | -4.55c | -5.03c | 54.1% | -1.60c |
| OW2-C (40c to 80c, +10%) | 4,763 | -4.00c | -12.43 | -4.46c | -3.55c | -4.61c | 64.1% | -0.98c |
| OW2-D (40c to 80c, +15%) | 4,763 | -3.84c | -11.65 | -4.32c | -3.35c | -4.43c | 57.4% | -0.85c |

- **Against the prediction.** A and B landed inside the predicted -2c to -5c. C and D were predicted at -1c to -3c and came in worse, at -4.0c and -3.8c. No variant came near the bar.
- **What it establishes.** The target is hit more than half the time, and the trade still loses, because the target is about the size of what the trade costs. Fees take about 2.9c to 3.0c a round trip and the spread (entry at the ask, exit at the bid) about 1c to 1.6c, so the gross figure is already negative before any fee. There is no early-move edge to rescue with a better exit. This is the same result as OP1 to OP3 and S27 to S37: cost, not signal, is the binding constraint.
- **Nothing is built from it.** No recorder, no collection, no page row. A `FALSIFIED` rule earns nothing.
- **Count.** Four variants: **2,597** tried in total (2,593 after OW1).
## Pre-registration: OW3, OW4, OW7, three hold-to-settlement contrasts (the owner asked for new strategies; fixed 2026-10-12 before any of them was run)

**Where they came from.** A research pass listed everything already tried (about 2,597 variants, every one `FALSIFIED` or `NOT_ENOUGH_DATA`) and proposed eight candidates, OW3 to OW10. None gives a different kind of exposure or is flat before L1 buys: a round trip costs about 1.3c of fees plus at least 1c of spread at 90c and about 3.5c plus spread at 50c, and every scalp family is already falsified on that arithmetic. So all of these hold to settlement and pay one fee. **Three of the eight are run.** OW5 (frozen gold feed) has about 49 windows in 31 days, so it can only ever return `NOT_ENOUGH_DATA`. OW6 (round-number asks), OW8 (hourly-bar close) and OW9 (turnover z-score) are weak rewordings of tried ideas or of OW4, and each one run raises the bar for everything after it. OW10 (the 08:00 UTC Deribit expiry) has 15 entries a month. None of those five is run. **A subset of L1 can only remove entries from L1; it cannot create a new strategy.** OW4 and OW7 are therefore tests of whether L1 could be filtered, not new trades.

**Disclosure: what was looked at before this was written.** Entry counts, strike steps and the median mid of frozen gold windows. No profit or loss of any of these rules was computed. The NO-lean idea (OW3) comes from public Kalshi analyses that the research pass recalled from memory and did not verify.

**Common definitions (fixed now).** Entries are one per market and time, from the minute candle that ENDS exactly the stated time before the close, bought at the ask and held to settlement, taker fee `0.07 p (1 - p)` on the entry only (`lstrats.hold_rule`). Each hypothesis compares an arm A (the one that would be traded) against an arm B. The statistic is the difference of mean net a contract (A minus B) with a day-clustered standard error, z = difference / standard error. **Family bar, because three are run: z at least 2.5**, the difference positive in BOTH halves of the history (split at the midpoint), arm A's own mean net above zero with fees 20% higher, and at least 300 entries in each arm on at least 5 days. Anything short is `FALSIFIED`; too few entries is `NOT_ENOUGH_DATA`. Verdict words: `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. There is no `promote`.

**OW3, the NO-side lean.** Favourite side ask 0.82 to 0.97 at 600, 480 and 360 s left, pooled. Arm A is NO favourites, arm B is YES favourites. To keep price from deciding it, each entry's net is replaced by its net minus the mean net of all entries at the same time and the same 2c price bucket, and the contrast is taken on those residuals. *Counterparty:* retail takers who lean YES. *Prediction:* NO minus YES = **+1.0c**, standard error about 1.3c, so underpowered. *Extra kill:* arm A's mean net at or below 0.

**OW4, US waking hours.** L1's band (0.88 to 0.97) at 360 s left, on weekdays only. Arm A: markets closing 13:30 to 20:00 UTC. Arm B: other weekday hours. Contrast per weekday, then the day-clustered z. *Counterparty:* lottery buyers when retail is active. *Prediction:* **+2.0c** against **+0.7c**, difference standard error about 1.6c.

**OW7, the opening open-interest ratio.** L1's band at 360 s left. Feature = (open interest at the candle ending 360 s left minus open interest at the candle ending 600 s left) divided by the larger of 1 and the summed volume of the candles ending 540, 480, 420 and 360 s left. A candle with no open interest or volume makes the market unusable for this test and it is counted and reported. Arm B is the lowest tercile of the feature over all usable entries, arm A is the other two. *Counterparty:* new money paying us; informed exiters are the adverse side. *Prediction:* the L1 mean rises from about +1.0c to **+1.5c** when the lowest tercile is skipped. The units of `oi` and `volume` are checked and printed before the contrast is read.

**Count.** Three hypotheses: **2,600** tried once run (2,597 after OW2). **Isolation from L1:** these are offline readings of history and place nothing. **What a pass would mean:** `NOT_YET_FALSIFIED` earns one forward read on data written down then, and no change to L1, whose entry rule is not touched by anything here.

**2026-10-12: OW3, OW4 and OW7 each ran once (`python -m scalper.ow3`, commit a960233, 4,831 markets, 31 days): all three `FALSIFIED`.**

| | n A | n B | days | Mean A | Mean B | A minus B | z | 1st half | 2nd half | A with fees x1.2 |
|---|---|---|---|---|---|---|---|---|---|---|
| OW3 NO minus YES (price-matched residuals) | 2,371 | 2,485 | 31 | -0.43c | +0.41c | **-0.83c** | -0.90 | -2.29c | +0.55c | -0.26c |
| OW4 US hours minus other weekday hours | 324 | 834 | 21 | -0.57c | +0.84c | **-1.41c** | -0.92 | -1.28c | -1.50c | -0.66c |
| OW7 kept two terciles minus lowest tercile | 967 | 485 | 31 | +0.96c | -0.47c | **+1.43c** | +1.15 | +1.98c | +1.07c | +0.88c |

- **Against the predictions.** OW3 and OW4 came out on the wrong side of zero (predicted +1.0c and +2.0c); neither is distinguishable from zero. OW7 had the predicted sign, +1.43c against a predicted +0.5c rise, positive in both halves and positive with fees 20% higher, but z was 1.15 against a bar of 2.5, so it fails on power, not on sign.
- **OW7 units check.** All 4,831 markets had a usable feature (min -0.343, median 0.229, max 0.879), so nothing was dropped.
- **What it establishes.** Nothing here beats the common bar and nothing can be built from it. OW7 is the one to note: skipping the lowest open-interest-ratio tercile of L1's entries is worth about +1.4c with a standard error of 1.25c, which is a hint, not a result. It is a filter on L1, so it could only remove L1 entries, and a hint with a z of 1.15 is the kind that moves on the next sample. It is NOT carried forward automatically and L1 is not changed.
- **Count.** Three variants: **2,600** tried in total (2,597 after OW2).

## Registered: the OW7 forward read, and an exploratory look at what it was (2026-10-12, after the first read, before any new data)

**Exploratory, information only, no verdict, no variant counted** (`ow3.py` features on the same 31 days, 1,452 L1-band entries at 6 minutes left; it is not a candidate and must not be used to choose a rule). What it showed, so nobody builds on it by accident:
- **It is not monotone.** Net by feature quintile, low to high: -0.08c, -0.42c, **+2.15c**, +1.38c, -0.60c. A rising line would suggest a mechanism. A hump is what noise and a subgroup look like.
- **It is concentrated.** The lowest tercile's weakness sits mostly in Bitcoin NO-side entries (-2.82c on 194). Gold's lowest tercile is +2.03c. The loss rate is 8.0% (39 of 485) in the lowest tercile against about 5.5% (53 of 967) in the other two: about 14 extra losses.
- **The feature barely varies in sign.** Open interest rose in 1,441 of 1,452 entries, so the feature is essentially the share of volume that opened new positions.
- **Read:** the +1.4c with z 1.15 is about 14 losses. It may be real and it may not; the first sample cannot say, so a new sample must.

**The one forward read of OW7 (fixed now).** Markets closing on or after **2026-10-13 00:00 UTC**, which the first read never saw. **One read, on 2026-11-16, not earlier**, after `python -m scalper.backfill 30` then `python -m scalper.ow3 --forward 2026-10-13`. The boundary between arm A and arm B is **fixed at 0.2395** (the value from the first 31 days, never refit on the new data). The bar is the same: z at least 2.5, positive in both halves, arm A positive with fees 20% higher, at least 300 entries in each arm on at least 5 days. Fewer than 300 gives `NOT_ENOUGH_DATA`. **A pass would mean one thing:** keep reading forward; L1's entry rule is not changed on any read of this sample. **Count:** a forward read of an already counted variant adds none (2,600).

## Pre-registration: SS1, a train and validation search for an opening scalp that is flat before L1 buys (the owner's request; fixed 2026-10-12 before it was run)

**What was asked.** "Find a paper scalp that is close to profitable and refine entries and exits until it has a high profit factor." Refining until the number is high is selection, and selection on the data it is judged on always produces a good-looking number: best-of-N crosses profit factor 1.5 somewhere between N=20 and N=200 on pure noise (`lib/deflate.py` in shwoop-server's research notes). So the refining is allowed and is fenced: it happens on one part of the history, one rule is frozen, and only the part it never saw can say whether it worked.

**Disclosure: what was looked at before this was written.** OW2 (four variants, all `FALSIFIED`, gross negative before fees: -0.85c to -1.62c before the entry fee, which is the spread alone) and the earlier scalp families (60 second scalps, OP1 to OP3, S27 to S37, H4). No SS1 cell had been computed. **My prediction, before the run: nothing is close.** The best cell on the training days will still be negative after fees and the single frozen winner will lose on the validation days. A scalp pays about 3c of fees plus 1c to 1.6c of spread to move a few cents, and the earlier searches (2,591 variants) found nothing. I expect `FALSIFIED`.

**The grid (fixed now, nothing added after seeing a result).** Every cell is one try.
- **Entry minute:** one per cell: the minute candle that ends 840, 780, 720 or 660 s before the close (the first four minutes). Never another minute, never two entries.
- **Band (ask of the side bought):** 0.20 to 0.40, 0.40 to 0.60 or 0.60 to 0.80. YES is tried before NO.
- **Entry condition:** none; momentum (that side's ask is at least 3c above its previous candle's ask); dip (at least 3c below).
- **Target:** closing bid at least the entry ask plus 3c, 5c or 8c.
- **Stop:** none, or a closing bid at least 4c below the entry ask (sold at that candle's bid).
- **Cut-off:** nothing is ever held past the candle that ends 480 s before the close (80 s before L1's earliest buy); it is sold at that candle's bid. A market with no valid candle at 480 s is not counted and is reported.
- **Costs:** taker fee `0.07 p (1 - p)` unrounded on both legs; closing ask in, closing bid out; a candle's high or low is never used.
- **Cells:** 4 x 3 x 3 x 3 x 2 = **216**.

**The split (fixed now).** Train: the first 21 days of the 31 day history (markets closing before the cut). Validation: the remaining markets. The cut is the date 21 days after the first market closes, written into the code as a function of the data's first date, not tuned.

**Selection (fixed now, the only free choice).** On the training days only: among cells with at least 300 training entries on at least 5 days, take the one with the highest mean net a contract after fees. Profit factor is printed for every cell but it is not the selector, because it rewards a few lucky wins. **That one cell is frozen and read once on the validation days.** No second cell, no tuning after seeing validation.

**Kill criteria for the frozen cell (validation days only), any one gives `FALSIFIED`:** fewer than 300 validation entries or fewer than 5 days (`NOT_ENOUGH_DATA`); a day-clustered z below 2.5; a mean not above zero; a mean not above zero with fees 20% higher. Verdict words: `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. There is no `promote`.

**What a pass would earn.** `NOT_YET_FALSIFIED` earns a forward paper read on days written down then, in its own recorder and collections, and nothing else. A pass on a search of 216 cells is a hint and not a result: the forward days are what count.

**Count.** 216 variants: **2,816** tried once run (2,600 after OW3 to OW7). Registered, not yet run.

**2026-10-12: SS1 ran once (`python -m scalper.ss1`, commit 23749f4, 4,831 markets): `FALSIFIED`. No scalp is close to profitable.**
- **Training days (3,450 markets, before 2026-10-03): 0 of 180 cells with entries had a positive mean after fees.** The best cell with at least 300 entries was **-2.91c a contract, profit factor 0.63** (entry 660 s, band 0.60 to 0.80, target +8c, no stop). Four cells with a better mean (-1.12c at best) were dip entries with only 175 trades, below the 300 bar, so they were not eligible; they are not a hidden winner, they are small samples.
- **Frozen cell on the validation days (1,381 markets, 10 days, read once):** n=759, **-3.77c**, z -5.27, profit factor 0.56, target hit 48.1%, -4.32c with fees 20% higher. `FALSIFIED`, and worse than on the training days, which is what a selected cell does.
- **Against the prediction.** Predicted: nothing close, best training cell negative, frozen winner loses on validation. All three held.
- **What it establishes.** Across 216 combinations of entry minute, price band, momentum or dip condition, target and stop, with a flat-before-minute-8 cut-off, none is profitable even on the data it was chosen on. Refining entries and exits until the profit factor rises would find the cell that was luckiest on those days, not one that works. The fee plus spread of a round trip is bigger than any 3c to 8c target at these prices. The higher the price band, the less it loses (0.60 to 0.80 beats 0.20 to 0.40), which points at fees shrinking toward the extremes, not at a signal.
- **Nothing is built from it.** No recorder, no collection, no page row.
- **Count.** 216 variants: **2,816** tried in total (2,600 after OW3 to OW7).

## Pre-registration: SS2, a 1,760 cell search on 40 days with Ethereum, train and validation, with a fair-market placebo (the owner's request; fixed 2026-10-12 before it was run)

**Why now.** The history was extended from 31 to 40 days (2026-09-02 to 2026-10-12) and Ethereum was added (3,792 markets), so there is new data the earlier tests never saw for 9 days of Bitcoin and gold and for all of Ethereum. The owner asked for at least 1,000 more Kalshi variants. 2,816 variants have been tried on overlapping data, so the bar below is raised and the split is strict: nothing is judged on the data it was chosen on.

**The grid (fixed now, every cell is one try; N = 1,760).**
- **Series:** KXBTC15M, KXGOLD15M, KXETH15M, or all three pooled (4).
- **Entry minute:** the candle ending 840, 720, 600, 480 or 360 s before the close (5).
- **Band (ask of the side bought):** 0.05 to 0.15, 0.15 to 0.30, 0.30 to 0.50, 0.50 to 0.70, 0.70 to 0.82, 0.82 to 0.88, 0.88 to 0.93, 0.93 to 0.97 (8). YES is tried before NO; one leg per market.
- **Condition:** none; momentum (the side's ask is at least 3c above the previous candle's); dip (at least 3c below); wide spread (ask minus bid at least 3c); tight spread (at most 1c) (5).
- **Exit:** hold to settlement (all entry minutes); or, for entry minutes 840, 720 and 600 only, a scalp with a +3c or +5c target on the closing bid and a time exit at the candle ending 480 s before the close (80 s before L1's earliest buy), as in SS1 (3 entry minutes x 2 targets).
- **Cell count:** per series, hold 5 x 8 x 5 = 200 and scalps 3 x 2 x 8 x 5 = 240, so 440; four series 1,760.
- **Costs:** taker fee `0.07 p (1 - p)` unrounded on the entry (and on the exit for scalps); settlement pays no fee; closing ask in, closing bid out.

**The split (fixed now).** Train: markets closing in the first 24 days after the first close. Validation: everything after, about 16 days, never used for any choice.

**Selection (the only free choice).** On the training days only, among cells with at least 150 training entries on at least 5 days, take the 10 with the highest mean net a contract after fees. Those 10 are frozen and each is read once on the validation days. Profit factor is printed, not used to select.

**Bar for a frozen cell (validation days only):** at least 300 validation entries on at least 5 days (fewer is `NOT_ENOUGH_DATA`, which is not a pass); a day-clustered z of at least **3.0** (raised from 2.5 because ten cells are read and 1,760 were searched); a mean above zero; still above zero with fees 20% higher. Verdict words: `FALSIFIED`, `NOT_YET_FALSIFIED`, `NOT_ENOUGH_DATA`. There is no `promote`.

**Fair-market placebo (hold cells).** The same selection and read run 10 times in a world where every outcome is drawn as a Bernoulli with probability equal to the entry's mid price (a market with no mispricing), keeping the real entries, prices, days and fees. It shows how good the best of 880 hold cells and its frozen top 10 look by luck alone. The real result is only interesting if it clearly exceeds the placebo's best.

**My prediction, before the run.** Nothing passes. The best training cell will be inside the placebo's range and the frozen top 10 will have a validation mean at or below zero. The earlier OW and SS families, the 15 minute efficiency findings and the cost arithmetic all point the same way.

**Count.** 1,760 variants: **4,576** tried once run (2,816 before this). Registered, not yet run.

**2026-10-12: SS2 ran once (`python -m scalper.ss2`, commit after the pre-registration, 10,288 settled markets, 40 days, Bitcoin, gold and Ethereum): nothing passes.**
- **Training days (6,254 markets, before 2026-09-26):** 742 of 1,760 cells had enough entries; **87 of them had a positive mean after fees**. The best was +4.47c a contract (all three series pooled, 720 s left, ask 0.88 to 0.93, hold, 155 entries).
- **Fair-market placebo (10 reps, the same entries and prices, outcomes drawn at the mid price):** the best hold cell on the training days looks like **+3.4c to +7.6c, median +5.4c** by luck alone. **The real best cell (+4.47c) is below the placebo median**, so it is not distinguishable from luck. The placebo's best frozen cell read on validation reaches a z of at most +0.43 (the bar is 3.0).
- **Frozen top 10 read once on the 4,034 validation markets:** one had 405 validation entries and was `FALSIFIED` (-1.11c, z -0.77). The other nine had fewer than 300 validation entries and are `NOT_ENOUGH_DATA`, which is not a pass. For information only, their validation means were +0.10c, +1.48c, -3.03c, -3.63c, +0.01c, -1.25c (twice, the same trades), +1.77c and -1.22c; the average over the ten is about -0.8c, with positive and negative cells on both sides of zero.
- **Against the prediction.** Predicted: nothing passes, the best training cell is inside the placebo's range, the frozen ten sit at or below zero. All three held.
- **What it establishes.** Another 1,760 combinations of series, entry minute, price band, condition and exit found no rule that survives a split. About 12% of cells looked positive on the training days, which a fair market also produces. The selection picked mostly thin, 150 to 400 entry cells, which is where luck lives.
- **Nothing is built from it.** L1 is not changed.
- **Count.** 1,760 variants: **4,576** tried in total.

## Pre-registration: BK1 (seven basket and pair ideas, written 2026-10-13 before `bk1.py` was run on any market)

Source: the owner's question "what if we had a strategy that covered a broader market with the same direction, i.e. buy yes on all 15 min markets, 1 share each", and the 165 idea brainstorm (`07_ideas_list.md` in the handoff folder). Measured before this section, on the same 40 days (10,293 settled markets), as controls and not counted as tries: YES resolved 50.2% overall (Bitcoin 50.1, Ethereum 50.6, gold 50.0); buying YES on every market at the open cost -2.27c a contract and NO -2.14c; at the L1 time -1.66c and -1.47c. So the bar for every idea below is not "beats zero" but "beats a random side bought at the same prices and times".

**Data and split.** `data/book.sqlite` as it stands (Bitcoin, gold and Ethereum 15 minute series, Sep 2 to Oct 12 2026). First 20 days and last 20 days are reported as halves. Nothing is tuned: every rule below is fixed here.

**One convention for every idea.** The signal candle S is the candle ending 840 s before the close (the first minute after the open); the entry candle E is the next one, ending 780 s before the close, so the entry is on a bar strictly later than the signal. Entry is a taker at E's closing ask, 1 contract per leg, held to settlement, fee 0.07 x p x (1-p) per contract (stress: fee x 1.2). A market with an unusable quote (`valid_quote` false) at S or E is dropped, never bridged. BK7 uses its own candles, stated below.

**The seven ideas (7 tries, no variants).**

| ID | Idea | Counterparty | Rule | Matched baseline (a random side at the same prices) | Prediction |
|---|---|---|---|---|---|
| BK1 | Favorite at the open | Sellers who price favorites too low | Buy the side with the higher mid at S (skip an exact 50c) | Average of the YES and NO buys at E in the same markets | Contrast between -0.5c and +0.5c; net about -2c |
| BK2 | Underdog at the open | Longshot buyers, if the bias exists | The other side of BK1 | Same | Contrast mirrors BK1, net about -2c |
| BK3 | Bitcoin YES plus Ethereum NO, every window both exist | Makers who quote them independently | Two legs at E; unit is the pair | Average of the four side combinations for the same pair of markets | Net about -4c a pair, contrast near 0 |
| BK4 | Bitcoin YES plus gold NO | Same | Same with gold | Same | Same |
| BK5 | Divergence pair | Slow quoters on the cheaper series | Only when the Bitcoin and Ethereum mids at S differ by 0.10 or more: YES on the lower mid, NO on the higher | Average of the four combinations, same windows | Net about -4c, contrast near 0 |
| BK6 | Narrow spread only | Nobody (a cost selection, allowed because spread is seen before the trade) | Buy YES at E only when E's spread is 1c or less | YES at E in all markets of the same days | Net less negative than the baseline by about 1c, still negative |
| BK7 | Ethereum lags Bitcoin's early extreme | Slower Ethereum quoters | At the candle ending 480 s before the close, if the Bitcoin mid is 0.95 or more, buy Ethereum YES at the next candle's ask when that ask is 0.90 or less; if the Bitcoin mid is 0.05 or less, buy Ethereum NO under the same ask cap | A random Ethereum side at the same candle in the same windows | The only one with a plausible positive contrast; most likely too few entries |

**Verdict words:** FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. There is no promote verb. NOT_ENOUGH_DATA if fewer than 300 entries or fewer than 5 days. Otherwise NOT_YET_FALSIFIED only if ALL of: net mean per unit above 0 on the full 40 days; day-clustered z of net at least 2.1; contrast (net minus matched baseline) mean above 0 with day-clustered z at least 2.1; both halves' net means above 0; stress net above 0. Anything else is FALSIFIED. With 7 tries the chance one passes on luck alone at this bar is about 12%, so a single pass would mean "watch it on new days", never "trade it".

**Overlap with L1 (the rule from "L1 is the only strategy").** All seven hold to settlement, so they overlap L1 in mindset and position. They are research only. Nothing here places an order.

### BK1 result (run once, 2026-10-13, `cd src && python -B -m scalper.bk1`)

10,288 settled markets in 3,792 windows, Sep 2 to Oct 12. Controls (not tries): YES at E in every market -2.32c, NO -1.92c. Net is per unit after the fee; contrast is net minus the matched random-side baseline; halves are the first and last 20 days.

| Idea | n | Net | z | Contrast | zc | Half 1 | Half 2 | Stress | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| BK1 favorite at the open | 10,239 | -2.21c | -3.75 | -0.09c | -0.16 | -2.24c | -2.18c | -2.53c | FALSIFIED |
| BK2 underdog at the open | 10,239 | -2.02c | -3.43 | +0.09c | +0.16 | -2.05c | -2.00c | -2.34c | FALSIFIED |
| BK3 Bitcoin YES + Ethereum NO (pair) | 3,792 | -5.06c | -7.69 | -0.83c | -1.27 | -5.20c | -4.91c | -5.69c | FALSIFIED |
| BK4 Bitcoin YES + gold NO (pair) | 2,692 | -4.76c | -4.19 | -0.54c | -0.47 | -3.54c | -6.10c | -5.39c | FALSIFIED |
| BK5 divergence pair | 453 | -3.39c | -2.10 | +0.83c | +0.51 | -2.17c | -4.41c | -4.02c | FALSIFIED |
| BK6 narrow spread only | 9,455 | -2.26c | -3.81 | +0.07c | +0.46 | -2.05c | -2.48c | -2.58c | FALSIFIED |
| BK7 Ethereum lags Bitcoin's early extreme | 18 | -4.55c | -0.75 | -3.00c | -0.50 | n/a | n/a | n/a | NOT_ENOUGH_DATA |

**Seven tries, all FALSIFIED or NOT_ENOUGH_DATA, as predicted.** No contrast reaches 1c in either direction, and none has |zc| above 1.3: choosing the favorite, the underdog, a pair, or a narrow spread beats a random side by nothing, so the whole result is the cost. A basket across Bitcoin, Ethereum and gold adds size, not edge.

**What the cost is made of.** A contract bought near 50c costs about 2.2c: the fee alone is 0.07 x 0.5 x 0.5 = 1.75c, plus about half a cent of spread. That is why BK6 (narrow spread only) barely helps (-2.26c against -2.32c): 92% of entries already had a spread of 1c or less, and the fee is the big part. The fee is smallest at the ends (0.07 x 0.9 x 0.1 = 0.63c at 90c), which is the arithmetic reason L1 buys at 88c to 97c, not at coin-flip prices.

**BK7** found only 18 entries on 13 days: Ethereum is usually priced in by the time Bitcoin is at an extreme with 8 minutes left, which is a finding about how fast Ethereum quotes follow Bitcoin, not a verdict on the idea. It stays NOT_ENOUGH_DATA and consumes no further try. Mutation notes: the tests killed every mutant I tried on the rules, after one same-second bytecode cache hiccup (stale `.pyc` after a same-size edit) that I caught by clearing `__pycache__` and re-running with `-B`.

## Pre-registration: E3, L1 unchanged on seven more 15 minute series (written 2026-10-13 before any of these markets was downloaded and before any result)

**The question.** The owner asked for "something with an edge that I can expand on", trading often enough to watch, simple to drop money into. L1 is the only thing live with a measured positive edge, and the E1 and E2 results say it is the same thin edge (+0.5c a contract) on every crypto series and a larger one on gold (+1.47c, z +2.80, the only series that cleared the bar alone). So the cheapest honest expansion is the same rule on more markets of the same kind. This section is that test on history, and nothing else.

**What was checked first (2026-10-13, public Kalshi data, counts and volumes only, no result).** Series that exist as 15 minute up/down markets and settled in the last 30 days, with median contracts traded per settled market: XRP 74,819; Dogecoin 36,878; HYPE 23,523; BNB 17,154; EUR/USD 4,538; GBP/USD 4,229; USD/JPY 3,781 (USD/CAD and AUD/USD only started Oct 7, 1,100 each, left out). The S&P, Nasdaq, Dow and Treasury yield 15 minute series have **no settled markets in the last 30 days** and are left out. Cardano has none either. For scale, Bitcoin was 3.5 million, gold 458,000, ETH 175,000, SOL 90,000 at the E1 check. The FX series are thin (their open books show 2c to 4c spreads), so they are the weak candidates and are included because gold, the non-crypto market, is the one that carries L1.

**Data.** `python -m scalper.e3 fetch`: every settled market of the seven series that closed in the last 40 days, with 1 minute bid/ask candles, into a **separate database `data/alts2.sqlite`**; `book.sqlite` and `alts.sqlite` and every earlier result are untouched.

**Rule (fixed now, identical to L1 and to E1, E2).** One observation per market from the candle that ENDS exactly 360 s before the close; buy the favourite when its ask is 0.88 to 0.97 (either side), hold to settlement, taker at the ask, the same fee model as `lstrats.net`. No filter, no other band or minute. A market with no candle at that minute, no quote in the band, or no result has no observation.

**Seven tries (XRP, DOGE, HYPE, BNB, EURUSD, GBPUSD, USDJPY), no variants.** Also reported as information, not a try: the seven pooled, the four crypto pooled and the three FX pooled.

**Counterparty.** The same as L1's and no new one is claimed. Crypto alts move with Bitcoin, so a pass would not be independent evidence (E1 and E2 measured that: when Bitcoin's entry lost, ETH's lost 51% of the time and SOL's 43%, against about 6%).

**Numeric prediction, before the run.** Crypto alts: about +0.5c a contract like ETH and SOL, z between 0 and 1.5, **FALSIFIED** on z. FX: at or below 0.0c because of the 2c to 4c spreads, **FALSIFIED**. If any series shows a mean above +1.5c it is an audit trigger first.

**Pass bar, fixed (the same as every earlier test).** `NOT_YET_FALSIFIED` only if ALL hold: at least 300 observations; at least 5 days; day clustered z of net per contract at least 2.1; mean net above zero; both halves of the days positive; mean above zero with fees times 1.2. Anything else is `FALSIFIED`. With seven tries, about 12% of the time one would pass by luck alone, so a single pass means "watch it forward", never "trade it". A pass is permission for the next stage only (a forward shadow run on new days, then a small stake), and never a reason to change the live bot.

**Information, not part of the verdict.** Per series: observations per day, win rate against the mean price paid, mean net by half, median traded volume of the entry minute's candle in contracts, and the median spread at the entry candle.

**Count.** Seven variants, one parameter set each. The running total in this file was 4,576 before today's BK1 (7), so it is 4,590 with these seven. The control is not needed because nothing is searched.

**Limits.** Candle asks are quotes, not our fills: the live bot fills about 56 to 59% of its signals. Thin books fill less at size, and the FX books are thin. The window is 40 days or whatever exists, so the FX series have under 20 days.

## Pre-registration: E4, L1 unchanged on the hourly ladders (written 2026-10-13 before any ladder market was downloaded and before any result)

**The question.** The owner asked for L1's rule on Kalshi's hourly "price above or below" ladders: more trades a day, same simple mechanism. Each hourly close lists many strikes at once (checked 2026-10-13, counts only: Bitcoin 188 strikes per close with a close every hour, 4,592 settled markets a day; Ethereum 300 per close, 7,240 a day; S&P 500 60 per close, 7 closes a day during US hours, 420 a day), so a single rule fires on several strikes in the same hour.

**Why this is not a bigger version of the 15 minute tests.** Every qualifying strike in one hour hinges on the same price move, so their outcomes are close to perfectly correlated: one adverse last-six-minutes move can lose five or six entries at once. The effective sample is hours, not markets. That makes the test far less powerful than E1 to E3 for the same number of entries, and the registration says so up front.

**Data.** `python -m scalper.e4 fetch`: every settled market closing in the window below, with the 1 minute candles from 420 s to 300 s before its close (the entry candle and its neighbours; one request covers 100 strikes), into a **separate database `data/ladders.sqlite`**. Windows: S&P `KXINXU` 40 days; Bitcoin `KXBTCD` and Ethereum `KXETHD` **14 days**. (This was 30 days in the first draft of this section. It was cut to 14 on 2026-10-13, still before any ladder market was downloaded or any result existed, because at the fetch rate measured on E3 about 16 requests a minute, 30 days of Bitcoin and Ethereum would have taken about four hours. 14 days is still 336 hourly closes each, and the power rule below reports what that can and cannot see.)

**Rule (fixed now, identical to L1 and to E1 to E3).** One observation per market from the candle that ENDS exactly 360 s before the close; buy the favourite when its ask is 0.88 to 0.97 (either side), hold to settlement, taker at the ask, the same fee model as `lstrats.net`. No filter, no other band or minute. A market with no candle at that minute, no quote in the band, or no result has no observation.

**Three tries (KXINXU, KXBTCD, KXETHD), no variants.**

**Counterparty.** The same as L1's, plus one specific to ladders: a market maker quoting 60 to 300 strikes at once reprices the deep strikes less carefully than the near ones, and retail buys the cheap tail. No new claim beyond that. Bitcoin and Ethereum are the same bet as each other (E1 measured it), so a pass on both would count as one piece of evidence.

**Numeric prediction, before the run.** Each series lands near L1's thin figure, **+0.5c per contract net, z between 0 and 1.5**, and the minimum detectable edge reads above 1c: this test probably cannot see a +0.5c edge. **Expected verdict: all three `FALSIFIED`** (the word says "not shown", see the rule below). If a series shows a mean above +1.5c it is an audit trigger first.

**Pass bar, fixed (the same as every earlier test).** `NOT_YET_FALSIFIED` only if ALL hold: at least 300 observations; at least 5 days; day clustered z of net per contract at least 2.1; mean net above zero; both halves of the days positive; mean above zero with fees times 1.2. Anything else is `FALSIFIED`. With three tries, about 5% of the time one would pass by luck, so a single pass means "watch it forward", never "trade it".

**The power rule, fixed now.** For each series the run also prints the **minimum detectable edge** (2.1 times the day clustered standard error of the mean net). **If that is above +1.0c, a `FALSIFIED` means "not shown at this sample size" and is reported that way; it is not evidence the edge is absent.** The next stage in that case is a forward shadow record on new days (needs a server change and a deploy, not built), not more history.

**Information, not part of the verdict.** Per series: observations per hour that has any, hours with at least one observation, the same z clustered by HOUR instead of day, the worst single hour (the sum of net over that hour's entries, which is the real size of a ladder loss), win rate against the mean price paid, mean net by half, and one row for "one entry per hour" (the entry whose ask is nearest 0.925, ties to the lower strike), which is what a live bot with a one-order-per-hour cap would take.

**Count.** Three variants, one parameter set each. The running total in this file was 4,590 before E4 (4,576, plus BK1's 7, plus E3's 7), so it is 4,593 with these three. The control is not needed because nothing is searched.

**Limits.** Candle asks are quotes, not our fills (the live bot fills 56% to 59% of its signals), and a ladder hour spreads several orders across thin strikes, so fills are likely worse than for one 15 minute market. Settlement of hourly markets uses a different reference than the 15 minute ones (an hourly price, not a 60 second average), so this is not the same bet on a different clock.

## Pre-registration: WX1, daily high-temperature markets against a public forecast (written 2026-10-13 before any weather market was downloaded and before any forecast was fetched)

**Why this one.** The owner asked for new edges, not only more of L1. Every earlier test priced a market against itself (its own history, its own quotes). Weather is the first case where an independent, free, public source (a numerical forecast) says something about the outcome that casual bettors may not read, with a new market every day in many cities. It is also frequent and simple to run hands-off if it ever worked. Counterparty: casual bettors, and market makers who quote a day-ahead bucket from a rough forecast; the loser is whoever sells a bucket the forecast makes much more (or less) likely than its price.

**What was checked first (2026-10-13; structure and availability only, no result).** Kalshi lists each city's daily high as six markets a day (four 2 degree buckets plus two tails), opening 14:00 UTC the day before and closing at local midnight (standard time) after the target day; 69 days of settled markets exist with hourly candles (bid, ask, volume). Open-Meteo's previous-runs API serves each hour's forecast as it stood a day earlier (`temperature_2m_previous_day1`), keyless. The quoted spreads are about 1c and hourly volumes run from tens to thousands of contracts for the busier cities, so size is not the obstacle.

**Universe, fixed now and chosen for nothing but being the longest listed daily-high series with markets in this data:** Chicago `KXHIGHCHI` (Midway 41.7860, -87.7524), New York `KXHIGHNY` (Central Park 40.7789, -73.9692), Miami `KXHIGHMIA` (25.7959, -80.2870), Austin `KXHIGHAUS` (30.1945, -97.6699), Denver `KXHIGHDEN` (39.8466, -104.6562), Los Angeles `KXHIGHLAX` (33.9382, -118.3866), Philadelphia `KXHIGHPHIL` (39.8719, -75.2411). Seven cities, one rule each, no per-city tuning.

**Data.** `python -m scalper.wx1 fetch`: every settled market of the seven series that closed in the last 69 days with its hourly candles over its whole life, into a **separate database `data/weather.sqlite`**, and for each city the hourly `temperature_2m_previous_day1` series (°F, UTC) for the same period from `previous-runs-api.open-meteo.com`.

**The forecast.** For a target day with market close `c`, the climate day is the 24 hours ending at `c` (UTC). `mu` = the maximum of the previous-day-1 hourly forecasts inside that window. No fresher forecast is used. A decision at 22:00 local the evening before sits at least a few hours after the model runs that feed those hours, so the forecast is not from the future; the decision candle is stated below.

**The model, walk forward only.** For city X on target day D, use only days whose results were already known at D's decision time (at least 20 and at most the last 20 resolved days before D). Observed temperature on a past day = the midpoint of the bucket that resolved YES (a tail bucket is dropped from the fit). Error = observed minus that day's `mu`. `bias` = mean error, `sigma` = the larger of the standard deviation of the errors and 1.5 °F. Fewer than 10 usable days in the window: that city-day has no trades. Probability of a bucket = Normal(`mu` + `bias`, `sigma`) over the bucket's range, with integer rounding: a "between a and b" bucket is [a - 0.5, b + 0.5), a "less" tail with cap c is below c - 0.5, a "greater" tail with floor f is at or above f + 0.5.

**The rule (fixed, one parameter set).** Decision candle: the hourly candle ending exactly 26 hours before the close (22:00 local standard time the evening before). Entry: the NEXT hourly candle (ending 25 hours before the close), so the entry is on a strictly later bar. For every bucket of the day with a usable quote at that candle (bid at least 0.01, ask at most 0.99, ask not below bid): edge_YES = p - ask_YES - fee, edge_NO = (1 - p) - ask_NO - fee with ask_NO = 1 - bid_YES. Take the side with the larger edge if it is at least 0.03 and that side's price is between 0.05 and 0.95. At most one trade per bucket, hold to settlement, taker at the ask, fee 0.07 x p x (1 - p) per contract. Test days: every day with at least 20 prior resolved days (about days 21 to 69).

**One try, no variants.** The edge threshold (0.03), the price band and the 26 hour decision time are chosen here and not touched. A sensitivity table over the threshold (0, 0.02, 0.03, 0.05) is printed as information only and is not a try.

**Pass bar, fixed (as in every earlier test, with a placebo).** `NOT_ENOUGH_DATA` if fewer than 200 trades or fewer than 20 days. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: mean net per contract above zero; z clustered by target date at least 2.1; both halves of the test days positive; positive with fees x 1.2; and the mean net above the 95th percentile of a fair-market placebo (200 repetitions with the same entries, prices and fees, outcomes drawn as Bernoulli at the entry's mid price). Anything else is `FALSIFIED`.

**The power rule, as in E4.** The run prints the minimum detectable edge (2.1 times the date clustered standard error). If it is above 3c, a `FALSIFIED` is reported as "not shown at this sample size". With a few hundred trades and a win-or-lose payoff it very probably will be.

**Information, not part of the verdict.** Per city: days, trades, mean net; the model's Brier score against the market mid's Brier score on the same buckets (does the model predict better than the price?); fitted bias and sigma by city; trades by side.

**Numeric prediction, before the run.** Weather makers use the same public models, so the market is close to the model: net about -1c to -2c a contract (cost), `FALSIFIED`, model Brier within a few percent of the market's. A pass would be a surprise and would be an audit trigger first (check the decision candle precedes any forecast information, and that no day's own result enters its own calibration).

**Count.** One variant. The running total in this file was 4,593 before WX1, so it is 4,594 with it.

**Limits.** Candle asks are quotes, not fills; the bucket quotes are thin for the smaller cities. The last few evening hours of a climate day are forecast by a run initialised about 24 hours before THOSE hours, which can be a little after the 22:00 local decision; they only matter on days when the maximum falls late in the evening, which is rare, and the effect cannot be removed without changing the registered rule. A forecast for a grid point is not the airport station's thermometer, which is what the bias term is for. Open-Meteo's "previous day" values are archived model output, and whether any archived value was revised after the fact is not something I can check.

## Pre-registration: DT1, a decision tree that skips L1 entries it flags as losers (written 2026-10-13 before any tree was fitted)

**Why.** The owner suggested decision trees and sub rules. L1 enters about 70 times a day with a 6% loss rate, so the only way to add edge without new markets is to skip the entries that are worse than the rest. Earlier filters were single, hand-picked conditions (`l1filters2.py`, S and F families, OW7 still on forward read). A shallow tree is the honest way to ask the question once: do the features available at entry say which entries lose, on days the tree never saw?

**Data and split.** `data/book.sqlite` as it stands: every L1 entry (the rule of `lstrats.L1`: the candle ending 360 s before the close, favourite ask 0.88 to 0.97, either side) on Bitcoin, gold and Ethereum, 40 days. The first 20 days are TRAIN, the last 20 days are VALIDATION, read once.

**Features, fixed now (all known at the entry candle or earlier).** (1) price paid; (2) side is YES; (3) spread at the entry candle; (4) change in the favourite side's mid over the last 1 minute; (5) the same over 3 minutes; (6) the favourite side's mid now minus its mid at the first candle of the market; (7) log volume of the entry candle; (8) UTC hour; (9) series is gold; (10) series is Ethereum; (11) the previous market of the same series resolved YES. Eleven features and nothing else; no feature is added after seeing results.

**The tree.** Regression on net per contract, depth at most 3, at least 150 training entries in a leaf, splits at the deciles of each feature, chosen by variance reduction. Written in numpy in `dt1.py`; there is no tuning of depth, leaf size or deciles.

**The rule.** Skip an entry if the tree's training-mean net for its leaf is at most -0.5c; trade all others. The tree and the rule are fixed on TRAIN alone, then applied to VALIDATION.

**The null (what luck produces).** 200 refits of the same tree on TRAIN with the net values shuffled across training entries within each series, each applied to VALIDATION with the same rule. The real result must beat what a tree fitted to noise achieves on the same days.

**One try, no variants.** The count is one tree and one skip rule.

**Pass bar, fixed.** `NOT_ENOUGH_DATA` if the tree skips fewer than 100 validation entries. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: the skipped validation entries' mean net is below zero with a day clustered z of at most -2.1; the improvement (minus the sum of the skipped entries' net, per validation day) is above the 95th percentile of the null; the skipped entries' mean net is below zero in both halves of the validation days; and the traded entries' mean net is higher than the baseline mean. Anything else is `FALSIFIED`. A pass means "watch it on new days", never "change the bot": the live bot does not change for any research result here, and the next stage would be a forward shadow record (needs a server change, not built).

**Prediction, before the run.** The tree finds leaves that look bad in TRAIN, none of them stay bad in VALIDATION, and the improvement sits inside the null band. `FALSIFIED`. The skipped set is expected to be 5% to 25% of entries.

**Information, not part of the verdict.** The fitted tree printed in words, TRAIN and VALIDATION mean net by leaf, the share of entries skipped, and the improvement in cents per day with the null's 5th, 50th and 95th percentiles.

**Count.** One variant: the running total in this file was 4,594 before DT1 (WX1 included), so it is 4,595 with it.

**Limits.** A skip rule needs the live bot to see the same features at the same moment, with its own latency. The 6% loss rate means about 3,000 entries hold only about 180 losses, so the tree is fitted to few events, which is why the shuffled-label null is the arbiter and not the raw improvement.

### DT1 result (run once, 2026-10-13, `cd src && python -B -m scalper.dt1`; the rule, bar and prediction are those registered above)

3,037 L1 entries with every feature (Bitcoin, gold, Ethereum, 40 days): TRAIN 1,532 (before Sep 22), VALIDATION 1,505. The tree fitted on TRAIN split first on UTC hour (6 and earlier), then side, price and the 3 minute move, and flagged three leaves (-3.33c over 230 entries, -2.22c over 255, and one more negative) as losers to skip.

| | Value |
|---|---|
| Validation entries skipped | 537 of 1,505 (35.7%) |
| Skipped entries' mean net | **+0.79c** (day clustered z +0.64; halves +0.59c / +0.98c) |
| Traded entries' mean net | -0.29c against a baseline of +0.10c |
| Improvement | -20.26c per day; shuffled-label null 5th / 50th / 95th percentile -28.70c / -2.14c / +27.08c |
| Verdict | **`FALSIFIED`** |

- **Prediction against outcome.** Predicted: leaves that look bad in TRAIN do not stay bad in VALIDATION, improvement inside the null band, `FALSIFIED`, 5% to 25% skipped. Measured: as predicted, except that 35.7% was skipped (above the range I guessed).
- **The skipped entries did not lose, they won slightly more than the rest** (+0.79c against a +0.10c baseline). The "bad" leaves in TRAIN were noise: with about 90 losses among 1,532 training entries a depth 3 tree can always find regions with a bad run, and they did not repeat. The shuffled-label null has a 95th percentile of +27c per day, so even a large improvement would not have counted; this one was negative.
- **Audit triggers.** None: nothing was better than predicted. The feature code reads only candles at or before the entry candle and the previous market's result, by test.
- **Count.** One variant: 4,595 as of 2026-10-13. The bot is unchanged.

## Information: GROWTH, what L1 could do to an account with monthly deposits (2026-10-13; not a hypothesis, not a try, no variant counted)

`cd src && python -B -m scalper.growth`: a day-block bootstrap of the 3,038 L1 entries (Bitcoin, gold, Ethereum, 41 days, measured mean net **+0.41c** per contract after fees), each filled with probability 58% (the live fill rate), under a simplified version of the live sizing and stop rules (contracts = start-of-day balance / $46.50, at most 40; one window's cost held to 4.5% of the balance; a day stops at -5%). Start $500 plus $500 every 30 days, 400 paths of 360 days per scenario. Every scenario shifts each entry's net by a constant so the mean net per contract equals the stated true edge.

| True edge | Day 90 median (paid in $1,500) | Day 360 median (paid in $6,000) | Day 360 5th to 95th percentile | Paths below what was paid in at day 360 |
|---|---|---|---|---|
| -0.50c | $1,201 | $3,857 | $2,317 to $5,353 | 98% |
| 0.00c | $1,556 | $6,139 | $4,342 to $7,912 | 46% |
| +0.25c | $1,746 | $7,444 | $5,768 to $9,438 | 9% |
| **+0.41c (measured)** | $1,908 | **$8,428** | $6,611 to $10,231 | **1%** |
| +1.00c | $2,533 | $11,595 | $9,962 to $13,543 | 0% |

**What it says.** If the measured edge is real, L1 would add about 40% on top of the deposits over a year at this size, which is real money on a growing balance and still not an income that replaces anything. If the edge is zero the account just returns the deposits less a coin-flip's worth of noise (46% of paths below paid-in), and a small negative edge (a fee change, worse fills) loses most of the deposits over a year. The measured edge has a z of about 1.5, so all rows are live; the live record (about 165 settled trades by Oct 13) is too short to choose between them.

**Left out on purpose:** the profit add-on pool, the weekly review's step timing, open positions counted as lost, correlated losses across series within a window beyond the window cap, fills that depend on price (the order data suggests the misses lose more than the fills, see below), and the chance that the edge decays. Treat the table as a size-of-the-thing check, not a forecast.

## Information: do the orders that fill differ from the ones that miss? (2026-10-13; the owner's pasted order diagnostics, not a hypothesis, not a try)

150 live L1 orders (2026-10-08 to 10-12) joined to the settled results in `book.sqlite` (133 had a result in the database). For an order that missed, the outcome is what it WOULD have earned at its decision price.

| | Orders | Won | Mean net per contract |
|---|---|---|---|
| Filled | 80 | 77 (96.2%) | **+2.68c** |
| Missed (hypothetical at the decision price) | 53 | 48 (90.6%) | **-1.79c** |

- **The gap is not significant.** 96.2% against 90.6% is a difference of 5.6 points with a standard error of about 4.5 (z about 1.25, 3 losses against 5). It is a pattern worth watching, not a result.
- **The limit cushion.** Orders sent with a limit at the decision price filled 36% of the time (17 of 47), and those that did fill averaged +3.13c; orders with a cushion filled 73% (63 of 86) at +2.56c a contract. Per signal (a miss earns nothing) the cushioned orders earned +1.88c against +1.13c. The pattern fits "more fills, and the extra fills are not worse than the rest", but with 133 orders and 8 losses nothing here can say whether a cushion helps.
- **What would settle it.** The same join on a few hundred more orders (the page's "Copy order diagnostics" export), or the forward shadow record. Until then the live bot, its limits and its cushion stay exactly as they are.

## Information: why there is no WX2 (late-day weather certainty), 2026-10-13

The idea: by the evening the day's high temperature is nearly known from observations, so a late quote of 85c to 97c on the favourite bucket might still be cheap. Before registering anything, the Chicago daily-high series was checked for PRICES only (no outcomes, no model): at 8 hours before the close 8 of 351 quoted buckets had a side priced 80c to 98c, and at 6, 4, 3 and 2 hours before the close **none of about 310 did**. The market has already moved to the extremes (98c or more, or 20c or less) by then, so there is nothing in the band to buy. Not registered, not run, no variant counted; the idea is closed by availability.

## Pre-registration: XM1, does the hourly ladder price the 15 minute market better than the 15 minute market does (written 2026-10-13 before any ladder strike was downloaded for this test and before any result)

**The idea (new: a cross-market consistency test, not an L1 variant).** Every hour a Bitcoin (and Ethereum) 15 minute up/down market closes at the same moment as the hourly "price above X" ladder, which has 188 (Bitcoin) or 300 (Ethereum) strikes and, in an example looked at while writing this (quotes only, one hour), strikes $100 apart near the money with 1c spreads. The 15 minute market's strike is the price at its open, so the ladder, read between the two strikes that bracket it, is an independent price for the same event. If the ladder is the better-informed (deeper, more watched) market, the 15 minute market's quote should drift to the ladder's; where it has not by 6 minutes before the close, the gap is the trade. Counterparty: whoever quotes the 15 minute market without reading the ladder.

**What was checked first (2026-10-13; quotes of one hour, no outcomes used):** at the close of KXBTC15M-26OCT131400 (strike 83,132.07) the ladder's YES bid/ask 6 minutes before the close were 83,099.99: 0.01 / 0.02, 83,199.99: 0.00 / 0.01 and 82,999.99: 0.08 / 0.09, and the 15 minute market's own quote was 0.012 / 0.013, so in that hour they agreed. One hour proves nothing; it shows the join is possible and that the expected result is "they agree".

**Data.** Hourly-aligned 15 minute markets (close on the hour) of Bitcoin and Ethereum from `data/book.sqlite` (about 40 days, up to 960 windows each). For each, `python -m scalper.xm1 fetch` lists that hour's ladder (`KXBTCD`, `KXETHD`), keeps the strikes within 1.5% of the 15 minute market's strike (chosen from the strike alone, never from any outcome), and stores their quote at the candle ending 360 s before the close, into a **separate database `data/xm1.sqlite`**.

**Rule (fixed now, one parameter set per series).** At the candle ending 360 s before the close: `p` = the mid of the ladder's YES (above) quote interpolated linearly in strike between the two ladder strikes that bracket the 15 minute strike (both must have a valid quote: bid at least 0.001, ask at most 0.999, ask not below bid; no bracket, no trade). edge_YES = p - ask_15m - fee, edge_NO = (1 - p) - (1 - bid_15m) - fee. Take the side with the larger edge if it is at least 0.02 and its price is between 0.03 and 0.97. One trade per window, taker at the 15 minute market's ask, hold to settlement, fee 0.07 x p x (1 - p) per contract. No tuning of the 0.02, the 1.5% or the minute.

**Two tries (Bitcoin, Ethereum), no variants.**

**Pass bar, fixed (as for WX1).** `NOT_ENOUGH_DATA` if fewer than 200 trades or fewer than 20 days. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: mean net above zero; z clustered by day at least 2.1; both halves of the days positive; positive with fees x 1.2; and above the 95th percentile of a fair-market placebo (200 repetitions, outcomes drawn at the 15 minute mid). Anything else is `FALSIFIED`. The power rule: the run prints the minimum detectable edge and, if it is above 2c, a `FALSIFIED` is reported as "not shown at this sample size".

**Numeric prediction, before the run.** The two markets agree to within a cent or two nearly always, so few windows trade (fewer than 200 is likely, `NOT_ENOUGH_DATA`), and those that do net about -1c. If a series reaches a mean above +1.5c it is an audit trigger first (check that the interpolation uses only quotes at or before the entry candle and that the strike comes from the 15 minute market's own ticker).

**Information, not part of the verdict.** The distribution of the gap (p minus the 15 minute mid) in cents: median, 5th and 95th percentile and the share above 2c; windows with a bracket; the Brier score of the ladder's p against the 15 minute mid's, on the same windows.

**Count.** Two variants: the running total in this file was 4,595 before XM1, so it is 4,597 with it.

**Limits.** The 15 minute market settles on a 60 second average and the hourly ladder on a single reference value, so the two are not the same bet to the cent. Ladder quotes are mids of tight books, not fills; the 15 minute side fills about 56% to 59% of the time live.

## Information: the 25c exit on 40 days (2026-10-13; `cd src && python -B -m scalper.exit25`; not a hypothesis, not a try, nothing counted)

The live exit watch sells a held L1 position when its bid reaches 25c (the owner's setting since Oct 12). On the 3,038 L1 entries of the 40 day history, using the minute candle closes after the entry (a coarse proxy for a watch that looks about every 10 seconds, so triggers here are a lower bound):

| | Value |
|---|---|
| Entries whose held side's bid closes at or below 25c at some later minute | 146 of 3,038 (4.8%) |
| Of those 146 held to settlement | 16 won (**11.0%**), mean net **-80.9c** per contract |
| With the line (sold at that minute's bid), optimistic | -81.7c on those 146; over all entries **+0.374c** against hold-only **+0.411c** (-114c over 3,038 entries, about -0.04c an entry) |
| With the line and 5c of extra slippage | -85.4c on those 146; **+0.197c** against **+0.411c** (-652c over 3,038 entries) |

**What it says.** Once the bid is at 25c or lower the position wins 11% of the time, close to what it would fetch if sold (the bid at the first minute close below the line averaged only about 11c, because these markets fall in jumps and the line is already behind them at the next close). So the line is close to neutral in this history: it neither saves money nor costs much, and each cent of slippage on the sale makes it a little worse. This does not say to change it: the exit watch exists to cut a tail (a position that is going to zero), and the history cannot see the seconds inside a minute where the live watch acts. The earlier exit studies (X1 to X8) reach the same conclusion at other lines.

## Information: how stable is L1's edge week to week, and how thin is it in loss-rate terms (2026-10-13; not a hypothesis, nothing counted)

L1 entries by calendar week of the 40 day history (mean net per contract in cents; entries in brackets):

| Week from | All | Bitcoin | Gold | Ethereum |
|---|---|---|---|---|
| Sep 2 | +0.7 (507) | +0.7 (174) | +1.8 (138) | +0.0 (195) |
| Sep 9 | +0.5 (531) | -0.7 (189) | +1.8 (143) | +0.6 (199) |
| Sep 16 | +1.2 (574) | +3.1 (220) | -1.8 (150) | +1.4 (204) |
| Sep 23 | +1.0 (539) | +2.4 (193) | +1.7 (133) | -0.7 (213) |
| Sep 30 | **-1.2** (546) | -2.7 (206) | +2.3 (138) | -2.1 (202) |
| Oct 7 (partial) | +0.1 (341) | -1.1 (139) | +0.1 (75) | +1.5 (127) |

- **The weekly figure is noise-sized.** One week of about 540 entries has a standard error of about 1.0c (an average win of +6.8c, an average loss of -91.8c). Every week is within about 1.5 standard errors of the overall +0.4c; the -1.2c week of Sep 30 is the lowest and the last two weeks are the weakest, which is worth watching and is not distinguishable from luck.
- **The edge in loss-rate terms.** The break-even loss rate is 6.8 / (6.8 + 91.8) = **6.9%**. Observed loss rates: Bitcoin 6.5% (73 of 1,121), gold 5.9% (46 of 777), Ethereum 6.8% (77 of 1,140). The whole +0.4c edge is a loss rate half a point below break-even, which is why 3,000 entries cannot separate it from zero (z about 1.5) and why one extra loss in 50 trades changes the sign.
- **Gold is the lowest loss rate, and still only about one standard deviation under break-even:** 46 losses in 777 entries against 54 expected at 6.9% (a standard deviation of about 7 losses, so z about -1.1). Bitcoin (73 against 77 expected) and Ethereum (77 against 79) sit within a loss or two per hundred of break-even.

### WX1 result (run once on the complete download, 2026-10-13, `cd src && python -B -m scalper.wx1 run`; the rule, bar and prediction are those registered above, nothing was changed after seeing them)

(An earlier `run` read an empty database after the first download crashed on a dropped TLS handshake; that printed `NOT_ENOUGH_DATA` on zero markets and is not a result. The fetch got retries and was rerun.) 2,898 market-days, seven cities, 69 days; 988 trades on 48 test days; 1,714 priced buckets scored.

| | Value |
|---|---|
| Trades | 988 on 48 days (627 NO, 361 YES) |
| Mean net per contract | **-3.26c**, day clustered z **-2.51** |
| Halves | -1.88c / -4.60c |
| Fees x 1.2 | -3.50c |
| Fair-market placebo, 95th percentile of the mean | +0.38c |
| Minimum detectable edge | +2.72c (below the 3c flag, so this is a real `FALSIFIED`, not "not shown") |
| Verdict | **`FALSIFIED`** |

| City | Trades | Net | Brier: model | Brier: market |
|---|---|---|---|---|
| Chicago | 149 | -3.59c | 0.1663 | 0.1154 |
| New York | 133 | -5.60c | 0.1556 | 0.1042 |
| Miami | 157 | -3.66c | 0.1589 | 0.1231 |
| Austin | 137 | -4.30c | 0.1468 | 0.1204 |
| Denver | 144 | -5.79c | 0.1380 | 0.0988 |
| Los Angeles | 135 | **+4.73c** | 0.1367 | 0.1232 |
| Philadelphia | 133 | -4.38c | 0.1507 | 0.1224 |
| All | 988 | -3.26c | **0.1504** | **0.1153** |

Threshold sensitivity (information only): edge at least 0, 0.02, 0.03, 0.05 gives -3.45c, -3.91c, -3.26c, -3.20c on 1,136, 1,044, 988 and 865 trades: no threshold turns it.

- **Prediction against outcome.** Predicted: net -1c to -2c, `FALSIFIED`, the model's Brier within a few percent of the market's. Measured: `FALSIFIED` as predicted, but **worse** than predicted: -3.26c with a significantly negative z, and the model's Brier is **30% worse** than the market's (0.1504 against 0.1153), not within a few percent.
- **What it means.** The day-ahead markets are priced by something better informed than a day-old model run plus a rolling bias fit: the market beats the forecast model in every one of the seven cities on probability accuracy, so a trader using that model bets against better information and pays for it. The one positive city (Los Angeles, +4.73c on 135 trades) is the best of seven cities and sits inside what chance gives; with the minimum detectable edge at +2.72c per whole sample, one city with a fifth of the trades cannot show a real edge of that size.
- **Audit triggers.** None: nothing was better than predicted. The tests prove the calibration never uses a result that arrives after the decision, the entry candle is strictly later than the decision candle, and the fit is the last 20 days only.
- **Count.** One variant: WX1 is the 4,594th (the total was 4,593 after E4); DT1 (4,595) and XM1 (4,597) were registered after it. Weather lows, rain and the other cities are not tried: the same calibration gap would apply and no result here supports spending a try on them.

## Pre-registration: SP1, heavy favourites in the sports game-winner markets (written 2026-10-13 before any sports market was downloaded for this test and before any result)

**Why.** Everything tested so far lived on Bitcoin, gold and a few look-alikes, which move together, so even thousands of entries are only a few hundred independent events (that is why L1's +0.4c cannot reach significance). Sports game-winner markets are thousands of independent events a month, with retail money on the other side, and the oldest documented bias in betting markets is the favourite-longshot bias (favourites are slightly under-priced, longshots over-priced). L1's own result has that shape: a loss rate half a point under break-even at 88c to 97c. The fee is lowest at those prices (0.07 x 0.93 x 0.07 = 0.46c). This is the same mechanism on a much larger, independent sample. Counterparty: the bettor who buys the longshot (or sells the favourite too cheap).

**What was checked first (2026-10-13; counts, volumes and time fields only, no prices and no results).** A survey of 162 sports series with settled markets in the last 4 days found 66 with a median of at least 20,000 contracts traded per market. The binary "<team> wins" series among the largest by volume are the universe below (soccer is excluded because each match has three outcomes, a home win, a draw and an away win, so a "heavy favourite" is rare there). Markets open a long time before the event (NCAA football: 14 days) and carry an `expected_expiration_time` that is known in advance and sits about 4 hours after the start for baseball, so it can anchor a rule without any outcome.

**Universe, fixed now by volume rank and nothing else (12 series):** `KXNFLGAME`, `KXMLBGAME`, `KXWNBAGAME`, `KXATPMATCH`, `KXUFCFIGHT`, `KXNBAGAME`, `KXWTAMATCH`, `KXNCAAFGAME`, `KXNHLGAME`, `KXATPCHALLENGERMATCH`, `KXVALORANTGAME`, `KXWTACHALLENGERMATCH`.

**Data.** `python -m scalper.sp1 fetch`: every settled market of the 12 series that closed in the last 40 days, with the hourly candles (bid, ask, volume) from 14 hours to 10 hours before its `expected_expiration_time`, into a **separate database `data/sports.sqlite`**.

**Rule (fixed now, one parameter set).** Entry candle: the latest hourly candle that ends at or before 12 hours before the market's `expected_expiration_time`. If its YES ask lies in [0.88, 0.97] (valid quote: bid at least 0.01, ask at most 0.99, ask not below bid), buy one YES contract at the ask, hold to settlement, fee 0.07 x p x (1 - p). Only the YES side is bought: in a two-team game the favourite's YES market is the bet and the underdog's NO side is the same bet, so one rule per market counts each game once. A market with no candle at that hour, no usable quote or no result has no observation. No other band, hour or filter.

**One try (the pooled 12 series), no variants.** Per series results are information only.

**Pass bar, fixed (as for WX1 and XM1).** `NOT_ENOUGH_DATA` if fewer than 300 entries or fewer than 10 days. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: mean net above zero; z clustered by day at least 2.1; both halves of the days positive; positive with fees x 1.2; and above the 95th percentile of a fair-market placebo (200 repetitions with the same entries, prices and fees, outcomes drawn at the entry's price). Anything else is `FALSIFIED`. The power rule: the run prints the minimum detectable edge; if it is above 1c, a `FALSIFIED` is reported as "not shown at this sample size".

**Numeric prediction, before the run.** Roughly 15% to 25% of markets qualify, so the entries number in the low thousands and are nearly independent. The mean net sits between -0.5c and +1.0c with a loss rate within a point of break-even; the minimum detectable edge is about 1c. **Expected verdict: `FALSIFIED`.** A mean above +2c is an audit trigger first (check the entry candle ends at least 12 hours before the expected expiration and that no entry uses a candle after the event started).

**Information, not part of the verdict.** Per series: entries, loss rate against the break-even loss rate at the mean price paid, net by half; the loss rate by price decile within the band; the share of entries by sport.

**Count.** One variant: the running total in this file was 4,597 after XM1's registration, so it is 4,598 with SP1.

**Limits.** An hourly candle 12 hours before the expected end is a stale price for sports that start much later than that (tennis, in particular, has no fixed schedule, so for some matches the candle is a day-early quote); that is a property of the rule, fixed here, not tuned. Whether a favourite at 88c to 97c half a day before the event is the same bet as one in the last minutes of L1's 15 minute market is exactly what the test asks. Candle asks are quotes, not fills.

## Result: SP1, heavy favourites in sports game-winner markets (run once on 2026-10-13)

9,118 settled markets in 12 series over 40 days; 535 qualified (YES ask 0.88 to 0.97 on the hourly candle ending at or before 12 hours before the expected end), on 40 days.

SP1: mean price paid 0.923, loss rate 11.40% (break-even about 7.2%), **net -4.19c per contract, z -2.79**, halves -3.84c / -4.67c, fees x1.2 -4.29c, placebo 95th percentile -4.94c. **FALSIFIED.** Minimum detectable edge +3.15c, so a small positive edge would not have been seen; but this is not a "not shown" case, it is the wrong sign with z -2.79 and both halves negative. The prediction (between -0.5c and +1.0c) was wrong on the low side.

Information, not tries. Per series: Challenger tennis `KXATPCHALLENGERMATCH` 209 entries, loss rate 17.7%, **-10.40c** (the bulk of the damage); NCAA football 157 entries, -0.46c; women's Challenger tennis +3.44c on 78; WTA +3.10c on 40; every other series under 25 entries. By price band: the loss rate does not fall as the price rises (11.7%, 14.0%, 14.7%, 11.9%, 5.5% over five bands), the opposite of a calibrated favourite. Why this matters: an hourly candle 12 hours early is a quote on a market that may be thin and stale, and we buy at its ask. In the thin tennis series the "favourite" at that time often changes before the match. A reading of this, not tested: the 88c to 97c favourite 12 hours early is **overpriced**, not underpriced, so favourite-longshot bias does not run in the direction that would pay a buyer of favourites here. The mirror (selling favourites / buying the longshot) is NOT registered, because choosing it after seeing this result would be the selection the deflation floor exists to stop.

**Count: 4,598** (SP1 was the one try).

## Result: E3, L1 unchanged on seven more 15 minute series (run once on 2026-10-13)

19,139 markets, 40 days (FX 16 to 17 days). Rule as registered.

| Series | n | net / contract | z | halves | fees x1.2 | verdict |
|---|---|---|---|---|---|---|
| XRP | 1,262 | **+1.43c** | +2.37 | +1.18 / +1.71 | +1.34 | NOT_YET_FALSIFIED |
| Dogecoin | 1,206 | **+1.54c** | +2.97 | +1.48 / +1.61 | +1.45 | NOT_YET_FALSIFIED |
| HYPE | 1,245 | -0.18c | -0.24 | | | FALSIFIED |
| BNB | 1,083 | -0.84c | -1.16 | | | FALSIFIED |
| EUR/USD | 340 | -0.56c | -0.50 | | | FALSIFIED |
| GBP/USD | 343 | -2.72c | -1.93 | | | FALSIFIED |
| USD/JPY | 345 | -4.29c | -2.18 | | | FALSIFIED |

Pooled (information): all seven -0.01c (z -0.03); four crypto +0.53c (z +1.30); three FX -2.53c (z -3.07, **FX is losing with a significant sign**).

The prediction said XRP and DOGE would be about +0.5c and fail on z; they did not, so that prediction was wrong for two of the seven. DOGE's +1.54c is over the registered +1.5c audit trigger, so the audit came first.

**Audit (information, no new parameter, nothing selected).**
- The quotes are real: median entry-minute volume 2,614 contracts (XRP) and 1,219 (DOGE), median spread 0.4c and 0.7c. The entry candle is the same one L1 uses (ends 360 s before the close), and the code is the same `hold_rule`.
- **The gain is concentrated.** The five best days of 41 carry 56% (XRP) and 51% (DOGE) of the total net. Without those five days: XRP +0.72c (z +1.22), DOGE +0.86c (z +1.75). Neither would pass the bar without its best five days.
- **It is not independent of Bitcoin.** In the windows where Bitcoin's L1 entry also existed and lost (32 for XRP's overlap, 26 for DOGE's), XRP also lost 13 and DOGE 10: about 40%, against a loss rate near 6% when independent. One adverse move in Bitcoin is also an adverse move in them.
- Entries in windows where Bitcoin had no L1 entry did better (+1.91c, +2.12c) than overlapping ones, so the series are not just copies of the Bitcoin result.
- Selection: two of four crypto series pass; the pooled four does not (z +1.30), because HYPE and BNB are negative. With seven tries about 12% of the time one passes by luck alone; two or more passing is under 1% under independence, but crypto alts are far from independent, so the honest reading is "one cluster, one draw, unusually good".

**What this is and is not.** By the registered rule a pass means "watch it forward", never "trade it" and never "change the live bot". Because the live bot already holds the window to 4.5% and sends series in order Bitcoin, gold, Ethereum, adding XRP and DOGE would mostly be starved by that window limit, so even a confirmed edge would not add much until the limit is a deliberate decision. Nothing in the live bot changes.

**Count: 4,598** (E3's seven were already counted).

## Pre-registration: E3F, the forward read of E3's two passes (written 2026-10-13 before any day it covers existed)

**The question.** Does L1 unchanged on XRP and Dogecoin keep its edge on days that did not exist when it was found?

**Why this is one try and not two.** The two series were selected because they passed in E3. Testing them separately would double-count one finding. They are tested **pooled**, as one variant, on **new days only**.

**Data.** `python -m scalper.e3f fetch` into its own `data/e3f.sqlite`. Only markets closing on or after **2026-10-14 00:00 UTC** count (`START_TS`). The fetch window is 60 days, but entries before the start are dropped in code (a test asserts it).

**Rule.** L1 unchanged (candle ending 360 s before the close, favourite's ask 0.88 to 0.97, hold to settlement, taker, same fee model).

**Single read.** `python -m scalper.e3f run` refuses to run before 2026-11-16 (a test asserts it). It is run **once**, on or after that date, and the result is recorded whatever it says. If the data are not yet enough at that date the verdict is `NOT_ENOUGH_DATA` and the read is repeated only after the stated minimum is met, never to chase a pass.

**Pass bar, fixed.** At least 500 pooled entries (about 60 a day, so about 9 days) and at least 10 days; mean net above zero; day clustered z at least 2.1; both halves of the days positive; positive with fees x1.2. Otherwise `FALSIFIED`. No placebo: the rule is L1's and the bar is the one L1's tests used.

**Numeric prediction, before the run.** The E3 figures (+1.4c, +1.5c) were the best two of seven and they rest on five days each; the regression-to-the-mean forecast is a true edge of about +0.5c, a pooled z under 1.5, **FALSIFIED**. Power: with about 33 days the standard error is about 0.5c, so the minimum detectable edge is about 1.0c; a true edge of +0.5c would be missed (that case reads FALSIFIED here and means "not shown"). A pass would still not change the live bot; it would put XRP and DOGE up for a size-capped, separate decision about the window limit.

**Kill criterion.** Any of the bar's conditions failing is FALSIFIED. The live record has nothing to say about it, because the live bot does not trade these series.

**Count.** One variant: 4,599 after E3F.

## Pre-registration: E3B, the backward holdout for E3's two passes (written 2026-10-13 before the older XRP and Dogecoin history was downloaded)

**Why this exists.** E3F needs 33 days to pass before it can be read. But E3 only downloaded the last 40 days, and Kalshi keeps 1 minute candles back about 68 days. The XRP and Dogecoin markets that closed 41 to 68 days ago were **never downloaded, never read and played no part in picking these two series**, so they are an honest holdout that exists today. (Checked 2026-10-13, counts only: both series have 12 settled markets in each 3 hour sample at 45, 55, 62 and 66 days back and none at 70.) The regime may differ (older days, a different market), which is a limit on the test, not a way to tune it.

**Data.** `python -m scalper.e3b fetch` into its own `data/e3b.sqlite`: settled markets of XRP and Dogecoin closing in the last 69 days. Only markets closing **strictly before 2026-09-03 20:00 UTC** (`FLOOR_TS`, the earliest close in E3's data) count; entries on or after it are dropped in code and a test asserts it.

**Rule.** L1 unchanged (candle ending 360 s before the close, favourite's ask 0.88 to 0.97, hold to settlement, taker, same fee model).

**One try, pooled** (the two series together, as in E3F), by the same argument: they were chosen together. Per series results are information.

**Pass bar, fixed.** At least 500 pooled entries and at least 10 days; mean net above zero; day clustered z at least 2.1; both halves of the days positive; positive with fees x1.2. Otherwise `FALSIFIED`; too little data `NOT_ENOUGH_DATA`.

**Numeric prediction, before the run.** Regression to the mean: a true edge of about +0.5c, pooled z under 1.5, **FALSIFIED**. About 25 days at roughly 60 entries a day is about 1,500 entries; the standard error is about 0.6c so the minimum detectable edge is about 1.3c. A pass here AND a pass in E3F would be two independent confirmations (still only "put up for a small separate decision", never a change to the live bot); a pass here alone, or a fail here with a pass in E3F, would each be reported as it is.

**Count.** One variant: 4,599 after E3F, 4,600 after E3B.

## Pre-registration: ARB1, locked arithmetic across a mutually exclusive event (written 2026-10-13 before any snapshot was taken)

**The idea (structural, not directional; overlaps L14 only in spirit).** L14, O9 and O10 looked for a locked or crossed book on ONE market. This is a different object: Kalshi marks events whose outcomes are **mutually exclusive** (at most one market resolves YES; the event list carries `mutually_exclusive`). If you buy the NO side of K legs of such an event, you receive at least K-1 dollars whatever happens (at most one leg is YES, so at most one NO loses). So if the YES bids of the legs sum to more than 1 plus the fees, that is a **riskless profit with no view on any outcome**. It needs no exhaustiveness (a "none of these" outcome only helps: you then receive K). Buying the YES side of every leg is NOT tested, because that needs exhaustiveness and the flag does not say it.

**Counterparty.** Whoever is bidding YES on several mutually exclusive legs without noticing the bids sum past 100%: a stale quoter, or a retail buyer paying a high price on one leg while another leg's bid is also high. The reason it might exist is that many events have dozens of thin legs and no one maintains the sum; the reason it might not is that market makers do exactly this arithmetic.

**Snapshots.** `python -m scalper.arb1 scan` reads every open event with its nested markets (about 6,000 events, 1,650 mutually exclusive, about 18,000 markets, 2 to 3 minutes) and stores, for each mutually exclusive event with at least 2 active legs that have a positive YES bid, the sum of those bids, the per set lock after fees, and the capacity (the smallest YES bid size among the legs, in contracts). **Twelve scans, at least 15 minutes apart**, taken once in a background loop. Then `python -m scalper.arb1 report`, once.

**Lock, fixed now.** For the legs with a positive YES bid: `lock = sum(bids) - 1 - sum(fee(bid_i))`, with `fee(p) = 0.07 p (1-p)` per contract (the unrounded model the rest of this file uses; the per contract fee on a NO at price 1-p equals the one on a YES at p). The cent-rounded fee is reported as information. Top of book only; no walking the book.

**An opportunity** is an event in one scan with `lock >= 0.01` and capacity `>= 10` contracts. **Persistent** means the same event is an opportunity in at least two scans at least 15 minutes apart (a flicker that a real order could not catch is not an opportunity).

**Pass bar, fixed.** `NOT_YET_FALSIFIED` only if ALL hold: at least **3 distinct events** are persistent opportunities; and the sum over distinct persistent events of `lock x min(capacity, 50)` (one fill per event, at most 50 sets, each event valued in the FIRST scan in which it was an opportunity) is at least **$1.00 per day**, the total scaled by 86,400 divided by the seconds between the first and the last scan (a generous scale-up, stated as such). Otherwise `FALSIFIED`. If the number of scans completed is under 8 the verdict is `NOT_ENOUGH_DATA`.

**Numeric prediction, before the run.** Fewer than 3 persistent events, **FALSIFIED**; the handful of locks that appear are on thin legs where the capacity is under 10 or the quote is stale and gone at the next scan. If any lock above 5c at capacity 10 or more is persistent, it is an audit trigger first (a misread flag or an event that is not really exclusive).

**Information, not part of the verdict.** Distribution of `sum(bids)` over events (median, 95th percentile, share over 1.00); the number of events scanned; the largest lock seen and its event; the share of locks that vanish by the next scan.

**What a pass would and would not mean.** No order is placed. Even a pass would only open the question "can this be executed as a basket of simultaneous NO orders at size, with all legs filling" (the leg risk is not zero: a partial fill leaves a directional position), which is a separate, reviewed change and not a change to the live bot.

**Count.** One variant: 4,601 after ARB1.

## Pre-registration: PM1, does Polymarket's 15 minute price carry information Kalshi's does not (written 2026-10-13 before any Polymarket price was downloaded)

**The idea (a second venue's price for the same event).** Polymarket lists "Bitcoin Up or Down" and "Ethereum Up or Down" for every 15 minute window (slug `btc-updown-15m-<window start>`, resolved by a Chainlink TWAP against the price at the start of the window). Kalshi's `KXBTC15M` and `KXETH15M` are the same bet with a slightly different reference index. If the two venues' quotes carry partly independent noise, averaging them predicts the outcome better than Kalshi's alone, and that would be a filter for L1 (skip an entry the other venue disagrees with). The same idea as XM1, with an independent venue instead of an hourly ladder.

**Counterparty.** Slow or thin quoters on either venue. The prior is against it: Polymarket's windows are thin (the check on 2026-10-13: the window starting 2026-10-13 00:00 UTC traded $34,000 on Bitcoin and $6,000 on Ethereum, against millions of Kalshi contracts), and its history shows quotes parked at 0.525 for minutes at a time. A stale quote adds noise, not information.

**Data.** `python -m scalper.pm1 fetch` into its own `data/pm1.sqlite`: for every `KXBTC15M` and `KXETH15M` market in `book.sqlite` (3,792 each, 40 days), the Polymarket event with slug `<btc|eth>-updown-15m-<close minus 900>` (batched, public read-only API, no key) and the "Up" token's price history (1 minute fidelity) from 15 minutes before to 6 minutes before the close. No order is ever sent.

**Observation.** One per Kalshi window with a valid quote (`analyze.valid_quote`) at the candle ending 360 s before the close AND a Polymarket history point at or before that second and no more than 180 s earlier. `p_k` = mid of Kalshi's YES quote; `p_pm` = the Polymarket "Up" price of that point; `y` = 1 if Kalshi's result is YES. A window with no Polymarket event, no recent point or no Kalshi quote has no observation.

**Test, one per series (two tries: Bitcoin, Ethereum), no variants.** Paired difference per window `d = (p_k - y)^2 - (0.5 p_k + 0.5 p_pm - y)^2` (positive when the 50/50 blend predicts better than Kalshi alone; the weight 0.5 is fixed now, not fitted). `NOT_ENOUGH_DATA` if fewer than 500 observations or 10 days. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: mean `d` above zero; day clustered z at least 2.1; both halves of the days positive. Anything else `FALSIFIED`.

**Numeric prediction, before the run.** The blend is worse than Kalshi alone (mean `d` below zero) on both series; **FALSIFIED**. If mean `d` is above +0.002 (the blend improving the Brier score by 0.2 of a point) it is an audit trigger first (a lookahead in the Polymarket timestamps is the first suspect).

**Information, not part of the verdict.** Brier of Kalshi alone, of Polymarket alone, and of the blend; the median absolute gap `|p_pm - p_k|`; the share of windows with a usable Polymarket point; the L1 entries (favourite ask 0.88 to 0.97 at that candle) split by whether Polymarket's price for the same side was 5 points or more below Kalshi's mid ("disagrees") or not: the number of entries and the loss rate in each. That split is NOT a test and gates nothing; if the blend passes, a filter on L1 would need its own registration.

**Count.** Two variants: 4,603 after PM1.

**Limits.** The two venues do not settle on the same index, so the outcome (taken from Kalshi's result) is the one Kalshi settles; a tie or a close call can differ. Polymarket's price is a midpoint or last trade, not a quote we could trade at; this is a test of information, not of an executable strategy.

## Pre-registration: FLB1, favourites in long-dated, non-sports, non-price markets (written 2026-10-13 before any such market was downloaded)

**Why.** Everything that produced L1's +0.4c lives on Bitcoin, gold and a few look-alikes that move together, so thousands of entries are a few hundred independent events (README, the "pooled L1 evidence" note). SP1 asked the same question on 535 nearly independent sports events and got -4.2c. This asks it on the rest of Kalshi: elections, politics, entertainment, "mentions", economics, science, companies, health. These are many truly independent events with long lives, so the same rule, at a horizon of days instead of minutes, is a real out-of-sample test of "do favourites beat their price".

**Counterparty.** The same as L1's and no new one is claimed: whoever holds the longshot side and sells it too cheaply to the favourite buyer. (It is still tested because the universe is different; a pass or a fail here says whether L1's pattern is a property of 15 minute crypto or of prediction markets in general.)

**Universe, fixed now.** Events from the public events list (`status=settled`, `with_nested_markets`) with at least one market closing in the last 60 days; the event `category` is NOT one of `Sports`, `Financials`, `Crypto` (sports is SP1, and Financials and Crypto are price-driven look-alikes of L1). Every market of such an event with result YES or NO and a lifetime (open to close) of at least 3 days. Selected on category and lifetime only, never on price or result.

**Rule (three leads, one parameter set each).** At the hourly candle that ENDS at the latest hour boundary at or before `close - lead`, with lead 24 h, 72 h or 168 h: buy the favourite when its ask is 0.88 to 0.97 (either side, the L1 band) and the quote is valid (`analyze.valid_quote`), hold to settlement, taker at the ask, the same fee model as `lstrats.net`. A market with no candle at that hour, no quote in the band or no result has no observation.

**Three tries (24 h, 72 h, 168 h).** They share markets, so they are not independent; they are counted as three anyway.

**Pass bar, fixed, per lead.** `NOT_ENOUGH_DATA` if fewer than 300 entries or fewer than 60 distinct events. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: mean net above zero; z clustered by EVENT (not by day: the strikes or candidates of one event are one bet) at least 2.1; both halves of the markets (split by close time at the median) positive; positive with fees x1.2; and above the 95th percentile of 200 placebo draws (the favourite's side drawn at random with the market's own mid as the probability). Anything else `FALSIFIED`.

**Numeric prediction, before the run.** Mean net between -2.0c and +1.0c at every lead, z under 1.5, **FALSIFIED** at all three. If any lead shows a mean above +2c it is an audit trigger first (a stale quote in a thin market that the settlement result happens to confirm is the first suspect). The minimum detectable edge is reported; with about a thousand entries clustered by event it is likely near 2c, so a FALSIFIED here may mean "not shown".

**Information, not part of the verdict.** Entries and mean net per category, per price decile within the band, the loss rate against the break-even loss rate at the mean price paid, and the median volume of the entry candle.

**Count.** Three variants: 4,606 after FLB1.

**Limits.** An hourly candle days before the close in a thin market is a stale quote (its ask may be what one person once offered); we buy at that ask, which is exactly what the rule would do and not an error of the test, but a real order would find the book empty more often than the candle suggests. Fills are not modelled.

## Result: E3B, the backward holdout for XRP and Dogecoin (run once on 2026-10-13)

13,062 markets downloaded (69 days); the holdout is the 29 days before E3's data began (closes before 2026-09-03 20:00 UTC).

E3B pooled XRP + Dogecoin: **n=1,917 on 29 days, net +1.76c per contract, z +3.97**, halves +0.81c / +2.68c, fees x1.2 +1.67c, minimum detectable edge +0.93c -> **NOT_YET_FALSIFIED.** Per series (information): XRP n=998 +1.62c (z +2.43), Dogecoin n=919 +1.92c (z +2.47). **My prediction (FALSIFIED, a true edge near +0.5c) was wrong.** The two series that passed E3 on 41 days also pass on 29 days nobody had looked at.

**Audit (information, no new parameter).**
- Loss rate 4.9% against a break-even of about 7.2% at the mean price paid 0.929; median entry-minute volume 1,167 contracts.
- The weekly series is positive every week (+0.23c, +2.43c, +1.59c, +2.29c, +2.36c, +3.65c), so it is not one lucky stretch.
- The gain is still concentrated in the best days: the five best of 29 carry 50% of the pooled total. **Without those five days the pooled result is +1.07c (z +2.63)**, which still clears 2.1; XRP alone without its best five is +0.52c (z +0.85) and Dogecoin alone +0.85c (z +1.10).
- **It sits in the cheaper favourites.** Entries priced under 93c: +3.72c on 901; at 93c and over: +0.03c on 1,016. In E3 the same split was +2.33c / +0.50c for XRP and +1.52c / +1.57c for Dogecoin, so that part is not stable. Not a rule, not tested, not to be tuned on.

**What this does and does not say.** This is the first mechanism in this file that was positive on data it was found on and then positive again on a holdout it never saw. It is still the same mechanism as L1 (the favourite buyer against the longshot buyer) in series where the quoter is a thinner, slower market maker (median spread 0.4c and 0.7c on XRP and Dogecoin). The correlation with Bitcoin found in the E3 audit stands (about 40% of the losses coincide), so these two are one bet on "crypto moves late" more than two. E3F (new days, one read on or after 2026-11-16) remains the forward test. **Nothing about the live bot changes** on this: adding a series is a deliberate code edit and review (`L1_SERIES`), and the 4.5% window limit means XRP and Dogecoin would be starved by the series ahead of them unless the order of the list is also a decision.

**Count: 4,606** (E3B was the one try already counted).

## Pre-registration: L1B, L1 on Bitcoin, Ethereum and gold, on the older days the book never held (written 2026-10-13 before those markets were downloaded)

**The question.** L1's rule (favourite's ask 0.88 to 0.97, 360 s before the close) was chosen on the last 40 days of Bitcoin, Ethereum and gold, and everything about its live edge (+0.41c, z about 1.5) is measured on those same days or on live orders. The 29 days before them were never downloaded for these three series. They are the first real holdout the live bot's own rule has had.

**Data.** `python -m scalper.l1b fetch` into its own `data/l1b.sqlite`: settled `KXBTC15M`, `KXETH15M`, `KXGOLD15M` markets of the last 69 days with 1 minute candles. Only markets closing **strictly before 2026-09-02 19:30 UTC** (`FLOOR_TS`, the earliest close in `book.sqlite`) count; a test asserts it.

**Rule.** L1 unchanged (`lstrats.L1`: candle ending 360 s before the close, favourite's ask 0.88 to 0.97, hold to settlement, taker, the same fee model).

**Three tries (Bitcoin, Ethereum, gold), no variants.** The pooled result is information, not a try.

**Pass bar, fixed (the same as E3).** `altseries.summarize`: at least 300 entries and 5 days; day clustered z of net per contract at least 2.1; mean above zero; both halves of the days positive; positive with fees x1.2. Otherwise `FALSIFIED`.

**Numeric prediction, before the run.** Bitcoin and Ethereum: about +0.3c to +0.5c, z between 0 and 1.5, **FALSIFIED** on z. Gold: its measured +1.47c (z +2.80) on the book window was the only series that cleared the bar alone, and it is the likeliest to regress; predicted +0.5c, **FALSIFIED**. Pooled three: between 0.0c and +0.8c.

**What each outcome would mean.** A pass on a series is "the live bot's edge on that series also holds on 29 older days", which is evidence for keeping it, not for sizing it up. A fail with a mean at or below 0 on a series is evidence against that series being worth its slot, to be put to the owner (the bot is not changed from here). Power: with roughly 29 days of entries the standard error is about 0.7c per series, so a true edge of +0.4c cannot reach z 2.1; most of the value is in the sign of the pooled mean and its size relative to the book window.

**Count.** Three variants: 4,609 after L1B.

## Result: PM1, Polymarket's 15 minute price against Kalshi's (run once on 2026-10-13)

7,584 Kalshi windows with a quote, 7,582 with a Polymarket point within 180 s before the entry second.

| | Observations | Brier gain of the 50/50 blend over Kalshi alone | z | Halves | Verdict |
|---|---|---|---|---|---|
| Bitcoin | 3,791 | **-0.0029** | -3.84 | -0.0033 / -0.0026 | FALSIFIED |
| Ethereum | 3,791 | **-0.0022** | -2.51 | -0.0025 / -0.0019 | FALSIFIED |

As predicted: Polymarket's price is the worse predictor (Brier Bitcoin 0.1523 against Kalshi's 0.1406; Ethereum 0.1432 against 0.1328; median gap between the two venues 5.0c), so averaging it in makes things worse. No audit trigger (the gain was negative).

**Information only (the registered split, not a test).** L1-style entries split by whether Polymarket's price for the side bought was 5 points or more below Kalshi's mid:
- Bitcoin: Polymarket disagrees 393 entries, loss rate 9.4%, **-1.72c**; agrees 728 entries, loss rate 4.9%, **+1.52c**.
- Ethereum: disagrees 437, loss rate 7.8%, -0.48c; agrees 703, loss rate 6.1%, +0.35c.

That was the pre-registered information split and it was looked at once, on the same 40 days that L1 itself was tuned on. A loss-rate gap of 4.5 points with 393 and 728 entries is about 2.6 standard errors on Bitcoin and 1.0 on Ethereum; it is a candidate, not a finding, because a result seen after a failed test is the textbook case of picking the one thing that looks good. It is tested separately on days it has not seen (PM2, below), which is the registered next stage for a filter.

**Count: 4,606** (PM1's two tries were counted when registered).

## Pre-registration: PM2, skip an L1 entry when Polymarket disagrees (written 2026-10-13 before any Polymarket price for these days was downloaded)

**The question.** PM1's information split suggested that L1 entries where Polymarket's price for the side bought sits 5 or more points under Kalshi's mid lose more often. Does that hold on days the split was never computed on?

**Counterparty.** Kalshi's own favourite buyer at those moments: when the other venue prices the same event 5 points less likely, Kalshi's 88c to 97c ask is more often too high. A thin market's stale quote would work against this idea, not for it (PM1 showed Polymarket is the worse predictor on average), which is why the prior is against it.

**Data.** The Bitcoin and Ethereum windows closing **strictly before 2026-09-02 19:30 UTC** in `data/l1b.sqlite` (the L1B download, 29 days nobody has looked at), and for each the Polymarket "Up" price history fetched the PM1 way into its own `data/pm2.sqlite`. No day in this window was in PM1.

**Rule (fixed now, no variants).** L1 entries as defined (favourite's ask 0.88 to 0.97 at the candle ending 360 s before the close) with a Polymarket point at or before the entry second and no more than 180 s old. `skip` = the Polymarket price of the side bought is at least **0.05** below Kalshi's mid of that side. Bitcoin and Ethereum pooled, **one try**.

**Pass bar, fixed.** `NOT_ENOUGH_DATA` if fewer than 100 skipped entries. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: the skipped entries' mean net is below zero; its day clustered z is at most -2.1; the skipped mean is negative in both halves of the days; the kept entries' mean is above the all-entries mean (skipping would have helped); and the improvement (kept mean minus all-entries mean) exceeds the 95th percentile of 200 permutation draws in which the same number of entries per series are flagged at random. Anything else `FALSIFIED`.

**Numeric prediction, before the run.** The split does not replicate: the skipped entries' mean net between -1c and +1c, z above -1.5, **FALSIFIED**. Power: about 800 entries over 29 days with roughly 280 skipped; the standard error of the skipped mean is about 1.5c, so a true gap as large as the one seen in sample (about 3c) would be seen only about half the time. A FALSIFIED here can therefore mean "not shown".

**What a pass would and would not mean.** It would put a Polymarket-disagreement filter up for a forward read, never into the live bot; the bot's server cannot be changed from here and its Polymarket read would be a new external dependency the owner has not asked for.

**Information, not part of the verdict.** Skipped and kept counts, loss rates and mean net by series; the loss rate in the skipped group against the kept group.

**Count.** One variant: 4,610 after PM2 (4,609 after L1B).

## Result: L1B, the live rule on the 28 days before the book (run once on 2026-10-13)

7,213 markets downloaded (the days before 2026-09-02 19:30 UTC; 14 with no candles skipped). L1 unchanged.

| Series | Entries | Days | Net per contract | z | Halves | Fees x1.2 | Verdict |
|---|---|---|---|---|---|---|---|
| Bitcoin | 838 | 28 | **+0.55c** | +0.88 | +1.24 / -0.11 | +0.46c | FALSIFIED (on z) |
| Ethereum | 901 | 28 | **+1.32c** | +2.24 | +1.67 / +1.02 | +1.22c | NOT_YET_FALSIFIED |
| Gold | 620 | 26 | **+2.20c** | +2.73 | +1.63 / +2.69 | +2.11c | NOT_YET_FALSIFIED |
| pooled (information, not a try) | 2,359 | 28 | **+1.28c** | **+3.20** | +1.50 / +1.08 | +1.18c | |

**My prediction was wrong for two of the three** (I predicted +0.3c to +0.5c and FALSIFIED for all): Ethereum and gold cleared the bar on days the rule was never fitted to. Bitcoin, the most liquid and the largest series, is the weakest and the only one that did not. Win rate 93.6% / 94.6% / 95.5% against 92.5% / 92.8% / 92.8% paid.

**Information, not a try: both windows together (68 days, 5,397 entries).** Mean net **+0.79c per contract, day clustered z +2.52**. By series over the 68 days: Bitcoin +0.45c (z +0.81, 1,959 entries), Ethereum +0.60c (z +1.26, 2,041), **gold +1.54c (z +2.94, 1,397)**. By ISO week the pooled mean is +2.74, +1.79, -0.02, +2.04, +0.23, +1.02, +0.35, +1.99, -0.92, +0.24 cents (the last week is partial and was not trusted), so the sign is positive in 8 of 10 weeks and the size is noisy; the weeks are not getting better.

**What this does and does not say.**
- The live bot's rule has a positive edge on 28 days it was never fitted to, which is the first time that has been checked. The earlier thin +0.41c (z about 1.5) was probably an underestimate of a real edge of somewhere around +0.8c, or a lucky older window; two windows 68 days apart are not enough to tell which.
- It is still before the live bot's real costs: the fill rate (about 58%), partial fills, and the 25c exit the owner chose (neutral on the 40 day sample).
- It does not say the edge is stable. The older window is stronger than the recent one in Bitcoin (+0.55c against about +0.3c) and gold (+2.20c against +1.47c), and 15 minute crypto and gold markets could be more efficiently quoted now than in August.
- Every number here is gross of nothing but Kalshi's taker fee model; it is a backtest on candle asks.

**Count: 4,609** (L1B's three tries were counted when registered). The pooled rows are information.

## GROWTH at a higher edge (information, 2026-10-13)

`python -m scalper.growth` prints, for the live sizing and stop rules with $500 and $500 a month: at +0.41c a median of about $8,400 after 360 days on $6,000 paid in; **at +1.00c a median of about $11,600 (5th percentile $9,960, 95th $13,540), with no path below what was paid in**; at 0.00c about $6,100; at -0.50c about $3,900 and 98% of paths below paid-in. The 68 day mean of +0.79c sits between the +0.41c and +1.00c rows. These are paths drawn from the 40 day entry history with the live sizing, not forecasts, and they leave out the profit add-on pool and the weekly size review.

**Information, 2026-10-13 (not a try, nothing registered on it): the "cheaper favourites carry the edge" reading does not hold up on the live series.** E3B's XRP and Dogecoin entries under 93c earned +3.7c against about 0 at 93c and over. On Bitcoin, Ethereum and gold the split reverses between windows: the older 28 days favour entries under 93c (+1.82c on 1,192 against +0.72c on 1,167) and the 40 day book window favours 93c and over (-0.09c on 1,561 against +0.95c on 1,477); over all 68 days it is +0.74c (z +1.42) under 93c and +0.84c (z +2.20) at 93c and over. By price bucket over the 68 days: 88c to 90c -0.73c (11.6% losses), 90c to 92c +1.08c, 92c to 94c +1.88c, 94c to 96c +0.59c, 96c to 97c +0.61c. A pattern that flips sign between two windows is noise until shown otherwise, so no band rule is proposed.

## Pre-registration: FWD1, the live series on days that do not exist yet (written 2026-10-13 before any such day)

**The question.** Do Bitcoin, Ethereum and gold under L1's unchanged rule keep a positive edge on days after 2026-10-13? E3F reads XRP and Dogecoin forward; this reads the three series the bot actually trades, on public candles, independent of the bot's own fills.

**Data.** `python -m scalper.fwd1 fetch` into its own `data/fwd1.sqlite` (the last N days, N chosen to cover 2026-10-14). Only markets closing on or after **2026-10-14 00:00 UTC** count; a test asserts it.

**Rule.** L1 unchanged. **One try:** the three series pooled.

**Single read.** `python -m scalper.fwd1 run` refuses before 2026-11-16 and is run ONCE, on or after that date, together with E3F's read.

**Pass bar, fixed (E3F's, imported).** At least 500 entries, 10 days; mean net above zero; day clustered z at least 2.1; both halves of the days positive; positive with fees x1.2. Otherwise `FALSIFIED`.

**Numeric prediction, before the run.** A mean between +0.3c and +1.0c; with about 85 entries a day over 33 days the standard error is about 0.45c, so a true +0.8c would reach z 2.1 only about half the time. I expect z between 1 and 2.5. **FALSIFIED** is the more likely verdict and would mean "not shown", not "gone". Information: per series, per ISO week.

**Count.** One variant: 4,610 -> 4,611 after FWD1 (PM2 was already counted).

## Pre-registration: E5, L1 unchanged on the other commodities and two more coins (written 2026-10-13 before any of these markets was downloaded and before any result)

**Why.** Gold is where L1 is strongest (+1.54c, z +2.94 over 68 days, the only live series that clears the bar alone), and every earlier universe check looked only at crypto and FX. Kalshi lists 15 minute markets on silver, crude oil, natural gas, copper, platinum and palladium that were never tested. Checked 2026-10-13, counts and volumes only, no result (median contracts traded per settled market, over samples 20 to 60 days back): silver 26,000 to 54,000; crude oil (WTI) 23,000 to 71,000; natural gas 10,000 to 17,000; copper 13,000 to 22,000; platinum 7,800 and palladium 9,200 (both exist for about 20 days only); Zcash 4,700 to 29,000; NEAR 3,900 to 29,000. For scale, XRP is 74,000 and gold 458,000. Left out: the stock index, Treasury yield and several coin series that have no settled markets in the last 60 days; the "coin race" and "crypto comparison" series, which are not up or down markets.

**Counterparty.** The same as L1's and no new one is claimed. Commodity 15 minute markets are quoted by the same kind of maker as gold's.

**Data.** `python -m scalper.e5 fetch` into its own `data/alts3.sqlite`: every settled market of the eight series in the last 69 days with 1 minute candles. Nothing else is touched.

**Rule (fixed now, identical to L1).** One observation per market from the candle that ENDS exactly 360 s before the close; buy the favourite when its ask is 0.88 to 0.97 (either side), hold to settlement, taker at the ask, the same fee model as `lstrats.net`. No filter, no other band or minute.

**Design, fixed now: a discovery window and a holdout, decided before looking.** Discovery = markets closing on or after **2026-09-03 20:00 UTC** (the last 40 days, the same cut as E3). Holdout = markets closing before it. Stage 1: each series is tested on discovery with the common bar. Stage 2: only a series that passes Stage 1 is read on the holdout, with the same bar. A series is `NOT_YET_FALSIFIED` only if it passes both stages; a series that passes Stage 1 but has fewer than 300 holdout entries is `NOT_ENOUGH_DATA` (platinum and palladium may be). The holdout is not a try; it is the confirmation that E3 only had after the fact.

**Eight tries (silver, WTI, natural gas, copper, platinum, palladium, Zcash, NEAR), no variants.** Also reported as information, not tries: the six commodities pooled and the two coins pooled, on each window.

**Pass bar, fixed (the same as every earlier test).** At least 300 observations; at least 5 days; day clustered z of net per contract at least 2.1; mean net above zero; both halves of the days positive; positive with fees x1.2. With eight tries about 15% of the time one passes Stage 1 by luck alone, which is why Stage 2 exists.

**Numeric prediction, before the run.** Commodities: between +0.3c and +1.0c, z between 0 and 2; Zcash and NEAR: about +0.5c, **most or all FALSIFIED at Stage 1**. If a series shows a mean above +1.5c at Stage 1 it is an audit trigger first (a stale quote that the result happens to confirm in a thin series).

**Information, not part of the verdict.** Per series and window: entries per day, win rate against the mean price paid, median entry-minute volume, median spread at the entry candle.

**Count.** Eight variants: the running total in this file was 4,611 after FWD1, so it is 4,619 with these eight.

**Limits.** Candle asks are quotes, not our fills; thin books fill less at size. Platinum and palladium have about 20 days. The live bot would need a code edit for any of these (`L1_SERIES` is a hard list) and the 4.5% window limit would still apply; nothing here changes the bot.

## Information: what adding XRP and Dogecoin at the END of L1's list would do to the window limit (2026-10-13, ORDER1, not a try, nothing registered on it)

The live bot holds the money put into one 15 minute window to 4.5% of the sizing base, and each entry costs about 2%, so at most **two entries fit in a window** and the series are taken in list order (Bitcoin, gold, Ethereum). On the 68 days of public candles, with every window's L1 entries on Bitcoin, gold, Ethereum, XRP and Dogecoin lined up: a window has 1 entry in 1,827 cases, 2 in 1,376, 3 in 960, 4 in 467 and 5 in 91 (4,721 windows with any entry). With one contract per entry and no fill model:

| List (at most two entries a window) | Entries | Net per entry | Mean day | Day sd | Worst day | 5th percentile day | Windows where both entries lose |
|---|---|---|---|---|---|---|---|
| Bitcoin, gold, Ethereum (live) | 5,154 | +0.87c | +0.65 | 1.86 | -4.89 | -2.73 | 28 |
| ... then XRP, Dogecoin at the end | 7,615 | +1.18c | +1.30 | 2.24 | -4.32 | -2.64 | 52 |
| XRP, Dogecoin first (in sample) | 7,615 | +1.39c | | | | | |
| gold, XRP, Dogecoin, Ethereum, Bitcoin (68 day edge order, in sample) | 7,615 | +1.41c | | | | | |

**Reading it.** Appending the two series costs the existing trades nothing, because they only fill the second slot in the 3,000-odd windows where the live three left room, and it doubles the expected net per day in sample, with a similar worst day (the window limit is unchanged). Day-to-day volatility rises by about 20% and double-loss windows go from 28 to 52 because XRP and Dogecoin lose with Bitcoin about 40% of the time. The orderings that put XRP and Dogecoin first or rank by 68 day edge are fitted to this sample and are not recommendations.

**What it does not say.** The XRP/Dogecoin edge is the part that is not yet forward-confirmed (E3F is due on or after 2026-11-16) and they were found on 41 days and held on 29; their fill rates on a thinner book are unmeasured (median entry-minute volume about 1,200 contracts); each is a new series for the 5% loss stop and the sizing review to see. Not a change to the live bot; written as a proposal in `docs/PROPOSALS.md`.

## Result: E4, L1 unchanged on the hourly ladders (run once on 2026-10-13)

61,743 ladder markets with a usable candle (S&P `KXINXU` 40 days, Bitcoin `KXBTCD` and Ethereum `KXETHD` 14 days). Rule as registered.

| Series | Entries | Hours with an entry | Net per contract | z (by day) | z (by hour) | Halves | Minimum detectable edge | Verdict |
|---|---|---|---|---|---|---|---|---|
| S&P 500 hourly | 250 on 27 days | 162 | **-2.78c** | -1.78 | -1.58 | -2.21 / -3.44 | +3.28c | FALSIFIED |
| Bitcoin hourly | 348 on 15 days | 235 | +0.96c | +0.96 | +0.83 | +2.29 / -0.56 | +2.10c | FALSIFIED (NOT SHOWN) |
| Ethereum hourly | 280 on 15 days | 217 | +0.64c | +0.64 | +0.49 | +0.76 / +0.51 | +2.12c | FALSIFIED (NOT SHOWN) |

One entry per hour (information): S&P -3.65c (z -2.37), Bitcoin +0.40c, Ethereum +0.84c. The prediction was that nothing would be shown; it was right, and the S&P ladder is negative with the wrong sign (the quoted favourite at the 88c to 97c band six minutes before the hourly close lost 8.8% of the time against 6.4% paid, worst single hour -1.78 dollars over 3 entries). The Bitcoin and Ethereum ladders are positive and small like their 15 minute versions, but the sample (14 days, 1.3 to 1.5 entries per hour) cannot tell +0.6c from zero. The entries per hour shows why a ladder is a worse place for this rule: every qualifying strike in an hour hinges on the same price move, so one bad last six minutes loses several at once. **Not a way to add volume.** Count unchanged (E4's three tries were counted when registered).

## Pre-registration: VOL1, skip Bitcoin and Ethereum entries made in a busy minute (written 2026-10-13 before any day it covers existed)

**What was seen first, disclosed.** On the 68 days of candles, splitting each series' L1 entries into terciles of the entry minute's traded volume (information only): Bitcoin +1.15c / +0.57c / **-0.36c** (low, middle, high) and Ethereum +1.66c / +0.48c / **-0.34c**; gold, XRP and Dogecoin show no such pattern (non-monotone, all positive). For Bitcoin and Ethereum pooled, entries above the top tercile's lower edge (Bitcoin 132,766 contracts, Ethereum 5,751) earned -0.91c on 391 entries in the older 28 days and -0.11c on 942 in the 40 day book window, against +1.49c on 1,348 and +0.43c on 1,319 for the rest: the same sign in both windows, but the tercile edges were taken from the very data they are shown on, so this is a candidate and not a result.

**The idea.** A busy entry minute means the price is moving and informed traders are in the book, so a 90c favourite is more likely to be one that is about to be hit. The counterparty story is L1's again (the longshot holder) with a time-varying twist: the favourite is least safe when the book is busiest. This is a filter on L1, not a new strategy.

**Rule (fixed now).** On the days after 2026-10-13 (the same forward data as FWD1, read from `data/fwd1.sqlite` in the same single read): L1 entries on Bitcoin and Ethereum are `skipped` if the entry candle's traded volume is strictly above **132,766** (Bitcoin) or **5,751** (Ethereum) contracts; otherwise `kept`. The thresholds are the numbers above and are not refitted. **One try**, Bitcoin and Ethereum pooled.

**Pass bar, fixed.** `NOT_ENOUGH_DATA` if fewer than 150 skipped entries or fewer than 10 days. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: the skipped mean net is below zero; it is below the kept mean in the whole sample and in both halves of the days; and the improvement (kept mean minus the all-entries mean) exceeds the 95th percentile of 200 permutation draws in which the same number of entries per series are skipped at random.

**Numeric prediction, before the run.** Regression to the mean: the skipped group is about -0.1c to +0.3c, the kept group about +0.5c; the gap is under 0.7c and the permutation test does not clear. **FALSIFIED** more likely than not. Power: about 60 Bitcoin and Ethereum entries a day, a third of them skipped, so about 650 skipped over 33 days; the gap seen in sample (about 1.3c) would show about half the time.

**What a pass would and would not mean.** A pass would put "skip a busy minute" up for a decision, never into the live bot from here (the server would need the entry minute's volume at order time, which the market list may not carry). The same single read as E3F and FWD1, on or after 2026-11-16.

**Count.** One variant: 4,620 after VOL1.

## Result: PM2, skip an L1 entry when Polymarket disagrees, on the 28 older days (run once on 2026-10-13)

5,269 Kalshi windows with a quote, 1,738 L1 entries (Bitcoin and Ethereum) with a Polymarket point within 180 s, on 28 days.

PM2: skipped 605 of 1,738 entries (34.8%). **Skipped entries' mean net -1.69c (day clustered z -1.34); halves +1.03c / -3.95c. Kept entries +2.36c against +0.95c for all entries; improvement +1.41c per entry, permutation 95th percentile +0.68c. -> FALSIFIED** (the bar requires z of the skipped mean at most -2.1 and a negative skipped mean in both halves; neither holds).

Information (not part of the verdict): Bitcoin skipped 296 entries, loss rate **9.8%**, -2.03c, against kept 541 entries, loss rate **4.6%**, +1.96c; Ethereum skipped 309, loss rate **8.7%**, -1.38c, against kept 592, loss rate **3.7%**, +2.72c. In the 40 day split that suggested it, the loss-rate gaps were 4.5 points (Bitcoin) and 1.7 points (Ethereum); on the older 28 days they are 5.2 and 5.0 points, the same direction and not smaller.

**Honest reading.** The registered verdict is FALSIFIED and stays FALSIFIED. Two things in the numbers are worth keeping apart from that verdict. (1) The z in the bar tests the skipped mean against ZERO, a harsh statistic for a filter whose worth is the gap to the kept entries; the first half of the older window had the skipped group at +1.03c, the second at -3.95c, so the sign is not stable within the window. (2) The improvement per entry, +1.41c, is twice the 95th percentile of what skipping the same number of entries at random gives (+0.68c): the permutation test, which asks the question the filter is for, is cleared by a wide margin. That is a candidate with two windows of the same sign, not a pass; and the registered bar was not met. It is tested on days neither window saw as PM3, below, with a bar that asks the filter's own question and is written down before those days exist. The Polymarket price itself still does not predict outcomes better than Kalshi's (PM1), so what is being claimed is narrower: "when the other venue's price for the same side is 5 points lower, an L1 entry is riskier than usual".

**Count: 4,610** (PM2 was one try, already counted).

## Pre-registration: PM3, the Polymarket-disagreement filter on days that do not exist yet (written 2026-10-13 before any such day)

**The question.** Does skipping L1 entries on Bitcoin and Ethereum where Polymarket's price for the side bought is 5 points or more below Kalshi's mid make the remaining entries better, on days after 2026-10-13?

**Data.** The forward Kalshi windows in `data/fwd1.sqlite` (FWD1's download) for Bitcoin and Ethereum closing on or after 2026-10-14 00:00 UTC, and for each the Polymarket price history, fetched the PM1 way into its own `data/pm3.sqlite`. The same rule, thresholds and flag as PM2 (`pm2.entries`, DISAGREE 0.05, 180 s freshness). One try, Bitcoin and Ethereum pooled.

**Single read.** `python -m scalper.pm3 fetch` then `python -m scalper.pm3 run`, once, on or after 2026-11-16, together with E3F, FWD1 and VOL1.

**Pass bar, fixed (a bar for a filter, not the zero test PM2 used).** `NOT_ENOUGH_DATA` if fewer than 100 skipped entries or fewer than 10 days. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: the skipped mean net is below zero; it is below the kept mean in the whole sample and in both halves of the days; and the improvement (kept mean minus the all-entries mean) exceeds the 95th percentile of 200 permutation draws in which the same number of entries per series are skipped at random.

**Numeric prediction, before the run.** The gap shrinks toward zero as the PM2 half-window pattern suggests: skipped mean between -1.0c and +0.5c, kept mean about +0.6c, the permutation test not cleared. **FALSIFIED** is more likely than not. About 60 Bitcoin and Ethereum entries a day over 33 days gives about 600 skipped entries, so a gap of 3c would show.

**What a pass would and would not mean.** A pass would be the first filter in this file confirmed on three separate stretches (the 40 days it was found on, 28 older days, and new days). Even then the live bot cannot use it from here: it would need an external Polymarket read at order time, a dependency the owner has not asked for. It would be put to the owner as a proposal, not made.

**Count.** One variant: 4,621 after PM3.

## Result: FLB1, favourites in long-dated, non-sports, non-price markets (run once on 2026-10-13)

28,005 eligible markets in 2,669 events (lifetime of at least 3 days, closing in the last 60 days, category not Sports, Financials or Crypto). Rule as registered.

| Lead | Entries | Events | Mean price paid | Loss rate | Net per contract | z (by event) | Halves | Placebo 95th pct | Minimum detectable edge | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 h | 1,837 | 701 | 0.936 | 6.6% | -0.64c | -0.81 | +0.09 / -1.36 | -0.75c | +1.67c | FALSIFIED (NOT SHOWN) |
| 72 h | 2,196 | 799 | 0.935 | 7.9% | **-1.83c** | **-2.43** | -2.57 / -1.10 | -0.97c | +1.58c | FALSIFIED |
| 168 h | 873 | 436 | 0.933 | 7.1% | -0.88c | -0.95 | -1.54 / -0.22 | -0.65c | +1.94c | FALSIFIED (NOT SHOWN) |

The prediction (between -2.0c and +1.0c, FALSIFIED at all three) was right. **Favourites in the rest of Kalshi do not beat their price; at 72 hours they lose.** L1's pattern is a property of 15 minute crypto and gold markets and not of Kalshi in general (SP1 said the same for sports).

Information, not tries: by category at 72 h, Politics -6.40c (225), Elections -2.42c (69), Entertainment -1.74c (351), Climate and Weather -2.80c (58), Science and Technology -0.66c, Economics -0.02c, Mentions -0.36c. **A deviation to state:** the "Commodities" category was not on the registered exclusion list, so daily and weekly commodity price brackets (price-driven look-alikes of L1, the very kind this test was meant to leave out) are in the universe: 718 of 2,196 entries at 72 h, -1.79c. Excluding them would not change a verdict that already reads FALSIFIED, and the rule was not changed after the fact. The median entry-candle volume is 0 contracts: most of these quotes are posted asks with no trading at that hour, the stale-quote problem the registration warned about. The mean price paid of 0.93 with a loss rate of 6.6% to 7.9% is just a fair price after a 0.4c to 0.5c fee, with a small negative drift. **Count unchanged** (FLB1's three tries were counted when registered).

## Information: the account simulation with XRP and Dogecoin appended (GROWTH2, 2026-10-13, not a try)

`python -m scalper.growth2`: the GROWTH simulation (live sizing at $46.50 a contract, 4.5% window limit, 5% day stop, fills 58% of the time, $500 plus $500 every 30 days, 400 paths of 360 days) on a day-block bootstrap of the 69 days of public candles (9,782 entries), with and without XRP and Dogecoin at the END of the list. The 69 days average +0.87c on the live three, so the baseline here is stronger than GROWTH's 40 day one. XRP and Dogecoin measured +1.61c on 4,385 entries.

| Case | Day 90 median | Day 180 median | Day 360 median (5th to 95th percentile) | Paths below paid-in at day 360 |
|---|---|---|---|---|
| Live three only | $2,322 | $5,168 | $10,773 ($8,848 to $12,630) | 0% |
| + XRP, Dogecoin as measured (+1.61c) | $3,518 | $8,514 | $18,330 ($15,617 to $20,975) | 0% |
| + XRP, Dogecoin at +0.5c | $2,553 | $5,729 | $12,653 ($10,053 to $15,428) | 0% |
| + XRP, Dogecoin at 0.0c | $2,120 | $4,832 | $10,575 ($7,801 to $12,928) | 0% |

**Reading it.** At zero edge the appended series do not hurt (the median is within 2% of the baseline; the window limit and the day stop keep the loss per window unchanged); at +0.5c they add about $1,900 over a year; at the measured edge they add about $7,500. The downside is bounded the way the proposal says and the upside depends on the edge holding. This is a bootstrap of past days with the profit add-on and the weekly review left out, not a forecast, and it inherits everything the proposal's caveats say (thin books, 40% correlated losses, E3F still to read).

## Information: what the sizing knobs do (GROWTH3, 2026-10-13, not a try)

`python -m scalper.growth3`: the account simulation on the live three series over 68 days (5,397 entries, measured mean +0.79c), varying the two sizing knobs: dollars of balance per contract (live: 46.5) and the contract ceiling (live: 40). Fills 58%, 4.5% window limit, 5% day stop, $500 plus $500 every 30 days, 400 paths of 360 days. Year-end balance (median, 5th and 95th percentile), share of paths ending below what was paid in, and the largest fall from a running peak (median and 95th percentile of paths):

| True edge | $ / contract | Ceiling | Median | 5th | 95th | Below paid-in | Median worst drop | 95th pct worst drop |
|---|---|---|---|---|---|---|---|---|
| 0.00c | 46.5 | 40 | $5,909 | $4,328 | $7,737 | 56% | 25.2% | 36.4% |
| 0.00c | 46.5 | 80 | $5,998 | $3,264 | $8,827 | 50% | 29.8% | 41.2% |
| 0.00c | 30 | 80 | $6,014 | $3,401 | $9,643 | 50% | 34.5% | 51.0% |
| +0.41c | 46.5 | 40 | $8,411 | $6,232 | $10,069 | 4% | 19.2% | 30.8% |
| +0.41c | 46.5 | 80 | $10,068 | $6,651 | $13,373 | 2% | 21.7% | 33.4% |
| +0.41c | 30 | 80 | $10,471 | $6,988 | $14,007 | 2% | 27.3% | 42.6% |
| +0.79c | 46.5 | 40 | $10,699 | $8,564 | $12,604 | 0% | 16.0% | 26.9% |
| +0.79c | 46.5 | 80 | $14,141 | $10,620 | $17,841 | 0% | 18.1% | 27.5% |
| +0.79c | 30 | 80 | $14,772 | $11,428 | $18,336 | 0% | 22.4% | 36.7% |
| +0.79c | 20 | 80 | $15,009 | $11,350 | $19,159 | 0% | 28.8% | 47.3% |

(The full 15 row grid is printed by the script.) **Reading it.** At the live setting the ceiling of 40 contracts is reached at a balance of about $1,860 and growth after that is close to linear, which is why raising it to 80 adds 20% to 30% to the year-end median at a similar drawdown, while shrinking the dollars per contract with the ceiling left at 40 changes almost nothing. Smaller dollars per contract with a higher ceiling buys a few more percent for a much deeper drawdown (a 95th percentile fall of 47% at 20 dollars per contract). Even with a zero edge the live setting has a median worst fall of 25% in a year, because the loss on a failed favourite is about 90c against a 6c win. Nothing here is a recommendation to change the sizing; the weekly size review and the owner's comfort with a 25% to 35% fall decide that.

## Information: the 25c exit on the 28 older days (2026-10-13, not a try)

`exit25` run on the L1B download (2,359 L1 entries on Bitcoin, Ethereum and gold): the line is crossed at a minute close in 98 entries (4.2%); of those 98, held to settlement 7 won (7.1%, mean -84.8c per contract). With an optimistic 0c slip the line adds +0.13c per entry (+1.407c against +1.276c hold-only); with a 5c slip it costs 0.03c (+1.243c against +1.276c). The 40 day sample said -0.04c, so the exit is neutral on both windows, as before: it limits the size of the rare loss, and its cost or gain is inside the noise either way.

## Result: E5, L1 unchanged on other commodities and two more coins (run once on 2026-10-14)

32,314 markets downloaded (30 with no candles skipped). Stage 1 on the 40 day discovery window, the holdout read only if Stage 1 passed. Rule as registered.

| Series | Entries (days) | Net per contract | z | Halves | Fees x1.2 | Median spread | Stage 1 |
|---|---|---|---|---|---|---|---|
| Silver | 742 (37) | +0.18c | +0.20 | -0.10 / +0.47 | +0.08c | 0.6c | FALSIFIED |
| Crude oil (WTI) | 784 (40) | +0.89c | +1.10 | +1.43 / +0.29 | +0.79c | 0.5c | FALSIFIED |
| Natural gas | 860 (40) | **+1.39c** | +1.94 | +1.13 / +1.68 | +1.30c | 1.0c | FALSIFIED (z below 2.1) |
| Copper | 837 (35) | -0.18c | -0.17 | +1.86 / -2.33 | -0.27c | 1.0c | FALSIFIED |
| Platinum | 436 (20) | -0.34c | -0.30 | +1.00 / -1.73 | -0.43c | 2.0c | FALSIFIED |
| Palladium | 394 (21) | -0.87c | -0.74 | -2.09 / +0.41 | -0.97c | 2.0c | FALSIFIED |
| Zcash | 1,155 (41) | **-1.85c** | **-2.24** | -2.85 / -0.80 | -1.94c | 1.2c | FALSIFIED |
| NEAR | 1,201 (41) | -0.84c | -1.05 | -1.40 / -0.25 | -0.93c | 1.0c | FALSIFIED |

Information (not tries): the six commodities pooled earned +0.34c (z +0.85) on discovery and **-0.50c** (z -0.77, 1,533 entries) on the older window; the two coins pooled -1.33c (z -2.15) on discovery and -0.55c on the holdout. The prediction (commodities +0.3c to +1.0c, coins about +0.5c, nearly all FALSIFIED) was right on the verdicts and a little optimistic on the coins. No audit trigger. Natural gas came closest (z +1.94) and has only 160 holdout entries, and it is one try of eight.

**What it says.** The L1 edge is not a property of "commodity" or "small coin" markets. The series where it has held on a separate window are gold, Ethereum (older days), XRP and Dogecoin; silver, oil, copper, platinum, palladium, Zcash, NEAR, HYPE, BNB and the currency pairs do not show it. Counting every 15 minute series tried on L1's rule (Bitcoin, Ethereum, Solana, gold, XRP, Dogecoin, HYPE, BNB, three currency pairs, six commodities, two coins) the honest base rate of "a series that passes on one window" is a handful out of about twenty, which is why XRP and Dogecoin needed their holdout and still wait for new days. **Count unchanged** (E5's eight tries were counted when registered).

## Result: XM1, the hourly ladder as a second price for the 15 minute market (run once on 2026-10-14)

1,896 hourly-aligned 15 minute windows (Bitcoin and Ethereum, 40 days), 1,870 with ladder quotes. Rule as registered.

| Series | Windows with a bracket | Trades | Net per contract | z | Halves | Placebo 95th pct | Minimum detectable edge | Brier: ladder vs 15 minute mid | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Bitcoin | 773 | 363 on 40 days | -2.05c | -0.90 | -1.38 / -2.66 | +2.09c | +4.75c | 0.1465 vs 0.1395 | FALSIFIED (NOT SHOWN) |
| Ethereum | 671 | 380 on 41 days | **-7.45c** | **-4.20** | -9.04 / -5.87 | +2.03c | +3.73c | 0.1470 vs 0.1321 | FALSIFIED |

The prediction (the ladder is the worse price, FALSIFIED) was right. The median gap between the ladder-implied probability and the 15 minute mid is about zero, but the 5th and 95th percentiles are about ±12c to ±14c, and trading toward the ladder loses: the 15 minute market is the better-calibrated price, and a ladder interpolated between strikes adds noise. Ethereum is clearly negative. **Count unchanged** (XM1's two tries were counted when registered).

**Control for L1B (information, 2026-10-14).** The same 2,359 older-window entries with the outcome redrawn at random with the market's own mid as the probability (300 draws): placebo mean **-0.80c**, 95th percentile +0.09c, largest +0.77c, against the observed **+1.28c**. The side bought costs on average 0.32c above its mid. So the L1B result is not an artifact of how entries are chosen (a fair market would have lost 0.8c), and the favourites really did win about 2.1 points more often than the mid priced them.

## Result: ARB1, locked arithmetic across mutually exclusive events (12 scans, 3.5 hours, 2026-10-13 and 14)

Twelve snapshots of every open event (about 13,700 to 14,100 events, 5,400 to 5,800 mutually exclusive, 5,070 to 5,430 usable with at least 2 legs bidding). **Zero opportunities in every scan** (a lock of at least 1c after fees on at least 10 contracts); zero persistent events; the verdict is FALSIFIED, as predicted.

Information: the sum of YES bids across the legs of a usable event has a median of 0.900 and a 95th percentile of 0.990; 0.98% of event-scans have a sum above 1.00, but none by enough to clear the fee on every leg. The largest lock seen was **-0.12c** (a two-leg House race, capacity 99), -0.14c with cent-rounded fees. Market makers keep exclusive events inside the arithmetic. Nothing to build. **Count unchanged** (one try, already counted).

## Information: an exploratory scan of the FLB1 download by category, side and price bucket (2026-10-14, looks, not tries; nothing registered)

To see whether any long-dated cell was worth a registered test, the FLB1 candles of the OLDER half of the markets (closing before 2026-09-16 10:30 UTC; the newer half was left unread) were split by category (7), side (YES, NO), price bucket (5) and lead (24 h and 72 h), keeping cells with 120 or more entries at both leads and the same sign. About 70 cells were looked at. The only cells with |z| above 2.5 at both leads were **buying YES in Mentions markets** at 10c to 30c (-7.1c, z -3.6 at 24 h; -8.9c, z -3.7 at 72 h) and at 30c to 70c (-6.7c and -13.0c), and buying NO in Commodities price brackets (-7c to -23c), i.e. YES on a "will they say it" market is overpaid for. The mirror, buying NO on Mentions at 70c to 90c, earns only +0.5c (24 h) and +3.9c (72 h) with z 0.24 and 1.42, because the NO buyer also pays the spread and fee. With 70 cells looked at, a few of this size would appear by chance, and the executable side shows no edge, so **nothing is registered from it**. The newer half stays unread in case a later idea needs it as a holdout.

## What FALSIFIED means here, and which results are only "not shown" (written 2026-10-14 at the owner's request)

**Definition.** `FALSIFIED` means the test did not clear a bar fixed before it ran: enough entries and days; mean net above zero; day clustered z of at least 2.1 (higher when several variants were tried); positive in both halves of the days; positive with fees x1.2; sometimes above a fair-market placebo. It is a statement about the evidence in that sample, not about the idea. `NOT_YET_FALSIFIED` is the best outcome and means "watch on new days"; there is no verdict that means "trade".

**Three kinds of FALSIFIED, kept apart.**
1. *Wrong sign, clearly:* SP1 (sports favourites -4.2c, z -2.8), FLB1 at 72 h (-1.8c, z -2.4), XM1 Ethereum (-7.5c, z -4.2), PM1 (Polymarket worse than Kalshi, z -3.8), E4 S&P (-2.8c), E5 Zcash (-1.9c, z -2.2), FX pairs (E3).
2. *Not shown (the minimum detectable edge is larger than any plausible edge):* E4 Bitcoin and Ethereum hourly ladders (14 days, MDE about 2.1c; means +0.96c and +0.64c), L1B Bitcoin (+0.55c, z +0.88), E5 natural gas (+1.39c, z +1.94, one try of eight), E5 oil (+0.89c, z +1.10), FLB1 at 24 h and 168 h, XM1 Bitcoin, E3 HYPE and BNB (-0.2c, -0.8c), the pooled six commodities on discovery (+0.34c).
3. *Failed its bar but carried a signal, re-registered:* PM2 (skipped entries lost 9.8% and 8.7% against 4.6% and 3.7%; now PM3 on new days).

**What stays open on purpose.** Group 2 can only be closed or confirmed with more data, not with a different rule: more days of the same test, or a forward read. Re-running the same rule on the same days is not allowed (it is the same try).

## Pre-registration: E5B and E3C, holdouts for two "not shown" series (written 2026-10-14; E5B reads data already downloaded, E3C downloads days never read)

**Why.** Two series were closed on thin evidence rather than a wrong sign, and the days that could test them again exist without waiting.

**E5B: crude oil (WTI) on the E5 holdout.** WTI was +0.89c (z +1.10) on discovery, FALSIFIED at Stage 1, so under E5's own design the holdout was not read (588 WTI entries before 2026-09-03 20:00 UTC exist in `data/alts3.sqlite`, unread). Natural gas (160 holdout entries) is too small to test and is left alone. Reading WTI's holdout now is a **new try that was chosen after seeing its discovery result**, which is disclosed here; the holdout days themselves were never looked at. Rule: L1 unchanged on `KXWTI15M` closing before the E5 split. Bar: at least 300 entries, 5 days, z at least 2.1, mean above zero, both halves positive, positive with fees x1.2 (the common bar). Prediction: +0.3c to +1.0c, **FALSIFIED (not shown)**; the MDE with about 590 entries is near 1.7c.

**E3C: HYPE and BNB on the 29 older days.** Both were slightly negative on E3's 41 days (-0.18c, -0.84c; z -0.24, -1.16) and never tested on older days. `python -m scalper.e3c fetch` into `data/alts4.sqlite` downloads only markets closing before 2026-09-03 20:00 UTC (E3's floor). Rule: L1 unchanged. Two tries (HYPE, BNB), the common bar. Prediction: both around 0c, **FALSIFIED**. A pass in either would be worth a forward read; a fail ends them.

**Count.** Three variants (WTI, HYPE, BNB): 4,621 -> 4,624.

## Result: E5B, crude oil on E5's holdout (run once on 2026-10-14)

`KXWTI15M` L1 unchanged, markets closing before 2026-09-03 20:00 UTC: **n=588 on 28 days, net -0.88c per contract, z -0.97**, halves -1.23c / -0.56c, fees x1.2 -0.97c, win 92.5% against 92.9% paid -> **FALSIFIED**. WTI's discovery result (+0.89c, z +1.10) did not repeat: it moved to the same size on the other side of zero, which is what chance looks like. Crude oil is closed (wrong sign on its own holdout). **Count: 4,622** after E5B (E3C's two tries are counted when it runs: 4,624).

## Result: E3C, HYPE and BNB on the 29 older days (run once on 2026-10-14)

5,442 markets downloaded (the days before 2026-09-03 20:00 UTC). L1 unchanged.

| Series | Entries | Net per contract | z | Halves | Fees x1.2 | Verdict |
|---|---|---|---|---|---|---|
| HYPE | 880 on 29 days | **-0.41c** | -0.60 | +0.08 / -0.91 | -0.51c | FALSIFIED |
| BNB | 897 on 29 days | **-0.64c** | -0.74 | +0.46 / -1.73 | -0.73c | FALSIFIED |

The prediction (both around 0c) was right. The two series that were slightly negative on E3's 41 days (-0.18c, -0.84c) are slightly negative on the older 29 as well: the win rate equals the price paid (93.0% against 92.9%), which is what a fair market gives after fees. Closed. These are "no edge", not "wrong sign with a large z". **Count: 4,624.**

**Where this leaves the series question.** On the 68 days, with a separate window for each, L1's rule shows an edge in gold, XRP and Dogecoin (confirmed on a holdout), Ethereum (older days only, +0.60c over 68) and Bitcoin (+0.45c, not significant); it shows none in HYPE, BNB, silver, oil, copper, platinum, palladium, Zcash, NEAR or the currency pairs. Natural gas is the only thin, unconfirmed lead (+1.39c, z +1.94, discovery only, 160 holdout entries): too small to test further without more days.

## Information: the live record against the backtest (owner's screenshots, 2026-10-14, bot since Oct 7; not a try)

188 settled trades, 177 won and 11 lost (94.1%, loss rate 5.9%), net **+$0.12**, profit factor 1.00, average win +$0.45, average loss -$7.23, deepest drawdown -$28.26, best/worst trade +$1.95 / -$20.36. 291 orders in all: 177 won, 11 lost, **103 no fill (35%)**, so about 65% of orders filled. Balance about $497.77; stake 9 contracts ($8.33, 1.7%); reinvest pool $0.00 of $0.93.

By market: Bitcoin 91 trades, 92% won, **-$20.62**; Ethereum 34 trades, 94%, +$5.11; gold 63 trades, 97%, **+$15.63**. By price paid: 88c to 90c 20 trades, 85% won, +$3.64; 90c to 92c 39, 90%, -$27.19; 92c to 95c 67, 96%, +$7.17; 95c to 97c 61, 100%, +$16.92.

**Reading it against the 68 day backtest.** The win rates sit where the candle backtest put them (Bitcoin 92% live against 93.6% older and about 93% recent; Ethereum 94% against 94.6%; gold 97% against 95.5%; by band the live 85%, 90%, 96%, 100% against a backtest loss rate of 11.6%, 7.6%, 4.7%, 3%), and **the series order is the same as the backtest's: gold best, Ethereum next, Bitcoin worst**. The dollar result is about zero, against about +$12 expected at +0.8c a contract on roughly 1,500 contracts. One trade is a loss of about $7 and one standard deviation of the total over 188 trades is about $24, so +$0.12 is half a standard deviation under +0.8c and the same distance over zero: **188 trades cannot tell +0.8c from zero.** The 25c exit was not the cause: the record shows the same few large losses a hold-only rule would have had. What the record does confirm is the mechanics (fills, sizing, stop, the series ranking); what it cannot yet confirm or deny is the edge. A few hundred more trades, and the 16 November reads, can.

## Pre-registration: BUYDIP1, "buy at key levels" against plain monthly buying, for SCHD, SPY and QQQ (written 2026-10-14 before any rule was run)

**The owner's question.** Buy and hold SCHD and JEPQ, adding at key levels instead of every month, and possibly fund them from an intraday strategy. Nothing in this file had tested a "buy the dip" rule on these funds by name (the earlier dividend work, about 6,000 variants, asked whether a dividend tilt beats SPY and found it does not).

**Facts first (public Yahoo daily total-return prices, information, 2026-10-14).** SCHD, 2011-10-20 to 2026-10-13: 6.44x, 13.2% a year, worst fall 33%; SPY over the same days 8.30x, 15.2% a year, worst fall 34%; QQQ 14.95x, 19.8% a year, worst fall 35%. JEPQ, 2022-05-04 to 2026-10-13 (4.4 years, one market cycle): 1.96x, 16.3% a year, worst fall 20%; QQQ 2.32x, 20.8% a year, worst fall 23%; SPY 1.93x. So the covered-call fund earned about what SPY did with a slightly smaller drop and gave up about 4.5 points a year to QQQ, the index it writes calls on; SCHD gave up about 2 points a year to SPY over 15 years. Neither is a free lunch; they are a choice of how the return arrives (income now, less upside).

**The question tested.** A saver receives $500 on the first trading day of every month. Does holding the cash and buying only at a "key level" end with more money than buying at once each month?

**Rules (all fixed now; signals use only closes up to and including the day, adjusted close).** Contributions of $500 arrive monthly for 60 months; cash earns 0%; the end value is the units held times the final adjusted close plus any cash left.
- **DCA:** buy at that day's close on arrival.
- **DIP10:** keep cash; spend ALL cash on the first close at least 10% below the highest close of the previous 252 trading days.
- **MA200:** keep cash; spend ALL cash on the first close below its 200 day average close.
- For both: any contribution that has waited 6 months is spent (with everything else waiting) on that day, so cash never sits forever.

**Tries (6, no variants):** DIP10 and MA200 on SCHD, SPY and QQQ. JEPQ is too short for 60 month windows; it gets 36 month windows as information only, not a try.

**Statistic.** For every start month with a full 60 months of data, R = end value of the rule divided by end value of DCA. `NOT_ENOUGH_DATA` if fewer than 24 start months. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: median R above 1.00; R above 1.00 in at least 60% of the start months; median R above 1.00 in both halves of the start months. Anything else `FALSIFIED`. **Power is low and stated:** start months overlap, so SCHD's 15 years hold about 3 independent 5 year windows and SPY and QQQ about 5; the bar can show a rule loses, not that one wins.

**Counterparty and prior.** The counterparty is the seller during a drawdown who does not wait for the recovery; the prior is against it, because stocks drift up, cash earns nothing here and a rule that waits for a dip spends many months out of the market. **Prediction: median R at or below 1.00 for all six, FALSIFIED.** If any median is above 1.00 it is an audit trigger first (a lookahead in the signal).

**Information, not part of the verdict:** mean cash held, share of months fully invested, worst-case R, and the same with cash earning 4% a year. **Count:** this file's running total was 4,624; six tries makes it **4,630**.

## Result: BUYDIP1, buy at key levels against plain monthly buying (run once on 2026-10-14)

Public Yahoo daily total-return closes: SCHD 3,767 days from 2011-10-20, SPY and QQQ 6,311 days from 2001-09-10, JEPQ 1,116 days from 2022-05-04. $500 a month for 60 months, cash earning 0%.

| Fund | Rule | Start months | Median R (rule / DCA end value) | R above 1 | Halves | Worst / best R | Cash held | Verdict |
|---|---|---|---|---|---|---|---|---|
| SCHD | DIP10 | 121 | 0.987 | 7% | 0.983 / 0.990 | 0.962 / 1.012 | 77% of days | FALSIFIED |
| SCHD | MA200 | 121 | 0.986 | 4% | 0.981 / 0.989 | 0.961 / 1.006 | 67% | FALSIFIED |
| SPY | DIP10 | 242 | 0.982 | 0% | 0.984 / 0.980 | 0.962 / 1.000 | 71% | FALSIFIED |
| SPY | MA200 | 242 | 0.982 | 2% | 0.987 / 0.978 | 0.953 / 1.004 | 67% | FALSIFIED |
| QQQ | DIP10 | 242 | 0.993 | 27% | 0.991 / 0.996 | 0.962 / 1.040 | 65% | FALSIFIED |
| QQQ | MA200 | 242 | 0.982 | 7% | 0.989 / 0.975 | 0.956 / 1.039 | 66% | FALSIFIED |

The prediction (median R at or below 1.00 for all six) was right and no audit trigger fired. Waiting for a "key level" ended with 0.7% to 1.8% LESS money than buying each month at the median, and beat monthly buying in 0% to 27% of start months. With cash earning 4% the gap shrinks to 0% to 1.1% and the rules still lose most months (QQQ DIP10 reaches median R 1.000, 48% of months above 1). JEPQ (36 month windows, information): DIP10 median R 0.957, MA200 0.979. **What this does and does not close:** these two rules (a 10% fall from the 252 day high, a close under the 200 day average) with a 6 month fallback lose to monthly buying on all three funds; it is not a proof that no entry level works, and with start months overlapping the 15 years of SCHD hold about 3 independent 5 year windows. It is consistent with the general finding that a saver who waits holds cash through the rises that make up most of the return. **Count: 4,630.**

**Information (2026-10-14).** Total return from public prices: SCHD 13.2% a year over 15 years against SPY 15.2% and QQQ 19.8% (worst falls 33%, 34%, 35%); JEPQ 16.3% a year over 4.4 years against QQQ 20.8% and SPY 15.9% (worst falls 20%, 23%, 19%); over the last 3 years SCHD 16.7% against SPY 23.2%, JEPQ 21.3% against QQQ 27.4%. JEPQ is one market cycle old, so its numbers are an anecdote about a rising Nasdaq with calls sold against it.

## Equities and options: what is already crossed off, and the next registered tests (written 2026-10-14 before any run)

**Owner's request:** find an edge in the equities or options universe.

**What is already settled (from `shwoop-server/research/MECHANISMS.md`, not re-derived).** Seven single-name intraday directional mechanisms (opening-range breakout, exhaustion fade, failed breakout, gap reversion tight and loose, VWAP displacement, close-auction drift), the within-group dispersion trade (+0.144% gross, killed by a 0.20% two-leg cost, and still failing after measured costs on search deflation), crypto-to-equity lead-lag, ORB swings on three universes, post-earnings drift, and the earlier fund, trend and dividend work (about 15,000 and 6,000 variants): all `FALSIFIED`, and "a real edge that is negative" for VWAP displacement. Options income (cash-secured puts, weekly credit spreads) has never been backtestable because Alpaca's options data is a live snapshot with no history; the only evidence is a forward paper record.

**What has not been tried, and why it is different.** Everything crossed off is a bet that THIS stock moves next. What remains are index-level structures with a named counterparty who is not trading for profit: (a) overnight versus intraday drift (market makers and day traders who must be flat by the close demand a premium for carrying risk overnight), (b) the turn of the month (salary and pension flows that arrive on fixed dates), (c) the pre-holiday session (retail optimism and thin selling), and (d) the volatility risk premium (hedgers who pay more for insurance than it later pays out). They cost almost nothing to trade in SPY and QQQ, have 25 to 33 years of daily history, and were published in the 1990s and 2000s, so **the days after 2011 are a true out-of-sample test of whether publication killed them**.

**Rules, fixed now.** Data: public Yahoo daily open and adjusted close (total return) for SPY and QQQ. Discovery = the days up to 2011-12-31; holdout = 2012-01-01 to the last day. Each mechanism is a rule for which days to hold, with `s_t` the strategy's daily net return (zero on days it is flat, cash earning nothing) and `r_t` the buy-and-hold daily return on the same day.
- **Overnight (A):** hold from each close to the next open (`open_t / close_(t-1) - 1`, dividends and splits adjusted); cost 2 basis points per day (an exit and an entry at the auction price), 4 in the stress case.
- **Turn of the month (B):** hold from the close of the last trading day of the month through the close of the 3rd trading day of the next month; cost 2 basis points per round trip, 4 in stress.
- **Pre-holiday (C):** hold the last session before a market holiday: buy the close of the session before it and sell the close of the pre-holiday session itself, earning that session's close-to-close return (a pre-holiday session is a session whose next session comes after a weekday with no trading, derived from gaps in the trading calendar); cost 2 basis points per round trip, 4 in stress. (Clarified on 2026-10-14 before any rule was run; the first draft's wording was ambiguous.)
- **Statistic:** alpha = mean(`s_t`) minus beta times mean(`r_t`), beta from regressing `s_t` on `r_t` over the same days; annualised by 252; standard error clustered by calendar month. It asks whether the rule earns more than its own market exposure explains, which is the only question that matters for a rule that is in the market a fraction of the time.

**Tries (4): A on SPY and on QQQ, B on SPY, C on SPY.** Four tries means the bar is a month-clustered z of at least **2.4**.

**Pass bar, fixed, on the HOLDOUT only.** `NOT_ENOUGH_DATA` if fewer than 150 active periods in the holdout. Otherwise `NOT_YET_FALSIFIED` only if ALL hold: annualised alpha net of costs above zero; month-clustered z at least 2.4; alpha above zero in both halves of the holdout (split at its date midpoint); alpha still above zero at the stress cost; and the discovery alpha is above zero (the published effect existed). Anything else `FALSIFIED`.

**Numeric prediction, before the run.** Discovery alphas positive (overnight 3% to 8% a year gross, turn of the month 1% to 3%, pre-holiday under 1%); holdout alphas indistinguishable from zero after 2 basis points a day; **all four FALSIFIED**, overnight probably "not shown" with a z near 1. If any holdout z is above 2.4 it is an audit trigger first (overnight `open` prices in Yahoo's history are the first suspect).

**The options side (information, not a try).** Without historical chains, the volatility risk premium can only be read from the index: the gap between the VIX (30 day implied volatility) and the volatility that SPY then realised over the next 30 days, from public daily data. It is printed as a distribution (mean gap, share of months positive, worst months, drop from a rule that is short that gap), and it cannot say anything about fills, skew or margin. **The thing that would unlock options research is data:** a daily recorder of the SPY, QQQ and IWM option chains (bid, ask, implied volatility, open interest) on the broker's live snapshot, so that six months from now the put-selling and spread mechanisms have a history to be tested on. That is a code change to the server that I have not made.

**Count:** the Kalshi total in this file was 4,630; the four tries here are kept in their own count (4) with their own bar and not added to it.

## Result: IDX1, overnight drift, turn of the month and the pre-holiday session (run once on 2026-10-14)

Public Yahoo daily data: SPY 8,484 sessions from 1993, QQQ 6,942 from 1999, ^VIX from 1993. Discovery to 2011-12-31, holdout from 2012-01-01. Alpha is annualised and net of 2 basis points per round trip (the stress cost is 4).

| Rule | Holdout active periods | Holdout net alpha | Month clustered z | Halves | At 4 bp | Discovery alpha (z) | Verdict |
|---|---|---|---|---|---|---|---|
| Overnight, SPY | 3,717 days | **-2.05%** | -1.01 | -3.12% / -0.97% | -7.09% | +3.07% (+1.76) | FALSIFIED |
| Overnight, QQQ | 3,717 days | +0.57% | +0.25 | +0.37% / +0.78% | -4.47% | +8.34% (+2.25) | FALSIFIED |
| Turn of the month, SPY | 178 months | +1.09% | +0.72 | -0.02% / +1.93% | +0.84% | +3.41% (+2.27) | FALSIFIED (not shown) |
| Pre-holiday, SPY | 139 holidays | | | | | | NOT_ENOUGH_DATA |

The predictions were right on every verdict (discovery positive, holdout indistinguishable from zero or negative, all four not passing). **Overnight drift existed before 2012 and is gone after costs**: SPY earned +3.1% a year of alpha in discovery and -2.1% in the holdout, QQQ +8.3% then +0.6%, and at 4 basis points a day both are clearly negative; holding only overnight returned +4.4% a year on SPY against +15.4% for buying and holding it over 2012 to 2026. **The turn of the month is positive in both periods (+3.4%, +1.1%) but under 1 z in the holdout**, which is "not shown" with 178 months, and its gain per month is small compared with a 2 basis point cost and the idle cash. **Pre-holiday**: the holdout has 139 holidays, under the 150 the bar required, so it is NOT_ENOUGH_DATA; my minimum was set without checking that a holiday count could reach it, a registration mistake that I am leaving as written instead of lowering the bar after seeing the number. The index-level calendar effects that were published in the 1990s and 2000s did not survive into the data after 2011 as something a retail account can trade. Own count (4 tries): 4.

**Options side, information:** over 403 non-overlapping 21 session windows since 1993 the VIX exceeded the volatility SPY then realised by **+3.66 vol points on average, in 83% of windows (median +4.46)**, and was below it by more than 6.5 points in the worst 5% and by **46 points in the worst month** (the 2020 and 2008 type months). So the premium that makes put selling look attractive is real in the index data, and so is the loss that comes with it; whether a defined-risk version (a put spread, not a naked short) keeps enough of the +3.7 points after bid-ask costs and capped gains cannot be answered without option chains, which is the data gap named above.

## The data that unlocks options research: a daily chain recorder (built 2026-10-14, on the `shwoop-server` branch `claude/epic-ptolemy-0amjd9`, NOT deployed)

`shwoop-server/src/optionsChainRecorder.js`, wired into the snapshot-only server: after the 16:10 ET close on weekdays it reads SPY, QQQ and IWM option snapshots (expirations up to 50 days, strikes within 12% of spot, the free `indicative` feed) and writes one compact row per contract (bid, ask, size, last, implied volatility, delta, open interest) to the backend-only collection `optionsChains`, with document ids `date_underlying_part` so two instances during a deploy overwrite each other with the same data. It never trades (a test asserts that no order, cancel, transaction or user-document call appears in the module). 8 gates pass; the rest of the server's tests are unchanged.

**What it is for.** In about six months it gives a history of roughly 120 sessions of real bids and asks, enough to test, with the same pre-registration discipline as everything above, a defined-risk put spread or a weekly credit spread at the quotes that were actually there. Until then every options mechanism has only a forward paper record. **What it cannot do:** the indicative feed is not the consolidated tape, so a test on it says what would have sold at an indicative bid; it will not show fill quality; and six months is one market regime. It starts collecting only when the server is deployed, which needs a laptop and the owner's go-ahead; nothing was deployed.

## Information: the live record on 2026-10-20 (owner's page copy; bot since Oct 7; not a try)

275 settled trades, 258 won, 17 lost (loss rate 6.2%); net **+$2.20**; profit factor 1.02; average win +$0.43, average loss -$6.36; expectancy +$0.01 a trade; best/worst +$1.95 / -$20.36; deepest drawdown -$28.26; longest losing run 2; streak now 9 wins. 432 orders in all, 157 no fill (36%).

By market: Bitcoin 124 trades, 92% won, **-$22.21**; Ethereum 57, 91%, -$2.62; gold 94, 98%, **+$27.03**. By price paid: 88c to 90c 34 trades, 82% won, -$3.08; 90c to 92c 56, 93%, -$19.34; 92c to 95c 92, 93%, +$1.73; 95c to 97c 92, 100%, **+$23.31**. The 25c exit: fell to 25c 14 times, sold 12, sell failed or skipped 2, trigger bid 19.3c on average, sold at 21.0c on average (slip -1.7c, i.e. better than the trigger), realised on the sells **-$67.45**, won after falling 1 of 2 (the two not sold).

**Reading.**
- **Total:** a loss rate of 6.2% against a break-even of about 7% at the prices paid, so slightly better than break-even; the dollar result (+$2.20) is about half a standard deviation under what +0.8c a contract would give (about +$19, sd about $27). Still cannot tell +0.8c from zero.
- **Series order matches the backtest again:** gold best, Ethereum next, Bitcoin worst (backtest 68 days: +1.54c, +0.60c, +0.45c). Bitcoin's live loss rate is 8% against 6.4% in the backtest.
- **By price:** all the profit is in the 95c to 97c band (+$23.31, 92 wins of 92); the three bands below 95c together lost $20.41 on 182 trades. The backtest does not agree (88c to 90c -0.73c, 92c to 94c best at +1.88c, 94c to 96c +0.59c). 92 wins of 92 at an expected 97% happens about 6% of the time by chance, so this is a pattern to WATCH, not to tune on; it is tested on new days only.
- **25c exit:** the exit line was touched in 14 of 17 losing trades; the backtest said the line is neutral (-0.03c to +0.13c a contract on two windows). On 12 sells realised -$67.45, about -$5.6 each; whether holding would have been better is not shown on the page for these (it needs the settlement result per trade). Two sells failed or were skipped, one of which won: a failure mode to watch.

**To circle back to** (owner's request): (1) reorder the series list so Bitcoin is last (backtest and live both rank it lowest; a decision, not a test), (2) whether a 95c floor is worth a pre-registered forward test, (3) the two failed sells and the exit's hold-versus-sell comparison once the per-trade settlement data is pulled, (4) the 2026-11-16 forward reads.

## Information: the published Research Log (2026-10-13) and the Daily Recap (2026-10-20), filed here at the owner's request (not a try)

Both pages were written from this README and the owner's figures; nothing in them is new data. Filed so the numbers sit in one place.

**Research Log headline, 2026-10-13.** L1 on the 28 days before the 40 it was found on: Bitcoin 838 entries +0.55c (z 0.88, below the bar), Ethereum 901 +1.32c (z 2.24), gold 620 +2.20c (z 2.73), pooled +1.28c (z +3.2). All 68 days pooled: 5,397 entries +0.79c (z +2.52); gold +1.54c (z 2.94), Ethereum +0.60c, Bitcoin +0.45c; positive in 8 of 10 weeks. XRP and Dogecoin: +1.43c and +1.54c on the first 41 days; on 29 older days pooled +1.76c on 1,917 entries (z +3.97), positive every week, about half the total from the five best days, about 40% of their losses coincide with Bitcoin losses.

**Tried and failed, as published:** sports favourites (12 series) -4.2c on 535 entries (z -2.8); weather against public forecasts -3.3c (z -2.5); decision tree on L1 entries (flagged losers won slightly more); Polymarket as a second price (z -3.8 Bitcoin, -2.5 Ethereum); hourly ladders (S&P -2.8c, crypto positive but too few entries); HYPE and BNB slightly negative, currencies -0.6c to -4.3c; locked arithmetic across exclusive events 0 opportunities in 12 scans; long-dated non-sports favourites -0.6c to -1.8c; silver, crude oil, natural gas (+1.4c, z 1.9, closest), copper, platinum, palladium, Zcash (-1.9c, z -2.2), NEAR none; hourly ladder as a second price for 15 minute markets (Ethereum -7.5c, z -4.2).

**Account simulation, as published** ($500 plus $500 a month, one year, $6,000 paid in, draws from past entries, not forecasts): at +0.41c median about $8,400; at +0.79c about $10,700; at zero about $5,900; with XRP and Dogecoin appended about $18,300 if their edge holds, $12,700 at +0.5c, $10,600 at zero. The 40 contract ceiling is reached near $1,860; 80 adds 20% to 30% to the year-end median at a similar drawdown; with zero edge the median worst fall in a year is about 25%.

**Daily Recap, 2026-10-20 (written from Oct 12 to 14 figures, so partly stale).** Its open items and decisions are merged into `docs/ROADMAP.md` ("What you need to do now") with what is done and what is still open as of 2026-10-20. Items it listed that were already done by the end of that day: the laptop deploy of the pool fix and sizing, XRP and Dogecoin added to the series list, and the size review (the cap was set to 4 by hand after the 2026-10-17 loss stop). Still open from it: the two failed 25c exits, whether the full functions deploy ever ran, the Flatten and exit overlap, hand-sold positions counted as held, the Firebase bill, and the decisions on the 90c to 92c band, Bitcoin, the Polymarket skip and the exit line itself.

## Pre-registration: TP1, take profit at 99c on L1's entries (written 2026-10-20 before any run; the owner's request, "cash out at 99% to avoid flips")

**The question.** L1 holds every entry to settlement, so a favourite that reaches 99c and then flips in the last minutes costs the whole stake (about 92c). Does selling at the bid the first time it is 99c or better beat holding to settlement?

**Why it might not.** Settlement is free and pays 100c. Selling at 99c gives up about 1c on every winner that reaches it, plus the sell's taker fee (about 0.1c, rounded up to a cent per order on Kalshi). The market prices a flip from 99c at about 1%, so selling there is break-even if that price is right and loses if it is. **Counterparty and edge story:** none beyond L1's own. The rule only helps if the 15 minute markets underprice a last-minute reversal when the favourite is already at 99c, that is, if flips from 99c happen more than about 1% to 1.5% of the time. Nobody has to be wrong for the rule to lose; somebody must be wrong for it to win.

**Rule, fixed.** Entries exactly L1's (`hold_rule`, 360 s left, favourite's ask 0.88 to 0.97, taker, same fee model). After entry the held side's bid is read at the candle closes 300, 240, 180, 120 and 60 s before the close (strictly later than the entry candle, the same checks as `exits.py`); at the first one where the bid is **at or above 0.99** the position is sold there, at that bid, paying a taker fee on both legs. Otherwise it is held to settlement. Nothing reads the result to decide the exit. One threshold only: 0.99. Other levels (0.98, 0.97) are not tried here, because the owner asked for 99 and each extra level is another try.

**Data.** Two windows, each read once: the 40 days in `book.sqlite` (primary) and the 28 older days in `l1b.sqlite` (the holdout). The rule must pass on both.

**Numeric prediction, before the run.** The rule fires on most entries (a winner nearly always reaches 99c by the last check), so it costs about 1.0c to 1.4c per entry against holding (give-up about 1c, plus fee), and the flips it avoids are rarer than 1%. Predicted difference against hold: **about -1.0c to -1.4c per entry, day clustered z below -3, FALSIFIED in both windows.**

**Pass bar, fixed (this is one try, so the single-try bar).** In **each** window: at least 300 entries on at least 5 days; the difference (rule minus hold) per entry above zero; day clustered z of the difference at least 2.5; the difference positive in both halves of the days; still positive with fees x1.2; and above the 95th percentile of the same rule in a fair market (outcomes drawn from each market's own late price), which measures what the rule costs when nobody is wrong. Otherwise `FALSIFIED`.

**Kill criterion.** Any condition failing in either window is FALSIFIED. There is also a plain figure reported whatever the verdict: of the entries whose bid reached 99c at a check, the share that then lost at settlement (the flip rate). Break-even is about 1% to 1.5%; a flip rate above that with a failed bar means the sample was too small, not that the rule is wrong, and would be re-registered on new days rather than re-read.

**Running count of tries.** About 4,625 on Kalshi with this one.

## Result: TP1, take profit at 99c on L1's entries (run once on 2026-10-20)

**Verdict: `FALSIFIED` in both windows.**

| Window | Entries | Line reached | Of those, lost at settlement | Rule | Hold | Difference | Day clustered z | Fair-market 95th pct | Halves | Fees x1.2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 40 days (`book.sqlite`, primary) | 3,038 on 41 days | 2,409 (79.3%) | 12 (0.50%) | +0.32c | +0.41c | **-0.09c** | -0.76 | +0.17c | +0.07c / -0.24c | -0.10c |
| 28 older days (`l1b.sqlite`, holdout) | 2,359 on 28 days | 1,831 (77.6%) | 5 (0.27%) | +1.00c | +1.28c | **-0.27c** | -3.14 | +0.45c | -0.30c / -0.25c | -0.28c |

**Reading.**
- The flip rate from 99c is **0.50% and 0.27%**, below the roughly 1% to 1.5% break-even, so the market prices a last-minute reversal from 99c higher than it happens. Selling there pays for insurance that was already priced above its risk.
- The cash-out was never positive: -0.09c on the primary window (inside the noise) and -0.27c on the holdout (z -3.14, a clear cost). Neither half of the days cleared zero in the holdout.
- **The prediction was right on the verdict and wrong on the size.** It said -1.0c to -1.4c per entry; the real cost is 0.1c to 0.3c, because the bid at the checks is often above 0.99, so the give-up per winner is smaller than the full cent assumed. Recorded as it was.
- Not tried here, deliberately: other lines (0.98, 0.97), each another try.

**What it does not say.** It uses minute candles read at five checks before the close, so a spike to 99c between checks, or a bid at 99c that a real sell could not fill at size, is not seen; both can only make the live rule worse than this. Four contracts at the touch is small, so depth is not the issue.

**Decision.** Nothing built, nothing changed live. Running count of tries on Kalshi: about 4,625.

## Information: a census of Kalshi's short-term series (2026-10-20, counts and volumes only, not a try)

The owner asked to expand to more short-term strategies and markets, so the whole series catalog was read (public `/series`, then `/markets?status=settled` with a 69 day window for each untested series). Nothing was priced or tested.

**Catalog.** 15,289 series; short-term repeating ones: 35 at 15 minutes, 78 hourly, 340 daily (weather 136, financials 105, economics 64, crypto 61, entertainment 30, commodities 19).

**15 minute series (35).** 19 are already tested (every liquid crypto and commodity one, EURUSD, GBPUSD, USDJPY). Of the 16 never tested: Brent, Cardano, Bitcoin Cash, TON, the Dow, the S&P 500 and the Nasdaq 100 have **no settled markets at all in the last 69 days** (listed, not trading); the four Treasury yield series (2, 5, 10, 30 year) have 66 markets on **2 days** at a median volume of **1 to 4 contracts**; the two "coin race" and "comparison" series are not up or down markets; one is a test series. **Only AUDUSD and USDCAD are live and new: 837 settled markets each on 12 days, median volume about 1,600 contracts a market** (for scale, gold is about 458,000, XRP 74,000, and the thinnest series tested before were 4,000 to 10,000).

**Hourly series (78).** 47 are tested or have no settled markets. The other 31 have 1 to 5 days of history; the one with real volume is Miami hourly temperature (median about 1,000 contracts, 5 days); the 8 other temperature series run at 1 to 56; the Treasury, Nikkei, Dow, metals, coin and Nasdaq hourly series sit at a median volume of 0.

**Reading.** The liquid, repeating, short-term Kalshi markets have been covered. What is left is thin (AUDUSD and USDCAD at 15 minutes, 12 days) or untested only because it is not traded. A second strategy therefore has to come from a different rule on markets already covered, or from the 340 daily series (weather was tested and lost, WX1 -3.3c; the economics, financials and entertainment dailies have not been looked at for liquidity), not from a new 15 minute or hourly series. Candidates worth a registered test: L1 unchanged on AUDUSD and USDCAD once they have enough days (the same rule, about 30 more days needed to reach 300 entries), and the hourly Bitcoin and Ethereum ladders again with more days (E4: positive, too few entries to tell from zero).

## Pre-registration: PAPER1, forward paper tracking of three candidates (written 2026-10-20 before any paper entry exists)

**What it is.** A keyless scheduled function (`kalshiPaperTick`) reads public open markets and records what L1's rule WOULD have bought, one contract, no money, and later the public result. It places nothing, signs nothing, holds no key, makes no `/portfolio` call and no POST. Its records are never shown next to the live record.

**Why paper, and why these three.** The owner wants more short-term strategies and markets. The 2026-10-20 census of Kalshi's short-term series found the liquid, repeating markets already covered; what is left is thin or only now trading. Forward paper entries are the only way to add days for a candidate that cannot be tested on history (AUDUSD and USDCAD have 12 days of it) and to read a near miss on days it was not selected on (natural gas). Three candidates, fixed now, no others:
1. **KXAUDUSD15M**, never tested (12 days of history, median volume about 1,600 contracts a market).
2. **KXUSDCAD15M**, never tested (the same).
3. **KXNATGAS15M**, tested in E5 on discovery and holdout and not shown (closest of the commodities, +1.4c, z 1.9); this is a forward read of a near miss, so it counts as a try.

**Rule (identical to L1).** Every minute inside the L1 window (330 to 400 s before the close) for each candidate's open markets: buy the favourite when its ask (YES) or one minus its bid (NO) is 0.88 to 0.97, one contract, taker at that price, fee 7% x p x (1 - p) per contract (the research's `scalps.fee`, NOT `kalshiSignalLib.takerFee`: that rounds up to a cent per order, which at one contract would charge about 1c where the research charges about 0.5c, and would bias every paper result down; corrected on 2026-10-20 while building, before any entry existed), hold to settlement. One entry per market (a deterministic document id, so two processes cannot record it twice). Nothing reads a result to decide an entry.

**Counterparty.** The same as L1's and no new one is claimed: retail buying the cheap side of a near-certain short-dated market. For the FX pairs there is no earlier evidence that this holds.

**Pass bar for promotion to a real-money slot, fixed now.** One read per candidate, on or after **2026-11-30** (about 40 days of entries), at least **300** paper entries and at least **10** days; mean net above zero; day clustered z at least **2.1**; both halves of the days positive; positive with fees x1.2; and then still only a candidate for a small capped slot with its own loss stop that cannot hold a position at the same time as L1's (see CLAUDE.md, "L1 is the only strategy"). A candidate that does not reach 300 entries by 2026-12-31 reads `NOT_ENOUGH_DATA`, never a pass or a fail. The read is run **once**; if the data are not enough it is repeated only after the minimum is met, never to chase a pass.

**Numeric prediction, before the first entry.** AUDUSD and USDCAD: net about +0.3c per entry, z under 1.5 at 40 days, **FALSIFIED or NOT_ENOUGH_DATA** (FX 15 minute markets are thin and the three FX pairs already tested were negative: -0.6c to -4.3c in the earlier FX check). Natural gas: about +0.5c, z under 1.5, FALSIFIED. Minimum detectable edge at 300 entries is about +1.0c, so a true +0.5c edge cannot be seen.

**Kill criterion.** Any bar condition failing is FALSIFIED. The paper record has nothing to say about slippage on a real order at size; a pass is only permission to consider a small live slot.

**Count.** Three tries: the running total in this file was about 4,625 after TP1, so it is about 4,628.

## Information: the research data is archived (2026-10-20, not a try)

The databases under `kalshi-scalper/data/` are gitignored and lived only in the cloud research container, and Kalshi's history reaches back about 69 days, so the early August days (the L1 holdout `l1b`, the E3B and E5 holdouts) would have been unrecoverable once the container ended or mid-September passed. They are now on the branch **`research-data`** of `shwoopnet/shwoopnet`: 14 databases and one price-file archive, 44 MB compressed, with `MANIFEST.md` (size, coverage, checksum per file) and `restore.sh` (decompresses into `kalshi-scalper/data/`; tested: `l1b` restores with its 7,213 markets and passes SQLite's integrity check; `book` and `e3b` were integrity-checked too). Public Kalshi market data and public price files only; no keys, balances or account data. The branch is not published by Pages (it is not the default branch) but it is readable by anyone who can read the repository, and a full clone now downloads about 44 MB more. The archive is a snapshot of 2026-10-20: forward days after it (for example the 2026-11-16 reads) come from fresh downloads, and a second snapshot should be taken before about 2026-12-01 so the early days are never the only copy.
