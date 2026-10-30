# GEN6 discovery frozen (2026-10-30, before any validation row is built)

Survivor files, byte-identical copies of `data/gen6_<market>_frozen.json`, committed and pushed before the validation read:
- `workers/GEN6_frozen_btc.json` sha256 0b0b8e4b7aee0d4bcd870599efacb98a640bd96e9fc64e96a909862c579230ba (30,890 generated, 5,000 distinct, 128 survivors)
- `workers/GEN6_frozen_gold.json` sha256 2acb19e68981fe97f7bbecd867cb98f2a0f47909f07aa5b29e1cd3722a0533ce (31,251 generated, 5,000 distinct, 10 survivors)

Family control lists (discovery failures with 100+ trades on 15+ days; not committed, deterministic from seed 6 and `src/scalper/gen6.py`):
- `data/gen6_btc_controls.json` sha256 5eb93ad31bbbea9f423d60d647f3a3605081125fd4571b649cad2d848c6ee995 (3,778 strategies)
- `data/gen6_gold_controls.json` sha256 039161283e0ba5b4031be0bc1fbeda6e87e330b0cb24df24d11906b6fa276596 (3,766 strategies)
- all distinct: `data/gen6_btc_distinct.json` c5ff0419..., `data/gen6_gold_distinct.json` 8244f4f7...

One implementation detail not spelled out in the registration, fixed in code before discovery and applied to every row: a side bid of 0 is not a sale (a time, stop, take-profit or 60 s exit skips a candle whose bid is 0, and the contract stays held if no later candle qualifies).
