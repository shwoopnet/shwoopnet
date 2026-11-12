# R&D Idea Desk A: structure and cross-market Idea cards (Nov 11, 2026)

Desk angle: market structure and cross-market mechanisms (pricing relationships between related Kalshi markets, order book and queue effects, fee and rounding structure, settlement mechanics, timing and calendar, liquidity provision). Research and simulation only. Nothing here places, changes or cancels an order, spends money, or touches trading code. Zero Kalshi API calls were made to write this file. All cards are stage **Idea**: registered as ideas, NOT scored. Each needs its own protocol committed before any outcome is read. The Verification Analyst scores the four uniqueness checks (lifecycle 7d), not this desk; the notes under "self-check" are my own reading and can be overruled.

## Status after the first day (updated Nov 12, 2026, 00:20 UTC; verdicts are as reported to this desk by Main, the Chief of Staff, and were not re-derived here)

| Card | Status | Why |
|---|---|---|
| 1 CRONCLUSTER1 | CLOSED by V2, 0 tries; RETIRED (V2 POWER2); re-derived and confirmed by this desk Nov 12 (`DESK_A_HELD_DATA_NOV12.md`) | No clustering: peak 0.87 to 1.11 against the 1.3 gate |
| 2 TIECOND1 | CLOSED by V2, 0 tries | 13 cells; best tie rate lower bound 1.96% against the 6% gate |
| 3 EXDIV1 | CLOSED by V2 at gate 0, 0 tries | Dividends pass through to perp holders as cash |
| 7 RETAILFRAC1 | CLOSED at stage A; stage B RETIRED (V2 POWER2); stage A re-derived and confirmed Nov 12 | No two crowds; stage B not run (Main's ruling). Descriptive only: dollar-typed takers pay 12c to 14c less per contract than whole-number takers, probably the longshot lean of small orders |
| 8 BASEFX1, 10 TWINLOCK1 | OUT, not run | Main ruled the lock and parity family CLOSED under the 3-falsified rule (ARB2 to ARB5, LADBFLY1, XSER1). Draft declined-list rows are in `IDEA_DESK_A_PROTOCOLS.md`, section P7 |
| 4 ORHARVEST1 | Protocol written (P5) | Main's ruling: MMSIM1 family for the one-test-per-family rule, so its scored stage queues behind MMSIM1's Nov 24 read; the counts-only stage can run now |
| 5 RACEMAKE1 | Protocol written (P6) | Same family; queues behind MMSIM1 |
| 6 RESIL1 | Held | Order-flow family is at 2 FALSIFIED; with RETAILFRAC1 closed at stage A (no try), a FALSIFIED here would close the family for good. Not recommended |
| 9 PERPBIN1 | HELD (Main, Nov 12 02:30Z) | Testable on held data with zero reads, but the try is not spent now: prior 2% and it raises the deflation floor |
| 11 AUCTION1 | RETIRED as a PF test (Main, Nov 12) | About 80 events a year against about 920 needed (`DESK_A_POWER_NOV12.md`) |

Desk worker count: 0 subagents (one session).

## 0. Honest count first

**11 cards, not 12.** The brief asked for at least 12 and also said never pad. This angle was mined heavily before today (about 730,000 rules tried; V2's batches B and C today carded or closed monotonicity, butterfly, cross-series dominance, calendar consistency, pinning, round numbers, new listings, stale reopen quotes, early close, fee rounding, rebates, settlement lag, averaging). I read those results before writing. A 12th card would have been a variant of something closed; section 4 lists what I considered and dropped, with the prior test that covers each, so nobody repeats it.

Two of the 11 are honest "cost input" cards (1 and part of 7), not strategies. Three carry a declined-list or family-budget flag that the Verification Analyst or the owner must rule on (cards 4, 5, 6 and 7 share the flags described there).

**One standing constraint that shapes every card:** the bot acts once a minute (the minute function) plus a 10 second exit loop. Anything that needs a reaction faster than about a minute is not implementable without new infrastructure, so I kept sub-minute latency ideas out or marked them.

## 1. What I read to avoid repeats

`docs/RND_CHARTER.md`, `docs/STRATEGY_LIFECYCLE.md` (7d uniqueness, 7e declined list, 7f classification, 7g versions), `docs/POLITICS_RULES.md`, `CLAUDE.md`; on the V2 branch (`claude/epic-ptolemy-0amjd9`): `workers/IDEA_CARDS_NOV11B.md`, `IDEA_CARDS_NOV11C.md`, `FIVE_DIFFERENT_MECHANISMS.md`, `IDEA_BACKLOG.md`, `DATA_INVENTORY.md`, `DOCS_CARDS_RESULT.md`, `LITSCAN_NOV11.md`, and the headline or result section of about 110 registrations, protocols and results (lock scans, MMSIM1 and its variants, TAPEFLOW1, STALE1, EARLYCLOSE1, PIN1/ROUND1/AVG1, LADBFLY1/XSER1, CAL1, SETTLE1, FXUSD, NEWH15, NEWH17, CMD3, STOCKPERP design, BARRIER1, COINRACE1, RACELOCK, OVERROUND1, INCENT1, COST1, BOOKIMB1, DEPTH1, R6T, FLOW tests, PUB20, TODSEAS1, REGIME1, SWEEP1, NONCRYPTO1); on the Refinement branch (`claude/refine-live`): `refine_tools/CARDS_NOV11_ROWS_74_93.md`, `POLITICS_CARDS_NOV11.md`. File listings only (no outcome) of the data branches `quote-data`, `perp-data`, `sports-data`, `pol-data`, plus the column headers of the R6 book, tape and coverage files.

Three facts from that reading that the cards lean on:

- **Fee facts (COST1, DOCS_CARDS_RESULT):** the 15 minute series and KXBTCD are plain `quadratic`, maker multiplier 0; taker fee 0.07 x p x (1-p) per contract, rounded up to the cent per order. About 160 sports and futures series carry a 0.0175 maker rate.
- **Settlement facts (SETTLE1, FXUSD, NEWH15):** every non-crypto 15 minute family settles on ONE Pyth 1 minute candle close against ONE print at the open; only Bitcoin and Ethereum average 60 s. A tie (settle equals strike) settles YES under the primary rule text; measured tie rates are 1.1% to 2.7% of windows (EUR/USD 1.78%, GBP/USD 1.90%, AUD/USD 2.71%, USD/JPY 1.11%, USD/CAD 2.27%, WTI 2.7%). The FX secondary text says "strictly greater", which conflicts with the primary text (see section 5, alert 1).
- **Tape facts (R6 header on `quote-data`):** every public trade row carries a microsecond `created_time`, a `taker_outcome_side`, a `yes_price_dollars` to 0.1c, and a FRACTIONAL `count_fp` (for example 52.40 and 12.94 contracts). Whole-number and fractional sizes can therefore be told apart on data we already hold. Card 7 is built on that field.

## 2. The cards

Card line format (lifecycle 7f): `NAME | family (entry mechanism + exit style) | risk class | stage`. "P" is my honest probability that the idea clears the research bar (cash PF 1.5 on development and on the held-out third, deflated) AND is tradable at the bot's cadence. For the two cost-input cards P is the chance of a usable finding instead.

### Card 1. CRONCLUSTER1 (execution structure, a cost input, NOT a strategy)

`CRONCLUSTER1 | none (measurement of taker arrival by second of the minute) | no position | Idea`

- **Mechanism, one line:** bots that run on a clock (ours included) all take liquidity in the first seconds after each minute boundary, so the touch is thinner and worse at second 0 to 10 than at second 40 to 59.
- **Why it should exist:** the project notes on main record that orders sent later after the minute boundary fill worse, and that a material share of orders end unfilled (figures are in the notes on main and are not repeated here). If other clock-driven takers cluster at the same boundary, we are queuing behind them every minute. The loser today is us.
- **Data and terms:** `quote-data:book15r6/*/trades.csv.gz` (complete public tape per window, microsecond times, five series, Oct 29 to Nov 13) and `book.csv.gz` (best 5 levels each side every 2 s). Public Kalshi data already recorded under the repo's recorder rules. No new read.
- **Cheapest test:** histogram of taker contracts by second of the minute (0 to 59), per series and per minute-to-close, against a flat line (chi-square, clustered by window); then touch size and spread at second 55 to 59 versus second 0 to 10 from the 2 s book. About 1,300 windows a series a week, millions of trades. No outcome is read.
- **Time to a verdict:** 2 to 3 hours. I can run it from this desk with zero API calls.
- **If true, what it gives:** an execution change for EVERY strategy (send before the boundary, or at a fixed off-boundary second), which is a version under 7g, tested beside the parent on fill rate and net dollars. It is not a new strategy and takes no shadow slot.
- **Closest prior work:** the refinement chat's R5 timing note and the send-time log (our own orders only). Different: this reads the whole market's tape, not our orders.
- **P:** 35% that a clear cluster exists; 15% that it yields a measurable fill-rate gain for gold L1 or OICORE.

### Card 2. TIECOND1 (settlement rule asymmetry, conditional)

`TIECOND1 | rule asymmetry: buy YES at the window open when a tie is likely; hold 15 minutes to settlement | about 50% to 60% win rate, loss about the price paid (45c to 55c), 1 contract, group D (non-crypto 15 minute, open of window) | Idea`

- **Mechanism, one line:** a tie settles YES, so in windows where the settlement print is unlikely to move at the source's precision, YES is worth 50c plus half the tie mass and a symmetric 50/50 quote underprices it.
- **Why it should exist, and who loses:** NO buyers and makers who quote the open symmetrically. NEWH15 closed the POOLED version by arithmetic (tie premium at most 1.3c against a 1.75c taker fee). Nobody scored it CONDITIONALLY. The tie rate is not flat: it should be several times the 1% to 3% average in dead hours (late US afternoon into the Asian open for FX, overnight for natural gas and the metals) and near 100% when the source is frozen. Break-even as a taker needs the conditional tie mass above roughly 8% with an open spread of 2c or less; as a resting order (maker fee 0) it needs only the tie mass above the adverse selection.
- **Arm A (quiet windows):** predictor = the trailing realised move in source ticks, which is free and exact from Kalshi's own data: the strike of window t+1 is the settle print of window t, so consecutive strikes give the 15 minute moves at the source's own precision, and `strike(t+1) == strike(t)` is a tie. (Check first: sign(strike(t+1) - strike(t)) must reproduce `result(t)` in essentially every window. That check also fixes RULES1's "final value not stored" gap.)
- **Arm B (frozen source):** exchange holiday halts and half days (first date Thursday Nov 26, 2026, then Dec 24 to 25 and Jan 1), the daily break, and the eleven shell 15 minute series (S&P 500, Nasdaq 100, Dow and others) if they go live outside cash hours. If Kalshi lists a window while the print cannot change, it ties. Whether such windows are listed at all is unknown (STALE1's gap events suggest most are not); that is the first thing the census answers.
- **Data and terms:** arm A on V2's held market tables and candles (`alts2`, `alts3`, `fxusd/candles`, `rep`, `fresh`: strike, result, first candle bid and ask), about 80,000 settled non-crypto windows. No fetch. Arm B forward on the NC15 recorder once merged (its series list has no gold; gold is a spot index and almost never ties anyway). Holiday calendar: CME Group's published holiday hours, keyed in by hand like EVENT830's calendar (no automated read).
- **Cheapest test:** stage 1, counts only: tie rate by series x UTC hour x trailing-move tercile; stop if no cell with 300 or more windows has a tie rate of 8% or more. Stage 2, registered before any P&L: buy YES at the first candle's ask in the pre-registered cells, cash basis, development two thirds, held-out read once. N counted: one per series group (FX, metals, energy, rates), so 4, plus arm B as 1.
- **Time to a verdict:** stage 1 in about 2 hours on V2's box; stage 2 the same day if stage 1 survives; arm B's first observation Nov 26.
- **Closest prior work:** NEWH15 (pooled tie arithmetic, not run), FXUSD (tie rates measured, not traded), RULES1B (rule-text features on the cheap side, 42 exact cases), OPENQ1 (first-candle misprice, a different signal). Different: conditional on a tie predictor, mid band at the open, YES only.
- **Self-check:** signal = the settlement rule plus source precision (not a price band); exit = hold 15 minutes with different entry rules; not favourite-late (entry near 50c at the open); not on the declined list. Honest weakness: makers very likely price ties in liquid hours; the idea lives or dies in the dead hours where books are also widest.
- **P:** 4%.

### Card 3. EXDIV1 (contract mechanics on Kalshi's single-stock perps)

`EXDIV1 | corporate-action calendar: short the perp before the ex-dividend open, cover after the cash open (time exit) | about 60% win rate, symmetric loss about 1.5% to 2% of notional overnight, size TBD, group E (equity perps, calendar) | Idea`

- **Mechanism, one line:** on the ex-dividend morning the cash share price drops by the dividend; a perp holder gets no dividend, so unless Kalshi adjusts for it or the perp already trades at a discount, a long loses the dividend and a short collects it.
- **Why it should exist, and who loses:** retail longs who treat the perp as "the stock" and hold through the ex-date. V2's STOCKPERP design note raised the question ("whether the perp is adjusted at the ex-dividend date is NOT visible in any field") and left it as a risk note, never a test. Funding cannot offset it: it is zero 88% of the time and capped near 0.085% a day (PERPCARRY1), against quarterly dividends of 0.7% to 1.6% on names in Kalshi's list (Verizon, Pfizer, Philip Morris, Chevron, Exxon, AbbVie, Merck, PepsiCo, Coca-Cola, Johnson and Johnson and about 25 more at 0.5% or above; yields are from memory and must be re-keyed).
- **Arithmetic, stated before any data:** a mean gain of about 0.9% minus about 0.24% for two crossings and about 0.1% of spread leaves about +0.55% against an overnight standard deviation of about 1.75%, which is a cash PF near 2.2 IF the perp is unadjusted and the discount is not already priced. Both ifs are the test.
- **Data and terms:** `perp-data` (hourly snapshots since Oct 21 with `price` and `reference_price`; 30 second open and close windows and 1 minute candles from Nov 6; recorders run to 2027-02-26). Stock perps only began trading Nov 5. Ex-dividend dates: keyed in by hand from each company's own dividend press release (about 35 dates a quarter). No automated calendar source is cleared (SEC EDGAR asks for a contact address in the User-Agent, which our privacy rule forbids without the owner's say; exchange calendar pages are unread terms, so barred).
- **Cheapest test:** gate 0 (1 hour, docs only): read Kalshi's perp contract terms for a dividend or corporate-action adjustment. If dividends are passed through, CLOSED in an hour. Gate 1 (descriptive, no P&L): for each ex-date since Nov 6, the path of (perp minus reference) / reference from two sessions before to one after: pre-priced discount, jump, or nothing. Gate 2 (registered): short at the last 30 second sample before the prior cash close, cover at the first sample after 10:00 ET, cash basis with the 0.12% per crossing fee.
- **Sample and time:** about 35 events a quarter. First descriptive read Dec 1 (about 10 events), first scored read Dec 31 (about 25), held-out by Feb 26 (about 45). Pooled events on one date cluster, so the honest n is dates.
- **Closest prior work:** EARNPERP1 to 3 (earnings), OVN1 to 5 and CASHGAP (overnight gaps, no dividend split), PERPEQ4 (SPY vs US 500 ratio). Different signal (dividend calendar), different day set.
- **Self-check:** signal = a calendar from a different data source on a different market type; exit = time; correlation with gold and OICORE should be near zero. Honest limits: any live version is a new product for the bot (perps are not traded by any code today), so it needs an owner popup and a build; overnight single-stock risk is unhedged.
- **P:** 6% (about 35% unadjusted x 35% not pre-priced x 50% survives costs and sample).

### Card 4. ORHARVEST1 (liquidity provision: over-round harvest on slow multi-outcome events)

`ORHARVEST1 | resting one-sided quotes on every bracket of a mutually exclusive daily event, completing into a locked set; orphans flattened by a set time | per-set P&L bounded, small; legs kept to YES 12c to 88c; group F (daily multi-outcome, LP) | Idea`

- **Mechanism, one line:** in a mutually exclusive set (for example the six brackets of a city's daily high) the YES asks sum to more than $1; a maker who sells YES one tick inside the ask on every bracket (a resting NO bid) and gets the whole set filled holds a lock worth the over-round.
- **Why it should exist, and who loses:** retail YES buyers of single brackets who pay the over-round one ticket at a time. OVERROUND1 showed the over-round ranks the taker's loss; nobody tested collecting it from the other side. The adverse party is the nowcaster who lifts only the bracket that is about to win, which is why the test must use a pessimistic fill model.
- **Data and terms:** `quote-data:wxens/quotes*` and `results*` (Kalshi bracket quotes for 14 cities twice an hour since Nov 4, highs and lows), `raincal`, `daily/` (30 minute snapshots). All public Kalshi data already recorded. Fee type of the weather series is NOT known to me; V2's COST1 table has it. If a maker fee applies the card is weaker.
- **Cheapest test:** stage 1 (counts): the over-round (sum of YES asks minus 1) by hours to close and city; stop if the median is under 4c. Stage 2 (registered): simulate a NO bid one tick inside on each bracket at a fixed look, with two fill models reported side by side: STRICT (a fill only when a later snapshot shows the market traded through my price, so every fill is adverse) and LOOSE (volume rose and the last price was at or above my price). A lead needs positive cash P&L per completed-or-flattened set under STRICT. About 14 cities x 2 markets x 7 days = about 200 event-days a week.
- **Time to a verdict:** stage 1 in 2 hours from this desk (zero API). Stage 2 in 1 day. A real fill model needs a tape, which the snapshot recorders do not have.
- **Closest prior work:** MMSIM1 (two-sided quotes on ONE strike, time flatten), OVERROUND1 (taker cheap side), RACELOCK (taker Dutch book). Different: the P&L source is the set's over-round and the exit is set completion.
- **Self-check, with a flag:** owner rule 6 (liquidity provision counts as unique; signal check not applicable) may cover it, but the Verification Analyst may instead call it a version of MMSIM1 on another market (7g). **Declined-list flag:** an unfilled set leaves single NO positions, which are favourite-shaped. I restrict legs to YES 12c to 88c and flatten orphans, but whether that clears "any buy-the-favourite-and-hold rule" (7e) is the owner's call. The charter also allows only one test per family at a time, so this queues behind MMSIM1's Nov 17 read.
- **P:** 3%.

### Card 5. RACEMAKE1 (liquidity provision: the Coin Race over-round)

`RACEMAKE1 | resting NO bids one tick inside on all five legs of a Coin Race event, set completion, orphans flattened 3 minutes before close | per-set bounded; group F (LP) | Idea`

- **Mechanism, one line:** the five YES asks of `KXCRYPTOLEAD15M` sum to about 1.24 at 9 minutes left with an 8c spread a leg (RACELOCK), so a maker who is filled on all five at ask minus 1c holds $4 of payoff for about $3.81.
- **Why it should exist, and who loses:** five-way lottery buyers. NEWH15 named this as a possible maker test in a footnote and did not register it ("not recommended before the owner's other recorders report").
- **Data and terms:** V2's `data/newh15/candles.sqlite` (31,715 markets, 1 minute bid, ask, volume; no sizes). A real test needs the public tape per market (API reads, shared budget: about 750 requests for 150 events).
- **Cheapest test:** stage A, zero API, on candles: per event, would a quote at ask minus 1c on each leg have been traded through within the next 3 minutes (strict), and what was the set's cash P&L including orphans flattened at the bid. Stage B only if stage A is positive under the strict model: tape for 150 events.
- **Time to a verdict:** stage A half a day on V2's box.
- **Honest weakness:** this book reprices on spot in seconds and our quotes would be up to a minute stale, so fast takers pick off the leg that just moved. That is the most likely way it dies. Same family and declined-list flags as card 4.
- **P:** 3%.

### Card 6. RESIL1 (order book resilience after a sweep)

`RESIL1 | book state: after a taker removes at least half of the touch, follow the sweep only if the level is NOT refilled within two snapshots; hold or 3 minute time exit | win rate near the entry price, 1 contract, group G (book state, 15 minute) | Idea`

- **Mechanism, one line:** when makers refill a swept level at once the sweep was uninformed; when they step away the sweep carried information the remaining quotes have not absorbed.
- **Why it should exist, and who loses:** the slower resting quotes one or two levels behind the swept price. Field: depth restored at a swept price within 4 to 6 seconds, which no test has used (BOOKIMB1 and DEPTH1 use static sizes, FLOW1 and TAPEFLOW1 use signed flow totals).
- **Data and terms:** `quote-data:book15r6` (2 s books plus full tape, five series) and `book/` (KXBTCD, 3 s). Held, public.
- **Cheapest test:** events = taker prints that remove 50% or more of the displayed touch; arms = refilled versus not refilled; entry at the next ask on the sweep's side one minute later (the bot's cadence, which is the honest version); cash PF by arm, development two thirds by date. Thousands of events in 14 days.
- **Time to a verdict:** 1 day from this desk or V2.
- **Family budget flag:** this is the order-flow family, which already has FLOW1 and TAPEFLOW1 FALSIFIED. A third falsified test closes the family for good (charter section 4), so RESIL1 and card 7 cannot both be spent lightly. If only one runs, I would run card 7 first.
- **P:** 2%.

### Card 7. RETAILFRAC1 (retail versus API flow from fractional sizes)

`RETAILFRAC1 | flow classifier: fade the net direction of fractional-size taker flow when whole-number flow disagrees; hold to settlement | win rate near the entry price, 1 contract, group G | Idea`

- **Mechanism, one line:** a fractional contract count (52.40, 12.94) is what a dollar-amount order typed into the app produces, so the tape can be split into app retail and API flow, and the two can be compared window by window.
- **Why it should exist, and who loses:** app users buying "$5 of YES". Every flow test so far pooled all takers (S-FLOW1, FLOW1, TAPEFLOW1, MECH1), and the pooled signal was noise or priced. A split by who is trading is a different field with different logic.
- **Stage A is a cost input worth having on its own (a map, not a strategy):** the share of taker volume that is fractional, by series, hour and minutes to close. It tells every maker and LP idea (cards 4 and 5, MMSIM1) where the uninformed flow is.
- **Data and terms:** `quote-data:book15r6/*/trades.csv.gz` and `coverage.csv.gz` (result per window), `book/*/trades.csv.gz` for KXBTCD. Held, public.
- **Cheapest test:** stage A counts only (2 hours, this desk). Stage B, registered first: per window at the 6 minute mark, net fractional flow and net whole-number flow over the prior 4 minutes; trade only when they disagree in sign and both exceed a pre-set size; buy the whole-number side at the ask one minute later; cash PF, about 6,500 windows in 14 days across five series, development two thirds by date.
- **Time to a verdict:** 1 day.
- **Self-check:** signal = a different field of Kalshi's own data (trade size type), which the owner's rule accepts; entry differs from every live rule (no price band trigger); the assumption "fractional = app retail" is unverified and stage A must show the two groups differ at all (size, timing, price paid) before stage B is worth a try. Same family budget flag as card 6.
- **P:** 4% for a strategy; 50% that stage A's map is useful.

### Card 8. BASEFX1 (cross-series arithmetic identity on inflation prints)

`BASEFX1 | implication lock between the year-over-year and month-over-month markets of the same print; two legs closed together at settlement | lock or nothing, tiny size, group H (economics releases) | Idea`

- **Mechanism, one line:** the year-over-year rate is fixed by the month-over-month change and the index level of 12 months ago, which is already public, so "MoM at or above m" implies "YoY at or above X" for a known X, and the two Kalshi series must respect that ordering.
- **Why it should exist, and who loses:** makers or retail quoting the two series (KXCPI and KXCPIYOY, core likewise) from separate consensus numbers without doing the base-effect arithmetic. ARB3 and ARB4 scanned within one series; nobody checked across the two.
- **Data and terms:** BLS index levels (US government, public domain, twelve numbers keyed in by hand). Kalshi quotes: the daily recorder already holds KXCPI and KXCPICORE; the YoY series is not recorded, so it needs about 20 public reads per print from the shared budget, or a watchlist line.
- **Cheapest test:** build the implication table from the unrounded index (the rounding of both published figures makes it a band, not a point; the table must carry the band), then count snapshots where YES(YoY at or above X) ask plus NO(MoM at or above m) ask is under $1 after two taker fees. Zero violations on two prints closes it.
- **Time to a verdict:** the next two CPI prints (dates from EVENT830's frozen calendar), so 1 to 6 weeks.
- **Family flag:** lock scans ARB2 to ARB5 are all FALSIFIED; if the Chief of Staff treats lock scans as one closed family, this card and card 10 are out.
- **P:** 2%.

### Card 9. PERPBIN1 (same-venue cross-instrument: Kalshi's perp as a field for Kalshi's binaries)

`PERPBIN1 | cross-instrument field: the Kalshi Bitcoin perp's premium to its reference and its open interest change, read at the 15 minute market's open; mid-band entry, hold | win rate near price, 1 contract, group B-adjacent (Bitcoin 15 minute) | Idea`

- **Mechanism, one line:** the perp premium measures how crowded leveraged longs are on this venue, and the same retail crowd buys the YES side of the up-or-down market.
- **Why it should exist, and who loses:** leveraged retail longs, if the binary's makers do not condition on the perp. OICORE and XOI1 used the binary's own open interest, MECHOI1 used an outside venue; the Kalshi perp's own fields were never joined to the binaries.
- **Data and terms:** V2 holds Kalshi's public margin candles for KXBTCPERP and KXETHPERP (1 minute, with open interest, June 3 to Nov 3, from SNAPBACK1) and the 15 minute candle book. No fetch.
- **Cheapest test:** premium tercile and open-interest-change tercile at the window open against the result, both directions pre-registered (2 tries per asset, 4 in all), development two thirds, about 9,000 windows an asset.
- **Time to a verdict:** 1 day on V2's box.
- **Self-check, with a flag:** it trades Bitcoin 15 minute windows, where OICORE lives, so the correlation check against OICORE is the one that could fail it. Weak mechanism: makers price off spot and the premium is small.
- **P:** 2%.

### Card 10. TWINLOCK1 (in-play twin-book lock, Kalshi's own sports quotes)

`TWINLOCK1 | lock: both teams' YES asks sum under $1 after fees for at least two consecutive polls; two legs held to the final whistle | lock or nothing | Idea`

- **Mechanism, one line:** a two-team game has two separate books for complementary outcomes; during a scoring run one book can reprice before the other.
- **Data and terms:** `sports-data:ingame/` (both moneylines at about 20 s while a game is hot, since Nov 8). Kalshi's own prices only, which is what the owner's sports rule allows (price consistency, no outside data).
- **Cheapest test:** count polls where ask(A) plus ask(B) plus both taker fees is under $1, and how many persist two polls (40 s, the least the bot could act on). No outcome needed. About 10 games a day.
- **Time to a verdict:** 1 hour from this desk.
- **Flags:** lock-scan family (see card 8). ARB2 found zero on 1 minute history; this is the same idea at 20 s in play.
- **P:** 1%. Listed because it costs an hour, not because I expect it.

### Card 11. AUCTION1 (Treasury auction concession on the daily yield ladders)

`AUCTION1 | calendar: on a coupon auction day, bet the auctioned tenor's yield closes BELOW the near-the-money strike seen the morning before the 1 PM ET result; hold to the daily close | mid-priced entry 30c to 70c, about even win rate, 1 contract, group C (calendar) | Idea`

- **Mechanism, one line:** dealers push yields up into an auction to make room for the supply and yields fall back afterwards (the auction concession, documented by Lou, Yan and Zhang, 2013).
- **Why it should exist, and who loses:** primary dealers hedging inventory are price-insensitive for a few hours; a Kalshi ladder priced off the morning yield would not carry the usual afternoon give-back.
- **Data and terms:** the Treasury's auction schedule (US government, public; the Treasury host is already read by the market tape), and the daily recorder's `KXUST2A`, `5A`, `7A`, `10A`, `30A` ladders at 1,440, 360 and 60 minutes before the close (on `quote-data:daily/` since Nov 4). No new read.
- **Cheapest test:** on each auction day take the strike nearest above the 360 minute mid for the auctioned tenor, buy NO at its ask, hold; compare with the same rule on non-auction days (the control). One pooled try plus the control.
- **Time to a verdict:** slow. About 5 matched auctions a month, so about 15 by February and 60 by late 2027. A first descriptive look is possible in mid December; a verdict at n 100 is more than a year away unless tenors are pooled across each auction day (correlated, so it does not really shorten it).
- **Self-check:** signal = an official calendar (a different data source, as EVENT830's is); market type = daily rate ladders, which no live strategy trades. One test per family at a time puts it behind EVENT830's forward read. TNOTE1 found the ladder prices the overnight move, which lowers the prior.
- **P:** 3%. Included for honesty about the angle; it ranks last on speed.

## 3. Rankings

**By speed to a first honest verdict:**

| Rank | Card | First verdict | Runs where | API calls |
|---|---|---|---|---|
| 1 | TWINLOCK1 (10) | 1 hour | this desk, `sports-data` | 0 |
| 2 | CRONCLUSTER1 (1) | 2 to 3 hours | this desk, `quote-data` | 0 |
| 3 | TIECOND1 (2), stage 1 | 2 hours | V2's box (held tables) | 0 |
| 4 | RETAILFRAC1 (7), stage A | 2 hours | this desk, `quote-data` | 0 |
| 5 | ORHARVEST1 (4), stage 1 | 2 hours | this desk, `quote-data` | 0 |
| 6 | EXDIV1 (3), gate 0 | 1 hour (docs), then Dec 1 and Dec 31 | docs, then `perp-data` | 0 |
| 7 | RACEMAKE1 (5), stage A | half a day | V2's box | 0 (stage B about 750) |
| 8 | RESIL1 (6) | 1 day | this desk or V2 | 0 |
| 9 | PERPBIN1 (9) | 1 day | V2's box | 0 |
| 10 | BASEFX1 (8) | 1 to 6 weeks (two prints) | recorder plus about 20 reads a print | about 40 |
| 11 | AUCTION1 (11) | mid December descriptive, 2027 for n | `quote-data:daily/` | 0 |

**By distance from what failed today** (cheap-side rules, grammar sweeps, butterfly, taker-flow fade, pinning, round numbers, new listings, mention combos, count models):

1. EXDIV1: a contract-mechanics event on a product no test has treated as a calendar; nothing like it in the ledger.
2. TIECOND1: a settlement-rule asymmetry at the open, mid band; the pooled version was only closed by arithmetic.
3. RETAILFRAC1: a field nobody has used (who is trading), though it sits in the flow family.
4. ORHARVEST1 and RACEMAKE1: the P&L source is the over-round, which was only ever paid, never collected; flags apply.
5. AUCTION1: new calendar, new market, slow.
6. CRONCLUSTER1: not a strategy; new measurement.
7. RESIL1, PERPBIN1: new fields inside families that have already lost.
8. BASEFX1, TWINLOCK1: new places to look for a lock; the lock family is 0 for everything so far.

**Top 5 overall (speed and difference together):** EXDIV1, TIECOND1, RETAILFRAC1, CRONCLUSTER1, ORHARVEST1.

**Sum of the strategy probabilities:** about 28%, so the honest expectation from this whole file is that zero or one idea reaches a shadow read, and the two cost-input cards are the likeliest to pay for the work.

## 4. Considered and dropped (already covered, or blocked)

| Idea | Why dropped | Covered by |
|---|---|---|
| Benchmark fix windows (4 PM London for FX, silver fix, COMEX settle) | Tested | PUB20 P06 (FALSIFIED, pooled n 97 PF 1.09), FXUSD FIX_PRE (NOT_ENOUGH_DATA), STRUCT1 |
| Futures roll gap in commodity markets | Tested or thin | NEWH17 ROLL (about 15 events), CMD3 (zero events in development). See alert 2 below |
| Pooled tie premium | Closed by arithmetic | NEWH15 (1.3c against a 1.75c fee). Card 2 is the conditional version |
| One-touch versus terminal dominance, reflection pricing | Thin and partly run | BARRIER1 (NOT_ENOUGH_DATA); no terminal monthly ladder to pair with |
| Quotes inside the last 150 s with the average partly fixed | Tested | QUOTE1 (PF about 0), AVG1, CFRTI1; also sub-minute, so not implementable |
| At-the-money range bracket against ladder-implied volatility | Same signal on another market | VOLGAP1; a variant under 7g |
| Daily gold or oil ladder still trading after its settlement print is fixed | Does not exist | KXGOLDD settles on the 5 PM ET candle; KXWTI closes at 14:30 ET with its settlement |
| Range brackets versus the above ladder (three-leg lock) | Grids share no edge | THREELEG1 |
| Hour h versus hour h+1 at the same strike | Calendar consistency family | CAL1, LADCONV1, LADCOH1 |
| Two-sided quotes at the open of a 15 minute window | Dead on arrival for Bitcoin: the R6 header row shows about 12,900 contracts resting at the best bid, so a new order sits behind all of it; on the thin series it is MMSIM1 on another market (a version, 7g) | R6T MAKER5, MMSIM1 |
| Reading the settlement oracle (Pyth) directly | Already a director brief; history fetch failed (401); Pyth's endpoint terms are unread, so barred | GOLDPYTH-H, Brief A |
| Monotonicity scans on the thinner hourly ladders | Same lock on other markets | LADBFLY1 (0 violations in 266,302 snapshots) |
| Being the seller of parlays (the house side of the combo over-round) | **Blocked by a standing rule, not by evidence.** It is a buy-NO-at-a-high-price-and-hold shape, which 7e bans without a written owner exception, and every combo test ran cheap side only by the owner's Nov 3 rule, so the house side has never been measured | PARLAY1, MVE1, COMBO1 (taker side only). I am not proposing it; I am noting that the largest documented retail bias in this area sits on the banned side |

**Data that would open more of this angle (nothing here is free and cleared today):**

- Closing-auction imbalance feeds (NYSE, Nasdaq): the imbalance published from 3:50 PM ET predicts the direction of the official close, and Kalshi's S&P and Nasdaq daily ladders settle on that close. A named, price-insensitive counterparty, which is what the owner asked for in the old equities notes. The feeds are paid or their terms are unread. One event a day, so slow as well.
- Spot Bitcoin ETF daily flows: the 3 to 4 PM ET benchmark window has forced creation and redemption trades whose direction is the day's flow. The flow tables are on issuer and aggregator pages whose terms are unread, so barred. Without the flow sign the idea collapses into an hour-of-day test, a family that has already failed (TODSEAS1, REGIME1).
- A tape for the weather and Coin Race books (a small recorder, owner popup, runner minutes over the Charter's 250): needed before cards 4 or 5 could be more than a bound.

## 5. Alerts for the Chief of Staff (not ideas)

1. **Rule-text conflict on ties (flag to the owner with the text, per the politics rule on resolution edge cases).** SETTLE1 records that the primary text of the non-crypto 15 minute families says "at least" (a tie settles YES) while the FX secondary text says "strictly greater". FXUSD measured ties settling YES. Card 2 depends on the primary reading; if Kalshi ever applies the secondary text the sign flips. Nothing automatic should rest on it.
2. **CMD3's event source is gone.** CMD3 (futures roll windows on the commodity perps) flags a roll from Yahoo's futures bars, and the Yahoo reads stopped today. The first real event it was waiting for is the December crude oil contract's last trade on 2026-11-20. If V2 wants that event, the flag has to be re-specified on Kalshi's own `reference_price` jump (an amendment to CMD3, V2's call) before Nov 20, or the event is lost.
3. **Gold L1 is not exposed to a futures roll.** I checked this because late November is the December to February gold roll: KXGOLD15M settles on Pyth's `Metal.Index.1OZGOLD/USD`, a spot index (GOLDPYTH-H note), so there is no contract switch inside a window. No action.
4. **Interest on balances: unverified.** REBATE1 found no page describing interest on cash or collateral and said "not proven absent". My memory is that Kalshi has paid a yield on balances above a minimum in the past; I could not verify it from the repo and did not fetch anything. If it exists and the account is not enrolled, it is free money on the sizing base; the owner can check it in the account's own settings in a minute. I am not quoting a rate.
5. **Fractional sizes and 0.1c prices are in the tape.** The R6 tape shows trades at $0.001 and counts like 52.40. Any simulation that assumes whole contracts and 1c ticks at the extremes (the 1c to 3c tail card TAIL1, fee rounding at one contract) should re-check its assumptions.

## 6. Protocols for the top three

Deepened, ready-to-run protocols for EXDIV1, TIECOND1 and RETAILFRAC1 (with CRONCLUSTER1 stage A, which shares RETAILFRAC1's files) follow in `kalshi-scalper/workers/IDEA_DESK_A_PROTOCOLS.md` on this branch.
