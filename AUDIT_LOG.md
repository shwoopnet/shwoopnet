# Research audit log

Independent weekly audit of the research chats' results (read only; the audit never edits research branches). One line per result: id, date, verdict (VERIFIED, MISMATCH, COULD_NOT_VERIFY), why.

## 2026-11-09 (first audit; raw sqlite files and scan ledgers are not on any branch)
- W-OIBIGLOSS1 / OICORE net since Nov 1: VERIFIED as of Nov 8 01:33Z: 56 fills, 9 wins, fill-booked +22.77, limit-booked +9.61. STALE now: through Nov 9 00:50Z it is 65 fills, 10 wins, fill-booked +14.86, limit-booked +1.70.
- W-WEEKPNL1: VERIFIED for the limit-booked figures (OICORE 7d 51 fills +8.05; since the Nov 6 deploy 13 fills -19.54; EVENT830 5 fills -1.46); fill-booked 21.00 vs their 20.21 (small, same sign).
- W-OIPARTIAL1, W-OIEXIT1, W-OISWEEP1, W-ESRATE1: COULD_NOT_VERIFY (candle and recorder data and sim trigger files are not committed); registration order and internal arithmetic only.
- Fee rescore at 10 contracts (V2 harness finding): COULD_NOT_VERIFY (no rescore file committed); direction is right; "no verdict changes" is plausible, not proven (COMBO3 1.398 + 0.07 is about 1.47, thin).
- HISTBTC1, HISTETH1, COINRACE1, COMBO1 to 3, BINPATH, SERIESLAG1: counts and profit factors COULD_NOT_VERIFY (raw data absent); N and z arithmetic VERIFIED (1,290,505 gives z 5.373; 1,450,505 gives z 5.394); SERIESLAG1 NOT_ENOUGH_DATA is correct by its own rule (n 44 under 150).
- Discrepancies: HISTBTC1 registered 22,502 development rows, result says 22,605 (unexplained); registration and result commits are 24 to 123 seconds apart and the scan ledgers are not on the branch, so registration-before-result is not provable from git; HISTBTC1 and HISTETH1 both report exactly 2,079 held-out markets (recount).
- Stronger than the evidence: "family closed" on the Jun to Aug 2026 feed (a quote-regime caveat V2 states itself); OICORE live 16% vs 28% sim is p about 0.03 to 0.04 unadjusted across several looks.

## 2026-11-09 follow-up (V2's answers, V2 commit 861f41d, workers/DATA_CHECKSUMS.txt)
- 22,502 vs 22,605 dev rows: PLAUSIBLE, not proven: the fetch loop was still growing the table between the protocol (6,023 markets) and the scans; verdicts do not hinge on it (best PF 1.384 vs bar 1.5). Fix agreed: freeze the table (row count and hash) in the protocol.
- 2,079 held-out markets in both HISTBTC1 and HISTETH1: RECOUNTED by V2 (each 22 dates, close from 2026-07-15, same windows in both series); accepted.
- Registration order: agreed fix: push the registration commit alone and cite its hash and the ledger file in the result; ledgers for HISTBTC1 and HISTETH1 are now on the branch.
- 10-contract rescore: V2 will commit a script and rows (still open); COMBO3 about 1.47 stays "thin, not a survivor either way".
- Wording: "closes the family" becomes "not found on this feed (Jun to Aug 2026 quote regime)".
