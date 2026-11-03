# VENUES1 registration (Strategy Research V2 worker, 2026-11-03, written before the result file)

Owner assignment via main. Desk research plus measurement from held data. Assumed account: $800. No live code, no functions/, no L1, no OICORE, no promote verb, no new try (N about 728,700, unchanged). Jurisdiction and legality are the owner's call and are stated as questions, never assumed.

## Venues to assess (one row each)
1. Crypto perpetual funding / cash-and-carry (FUND1, PERP1-3) re-checked at MAKER fees, using the held Hyperliquid funding file (`data/fund1_hl.json`), the `perp-data` branch of Kalshi perps if readable, and public fee schedules.
2. Options volatility risk premium on Deribit (DERIBIT-IMPLIED registration and its recorder on `quote-data`): what $800 of margin allows (naked short vs defined-risk spreads), what edge evidence is held.
3. Polymarket-only edges (PM1, PM2, PM3, XVENUE1): evidence held, US access status as an owner question.
4. Spot crypto / equity arbitrage (cross-exchange, triangular, ETF vs basket).
5. Funding basis / dated futures basis.

## Columns for each
Minimum capital, fees, edge evidence held (README ids), feasible on $800 yes/no and why, API / keys / jurisdiction actions for the owner. The report says plainly what is NOT feasible.

## Computed from held data (only these)
- FUND1 yield recomputed by year only as arithmetic on the already-run result (no new test): net of a maker-fee round trip (maker 0.02% a side perp, spot 0.0-0.1%) and of the 0.94% taker cost, amortised over 12 months, and dollars per year on $800 at 1.2x capital. Labelled information, not a try.
- Margin arithmetic for Deribit short options and spreads at $800 using public contract specs (no recorded Deribit outcome is read; the recorder has no read before 2027-01-01).

Result: `workers/VENUES1_RESULT.md` and a README ledger entry.
