# CANDLEGAP-2 closed as NOT DECIDED (dated note, Nov 13, 2026, Head of R&D's ruling at 06:48Z)

**Zero tries.** No result, rule or figure from CANDLEGAP-2 is reported.

- **Gate A (pull structure) PASSED** (Auditor B, 06:38Z) on `pull/CANDLEGAP2_TTEBB/2026-11-13T0632Z_43379341927/` (kalshi-pull-data): 3 of 3 requests at HTTP 200, none truncated, hashes and bytes equal to the manifest, the embedded job byte for byte `CANDLEGAP2_TTEBB.json` (1a391881), all 74 tickers present.
- **Gate B (printed checks) FAILED on both series.** The frozen code (candlegap.py a7178688, candlegap2_run.py fbbed7bf, design a91d4113, hashes re-checked before the run) was run on `wheelbook/2026-11-12/2031` and the landed pull, and ONLY the two gate keys were printed:
  - KXLIGAPROMATCH: tickers_with_candles 46, markets_closed_in_lists 40 (the gate needs 46);
  - KXEBASKETBALLGAME: tickers_with_candles 28, markets_closed_in_lists 24 (the gate needs 28).
  So the before/after-close split is "not decided" for both series.
- **Nothing beyond the two gate keys was read or reported.** Which markets lack a close was not looked at. The two output files were deleted from the History Miner's scratch and never committed.
- **Likely cause (not checked, by the ruling):** the 2031 folder comes from the wheelbook recorder before its fix (merged 00:36:13Z, Nov 13); its lists miss closes outside its own window. No repair pull is made: a lists read chosen after the candles landed is not allowed, and the measurement's purpose has gone (INPLAYJUMP's table tennis family falsified and its e-basketball family closed on cost, on two builds, Nov 13).
- **CANDLEGAP's first result (CS2, `CANDLEGAP_RESULT.md`) stands as recorded, with its limits.**
- For any later card that takes Nov 12 to 13 Liga Pro or e-basketball closes as its held-out: this pull happened (74 tickers, candles read only by the frozen code; only the two gate keys were printed).
