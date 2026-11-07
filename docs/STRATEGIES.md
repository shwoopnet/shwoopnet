# The live strategies, defined in full (Nov 5, 2026)

Each strategy below has: what it is, the exact rules as the code runs them today, its record, and what is not known. Rules are read from `functions/kalshiLiveLib.js` and `functions/kalshiSlotLib.js`; stats are dated and sourced. Nothing here changes a rule: proposed changes are in `docs/STRATEGY_RISK_SEPARATION.md`. All times US Central.

## L1 "Closing buy" (gold; Dogecoin paused)

**What it is.** About 6 minutes before a 15 minute Kalshi market closes, buy the side that is already priced 88c to 97c (the heavy favourite) and hold it to settlement, selling early only if the side's bid falls to 25c. It collects the last few cents of a nearly settled market. Wins are small, a loss is large, so it only works at a high win rate.

**Markets.** Gold (`KXGOLD15M`) and Dogecoin (`KXDOGE15M`). Gold scales on the size ladder. Dogecoin is paused in code since Nov 3 (it was on the ladder Oct 30 to Nov 3; a resume would start at a fixed 5). Gold is closed Friday 17:00 to Sunday 18:00. Dogecoin runs around the clock. No quiet hours (the 8 PM to midnight block was lifted Oct 30). Paused in code and never candidates: XRP, Bitcoin, Ethereum and the three probe markets. XRP, Bitcoin and Ethereum stay in the list so quotes, names and the exit watch still work.

**Entry rule.**
1. Look when 5.5 to 6.7 minutes remain (330,000 to 400,000 ms), once per market.
2. A side qualifies if its price is 88c to 97c: a YES at its ask, or a NO at 1 minus the YES bid. If neither side is in the band, no order.
3. Order: immediate-or-cancel limit at the touch, so it either fills at once or not at all. The order id comes from the market ticker, so a second process (the normal state during a deploy) cannot place it twice.
4. If it does not fill (about 28% to 35% of attempts) there is no retry in that window.

**Exit rule.** The exit watch (a separate function, runs every 10 seconds from minute 3 of each quarter hour) sells the whole position with an immediate-or-cancel order when the side's bid falls to 25c or lower. Otherwise it holds to settlement. A hand close is not counted as the bot's result.

**Size rule.**
- Base: one contract per $43 of the sizing base (the balance minus profit skimmed to savings), at most 15 contracts (held there since Nov 3, 2026), 1 contract minimum.
- Step up: at most 1 contract every 3 days (a change to 3 is proposed, not made). Step down within 2 hours of a confirmed lower target.
- Add-on: reinvested profit buys extra contracts, capped at a quarter of the base size.
- Hard limits: 50 contracts per order (an order above that is refused), and the account holds one order per market at a time.

**Risk rules.**
- Window limit: money at risk in one 15 minute window, across strategies, is at most 5.5% of the sizing base.
- Each strategy also has its own stop at the same 12%, measured on its own orders only (since Nov 2, 2026), and the combined 12% stop over both backs them up.
- Loss stop: if the bot's orders over the last 24 hours are down 12% of the sizing base (open orders counted as lost, add-on profit excluded), the bot stops itself and stays off until you restart it.
- It is blocked from trading the opposite side of a contract another strategy holds (the direction lock).

**Record (sources in brackets).**
- Last week, all L1: 337 settled, win rate 92.0%, +$23.08 (Strategies table, Nov 1).
- Last 7 days to Oct 31, by market: Dogecoin 119 settled, +$18.14, PF 1.96; gold 69 settled, +$6.37, PF 1.14 (nightly report; the 7 day figures also include paused markets until they age out).
- Live record of gold and Dogecoin fills: 391 fills, 18 losses (4.6%); 16 of the 18 losses are early sells at the 25c line, -$75.34 in total (refinement chat, Nov 1).
- By price: fills at 90c to 92c, 93 fills, 9 losses, -$1.01; every other fill, 298 fills, 9 losses, +$66.43. The gap is p 0.012 raw, about 0.12 after counting the cells searched (refinement chat). It is a lead being tested forward, not a finding.
- Dogecoin at ladder size (11 to 13 contracts, since Oct 30): 51 orders, 33 fills, 1 loss (-$8.70), net +$14.34 (refinement chat). Dogecoin's no-fill share is about 35%.
- History (backtest, in-sample, upper bounds): gold profit factor 1.44 / 1.03 / 1.17 by third; Dogecoin 1.29 / 1.26 / 1.15 (research session). Holding to settlement beat every exit shape in history (EXIT1: hold 0.961 / 0.928 / 0.898, 25c line 0.921 / 0.897 / 0.869 per contract).

