# FALS4 registration: falsifier for GEN6's open interest core (Bitcoin cheap side at 180 s after an open interest jump), research only

Written 2026-10-30 by worker FALS4 and pushed BEFORE any FALS4 scoring. Before this commit I read: `workers/RULES.md`, `workers/GEN6_RESULT.md`, `workers/candidates/REF_GEN6_OICORE.json`, `workers/FALS3_RESULT.md`, the spec lines of `workers/GEN6_REGISTRATION.md` (look, side, fill, fee and date definitions; no code), `src/scalper/paths.py`, the table schemas and Bitcoin close ranges of `data/l1b`, `book`, `fresh`, and the candle rows of ONE Bitcoin window (Sep 7, 22:30, to see the offsets and the `oi` column). I have NOT read `src/scalper/gen6.py`. My scorer `src/scalper/fals4.py` is written from the raw candles first; gen6.py may be read afterwards only to explain a gap, and the result will say so.

## The claim under test

`KXBTC15M`. Signal candle = the 1 minute candle with `end_ts = close - 180`. Cheap side = the side whose ask at the signal candle is in [0.05, 0.50] (YES ask = `ask_c`, NO ask = 1 - `bid_c`; YES tried first). Condition: `doi > 86,299.56`, doi = `oi(signal candle) - oi(candle ending close - 360)`. Fill = the next candle's (end close - 120) closing ask of that side; a missing next candle = no trade. Hold to settlement (`market.result`). GEN6: discovery PF 2.28 (n 222), validation 1.85 (n 333, z 4.53).

**Counterparty (as claimed):** late favourite buyers in the last minutes (bots like L1) who overpay for the near-certain side when a wave of new contracts arrives; FALS3 measured the Bitcoin favourite at 180 s at PF 0.77 over 85 days.

## Data and windows (by close time, UTC)

Every settled Bitcoin window in `data/l1b.sqlite`, `book.sqlite`, `fresh.sqlite`, a ticker in two files taken once (first file in that order). DISCOVERY 2026-08-06 to 2026-09-20; VALIDATION 2026-09-21 to 2026-10-27 23:59:59. Nothing closing on or after **2026-10-28 00:00 UTC** is loaded (the SQL filters on `close_ts`); the forward window is the third window and is NOT read by FALS4. Fees 7% x C x p x (1-p) rounded up to the cent per order, C = 10 headline, C = 1 reported, fees x1.2 (multiplied before rounding). Zero-volume signal or fill candles reported both ways.

## Checks (all fixed now)

1. **Re-implementation.** Trades and PF (C = 10) per stage, also day-clustered z. A gap over 10% in trades or 0.15 in PF is explained (after which, and only then, gen6.py may be read).
2. **Look-ahead audit.** (a) What `oi` on a candle means: compare `oi` against the cumulative candle volume pattern and the post-close candle (does the candle ending at the close already hold the final oi; does the `+60` placeholder repeat it), i.e. is oi an end-of-candle snapshot. (b) The fill candle starts at close - 180, the moment the signal candle ends, so the signal is usable only if oi is known at its candle's end; FALS3 found closing quotes match the recorder about 5 s after `end_ts`, so I also score a **one candle later** version (signal oi as before, fill at the candle ending close - 60) as a latency stress. (c) Missing candles: rate of windows lacking the signal, the -360 or the fill candle, and the YES rate in windows with and without gaps; result joined by ticker, not by close time (check the ticker's time part equals `close_ts`). (d) The band filter uses only the signal candle (verified in code; also a variant that additionally requires the fill-candle ask in [0.05, 0.50]).
3. **Costs.** C = 10, C = 1, fees x1.2; fill at the SIGNAL candle's ask + 1c and + 2c.
4. **Fill realism.** PF with fills under 5c excluded; share of trades whose fill candle volume is under 10 contracts.
5. **Threshold drift (information).** Threshold = 90th percentile of doi at 180 s over all Bitcoin windows (any side, valid doi) closing in the 30 calendar days before the window's day (earlier days only; at least 10 days of history, else no trade). PF per stage.
6. **Stability.** PF per 8 day block from Aug 6 (last block may be short, ends Oct 27); longest run of consecutive losing trades; longest stretch in days without a new equity high.
7. **Counterparty (1 try).** In the same windows (doi > 86.3k and a cheap side existing), buy the OTHER (favourite) side at the next candle's ask, held. **Prediction: PF below FALS3's 0.77 in both stages (I expect 0.45 to 0.70).** Note now: this is close to mechanical (the favourite is the cheap side's complement minus two half-spreads and fees), so a confirmation is weak evidence; a favourite PF at or above 0.77 would be strong evidence against the counterparty story.
8. **Proxies at matched counts.** Cheap side at 180 s, held, no doi condition, under: (a) volume over the same 3 candles (end -300, -240, -180) above a threshold; (b) |side mid change from -360 to -180| above a threshold; (c) time of day: random cheap-side entries resampled to the core's UTC hour mix, 2,000 draws, median PF. For (a) and (b) the threshold is set so the DISCOVERY count equals the core's discovery count, then applied unchanged to validation. Also the core restricted to below-median and above-median 3 minute volume (does doi add anything given volume).

## Predictions

Check 1 reproduces within the 10% / 0.15 tolerances (70%). Check 2 finds no leak (75%), but the latency stress costs PF (validation 1.2 to 1.6). Check 3: + 2c signal fill keeps PF above 1.3 in both stages (60%). Check 4: excluding sub-5c fills lowers PF to 1.3 to 1.8. Check 5: drift threshold validation PF 1.3 to 1.9. Check 6: at least one 8 day block below 1.0 (65%). Check 8: no proxy matches the core in both stages (60%); volume is the likeliest to come close.

## Verdict rules (fixed now)

- **BROKEN** if any of: the re-implementation gives PF below 1.3 in either stage and the gap is not a definitional choice; a look-ahead is found and the fixed version has PF below 1.2 in either stage; signal ask + 2c gives PF below 1.0 in either stage; excluding sub-5c fills gives PF below 1.0 in either stage.
- **CHANGED** (say what) if not BROKEN but any of: a proxy at matched count reaches at least the core's PF minus 0.1 in BOTH stages (the rule is really that proxy); the latency stress or + 2c fill gives validation PF below 1.3; the drift threshold gives validation PF below 1.3; fewer than half the 8 day blocks have PF above 1.0; a reproduction gap that changes the definition.
- **SURVIVES** otherwise. RULES words alongside: with only two history windows and z below the bar, the most this can earn is NOT_YET_FALSIFIED (forward decides); a BROKEN maps to FALSIFIED.

## Tries (N)

Each scored variant counts 1: re-implementation 1; look-ahead variants (latency, fill-band) 2; costs (C = 1, x1.2, +1c, +2c) 4; sub-5c exclusion 1; drift 1; stability 1; favourite 1; proxies (volume, move, hour, volume split) 4. Planned N added = **16**; the result reports the exact count. Running count before FALS4 about 563,336.
