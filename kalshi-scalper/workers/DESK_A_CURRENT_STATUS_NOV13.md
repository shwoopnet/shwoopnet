# Desk A current status index (Nov 13, 2026): what governs, where older files disagree
Written because several frozen or dated files still carry superseded dates. No frozen body was edited (a prepended line would change its hash); this file points at the rulings instead.

## CFRTI family: current held-out dates (supersede the Nov 5, Nov 9 and Nov 20 wording inside the files)
- CFRTI1-BTC, CFRTI1-BTC Kraken-only, CFRTI-B: held-out from 2026-11-09 (CFRTI_HELDOUT_AMENDMENT_NOV12.md; frozen at the hashes in FROZEN_BEFORE_DEPTH1.md). The old HELDOUT_FIRST_DAY 2026-11-05 text in their registrations is superseded. Read once on or after 2026-11-20, same sitting.
- CFRTI-K, CFRTI-K-TX, PERPBIN1: not frozen; held-out from closes 2026-11-14T00:00:00Z (amendments cf864b55 and b3ae4974). Earlier rows are printed apart as "not blind", never pooled.
- Order of authority: the dated amendment at the end of a file, then FROZEN_BEFORE_DEPTH1.md, then the file's body.

## Wheel and INPLAYJUMP: which version is current
- Wheel: frozen sheet DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md (do not edit); scorer desk_a_verify/nc15_wheel_replay.py v2 (sha256 8d1055df...); block reader desk_a_verify/wheel_block_reader.py v6 (sha256 5525cbbb..., lane text rnd-queue 5225eff1 v1.3). Mentions of lane text bd7007cb, 77eeb93b, dbd2f4da, 7c4c71d2 in older notes are SUPERSEDED.
- INPLAYJUMP: engine desk_a_verify/inplayjump.py sha256 6e356373... is the one to audit; outputs for engine c39b1e9b and 870a453e are PROVISIONAL history. No verdict is recorded until the Testing Desk and Auditor B print matching lines (rule 16b).
