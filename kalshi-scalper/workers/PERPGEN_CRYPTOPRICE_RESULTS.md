# PERPGEN slice CRYPTOPRICE results (worker, 2026-11-06)

Protocol `workers/PERPGEN_PROTOCOL.md` unchanged (no amendment file). Engine `src/scalper/perpgen_cryptoprice.py` (vectorised numpy, one-position selection in a small C routine). Group CRYPTO (10 tickers, pooled), atoms only from the 20 price-family numeric features (r5 r15 r60 r240 r1440, vol60 vol240 volratio rng60 rng240, vlr15 vlr60 doi60 doi240 tvm, dhi240 dlo240 dhi1440 dlo1440 pir1440; 200 numeric atoms); no funding, time or cross-asset atoms. Cuts from discovery decision times only: `workers/perpgen_cryptoprice_cuts.json` (sha256 e2b729f82763d27104491efc9b7b8861339825ec7ae77d90f7d7e5bc01b0d61e). Seeds 1000 + run number, ledger `workers/perpgen_ledger/RUN<nn>_CRYPTOPRICE.ids.gz` written before each 500-rule batch was scored. Frozen survivor lists `workers/PERPGEN_FROZEN_CRYPTOPRICE_R<nn>.json` (all empty).

**N for this slice: 200000 distinct (rule, CRYPTO) pairs in 40 runs of 5,000. Discovery survivors: 0. Validation, audit and holdout were never read (nothing to read; the holdout guard file was never written).** Ledger lines across all PERPGEN ledgers at the time of this write: 500000 (other workers included).

Funnel per run (discovery regions only, 12 bps a side; each column adds a bar): n at least 200 trades; then at least 20 dates and PF at least 1.3; then PF above 1.0 in both halves; then mean net above 0 at 24 bps; then no date over 25 percent of net profit (a survivor).

