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

Strategy variants tried so far: 1 (see Verdicts). Cuts examined by the decision rule: 18.

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

Strategy variants tried so far: 1 (this one). Cuts examined: 18.

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
