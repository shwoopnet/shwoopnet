**CLOSED, Nov 13, 2026: CANDLEGAP-2 was closed as NOT DECIDED (gate A passed, gate B failed). See `CANDLEGAP2_CLOSED_NOV13.md` (f675d325). The gates below are kept as written.**

# CANDLEGAP-2 read-time gates (dated note, Nov 13, 2026, about 02:20Z; Auditor B's CLEAN of fd92418c, accepted by the History Miner)

No frozen file changes; the hashes stand (candlegap.py a7178688, candlegap2_run.py fbbed7bf, CANDLEGAP2_DESIGN.md a91d4113, CANDLEGAP2_TTEBB.json 1a391881). Both gates are applied BEFORE any count is read:

- **(A) Pull structure.** Auditor B runs their structure check on the landed CANDLEGAP2_TTEBB pull (3 of 3 requests at HTTP 200, none truncated, sha256 and bytes equal to the manifest, parameters equal to the job, no candle outside its request range, every ticker present, nothing after 00:04Z) and answers. No count is read before that answer. A refused or 429 row would silently turn a third of the tickers into "candle missing", the very thing measured, so a pull that fails (A) is not read at all.
- **(B) Printed checks.** Each series' output is read only if `markets_closed_in_lists` is 46 for KXLIGAPROMATCH and 28 for KXEBASKETBALLGAME; otherwise the before/after-close split is "not decided" and is not reported. `tickers_with_candles` is stated beside every count.

Known wrapper gaps (Auditor B, tested): the HELDOUT_ guard is case-sensitive (no such folder exists; none is to be made); the wrapper does not itself refuse a manifest with a non-200 row (fenced by gate A). If a later card takes Nov 12 to 13 Liga Pro or e-basketball closes as its held-out, it must say this pull happened (the output includes a candle-against-book match). Rule 16b: the Testing Desk's second build still applies.
