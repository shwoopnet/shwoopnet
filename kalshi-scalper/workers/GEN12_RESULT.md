# GEN12 result (2026-11-11): FALSIFIED on development, 0 survivors of 300,000, held-out never read

Registration `workers/GEN12_REGISTRATION.md` (committed first), code `src/scalper/gen12.py`, raw output `workers/GEN12_search_output.txt`, frozen list `workers/GEN12_frozen.json` (empty). Basis everywhere: CASH, 1 contract, unrounded fee 0.07 p (1-p) on the entry and every sale, cheap side only (ask 0.04 to 0.30, spread <= 0.03), 15 non-crypto series, development = first two thirds by close time per series (206,800 rows, 44,432 windows, 77 days).

- Strategies drawn and scored: 300,000 (272,637 with at least one trade; 226,261 with n >= 150). N for deflation 1,100,000 (shared 800,000 + 300,000), z bar 5.34 (4.36 at N 7,731).
- Cash PF >= 1.0 on development: 4,635 of 300,000 (1.5 percent, mostly tiny cells). PF >= 1.3 with n >= 150: 5. PF >= 1.5 with n >= 150: 0.
- Stage 1 (PF >= 1.5, n >= 150, 25 days, zero-volume <= 20%): 0. Frozen list: empty. Held-out (last third, 122,837 rows, 32 days) was NOT read; nothing was frozen to read it for.
- Best development cash PF among n >= 150: 1.49 (n 152, 62 days), 1.40 (n 211, 23 days), 1.34 (n 180, 23 days). None is near the z bar; chance-fit sizes for 300,000 draws.
- Overlap with L1-style: not computed (no survivor). No IMPLEMENT, KILL or RETURN rules.
Verdict: FALSIFIED for this grammar on these 15 series (cheap side). Consistent with NONCRYPTO1 (every cheap-side series calibration below 1.05 cash PF). Not tested: favourite-side entries (barred), anything needing sizes or depth, forex beyond 15 to 43 days of history.
