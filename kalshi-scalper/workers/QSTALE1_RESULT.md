# QSTALE1 result: a stale quote with trades printing and a wide spread, the cheaper side of Bitcoin, HYPE, NEAR, Zcash, BNB and XRP 15 minute markets (2026-11-03)

Registered and pushed first (`workers/QSTALE1_REGISTRATION.md`, commit 24dcffc, before any outcome), scored once with `src/scalper/qstale1.py` (`python -m scalper.qstale1 score`; refuses a second run; raw output `data/qstale1_score.json`, gitignored). Tests: `tests/test_qstale1.py` (5 pass, plain runner). Disclosure: `qstale1.py` and the test file were committed with the registration and not edited after; the only departure from the brief (relative stale rule instead of the literal half cent, from outcome-free counts) is in the registration. One post-score read-only recomputation (largest fill, for the worst-loss line) changed nothing.

## Verdict: FALSIFIED
Try A PF 0.72 in W1 and 1.20 in W2, both under the 1.5 bar. The W3 holdout (2026-10-05 to 2026-11-03) was NOT read, as registered. Cost: 7% x C x p x (1-p) rounded up per order, C = 10, taker at the next candle's ask; x1.2 stress shown. N = 728,726 tried (running), one-sided z bar 5.27.

| window (dates) | n | win rate | avg win / avg loss (c) | payoff ratio | PF | PF x1.2 | mean c / contract | day-clustered z |
|---|---|---|---|---|---|---|---|---|
| W1 (2026-08-06 to 09-04) | 282 | 14.9% | 52.4 / 12.7 | 4.12 | 0.72 | 0.71 | -3.02 | -2.14 |
| W2 (2026-09-05 to 10-04) | 167 | 18.6% | 53.9 / 10.2 | 5.28 | 1.20 | 1.19 | +1.70 | +0.62 |
| W3 (2026-10-05 to 11-03) | unread | | | | | | | |
| pooled W1+W2 | 449 | 16.3% | 53.0 / 11.8 | 4.49 | 0.87 | 0.86 | -1.26 | -0.91 |

Average fill **16.8c** (so a win nets about 53c, a loss about 12c). **Prediction check (written before scoring): mostly wrong in level, right in verdict.** Win rate 16.3% (predicted 22% to 29%: below), average fill 16.8c (predicted 24c to 32c: below), payoff ratio 4.49 (predicted 2.3 to 3.3: above), pooled PF 0.87 (predicted 0.60 to 1.15: inside), mean -1.26c (predicted -6c to +1c: inside), P(PF >= 1.5 in W1 and W2) 2% (did not happen). The cause of the miss: the stale-and-wide windows are quiet, so the cheap side was usually a far underdog (a 17c average ask), not the 28c of OICORE.

**Per series (pooled W1+W2, information, not new tries):** Bitcoin n 9 PF 1.32 (too few); HYPE n 76 PF 0.85; NEAR n 108 PF 0.55; Zcash n 106 PF 0.83; BNB n 100 PF 1.30; XRP n 50 PF 1.04 (flagged for L1 non-overlap, can be dropped without a rerun). No series reaches 1.5; BNB's 1.30 on 100 trades is noise.

**Contrary hypothesis vs counterparty hypothesis.** Under the counterparty hypothesis the win rate would sit 3c or more above the fill; it sits **0.5c below** (16.3% against 16.8c), and the mean per contract is -1.3c. That is the contrary reading: a stale wide quote is a quiet minute, the underdog is priced about right, and the buyer pays the spread plus fee. The contrasts agree: **wide but NOT stale (information, W1/W2):** n 2,609 / 2,817, win 23.7% / 24.0% at average fill 25.4c / 25.6c, PF 0.82 / 0.82, z -3.5 / -3.1; **Try B (stale with trades, no spread condition):** W1 n 1,183 PF 0.77 (z -2.6), W2 n 848 PF 0.85 (z -1.2), win 10.4% / 11.7% at fill 11.6c / 12.3c, W3 unread. Adding the spread condition to staleness moved the PF from 0.77/0.85 to 0.72/1.20 on 449 trades, which is inside noise. Nothing here supports the stated mechanism.

**Overlap with OICORE.** Bitcoin is 9 of 449 QSTALE1 entries (2.0%), and **0 of those 9 are also OICORE entries: the share of QSTALE1 entries that are also OICORE entries is 0.0%** (OICORE had 343 entries on the same dates; QSTALE1 caught none). The two rules are orthogonal by construction (Bitcoin's 1c spread almost never exceeds its own tertile, so QSTALE1 is an alt rule). Prediction (under 1%) held.

**Streak report** at the observed pooled win rate 16.3% (`src/scalper/streaks.py`): empirical longest losing run in the 449 realised trades **24** (376 losses, longest winning run 3); in 100 trades the longest losing run has median 17, **95th percentile 30, 99th percentile 39**; chance of at least one 10-loss run in 100 trades **98.3%** (exact, independence assumed; losses cluster across series in a window, so a floor). At the predicted 25% it would have been p95 20, p99 26, 79%.

**Worst single loss.** The registration said $2.59 at 5 contracts and $5.18 at 10 at the 0.50 cap. **The largest realised fill was 94c** (the next candle's ask after a signal ask of 50c or less: the quote jumped through the signal), so the worst realised loss on one order of 10 contracts was **$9.44** ($4.72 at 5 contracts). The signal-time cap is not a fill cap; a live version would need a limit price, which this test did not model (the same lateness risk as OICORE).

## Forward read
Not recommended (FALSIFIED). For the record: 449 trades over 59 dates (W1+W2) is about 7.6 trades a day (6.5 over all 90 dates, 4.6 in W3), so 150 forward trades would take about 20 to 33 days after 2026-11-03, a read on or after 2026-11-26 to 2026-12-06. **No recorder is needed**: Kalshi candles are retrievable after the fact for these series, so the forward read is a re-score of markets closing after 2026-11-03.

## Caveats
Single venue data; 1 minute candle closes only, so "stale" is a minute-close property, not a book age (the recorder books would be the finer test and have days, not months, of data); the relative tertile rules are a coarse, one-definition test of the idea, and the literal half-cent stale rule was not runnable (16 windows). Fill is the next candle's ask, one minute after the look, with no price limit. No variant (a different percentile, look, band or the direction split) is run under this registration.
