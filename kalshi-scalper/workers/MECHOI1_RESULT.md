# MECHOI1 result: why does OICORE work? (2026-11-03; registered in afab6e8 before any outcome; `src/scalper/mechoi1.py`, `tests/test_mechoi1.py`; one run, refuses a second)

Bitcoin 15 minute markets, W1 + W2 only (60 dates, 2026-08-06 to 2026-10-04); **W3 (2026-10-05 to 2026-11-03) never built into a record, no second look.** 3,119 windows with a cheaper side; FIXED trigger (doi > 86,299.56) n 344, baseline n 2,750; REL trigger (trailing 24 h p90) n 332. Parity before scoring: discovery n 222, PF 2.28 reproduced. Fee 7% x C x p x (1-p) rounded up, C = 10, fill at the next candle's ask, held. OKX BTC-USDT 1 minute spot. 95% intervals are day-clustered bootstrap (2,000 reps). N 728,726 -> **728,727** (z bar 5.27). Optimistic by selection: OICORE's threshold was fitted on Aug 6 to Sep 20, inside this sample.

## Verdict by the registered rule (primary FIXED; REL gives the same labels)
**No mechanism is SUPPORTED. M1 (volatility event) is LEANING, M2 / M3 / M4 are NOT SUPPORTED.** What the data do show is a mixture that none of the four stories predicted whole: after the jump (1) the spot moves MORE in the last 3 minutes and (2) it leans toward the cheaper side, (3) while the signal window itself was not unusually volatile, and (4) the edge pays both ways, is not concentrated in a stale quote and is not lumpy.

| mechanism | registered lines | result | label |
|---|---|---|---|
| M1 vol event | R_post >= 1.20 with CI above 1 | **1.22 [1.10, 1.36]** pass (REL 1.21 [1.10, 1.32]) | |
| | no directional lean, abs <= 0.10 sd | **+0.29 sd [0.18, 0.41]** FAIL (REL +0.34) | |
| | pays in both directions >= 3c each | YES-cheaper +11.6c [6.3, 16.8], NO-cheaper +10.4c [4.8, 15.8] pass | |
| | far minus near >= 3c | +6.7c [-4.4, 17.0] point passes, CI crosses (REL +1.2c, fails) | **LEANING** |
| M2 informed direction | signal-window lean >= 0.15 sd, CI > 0 | +0.13 sd [0.05, 0.21] fails the size line | |
| | post lean >= 0.10 sd, CI > 0 | +0.29 sd [0.18, 0.41] pass | |
| | edge concentrated where Dsig > 0, split >= 5c | **-0.2c [-7.5, 7.4]**: Dsig > 0 +11.0c, Dsig <= 0 +11.1c, FAIL | **NOT SUPPORTED** |
| M3 stale maker | unchanged-ask split >= 4c, CI > 0 | -1.6c [-21.0, 14.7]; only 5.5% of trigger windows (19) have the ask unchanged within 1c, vs 5.3% in the baseline | **NOT SUPPORTED** (and nearly untestable) |
| | spread not wider | median 1c in both: pass | |
| M4 lumpy | lumpy split >= 4c, CI > 0 | -2.0c [-12.7, 8.6]; lumpy (>= 60% in one minute) 19.5% of triggers vs 30.8% of baseline (n 67 vs 277) | **NOT SUPPORTED** |