**Not known.** The research bar (profit factor 1.5 in each of three windows after fees and after deflating for how many things were tried) has never been met by L1. The live edge comes from a 5% loss rate against a break-even rate of roughly 8% at these prices, which is thin: a few more early sells move it. Review rule (written Oct 30): Dogecoin goes back to a fixed size of 5 if its last 100 settled orders at ladder size lose more than 8% or net under +0.5c a contract. Since Nov 2 the Bot page warns when this line is crossed; it changes nothing by itself.

## OICORE "Open interest jump" (Bitcoin, second slot)

**What it is.** A capped live probe, not a proven strategy. When the number of open contracts on a Bitcoin 15 minute market jumps in the last minutes before the close, buy the cheaper side (the underdog) and hold it to settlement. It wins rarely but a win pays about 3 to 4 times its cost.

**Market.** Bitcoin 15 minute (`KXBTC15M`) only. Bitcoin is paused for L1; OICORE is its own strategy.

**Entry rule.**
1. Look when 120 to 180 seconds remain, once per market.
2. Condition: open interest at the candle ending 180 seconds before the close is at least 86,300 contracts higher than at the candle ending 360 seconds before the close (public one minute candles). A missing reading means no order.
3. Side: the cheaper side, whose price must be 5c to 50c.
4. Order: 10 contracts to start (up to 30 by the ladder), limit 1c above the touch (never past 50c), never more than 25% of the size resting at the touch.
5. Scale-in: at most one more order, same side, at least 30 seconds later, only after the first filled.

**Exit rule.** None: held to settlement (the one reviewed exception to "every exit is before settlement"). It is still sold if it ever becomes a hedge against another strategy's contracts.

**Size rule.** 10 contracts to start, then 12, 15, 20 and 30, one step at a time, each earned on OICORE's own settled record and a large enough balance (`SLOT_LADDERS` in `functions/kalshiSlotLib.js`; built in #699); down at once after a bad stretch. Up needs at least 20 fills and 7 days at the step, a win rate of 0.20 or more, net of at least $1.00 a contract, profit factor 1.3 or more and a drawdown under $3 a contract, and a balance base of at least 825, 900, 1030 and 1350 for the steps 12, 15, 20 and 30. No add-on.

**Risk rules.**
- Dollar caps scale with the sizing base: one order 1% (at most $20), one window 2% ($40), all open orders 3% ($60), one day 2% ($20), lifetime 6% ($60).
- Shares the 5.5% window limit with L1. Has its own 12% loss stop on its own orders (since Nov 2, 2026), plus the combined account stop at the same 12%.
- Kill rules (latch off, only a reviewed edit re-arms): 18 losses in a row, or net below -$6 after 40 fills.

**Record.**
- Live (Oct 30 to Nov 1): 10 filled, 3 won, 7 lost, net about +$13.0 to +$13.4, profit factor about 4.1 (refinement chat and Strategies table). The wins were at 39c to 50c, the losses at 6c to 16c.
- Research validation: held profit factor 1.85; selling at 60 seconds kept about 1.52. Day z 4.42 against a bar of about 5.2, so it did not reach the research bar (V2).
- V2's forward reference ledger: 6 trades, 0 wins, -16.4c (0 of 6 at a 28% hit rate happens about 14% of the time). Needs 30 or more trades over 10 or more days before it means anything.

**Not known.** No counterparty is named (the first guess did not hold). Ten live fills cannot separate a real edge from luck. Forward read: Nov 13. The live record is better than V2's reference ledger, which is a reason for caution as much as for hope.

## EVENT830 "Release day longshot" (eight L1-free markets, second slot)

**What it is.** A small capped live probe, below the research bar, added Nov 3, 2026. Only on a listed US 8:30 AM Eastern data release day, in the 15 minute window that closes at the release (7:30 AM Central), buy the cheaper side and hold it to settlement. The registration's own prior is that it loses (profit factor central 1.05); it exists to be read forward.

