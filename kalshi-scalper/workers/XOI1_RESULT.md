# XOI1 result: Bitcoin's open interest jump as the trigger, the cheaper side of HYPE, NEAR, Zcash, BNB and XRP 15 minute markets (2026-11-03)

Registered and pushed first (`workers/XOI1_REGISTRATION.md`, commit db0034a, before any alt outcome), scored once with `src/scalper/xoi1.py` (`python -m scalper.xoi1 score`; it refuses a second run; raw output `data/xoi1_score.json`, not committed). Tests: `tests/test_xoi1.py`. Disclosure: no code change after registration other than adding `tests/test_xoi1.py` (and fixing one sloppy assertion inside that test file before the run); `xoi1.py` was committed with the registration and not edited after.

## Verdict: FALSIFIED
PF 1.02 in W1 and 0.88 in W2, both under the 1.5 bar. The W3 holdout (2026-10-03 to 2026-11-02) was NOT read, as registered. Cost: 7% x C x p x (1-p) rounded up per order, C = 10, taker at the next candle's ask; x1.2 stress shown. N = 728,704 tried (running), one-sided z bar 5.27.

| window (dates) | n | win rate | avg win / avg loss (c) | payoff ratio | PF | PF x1.2 | mean c / contract | day-clustered z |
|---|---|---|---|---|---|---|---|---|
| W1 (2026-08-06 to 09-03) | 1,470 | 19.9% | 55.5 / 13.4 | 4.13 | 1.02 | 1.01 | +0.25 | +0.25 |
| W2 (2026-09-04 to 10-02) | 1,327 | 20.3% | 50.4 / 14.6 | 3.45 | 0.88 | 0.87 | -1.39 | -1.38 |
| W3 (2026-10-03 to 11-02) | unread | | | | | | | |
| pooled W1+W2 | 2,797 | 20.1% | 53.0 / 14.0 | 3.79 | 0.95 | 0.94 | -0.53 | -0.73 |

Average fill 19.8c (so a win nets about 53c, a loss about 14c). Prediction check (written before scoring): win rate 21% to 27% (observed 20.1%, just under), payoff ratio 2.6 to 3.6 (observed 3.79, just over), pooled PF 0.80 to 1.15 (0.95, inside), P(PF >= 1.5 in W1 and W2) 3% (did not happen).

**Per alt (pooled W1+W2, information, not new tries):** HYPE n 521 PF 1.19 (W1 1.38, W2 1.03); NEAR n 684 PF 0.83 (0.93, 0.73); ZEC n 617 PF 0.84 (0.79, 0.90); BNB n 468 PF 0.95 (0.99, 0.90); XRP n 507 PF 1.05 (1.20, 0.90). No alt reaches 1.5 in either window; none is a lead (HYPE's best window 1.38 is under the bar and decays).

**Direction of the cheaper side.** The cheaper side is simply the side priced below 50c at the look (YES first); it was YES in 50.7% of trades. Against the sign of Bitcoin's YES-mid move from 360 s to 180 s before the close: the cheaper side **agrees with Bitcoin's move in 34.5% of trades** (n 966, win rate 18.3%, PF 0.64), **disagrees in 65.0%** (n 1,818, win rate 20.8%, PF 1.17), flat 0.5% (n 13). So the sample is mostly the alt's contrarian side to Bitcoin's move (the trigger fires in busy windows when the market already leans one way and the alt's cheap side is the other), and the agreeing trades, which are the ones the stated mechanism (Bitcoin drags the alt across its strike) describes, are the worse ones. The mechanism as written is not supported. Information only; no variant was run on it.

**Try B (information only, no verdict):** Bitcoin's fixed OICORE trigger (doi > 86,299.56) with the same trade: W1 n 1,354 PF 1.07, W2 n 1,408 PF 0.95 (W3 unread). Also not near 1.5.

**Overlap with OICORE (they share a trigger).** In the 1,101 distinct close times where XOI1 traded (W1+W2), OICORE's own Bitcoin rule also fired in 235, **21.3%** (parity check on the same loader: OICORE discovery n 222 PF 2.28, validation n 333 PF 1.85, as GEN6). Daily net dollars, XOI1 pooled vs OICORE Bitcoin, over the 58 dates: Pearson **+0.10** (n 58 days; every date had both rules trade, so all-days and both-traded-days are the same). Weakly positive, as expected for a shared trigger, but small; the five alts' orders in one window are correlated with each other (up to five orders per window), which the day-clustered z accounts for.

**Streak report** at the observed pooled win rate 20.1% (`src/scalper/streaks.py`): empirical longest losing run in the 2,797 realised trades **36** (ordered by close time then ticker; 2,235 losses, longest winning run 5); in 100 trades the longest losing run has median 15, **95th percentile 25, 99th percentile 32**; **chance of at least one 10-loss run in 100 trades 93.2%** (exact, independence assumed; real losses cluster across alts in a window, so these are a floor).

## Forward read
Not recommended (FALSIFIED). For the record: 2,797 trades over 58 dates = about 48 trades a day (five alts, up to five per window), so 150 forward trades would take about 3 to 4 days of markets closing after 2026-11-02, and Kalshi candles are retrievable after the fact for these series, so no recorder would be needed. A pass would still lack a named counterparty.

## Caveats
Single venue data and one trigger definition (OIREL, fitted on Bitcoin discovery); fill is the next candle's ask, one minute after the look (the lateness that cut the Bitcoin core's own discovery PF from 2.28 to 0.94 in another test is a stated risk, not tested here); XRP is included as asked though live L1 pauses it; no variant (a different look, band, trigger or the agreeing subset) is run under this registration.