## The numbers that carry it (FIXED rise, W1 + W2)
- The edge in this sample: win rate 29.1% [24.4, 34.2] against an average fill of 18.0%, excess +11.1c [7.8, 14.6] per contract before fees, +9.7c [5.8, 13.7] over the baseline's +1.4c; net +10.3c per contract after fees, PF 2.28 [1.79, 2.94] against 1.04 [0.92, 1.18] for the baseline. W1 PF 2.56 (n 151), W2 2.09 (n 193). The edge is a WIN RATE far above the price, not a payoff effect.
- Spot after the look: absolute move over the last 180 s is 1.22x the same-day baseline (1.23x in sd units of the trailing hour's volatility, so the extra is NOT just "it was already a volatile hour"). Directional lean of that move toward the cheaper side: +0.29 sd above baseline.
- Spot before the look: the signal window's absolute move is 0.88x baseline [0.80, 0.98], i.e. NOT larger; the jump does not mark a move that has already happened (lean +0.13 sd, small). The extra movement comes AFTER the quote was read. This is the finding that most separates the jump from "volatility already underway".
- Back-of-envelope (not registered, no data touched): at a 18c longshot a 1.22x wider distribution lifts the win chance by about 4 to 5c; a lean of 0.29 sd by up to 8c if applied to every window; the observed gross excess over baseline is 9.7c. So both pieces are the right size and neither can be ruled out as the larger one. The intervals do not separate them.
- OKX closes on the same side of the strike as Kalshi's result in only 78.2% of windows: the spot proxy is noisy near the strike (Kalshi settles on a reference-rate average). Move size and lean are less affected than the strike-gap terciles (FAR/NEAR), which should be read loosely.
- Power: subset differences have half-widths of 8c to 20c (M3's unchanged subset is 19 windows). A "NOT SUPPORTED" on M3 and M4 means the point estimates fail, not that the intervals exclude a 4c effect.

## The mirror: OI DROP of the same size (information, no decision line)
- FIXED drop (doi < -86,299.56): **n 25 -> NOT_ENOUGH_DATA** (under 60). Point: win 32.0% vs fill 26.5%, excess +5.5c [-12.0, 26.2], PF 1.32 [0.37, 5.54]. Uninformative.
- REL drop (doi < -trailing 24 h p90): **n 31 -> NOT_ENOUGH_DATA.** Point: win 41.9% vs fill 30.8%, excess +11.1c [-4.3, 28.0], PF 1.84 [0.71, 6.45]. Uninformative.
- Registered fallback (doi below the trailing 24 h 10th percentile), **n 176**: win 27.3% vs fill 26.8%, excess **+0.5c [-5.0, 6.4]**, vs baseline -0.8c [-6.0, 5.2], net -0.5c, **PF 0.96 [0.59, 1.53]** vs baseline 1.03. **An OI drop does NOT predict the opposite and carries no edge: the cheaper side wins about its price.** Its post-look move is also bigger (R_post 1.24 [1.02, 1.46]) with no lean (-0.08 sd [-0.22, 0.07]); its signal-window move is 2.1x baseline with a lean AWAY from the cheaper side (-0.63 sd): drops follow big moves against the cheaper side (positions closing), which is already in the price. So a bigger post-look move alone (drop: 1.24x, no edge) is NOT enough; the rise's edge needs the lean.

## What this means
The data say the OICORE edge is "more movement and a lean toward the cheaper side in the last 3 minutes, in windows where nothing unusual had yet happened in spot, from open interest that built evenly rather than in a few big prints, with a normal 1c spread and a quote that moved". That fits a world where the open interest jump is new positions (not closing, as the drop mirror shows) put on while the quote still reflected a calm signal window, followed by spot moves in their favour; it does not name who loses. It fits MECH1's finding of no whales and an even favourite/cheap taker split. The extra movement alone is not enough (drop). **The lean is the part no registered mechanism owned whole**, and it is the part that would need a pre-registered test on its own (for example on the held-out W3, which this file did not read). It does not meet the bar for a named counterparty.

**Would a number matter to the L1 chat?** Plainly: in jump windows the opposite side of the cheaper side (the favourite, L1's side) wins 70.9% of the time against 82.0% priced, i.e. the cheaper side wins 29.1% against 18.0% paid. But the jump is measured at 180 s before the close, after L1's 6 and 10 minute entries, so it cannot filter an L1 entry; it could only matter as an exit trigger, which EXITOI and EXITOI-G already tested (hold PF 1.158 vs sell 1.120, FALSIFIED). Nothing here proposes a filter.

## Derived trigger ideas
None. The registration allows ideas only if a mechanism is SUPPORTED; none is. (For the record, the one thing worth a registered look by someone is the post-look lean, not a trade: it would be tested first as a spot-direction forecast on W3.)

---

Windows with a cheaper side in the first two thirds: 3119 of 5685 with a usable open interest pair; dates 2026-08-06 to 2026-10-04 (60 dates). Holdout 2026-10-05 to 2026-11-03 not read. Spot available: 3117. OKX close on the right side of the strike as Kalshi settled: 0.782.


## fixed_rise: n 344
| statistic | point [95% day-clustered CI] |
|---|---|
| n_t | 344.000 [290.000, 401.000] |
| win_t | 0.291 [0.244, 0.342] |
| fill_t | 0.180 [0.153, 0.208] |
| exc_t (cents) | 11.1 [7.8, 14.6] |
| exc_b (cents) | 1.4 [-0.2, 2.9] |
| exc_diff (cents) | 9.7 [5.8, 13.7] |
| net_t (cents) | 10.3 [7.1, 13.8] |
| net_b (cents) | 0.5 [-1.0, 2.0] |
| pf_t | 2.283 [1.793, 2.937] |
| pf_b | 1.043 [0.917, 1.176] |
| R_post | 1.222 [1.095, 1.364] |
| R_sig | 0.883 [0.796, 0.980] |
| R_post_sd | 1.232 [1.109, 1.368] |
| lean_post | 0.288 [0.175, 0.409] |
| lean_sig | 0.133 [0.054, 0.211] |
| exc_yes_t (cents) | 11.6 [6.3, 16.8] |
| exc_no_t (cents) | 10.4 [4.8, 15.8] |
| exc_far_t (cents) | 14.9 [9.2, 21.0] |
| exc_near_t (cents) | 8.2 [0.0, 17.1] |
| far_near_t (cents) | 6.7 [-4.4, 17.0] |
| far_near_b (cents) | 1.4 [-2.3, 4.7] |
| exc_dpos_t (cents) | 11.0 [5.8, 16.3] |
| exc_dneg_t (cents) | 11.1 [6.2, 16.2] |
| dsplit_t (cents) | -0.2 [-7.5, 7.4] |
| share_dpos_t | 0.433 [0.389, 0.480] |
| share_dpos_b | 0.410 [0.392, 0.429] |
| share_unch_t | 0.055 [0.034, 0.078] |
| share_unch_b | 0.053 [0.044, 0.063] |
| exc_unch_t (cents) | 9.5 [-9.6, 24.9] |
| exc_mov_t (cents) | 11.1 [7.7, 14.8] |
| unch_split_t (cents) | -1.6 [-21.0, 14.7] |
| spread_t (cents) | 1.0 [1.0, 1.0] |
| spread_b (cents) | 1.0 [1.0, 1.0] |
| spread_diff (cents) | -0.0 [-0.0, 0.0] |
| share_lumpy_t | 0.195 [0.160, 0.237] |
| share_lumpy_b | 0.308 [0.291, 0.325] |
| exc_lumpy_t (cents) | 9.5 [0.6, 18.4] |
| exc_even_t (cents) | 11.4 [7.3, 15.8] |
| lumpy_split_t (cents) | -2.0 [-12.7, 8.6] |
| n_lumpy_t | 67.000 [51.000, 84.000] |
| n_even_t | 277.000 [230.000, 326.000] |

## fixed_drop: n 25
| statistic | point [95% day-clustered CI] |
|---|---|
| n_t | 25.000 [12.000, 39.000] |
| win_t | 0.320 [0.118, 0.565] |
| fill_t | 0.265 [0.180, 0.336] |
| exc_t (cents) | 5.5 [-12.0, 26.2] |
| exc_b (cents) | 1.4 [-0.2, 2.9] |
| exc_diff (cents) | 4.1 [-13.3, 25.0] |
| net_t (cents) | 4.5 [-12.8, 25.1] |
| net_b (cents) | 0.5 [-1.0, 2.0] |
| pf_t | 1.315 [0.368, 5.541] |
| pf_b | 1.043 [0.917, 1.176] |
| R_post | 1.413 [0.984, 1.878] |
| R_sig | 2.738 [2.149, 3.596] |
| R_post_sd | 1.213 [0.891, 1.517] |
| lean_post | 0.215 [-0.183, 0.636] |
| lean_sig | -1.175 [-1.598, -0.846] |
| exc_yes_t (cents) | -14.0 [-42.5, 57.0] |
| exc_no_t (cents) | 14.6 [-4.3, 35.8] |
| exc_far_t (cents) | 28.1 [5.1, 53.6] |
| exc_near_t (cents) | 7.2 [-27.0, 49.9] |
| far_near_t (cents) | 20.8 [-22.6, 53.6] |
| far_near_b (cents) | 1.4 [-2.3, 4.7] |
| exc_dpos_t (cents) | 3.9 [-40.0, 53.7] |
| exc_dneg_t (cents) | 5.8 [-12.9, 28.5] |
| dsplit_t (cents) | -1.9 [-49.4, 44.1] |
| share_dpos_t | 0.200 [0.069, 0.333] |
| share_dpos_b | 0.410 [0.392, 0.429] |
| share_unch_t | 0.040 [0.000, 0.158] |
| share_unch_b | 0.053 [0.044, 0.063] |
| exc_unch_t (cents) | -9.3 [-9.3, -9.3] |
| exc_mov_t (cents) | 6.1 [-12.0, 28.0] |
| unch_split_t (cents) | -15.4 [-36.9, 2.8] |
| spread_t (cents) | 1.0 [1.0, 1.0] |
| spread_b (cents) | 1.0 [1.0, 1.0] |
| spread_diff (cents) | 0.0 [0.0, 0.0] |
| share_lumpy_t | 0.640 [0.478, 0.882] |
| share_lumpy_b | 0.308 [0.291, 0.325] |
| exc_lumpy_t (cents) | 11.5 [-6.9, 29.0] |
| exc_even_t (cents) | -5.4 [-31.2, 30.0] |
| lumpy_split_t (cents) | 16.9 [-12.9, 47.1] |
| n_lumpy_t | 16.000 [9.000, 24.000] |
| n_even_t | 9.000 [2.000, 18.000] |

## rel_rise: n 332
| statistic | point [95% day-clustered CI] |
|---|---|
| n_t | 332.000 [299.000, 365.000] |
| win_t | 0.286 [0.239, 0.339] |
| fill_t | 0.170 [0.144, 0.196] |
| exc_t (cents) | 11.7 [7.9, 15.6] |
| exc_b (cents) | 1.2 [-0.5, 2.9] |
| exc_diff (cents) | 10.4 [6.1, 14.9] |
| net_t (cents) | 10.9 [7.2, 14.8] |
| net_b (cents) | 0.4 [-1.3, 2.0] |
| pf_t | 2.372 [1.803, 3.095] |
| pf_b | 1.032 [0.897, 1.177] |
| R_post | 1.205 [1.103, 1.319] |
| R_sig | 0.946 [0.841, 1.059] |
| R_post_sd | 1.263 [1.137, 1.394] |
| lean_post | 0.339 [0.222, 0.471] |
| lean_sig | 0.037 [-0.048, 0.127] |
| exc_yes_t (cents) | 12.8 [7.3, 18.5] |
| exc_no_t (cents) | 10.2 [4.8, 15.9] |
| exc_far_t (cents) | 12.5 [6.4, 19.2] |
| exc_near_t (cents) | 11.2 [3.1, 20.0] |
| far_near_t (cents) | 1.2 [-10.1, 12.6] |
| far_near_b (cents) | 1.0 [-2.8, 4.4] |
| exc_dpos_t (cents) | 13.0 [7.4, 19.1] |
| exc_dneg_t (cents) | 10.7 [5.9, 15.6] |
| dsplit_t (cents) | 2.4 [-5.2, 10.1] |
| share_dpos_t | 0.416 [0.366, 0.466] |
| share_dpos_b | 0.420 [0.399, 0.442] |
| share_unch_t | 0.048 [0.030, 0.067] |
| share_unch_b | 0.055 [0.046, 0.065] |
| exc_unch_t (cents) | 3.8 [-14.6, 22.7] |
| exc_mov_t (cents) | 12.1 [8.4, 15.9] |
| unch_split_t (cents) | -8.3 [-26.4, 9.3] |
| spread_t (cents) | 1.0 [0.3, 1.0] |
| spread_b (cents) | 1.0 [1.0, 1.0] |
| spread_diff (cents) | -0.0 [-0.7, 0.0] |
| share_lumpy_t | 0.196 [0.157, 0.239] |
| share_lumpy_b | 0.293 [0.275, 0.311] |
| exc_lumpy_t (cents) | 12.8 [2.3, 23.8] |
| exc_even_t (cents) | 11.4 [7.1, 15.9] |
| lumpy_split_t (cents) | 1.4 [-10.4, 13.7] |
| n_lumpy_t | 65.000 [50.000, 81.000] |
| n_even_t | 267.000 [237.000, 298.000] |

## rel_drop: n 31
| statistic | point [95% day-clustered CI] |
|---|---|
| n_t | 31.000 [17.000, 46.000] |
| win_t | 0.419 [0.250, 0.621] |
| fill_t | 0.308 [0.230, 0.393] |
| exc_t (cents) | 11.1 [-4.3, 28.0] |
| exc_b (cents) | 1.2 [-0.5, 2.9] |
| exc_diff (cents) | 9.9 [-5.4, 26.9] |
| net_t (cents) | 10.0 [-5.4, 26.8] |
| net_b (cents) | 0.4 [-1.3, 2.0] |
| pf_t | 1.839 [0.712, 6.447] |
| pf_b | 1.032 [0.897, 1.177] |
| R_post | 1.267 [0.948, 1.603] |
| R_sig | 3.038 [2.438, 3.864] |
| R_post_sd | 1.143 [0.897, 1.363] |
| lean_post | 0.251 [0.011, 0.523] |
| lean_sig | -1.021 [-1.558, -0.607] |
| exc_yes_t (cents) | 5.0 [-29.5, 54.6] |
| exc_no_t (cents) | 14.1 [-1.9, 34.3] |
| exc_far_t (cents) | 25.7 [7.1, 46.1] |
| exc_near_t (cents) | 22.0 [-14.1, 57.5] |
| far_near_t (cents) | 3.7 [-35.9, 41.9] |
| far_near_b (cents) | 1.0 [-2.8, 4.4] |
| exc_dpos_t (cents) | 22.3 [-12.4, 54.0] |
| exc_dneg_t (cents) | 7.2 [-9.2, 26.8] |
| dsplit_t (cents) | 15.1 [-22.6, 47.2] |
| share_dpos_t | 0.258 [0.130, 0.381] |
| share_dpos_b | 0.420 [0.399, 0.442] |
| share_unch_t | 0.032 [0.000, 0.125] |
| share_unch_b | 0.055 [0.046, 0.065] |
| exc_unch_t (cents) | -9.3 [-9.3, -9.3] |
| exc_mov_t (cents) | 11.8 [-4.0, 29.9] |
| unch_split_t (cents) | -21.1 [-39.4, -4.9] |
| spread_t (cents) | 1.0 [1.0, 1.0] |
| spread_b (cents) | 1.0 [1.0, 1.0] |
| spread_diff (cents) | 0.0 [0.0, 0.0] |
| share_lumpy_t | 0.581 [0.440, 0.760] |
| share_lumpy_b | 0.293 [0.275, 0.311] |
| exc_lumpy_t (cents) | 13.1 [-3.1, 31.4] |
| exc_even_t (cents) | 8.4 [-16.4, 31.6] |
| lumpy_split_t (cents) | 4.7 [-16.6, 29.1] |
| n_lumpy_t | 18.000 [10.000, 27.000] |
| n_even_t | 13.000 [5.000, 22.000] |

## rel_drop_p10: n 176
| statistic | point [95% day-clustered CI] |
|---|---|
| n_t | 176.000 [135.000, 215.000] |
| win_t | 0.273 [0.209, 0.342] |
| fill_t | 0.268 [0.232, 0.306] |
| exc_t (cents) | 0.5 [-5.0, 6.4] |
| exc_b (cents) | 1.2 [-0.5, 2.9] |
| exc_diff (cents) | -0.8 [-6.0, 5.2] |
| net_t (cents) | -0.5 [-6.0, 5.4] |
| net_b (cents) | 0.4 [-1.3, 2.0] |
| pf_t | 0.961 [0.591, 1.529] |
| pf_b | 1.032 [0.897, 1.177] |
| R_post | 1.236 [1.023, 1.463] |
| R_sig | 2.145 [1.909, 2.398] |
| R_post_sd | 1.174 [1.007, 1.356] |
| lean_post | -0.076 [-0.220, 0.069] |
| lean_sig | -0.632 [-0.781, -0.471] |
| exc_yes_t (cents) | -0.1 [-7.2, 7.5] |
| exc_no_t (cents) | 1.0 [-6.7, 9.5] |
| exc_far_t (cents) | 3.0 [-5.0, 12.2] |
| exc_near_t (cents) | 2.7 [-6.8, 12.1] |
| far_near_t (cents) | 0.3 [-12.5, 14.4] |
| far_near_b (cents) | 1.0 [-2.8, 4.4] |
| exc_dpos_t (cents) | 7.0 [-3.2, 16.7] |
| exc_dneg_t (cents) | -2.1 [-8.4, 4.2] |
| dsplit_t (cents) | 9.1 [-2.6, 20.6] |
| share_dpos_t | 0.284 [0.232, 0.335] |
| share_dpos_b | 0.420 [0.399, 0.442] |
| share_unch_t | 0.023 [0.005, 0.047] |
| share_unch_b | 0.055 [0.046, 0.065] |
| exc_unch_t (cents) | 23.5 [-9.3, 94.8] |
| exc_mov_t (cents) | -0.1 [-5.2, 5.5] |
| unch_split_t (cents) | 23.6 [-6.8, 94.0] |
| spread_t (cents) | 1.0 [1.0, 1.0] |
| spread_b (cents) | 1.0 [1.0, 1.0] |
| spread_diff (cents) | 0.0 [0.0, 0.0] |
| share_lumpy_t | 0.534 [0.461, 0.605] |
| share_lumpy_b | 0.293 [0.275, 0.311] |
| exc_lumpy_t (cents) | 0.3 [-7.0, 8.0] |
| exc_even_t (cents) | 0.7 [-7.3, 9.0] |
| lumpy_split_t (cents) | -0.5 [-11.4, 10.3] |
| n_lumpy_t | 94.000 [70.000, 120.000] |
| n_even_t | 82.000 [60.000, 105.000] |

## Labels (primary: fixed 86,299.56 rise; second version: relative trailing 24h p90 rise)
- fixed: M1 LEANING, M2 NOT SUPPORTED, M3 NOT SUPPORTED, M4 NOT SUPPORTED
  - M1 lines: {'ratio': (True, True), 'no_lean': False, 'both_directions': True, 'far_gt_near': True}
  - M2 lines: {'sig_lean': (False, True), 'post_lean': (True, True), 'concentrated': False}
  - M3 lines: {'split': (False, False), 'unchanged_pays': True, 'spread_not_wider': True}
  - M4 lines: {'split': (False, False), 'lumpy_pays': True}
- rel: M1 LEANING, M2 NOT SUPPORTED, M3 NOT SUPPORTED, M4 NOT SUPPORTED
  - M1 lines: {'ratio': (True, True), 'no_lean': False, 'both_directions': True, 'far_gt_near': False}
  - M2 lines: {'sig_lean': (False, False), 'post_lean': (True, True), 'concentrated': False}
  - M3 lines: {'split': (False, False), 'unchanged_pays': True, 'spread_not_wider': True}
  - M4 lines: {'split': (False, False), 'lumpy_pays': True}

## Halves (fixed rise, point values)
- W1: n 151, exc 12.5c, R_post 1.342, lean_post 0.312, unch_split -12.0c, lumpy_split 2.4c, PF 2.56
- W2: n 193, exc 9.9c, R_post 1.135, lean_post 0.269, unch_split 2.1c, lumpy_split -5.3c, PF 2.09
