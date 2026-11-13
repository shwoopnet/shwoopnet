# WHEEL0 precondition marker (Head of R&D's ruling of 2026-11-12 20:21Z)

The WHEEL0 scorer refuses to run its read before 2026-11-14T00:00Z, and until this file carries a line that begins with the words DEPTH1 READ MADE and a colon, in capitals, at the start of a line. That line is added by the Forensics desk, in its own commit, only on the Head of R&D's word that DEPTH1's single read has been made and reported.

Status: DEPTH1's read has not been made.

## Dated line, 2026-11-13 00:18Z (Head of R&D's ruling; text only, the scorer and its hash are untouched)

A static check on 2026-11-13 found one comparison in `wheel0.py` with no tolerance: line 355, the NOT SUPPORTED test "profit factor after HOT under 1.0". Every other registered line carries a tolerance of 1e-9. The frozen scorer is left as it is (sha256 `10a7b3630be5807aaf31cdd18f50537e547ffc6e9d1732b72322b4d049a10cf4`). Instead, a standing rule for this read and every read: **if any verdict figure lands within 0.001 of its bar, both builds (this scorer and the Testing Desk's `wheel0_second.py`) recompute that figure in exact whole cents, and the exact figure decides.** For WHEEL0 the verdict figures and bars are: profit factor after HOT against 1.15 and against 1.0, D against zero (within 0.001 dollars), the HOT pair count against 30 (a whole number, never near), and both p values against 0.05.

## Dated line, 2026-11-13 07:03Z (Head of R&D's order, from Auditor B's independent sweep of every branch; text only, the scorer, its hash and the order of work are untouched)

These words are added to the first lines of WHEEL0's result when it is printed:

> Not the first outcome read on these windows: the old research team's open interest test (OICOREX1) read its holdout from 2026-10-28 on the Bitcoin, XRP and Dogecoin 15 minute series under a different rule, so Bitcoin's closes of Oct 28 and XRP's and Dogecoin's closes from Oct 28 were read before; and this desk's own baselines of Nov 12 (closes Oct 29 to Nov 8), already disclosed in section 9.

Also recorded from the same message: the old team's unread forward reads on these series are frozen at its branch tip `79724f00`; its market making and closing-buy reads are marked CLOSED UNREAD by the Head; and no CFRTI card holds out Ethereum by registration, so this test's Oct 29 Ethereum bound is simply conservative and stays.

Nothing else changes: `wheel0.py` keeps its sha256 `10a7b363...`; the read waits for DEPTH1's read, the marker line this file describes at its top, and the Head's go.
