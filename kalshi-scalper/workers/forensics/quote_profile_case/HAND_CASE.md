# Hand case for kxinx15m_quote_profile.py (Forensics desk, Nov 13, 2026; written and frozen BEFORE the script was run)

Made-up data only (`make_fixture.py` builds a fake run folder; no Kalshi data). Three windows. Prices are close dollars of yes_bid / yes_ask, shown here in cents.

Window A (KXINX15M-26NOV051300-00), 13 candles:
| # | bid, ask | counts as |
|---|---|---|
| 1 | 49, 51 | two-sided, spread 2; cheap ask min(51, 51) = 51, no |
| 2 | 50, 51 | two-sided, spread 1; cheap min(51, 50) = 50, no |
| 3 | 70, 73 | two-sided, spread 3; cheap min(73, 30) = 30, YES (upper edge) |
| 4 | 71, 75 | two-sided, spread over 3 (4); cheap min(75, 29) = 29, YES |
| 5 | 0, 5 | not two-sided (bid 0) |
| 6 | 95, 100 | not two-sided (ask 1) |
| 7 | 20, 22 | two-sided, spread 2; cheap min(22, 80) = 22, YES |
| 8 | bid absent, ask 40 | missing quote |
| 9 | 40, 40 | not two-sided (bid at the ask) |
| 10 | 69, 72 | two-sided, spread 3; cheap min(72, 31) = 31, no (just outside) |
| 11 | 30, 33 | two-sided, spread 3; cheap min(33, 70) = 33, no |
| 12 | 80, 81 | two-sided, spread 1; cheap min(81, 20) = 20, YES (lower edge) |
| 13 | 0.5000 bid is fine, ask "0.5050" | off-cent, excluded from every other count |
Window A totals: candles 13, two_sided 8, spread_1c 2 (#2, #12), spread_2c 2 (#1, #7), spread_3c 3 (#3, #10, #11), spread_over3c 1 (#4), cheap_20_30 4 (#3, #4, #7, #12), not_two_sided 3 (#5, #6, #9), missing_quote 1 (#8), off_cent 1 (#13). 8 + 3 + 1 + 1 = 13.

Window B (KXINX15M-26NOV051315-15): named in the request, the answer holds no candles. windows_no_candles 1.

Window C (KXINX15M-26NOV051330-30): end time 100 bid 45 ask 47 (twice, same prices, on a second page: one duplicate, no conflict); end time 160 bid 45 ask 48 (and again with ask 49: a duplicate and a CONFLICT, first answer kept). Counts: candles 2, two_sided 2, spread_2c 1, spread_3c 1, cheap_20_30 0 (cheap asks 47 and 48... min(47, 55) = 47, min(48, 55) = 48), duplicate answers 2, conflicts 1.

One other ticker (KXINX15M-26NOV051345-45, not in any request) appears in an answer: ignored, counted once.

Expected run totals: windows 3, windows_no_candles 1, windows_with_a_two_sided_minute 2 (A, C), windows_with_a_cheap_20_30_minute 1 (A), candles 15, two_sided 10, spread_1c 2, spread_2c 3, spread_3c 4, spread_over3c 1 (2 + 3 + 4 + 1 = 10), cheap_20_30 4, not_two_sided 3, missing_quote 1, off_cent 1, duplicate_answers 2, duplicate_conflicts 1, other_tickers_ignored 1.

Refusal cases (expected exit 1, a REFUSED line): (R1) a run whose request names KXINX15M-26DEC011000-00; (R2) a manifest whose status is not complete; (R3) a run folder whose path contains HELDOUT_.
