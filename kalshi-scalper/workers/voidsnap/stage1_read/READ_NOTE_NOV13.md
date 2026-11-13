# VOIDSNAP stage 1: the one read, Nov 13, 2026, 05:32Z (PROVISIONAL, ONE BUILD, a hindsight measurement, not a rule)

Zero tries. No bet, no profit figure. Nothing here is a verdict until Forensics' second build prints the same figures on the same files (rule 16b); the Head of R&D records it.

- **Scorer:** `voidsnap/voidsnap.py`, sha256 c176146bd05130f04bcd6ec62c5587681f9fb5edb6882caa922e63fdaaf8c211 (Auditor B CLEAN). Run once: `voidsnap.py measure <the MAPBREAK lists run> <the candle run> voidsnap/VOIDSNAP_SAMPLE.json`.
- **Candle run:** `pull/VOIDSNAP_CANDLES/2026-11-13T0244Z_43354200129/` on `kalshi-pull-data` (79 requests, job 158c8685). Auditor B's structure check passed before it was opened (manifest equal to the committed job, every sha256 and length, no stray file, 746 tickers asked and present, nothing after the development window).
- **Sample:** `VOIDSNAP_SAMPLE.json` (583561d0): 195 voided esports events and 195 matched played ones.
- **My printed lines, whole:** `desk_b_printed_lines.txt` (53 lines).

## What it printed, in plain words

**READING: CLOSED, no try spent.** No detector meets its three lines under any of the three readings of a missing minute, so the reading does not depend on the carry.

| Question (the line it had to meet) | Under the registered carry | 60 minute carry | No carry |
|---|---|---|---|
| 1. Was the settlement value knowable beforehand? Best allowed reference within 3c of it (needs 70% of voids) | 35.9% | 35.4% | 23.1% |
| 2. Was there anything to buy? Voids with 5 buyable minutes in a row (all voids, before any detector) | 24 of 195 | 24 of 195 | 14 of 195 |
| Detector 1, frozen after the start: flagged voids with a buyable run (needs 40) / share of voids among the flagged (needs 30%) | 0 / 25.3% | 0 / 25.3% | 0 / 20.1% |
| Detector 2, no trade after the start: the same two | 0 / 28.4% | 0 / 28.4% | 0 / 28.4% |
| Detector 3, ran before the start: the same two | 7 / 14.4% | 7 / 14.4% | 2 / 7.7% |

Of the 195 voids, 16 had no window and 179 had a candle. Where a void was buyable at all, the median shortfall under the settlement value was 13c at a median one-way cost of 3.5c, but only 24 voids had such a run and no detector found them in time: the two detectors that fire after the start caught none, and the one that fires before the start caught 7.

## What this does and does not say

- It says the three things the card needed are each absent on esports in this window: the fair price cannot be read ahead within 3c in most voids, few voids stay buyable under their settlement value, and none of the three registered ways of spotting a void in time works.
- It does not say voids are never mispriced: 24 voids did sit 10c or more under their settlement value for five minutes. It says a rule could not have known which matches those were.
- It is hindsight on one window of one family (esports "fair price" voids). The fixed-price families (e-soccer, Liga Pro, e-basketball, ITF) were not measured here; Idea Desk C's census already found their voids barely trade away from the fixed price.
- A carried ask is a quote last seen, not a quote that could be paid.
- The stage 2 text (`VOIDSNAP_STAGE2_RULE.md`) was written before this read and is NOT registered. On this reading it is not registered at all.

## Second build: the same output (05:35Z)

Forensics printed and committed its own build's output first (`claude/forensics-desk` b10f83da, `second_builds/VOIDSNAP_SECOND_OUTPUT_landed_VOIDSNAP_CANDLES_2026-11-13T0244Z.txt`, from `voidsnap_second.py` 32243990 on the same candle run, lists run and sample), and only then opened `desk_b_printed_lines.txt`. Its comparison parsed all 53 lines: 157 figures compared, 0 differ. Both builds read CLOSED, no try spent, with every detector failing all three lines under all three carries. Rule 16b is met; the verdict is the Head of R&D's to record. Until the Head records it, the card's own text is not touched.
