# TSLM1 result: shock then calm, cheaper side held to settlement (2026-11-03)

Registered and pushed first (`workers/TSLM1_REGISTRATION.md`, commit ab919bd, before any count or outcome), Amendment 1 pushed before any outcome (commit 32f9fd4), scored once with `src/scalper/tslm1.py` (`python -m scalper.tslm1 score`; refuses a second run; raw `data/tslm1_score.json`, not committed). Tests: `tests/test_tslm1.py`. **Disclosure:** the only change after registration is Amendment 1 (the trailing 95th percentile and median use only changes ending 840 to 180 s before their own market's close, because including the closing collapse made the 95th percentile 0.4995 and the trigger fire 17 times); made after an outcome-free count, before any result was read. Nothing changed after that.

## Verdict: PRIMARY FALSIFIED; LATE FALSIFIED
Cost: 7% x C x p x (1-p) rounded up per order, C = 10, taker at the next candle's ask, held to settlement. N = 728,726 (running, +4), z bar 5.27. W3 holdout (2026-10-05 to 2026-11-03) NOT read for either, as registered. Dates 2026-08-06 to 2026-11-03 (90), thirds W1 08-06 to 09-04, W2 09-05 to 10-04.

| try, window | n | win rate | avg win / avg loss (c) | payoff ratio | PF | PF x1.2 | mean c / contract | day z |
|---|---|---|---|---|---|---|---|---|
| PRIMARY W1 | 276 | 11.2% | 53.8 / 8.3 | 6.45 | 0.82 | 0.80 | -1.36 | -1.03 |
| PRIMARY W2 | 229 | 13.5% | 54.3 / 9.3 | 5.85 | 0.92 | 0.90 | -0.68 | -0.29 |
| PRIMARY pooled W1+W2 | 505 | 12.3% | 54.1 / 8.8 | 6.17 | 0.86 | 0.85 | -1.05 | -0.83 |
| LATE W1 | 1,729 | 23.3% | 48.7 / 17.7 | 2.76 | 0.84 | 0.83 | -2.22 | -2.47 |
| LATE W2 | 1,726 | 23.5% | 49.4 / 17.6 | 2.81 | 0.86 | 0.85 | -1.83 | -1.81 |
| LATE pooled W1+W2 | 3,455 | 23.4% | 49.1 / 17.6 | 2.78 | 0.85 | 0.84 | -2.03 | -2.99 |

Average fill: PRIMARY 12.7c (the cheaper side after a shock-then-calm is usually already a longshot: only 12% win, payoff 6x, not the 28% / 3x OICORE shape), LATE 24.5c. Trade count: PRIMARY 8.4 a day (predicted 8 to 20 a day, 4% to 8% of windows; observed 2.6%), LATE 57.6 a day. Prediction check: PRIMARY win rate 20% to 27% predicted, **observed 12.3% (wrong, fills far cheaper than 20c to 28c)**; payoff ratio 2.8 to 3.8 predicted, **6.2 observed (wrong)**; PF 0.80 to 1.15, **0.86 (inside)**; verdict right.

**Groups and series (PRIMARY, pooled W1+W2, information, not tries):** Bitcoin n 66 PF 1.41 (W1 n 32 PF 2.46, W2 n 34 PF 0.87); the five others n 439 PF 0.79. By series (n, PF): HYPE 60 / 1.38, NEAR 130 / 0.86, Zcash 105 / 0.32, BNB 71 / 1.80, XRP 73 / 0.35. Per window: BNB 3.50 then 1.14 and HYPE 1.16 then 1.63 look good on 26 to 42 trades and are noise next to Zcash 0.14 and XRP 0.44; none clears 1.5 in both windows. LATE: Bitcoin n 644 PF 1.10 (W1 1.12, W2 1.08, the only series above 1.0, under the 1.5 bar), alts n 2,811 PF 0.80.

**OICORE overlap (PRIMARY, W1+W2):** 11 of 505 entries are OICORE entries (Bitcoin window where OICORE's rule also fires) = **2.2% of all entries** (predicted 1% to 2%), 16.7% of the 66 Bitcoin entries (predicted 5% to 10%; slightly high on a small n). LATE: 42 of 3,455 = 1.2% (6.5% of 644 Bitcoin entries). So the trigger is close to independent of the open interest jump.

**Streak report at the observed PRIMARY win rate 12.3% (505 trades):** empirical longest losing run **34** (longest winning run 3; 443 losses); in 100 trades the longest losing run has median 22, **95th percentile 39, 99th percentile 50**, and the chance of at least one 10-loss run in 100 trades is **99.8%**. LATE at 23.4%: empirical longest 27; 100 trades p95 22, p99 28, chance of a 10-loss run 84.7%. Independence assumed; losses cluster across series in a window, so these are a floor.

**Worst single loss:** largest fill seen PRIMARY 0.922 (the fill candle's ask can be far from the look quote), worst single loss at 10 contracts **9.28 dollars** (about 4.64 at 5 contracts), against the registered 0.50-cap figures 2.59 and 5.18 dollars; a fill above the cap is possible because the cap applies to the look candle. LATE worst loss 9.94 dollars at 10 contracts (fill 0.993). Typical loss at 12.7c fill: about 1.4 dollars at 10 contracts.

## Counterparty reading
Neither story is supported: the cheaper side after a shock-then-calm wins 12.3% against an average price of 12.7c plus fees (a small negative edge, PF 0.86, z -0.8), and a late shock is also a negative (PF 0.85, z -3.0). There is no sign that quote providers stay anchored to the pre-shock price, which is the H-null reading, same as FAM2 and LAG15.

## Forward read
Not recommended (FALSIFIED). For the record: at 8.4 PRIMARY trades a day, 150 forward trades would take about 18 days, so the earliest read is **about 2026-11-22** on markets closing after 2026-11-03. **No recorder is needed**: Kalshi 1 minute candles can be fetched after the fact for these series and the same `tslm1.py` re-scores them; one is needed only if the candle ingest stops.

## Caveats
One trigger definition (5% and median levels registered, not scanned), one look time (180 s) and band (5c to 50c); the cheaper side after a shock mostly lands under 15c, which is a different trade from OICORE's 12c to 19c mix with 28% wins and may be the wrong band for this trigger; no variant was run under this registration and none should be run on this data without a new registration.
