# NEWH11 result (V2 worker NEWH11, 2026-10-30, research only)

Registration `workers/NEWH11_REGISTRATION.md` (commit cb427dd, pushed before any quote after a signal or any outcome was read).
Code `src/scalper/newh11.py` (`counts` reads clocks, coverage and strikes only; `dv` scored once; `holdout` never run). Printout
`studies/newh11_result_2026-10-30.txt` (aggregates only). Nothing was changed after the score. Fees rounded up per order (C = 10 and
C = 1, x1.2 at C = 10). Fill at the next candle's ask (ending 780 s before the close), held.

**No rule passed discovery and validation, so no frozen holdout was read** (GOLDOPEN's 10-20 to 10-29, CMEGAP's 10-18 to 10-30).

## Step 1: the brief's families against the ledger

- Settlement-source mechanics (partly locked 60 s BRTI average, three-venue proxy, either side): TESTED as **BTCAVG** (and L9,
  LATECAL). No try.
- Strike placement: NOT APPLICABLE to the 15 minute markets. Information look I1: 8,158 KXBTC15M and 6,723 KXGOLD15M strikes carry
  all 100 cent endings, 1.0% and 0.9% whole dollars (the base rate), 0.0% on a $10 grid: the strike is the settlement source's value
  at the open, not a chosen level. The lagging-average strike is **L8**, round levels are **NEWH1**, the $100 hourly grid is
  **KINK** and **LAD1**. No try.
- Window-to-window persistence: TESTED (**S06, BTC1 CONT, S07, BK2, STREAK3, OPENLEAN, XLEAD1**, NEWH1 flip reversal). No try.
- Gold against COMEX at the open: UNTESTED at the first minute (GOLDFV1 is 10 and 6 minutes): **H1 GOLDOPEN**.
- Other family with a named counterparty: the CME weekend gap (needs-list item N6, never run): **H2 CMEGAP-W, H3 CMEGAP-R**.
- Declined, no try: Upbit premium (rule shape of COINPREM, FALSIFIED), Pyth gold (NOT_RUNNABLE, 401), spot depth (no history).

## Verdicts (PF at C = 10)

| Rule | Counterparty named | Discovery n / PF10 / PF1 / PF x1.2 / day z | Validation n / PF10 / PF x1.2 / day z | Verdict |
|---|---|---|---|---|
| H1 GOLDOPEN (gold window's first minute against the GC=F move since the strike minute; side with a 5c model edge, 10c to 90c) | gold opening quoters slow to a COMEX move | 54 (8 d) / 1.51 / 1.48 / 1.49 / +1.46 | 66 (7 d) / 0.79 / 0.78 / -0.75 | NOT_ENOUGH_DATA (54 against 100; validation 0.79) |
| H2 CMEGAP-W (weekend windows, Bitcoin at least 0.5% from the CME Friday close, buy toward it, 30c to 70c) | driftless weekend quoters vs gap-fill flow | 270 (9 d) / 0.98 / 0.97 / 0.96 / -0.20 | 234 (7 d) / 0.81 / 0.80 / -1.30 | FALSIFIED |
| H3 CMEGAP-R (Sunday reopen to Monday close, gap unfilled, buy toward it) | as H2, plus CME traders closing the gap | 18 (5 d) / 1.82 / 1.80 / 1.79 / +2.74 | 111 (6 d) / 0.85 / 0.84 / -2.12 | NOT_ENOUGH_DATA (18 against 100; validation 0.85) |

Win rate against price paid: GOLDOPEN 66.7% vs 57.1c (discovery), 48.5% vs 52.3c (validation); CMEGAP-W 51.5% vs 50.3c, 46.2% vs
49.3c; CMEGAP-R 66.7% vs 51.6c (18 trades), 49.5% vs 51.7c.

Funnels (all three windows): GOLDOPEN 1,840 windows, 1,538 no 5c edge, 100 skipped on COMEX data (29 bar gaps, 61 thin sigma, 10
jumps), 2 band, 200 trades (80 in the holdout, unscored). CMEGAP-W 2,352 windows, 1,513 gap under 0.5%, 166 band, 673 trades.
CMEGAP-R 1,104 windows, 339 gap under 0.5%, 490 already filled, 74 band, 201 trades. Validation CMEGAP trades were almost all NO
(yes share 0.02 and 0.00): Bitcoin sat above its Friday close through the validation weekends, so validation tests one direction.

**Zero volume both ways.** No signal or fill candle used had volume 0 in any rule; every PF is the same with and without.

## What it says

- **Gold at the open:** a 5c disagreement between the first Kalshi gold minute and a COMEX random-walk model fires on about 1 window
  in 9. Discovery looked good on 54 trades (PF 1.51) and validation reversed (0.79 on 66): the same pattern as GOLDFV1 at 10 and 6
  minutes. Kalshi's gold opening quote does not lag COMEX in a way 1 minute bars can show; with GOLDFV1 the gold-against-COMEX family
  is closed on the 30 days of free GC=F minutes (only a longer future history or Pyth itself could reopen it).
- **CME gap:** weekend Bitcoin does not drift back toward the CME Friday close (PF 0.98 and 0.81, win rate at or below price); after
  the Sunday reopen most gaps are touched early (490 of 1,104 windows already filled) and the unfilled ones lost in validation (0.85
  on 111). The folklore has no 15 minute edge on Kalshi.

## Count

**N added: 4** (3 tries: GOLDOPEN, CMEGAP-W, CMEGAP-R; 1 information look: I1 strike structure). Running count about 627,852
(after NEWH10) + 4 = **about 627,856**. Deflated one-sided z bar 5.24.

## Proposed README section (for the lead to merge)

## Result: NEWH11 (gold's opening quote against COMEX; the CME weekend gap on Bitcoin), 2026-10-30

Registered first (`workers/NEWH11_REGISTRATION.md`, commit cb427dd), result `workers/NEWH11_RESULT.md`, code `src/scalper/newh11.py`,
public data only (Yahoo GC=F 1 minute, Binance spot BTCUSDT 1 minute, local Kalshi candles); holdouts NOT read because nothing passed.
Family check first: the partly locked BRTI average is BTCAVG, window-to-window persistence is S06, BTC1, BK2 and OPENLEAN, and strike
placement does not apply to the 15 minute markets (strikes are full-cent settlement values, no grid; round levels are NEWH1), so no
try was spent there. **GOLDOPEN** (first minute of each gold window against the GC=F move since the strike minute, side with a 5c
model edge, next-candle fill): PF 1.51 on 54 then 0.79 on 66, **NOT_ENOUGH_DATA** (with GOLDFV1, gold against COMEX is closed on the
free 30 days of minutes). **CMEGAP-W** (weekend Bitcoin at least 0.5% from the CME Friday close, buy toward it): 0.98 / 0.81 on 270 /
234, **FALSIFIED**. **CMEGAP-R** (after the Sunday reopen while the gap is unfilled): 1.82 on 18 then 0.85 on 111, **NOT_ENOUGH_DATA**.
N +4; running count about 627,856 (z bar 5.24).
