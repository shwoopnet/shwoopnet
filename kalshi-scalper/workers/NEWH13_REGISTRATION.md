# NEWH13 registration (Strategy Research V2 worker NEWH13, 2026-10-30, research only)

Family: cross-market consistency and arbitrage (the same event priced twice), gold and Bitcoin. Written and pushed BEFORE any
NEWH13 rule was joined to a fill quote after its signal or to any outcome. Code `src/scalper/newh13.py` (committed with this
file; its thresholds are the ones below and are not changed after any score); result `workers/NEWH13_RESULT.md`. Public data
only; nothing new fetched for a score (the probes listed under "What was looked at" were quote-free or history-free). Times are
UTC in the code and US Central (CDT, UTC-5, the whole sample) in words.

## Step 1: what this family already holds in the ledger (grep of README to GEN10)

| Same event, two prices | Ledger | Status |
|---|---|---|
| 15 minute Bitcoin and Ethereum against the hourly ladder at the shared close, directional, toward the ladder | **XM1** (Bitcoin -2.05c, Ethereum -7.45c z -4.20, FALSIFIED); **BLADX** (Bitcoin, EITHER leg: 15 minute side or ladder side, 1.08 / 0.76 and 0.78 / 0.92, FALSIFIED: "neither book is the stale one") | TESTED on Bitcoin for both legs, on Ethereum for the 15 minute leg. No try. |
| 15 minute GOLD against the hourly gold ladder KXGOLDH at the shared close, directional | **GLADH** (NEWH2 H4: the 15 MINUTE leg when 6c+ off the ladder's interpolated value; 52 / 40 trades, PF 0.63 / 0.66, NOT_ENOUGH_DATA, "the ladder is the one that is wrong when they disagree") | The 15 minute leg is TESTED. **The LADDER leg on gold has not been run** (BLADX ran it on Bitcoin only), and GLADH's own reading (the ladder is the wrong price) is the case for it: **H2** below. |
| Locks between the 15 minute contract and the hourly ladder at the shared close (riskless by monotonicity) | **LOCK2** (registered forward poll, main session's lane, never read); **LOCK2H** (Bitcoin history Sep 26 to Oct 26 on minute candles: 4 of 704 closes with a 1c lock, 5 lock minutes, NOT_ENOUGH_DATA) | Bitcoin TESTED in history. **Gold has never been scanned for a lock** (GLADH was one-sided, LADLOCK was across ladder strikes): **H1** below. Bitcoin's days before Sep 26 are unread: **I2** (information). |
| Locks across the strikes of ONE ladder (adjacent-strike monotonicity) | **LADLOCK** (NEWH9: Bitcoin 0 signals in 1,544 events, gold 2 in 1,026, NOT_ENOUGH_DATA, "the ladders keep monotonicity at minute resolution"); **KINK** and **TAIL** (NEWH4, the ladder's own shape, FALSIFIED) | TESTED at minute resolution. The recorded 5 level book (3 s, since Oct 29) is new data: **I1** (information only, two days). |
| Locks across events (mutually exclusive sets, deadline ladders, range brackets against the above ladder) | **ARB1** (0 in 12 scans), **ARB2, ARB3, ARB4** (0 opportunities, FALSIFIED), **ARB5** (sports totals, FALSIFIED), **RULES1** (the one "lock" was two different questions) | TESTED. No try. |
| A Dutch book WITHIN one 15 minute market (YES ask plus NO ask under $1 after fees) | **L14 / O9 / O10** (NOT_RUNNABLE: "a consistent book has ask plus other-side ask at or above 1 by construction") | **NOT_RUNNABLE, 0 tries, not a data problem:** Kalshi keeps ONE order book per market with YES bids and NO bids; the YES ask is defined as 1 minus the best NO bid and the NO ask as 1 minus the best YES bid, so YES ask + NO ask = 1 + the spread, never under 1. A crossed state (YES bid + NO bid over $1) is matched by the exchange the instant it would arise, so no taker can buy both asks under $1 at any resolution. Nothing to score. |
| Kalshi against an options-implied distribution (same close) | **IV1** (DVOL fair value for the 15 minute market, FALSIFIED), **LAD1** (option-style fair value on KXBTCD, 6 tries, FALSIFIED), **DIGI1** (strategy card: Kalshi's Bitcoin ladder against Deribit's call-spread-implied probability, "to register; forward only", never registered) | The model-free version (Deribit's OWN option prices at the SAME expiry instant, not a volatility model) has not been run. **It cannot be run in history** (see H3): registered as a forward-only candidate, NOT_ENOUGH_DATA now, 0 outcome reads. |
| Kalshi against another venue's price for the same event | **PM1, PM2, PM3** (Polymarket, FALSIFIED), **COINPREM**, **XMAC1** | TESTED. No try. |
| Consistency across clocks and instruments as an L1 filter | **CONF1, CONF2, CORR1, LADL1, E4** | TESTED and banned ground (L1 filters). No try. |

So the untested cells with usable public data are: a gold lock at the shared close (H1), the gold LADDER leg traded toward the 15
minute book (H2), and a model-free options cross for the Bitcoin ladder which only a forward recorder can feed (H3). The
within-market Dutch book is structurally impossible on this exchange (0 tries). The 5 level book gives an information look (I1).

## What this is NOT

No 88c to 97c favourite (L1): every directional fill here is capped at 85c and sits 7 to 10 minutes before the close. No L1
exit, size, filter, hour or throttle test. Nothing bought in the last 6 minutes: every fill candle ends 420 s or more before the
close (the lock scan over minutes 6 to 1 is an information count of signal-candle quotes, no fill, no trade). No cheap side chosen
by a price band: H2's side is the direction of a monotonicity violation between two books. No round trip (held to settlement).

## What was looked at before this was written (disclosure)

The ledger sections above; `newh9.load15` / `newh9.load_ladder` counts (universe sizes only, no quote joined to another book, no
outcome): 1,459 top-of-hour gold windows, 1,026 with a settled KXGOLDH event at the same close (discovery 444, validation 429,
holdout 153); KXGOLDH strikes are $2 apart, 12 a market; 1,004 of the 1,026 15 minute strikes lie inside the ladder's strike range;
every minute from 840 s to 60 s before the close is pairable on about 1,023 of them. Kalshi's public rules for the two series
(one market each, today): both resolve on "the close price of the 1-minute candlestick for gold" at the same instant (the 15
minute market: at or above its strike; the hourly: above x.99), rounded to 2 decimals, so a monotonicity lock between them is
riskless. Deribit's public API (today, keyless): `get_instruments` with `expired=true` lists only the latest expiry (Oct 30
08:00 UTC); `get_last_trades_by_currency_and_time` returns NO option trades for any past hour tried (Sep 15, Oct 1, Oct 15, Oct
22, Oct 29) and `get_tradingview_chart_data` and `get_book_summary_by_instrument` answer "instrument not found" or "not open" for
an expired daily option; only the live instruments answer. The book recorder's first five runs (origin/quote-data, `book/`, Oct
29 10:26 to Oct 30 10:28 UTC) were read for their column headers only. No lock, violation or trigger was counted before this
file was pushed: for a lock test the signal count IS most of the result, so no `counts` command was run.

## Common to every scored rule (fixed now)

- **Data:** gold 15 minute windows from the local candle files (`l1b`, `book`, `fresh`, `five`, first file wins per close) and
  KXGOLDH from `newh2_goldh.sqlite` (the last 15 minutes of each hourly market, Aug 23 to Oct 27); Bitcoin for I2 from `l1b`,
  `book`, `fresh` and `conf2_lad.sqlite` / `lad2.sqlite`. **Universe (time only):** every settled gold 15 minute window closing
  at the top of an hour whose KXGOLDH event (same close instant) is on file. **Windows:** DISCOVERY closes before 2026-09-21;
  VALIDATION 2026-09-21 to 2026-10-18; HOLDOUT 2026-10-18 to 2026-10-30 (frozen; read once, only after a pass in both, after that
  result is pushed).
- **Quotes:** a candle's closing bid and ask. A quote is readable if 0 <= bid <= ask <= 1, ask above 0 and bid below 1. YES ask
  = ask; NO ask = 1 - bid. **Fill:** the NEXT candle's ask of every leg bought, whatever it is (a lock at the signal can be a loss
  at the fill). Held to settlement, nothing sold.
- **Fees:** 7% x C x p x (1 - p) rounded up to the cent per order, per leg. Headline C = 10; C = 1 and fees x1.2 at C = 10 reported.
- **Zero volume both ways:** PF with all trades and without trades whose signal or fill candle (any leg) had volume 0.
- **Bar (each scored rule):** PF at C = 10 at least 1.5 in EACH window, net positive at fees x1.2 in each, at least 100 / 50 / 30
  trades (discovery / validation / holdout), a named counterparty, pooled day-clustered z at least the deflated bar (about 5.26).

## H1 GLOCKH (1 try): a lock between gold's 15 minute contract and the hourly gold ladder at the shared close

- **Structure:** both contracts settle on the same Pyth gold 1 minute close. For a ladder strike k (x.99) at or above the 15 minute
  strike K0: [final >= K0] + [final <= k] >= 1 always, so 15 minute YES plus ladder NO at k pays at least $1 (and $2 when the final
  lands in [K0, k]). For k below K0: 15 minute NO plus ladder YES at k pays at least $1.
- **Signal:** at each candle ending 840, 780, ... , 480 s before the close (minutes 1 to 7 of the window), over every ladder
  strike with a readable quote in that candle, the best pair's lock = 1 - p1 - p2 - (fee(p1) + fee(p2)) / 10 at C = 10, p1 and p2
  the two legs' asks. A lock of at least 1.0c is the signal; the FIRST signal candle decides the close (one trade per close).
- **Fill:** both legs at the next candle's asks (ending 780 to 420 s before the close). Payoff = [15 minute leg wins] + [ladder
  leg wins]. Net at C = 10 = 10 x (payoff - p1 - p2) - fees.
