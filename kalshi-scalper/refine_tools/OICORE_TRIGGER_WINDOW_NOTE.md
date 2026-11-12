# OICORE model trigger windows (public open interest cache)

List: `OICORE_TRIGGER_WINDOW_TICKERS.csv` (ticker, close_time_utc, oiRise). Tickers and public-cache open interest only; nothing about orders or results.

Definition (same computation as the `trig()` function in the OIGAP run script): KXBTC15M window with close time c; oiRise = OI at the candle ending c-180 s minus OI at the candle ending c-360 s; listed when oiRise >= 86,300. The price band (cheaper side 0.08 to 0.50 at c-180, entry price at c-120) is NOT applied: this is the open interest trigger only, as asked. Windows without both candles or with a blank OI are skipped.

Source: `oi/btc.jsonl` (6,468 settled windows read OK) plus the BTC rows of `fwd_cache.jsonl` (830 windows, 591 also in btc.jsonl; 0 disagreements on oiRise in the overlap). 6,707 distinct windows examined, closing 2026-09-02 12:45 UTC to 2026-11-12 06:15 UTC. **2,563 trigger** (134 of them only in fwd_cache, closing from 2026-11-03).

Missing OI data: none among the examined windows. 4 rows in btc.jsonl were flagged not-ok (failed fetch) and unsettled rows are excluded before counting, so they are not in the 6,707.

Ambiguities: (1) the OIGAP script uses a band of 0.05 to 0.50 on the pre-entry price while the registered model text says 0.08 to 0.50 (OIBASE1 uses 0.08); irrelevant here since the band is not applied. (2) The cache holds only settled windows, so a very recent window may be absent. (3) The comparison is `>=` on floats; the smallest listed value is 86,341, so no window sits exactly at the line. (4) Windows from btc.jsonl whose candles lack the c-360 or c-180 mark would be dropped as missing; there were none.
