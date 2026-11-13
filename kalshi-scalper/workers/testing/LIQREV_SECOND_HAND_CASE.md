# LIQREV scorer, BUILD 2: hand case (Testing Desk, Nov 13, 2026), committed BEFORE the code
Built from Desk C's LIQREV_CARD.md at d2822839 (sha256 f0257cce verified) with Amendments 1 to 3 ONLY. liqrev_score.py, its tests and hand-case files were NOT read. DEVELOPMENT ONLY (the Head): the read is refused before 2026-11-30T00:00Z and H is an INPUT (never computed here). INVENTED rows only; no real file read. The only real thing looked at: the column NAMES of the OKX recorder's liquidations.csv.gz (t_recv_ms, inst_id, uly, ts_ms, side, pos_side, sz, bk_px, bk_loss, ccy) and coverage.csv.gz header, and the R6 header already verified.

## The rule as I read it (card + R1 to R15)
- Window = a settled KXBTC15M market. Development = closes 2026-11-17T00:00:00Z to before 2026-11-30T00:00:00Z; halves split at 2026-11-23T12:00:00Z (by close). Closes on or after 2026-11-30 are IGNORED and COUNTED (held-out, never read here); closes before 2026-11-17 are ignored and counted.
- R15 coverage: a window is scored only if ONE coverage interval [a, b) contains [close - 900, close - 180): a <= close - 900 and close - 180 <= b. Otherwise "no_liq_coverage".
- R4: trigger minutes t = close - 720 s up to close - 180 s inclusive in steps of 60 (10 checks), in time order. R3: L(t) per side = BTC of that side with t - 180 s <= ts < t (ts from ts_ms). R1: side 'sell' = a long was liquidated: bet YES; 'buy' = a short: bet NO. R2: BTC-USDT-SWAP size = sz x 0.01 BTC; BTC-USD-SWAP = sz x 100 / bk_px BTC; any other inst_id is refused. R12: rows de-duplicated on (inst_id, ts_ms, side, pos_side, bk_px, sz).
- Trigger: the FIRST minute with L(side) >= H - 1e-9 for one side. R5b: both sides at H in that minute: no bet ("both_sides"). At most one bet a window.
- R6 quote: the first R6 poll with t_recv_ms in (t, t + 10 s] (the trigger minute t): none = "no_quote". YES ask = 1 - no_bid_px_1; NO ask = 1 - yes_bid_px_1; spread = YES ask - yes_bid_px_1 (both sides); usable only if 0 < yes bid < YES ask < 1, else "one_sided_quote" (not a two-sided quote, not triggered-with-quote). The first poll only; no later poll or minute is tried.
- R7: the bet side's ask in [0.20, 0.80] and spread <= 0.04, inclusive, 1e-9. Fail = "band_or_spread_fail" (a TRIGGERED window; the window is USED: no later minute is tried). Pass = a bet: 1 contract at the ask, fee 0.07 p (1 - p) rounded up to the cent (scorekit.fee_rounded). Win +1 - p - fee, loss -p - fee, void -fee (a void is a bet). R8/R10: results other than yes, no or void, an empty result, or a duplicate window STOP the run naming the window.
- R14: zero-try count: triggered windows with a two-sided quote = bets + band_or_spread_fail; under 60 = closed. Development closed if bets < 60, PF < 1.0 or a half PF < 1.2; with fewer than 30 bets the label is "no evidence at n = x". R11: PF = gross gain / gross loss, unrounded; z clustered by the US Central date of the close (scorekit.cluster_z, mean of per-day mean nets over its standard error across days with a bet); all bar tests on unrounded values (1e-9).
- R9: no conflict rule in the paper read.

