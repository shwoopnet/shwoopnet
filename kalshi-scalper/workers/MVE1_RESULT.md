# MVE1 result (2026-11-06): NOT_ENOUGH_DATA (treated n 11, 3), no lead; CONTROL information only

Registered first (`workers/MVE1_REGISTRATION.md`, commit b2520c6). Scored once with `python3 -m scalper.mve1 score <cache>`; code `src/scalper/mve1.py`. Window: combos closing 2026-09-06 to before 2026-10-03T16:00Z (frozen third never fetched), two 20 minute close windows a day, halves cut 2026-09-20. Pool: 13,975 traded combos with 2 to 5 yes legs; 400 cheap-side candidates (first print 3c to 30c, md5 rank, 726 combos processed); 336 had every leg priced at the print minute, 64 failed on a leg quote. Taker at the print, held, fee 7% x C x p x (1-p) rounded up, C = 10, x1.2 stress. N +2 (running about 730,451, z bar 5.27).

| arm | n (hours) | win | avg print | net c/contract | PF | clustered z | D1 / D2 net | fees x1.2 |
|---|---|---|---|---|---|---|---|---|
| CONTROL (all with R) | 336 (195) | 16.7% | 14.1c | +1.76 | 1.15 | +0.86 | +2.10 / +1.24 | +1.60, PF 1.14 |
| TRY A, R <= 0.80 | 11 (9) | 27.3% | 13.6c | +12.77 | 2.24 | +1.29 | +26.98 (n 5) / +0.93 (n 6) | +12.63 |
| TRY B, R <= 0.50 | 3 (3) | 33.3% | 11.6c | +21.00 | 3.88 | +0.80 | +38.70 (n 2) / -14.40 (n 1) | +20.87 |
| info, R >= 1.25 | 114 (75) | 11.4% | 12.5c | -1.86 | 0.83 | -0.67 | -2.64 / -0.52 | -2.00 |

Verdict: NOT_ENOUGH_DATA for A and B (11 and 3 treated against 150 needed, z 1.29 and 0.80 against 5.27). The numeric prediction missed: median R was 1.12 (10th to 90th percentile 0.96 to 2.65), so combos were NOT systematically overpriced against the product, and CONTROL was +1.76c, not -7c to -10c. The mean R of 47.7 is an outlier artifact (a leg with a near zero mid), use the median. Only 3 percent of candidates are priced at least 20 percent under the independence product, so about 40 treated per 1,000 candidates; reaching 150 needs about 4,000 candidates (about 5 more hours of a shared rate limited fetch) and would still face the fill problem.

What it means: (1) the one RFQ print is the only visible price and there is no standing ask (yes ask 1.00 after the print), so even the +1.76c CONTROL is an upper bound that a later buyer could not obtain; the favourable sign is within noise (z 0.86, win 16.7% against 14.1% priced) and is not a finding. (2) The conjunction is priced close to the product of its legs (median ratio 1.12), so no systematic mispricing of that kind is visible at this sample size. (3) The combos that are expensive against their legs (R >= 1.25) do lose (-1.86c) but that is the likely-NO side, which is out of scope. No forward probe: nothing to probe without a way to obtain an RFQ quote. No lead. Gap not tested: correlated same-game legs (this collection is almost all cross category).
