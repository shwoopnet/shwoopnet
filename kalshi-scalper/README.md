# kalshi-scalper

Research and risk tooling for Kalshi 15 minute BTC (`KXBTC15M`) and gold
(`KXGOLD15M`) markets. Standalone on purpose: it is not part of
`shwoop-server`, which places real Alpaca orders.

## Status

Nothing here places an order. Order placement does not exist yet and is
added only after the bar below is cleared in paper trading.

## Build order

1. `recorder.py`  record books for days (run it, see below).
2. `analyze.py`   is there any move bigger than spread plus fees (done).
3. Paper engine   simulate fills from recorded books, never from mids.
4. Strategy       only if step 2 shows room. Declares counterparty first.
5. Live, tiny     demo env, then smallest real size, behind `risk.py`.

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

## Run it on your Mac (background, survives reboots)

Kalshi's CDN refuses requests from Google Cloud addresses, so this runs on your
own computer instead of Firebase. It only reads Kalshi's public prices: no
account, key or password.

    cd kalshi-scalper/src
    python3 -m scalper.service install      # start now, and at every login
    python3 -m scalper.status               # how much is saved, and any gaps
    python3 -m scalper.service uninstall    # stop it (saved data is kept)

Data lands in `kalshi-scalper/data/book.sqlite` (about 10 MB a day). Back that
file up if it matters to you; it is not in git.

**Sleep is the thing to watch.** The service stops the Mac idling to sleep, but
a closed lid or a manual sleep still stops it. `status` reports those as gaps,
so a hole shows up as a fact and not as silence. Anything computed over the data
must not span a gap.

If you see `CERTIFICATE_VERIFY_FAILED`, you are on a python.org install: run
"Install Certificates.command" from `/Applications/Python 3.x/`.

On other systems: `cd src && python3 -m scalper.recorder 2`.

## Analyse

    cd src && python3 -m scalper.analyze    # needs a few days of data first
    ./run_tests.sh

Create an empty file named `KILL` in this directory to halt all ordering.
