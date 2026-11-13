# workers/testing: which print is the record (Testing Desk, Nov 13, 2026)
Superseded prints sit under `superseded/` and are not records. The pinned hashes below are the ones Auditor B diffed and cleared.

| Reader | Frozen build (first 16 hex) | Record print | Notes |
|---|---|---|---|
| INPLAYJUMP second scorer | `inplayjump_second.py` fb9bca51de40b7c1 (b39596b6), wrapper `inplayjump_read.py` 65f5c9e5eebb4e5b (pin updated, 11fee473; the reads were made with 6df28ad7 and scorekit 02728f2a), `scorekit.py` f219b43c755b4b87 (the guard of a763e2a4; earlier readers were audited on 02728f2a) | counts: `inplayjump_second_reads/v2/counts_*.json`; full reads: `inplayjump_second_reads/v3/full_*.json` (968d6830) | recorded on two builds Nov 13; e-soccer and e-basketball closed on cost, table tennis, ITF and challengers FALSIFIED |
| SOCDERIV reader | `socderiv.py` 77ea2ba71def6e3e (641e0e92) | stage 1: `socderiv_landed_reads/stage1_record_counts.json` (a40b4f34, made with reader 159ff24f); stage 3 on invented rows: `socderiv_stage3_prints_23cases/` | candles not read yet; see SOCDERIV_MEASUREMENT.md |
| Hourly temperature second reader | `hourlytemp_second.py` c3b6f048bad6082c (volume count over each market's own life; step 1 cleared at 00074594, f94e1bbd), note sha256 3ff1de2d... | invented cases: `hourlytemp_second_prints_v6/` (identical to v5, the earlier hash); real lists step 1: `hourlytemp_landed_reads/step1_sample.txt` (bea805e9) | measure step waits for the candle run |
Other readers (WHEEL0, ESOCTIE, CANDLEGAP, REMATCH, TIE3, MAPBREAK, WXDAYEND, POLCOST): the module header states the registration and hash it was built to; their recorded results are in rnd-queue.
Fixtures: every `*_fixture_inputs_MADE_UP_DATA` folder is invented data; SOCDERIV cases 01 to 14 use an invented ticker layout, 15 to 23 the real one.
