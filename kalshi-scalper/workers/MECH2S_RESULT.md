# MECH2S result (run once, 2026-11-04)

Registration sha256 `b16e614e98957eec37b1bff5a373d4db844b5a54cbba6bbf0fea97d4d86c44e7` (commit a980013). Pool 16,201 cheap rows (ask 3c-30c), MECH1S code, fee 7% x C x p x (1-p) rounded up, C=10, taker at ask, held to settlement. Net c/contract; event-clustered 95% interval.

| mechanism | n | ALL net [95%] | D1 | D2 | TEST | PF | placebo n / net | verdict |
|---|---|---|---|---|---|---|---|---|
| PATH_FALL | 2753 | -6.29 [-7.40, -5.26] | -6.38 (n 613) | -4.57 (n 859) | -7.40 (n 1281) | 0.47 | 1049 / -8.19 | FALSIFIED |
| VS_OPEN | 2869 | -5.03 [-5.99, -4.05] | -5.88 (n 998) | -4.47 (n 1111) | -4.74 (n 760) | 0.50 | 2107 / -5.11 | FALSIFIED |
| WEEKEND | 2275 | -4.97 [-6.40, -3.57] | -4.17 (n 920) | -4.58 (n 614) | -6.27 (n 741) | 0.61 | 2882 / -6.72 | FALSIFIED |
| SHOULDER | 1798 | -6.04 [-7.56, -4.56] | -5.45 (n 387) | -5.15 (n 495) | -6.78 (n 916) | 0.63 | 1232 / -5.82 | FALSIFIED |
| SPREADM | 1225 | -4.34 [-6.77, -1.91] | -7.01 (n 414) | -2.05 (n 403) | -3.90 (n 408) | 0.74 | 3031 / -10.61 | FALSIFIED |
| FEE_WASTE | 2178 | -5.54 [-6.62, -4.34] | -4.36 (n 612) | -4.43 (n 582) | -6.92 (n 984) | 0.51 | 2627 / -5.75 | FALSIFIED |
| VOLRANK | 776 | -5.55 [-7.23, -3.71] | -6.49 (n 232) | -6.11 (n 292) | -4.03 (n 252) | 0.48 | 676 / -4.71 | FALSIFIED |

All seven FALSIFIED: every ALL net and every D1, D2 and TEST net is negative and every interval is entirely below zero. Predictions held (-4c to -7c). OFFHOURS (D2 88, test 74) and YDAY (D2 79, test 65) not scored (under 150 in a part), no verdict, no N.

N +14 (7 mechanisms x 2). No forward plan, no candidate, no promote verb.

Caveat: same pool as CALIB1, LIQ1, MECH1S; the best arm (SPREADM -4.34c, upper bound -1.91c) is still about 4c under break-even.
