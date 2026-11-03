# EVENT1 registration: cheap sides of the L1-free 15 minute markets next to scheduled events (Strategy Research V2, worker EVENT1, research only)

Written 2026-11-03 BEFORE any win, loss, profit factor or result of an event or non-event window was computed. Only counts of events,
windows and would-be entries (`python -m scalper.event1 counts`, quotes only, the `result` column is never read there) were looked at.
Code: `src/scalper/event1.py`, tests `tests/test_event1.py` (synthetic candles, plain runner). Calendar: `workers/EVENT1_CALENDAR.csv`.
Nothing here means trade. No promote verb. Touches no live code, `functions/`, L1 or OICORE.

**Plain statement.** The likeliest outcome is FALSIFIED. Both known scheduled-event reads on gold and Bitcoin (EVT1) found every macro
release NOT_ENOUGH_DATA and every powered cell FALSIFIED against a matched control. The contrary hypothesis (events are priced; the
volatility is already in the quote) is the prior.

## Ledger check (how this differs)
`grep -n -i "EVT1\|CPI1\|MENT1\|ECONNEW\|WXNEW1\|scheduled" README.md workers/OICORE_SHAPE_INVENTORY.md`:
- **EVT1** (2026-10-29/30) tested scheduled-event windows on **gold and Bitcoin only** (L1 markets), 384 side cells, any fill price,
  windows before / containing / after the event, and found macro releases NOT_ENOUGH_DATA (1 to 7 windows each) and every powered cell
  FALSIFIED. EVENT1 differs on: **market** (silver, copper, WTI, EURUSD, GBPUSD, USDJPY, HYPE, BNB; none is an L1 or OICORE market, so a
  cheap-side trade cannot hedge L1), **fill** (HARD LIMIT 0.50, EVT1 allowed any price below 1), **calendar** (adds ISM, Conference
  Board, the NYSE open and close, the London, Tokyo and Hong Kong opens), **trigger** (one pre-registered window rule, below, not a 3
  position x 4 side grid), **look** (180 s only), **universe pooled** (the verdict is on 8 series pooled, so the macro releases are not
  the only source of trades) and **baseline** (same series, same 15 minute slot, same weekday class).
