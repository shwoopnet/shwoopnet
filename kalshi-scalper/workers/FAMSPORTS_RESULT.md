# FAMSPORTS result (run once 2026-11-03; registered in 8bb158d before any score was downloaded)

Code `src/scalper/famsports.py`, tests `tests/test_famsports.py`, raw output `data/famsports/famsports_result.txt` (local). Reference: ESPN keyless day scoreboard, 2025-09-01 to 2026-11-02 (NBA 1,570, NFL 456, NHL 1,798 final games). Cost 7% x C x p x (1-p) rounded up, C = 10, taker at the ask. N +2, running about 728,732, z bar 5.27.

## Universe actually reached
456 settled-total games matched to ESPN and a model; 190 eligible after the quote rule. Dropped: no valid two-sided quote 120 to 10 minutes before the start 266 (mostly NBA: only 8 NBA games qualify; the NBA season on file begins 2026-10-04), team code not split 15. Eligible: NBA 8, NFL 91, NHL 91. Thirds by game date (63 / 63 / 64 games); W3 unread.

## Results (W1 + W2)
| | Brier model | Brier market mid | n trades | W1 PF | W2 PF | pooled PF | mean | event z | fees x1.2 PF |
|---|---|---|---|---|---|---|---|---|---|
| Try A, edge 0.08 | 0.3033 | 0.2664 | 47 | 0.73 | 0.69 | 0.71 | -8.66c | -1.12 | 0.70 |
| Try B, edge 0.15 | 0.3033 | 0.2664 | 16 | 0.19 | 1.87 | 0.83 | -4.71c | -0.35 | 0.82 |

**Verdict: both tries FALSIFIED** on the registered Brier gate (a 10-game trailing average of final scores predicts totals worse than the market's mid by 0.037, far outside the predicted 0.005 to 0.03), and independently under 150 trades and PF under 1.5. Prediction held on direction; the miss on Brier was larger than predicted. Per sport (information only): NFL A n 26 -11.0c, NHL n 20 -8.6c.

## Failed assumption, and the different input that would be new
Killed assumption: that a points model from public final scores sees something the totals line does not. The line already contains injuries, pace, weather and lineups; a team average contains none. A sportsbook consensus line is blocked here (the-odds-api 401 key, stats.nba.com 403), and a model on top of the book's own line would need the book's line as the reference. **Different input that would be new:** player-prop lines against minutes/usage projections, or sportsbook closing lines (needs a key the owner would have to supply), neither on file.

## Smallest honest live probe
None. The model fails Brier, so there is nothing to probe. (Template if the owner insists: 1 contract, limit at model fair minus 8c, kill at 40 fills with PF under 1.2 or -$15, worst day = 2 fills a day x about $0.60 = about $1.20; 40 fills about 3 to 4 weeks at the 1.7 trades a day seen. Not recommended.) Full bar for any future version: PF 1.5 or better in three windows after fee, deflated z about 5.27 at N about 728,730.
