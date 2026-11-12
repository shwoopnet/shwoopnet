# The wheel: lane ledger (kept by the Head of R&D)

Rules: `ROTATION_LANE.md` section 9.2. Every place ever admitted, every block read, cleared or failed. No live account figure is in this file; a place's own live fills are reported by message only. [design]

Expected lucky clears with no edge anywhere: blocks read times about 0.035 (0.05 for a favourite at 88c or above).

| Date | Places on the shadow list | Places with a working log source | Blocks read | Blocks cleared | Lucky clears expected | Seats taken |
|---|---|---|---|---|---|---|
| 2026-11-12 (batch 1) | 12 | 3 (to Nov 20) | 0 | 0 | 0 | 0 |
| 2026-11-12 (batch 1b) | 23 | 14 (3 to Nov 20, 11 to Dec 31) | 0 | 0 | 0 | 0 |
| 2026-11-12 (correction: the two DEPTH1 places withdrawn, it is 20 tries and not a rule) | 21 | 12 (1 to Nov 20, 11 to Dec 31) | 0 | 0 | 0 | 0 |

## Probation seats (rules section 5a; live results by message only, never here)

| Seat | Rule and market | Owner's popup | State |
|---|---|---|---|
| 1 | CFRTI-K, Bitcoin 15 minute (spec: DESK_A_PROBATION_SPECS_NOV12.md on claude/idea-desk-a, ddebdd87) | approved Nov 12 ("Yes, arm it") | to be built, reviewed and armed by the Chief of Staff; not live yet |
| next | REMATCH (e-soccer); MAPBREAK capped under 88c (CS2, Dota 2); a period-tie rule if TIE3 finds a cell | each needs its own popup | "As their reads allow": armed only if its first read is not under 1.0 |

## Premise test

WHEEL0 (does a HOT 60 predict the next 60): assigned to Forensics Nov 12 19:53Z, design fixed by the Head of R&D, 1 try. Counts before anything ran (no outcome joined, 8c2d924 on claude/forensics-desk): on the two weeks of recorded books, 2,674 windows, 112 blocks, 61 pairs, about 4 HOT pairs by luck, so books alone can only say "no evidence". On public one-minute candles from Sep 12 (Bitcoin landed; gold, XRP, Dogecoin and Ethereum-before-Oct-29 in one pull of about 880 requests): about 1,150 pairs, about 70 HOT by luck; the test can just see about 2.7c a contract at 70 HOT pairs, which is about the size its verdict line asks for. Five design rulings given 20:02Z (blocks grow to 10 of the rarer outcome on every template; per-band luck rates; look tolerances; a per-template random drop from the books-only fill table with a fixed seed; halves by count). **REGISTERED 20:12Z, before any outcome was joined:** claude/forensics-desk 2281057, folder kalshi-scalper/workers/forensics/wheel0/. sha256: wheel0.py 72b4594d70873a46a29ec1d1c3b7bbfd6150c614bc922ba6f60a98c9b87283f8; WHEEL0_REGISTRATION.md 680426efc1fa8461e522681f90129adc40d518bcb13c61ac70bc504a94ea483b; WHEEL0_DROP_TABLE.json f5f629704c29e8d0c98a78db2f784cefc63556a87f8d739accc1bfec4839bb74; WHEEL0_NULL_SIM.json bb9456dda0f3a704fb7228e9211f99b72c3d8ec5870f01f0239b033033b24bc7; WHEEL0_LISTS.json 20f8dd301f5295c5fb29b57f8c5ce40f04967802f62827fb83bf3abe655e0afd; build_wheel0_candles.py 2ac343fb07aab0d1497d80446149c37e8af30346e99978c8dbc45d639aeb7c15. Luck per band under the growing-block rule: 9.3, 6.5, 5.7 percent (cheap, low to high), 6.9, 8.7, 6.8 percent (favourite); favourites at 88c to 97c under the 150 rule 3.9 percent. Scorer selftest 22 of 22 on made-up data (finds a planted persistence, finds none where none is planted); its book mode reproduces the independent books-only count exactly (9,961 orders, 0 differences) with no result loaded. Blocks end on outcomes, so pairs cannot be counted before the read. List job (4 requests) with the Chief of Staff as the owner's ordered test; candle jobs (about 880 requests) follow. Auditor B's leak audit next. Nothing read; the read waits for the Head's go. No full seat before it is read.

## Per place

None has a block yet.