- **Counterparty:** the slower of the two quoting bots when Pyth gold moves: the hourly ladder's makers at a strike within $2 of
  the 15 minute strike, or the 15 minute market's makers, whose stale quote is lifted before it is pulled. They pay because their
  refresh cycles differ and neither reads the other book.
- **Honest alternative:** LOCK2H on Bitcoin found 4 lock closes in 704 and none that lasted beyond 2 minute closes; candle closes
  are not simultaneous, so a minute-candle lock is an upper bound; the gold ladder is thin (NEWH10 saw mostly zero-volume
  candles), so a "lock" against a stale wide quote vanishes at the fill.
- **Prediction:** 0 to 5 signal locks of 1.0c in the 873 discovery and validation closes, none surviving to the fill at a profit:
  **FALSIFIED** (zero signals) or **NOT_ENOUGH_DATA** (under 100 discovery trades).
- **Kill:** zero signal locks in discovery and validation together: FALSIFIED (the history version). 1 to 99 discovery trades:
  NOT_ENOUGH_DATA, with the count of closes with a lock, the largest signal lock, the fill cost and whether any fill still locked.
  100 or more: the common bar.

## H2 GLADX-L (1 try): the gold LADDER leg traded toward the 15 minute book when monotonicity is violated at the mids

- **Why it is new:** BLADX ran both legs on Bitcoin; on gold only the 15 minute leg was run (GLADH), which lost and read the LADDER
  as the wrong price. This trades the ladder. It is adjacent to GLADH and BLADX (disclosed) and uses no interpolation: a strict
  inequality between the 15 minute book and the two ladder strikes that bracket its strike.