**Markets.** Silver, copper, WTI oil, EUR/USD, GBP/USD, USD/JPY, HYPE and BNB 15 minute markets (`KXSILVER15M`, `KXCOPPER15M`, `KXWTI15M`, `KXEURUSD15M`, `KXGBPUSD15M`, `KXUSDJPY15M`, `KXHYPE15M`, `KXBNB15M`), reserved to this strategy. None of them is an L1 market. The three FX markets are on shard 0 and send nothing until it holds money.

**Calendar.** `SLOT_CALENDARS.EVENT830`, frozen in code: 15 windows from Nov 5 to Dec 23, 2026 (jobs, CPI, PPI, retail sales, GDP and PCE, weekly jobless claims). Both the close Kalshi reports and the ticker's Eastern window code must match a row. Nothing stored can add a date; a later date is a reviewed edit from official schedules. The minute function reads the eight markets only when a listed window is about to enter (about 8 public reads at 13:27 UTC on a release day, none on any other minute).

**Entry rule.**
1. Look when 120 to 180 seconds remain, once per market, only in a listed window.
2. The YES spread must be 10c or less.
3. Side: the cheaper side, whose price must be 5c to 50c. Hard limit 50c, no slip above the touch.
4. Order: 1 contract. Live it enters at the quote about 177 seconds before the close, about a minute earlier than the research fill (the slot cannot enter under 120 seconds).

**Exit rule.** None: held to settlement (`SLOT_HOLD_ALLOWED` is OICORE and EVENT830). It is still sold if it ever becomes a hedge against another strategy's contracts.

**Size rule.** Fixed 1 contract. No ladder and no add-on.

**Risk rules.**
- The slot's dollar caps and the shared 5.5% window limit apply.
- The slot's own loss stop (`RISK_PROFILES.SECOND`) is one budget over OICORE and EVENT830 together; the Bot page's Own stops line shows it as `OICORE + EVENT830`. The combined 12% account stop backs it up.
- Kill rules (latch off, only a reviewed edit re-arms): net below $0 at any point from 40 settled fills, or 20 losses in a row. The registered profit factor line of 1.2 cannot be written in the validator and must be read by hand. Worst single loss $0.52; 40 fills at 50c can lose at most $20.80.

**Record.** No live fill as of this note; the first listed window is Nov 5, 2026. Forward read: Dec 7, 2026. Pre-registration: `kalshi-scalper/README.md#SLOT-EVENT830`.

**Not known.** The slice was picked after its parent test failed, so its history is not evidence of an edge. No counterparty is named.

## Retired or paused (for completeness)
| Strategy | Status | Why |
|---|---|---|
| XRP (L1) | paused in code Oct 28 | live profit factor 0.49 over 65 fills; forward reads Nov 12 |
| Bitcoin (L1) | paused Oct 29 | live profit factor 0.72 over 155 orders |
| Ethereum (L1) | paused Oct 30 | the smooth-climb rule left it almost no entries |
| AUD/USD, USD/CAD, natural gas probes | paused Oct 28, off the list Oct 30 | no edge shown; 97c entries won 3c |

## Risk and scaling, side by side (today)
| | L1 | OICORE | EVENT830 |
|---|---|---|---|
| Win rate | about 92% to 95% | about 28% to 30% | about 19% expected (registration), no live fill yet |
| Typical win and loss | win about 6c a contract, loss about 66c (early sell) | win about 3 to 4 times cost, loss the whole premium (6c to 50c) | a win pays 1 to 19 times its cost (5c to 50c entries), a loss is the whole premium (at most $0.52 with the fee) |
| Size | gold: ladder, $43 per contract, +1 per 3 days, add-on, held at 15 / order ceiling 50; Dogecoin: paused | 10 to 30 (ladder, earned) | fixed 1 |
| Own stop | yes, 12% of L1's own orders (`RISK_PROFILES.L1`) | yes, 12% of its own orders (`RISK_PROFILES.SECOND`) plus kill rules; the combined 12% account stop backs both up | shares the slot's one 12% stop with OICORE (`RISK_PROFILES.SECOND` covers both), plus its own kill rules |
| Own window cap | no (shared 5.5%) | no (shared 5.5%, slot at most half) | no (shared 5.5%, slot at most half) |
