# GEN8 discovery frozen (2026-10-30, before any validation row is built)

Survivor files, byte-identical copies of `data/gen8_<market>_frozen.json`, committed and pushed before the validation read:
- `workers/GEN8_frozen_btc.json` sha256 735b3a22eaf23f8a2b0e3fabe3b6607d7a01f74a10268f181f64c983a8810ade (18,363 generated, 5,000 distinct, **0 survivors**; best PF at size 1.14)
- `workers/GEN8_frozen_gold.json` sha256 7402cb26ac0729644bed89c396203a70dda491ade704e17a5ef8d59ecfb2e5bd (17,365 generated, 5,000 distinct, **0 survivors**; best PF at size 1.09)

Family control lists (discovery failures with 100+ trades on 15+ days; not committed, deterministic from seed 8 and `src/scalper/gen8.py`):
- `data/gen8_btc_controls.json` sha256 5b27f479869214e29c1fd5e6d455122c6546a3c85597b67ce81c9b9397ae6e85 (4,204 strategies)
- `data/gen8_gold_controls.json` sha256 a1e00b8e85554bfb653913eebd8369830eeb1aeb6024643b9505b6627cc693e7 (4,145 strategies)
- all distinct: `data/gen8_btc_distinct.json` 564e6eab..., `data/gen8_gold_distinct.json` 0e148f96...

Both markets have no discovery survivor, so both are FALSIFIED at discovery by the registered kill rule. The controls (and, as information only, the ten best discovery rules at size per market) are still read once on validation for the record.
