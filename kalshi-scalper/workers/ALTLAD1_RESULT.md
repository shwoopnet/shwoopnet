# ALTLAD1 result (run 2026-11-04; registered in 645e2ff, sha256 `4e8c2f6e1e150bd9cb88adbbdf38f758652be764d50d3d76157be4634cbd47c8`, before any candle or outcome; `src/scalper/altlad1.py`, `tests/test_altlad1.py`, printout `studies/altlad1_result_2026-11-04.txt`)

**Rule A (30 minutes before the close): NOT_ENOUGH_DATA (29 treated trades, bar 150). Rule B (10 minutes): NOT_ENOUGH_DATA (104 trades), and rule B is clearly losing, not a near miss.** W3 (from 2026-10-03T16:00Z) never listed, fetched or joined. Not a pass, no promote verb. N +4. Cheap side only (ask 3c to 30c); no favourite-side result was computed or printed.

## Duplicate check
HOURLY1 (2026-11-02) tested the same four hourly alt ladders with a lognormal at 10 minutes and BANNED entries under 0.20, so the cheap side was the untested cell; it is not an exact duplicate, but HOURLY1's verdict (model Brier worse than the quote mid; SOL PF 0.90) is the prior and it held. COMDAY1 and the other priors carried.

## Census (listings and close times only, before any candle)
Alt ladder series with settled markets before the cut: KXSOLD 860 hourly events (249,750 markets), KXXRPD 860 (63,440), KXDOGED 860 (45,542), KXHYPED 860 (145,875), KXBNBD 860 (63,330), KXSHIBAD 36 daily events (1,046), 2026-08-28 to 2026-10-03 (37 UTC dates), 4,336 events. No market at all (dead or empty): KXZECD, KXZECH, KXNEARD, KXNEARH, KXTOND, KXTONH, KXXLMD, KXRIPPLED, KXLINKD, KXDOTD, KXAVAXD, KXLTCD, KXBCHD and the weekly KXZECHW, KXNEARW, KXTONW (NOT_RUNNABLE, dropped). Event count passed (4,336 against 150); the binding limit is the treated trade count, which only quotes can show (the markets listing gives the history only from 2026-08-28).

## Data actually scored
OKX 1 minute klines (53,200 per coin), df of the t tail fitted on the first two thirds of dates from OKX alone: 4 for both looks (n 2,844 events). Strikes with model P between 0.03 and 0.97: 12,008 tickers in 3,697 events; Kalshi candles fetched for ALL of them (full coverage, nothing sampled). Events with a model 4,336 per look.

## Numbers (C = 10, fee 7% x C x p x (1-p) rounded up, taker at the quote in force at D+60)
| | n | days | PF | mean | day/event-clustered z |
|---|---|---|---|---|---|
| A treated W1 | 7 | 5 | 0.00 | -10.51c | -4.37 |
| A treated W2 | 22 | 21 | 2.17 | +4.71c | +0.76 |
| A treated pooled | 29 | 26 | 1.18 | +1.03c (x1.2 W1 -10.64c, W2 +4.67c; +1c slip -0.00c) | +0.21 |
| A control (all cheap strike-sides) W1 / W2 | 2,836 / 4,464 | | 0.70 / 0.75 | -3.83c / -3.10c | -6.12 / -5.57 |
| B treated W1 | 29 | 28 | 0.00 | -6.80c | -9.95 |
| B treated W2 | 75 | 72 | 0.42 | -3.39c | -1.85 |
| B treated pooled | 104 | 100 | 0.29 | **-4.35c** (+1c slip -5.39c) | -3.22 |
| B control W1 / W2 | 1,618 / 2,672 | | 0.58 / 0.60 | -5.04c / -4.74c | -7.42 / -8.53 |

Rule B treated win rate 1.9% against a mean price 0.058 and a model probability 0.217 (the model is 20 points too high). Rule A treated 6.9% against price 0.054 and model 0.227. Per series (descriptive): rule B HYPED 44 trades -0.9c, SOL 38 -7.4c, XRP 12 -5.3c, BNB 8 -7.0c, DOGE 2; SHIB 0. Rule A W2 (+4.7c, 22 trades) against W1 (-10.5c, 7 trades) is noise on 29 trades. The only treated-above-control reading is rule A W2 (+4.7c against -3.1c); it is below the count bar and not a finding.

## Calibration (the information that matters), W1+W2, every cheap strike-side
- Rule B, ratio at least 3: n 104, price 0.058, **win 0.019**, model t 0.217 (Gaussian 0.260). By model p: 0 to 0.09: win 5.0% vs price 8.2%; 0.09 to 0.2: 8.7% vs 13.8%; 0.2 to 0.4: 14.9% vs 19.9%; above 0.4: 25.5% vs 24.2% (n 137).
- Rule A, ratio at least 3: n 32, price 0.055, win 0.062, model 0.242. Ratio under 3: win rate 3 to 5 points under the price.
Cheap alt-ladder strikes lose at almost every model bucket (win 3 to 5 points under the ask), the same favourite-longshot loss as COMDAY1, VOLGAP1 and IDXFUT1; the fat tail does not rescue the model, it raises the model probability further above what the quoters know. Both looks agree with HOURLY1: the model is least right exactly where it disagrees most with the quote.

## Counts and the forward plan
Treated trades per development date: rule A 0.78 (about 191 more days to 150), rule B 2.81 (about 53 days to 150). Because the sign is negative with n over 100 in rule B (pooled -4.35c, PF 0.29, control also negative), a forward read of rule B is NOT planned: it would only be spent on a rule whose development read is already FALSIFIED in the direction (it fails the registered kill lines on both windows, but the count rule makes the verdict word NOT_ENOUGH_DATA, as registered). Rule A cannot reach 150 in under six months at one hourly alt book; **forward read on or after 2026-12-04 is registered as a dated optional look only, for rule A and B together, if the owner wants the count (no recorder needed: Kalshi candles and OKX klines are retrievable later)**. The frozen holdout stays untouched.

## Limits and disclosures (none changes the verdict word)
- **Code bug found after the first scored run, fixed, and the run repeated on the same data and rule:** `net_c` compared the stored result `'y'/'n'` with `'yes'`, so every NO trade counted as a win in run 1. Run 1 (buggy, preserved as `studies/altlad1_run1_BUGGY_not_valid.txt`) showed treated +25c / +32c, which is the symptom of the bug (win rate 1.9% cannot make +32c). The calibration and win-rate lines were never affected (they used `'y'`); trade counts, selection and verdict word were identical in both runs. A test that fails on the old code was added (`test_net_includes_fee_and_slip`). The corrected run is the only valid result; this is a mechanical coding error, not a rule change.
- Candle fetch used two threads (a second walked the md5 event order from the far end) for speed; logistics only, full coverage reached (12,008 of 12,008 tickers).
- The df of the t tail was fitted on the first two thirds of the dates (OKX only); W2 overlaps the second half of that fit window (OKX only, no quote or outcome), as registered.
- One venue (OKX USDT) is not the CF Benchmarks index; the basis is unmeasured. A quote is not a fill; taker at the quote is generous. The sample is 37 days (the markets listing begins 2026-08-28), one regime.
- Only the 30 and 10 minute looks, df grid and cheap band were run; no variant.

Reading: duplicate in spirit of HOURLY1/COMDAY1, new in the cheap side and the 30 minute look, and it fails the same way. Altcoin ladders priced from an outside spot with a fat tail are not an edge on the cheap side; the wings are priced by the quoters, and the quotes are closer to the outcome than the model.
