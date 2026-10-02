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

Strategy variants tried so far: 0. Cuts examined by the decision rule: 18.

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