| run | rules | n>=200 | +20 dates, PF>=1.3 | +both halves>1 | +mean24>0 | survivors | best disc PF (n) |
|---|---|---|---|---|---|---|---|
| 01 | 5000 | 4516 | 0 | 0 | 0 | 0 | 1.258 (211) |
| 02 | 5000 | 4391 | 0 | 0 | 0 | 0 | 1.232 (210) |
| 03 | 5000 | 4396 | 1 | 0 | 0 | 0 | 1.406 (222) |
| 04 | 5000 | 4372 | 1 | 1 | 1 | 0 | 1.308 (211) |
| 05 | 5000 | 4343 | 2 | 0 | 0 | 0 | 1.506 (224) |
| 06 | 5000 | 4362 | 2 | 2 | 1 | 0 | 1.359 (212) |
| 07 | 5000 | 4369 | 2 | 2 | 1 | 0 | 1.347 (208) |
| 08 | 5000 | 4362 | 2 | 1 | 1 | 0 | 1.310 (210) |
| 09 | 5000 | 4382 | 1 | 0 | 0 | 0 | 1.308 (205) |
| 10 | 5000 | 4345 | 1 | 1 | 1 | 0 | 1.350 (213) |
| 11 | 5000 | 4332 | 0 | 0 | 0 | 0 | 1.209 (208) |
| 12 | 5000 | 4352 | 1 | 1 | 1 | 0 | 1.519 (236) |
| 13 | 5000 | 4356 | 1 | 0 | 0 | 0 | 1.302 (252) |
| 14 | 5000 | 4489 | 0 | 0 | 0 | 0 | 1.226 (208) |
| 15 | 5000 | 4436 | 1 | 1 | 1 | 0 | 1.327 (232) |
| 16 | 5000 | 4412 | 0 | 0 | 0 | 0 | 1.262 (213) |
| 17 | 5000 | 4351 | 0 | 0 | 0 | 0 | 1.237 (253) |
| 18 | 5000 | 4436 | 1 | 0 | 0 | 0 | 1.423 (232) |
| 19 | 5000 | 4421 | 2 | 1 | 1 | 0 | 1.406 (236) |
| 20 | 5000 | 4400 | 0 | 0 | 0 | 0 | 1.273 (207) |
| 21 | 5000 | 4421 | 3 | 2 | 0 | 0 | 1.441 (203) |
| 22 | 5000 | 4350 | 0 | 0 | 0 | 0 | 1.275 (258) |
| 23 | 5000 | 4386 | 1 | 0 | 0 | 0 | 1.303 (250) |
| 24 | 5000 | 4337 | 0 | 0 | 0 | 0 | 1.252 (228) |
| 25 | 5000 | 4401 | 1 | 0 | 0 | 0 | 1.341 (270) |
| 26 | 5000 | 4367 | 1 | 0 | 0 | 0 | 1.365 (203) |
| 27 | 5000 | 4341 | 2 | 2 | 2 | 0 | 1.625 (212) |
| 28 | 5000 | 4345 | 1 | 0 | 0 | 0 | 1.366 (206) |
| 29 | 5000 | 4343 | 0 | 0 | 0 | 0 | 1.249 (265) |
| 30 | 5000 | 4338 | 0 | 0 | 0 | 0 | 1.200 (258) |
| 31 | 5000 | 4350 | 1 | 0 | 0 | 0 | 1.322 (246) |
| 32 | 5000 | 4335 | 0 | 0 | 0 | 0 | 1.260 (224) |
| 33 | 5000 | 4332 | 1 | 0 | 0 | 0 | 1.339 (221) |
| 34 | 5000 | 4368 | 0 | 0 | 0 | 0 | 1.266 (266) |
| 35 | 5000 | 4321 | 1 | 1 | 1 | 0 | 1.378 (246) |
| 36 | 5000 | 4345 | 1 | 0 | 0 | 0 | 1.401 (236) |
| 37 | 5000 | 4330 | 0 | 0 | 0 | 0 | 1.244 (232) |
| 38 | 5000 | 4368 | 0 | 0 | 0 | 0 | 1.261 (220) |
| 39 | 5000 | 4312 | 0 | 0 | 0 | 0 | 1.185 (258) |
| 40 | 5000 | 4310 | 1 | 1 | 0 | 0 | 1.441 (203) |
| total | 200000 | 174823 | 32 | 16 | 11 | 0 | 1.625 (n 212, run 27) |

Reading: of 200,000 rules about 87 percent trade at least 200 times, but only %d reach PF 1.3 on 20 dates at 12 bps a side (24 bps round trip plus the spread), %d have both halves above 1, and none survives the 24 bps mean and the date-concentration bar together. The unconditional core loses about 25 to 27 bps a trade at every horizon (cost), as the protocol predicted. The nearest miss (RUN27, `dhi240:ge:0.25&r5:ge:0.75&rng240:ge:0.90|S|28800`, PF 1.62 on 212 trades, 45 dates) fails only the 25 percent single-date bar (39.7 percent). Not a pass, not a lead: no label beyond FALSIFIED-at-discovery applies; the protocol's prediction (under 1 percent survivors, zero candidates) held. Validation was not read for any rule, so no validation or audit figure exists for this slice. Not implemented because not needed: the `validate` and `audit` commands (A1 to A10 plain-loop recompute, placebo, holdout freeze); they must be written before a future run produces a survivor.

Deviations and disclosures: (1) the protocol's feature list has no candle-shape feature, none was invented; spread atoms (sp, spr) were left out as not in the slice's list. (2) Run numbers 1 to 40 are this slice's own (file suffix CRYPTOPRICE); seeds 1000 + nn may coincide with another worker's seed but their grammar differs. Runs 2 to 13 and 27 to 40 were first attempted while another worker's ledger was mid-write (a read error before any rule was drawn, no ledger written), then run normally; the per-run funnel above was produced by a deterministic re-score of each ledger (`rescore`, writes nothing). (3) Zero-volume windows make vlr undefined (feature missing, atom false). (4) A signal whose fill quote is defective or out of the stage does not open a position; a trade whose exit is missing within 5 minutes does occupy the position and is void.
