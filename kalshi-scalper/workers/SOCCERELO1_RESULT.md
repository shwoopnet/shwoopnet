# Result: SOCCERELO1 (Kalshi soccer cheap side vs walk-forward Elo with draw model from ESPN results), 2026-11-04

Registration `workers/SOCCERELO1_REGISTRATION.md` (sha256 `4f89849adf230296a23a78b0217f841e48babd6c34fb2bc8ec0b8d22f069864e`, pushed before any join). Code `src/scalper/soccerelo1.py`, tests `tests/test_soccerelo1.py`. **N: +2.** Cheap side only; no favourite-side result computed. Frozen W3 never fetched or joined.

**Disclosure.** One outcome-free census was run before scoring (pre-window ratings, SOCCER1's cached asks, no Kalshi result and no in-window ESPN result): 225 rated matches, 404 cheap outcomes, 14 expected treated, gap median +4.6c. It changed nothing in the rule. A first census call returned 0 only because of a join bug (it needed window results for names); fixed to use SOCCER1's name list. Scored once.

**Data.** ESPN completed results 3,347 matches (2025-08 to 2026-10-02, 9 leagues); fit on the warm-up only: HA 60, nu 0.8, K 30, log loss 1.014 (walk-forward, 1,957 scored matches). Kalshi GAME events with an ESPN match and both teams rated: **237 matches**, 427 cheap outcomes (control).
**Gap (Elo minus ask):** median +4.87c, p10 -0.87c, p90 +15.3c. Prediction (median -2c to +1c) MISSED: Elo is less sharp than the market and puts more probability on underdogs and draws, which is smoothing, not information.
**Control (all cheap outcomes):** win 0.227 vs ask 0.217 vs Elo 0.280; mean net -0.16c; PF 0.99; z(match) -0.09. Flat, in the predicted range.
**Treated (Elo >= 3 x ask):** n 16 in 10 matches. Win 0.000 vs ask 0.073 vs Elo 0.271; mean net -7.83c; PF 0.00; fees x1.2 -7.93c; half 1 -9.07c (n 8), half 2 -6.58c (n 8). Zero wins of 16 where Elo said 27 percent: Elo overstates these long shots (the opposite of an edge), consistent with the book and Kalshi being right.
**Verdict: NOT_ENOUGH_DATA (16 of 150).** Not FALSIFIED by the rule; the direction is clearly against the idea.
**Forward plan:** rate about 13 treated per month in season, so about 10 months to 150; not worth building, and the 0 of 16 points the wrong way. Re-run only if a better-calibrated rating (goals-based, more seasons) is registered anew.
