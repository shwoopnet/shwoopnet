# FXREF1 result (2026-11-03): NOT_RUNNABLE

Registered first: `workers/FXREF1_REGISTRATION.md` (sha256 `5007b580578c728d8b36046bf82559d9399b17d6fb05631d5593bec2983b6bbd`, pushed before anything else). Code `src/scalper/fxref1.py`, synthetic tests `tests/test_fxref1.py` (5 pass). No outcome was joined, no reference price was fetched, the frozen third (closes from 2026-10-03T16:00Z) was not touched.

## Why
- **Duplicate check:** not a duplicate in cell (H7 is Bitcoin both sides; CMD1 is commodity dailies both sides; E5 and FXUSD use L1 or USD direction), a near relative in mechanism of two FALSIFIED tests.
- **Reference gate failed:** no free minute reference exists for the pre-cut history. Yahoo 1 minute is about 7 days (all after the cut), Yahoo 5 minute is about 60 days (from about 2026-09-04, and not minutes); Stooq and Dukascopy are unreachable from this host (connection reset); Yahoo answered HTTP 429 and I did not work around it. WTI and gas pre-cut history starts 08-06 and 08-27, FX 09-23 (AUD/USD and USD/CAD have no pre-cut markets at all).
- **Census (stored Kalshi prices at the 600 s look, no result column):** cheap-side quotes (ask 3c to 30c): WTI 1,919 of 4,146 markets, gas 1,062 of 2,606, EUR/USD 271, GBP/USD 256, USD/JPY 283 of 649 each. The treated count (model at least 3x ask) cannot be known without the reference; NOWCAST1's analogous 3x rule left 12 trades of 86 releases, and a well-calibrated model on liquid references rarely disagrees 3x, so the expected treated count is likely well under 150 for FX and uncertain for WTI and gas.

## Verdict and plan
`NOT_RUNNABLE` (reference history). Win vs price and PF vs control: not computed. Forward plan: a keyless daily Yahoo 1 minute recorder for the seven symbols to the `quote-data` branch (not built here), one frozen read on or after 2026-12-15 under the unchanged rules; `NOT_ENOUGH_DATA` if under 150 treated trades. N +2.
