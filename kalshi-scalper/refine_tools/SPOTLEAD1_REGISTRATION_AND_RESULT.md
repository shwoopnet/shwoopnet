# W-SPOTLEAD1 registration (2026-11-11, written BEFORE any profit or loss was computed)

Mechanism 5 of FIVE_MECHANISMS_NOV11.md. No money, no trading code. Shadow candidate at most.

Data: R6 book15r6 (quote-data) for KXBTC15M and KXETH15M, windows with at least 100 good polls and a result in coverage.csv (about 920 per asset, Oct 29 22:15Z to Nov 11 16:00Z). Spot ticks: Kraken public Trades (XBTUSD, ETHUSD), from 200 s before each close, fetched per window. 1 minute Coinbase candles for the reference and the volatility.

Rule, fixed here:
1. Look L = close minus 180 s. Decide once per window per asset, using only data at or before L.
2. Strike K proxy = open of the Coinbase 1 minute candle that starts at close minus 900 s (Kalshi's own strike is a CF Benchmarks print, not in the cached files; resolution limit: the reference is a 1 minute open, not a tick).
3. Spot S = price of the last Kraken tick at or before L.
4. sigma = standard deviation of the 60 most recent 1 minute Coinbase log returns whose candle closed at or before L; sd_remaining = sigma * sqrt(180/60) (tau 180 s, no drift, no averaging adjustment).
5. p_yes = Phi(ln(S/K) / sd_remaining), p_no = 1 - p_yes.
6. Book: asks from the R6 2 second book. YES ask = 1 - best NO bid; NO ask = 1 - best YES bid. Execution row = the last book row received (t_recv) at or before L + 2 s (main) or L + 10 s (variant). Fill one contract at that ask, depth ignored (level 1 size reported, not required).
7. Buy the side with edge = p_side - ask_side >= 0.10, only if its ask is in [0.50, 0.87] (the 88c to 97c favourite band is excluded on purpose). One trade per window per asset at most; if both sides qualify, the larger edge.
8. Hold to settlement, outcome = Kalshi's recorded result. Cash basis: paid = ask, win pays 1; fee = 0.07 * paid * (1 - paid) per contract, unrounded; slip +0c and +1c added to paid.
9. Pass bar (set now): at +1c slip with the +2 s delay, pooled BTC and ETH profit factor >= 1.3 on n >= 80 trades, first half and second half (by close time, split at the median trade) both PF > 1.0, and still PF > 1.0 with the +10 s delay. Otherwise: FAIL if PF < 1.0 at +0c; DATA_LIMITED if the point is above 1.0 but the bar is not met or n < 80.
10. Sensitivities (counted, none can rescue a miss): edge 0.05 and 0.15; look 120 s; sd x1.5; BTC alone, ETH alone. N counted for this test = 8 variants x 2 assets, added to the project's try count.
11. Descriptive only: proxy agreement sign(final spot - K) vs result; daily P/L correlation with gold L1 cash P/L if 10 or more overlap days.

Windows held: about 920 per asset, so n for the rule is whatever fires; if fewer than 80 fire, the date n 80 is reached is projected from the firing rate per day. Shadow candidate only: no deploy, no money.

## Deviation note (written after the first main score, which was run in the mode below)
Kraken tick pulls ran at about 12 requests a minute (2.6 hours for all windows), so the MAIN score uses the Coinbase 1 minute candle that ends exactly at L (close minus 180 s, minute aligned) as spot S. This is the price at L to within the Coinbase tick, so for a single look at a minute boundary it loses little, but the sub-minute path is not used (resolution limit). Kraken ticks are used only as a cross-check on the subset pulled. First main result (+2 s, +0c) n58 PF 1.58; the rule was not altered after seeing it.

## Re-read date and n, committed Nov 12, 2026 (restored file: the privacy scrub had removed the bar and execution rows; they are public R6 research rules, restored from 22d61267)
- REGISTERED BAR = item 9 above (pooled BTC and ETH PF 1.3 or more at +1c with the +2 s delay on n of 80 or more, both halves PF above 1.0, PF above 1.0 with the +10 s delay). V2's draft bar, if different, is not the registered one.
- RE-READ: once, when n of 80 firings is reached or when the R6 recorder (extended to Dec 15) has ended and its last day is in (2026-12-16), whichever comes first. The first scored read (Nov 11, data through 2026-11-11T16:00Z; an earlier Nov 4 sketch used less data) stays DATA_LIMITED. Held-out: none; this is a shadow candidate only.

## Seen block and unseen block, committed Nov 12, 2026 (Head of R&D amendment, before the re-read)
- SEEN BLOCK constant: every window closing at or before 2026-11-11T16:00:00Z (epoch 1794412800) was in the first read's data (its 58 firings at +1c slip, +2 s delay; the last firing closed 2026-11-11T15:00:00Z, epoch 1794409200). Windows closing after the constant are UNSEEN.
- The re-read prints TWO lines: (a) the registered pooled figure on all firings; (b) the unseen block only (windows closing after 2026-11-11T16:00:00Z), with its own n.
- VERDICT is judged on (b) when (b) has 80 firings or more by itself. If (b) has fewer than 80 at the re-read the label is 'no evidence at n = x' for the unseen block, whatever (a) shows.
- What it trades: it buys the 50c to 87c side (ask in [0.50, 0.87]) and holds to settlement. That is a favourite-side hold: any live probe on this rule needs the owner's written exception to the favourite-and-hold ban, in addition to the owner's popup.

## Which files give the signal and the execution price (committed Nov 12, 2026, before the re-read; Forensics QUOTEVSBOOK1 finding)
- SIGNAL: the Coinbase 1 minute candles (spot S and the 60 minute volatility) and the strike proxy K (Coinbase open at close minus 900 s). It uses NO Kalshi quote.
- EXECUTION PRICE: the R6 book (book15r6, the 2 second order book read), both asks (YES ask = 1 minus best NO bid, NO ask = 1 minus best YES bid). The edge test (model probability minus ask) and the fill price both come from the R6 book.
- The quote recorder (quotes/ files, ladder.csv, the market-list endpoint) is used NOWHERE in this test, so the stale-copy finding (list endpoint refreshed about every 11 s) does not touch it. Only the book-priced figure counts, and it is the registered one.

## Rulings of Nov 12, 2026 (Head of R&D, owner ruling via the EA)
- LIVE USE: the owner ruled that no live probe may read Coinbase or Bitstamp (Coinbase market data terms unread; the EA's attempt returned a 403). W-SPOTLEAD1 as registered (signal = Coinbase 1 minute candles and a Coinbase strike proxy) therefore CANNOT go live even if its re-read clears, in addition to needing the owner's written exception to the favourite-and-hold ban. A version that could run would need its signal from Kraken or from Kalshi's own Bitcoin perpetual: that is a NEW registration and a NEW counted try, not an edit of this one.
- RESEARCH READS: no new request to Coinbase from the Refinement desk until the owner rules (stop, or accept the risk in writing). Data already held stays and may be used. If the owner says stop for good, the unseen-block re-read is scored on whatever signal data was already held at that time and labelled accordingly (unseen firings with no held Coinbase candles are reported as missing, not dropped silently).

## Owner acceptance of Coinbase and Bitstamp reads in research (Nov 12, 2026, later the same day)
- The owner accepted Coinbase and Bitstamp reads IN RESEARCH as an owner-accepted terms risk. The pause on new Coinbase requests from the Refinement desk is lifted. LIMIT: research only. Any LIVE probe that reads either venue still needs the owner's own popup naming that source. The line above stands: W-SPOTLEAD1 CANNOT go live as registered.
