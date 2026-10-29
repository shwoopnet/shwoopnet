# FALS3 registration: falsifier for GEN4's core (the Bitcoin favourite at 50c to 85c about 148 s before the close)

Worker FALS3, Strategy Research V2, 2026-10-29. Research only. Written and pushed BEFORE any of my own scoring. Before this commit I read `workers/GEN4_REGISTRATION.md`, `workers/GEN4_RESULT.md`, `workers/LATECAL_RESULT.md`, the HUNT2 and UNDER1 sections of `README.md` and `data/under1_result.txt` (top 20 cells), the CSV headers of the recorder and the sqlite schemas and date ranges. I have NOT read `src/scalper/gen4.py`; I will read it only after my own Check 1 numbers exist, to explain differences.

**Under attack.** GEN4_REF_FAV150: Bitcoin `KXBTC15M`, at the FIRST recorder poll with 150 to 120 s left, buy the side whose mid is above 0.5 if its ask is in [0.50, 0.85] (at least 1 contract at the ask), hold to settlement. Claimed PF1 1.61 (n 50, Oct 22 to 26) and 1.57 (n 35, Oct 27 to 29). And B01 (FAV, 150 to 45 s, `lsz_ask <= 7.78`, `zd >= -1.58`, sell at the bid at 30 s): 2.13 / 2.64.

**Counterparty GEN4 would need:** whoever sells the Bitcoin favourite too cheaply about 2.5 minutes before the close. Already in tension with the record: UNDER1 found Bitcoin's CHEAP side (ask 0.30 to 0.45 and below) positive at 2 to 3 minutes left over 79 days, which, after the spread, means the favourite at its ask cannot also be cheap there. Stated now as the reason to expect Check 2 to break it.

## Check 1: independent re-implementation on the recorder (1 try)

Data `origin/quote-data` at `b7dc9cbe823b2b9f734dc085ea03452a1aec3c1b`, `quotes/*/*/quotes.csv.gz` and `results.csv.gz`. Bitcoin rows only; each window (ticker) counted once (first folder holding it); only windows with a results row of yes or no. Seconds left = close_ts - t_recv_ms / 1000 (close_ts from the ticker's Eastern time, cross-checked against results `close_time`). Valid poll: status active, 0 < yes_bid <= yes_ask < 1. Bare rule: the first valid poll with 120 <= s <= 150; FAV = YES if (bid+ask)/2 > 0.5, NO if < 0.5 (exactly 0.5: no entry); side ask (YES ask, or 1 - yes_bid with size bid_size) in [0.50, 0.85] with size >= 1, else no entry in that window (no later poll is tried). Fill at that ask, hold. Fee 7% x C x p x (1 - p) rounded up to the cent per order; C = 1 and C = 10 (min(10, size)). Discovery = close before 2026-10-27 00:00 UTC, validation = 2026-10-27 00:00 to 2026-10-29 23:59:59. Report n, wins, mean ask, PF1, PF10, x1.2, next-poll fill. Also B01 as I read the grammar (spot proxy and zd per GEN4's registration text). Material difference: PF off by more than 0.25 or n off by more than 3 in either window.

## Check 2: long history on 1 minute candles (the decisive check; 1 try per (series, time, fill) cell reported; BTC same-candle cells at 180 and 120 s are the verdict cells)

Markets from `data/l1b.sqlite`, `data/book.sqlite`, `data/fresh.sqlite` (Dogecoin, absent from l1b and book, also from `e3b.sqlite` and `alts2.sqlite`); a ticker in more than one file is taken from the file with more candles; result yes or no only; closes 2026-08-06 to 2026-10-29. Series KXBTC15M (verdict), KXGOLD15M, KXETH15M, KXDOGE15M (comparison). Decision candle: `end_ts == close_ts - T`, T in {180, 120} (150 is not on the grid). Valid: bid_c and ask_c present, 0 < bid_c <= ask_c < 1. FAV as in Check 1 from the candle's closing mid; side ask = ask_c (YES) or 1 - bid_c (NO), in [0.50, 0.85]. Fill A: that ask. Fill B: the NEXT candle's (end_ts + 60) closing ask of the same side, any price, valid quote, else no trade. Hold to settlement. Fees as above at C = 1 and x1.2. Zero-volume decision candles reported both ways (all candles; volume > 0 only). Thirds: three windows of equal day counts by UTC date of the close; the last third is read as the holdout. Also over the recorder's dates only (Oct 22 to 29), split recorded windows vs not recorded.

**BROKEN by Check 2 if** Bitcoin, fill A, all candles, at BOTH T = 180 and T = 120: PF1 below 1.2 over all days, or below 1.5 in two or more thirds (n per third at least 100). The RULES bar (PF 1.5 in each third, positive at x1.2) is reported as information.

HUNT2 and UNDER1: I will state what their output files say for the nearest cells (time 2 and 3 minutes, favourite bands 0.50-0.70 and 0.70-0.88; cheap side 0.10 to 0.45 at 2 and 3 minutes, which is the mirror of a 0.55 to 0.90 favourite).

## Check 3: recorder artefacts (1 try)

(a) Coverage: list every KXBTC15M window closing Oct 22 to 29 in `fresh.sqlite`; mark which are in the recorder with a result row and which have a poll in 120 to 150 s. Compare recorded vs not recorded: YES rate, the candle-based bare rule at T = 180 and 120 (PF, n), and the absolute change in the YES mid from 600 s to 0 / the candle range (a volatility proxy). (b) The first-poll time: distribution of seconds left at the first valid poll; whether windows whose first poll is later than 150 s left (job started mid-window) differ. (c) Whether results.csv rows exist only for some recorded windows, and whether the missing ones differ on the candle rule. **BROKEN by Check 3 if** the candle rule on the same days gives PF at least 0.5 higher on recorded than on non-recorded windows with at least 30 of each, or the recorded subset's YES rate differs from the non-recorded by more than 15 points (z above 2).

## Check 4: fill realism (1 try)

Ask size at the entry poll (median, share under 10 contracts); next-poll fill PF; fees x1.2; for B01 the bid size at the 30 s exit poll and the share of exits that fall back to settlement. **BROKEN by Check 4 if** the next-poll fill or x1.2 turns either window's PF below 1.2, or B01's PF falls below 1.3 in either window when exits need at least 10 contracts at the bid at C = 10.

## Check 5: calibration cross-check with LATECAL (1 try)

Win rate minus mean ask by band (0.50-0.70, 0.70-0.85) for the recorder at 150 to 120 s (first poll) and at 120 to 90 s (LATECAL's cell), and for the candle history at 180 and 120 s. Reported as information; it explains, it does not decide.

## Verdict rule (fixed now)

BROKEN, naming the check, if any of Checks 2, 3 or 4 meets its BROKEN line, or Check 1 does not reproduce within the material-difference limits AND my version is below PF 1.3 in either window. Otherwise SURVIVES THE FALSIFIER (it stays a forward-ledger item; nothing more). Strategy verdict words: if broken, the bare rule is FALSIFIED on the named check.

**Prediction (stated now):** Check 1 reproduces within limits. Check 2 breaks it: Bitcoin favourite 0.50 to 0.85 at 180 and 120 s on 84 days has PF about 0.85 to 1.0 (UNDER1's cheap side was positive there), and the recorder's 8 days were a fluke. Check 3 finds no strong selection. Prior that it survives: 10%.

**Tries:** Checks 1 to 5 = 5 (Check 2's comparison series and fill variants are information inside one try). Running count about 475,577 + 5 = about 475,582.
