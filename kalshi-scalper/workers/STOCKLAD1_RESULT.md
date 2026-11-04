# STOCKLAD1 result (2026-11-04): NOT_RUNNABLE

Registration: workers/STOCKLAD1_REGISTRATION.md (sha256 e0ab8a152cffcd127f39d81bd80e1ca434b651e15df8c2a243e5072226cb3fa5).

Census on the public series list found no Kalshi single-stock close ladder or range series (0 of 15,687; company series are CEO, product, KPI, subscriber and legal markets, covered by EARN1/MENT1; price ladders are indices, covered by INX1/IDXFUT1). Settled single-stock ladder events before 2026-10-03T16:00Z: 0 (bar 25); expected trades 0 (bar 150). No candle, outcome or Yahoo price was fetched; nothing scored; no PF, no control, no win-versus-price table exists.

**Verdict: NOT_RUNNABLE.** Code (src/scalper/stocklad1.py, tests/test_stocklad1.py) is synthetic-only and ready if a series appears.

**Forward plan.** Re-run the series-list census on 2027-02-01; run only if a single-name price series exists with at least 25 settled events before a fresh frozen cut. Otherwise stay closed.

N: +2.
