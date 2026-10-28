# No-view mechanisms already tested on the Bitcoin, Ethereum and gold contracts (2026-10-28)

"No view" = profit that does not depend on predicting direction. Sample, verdict, what blocked it. Everything else in the README (about 22,100 variants) is a directional view (a price pattern, a fair value, a forecast, a filter) and does not belong on this page.

| Mechanism | Tested? | Sample | Verdict | What blocked it |
|---|---|---|---|---|
| Lock across mutually exclusive legs of one event (sum of legs below $1 after fee) | ARB1 | 12 scans of every open event, 5,070 to 5,430 usable events per scan (Bitcoin and Ethereum ladders inside them) | FALSIFIED: zero locks of 1c or more at 10 contracts; the largest was -0.12c | Nothing; market makers keep the sums at arithmetic |
| Lock between strikes of one ladder (YES low strike + NO high strike), including Bitcoin, Ethereum, gold hourly ladders | Snapshot 2026-10-26 00:35 UTC | 4,064 strike pairs | Zero locks after fees | One snapshot only; how long a lock lives and whether one appears at the instant of a move was never measured |
| Cross-contract consistency, hourly ladder against the 15 minute mid | XM1 | 1,896 windows, 40 days (traded toward the ladder's implied price) | FALSIFIED: Bitcoin -2.05c, Ethereum -7.45c | It was a directional trade on the gap, not a lock; the two contracts do not settle on the same number except at coincident closes |
| Cross-venue consistency (Polymarket against Kalshi) | PM1 (2026-10-13), PM1 (2026-10-27) | 7,584 15 minute windows; 20 days of noon strikes | Blend worse than Kalshi alone; noon-strike test could not be made (no quotes) | Polymarket is the worse price; strike grids do not match |
| Two-sided passive quoting (market making) | MAKER1 | Tennis only: 4,300 to 4,500 postings, 228 matches | FALSIFIED: Q=1 zero fee +0.22c per fill, queue Q=100 and 300 negative, adverse selection | **Never tested on Bitcoin, Ethereum or gold** |
| Resting-bid entry instead of the ask | MAKER2, MAKER3 | 28,873 opportunities | FALSIFIED: the fills are the dips (adverse selection), hybrid loses 0.5c to 0.8c | These were L1 entries (one-sided, with a view), not two-sided quoting |
| Hedged positions against spot, the perpetual or Deribit | None as a hedge | n/a | **UNTESTED** | Deribit and Binance data were used only as directional views (IV1, LAD1, SEARCH5K, FACT1, FLOW1, PERP3, PERPFLOW1: all FALSIFIED) |
| Volatility structures (long or short several strikes, ranges) | None | n/a | **UNTESTED** | It is a view on volatility, not a lock; needs a vol forecast |
| Fee and rounding quirks | QUIRK1, feerounding | 28 cells | FALSIFIED | Rounding gains are under 0.1c |
| Settlement-averaging structure (the 60 second BRTI average) | L8, L9 (model tests) | Bitcoin 15 minute windows | Directional; no standalone edge | It changes pricing near the close, not a lock |

**Untested for Bitcoin, Ethereum and gold:** two-sided quoting with an explicit queue and adverse selection; persistence (seconds) of any lock; strict locks between the 15 minute contract and the hourly ladder at coincident closes; hedged positions; volatility structures.

**Data on file for them:** the recorder branch `origin/quote-data` (25 runs, 2026-10-22 to 10-28, about 850 windows): the last 150 seconds of each 15 minute window for Bitcoin, Dogecoin, Ethereum and Solana, best bid and ask with sizes about every 0.6 seconds, plus the spot and the result. **Gold and the hourly ladders are not recorded.** No trades are recorded; the public trade tape (`/markets/trades`) supplies them.
