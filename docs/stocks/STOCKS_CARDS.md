# Stocks desk: ten pre-registered cards (Task 2), Nov 12, 2026

Relayed from the predecessor desk (its commit fe1d5b07, sha256 c463c7c9b2bd...). Stale phrases superseded by Amendment 1: "Scoring scripts: NOT yet committed" and "waits on the Head's ruling".

Counts first. Cards 10. Tries scored 0. Paid pulls 0. Spend $0 of $25. Registered tries if every line were run: 16.

## SHARED RULES
- Bar: cash PF 1.5 in each of three windows, after costs, deflated. Windows (daily cards): W1 2018-05-01..2021-03-31, W2 2021-04-01..2024-06-30, W3 2024-07-01..2026-11-11. HELDOUT_START = 2024-07-01 (W3 read once, marker line committed).
- Events needed: PF 1.5 = mean/sd d 0.162 for normal returns; n=(z/d)^2: 1,141 at z 5.46 (50% power), 1,519 at 80% power; 255 and 448 at z 2.58. Independent = DAYS, not name-days. Fat tails make these too small.
- Costs ASSUMED, one way: commission $0; SEC 0.0000206 of sell value; CAT negligible; spread+slippage at $2-5k orders: index ETFs 0.5bp, large caps 1.5bp, auction fills print +0.5bp, illiquid 15bp; impact zero (under 0.1% ADV); borrow ETB 0, HTB 10%/yr assumed.
- Universe: U500 = 500 common stocks and ETFs with highest MEDIAN daily dollar volume in May 2018 (listing-venue daily bars), fixed for the whole test, delisted kept. One bounded pull: ohlcv-1d ALL_SYMBOLS May 2018, XNAS $0.25, XNYS $0.11, ARCX $0.24 = $0.59 (Head allowed this single exception; re-estimate immediately before, stop if any one is above $0.50).
- Hard data rules: no pull without a recorded free estimate; no ALL_SYMBOLS beyond that exception; closes and opens from the LISTING venue's statistics schema (pilot confirms); no Alpaca; no split/dividend adjustment: drop name-days with close ratio outside 0.4 to 2.5.

## RANKING (speed to verdict)
1 S1 overnight vs intraday index ETFs ($0.03, 252 days/yr); 2 S2 overnight/intraday clientele single names (U500); 3 S3 1-week reversal illiquid (52 wks/yr, 430 in data); 4 S4 opening gap fade; 5 S5 post-gap drift (earnings proxy); 6 S6 leveraged-ETF rebalance last 30 min ($6.83 ARCX 1m, 8 ETFs); 7 S7 first 30 predicts last 30 (same pull); 8 S8 closing auction imbalance ($7.14 for 20 names 1 yr; cannot reach bar in cap); 9 S9 opening cross imbalance (rides S8 pull); 10 S10 index adds/deletes (hand-typed dates, decades).

UNION COST: ranking $0.59; U500 daily+statistics about $5 (extrapolated 25x the 20-name $0.07+$0.08 per venue; exact call first); ARCX daily+stats SPY QQQ IWM DIA $0.03; ARCX 1m eight ETFs $6.83; imbalance 10+10 names 1 yr $7.14. About $19.6 total, under the $20 ceiling.

## Cards
**S1 Overnight vs intraday, index ETFs.** Other side: intraday liquidity demanders/day traders pay the overnight risk premium; partly arbitraged, premium shrinking. Rule: buy official close (MOC), sell official next open, SPY QQQ IWM DIA, every day; control open-to-close. Data: ARCX.PILLAR statistics + ohlcv-1d, $0.03. Costs 0.5bp each side + SEC on sell. Events 252/yr, 2,150 in data, need 1,141: reachable. Tries 1. Kill: PF<1.0 in W1+W2 after costs or any W3 window <1.0; if statistics close absent, blocked. Honest prior: expected below the bar (needs d 0.16; index daily Sharpe roughly 0.05-0.07 from memory, to be measured).

