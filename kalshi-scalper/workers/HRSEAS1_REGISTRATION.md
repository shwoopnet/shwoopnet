# HRSEAS1 registration: hour-of-day and day-of-week seasonality of the cheap tail on the HOURLY Bitcoin ladder (written 2026-11-03, before any trade, win rate or PnL of this rule was computed)

Worker HRSEAS1, Strategy Research V2. Research only: no `functions/`, no L1, no OICORE, no promote verb. Code `src/scalper/hrseas1.py` and tests `tests/test_hrseas1.py` (synthetic, plain runner) are committed with this file; result `workers/HRSEAS1_RESULT.md`. Times are UTC in code, US Central in words only where stated.

**Plain statement.** The likeliest outcome is NOT_ENOUGH_DATA by count, with the sign test already against every block. The unconditional cheap tail loses (VOLGAP1 / LADLONG1 / OIHR1 control: PF 0.64 to 0.80). This asks only whether SOME clock block is different.

## 1. Duplicate check (done first; README and workers read)
- **TODSEAS1** (`workers/TODSEAS1_REGISTRATION.md`): time-of-day on the NON-crypto 15 minute slots, FALSIFIED. Same idea of a clock effect, different market, different trade.
- **LADLONG1** (BTC hourly, 94c to 98c wings at 45 minutes) and **NEWH4 TAIL** (2c to 6c longshots at 30 minutes): unconditional, all hours pooled; neither split by hour of day or weekday. Same family of contracts, different look, band and no clock.
- **VOLGAP1** (cheap tail when 5-minute realised vol is 1.5x the ladder's implied vol; PF of the unconditional tail 0.64 to 0.72), **PERPOI1** (perp OI surge trigger), **OIHR1** (ladder open-interest jump trigger; control PF 0.80/0.64, FALSIFIED), **LADFADE**, **LAD1/LADL1** (model-based, sigma from DVOL or realised), **HOURLY1** (SOL, XRP, DOGE, HYPE hourly, spot model): all use an event or model trigger, none uses the clock. Their uniform "control" cells are the all-hours baseline I compare against.
- `grep -iE "hour.of.day|seasonal|weekend|us open|asia" README.md workers/*.md`: only TODSEAS1 (non-crypto) and L1-side time-of-day cuts on 15 minute gold; none on the hourly BTC ladder.
**Same:** contracts, band 3c to 30c, hard limit 0.30, hold to settlement, ladder makers as counterparty, fee, C = 10, `data/conf2_lad.sqlite`. **Different:** the only conditioning variable is the CLOCK (hour of the close, weekday), decided before any outcome. **Not a duplicate; but the pooled cell is already known to lose.**

## 2. Mechanism and counterparty
Realised crypto volatility is strongly seasonal (US cash open, Asia open, London open, funding times, the weekend lull). A ladder maker who quotes a near-constant volatility would sell tails too cheap in high-vol blocks (tail wins more than its price) and too dear in low-vol blocks (tails lose more; then the favourite 85c to 97c side is underpriced). Counterparty: the maker selling the 3c to 30c tail (high-vol blocks) or the favourite's opposite side (low-vol blocks). Honest alternative: makers already know the clock (many are the same desks that trade the perp), the tail is priced fairly, and the fee and spread are the whole loss in every block. Prior for a pass: low.

## 3. Data (fixed)
`data/conf2_lad.sqlite`, KXBTCD hourly markets with a stated `result`, 1 minute bid/ask candles from 55 minutes before each close: 956 closes with a result, 2026-08-24 to 2026-11-03 (a count, read before this file; no outcome tabulated). KXETHD: 14 days only, not runnable (no history, so not tested). The `quote-data` branch `book/` recorder (5 levels every 3 s) started 2026-10-29: a forward-only source for a probe, not used for the read. No new fetching: the local cache is the only source; the public API's older KXBTCD hours were not fetched (a fetch would add months, not blocks, and other fetches are running).

## 4. Blocks (fixed now, by the UTC hour of the hourly CLOSE, from known clock events; overlap allowed only where marked)
| Block | Closes (UTC) | Why |
|---|---|---|
| ASIA_OPEN | hours 00, 01, 02 | Tokyo/Asia open |
| NIGHT_LULL | 03 to 06 | US late evening / Asia mid-session, quietest hours (low-vol, mirror also tested) |
| LONDON_OPEN | 07, 08, 09 | London/Europe open |
| US_OPEN | 13, 14, 15 | US cash open (13:30 UTC in EDT, 14:30 in EST) and first hour |
| US_CLOSE | 19, 20, 21 | cash close 20:00 UTC (EDT) |
| FUNDING | 00, 08, 16 | perpetual funding times (overlaps ASIA_OPEN and LONDON_OPEN by design, counted separately) |
| WEEKEND | any hour, close on Saturday or Sunday UTC | weekend lull (low-vol, mirror also tested) |
Control for a block = the same trade at every close NOT in that block (same half). Baseline = the same trade in all hours.

## 5. Trade (fixed)
For each hourly close C with a ladder, look t = C - 1500 s (25 minutes before). Needs at least 4 strikes quoted in the candle ending at t. **Selection from the candle ending at t; fill at the ask of the candle ending at t+60 (the next minute), never the look candle's own quote.**
- **TAIL (all 7 blocks):** per side, the strike with the HIGHEST (nearest the money) price in [0.03, 0.30] at t: YES at ask, NO at 1 - yes_bid. Up to two trades per close (one YES, one NO). Hard fill limit 0.30 (no fill otherwise). Held to settlement, C = 10 contracts, taker.
- **FAV mirror (NIGHT_LULL and WEEKEND only; a separately counted try):** per side, the strike whose price is nearest 0.90 inside [0.85, 0.97]; hard fill limit 0.97. Same fill, hold, C.
- Fee 7% x C x p x (1-p), rounded up to the cent (round to 1e-9 first); fees x1.2 shown. A trade that does not fill is no trade.

## 6. Splits and holdout
Closes sorted by date T0..T1 (956 closes). Development = closes before T0 + 2 (T1-T0)/3; half 1 = before T0 + (T1-T0)/3; half 2 = the rest of development. **The last third (W3, closes at or after T0 + 2 (T1-T0)/3) is never computed by the code and stays unread.** One run only; `run` refuses a second (`data/hrseas1_score.json`).

## 7. Numeric predictions (before any outcome)
- Baseline tail (all hours): win rate 14% to 18% against a mean price 17c to 21c; net -3c to -6c per contract; PF 0.65 to 0.85 (prior cells 0.64 to 0.87).
- Every block's PF in half 1 and half 2 below 1.5; at most two blocks above 1.0 in a half; block-minus-control within +-6c in each half (n per half 20 to 90 trades, noise dominates).
- Trades per block in development (tail): 100 to 300 for the 3 and 4 hour blocks, about 330 for WEEKEND; the 150 floor not met by the 3 hour blocks except possibly some. FAV: win rate 1 to 3 points under the price paid, PF under 1.0.
- Verdict: no block passes. FALSIFIED where n is 150 or more; NOT_ENOUGH_DATA where under 150 (months to go reported), with the kill rule noted as already firing.

## 8. Bars and kill rules (decided now)
Per block (tail and FAV counted separately):
- **PASS_DEVELOPMENT** needs, in BOTH halves: PF at least 1.5 after fees, and block-minus-control net per contract positive, with at least 150 development trades; only then is W3 read once. Even then the family-wise bar (about z 5.27 after the running N) must be met on forward data before any live use.
- **FALSIFIED** if any block's PF is under 1.5 in either half, or block-minus-control is not positive in both halves, with at least 150 development trades.
- **NOT_ENOUGH_DATA** under 150 development trades: the months to 150 are reported at the observed rate; the kill rule is reported alongside if it already fires. Family verdict: FALSIFIED if no block passes.
- A bootstrap by close (block minus control, 5th and 95th percentile) is reported; ties in the number of tries are not tuned away (no second block definition, no moved look, no other band).

## 9. Probe spec (only if some block is positive in both halves with a mechanism)
1 contract, hard limit 0.30, that block's closes only, tail side per the rule, kill rule (stop at the first of: 3 losses in the first 12 fills beyond the expected, or net under -$1.50, or 40 fills), worst day = (number of closes in the block per day, up to 3) x 2 sides x 30c = about $1.80. When 40 fills would exist: at about 0.9 fills per close x closes per month, stated in the result. Not otherwise written.

## 10. Count
**N +18**: nine registered slots (7 tail blocks, 2 FAV mirror blocks) at +2 each. Expected read date: the development read runs once right after this push (2026-11-03); the forward read needs about 150 block trades, months-to-go reported in the result.
