# CFRTI-K held-out reader, SECOND BUILD: hand case (Testing Desk, Nov 13, 2026), committed BEFORE the reader code
Written from CFRTI_K_REGISTRATION.md at 57e2b153 on claude/idea-desk-a (sha256 f42574fb) and its dated lines ONLY (sections 1 to 13, the Nov 12 and Nov 13 amendments, the owner's dated line). Desk A's reader and cfrti_k.py were NOT read. MADE-UP numbers; test_cfrti_k_heldout_second.py must reproduce every figure. Nothing here comes from a landed file.

## What the reader does (as I read the card)
- Windows: settled KXBTC15M markets from the lists (ticker, event, close_time, floor_strike, result). Held-out = closes from 2026-11-14T00:00:00Z (HELDOUT_FIRST). Closes 2026-11-09T00:00Z to before 2026-11-14T00:00Z are printed SEPARATELY as "not blind: shares Bitcoin windows with DEPTH1's read of 2026-11-14" and never pooled. Closes before 2026-11-09 are not read (counted).
- Decision candle (section 7): the KXBTC15M candle with end_period_ts = close - 120 s, YES ask and bid CLOSE both present, YES spread (ask - bid) <= 0.03.
- Cheap side (section 7 band, 5c to 30c): YES if its ask is in [0.05, 0.30], else NO if 1 - yes_bid is in [0.05, 0.30] (the YES test comes first).
- Index (section 12): the perpetual's mid (bid close + ask close)/2 from PERPBTC1M. Model index = strike x (mid at the candle ending close - 120 s / mid at the candle ending close - 900 s); missing opening mid drops the window ("no opening minute"). The 10,000 unit never enters.
- Volatility (section 1 and 12): the mids at close - 120 - 60j s, j = 0..10; log changes between neighbouring marks where both exist; at least 6 changes or no trade; sample sd (n - 1); times sqrt(4/3). sd = 0 cannot give a probability: dropped and counted (ambiguity, stated).
- Model chance of YES = Phi(ln(model index / strike) / sd) = Phi(ln(mid_now / mid_open) / sd). Buy the cheap side when (model chance of that side - its ask) >= 0.05; 1 contract, held to settlement; fee 0.07 x p x (1 - p) UNROUNDED, cash (section 1). A void is a fee-only loss (price refunded, fee kept). An empty or odd result text STOPS the run naming the window. Every comparison carries 1e-9.
- Registered bar (section 4): n >= 50 AND cash PF >= 1.3 AND a positive mean = "cleared its registered bar (NOT the research bar)"; cash PF < 1.0 at n >= 30 = FALSIFIED; otherwise "no call at n = x". Under 50 held-out rows the reader prints NOT_ENOUGH_DATA with the count only and does NOT burn the read-once marker. All decided on UNROUNDED PF and mean.
- Beside the registered line (section 7, 10): haircut (a) random 34% drop (a fixed count round(0.34 n) dropped per draw, 1,000 draws, random.Random(20261114), rng.sample(range(n), k); median and 5th to 95th percentile by nearest rank); line (b) "ran rows dropped" (a row is RAN when the cheap side's ask close in the NEXT candle, end close - 60 s, is 1c or more above the ask seen; NO: 1 - next yes_bid close against the NO ask seen; rows with no next candle are excluded from (b) and counted; PF on the non-ran rows and the ran share printed); BOOK-REPLAY (R6) +2 s and +6 s (scorekit.fill_ioc, Desk A's convention as the Head ruled: first poll within 4 s after the delay, up to 5 levels at or below the ask seen); stale-ask count (a poll 0.25 s to 4 s before the decision with a book ask more than 1c above the ask seen). The replay and stale-ask lines print only when R6 polls are supplied.
- Read date READ_DATE = 2026-11-20T00:00:00Z (the Head's message); the committed marker is the line starting READ-ONCE MARKER in the registration file; a local marker file is written before output once the read is made.

## Model arithmetic
a = 0.0005 alternating log changes on the 11 marks: sd_1m = a x sqrt(10/9) = 0.00052705; sd = sd_1m x sqrt(4/3) = 0.00060858. z = +1: Phi(1) = 0.841345; z = -1: 0.158655. mid_open = 100 x exp(-z x sd); mid_now = 100.

## Windows (made-up; closes on 2026-11-14 unless stated; next candle = the candle ending close - 60 s)
| id | close | z | yes bid / ask | next yes bid / ask | result | outcome |
|---|---|---|---|---|---|---|
| H1 | 00:00 (exactly HELDOUT_FIRST: held-out) | +1 | .90 / .91 | .90 / .91 | no | YES ask .91 out of band; NO ask 1 - .90 = .10 in band: NO, chance(NO) .158655, edge .0587: TRADE NO, wins. fee .07 x .1 x .9 = .0063: net = .9 - .0063 = **+0.8937**; next NO ask .10, not ran |
| H2 | 00:30 | -1 | .09 / .10 | .09 / .10 | no | YES ask .10 in band: YES, chance .158655, edge .0587: TRADE YES, loses: net = -.10 - .0063 = **-0.1063**; not ran |
| H3 | 00:45 | +1 | .90 / .91 | .87 / .88 | void | as H1; void: price refunded, fee kept: net **-0.0063**; next NO ask 1 - .87 = .13 >= .10 + .01: RAN row |
| H4 | 01:00 | +.5 | .70 / .71 | .70 / .71 | yes | NO ask .30 in band, chance .3085, edge .0085: no trade |
| H5 | 01:15 | +1 | .90 / .94 | | no | spread 4c: no trade |
| H6 | 01:30 | +1 | .90 / .91 | | no | no opening perp mid: dropped, "no opening minute" |
| H7 | 01:45 | +1 | .90 / .91 | | no | only 5 usable changes: dropped, "fewer than 6 changes" |
| H8 | 02:00 | +1 | no decision candle | | no | counted, "no decision candle" |
| H9 | 02:15 | +1 | all perp mids equal | | no | sd = 0: dropped, "sd zero" |
| N1 | 2026-11-10 00:15 | +1 | .90 / .91 | .90 / .91 | no | NOT BLIND group (closes 2026-11-09 to 2026-11-13): same as H1, printed separately, never pooled |
| D1 | 2026-11-06 00:15 | +1 | .90 / .91 | | no | before 2026-11-09: not read, counted |
| B0 | 2026-11-08 23:45 | +1 | .90 / .94 | | no | before 2026-11-09: not read, counted |
| B1 | 2026-11-09 00:00 | +1 | .90 / .94 | | no | exactly NOT_BLIND_FROM: not blind group (spread 4c, no trade) |
| B2 | 2026-11-13 23:45 | +1 | .90 / .94 | | no | last window before HELDOUT_FIRST: not blind group (spread 4c, no trade) |
| E1 | 02:30 | | | | (empty) | the run STOPS naming the window (run separately) |

## Expected (held-out group, H1 to H9; the test sets the minimum row count to 3, because the registered 50 cannot be reached by 3 made-up rows)
- listed 14, held-out windows 9 (H1 to H9), not-blind windows 3 (N1, B1, B2), not read 2 (D1, B0); traded 3 in the held-out group (void 1) and 1 in the not-blind group (N1); drops: edge under 5c 1 (H4), spread above 3c 3 (H5, B1, B2), no opening minute 1 (H6), fewer than 6 changes 1 (H7), no decision candle 1 (H8), sd zero 1 (H9).
- Registered line (unrounded fee): net +0.7811, mean +0.26037, PF .8937 / (.1063 + .0063) = **7.9369**, win rate 1/3, label "cleared its registered bar (NOT the research bar)" (PF >= 1.3, mean > 0, n 3 >= the test's minimum 3).
- Line (b): rows with a next candle 3, ran 1 (H3, share 1/3); PF on H1 and H2 only = .8937 / .1063 = **8.4073**, n 2.
- Haircut (a): k = round(0.34 x 3) = 1 row dropped per draw: PF is one of 0 (H1 dropped), 141.857 (H2 dropped: .8937 / .0063), 8.4073 (H3 dropped: .8937 / .1063); the median and the 5th to 95th percentile are among those three values.
- Replay (synthetic polls): H1 at +6 s fills .10 from a YES bid book [(0.90, 5)]; no poll in the +2 s span = no trade. Stale-ask: a poll 1 s before the decision with YES bids [(0.80, 5)] gives a NO book ask of .20, more than 1c above .10: stale 1 of 1 with a book.
- Under 50 rows (the real minimum): NOT_ENOUGH_DATA with the count only, and no local marker written.
- Before READ_DATE (2026-11-20T00:00Z): refused before anything is loaded.