- NEWH10 (8:30 ET wing on the hourly ladder, PF 2.56 on 15 events: "15 events cannot carry a claim") and IDEAS20D `DATA_0830ET` (Bitcoin
  and Ethereum, all days) are the nearest clock-time reads. CPI1 / MENT1 / ECONNEW1 / ECONNEW2 / WXNEW1 priced a model against the market
  (Kalshi's own economics, mention and weather markets), not a cheap side of a 15 minute market near a release; not duplicates.
- Gold, Bitcoin, Ethereum, Dogecoin are excluded (L1 buys the favourite there; a cheap side in the same window would hedge it; Bitcoin
  is also OICORE's market). XRP is paused in L1 and left out as well. SOL's history ends Oct 22 and is left out.

## Calendar (built and written before any outcome; `workers/EVENT1_CALENDAR.csv`, 623 events, Aug to Dec 2026)
Columns: date, utc_time, event, source. Event types and sources:
- **Data releases 8:30 ET:** CPI, PPI, jobs report, GDP and PCE (released together; one type), advance retail sales, weekly jobless claims
  (Thursdays). Dates read by the CAL worker from bls.gov/schedule/2026, bea.gov/news/schedule/full and census.gov (status `verified`) in
  `studies/EVENT_CALENDAR_2026.csv`; claims are the official recurring Thursday rule (dol.gov answered 403 to that worker, so each is
  `rule`, and the three holiday-week Thursdays marked `unverified` are left out). This session's own curl to bls.gov/schedule/news_release/
  answered HTTP 403 (not worked around); the Federal Reserve calendar page answered 200 and shows the 2026 meetings, in agreement with
  the file (Sep 15-16, Oct 27-28, Dec 8-9; statement 14:00 ET on the second day).
- **FOMC statement 14:00 ET** (Sep 16, Oct 28 verified; Dec 9 rule). **EIA Weekly Petroleum Status Report** (10:30 ET Wednesday; 12:00 ET
  Thursday in holiday weeks; verified on eia.gov by CAL). Added because WTI is in the universe.
- **10:00 ET releases (official recurring rules, status rule):** ISM Manufacturing PMI (first business day), ISM Services PMI (third
  business day), Conference Board Consumer Confidence (last Tuesday). ismworld.org and conference-board.org answered 301 to this session
  and were not followed; the dates are by rule and may be one day off in a holiday month.
- **Market opens and closes, by rule:** NYSE open 9:30 ET and close 16:00 ET (13:00 on early-close days), skipping 2026-09-07,
  2026-11-26, 2026-12-25; London open 08:00 London time; Tokyo open 09:00 JST; Hong Kong open 09:30 HKT. **UK, Japanese and Hong Kong
  holidays are NOT removed** (a few non-event days are labelled events; same labelling in W1, W2 and W3, disclosed).
- Not included: Fed speeches, Treasury auctions (EVT1 had them for gold and Bitcoin), housing, JOLTS, earnings, Coinbase maintenance.
Every event is on a quarter hour (:00, :15, :30, :45).

**Events per month in the calendar** (Aug to Dec each): CPI 1, PPI 1, jobs 1, GDP and PCE 1, retail 1, ISM 2, Conference Board 1, claims 3 to 5,
EIA 4 to 5, FOMC 0 or 1 (Sep, Oct, Dec), NYSE open about 21, NYSE close about 21, London open about 21, Tokyo open about 21, Hong Kong open
about 21. So data releases plus FOMC plus EIA plus ISM and Conference Board are **about 15 to 18 event times a month**; the five daily opens
and closes are about 105 more.

## Trigger (ONE primary, "Try A")
For a 15 minute market with close time c and look L = c - 180 s: the window is an **EVENT window** if some calendar event time e satisfies
**c - 300 s < e <= c** (the owner's rule: the event is inside the last 3 minutes, closed at the close, or the look falls within 2 minutes
after it). **Disclosure that matters:** every event on the calendar is on a quarter hour, so the only window it falls into under this
rule is the one **closing at the event time** (e = c). The "look within 2 minutes after" half never fires, and under a strictly half-open
reading (e < c) the rule would select **zero** windows. I read it closed at c, so Try A is a test of the 3 minutes leading INTO a known
event: a market maker who does not widen before known volatility. It does not test the windows that live through the event.
Those are **Try B (information only, no verdict, still counted in N):** the event falls in the first 5 minutes of the window
(c - 900 <= e < c - 600, i.e. the window that opens at the event; look 12 minutes after it). A and B never select the same window on this
calendar (counted: 0). Control windows are those in neither A nor B.

## Universe (fixed on metadata, before any outcome)
KXSILVER15M, KXCOPPER15M, KXWTI15M, KXEURUSD15M, KXGBPUSD15M, KXUSDJPY15M, KXHYPE15M, KXBNB15M. Classes: metals (silver, copper), energy (WTI),
fx (three pairs), crypto (HYPE, BNB). Candle history: silver, WTI, HYPE, BNB from 2026-08-06; copper from 2026-08-27; the three FX pairs from
2026-09-23; all to 2026-11-03 09:15Z (about 89 days). Reported separately per series and per class; **the verdict is the 8 series pooled**.
Pools registered: ALL, the four classes, and the event groups DATA830, DATA1000, FOMC, EIA, US_OPEN, US_CLOSE, LONDON_OPEN, ASIA_OPEN
(reports, not tries). A MACRO read (data releases, ISM, Conference Board, FOMC, EIA) is shown as the groups above.

## Trade rule (exactly)
At the 1 minute candle ending **180 s before the close**: require 0 < bid < ask < 1 (YES) and ask - bid <= 0.10 (a liquidity rule on the
signal candle, applied to event and control windows alike). The **cheaper side** is YES if its ask is 0.05 to 0.50, else NO if its ask
(1 - YES bid) is 0.05 to 0.50, else no trade. **Fill at that side's ask on the next candle (ending 120 s before the close) with a HARD
LIMIT at 0.50:** a fill ask above 0.50 is no trade (counted as "limit", never filled higher). A missing or one-sided signal or fill candle
is a counted gap. Held to settlement, 1 order per series per window, C = 10 (headline), taker at the ask. **Fee 7% x C x p x (1-p) rounded
up to the cent per order** (`gen6.fee`); fees x1.2 reported. Zero-volume signal or fill candles are flagged.
In the 89 days: 20,596 eligible trades in all (1,119 in Try A windows, 981 in Try B windows); 3,078 windows hit the 0.50 limit, 16,515 had no
cheap side or a wide spread, 1,571 were gaps (all outcome-free counts).

## Baseline (the time-of-day control)
Control trades are eligible trades in windows that are neither A nor B. For each event trade: the mean net (cents per contract) of control
trades **in the same series, the same UTC 15 minute slot and the same weekday-or-weekend class, in the same date third**; if that slot
has fewer than 10 control trades (the five daily opens and closes recur every weekday, so their slot has no event-free weekday), the mean of the slots
2 hours before and 2 hours after; if still fewer than 10, the trade is dropped from the difference (reported). **diff** = mean of (trade net -
its control mean) in cents per contract; z = diff / sqrt(day-clustered SE of the residuals ^2 + day-clustered SE of the control mean ^2).
A positive diff at z >= 2 in BOTH W1 and W2 is what an event effect would look like.

## Windows and holdout
By window close date: **W1 2026-08-06 to 09-04, W2 2026-09-05 to 10-04, W3 2026-10-05 to the end of the data (11-03 09:15Z)**. **W3 is the
frozen holdout, not scored unless W1 and W2 both pass, and there is no second look.** Counts of W3 trades were printed (counts are not
outcomes). Verdict is read on W1 and W2; W3 only after both pass.

## Counts and time to 150 (outcome-free, printed before this file)
Try A eligible trades (8 series pooled) 1,119 in 89 days: **W1 283, W2 334, W3 502 (W3 is larger because the FX pairs only start
2026-09-23)**; about 375 per 30 days, so the 150-trade floor is reached in about **0.4 months pooled**. By event group (eligible trades,
per 30 days, months to 150): ASIA_OPEN 404 (136; 1.1), US_OPEN 194 (65; 2.3), LONDON_OPEN 191 (64; 2.3), US_CLOSE 185 (62; 2.4),
DATA830 74 (25; **6.0**), EIA 39 (13; 11.5), DATA1000 (ISM and Conference Board) 27 (9; **16.6**), FOMC 5 (1.7; **89**, i.e. never on
this history). Macro (data releases, FOMC, EIA, ISM, Conference Board) pooled 145 (49 per 30 days; **3.1 months**). By series, Try A
trades: silver 200, copper 164, WTI 203, EURUSD 87, GBPUSD 83, USDJPY 89, HYPE 146, BNB 147.

## NUMERIC PREDICTION (written before any outcome)
Pooled Try A, W1 plus W2 (about 617 trades; all three windows about 1,119): **windows per month about 375 trades**; **win rate 24% to 30%
(central 27%)**, **average fill 22c to 32c**, win rate about 1c to 3c BELOW the fill (the fee and the spread; the quote is already efficient
on this family: QSTALE1 won 0.5c below its fill, XOI1 and OICOREX1 found no cheap-side edge on these same alts), **payoff (average
win / average loss) 2.2 to 3.4 (central 2.8)**, **profit factor 0.75 to 1.10 (central 0.92)** in each of W1, W2 and W3, **mean -3.5c to +0.5c
per contract**. Event-minus-control diff -3c to +3c per contract (central 0), |z| below 2 in at least one of W1 and W2. Macro group (145
trades) PF 0.6 to 1.4, NOT_ENOUGH_DATA on its own. Probability PF >= 1.5 in both W1 and W2: **2%**. Probability pooled z reaches 5.27:
under 0.5%. Probability the event trades beat their slot control by +2c at z >= 2 in both W1 and W2: **4%** (a positive effect on the 15
minute market from an anticipated release would need makers who do not widen; CME and spot makers quote through these minutes).

## KILL RULES (fixed now, no tuning)
- **NOT_ENOUGH_DATA:** fewer than 150 Try A trades pooled in W1 plus W2 (not expected for the pooled read; certain for DATA830, DATA1000,
  EIA and FOMC alone).
- **FALSIFIED:** profit factor (C = 10, after fees) under 1.5 in W1 or in W2, or (if read) in W3. Fees x1.2 PF at or under 1.0 in any scored
  window also falsifies.
- **NOT_YET_FALSIFIED:** PF at least 1.5 in each of W1, W2 and W3 and fees x1.2 PF above 1.0. **A pooled day-clustered z below the deflated bar
  5.27 (N about 728,734) is reported as NOT_YET_FALSIFIED, never a pass.** History alone can earn no more. The named counterparty is
  "market makers who do not widen for known scheduled volatility", which is a hypothesis about quotes, not yet a measured person; the
  contrary hypothesis (volatility is in the quote) is the one the baseline difference tests.
- No promote verb. Try B and every per-series, per-class and per-group table are reports, not verdicts.

## STREAK REPORT (computed with `src/scalper/streaks.py`)
At the PREDICTED central win rate 27% (100 trades): longest losing run mean 11.8, median 11, 95th percentile 19, 99th percentile 24; chance of
at least one run of 10 straight losses in 100 trades 71% (at 24%: p95 21, p99 27, 83%; at 30%: p95 17, p99 21, 58%); a 10-loss run is
expected about every 82 trades. Independence is assumed, and losses here cluster (one release or one open hits several series at once), so
these are a floor. The result recomputes them at the observed win rate with the empirical longest run.

## WORST SINGLE LOSS (hard limit 0.50)
Largest possible fill 0.50: the premium is 50c a contract. **At 10 contracts: 500c premium + fee ceil(7% x 10 x 0.5 x 0.5) = 18c = $5.18.
At 5 contracts: 250c + fee ceil(8.75c) = 9c = $2.59.** The limit is in code and tested (a fill at 0.52 is no trade); a research read of
history, not an order. In the XOI1/QSTALE1 history a quote jumped through 50c to a 94c fill, which this limit removes by construction (counted as "limit").

## N tried
Two tries per asset class (A, B) x 4 classes (metals, energy, fx, crypto) = **8**. Running count about 728,726 -> **728,734**; one-sided
z bar for 0.05 / N is about **5.27**. Per-series, per-class, per-group and per-month tables are reports. Any change to the code after this
commit will be disclosed in the result.

## Overlap with L1 and OICORE
None placed: no L1 or OICORE series is in the universe, and the trade is a 15 minute cheap side on other markets. If the family were ever
traded, a position could not coincide with L1 in the same market. Not a promotion path.

## Expected read date and forward read
Run once on the settled history on 2026-11-03 (this commit, then the score). A forward re-score of the same fixed code on windows closing
after 2026-11-03 09:15Z needs no recorder (Kalshi candles are retrievable): 150 more Try A trades take about 0.4 months pooled, about 3
months for the macro group alone, so a forward read of the pooled rule is possible by about 2026-12-03; a read of the releases alone
is not before about 2027-02.
