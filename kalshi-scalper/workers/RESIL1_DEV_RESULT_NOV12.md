# RESIL1 development result (Idea Desk A, Nov 12, 2026). Script `desk_a_verify/resil1.py` (commit 4236f81e) was committed and self-tested before this run; nothing tuned.

Development = windows closing from 2026-10-29T22:15Z to before 2026-11-05T00:00Z on the five R6 series; held-out (closes on or after Nov 5) not opened. 1,944 windows with a sweep in the 12 to 4 minute span: 1,742 traded, 101 had no pre-sweep poll, 101 had an entry ask out of band or empty.

- **Registered rule (swept side NOT refilled, buy at the ask one minute later, hold): n 1,061, cash PF 0.90, mean -2.11c, 538 wins.**
- Descriptive, no try (refilled arm): n 681, cash PF 0.95, mean -1.13c, 309 wins.
- Label by the registration: **FALSIFIED on development** (cash PF under 1.0 with n of 100 or more). The held-out is not read.

Reading: following a sweep, refilled or not, pays about the price plus the fee, i.e. no edge in either arm; the "not refilled" arm is not better than the "refilled" arm. This is the order-flow family's third FALSIFIED (FLOW1, TAPEFLOW1, RESIL1) by the registered rule. Subject to the Verification Analyst's re-run. Caveat: the sweep (two or more prices in one second) is common on these books (every window had one in the span), so the first one is a weak marker; the price-based refill field is the registered design change and was not varied.