- **Signal candles:** ending 660, 600, 540 and 480 s before the close (minutes 4 to 7); the FIRST trigger decides the close.
  Readability: 15 minute spread at most 4c, the ladder strike's spread at most 6c (cost filters, seen before the trade).
- **Trigger:** m15 = 15 minute YES mid; k_hi = the smallest ladder strike at or above K0, k_lo = the largest strike below K0 (both
  must be quoted). By monotonicity P(above k_hi) <= P(at or above K0) <= P(above k_lo). **A:** the ladder YES mid at k_hi is at least
  m15 + 0.03: buy ladder NO at k_hi. **B:** the ladder YES mid at k_lo is at most m15 - 0.03: buy ladder YES at k_lo. If both, the
  larger violation. One contract set, one leg.
- **Fill:** the leg's ask at the next candle (600 to 420 s before the close), inside [0.05, 0.85] (nothing at L1's 88c to 97c);
  missing or outside the band counted, never retried. Held to settlement.
- **Counterparty:** the hourly ladder's quoters at the strikes next to the 15 minute strike, whose quote at that strike has not
  followed the busier 15 minute book (GLADH: when the two disagree the ladder is the one that is wrong); they pay because the
  ladder's near-the-money strikes at the top of the hour are quoted by fewer bots than the 15 minute contract.
- **Honest alternative:** the gold ladder's spread is wide and its candles mostly empty, so a mid violation of 3c is a wide-quote
  artefact and the taker pays that width at the fill; BLADX found neither book stale on Bitcoin; a 3c mid gap is close to one
  fee plus one spread.
