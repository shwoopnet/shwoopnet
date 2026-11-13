# S-OICHEAPSKIP1: would OICORE's signals priced under 8c have made money? (read only)

Registered 2026-11-08, BEFORE any skip exists. Source: S/w_design_oi/DESIGN.md (OICORE_SKIP7, PR 742). Measure only: no rule, no order. Public GET only, no key.

## Group
Skip records with reason `cheap_skipped` and time at or after the deploy timestamp (argument, or the file DEPLOY_TS in this folder). Each has ticker, detail.price (the signal price: rounded-up cheaper-side touch) and, in the stored record, the side in `note`. The report's skips section does NOT carry `note` (only detail), so side is read from row.note or row.side if present; otherwise inferred from the public 1 minute candles at the skip time (the side priced under 0.5: yes if the YES mid is under 0.5). Rows whose side cannot be found are counted "side unknown" and excluded, and a report change to carry the side is the fix. Before the deploy there are none: prints NOT DEPLOYED. Outcome: public GET /markets/{ticker} result. Win = result equals the side.

## Cash booking at 5 contracts (design section d)
paid = signal price. Win: 5 x (1 - paid) minus fee. Loss: 5 x paid plus fee. Fee = ceil(7 x 5 x p(1-p))/100 dollars (Kalshi's schedule, rounded up to the cent). Information only: the same signals at OICORE's live size, cash. Also recorded: the deploy date, because OICORE's streak, kill and ladder win-rate inputs change from that day (cheap fills leave its record).

## Prior and multiplicity
The live record is not restated here (privacy rule); none of it is adopted. Sim about 7 percent. About 420 earlier splits tried, so the group was picked after seeing data (selection bias). Tries here: 1 (win count in the group).

## Decision (fixed now)
Read at 40 signals (about 10 days) and again at 80.
- At most 1 win in 40 (net under -$6): PERMANENT SKIP (at 80: at most 3 wins).
- 4 or more wins in 40: DROP THE SKIP.
- Otherwise extend to 80. Weak test: a 2 or 3 win read is not a finding.
Under 40 settled signals: counts only, NO READ.


Dated clarification Nov 13, 2026 (Head of R&D ruling): rule words restored from commit 44dda69f^; nothing re-decided. 10 markers: 7 verbatim (title, side rule, tries, the 40 and 80 signal thresholds and the weak-test and no-read lines); 3 rewritten, 3 sentences: the cash booking line (dropped a remark on how live fills priced against the touch), the information-only line (names the live size without a number) and the prior (the live and forward win counts were removed).

Dated line Nov 13, 2026 (Head of R&D ruling on the owner poll, text only): what feeds this tracker today: the skip records OICORE writes when its signal is priced under 8c (needs the deploy time, see the dated DEPLOY_TS line if one has been added). The read waits for its own count (40 settled signals, then 80) and is not brought forward.