**S2 Overnight vs intraday, clientele in single names.** Other side: retail/short-horizon overpay at open. Rule: rank U500 daily by trailing 60-day mean (overnight minus intraday) return; long top decile at close, sell at open; short bottom decile. Costs 1.5bp each side, borrow as above. Events 252/yr, need 1,141, have 2,150. Tries 2 (long leg, long-short). Kill: PF<1.0 on W1+W2, or two of three windows <1.5 at end of W3. Prior: crowded, about 6bp round trip eats it, likely dead.

**S3 One-week reversal, illiquid names.** Rule: each Friday close, among U500's bottom 60-day dollar-volume quintile, buy the bottom decile of 5-day return, sell next Friday close; short leg optional. Costs 15bp each side, borrow 10%/yr. Events 430 weeks, cannot reach z 5.46; screen only. Tries 2. Kill: gross reversal under 30bp (round trip) in W1+W2. Prior: spread consumes it.

**S4 Opening gap fade, large caps.** Rule: at the official open, if a U500 name gaps >2% from prior official close with no volume spike, trade against the gap, exit at the close. [AMENDED: no-news filter uses PRIOR-day volume (<2x its prior 20-day mean); the original "volume under 2x its 20-day mean" used today's volume = lookahead.] Costs open 1.5bp, close 0.5bp, SEC, borrow on shorts. Events ~30 qualifying days/yr (estimate, void until a count-only read). Tries 2 (down-gap long, up-gap short). Kill: <100 qualifying days in W1+W2: "no evidence at n = x"; PF<1.0 on development: FALSIFIED.

**S5 Post-gap drift (earnings proxy).** Other side: slow information absorbers (PEAD). Rule: gap >5% with volume >3x its prior 20-day mean; enter at the SECOND day's close, exit 20 trading days later; buy gap up, short gap down. Costs 1.5bp each side + 10bp extra slippage, borrow on shorts. Independent unit = earnings-season week (~16/yr, ~130 in data); cannot reach bar; report name-events with cluster-robust SE and weeks. Tries 2. Kill: PF<1.0 at 100+ events on development.

**S6 Leveraged-ETF rebalancing, last 30 minutes.** Other side: leveraged/inverse ETF issuers must buy into rises/sell into falls at the close. Rule: if SPY return from prior close to 15:30 ET exceeds +1.0% buy SPY at 15:30, sell at the 16:00 official close; below -1.0% short. Threshold pre-fixed. Data: ARCX.PILLAR ohlcv-1m SPY plus SSO SPXL SPXU SDS QQQ TQQQ SQQQ, $6.83; official close from statistics. Costs 0.5bp each side. ~40 days/yr (estimate), cannot reach z 5.46. Tries 2. Kill: <100 qualifying days "no evidence at n = x"; PF<1.0 at 100+.

**S7 First 30 minutes predicts the last 30.** Rule: sign of SPY 09:30-10:00 return; buy or short SPY 15:30 to 16:00 close, every day. Same ARCX pull. Events 252/yr, reachable. Tries 1. Kill: PF<1.0 on W1+W2. Overlap flag with S6: Verification Analyst computes daily P&L correlation; more correlated card rejected. Prior: effect is about a tenth of a percent of variance; expect FALSIFIED.

**S8 Closing auction imbalance, provide liquidity (DEFERRED).** Other side: index funds/ETF baskets/MOC algos that must trade at the close (the 1,096,888-share SPY print in CLAUDE.md). New vs the record: the record measured only the print size; this tests whether the published imbalance predicts the move to the close and the next-open reversal. Rule: at 15:50 ET NYSE imbalance or Nasdaq close imbalance message, imbalance >5% of 20-day ADV: take the opposite side by limit-on-close, exit next open. Data XNAS.ITCH + XNYS.PILLAR `imbalance`, 20 names, 1 year ~$7.14. HELDOUT_START 2026-05-01. Tries 2. Prior: most contested trade in the market; expect arbitraged away.

**S9 Opening cross imbalance (DEFERRED).** Rule: at the 09:28 ET opening-cross imbalance, trade against a large imbalance at the open, exit 30 minutes later. Rides S8's pull (+ ~$2 of 1m bars, estimate first). Tries 1. Dropped if S8 not bought.

**S10 Index additions and deletions (DEFERRED).** Rule: buy S&P 500 additions at announcement-day close, sell at effective-date close; short deletions. Hand-typed dates only. Independent dates 4-12/yr; decades. Tries 1. Paper-list screen at best (30 events, both halves positive); expected nothing at our size.

CONSIDERED AND DROPPED: turn of month (12 events/yr), Jan tax-loss (1/yr), pre-FOMC (8/yr), lottery MAX short (borrow data, broker route gone), ETF vs constituent arbitrage (HFT owns it), dividend capture (tax effect). PRIOR TRIES: the opening-range breakout and its variants are prior tries, not leads (CLAUDE.md).

## AMENDMENT 1 (Nov 12, before any data bought or scored; supersedes card text where different)
1. S4 lookahead fix as above, with a test that changing today's volume cannot change which days trade.
2. Ranking pull rule and U500 median-dollar-volume rule as above.
3. First wave: S1, S2, S7 judged + S6 screen + S3, S4, S5 screens; S8-S10 deferred. Purchase order: ranking $0.59, pilot $0.30 (schema check, scores nothing), S1 $0.03, U500 daily ~$5 (exact estimate first), ARCX 1m $6.83 = about $12.75.
4. Labels: S3-S6 never a pass ("screen only, no evidence at n = x" or paper-list); S1, S2, S7 judged at z 5.46 and PF 1.5 in each of three windows; a clear is "cleared its registered bar" until the Verification Analyst re-checks.
5. One price definition across the cutoff = primary listing venue official auction print, no switch to consolidated at 2024-07-01; a card whose entry price cannot be shown tradable is BLOCKED.
6. Costs ASSUMED and every report says so.
7. No Nasdaq-listed pull until Q4 answered.
8. Scripts S1-S7 in stocks_desk/ with synthetic tests in tests_stocks/ (17 tests; 5 lookahead guards each shown to fail when the lookahead is put back); held-out read-once marker file HELDOUT_READ_MARKER.txt, one committed line per card before the W3 read.

## AMENDMENT 2 (Nov 12, found by the predecessor reading its own scorers before any data was bought)
A trade at the OFFICIAL CLOSE t cannot use close t in its signal: the order must be placed before the close prints. S2 ranked names on a window that included day t and S3 ranked on the 5-day return and dollar volume through day t, then both traded at close t. That would let the entry price select the names (bid-ask bounce and end-of-day reversal flatter a close-to-open or weekly-reversal result). Both signals are now lagged one day (days up to t-1 only; s2_signal, s3_signal). For S3 the rule reads: at each Friday's official close, rank on the 5-day return and 60-day dollar volume as of Thursday's close. Two tests prove today's close and volume cannot change the signal, and each fails if the lag is removed. S1 has no signal; S4 uses the gap known at the open; S5 enters one day after the event day; S6 and S7 use bars before 15:30. Event counts and kills are unchanged. Registered tries still 16.

## AMENDMENT 3 (Nov 12, Head of R&D notes, before any data bought or scored; labels and disclosures only, no rule changes)
1. LABELS. "FALSIFIED" means cash PF under 1.0 at 100 or more trades. A card between 1.0 and 1.5 at full n is "below the bar at n = x, PF y", not FALSIFIED. S1's honest prior reads "expected below the bar" (replacing "expect FALSIFIED"); the kill lines saying FALSIFIED for PF under 1.0 stay as written.
2. DIVIDENDS. No split or dividend adjustment is used, so every ex-dividend open shows a price drop that is not a loss to a holder. This UNDERSTATES a long overnight leg (S1 and the S2 long leg: conservative) and FLATTERS any short held over an ex-date (S2 short leg, S3 short leg, S4 up-gap short, S5 short), because a short pays the dividend. A short-side result is an upper bound on two counts (assumed borrow and dividends). The long-short S2 line (S2LS) is reported but NOT judged; the judged S2 line is the long leg.
3. CLOSE-RATIO FILTER. The drop of name-days with close ratio outside 0.4 to 2.5 removes the pair of days around a break (a split day and the day after) from the record. It is never used to choose a trade from its outcome. Every output carries the count of dropped name-days (`dropped_name_days`).
4. S1 and S7 report each ETF separately as well as pooled (S1 built: `per_etf`; S7 runs on SPY only by registration, so its per-ETF line is SPY). The S6 to S7 correlation is computed on development dates only (`dev_corr`), before either held-out read.
