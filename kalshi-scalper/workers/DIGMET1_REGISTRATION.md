# DIGMET1 registration (2026-11-06): digital-metric markets with a partially observable public count at the look

Written before any price, candle or outcome was read. Only listings (event tickers, close times, volume) were counted, before the frozen cut 2026-10-03T16:00Z (`workers/DIGMET1_CENSUS.json`).

**Ledger check.** Grep of README for CHART1, SPOTD1, APP1, COUNT1D, COUNT2, EARNPR1, MENT1, BOXOFF1, EARN1, Netflix, Spotify, Rotten, Metacritic: covered are Netflix and Billboard weekly rank (CHART1, NOT_RUNNABLE, no daily history), Spotify daily chart winners (SPOTD1, FALSIFIED, 484+ events), Truth Social counts (COUNT1/1B/1D), tornado counts (COUNT2), approval ladders (APP1, APPROVAL1), earnings word markets (MENT1, EARNPR1), company KPIs (EARN1, NOT_RUNNABLE), box office (BOXOFF1). Not tried: Spotify total-stream thresholds (`KXMW*`, `KXSPOTIFYSONGS*`), Rotten Tomatoes score, Metacritic, App Store rank, YouTube charts, Google Trends, Ornn GPU index.

**Question.** Where a market resolves from a public number that is free and timestamped at the look, does the partial count (outside fact) lift the cheap side (ask 3c to 30c, held to settlement, fee 7% x C x p x (1-p) rounded up, C=10, taker at ask) by at least 6c over the pooled cheap-side baseline (about -5.5c to -6c)?

**Counterparty.** Retail traders pricing a threshold without reading the live count.

**Universe, fixed before any outcome.** The families above with at least 100 settled events before the cut AND a free, dated historical partial-count source. Gate is checked on the source, not on prices.

**Numeric prediction.** If runnable: cheap-side net mean of -6c to -3c, no lift of 6c; PF below 1.

**Kill criteria.** NOT_RUNNABLE if no free dated source for the partial at the look exists; NOT_ENOUGH_DATA if fewer than 100 independent events with source; otherwise FALSIFIED if net mean lift under 6c or z (event-clustered, halves D1/D2 both positive) under the deflated bar about 5.32.

**N.** One family question tried, +1 (running about 730,491, plus PERPGEN 500,000; bar about 5.32).
