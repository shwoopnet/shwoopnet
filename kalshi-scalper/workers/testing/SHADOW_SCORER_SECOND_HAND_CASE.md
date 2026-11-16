# Shadow scorer, BUILD 2 hand case (Testing Desk, Nov 16, 2026). Written before code.
Spec: per signal, one contract, price p paid (cash), slip s cents worse: paid = min(0.99, p + s/100). Fee per contract = ceil(0.07 x 10 x paid x (1 - paid) x 100 - 1e-9) / 1000 (the 10 contract order fee over 10). Win pays 1 - paid - fee, loss pays -(paid + fee). Net = sum, rounded 4 dp. PF = gross win / gross loss, 3 dp, None when no losses. Only fill-checked, one per ticker and side (first by time), ts >= start and <= now; only a yes/no result is settled (a signal with another result is counted as a signal, not settled).
Independent reading of the engine: engine1_core's fee is fee_up_order(p, n) = ceil(round(0.07 n p (1-p) 100, 9)) / 100 at n = 10, which over 10 is the same number; the JS 1e-9 guard and the engine's 9 dp rounding agree except at exact cent boundaries (checked below).
Cases:
- A 10c yes win: 0.07 x 10 x 0.1 x 0.9 = 0.063, x100 = 6.3, ceil 7, fee 0.007: win 0.893. Loss -0.107. 50c no win: 0.175 x 100 = 17.5, ceil 18, fee 0.018: win 0.482. Cash net 1.268, gross win 1.375, gross loss 0.107, PF 12.850 (12.8504 rounds to 12.85).
- Slip +1c: 11c: 0.07 x 10 x 0.11 x 0.89 = 0.06853, x100 = 6.853, ceil 7, fee 0.007: win 0.883, loss -0.117; 51c: 0.7 x 0.51 x 0.49 = 0.17493, x100 17.493, ceil 18, 0.018: win 0.472. Net 0.883 - 0.117 + 0.472 = 1.238.
- Cap: 98.5c +2c pays 0.99 (not 1.005). Fee 0.07 x 10 x 0.99 x 0.01 = 0.00693, x100 0.693, ceil 1, 0.001: win 0.009, loss -0.991.
- Exact boundary: p = 0.5 gives 17.5 exactly (ceil 18); p = 0.2: 0.7 x 0.16 = 0.112 x 100 = 11.2, ceil 12, fee 0.012.
- No losses: PF None, noLosses true; empty: net 0, PF None, noLosses false.
- Filters: fill_checked False dropped; ts before start dropped; ts after now dropped; duplicate ticker+side keeps the earlier; a None result is a signal, not settled; other spec id dropped.
- Void (known divergence, information): the engine keeps the entry fee on a void (cash -fee); the JS scorer leaves a non-yes/no result out of settled, so a void is unscored there. Not a bug in either, a spec point for the Head.

## Addendum 1 (Head ruling, Nov 16): void follows the engine
A void (result "void") is a scored settled trade: price refunded, entry fee kept as a loss (-fee). None/pending stays unsettled. Output carries voids as its own count. Hand: a 10c yes win (0.893) plus a 10c void (-0.007) plus a pending: signals 3, settled 2, wins 1, losses 1, voids 1, net 0.886, PF 0.893 / 0.007 = 127.571.
