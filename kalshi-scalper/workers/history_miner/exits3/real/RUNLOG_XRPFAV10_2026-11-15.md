# EXITS3: the one run of XRPFAV10 (2026-11-15 15:55:51Z), on Auditor B's CLEAN (15:55Z); XRPFAV6 not run (dropped by the Head, 15:54Z)

- Code: exits3.py 1f0c30c6 (commit 677a4ec5). Supplement t_share.py f21816bd, written after the CLEAN at Auditor B's request: it only counts T exits whose sale is at or below the entry price and changes no figure. Exit 0 for both.
- Data: XRPFAV_extract.sqlite.xz (claude/forensics-desk 31351c1b), xz sha256 be6bc75f080843492989fb18ca08d2836ceb4465d7af520677cf11075bca7f13, sqlite 04b377f0...: KXXRP15M from alts2, closes 2026-09-03 to 10-02 23:45Z, XOI1 cut from Oct 3. Guard list c561184a (equal to main). Touched: only this extract (in scratch) and this repo's code.
- Prints, committed before reading:
  - EXITS3_XRPFAV10.json, sha256 03900e53aa56e6d9d3db162146d20ca4ac9c5b73c98e040ce1bc23d6246b0fea
  - EXITS3_XRPFAV10_Tshare.json, sha256 04e4b4d7e7dc7ddf1371223571fc2a5e4234ccc64c077e042c61eca48217e0c1

**Read with the prints (Auditor B's points):**
1. XRPFAV10 has no spread cap, so the float spread note (XRPFAV6's 0.02 cap) does not apply. The entry candle is the LAST candle with 570 to 640 s left, tested after it is picked, whereas regime_b2 drops incomplete candles first. So n can differ from regime_b2's and from the haircut readers'.
2. **1 contract with a per-order fee rounded to the cent** (about 1c a leg at 0.90) is a different cost basis from the 10-contract recompute. No PF here is comparable to the haircut recompute's.
3. **T's target is the 0.90 cap** for e from 0.88 to 0.92, so T sells near the entry price, minus fees and the haircut: a loss-making exit by construction. The Tshare file gives the count of T sales at or below the entry at h 0, 1c and 2c.
4. M applies (the 180 s mark is after a 570 s or later entry). Primary: hold and M 1c, T and S 2c. Upper bound, not fill-checked. A pass is information only and needs a second build under 16b.
