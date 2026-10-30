# GEN7 discovery frozen (2026-10-30, before any validation row is built)

Survivor files, byte-identical copies of `data/gen7_<market>_frozen.json`, committed and pushed before the validation read:
- `workers/GEN7_frozen_btc.json` sha256 b8f09a9afc4111892579e4c3fe67885c6ee94860e36f93d4172dad6cf0ddf3e7 (14,408 generated, 5,000 distinct, 15 survivors)
- `workers/GEN7_frozen_gold.json` sha256 3c85fd8dbba59a63fdb69aed56359e1c58e579fb446bd27a8f0d875c25beb2e0 (13,211 generated, 5,000 distinct, 0 survivors)

Family control lists (discovery failures with 100+ trades on 15+ days; not committed, deterministic from seed 7 and `src/scalper/gen7.py`):
- `data/gen7_btc_controls.json` sha256 5c280ae166d604362f614e6875a57b9f3b011e5c2d45672147773c2bc7ed2187 (4,177 strategies)
- `data/gen7_gold_controls.json` sha256 f3ee45df09a21aa5f7b0af03bfd6a069034d4fd1f935ff4fbc78a90c652ac57c (4,133 strategies)
- all distinct: `data/gen7_btc_distinct.json` f2abc388..., `data/gen7_gold_distinct.json` e0202af5...

Gold has no discovery survivor (best PF at size 1.47), so gold is FALSIFIED at discovery; its controls are still run through validation for the record.
Implementation details fixed in code before discovery: a fill ask of 0 or 1 is no entry at that look; the zero-volume flag covers the signal and fill candles and the exit candle; the REF_GEN6_OIDRIFT exclusion set uses `scalper.oidrift._thr` (57 discovery windows here, its 20 day minimum makes the first usable day later than FALS4's check 5).
