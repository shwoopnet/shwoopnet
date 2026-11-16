# PERPLEADLAG1 card (Testing Desk, Nov 16, 2026): does the US Tech 100 perp lead single-stock perps around the cash open and close? A new scalping lane, not a version.
**Label on every figure: first week, one regime, development, no evidence at n < 100.** Stock perps began Nov 5, 2026, so about 7 trading days exist before Nov 17. Nothing in this card has been read: counts first, outcomes only after Auditor B signs the spec and the loader. No account figure anywhere (price terms and percent of margin).

## Question
At the 09:30 ET cash open and the 16:00 ET cash close, when KXUSTECH100PERP moves by an unusually large amount in one minute, do the single-stock perps NVDA, AAPL, MSFT, META, AMZN and GOOGL (KXNVDAPERP, KXAAPLPERP, KXMSFTPERP, KXMETAPERP, KXAMZNPERP, KXGOOGLPERP) follow in the same direction over the next 1 to 5 minutes by more than a taker round trip (24 bp) plus haircut? The mechanism: the index perp is the deepest book, the stock perps are thin and their resting quotes are repriced by market makers after the index moves; the lead would last seconds to a minute.

## Uniqueness (checked against the register, nothing renamed)
Closest rows: PERPSCALP2 (own-name signals E1 to E7 only, no cross-asset input), PERPSLANE4 (gaps and sessions, funding and underlying ratios), ENGPERPS lanes 1 and 6 (relative strength INSIDE a stock basket and pairs; no index leg), POOL1 (single-name signals), PERPBASIS1 (stock against perp basis). None uses the index perp as the signal for stocks. Not on the declined list as far as I can read it; the Head confirms. Family flag: a cross-asset lead-lag family (new).

## Counterparty
The slow quote: the stock perp's resting bid and ask, repriced late by its market makers after the index perp moves. We pay it the spread (entry at ask or bid) and a haircut h; the edge exists only if the stock's catch-up move after our fill exceeds 24 bp of taker fees plus h on both legs. A fast market maker who reprices inside our minute removes it, which is the expected outcome.

