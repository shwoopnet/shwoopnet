# Held-out leak tests on three scorers frozen on the night of Nov 12 to 13 (Forensics desk)

**Run Nov 13, 2026, about 01:52Z, on the Head of R&D's order.** Tool: `leak_heldout_audit.py frozen <Desk B's workers folder> <the History Miner's workers/history_miner folder>`,
then the same with `--parent`. A Python audit hook counts every file open and folder listing inside a made-up `HELDOUT_X` folder (by real path), in five shapes: the folder
typed, a sub-folder of it, an innocently named symlink to it, "." from inside it, and its parent typed. Each command is first run on an ordinary folder of the same made-up
rows as a control; the made-up folders hold CS2 match rows, a politics market, one-minute and hourly candle answers and the wheel book recorder's run files, so each scorer's
control opens real answer files. No real data is in the folders.

| Scorer (sha256) | Command | Result |
|---|---|---|
| Desk B `voidsnap.py` (`c176146b...`) | `sample <lists> <out>` | REFUSES, all 5 shapes; control opened 2 files |
| | `measure <lists> <candles> <sample>` | REFUSES, all 10 cases (5 shapes, 2 folder arguments); control opened 8 files |
| Desk B `polgaph.py` (`9186c8b5...`) | `hourly-job <lists> <out>` | REFUSES, all 5 shapes; control opened 2 files |
| | `decide <lists> <hourly> <out>` | REFUSES, all 10 cases; control opened 8 files |
| | `score <lists> <hourly> <minute> <decisions>` | REFUSES, all 15 cases; control opened 9 files |
| History Miner `candlegap.py` (`a7178688...`) | `<recorder run> <pull>` | REFUSES, all 10 cases; control opened 13 files |

6 commands, 0 holes, 0 unproven. Not tested: `voidsnap.py job` and `polgaph.py minute-job` (they take a sample or decisions file and an output path, no data folder).

## One more test, VOIDSNAP only: the `hist_` answers inside an ORDINARY lists run

VOIDSNAP's held-out set is not a `HELDOUT_` folder: it is the `hist_` answers that sit in the same landed lists run as the development answers
(`pull/MAPBREAK_LISTS/2026-11-12T1919Z_43289005222`). The folder guard cannot protect those; only the reader's choice of rows can. An audit hook counted opens of the
23 `hist_` answer files of that run (file names taken from the manifest's row ids; I opened none of them):

| Build | Command | `hist_` files opened | Other answer files of the run opened |
|---|---|---|---|
| Desk B `voidsnap.py` (`c176146b...`) | `sample` on the real lists run | 0 of 23 | 5 |
| Forensics `voidsnap_second.py` | `sample` on the real lists run | 0 of 23 | 5 |
| Desk B `voidsnap.py` | `sample` and `measure` on a made-up fixture with one `hist_` answer | 0 | 2 |

Desk B's sample file made in that run is byte for byte its committed `VOIDSNAP_SAMPLE.json`.

**A limit worth knowing:** `voidsnap.py` and `polgaph.py` read a CANDLE run by opening every numbered answer file in the folder, not the files the manifest lists. That is
safe for a candle run, which holds only candle answers, but it means a candle folder must never be a folder that also holds list answers of a held-out set.
