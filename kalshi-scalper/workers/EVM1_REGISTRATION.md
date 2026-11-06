# EVM1 registration (2026-11-06): which venue leads, Bitcoin perp or Kalshi's hourly ladder? (measurement, N +1)

Written before any ladder-implied level or lead-lag number was computed. Discovery only; no live code, no promote verb. Part of the perp-versus-event-markets mechanism (family EVM1 to EVM4).

**Counterparty / mechanism.** Ladder quoters (hourly KXBTCD "above K" strikes, 1c wide in the middle) may reprice more slowly than the perp's continuous book, or the reverse. If the perp leads, a ladder strike is stale for a few minutes after a perp move (the basis for EVM2 and EVM3). If the ladder leads, EVM2 and EVM3 have no premise.

**Data (all local, nothing fetched).** Ladder: `data/conf2_lad.sqlite`, KXBTCD hourly markets, 1 minute bid/ask candles from 55 minutes before each close, 42 closing dates 2026-08-24 to 2026-11-04. Perp: `/tmp/claude-0/cache/KXBTCPERP_1m.jsonl` (SNAPBACK1's 1 minute candles). Bitcoin only: it is the only underlying with a ladder and a perp history long enough. The other underlyings (S&P, Nasdaq, gold, oil) are EVM4 and NOT_ENOUGH_DATA.
**Universe chosen on cost:** Bitcoin perp recorded spread is 0.01 to 0.03 percent; the ladder middle is 1c wide. No selection on returns (one underlying, every close).

**Frozen split.** Closing dates by UTC date, first two thirds (28 dates, 2026-08-24 to the cut **2026-09-20**) = development; **closes on or after 2026-09-21 (14 dates) are the HELD OUT third and are never read** (no candle, count or outcome) unless development passes. D1 = first 14 development dates, D2 = last 14.

**Definitions (no tuning).** Perp mid at a minute end s = (bid close + ask close)/2 from the candle ending at s, valid when both are above 0 and the spread is at most 0.5 percent of mid; carried forward at most 3 minutes. Ladder implied level at s = the strike where the strikes' YES mid ((bid_c+ask_c)/2, both present) crosses 0.50, linear interpolation between the two bracketing strikes, needs a pair 200 dollars or less apart. Perp price in dollars = 10000 x the perp quote (the unit is read off notional/OI; check below). For each close C and minute s in [C-55 min, C-2 min]: dp(s) = ln perp mid(s) - ln perp mid(s-1 min), di(s) likewise for the implied level. Lead measure: L_pi = corr(dp(s), di(s+1 min)) (perp leads), L_ip = corr(di(s), dp(s+1 min)) (ladder leads), pooled within a date and averaged across dates; standard error by date clustering.
**Scale check (disclosed, no outcome used):** median over development closes of implied level at C-25 min divided by 10000 x perp mid must lie in 0.99 to 1.01; if not, the scale is re-estimated once from that median and disclosed as an amendment.

**Numeric prediction.** L_pi 0.05 to 0.15, L_ip within +/-0.03 of zero (the perp is the deep book; ladder mids move in 1c steps so di is lumpy and weakly correlated with anything). Probability the perp leads by at least 0.05 in both halves: 65 percent.

**Kill criteria.**
- NOT_ENOUGH_DATA: fewer than 2,000 usable (dp, di) minute pairs in development, or fewer than 20 development dates with data.
- FALSIFIED (no perp lead): L_pi minus L_ip below 0.05 in either half, or date-cluster z of the difference below 2.0.
- LEAD (information only, not a profit edge; the 5.27 deflated bar applies only to the profit tests EVM2 and EVM3): difference at least 0.05 in both halves and z at least 2.0.
Cost: none charged (no trade). N +1 (running about 730,456).
