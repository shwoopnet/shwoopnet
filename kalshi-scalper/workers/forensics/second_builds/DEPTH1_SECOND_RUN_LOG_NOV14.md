# DEPTH1 second build, the one real run (Forensics desk, Nov 14, 2026)
Run once at 2026-11-14T00:09:59Z (started marker written), exit 0, 3 min 53 s, Python 3.13.18 (python3 -I). Script depth1_second.py sha256 932121794f76ec19..., compare script 0b397fde456db565...
Input: quote-data pin 2b4ff3957b078def19a6a2bd8d7b83d87f322f7d (Desk A's pin, commit time 2026-11-14T00:03:03Z), sparse checkout of book15r6/ only (344 files, 86 run folders, dates 2026-10-29 to 2026-11-13), fetched into its own scratch directory; command: python3 -I depth1_second.py read <that book15r6 folder> <empty out dir>.
Outputs (figures SEALED: the two files are kept out of the repository and not sent until the comparison agrees; their sha256 below is the seal, written before any Desk A line was opened): result json sha256 96a5fa2dbbc9a220..., printed lines (26 lines, my own format; Desk A's wrapper prints 55 lines in another format, so a byte hash of the two bodies cannot match; the figure-by-figure compare is depth1_compare.py) sha256 4d87573aef875199...
No Desk A line was opened before this commit.

The two output files will be committed to this folder only after the comparison reads the same figures, all 20 tries, control included (the Head's rule: no figure to anyone before then).
