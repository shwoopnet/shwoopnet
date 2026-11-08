# HISTLAD1 PROTOCOL (registered Nov 8, 2026, before any outcome is read)

Research only. No trading code, no key, no order. Public Kalshi /historical (keyless) and the Binance Vision 1-minute spot data already held.
**This is a disclosed EXTENSION, not a new mechanism** (main's approval, Nov 8 about 8:30 AM CT, with conditions): the favourite-longshot story is L1's (`research/MECHANISMS.md`). Prior tries on this ladder, counted in the history already: E4 (L1's rule on KXBTCD, 14 days, FALSIFIED / low power) and LAD1 (option-style fair value on KXBTCD middle strikes, ask 10c to 90c, 30 days, 6 tries, all FALSIFIED). New here: the cheap tails (ask 3c to 30c), which LAD1 excluded, on about 62 days of /historical. ONE registered scan, not a family of variants. A zero closes the ladder tail idea for good and goes in MECHANISMS.md.
Quote-regime caveat on every result: Kalshi /historical, Jul to Sep 2026; Binance spot is the underlying proxy, not the CF Benchmarks settlement average.

## Data and cuts
Hourly Bitcoin ladder `KXBTCD`, markets closing 2026-07-09 00:00Z (ts 1783555200) to 2026-09-08 00:00Z (ts 1788825600). Development: closes before 2026-08-19 00:00Z (ts 1787097600), W1/W2/W3 = thirds of its UTC dates. Held out: closes from 2026-08-19, behind `scan.guard_check`, read ONCE.
Strike choice uses Binance only, never a Kalshi price: for each hourly event closing at T, S_ref = close of the Binance 1-minute bar ending T-45 min; the 5 listed strikes at or below S_ref nearest to it and the 5 above nearest to it are fetched (10 per event). Candles from T-55 min to T-3 min. A strike with no result is dropped.
NOT_ENOUGH_DATA rule (main's condition): if the dev region has fewer than 150 distinct hourly events with at least one cheap-side row, NO rule is scored and the result is NOT_ENOUGH_DATA.

## Entry (the harness, with these fixed choices)
Looks 2700, 1800, 900, 600 s before the close (candle ending exactly then). Both sides eligible; cheap side only: ask 3c to 30c (a NO buy at 1 minus the YES bid). One contract, taker at the ask, fee `ceil(0.07 p (1-p) 100 - 1e-9)` cents, stress x1.2, held to settlement. Features: the harness's Kalshi features (ask, bid, spread, d1 d2 d3 d5, rng5, vol, doi, nprev, hour; series, hod4, dow) plus two Binance-derived, defined now: `zk` = |ln(S/K)| / (sigma sqrt(tau)) and `fvgap` = fair probability of the side bought minus its ask, with S = Binance close of the bar ending at the decision minute, K the strike, tau = minutes left plus 1/3 (the 60 second settlement averaging), sigma = standard deviation of the last 60 one-minute log returns, fair YES = Phi(ln(S/K) / (sigma sqrt(tau))), fair NO = 1 minus that. Bar unchanged: PF 1.5 in each of W1, W2, W3, floors 40 / 150 / 3 dates, z deflated by the one-sided Bonferroni at 0.05 / N.

## Runs and N
One scan of 30,000 distinct rules (seeds 81301, 81302, 81303 of 10,000 each), N 1,350,505 to about 1,380,505, z about 5.39. Ledger before scoring. Survivors: freeze, audit (7 hooks), held-out read once.

## Prediction (before anything is read)
Zero survivors (about 90%): the ladder is quoted by firms that run the same lognormal model, the fee at cheap prices is small but the tails are priced from the smile, and LAD1 found the middle strikes 2c to 4c negative. Expected pooled cheap-side net -3c to -6c per contract. A survivor would first have to hold on the Aug 19 on held-out and on a rerun against the fresh Oct data before anything is claimed. No promote verb.
