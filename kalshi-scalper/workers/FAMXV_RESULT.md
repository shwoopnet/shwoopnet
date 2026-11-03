# FAMXV result (run once 2026-11-03 after Amendment 1; registered in 8bb158d, amendment 953e67a, both before any gap or outcome was read)

Code `src/scalper/famxv.py`, tests `tests/test_famxv.py`, raw output `data/famxv/famxv_result.txt` (local). Cost 7% x C x p x (1-p) rounded up, C = 10, taker at the Kalshi ask. N +2, running about 728,734, z bar 5.27.

Process disclosure: a first `run` before the amendment printed "games on file 230, eligible 0" (no pre-game Kalshi quote on file, because espn1.sqlite candles start 8 minutes before the game). It printed no gap, Brier, trade or outcome; the amendment fetched the missing candles and the run above is the one scored read.

## Part 1, internal consistency: DUPLICATE
10-23 structure scan, ARB1 to ARB5, RULES1, FEE1, WX3, SPORTCONS1: all FALSIFIED, zero persistent locks, best -1.5c / +0.6c / +0.1c. Killed assumption: stale quotes leave locks at the top of the book; makers enforce arithmetic inside the fee. Not repeated.

## Part 2, Kalshi against Polymarket on NBA and NFL game winners
230 games on file; Polymarket event found for 170 (60 not found by the slug scheme, mostly NFL/NBA slugs differing, dropped and counted), all 170 had a pre-game Kalshi quote and a Polymarket point within 15 minutes. Look 60 minutes before the start.
| | Value |
|---|---|
| Gap \|P_pm - Kalshi ask\|, 340 team legs | median **0.5c**, p90 1.5c |
| Brier (W1+W2, 226 legs) Polymarket / Kalshi mid / blend | 0.2322 / 0.2322 / 0.2321 |
| Try A, gap at least 4c | 2 trades (W1 0, W2 2), both lost, mean -39c; NOT_ENOUGH_DATA |
| Try B, gap at least 8c | 0 trades; NOT_ENOUGH_DATA |
Verdict: **NOT_ENOUGH_DATA by count, and nothing to wait for**: the two venues are one price. Median disagreement half a cent (less than the Kalshi spread), identical Brier, 2 of 170 games (1.2%) with a 4c gap against the predicted 4% to 12%. Prediction held on direction (NOT_ENOUGH_DATA, Kalshi not worse) but the trigger rate was lower than predicted. W3 unread.

## Failed assumption, new input, probe, owner action
Killed assumption (same as PM1 and XVENUE1): Polymarket carries information Kalshi's price lacks. For sports both copy the same sportsbook line and an arbitrageur keeps them within a cent. The different input that would be new is a source that is NOT a copy of the same line: a sharp book's closing line (keyed API) or a non-sports pair where Polymarket's crowd is the primary source (Fed, CPI, elections; about 8 FOMC meetings a year, too few independent events, not run).
**Smallest honest live probe: none.** At 1.2% of games with a 4c gap, a full NBA plus NFL regular season (about 1,600 games) gives roughly 19 triggers, so 40 fills would not exist in a season; a buy at the ask for a 4c gap loses to the spread plus fee (median 0.5c gap). If the owner insisted: 1 contract, limit = Polymarket price minus 2c, kill at 40 fills PF under 1.2, worst day about 3 triggers x $0.60 = $1.80, 40 fills not before about 2028. Full bar for any version: PF 1.5 or better in three windows after fee, deflated z about 5.27 at N about 728,730. Owner action: none.
