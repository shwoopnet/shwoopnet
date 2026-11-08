# COINRACE1 PROTOCOL (registered Nov 8, 2026, before any outcome is joined)

Research only. No trading code, no key, no order, no fetching: local sqlite `data/newh15/candles.sqlite` (A11 in DATA_INVENTORY). Quote-regime caveat: Aug 24 to Oct 30 2026 public Kalshi candles.

## What and why (and what is NOT new)
Market: Kalshi `KXCRYPTOLEAD15M` ("Coin Race"): five mutually exclusive YES markets per 15 minute event (BTC, ETH, SOL, XRP, HYPE), the winner is the token with the best return in the window. 6,343 events, 31,715 markets, 25,287 with the full 15 candles. Prior work on this series: RACELOCK (structure only: Dutch book T1, over-round, and T2 = NO on the leg with the largest ask above its normalised share, FALSIFIED PF 0.77 / 0.775 on n 1,662 / 1,379, which read some windows in the Oct holdout region). Never done: a token-level cheap-side YES scan (the inventory says it is the only series with 1,500+ windows without an L1-shape test). So this is a NEW SERIES for the cheap-tail rule scan, with RACELOCK T2 disclosed as the nearest prior try and counted in N already.
Counterparty: retail buyers of the five-way race who pay a visible over-round (the five asks sum to about 1.24 at 9 minutes left, per RACELOCK) and chase the token that already ran or the lottery-priced laggard. A cheap-side rule can only win if some subset of those tickets is priced below its fair share after the over-round; the pooled baseline is expected to be about -5c per contract from the over-round alone.

## Data and cuts
Dev: events closing before 2026-10-05 00:00Z (ts 1791158400), 19,495 markets (Aug 24 to Oct 4, 42 dates), W1/W2/W3 = thirds of its UTC dates. Held out: closes from 2026-10-05 (12,220 markets), the F1 frozen third, read ONCE behind `scan.guard_check`. Only counts were looked at.

## Entry (the harness, fixed choices)
Looks 840 to 180 s before the close (step 60). Both sides eligible, cheap side only: ask 3c to 30c (a NO buy at 1 minus the YES bid). One contract, taker at the ask, rounded fee, x1.2 stress, held to settlement. Features: the harness's Kalshi features (ask, bid, spread, d1 d2 d3 d5, rng5, vol, doi, nprev, hour) plus five cross-sectional ones computed from the five YES quotes of the same event at the same candle: `rank` (1 = highest YES ask among quoted tokens), `askshare` (this ask over the sum of the quoted asks), `askgap` (this ask minus the mean ask of the others), `overround` (sum of quoted asks minus 1), `nq` (tokens with a valid quote). Categorical: token (stored in the harness's `series` slot: BTC, ETH, HYPE, SOL, XRP = 0..4), hod4, dow. Bar unchanged: PF 1.5 in each of W1, W2, W3, floors 40 / 150 / 3 dates, deflated by the one-sided Bonferroni at 0.05 / N.

## Runs and N
One scan, 3 x 10,000 distinct rules, seeds 81401 to 81403 (30,000 rules). N about 1,350,505 plus the ladder scan's 30,000 (not yet run) plus these. Ledger before scoring. Survivors: freeze, audit, held-out ONCE.

## Prediction (before anything is read)
Zero survivors (about 90%). The over-round alone costs about 5c a contract, and RACELOCK T2 already lost at PF 0.77. A survivor must also hold on the held-out and be re-checked against the Nov data before anything is claimed. Zero closes the Coin Race cheap-side family. No promote verb.