- **Prediction:** discovery 60 to 200 trades, PF 0.8 to 1.2 at C = 10: **FALSIFIED** or **NOT_ENOUGH_DATA**.
- **Kill:** the common bar (under 100 discovery trades NOT_ENOUGH_DATA; PF under 1.5 or net x1.2 at or below 0 in any window
  FALSIFIED; holdout read once only after both pass; day z under the bar after all PF gates: NOT_ENOUGH_DATA).

## H3 BTCDIGI-F (1 try, forward-only; NOT_ENOUGH_DATA now, 0 outcome reads)

- **Event:** the KXBTCD market closing 08:00 UTC (3:00 AM Central) each day shares its close instant with Deribit's daily BTC
  options expiring 08:00 UTC. The two settle differently (Kalshi: the 60 s CF Benchmarks BRTI average; Deribit: the 30 minute TWAP
  of its own index), so they are the same event only to the width of that gap.
- **Rule (fixed now, to be run only on data recorded after this file):** at each minute from 60 to 30 minutes before 08:00 UTC,
  from Deribit's public order book of the two daily call strikes bracketing the ladder strike K (and the two puts for a check),
  the digital probability P(final > K) = the call spread's mid price (in USD at the index) divided by the strike gap, linear
  between the two strikes; the ladder's YES ask at K. Edge = P - ask - fee for YES, (1 - P) - (1 - bid) - fee for NO; trade the
  larger if at least 4c, fill at the next minute's ask, 5c to 85c, one trade per event, held. Fees as above.
- **Counterparty:** Kalshi ladder quoters not reading the deepest BTC options venue at the one hour of the day when it prices the
  same instant. **Honest alternative:** the settlement gap and PM1, XM1, LAD1 (Kalshi's ladder was the better price than Polymarket,
  than the 15 minute interpolation and than an implied-volatility model).
- **Why it is forward only:** Deribit's public API keeps no quotes or trades of expired options (probed today, see the disclosure);
  only live instruments answer. A recorder would poll `public/get_order_book` for the bracketing strikes and the KXBTCD market
  object once a minute for 30 minutes a day: one event a day, so 60 events take two months.
- **Prediction:** FALSIFIED (PF 0.8 to 1.2 on the first 60 events). **Kill:** under 60 events NOT_ENOUGH_DATA; PF under 1.5 at C = 10
  or net x1.2 at or below 0 on the first 60: FALSIFIED. No recorder is built by this worker; this is a candidate for the owner.

## H4 Dutch book within one 15 minute market: NOT_RUNNABLE (0 tries)

Reason in the table above: on Kalshi one book serves both sides, the YES ask is 1 minus the best NO bid, so the two asks sum to 1
plus the spread by definition at every instant and at every resolution. No data, no rule, no count.

## Information looks (counted in N, not rules)

- **I1 KXBTCD 5 level book consistency at depth** (the book recorder, `book/` on origin/quote-data, 3 s polls of 7 near-the-money
  strikes, Oct 29 to Oct 30): per poll and adjacent strike pair k1 < k2, (a) a top-of-book cross: NO bid(k1) + YES bid(k2) above
  $1 (a lock before fees); (b) a lock of at least 1c after C = 10 fees; (c) a mark inversion: YES bid(k2) above YES bid(k1); (d)
  the locked quantity when walking the 5 levels (the sum of sizes while the two level prices still cross); (e) how many
  consecutive polls a cross lasts. Reported by minutes to the close. Two days of data: a count, no claim, no trade.
- **I2 Bitcoin lock scan on LOCK2H's unread days:** H1's signal count (minutes 14 to 1, no fill, no outcome) on KXBTC15M against
  KXBTCD for closes Aug 24 to Sep 25 (LOCK2H read Sep 26 to Oct 26), to set beside its 4 of 704.
- **I3 gold lock count over the whole window:** H1's signal count on minutes 14 to 1 (the late minutes are information only; no
  trade is placed there), comparable with LOCK2H and I2.
- **I4 H2's base rate:** the same ladder legs (NO at k_hi, YES at k_lo) at the same candles when there is NO violation (the
  inequality holds by at least 3c), discovery and validation: win rate against price paid, so an H2 result can be told from a
  drift of the ladder's near strikes.

## Count

N tried: **3** (GLOCKH, GLADX-L, BTCDIGI-F registered forward) + 4 information looks (I1 to I4) = **7**. H4 adds 0. Running count
about 700,154 (after GEN10) + 7 = **about 700,161**. One-sided Bonferroni z bar at 0.05: **5.26**.
