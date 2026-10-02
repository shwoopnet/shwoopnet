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

Strategy variants tried so far: 0.

## Facts measured, not assumed (Oct 2026)

- Market resolves on a 60 second average of CF Benchmarks index at close vs
  at open, not the last tick.
- Quotes are dollar strings; ticks are 0.1c below 10c and above 90c, 1c between.
- Fee type is `quadratic`: dearest at 50c, cheap near the extremes. A scalp
  that exits early pays it on both legs.
- Fee rate (0.07) in `fees.py` is from memory. Verify against real fills.

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