## Invented windows (H = 10 BTC input; every close at 12:00Z of its day unless stated; USDT rows: sz 600 = 6 BTC, 400 = 4, 1100 = 11, 999 = 9.99, 1000 = 10)
| id | close | rows | R6 first poll in (t, t + 10] | outcome |
|---|---|---|---|---|
| W1 | 2026-11-17 | sell 600 at C - 700, sell 400 at C - 650 | at t + 2: yes bid .35, no bid .63 | t = C - 600 is the first minute with L(long) = 10 >= H (the minute C - 660 sees 6); YES ask .37, spread .02: BET YES at .37, fee .0231 rounds to .02; result yes: net +0.61 |
| W2 | 2026-11-18 | buy 1100 at C - 400 | at t + 3: yes bid .62, no bid .35 | t = C - 360 (L(short) = 11; the minute C - 420 does not see a row at C - 400): NO ask .38, YES ask .65, spread .03: BET NO at .38, fee .02; result yes (the NO bet loses): net -0.40 |
| W3 | 2026-11-19 | sell 1000 and buy 1000 both at C - 700 | | both sides at H in the same minute: "both_sides", no bet |
| W4 | 2026-11-19 | sell 999 at C - 700 | | L = 9.99 < H at every minute: "no_trigger" |
| W4b | 2026-11-19 | sell 1000 at C - 700 | at t + 1: yes bid .40, no bid .58 | L = 10 = H exactly: triggers (the tolerance): YES ask .42, spread .02: BET YES at .42; result no: net -0.44 (fee .07 x .42 x .58 = .0171 -> .02) |
| W5 | 2026-11-20 | buy 1100 at C - 400 | none within 10 s (a poll at t + 11) | "no_quote" |
| W6 | 2026-11-20 | sell 1100 at C - 700 | at t + 1: yes bid empty | "one_sided_quote" |
| W7 | 2026-11-21 | sell 1100 at C - 700 | yes bid .12, no bid .02: YES ask .98 | outside 0.20 to 0.80: "band_or_spread_fail"; a LATER minute that would pass is not tried |
| W8 | 2026-11-21 | sell 1100 at C - 700 | yes bid .30, no bid .65: YES ask .35, spread .05 | spread over .04: "band_or_spread_fail" |
| W9 | 2026-11-22 | sell 1100 at C - 700 | (no coverage interval holds the window) | "no_liq_coverage" |
| W10 | 2026-11-24 | sell 1100 at C - 700 | at t + 1: yes bid .49, no bid .49: YES ask .51, spread .02 | BET YES at .51, fee .07 x .51 x .49 = .0175 -> .02; result void: net -0.02 |
| W11 | 2026-11-24 | one BTC-USD-SWAP sell row at C - 700, sz 10,000, bk_px 100,000: 10,000 x 100 / 100,000 = 10 BTC | at t + 2: .45 / .53 | USD swap size rule: BET YES at .47; result yes: net = 1 - .47 - .02 = +0.51 (half 2) |
| W12 | 2026-11-16 | any | | before development: not read, counted |
| W13 | 2026-11-30 | any | | held out: ignored and counted |
Halves: W1, W2, W3, W4, W4b, W5 to W9 are half 1 (closes before 2026-11-23T12:00Z); W10 and W11 are half 2.
Expected with the registered thresholds lowered for the test (min triggered 3, min bets 3, evidence n 3): bets 5 (W1, W2, W4b, W10, W11); no_trigger 1 (W4); both_sides 1; no_quote 1; one_sided_quote 1; band_or_spread_fail 2; no_liq_coverage 1; triggered with a two-sided quote = 5 + 2 = 7. Net: +0.61 - 0.40 - 0.44 - 0.02 + 0.51 = +0.26; gross gain 1.12, gross loss 0.86, PF = 1.12 / 0.86 = 1.3023. Half 1 (W1, W2, W4b): gain .61, loss .84: PF .7262; half 2 (W10, W11): gain .51, loss .02: PF 25.5. Half 1 under 1.2: CLOSED (half PF).
Guards: before 2026-11-30T00:00Z the read refuses before anything is loaded; H None raises; an unknown inst_id raises; duplicate window or odd result text stops the run naming the window.