## Data (counts first, in this order)
- **Tier A (now, minutes):** the perp archive's `kalshi1m` files (ticker, end_period_ts, bid_close, ask_close, volume) and `funding` files on perp-data, per-day files only, the same extract, loader pattern and wall as PERPSCALP2 (Auditor B's allow line for a reader named in the spec). Seven names (the six stocks and KXUSTECH100PERP); other tickers are not parsed.
- **Tier B (seconds, not available now):** the trade tape (`GET /margin/trades`, fields trade_id, ticker, count, price, created_time, taker_side; back-served, depth untested) pulled by a kalshi-pull job for the seven names on the open and close windows of each development day (no Kalshi request from this session's address); the 30 second recorder `perps30/` has ONE file (2026-11-06 close) and its dated files from 2026-12-01 are HELD (HOLDS.json H17, from 1796083200): perps30 is not read before Auditor B states the hold. The 60 second live recorder (`perp-live-data`) cannot resolve seconds and is not used.
- **Counts printed before any outcome:** per name and window the number of valid candles; per day the number of index signals (the signal needs no stock outcome); the pooled trades a day against the 3 a day gate. A name under 600 valid candles is left out and listed; a window day with fewer than 20 valid minutes is skipped and counted.

## Rules (Tier A: 12 rules, m_new = 12)
Candle end t (one minute grid), regular session days, DST-aware ET clocks (offset read at the ET day's midday).
- **Windows:** OPEN = t from 09:31 to 10:00 ET inclusive; CLOSE = t from 15:31 to 15:59 ET inclusive (a candle after 16:00 is not used).
- **Index signal:** r_I = ln(mid_I(t) / mid_I(t - 60 s)); sigma_I = population sd of the 60 one minute log mid returns of the index ending at t - 60 s (at least 45 valid); signal when |r_I| >= c x sigma_I, c in {2, 3}; direction = sign(r_I); the index and the stock both need a usable candle (0 < bid <= ask) at t and t - 60 s.
- **Not-yet-moved filter (the lag):** the stock's own one minute return r_s(t) satisfies sign(r_s) x sign(r_I) x |r_s| <= 0.25 x |r_I| (it has moved in the index's direction by at most a quarter of the index's move, or moved against it); otherwise no entry (counted).
- **Entry:** the stock's candle ending t + 60 s: long at ask x (1 + h) or short at bid x (1 - h) (the first candle after the signal minute; the signal minute itself is not traded); h = 0.0002 (primary) and 0.0005 (stress, the 5 bp haircut); taker fee 12 bp a side.
- **Exit:** time exit only, H in {1, 2, 5} minutes after the entry candle end, at bid x (1 - h) (long) or ask x (1 + h) (short) of the candle ending at entry + 60 H; a missing candle there is a dropped trade (counted); no stop or target in this card (a stop is a second family and would be a new try).
- **Cooldown:** one position per name; a signal is blocked while the name's last exit end is later than the entry end; the index signal can fire on consecutive minutes, so blocked counts are printed.
- **Funding:** booked as in the other perps passes (strictly between entry end and exit end; the open and close windows sit away from the 21:00Z print, so spanning counts are expected to be 0 and are printed).
- **Rules:** 2 c x 2 windows (OPEN, CLOSE) x 3 H = 12, pooled across the six stocks (a trade carries its name; per name tables are information, not tries).
- **Tier B (not registered here; its own card amendment when the tape lands):** the same signal on trade prices over the last S in {10, 30} seconds, 2 c x 2 windows x 3 H x 2 S = 24 more tries, entry on the first stock book after the signal second, held to H in {30, 60, 120} seconds.

## Gate, costs and counts
- **Per trade net** = gross price return - 2 x 12 bp (taker) - funding; costs printed at h 0.0002 and 0.0005; day-clustered one-sided z; halves floor(n/2) by entry time.
- **PASS (shadow candidate only, never live):** n >= 100 pooled trades, at least 10 trade days, PF >= 1.3 at h 0.0002 with both halves >= 1.0 and PF >= 1.0 at h 0.0005, no ET day above 30 percent of net. **The 3 a day gate:** pooled trades a day (trades / trading days) must be >= 3 or the rule is parked; with 7 trading days that needs about 21 trades.
- **m:** m_carried 6,290,660 (the Head's number for today; 7,492,484 from 2026-11-17, written in on the day by Auditor B) + 12 = 6,290,672 today. BH over that, bars on unrounded figures.

## Margin view (information, not a try; table a67ac7f9)
Page max leverage from PERPS_PAGE_MAX_20261116.tsv at commit a67ac7f92 on claude/forensics-desk (sha256 5be707ecce0cab05f7c5e1103af1ec2915d2b340b27f969853fb22d85888de36): NVDA 4.5, AAPL 4.9, MSFT 4.9, META 4.5, AMZN 4.9, GOOGL 4.9 (small-size max, owner paste via the EA, 2026-11-16 17:40Z), US Tech 100 28.9 (index, not traded here). At 10, 25 and 50 percent of the page max: L = x times the page max; percent of margin = 100 x net x L; liquidation distance = 1 / L - 0.045 (maintenance assumed 4.5 percent, labelled); flagged if the 1 minute index move times the stock's own typical move exceeds it is not computed; a trade whose time exit moves against it by more than the liquidation distance in its own path is counted (stop beyond liquidation: the path low or high of the candles held). A name with no page max in the table is not shown for margin and the pass is candidate_blocked.

## Dates and holds (date constants)
Development = candle ends through 2026-11-15T23:59:59Z (epoch 1794787199); 2026-11-16 is a buffer day not read; forward read registered from 2026-11-17T00:00:00Z (1794873600), one read on or after 100 pooled forward trades or 2026-12-01, whichever is later, frozen rules, on the Head's go. Holds to be confirmed by Auditor B before any outcome read: H17 perps30* and cash1m* files dated from 2026-12-01 (1796083200); the stock perps held-out of H16 (from 1797897600, 2026-12-22) is untouched by a window ending in 2026. Overlap with PERPSCALP1, PERPSCALP2 and PERPSLANE4 on the same days and candle files is disclosed: those read the same development days (PERPSCALP2 is the nearest, E1 to E7 on the same names).

## Prediction (numeric)
Pooled n about 100 to 250 over 7 days if the lag filter keeps a third of index signals; mean gross move in the index's direction over 1 to 5 minutes 3 to 10 bp, mean net -14 to -22 bp; PF at h 0.0002 under 1.0 in at least 10 of 12 rules; no BH survivor; at least 8 of 12 rules print "no evidence at n = x".

## Kill
- No rule meets the gate after the whole development window is read: closed (Tier B not built).
- kill_fast: after the first 100 pooled trades the mean gross move is under 12 bp (it cannot pay 24 bp of fees): the family is closed without further reads.
- A rule under 3 trades a day pooled is parked.
- A pass is a shadow candidate for the forward read above and is never live.

## Process
Hand case written and committed before code; Desk-independent second build (rule 16b at 1e-9) before any real read; the print sha256 is committed before it is read; one run through a loader with a wall and an allow line signed by Auditor B; no Databento-derived data or raw prints in any repo; no Kalshi request from this session. Spec JSON (kind perps_grid) follows after the Head's reading of this card.
