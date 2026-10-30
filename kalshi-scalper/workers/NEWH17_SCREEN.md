# NEWH17 feasibility screen (2026-10-30, research only, no outcome read)

Owner order: the search for new Kalshi 15 minute strategies never stops. This round is built to waste no tries: every idea below was
priced on the cost arithmetic BEFORE any data was scored, and an idea whose best case cannot reach the bar was dropped, not tried.
Inputs: `NEWH15_INVENTORY.md` (38 series, spreads at 10 minutes left), `CENSUS_2026-10-30.md`, `NEWH15_RESULT.md`, `NEWH16_DIGEST.md` and
`NEWH16_RESULT.md`, `FXUSD_RESULT.md`, `RACELOCK_RESULT.md`, `XVENUE1_RESULT.md`, and README greps for each idea. Times US Central.

## The arithmetic every candidate is priced against (computed here, C = 10, fee 7% x C x p x (1-p) rounded up per order)

A taker buys at the ask: price p plus half the series' median spread, plus the fee per contract. Break-even hit rate = that all-in price. PF 1.5
needs W with W(1 - p_eff) = 1.5 (1 - W) p_eff.

| Spread class (median at 10 min left) | Series | Fee a contract at 50c | Break-even hit rate | Hit rate for PF 1.5 | Edge over 50% PF 1.5 needs |
|---|---|---|---|---|---|
| 1c | BTC, ETH, SOL, XRP, DOGE, BNB, HYPE, gold, WTI, natural gas, silver | 1.80c | 52.3% | **62.2%** | 12.2 points |
| 2c | ZEC, copper | 1.80c | 52.8% | 62.7% | 12.7 points |
| 3c | NEAR, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, palladium, platinum | 1.80c | 53.3% | 63.1% | 13.1 points |
| 10c | Brent | 1.80c | 56.8% | 66.4% | 16.4 points |
| 25c | the four Treasury yields | 1.70c | 64.2% | 72.9% | 22.9 points |

**Correction to the brief.** The brief says PF 1.5 needs "about 58%". On a 50c entry it needs about **62%** (58% is PF 1.27 at 50c; NEWH16's best
cell, 56.6% at a 50.7c price, printed PF 1.18, which matches the formula). Break-even is 52 to 53% as stated. So the bar for any coin flip taker
entry is a 12 to 13 point information advantage over a book quoted 1c wide. The only entries that can clear PF 1.5 with a smaller edge are far
from 50c (favourites held, cheap sides late), and both are owner bans. That is the whole reason the table below ends with nothing registered.

Data windows used by the registrations in this series: discovery 2026-08-24 to 09-28, validation 09-28 to 10-18, frozen holdout 10-18 to
10-30 (latest 12 days). Series younger than that cannot have all three: the four yields (first settled 10-19), Brent (10-21) and AUD/USD and
USD/CAD (10-07, 11 days before the holdout) have **no discovery window at all, or one too short for a 100 trade bar**.

## The screen: 12 candidates

| # | Candidate | Mechanism and named counterparty | Data (exists today?) | Windows | Feasibility number (best case, no outcome) | Verdict |
|---|---|---|---|---|---|---|
| 1 | **TIEPERSIST**: YES after a window ended in a tie (a stale feed repeats the same print; ties settle YES) | A frozen Pyth print makes the next window a tie too and a tie is YES. Counterparty: the quoter who prices a stale-feed window at 50c. | Yes (`mk_*.json`, strike vs expiration value) | 26 series, 163 windows that follow a tie in discovery | Needs P(tie after tie) of about 25% or more to reach 62% (a tie is a certain YES, so 0.5 + P/2). **One counted look, discovery only, tie flags only: 0 ties after 163 ties** (WTI 0 of 59, XRP 0 of 32, BNB 0 of 18, gold 0 of 12, silver 0 of 10, others fewer). Upper 95% bound 1.8%, a tie premium of 0.9 points. | **DROP** (mechanism absent; 1 look, 0 tries) |
| 2 | **ROLL**: Pyth commodity feed changes contract at a futures roll, a jump bigger than a 15 minute move decides the window | A deterministic sign on a known calendar date. Counterparty: books priced at 50c through a calendar-spread jump. | Dates from the public futures calendar; whether the Pyth feeds roll at all is not known without reading outcomes | WTI/gas/copper/silver/gold/Brent, about 1 to 3 roll windows each since Aug 24, 15 or fewer pooled; one per month per series going forward | The edge could be huge (jump larger than sd), but trades are about 15, against 100/50/30 per window. | **DROP** NOT_ENOUGH_DATA by construction. Forward watch only (no recorder): roll dates are on the public futures calendar. |
| 3 | **PRINTNOISE**: after a window ended UP, the next window ends DOWN more often, because both share one Pyth print (strike of k+1 is the settled value of k) | Noise in the shared print makes consecutive moves negatively correlated. Counterparty: books assuming independence. | Yes | Metals, oil, gas, FX: about 28,000 windows | For a random walk the shared print is the true price at that second, so the correlation is about 0. The theoretical maximum (all noise) is -0.5, flip probability 66.7%; the borderline needed for 62.2% is a correlation of about -0.37, i.e. noise as big as the move. FLAT2/GEN1 pools and BTC1 FADE (FALSIFIED) already sit next to it. | **DROP** (best case unreachable; reworded BTC1 FADE) |
| 4 | **LAGAVG**: at the open of a CF 60 s average window the strike is the lagged average, so spot starts ahead of or behind it | Spot minus the 60 s average at the open is about half the last minute's move: sd about 0.13 of a 15 minute sd. Counterparty: makers who quote the first candle at 50c. | Yes (Coinbase/Binance 1m, Kalshi 1m) | 9 CF series, about 58,000 windows | If the book priced the open at exactly 50c and only displacements above 1 sd were traded: 0.5 + 0.399 x 0.129 x 1.5 = **57.9% < 62.2%**. The books are quoted 1c wide with spot in view, so the real best case is a point or two; QUIRK1 (first candle both sides, 28 of 28) priced the base case. Pyth single print series have no such lag. | **DROP** (best case 57.9% before the market prices any of it) |
| 5 | **ALTSPOT**: Binance/Coinbase 1 minute spot against a thin CF index (ZEC, NEAR, HYPE, BNB) in the last half of the window | Index built from stale exchanges lags spot. Counterparty: the thin-book quoter. | Yes | 4 series x 6,428 | Needs a 12 point advantage from information the quoter reads on the same screen at minute resolution; BTC lead-lag (LAG2/LAG2B), XLEAD1, XMAC1, GEN1 market-wide and NEWH12 XLAG are all FALSIFIED or closed on the same feed. | **DROP** (reworded lead-lag; priced in) |
| 6 | **YIELDMAKE**: rest a bid below mid on the 25c-spread Treasury yield contracts, held to settlement | Counterparty: takers who cross a 25c spread. Best case is large (free fill 12c under mid at a fair 50c is PF 1.67). | Candles yes; fills only from the public trade tape (not fetched) | 4 series x 476 windows = **12 days, all of it the frozen holdout** | The arithmetic could clear the bar, but there is no discovery or validation window: every yield window is inside the latest 12 days. Also 160 to 380 contracts a market, so a handful of fills a day. | **DROP** NOT_ENOUGH_DATA (by calendar). Re-look when the yields have 40+ days (about 2026-11-30); the weekly census will say when. |
| 7 | **ALTMAKE**: rest a bid at the bid on 2 to 3c spread series (NEAR, ZEC, FX), held | Counterparty: takers paying the spread. | Fills unobserved in candles | 1,586 to 6,428 | Even free fills at the bid with no fee give PF = (0.5 + 0.015) / (0.5 - 0.015) = **1.06** at a 50% hit rate. Cannot reach 1.5. | **DROP** (best case 1.06; MAKER2 to MAKER5 / MM1 own the maker question) |
| 8 | **SETTLETYPE**: calibration of favourites by settlement type (CF 60 s average damps the last minute, a Pyth single print does not) at equal distance from the strike | A single print flips more late than an average; counterparty: quoters using one vol model for both. | Yes | 12 CF and 9 Pyth series | The test is "hold the favourite at 80c to 97c": the live L1 family. | **DROP** owner ban (favourite-and-hold) |
| 9 | **RELEASES**: pooled scheduled releases (EIA storage and crude, Treasury auctions, 8:30 ET data) on oil, gas, yields | Counterparty: books not widened before a release. | Calendar, yes | About 9 to 15 releases in 67 days per series | EVT1 and CPI1 were already NOT_ENOUGH_DATA; yields have no discovery window; the pooled-release read is on the director's list for mid-December. | **DROP** NOT_ENOUGH_DATA (count) |
| 10 | **COINRACE+**: a fourth Coin Race rule (second choice, size of the over-round, time to close) | Counterparty: the thin race quoters. | Yes | 6,343 events | H1 to H3 and RACELOCK T2 all lost 20 to 40% of every ticket (spread 8c a leg padded on every name, win rate 36% priced at 39c); T1 locks are 1 in 400 windows worth cents. | **DROP** (same book, four verdicts already) |
| 11 | **CROSSDUR**: 15 minute market against the hourly ladder on the same instrument at the same instant (top of the hour windows) | A consistency arbitrage between two Kalshi products on one index. Counterparty: the less liquid of the two. | Partly (`ladl1_*`, `conf2_lad.sqlite`) | Bitcoin and Ethereum, 1 in 4 windows | CONF1 LADDER, LADL1 (KXBTCD 6 min PF 1.38 / 0.95 / 0.53), ARB1 to ARB5 (cross-market consistency, zero persistent locks) are FALSIFIED; a hedge needs two fees and a second fill. | **DROP** (covered by the ledger) |
| 12 | **TIEPREM**: tie premium on the YES side of WTI, FX and yield series | Ties settle YES (WTI 2.7%, 2-year yield 4%). | Yes | 4,913 WTI windows | 0.5 x tie rate = 1.35 points at most against a 1.8c fee plus half a spread (NEWH15: "killed by arithmetic"). | **DROP** (0 tries, already priced in NEWH15) |

Also dropped on sight and not numbered, per the owner's bans: copies of falsified rules on another market (prior-window continuation or fade on
the thin coins is BTC1 CONT/FADE and XLEAD1), L1 and its variants, favourite-and-hold, cheap-side-late, round trips, 5,000 rule generators,
and anything the refinement chat owns (the live rule's filters, the exit, sizing).

## Result of the screen

**Zero candidates reach a hit rate of 62% (PF 1.5) at a coin flip price, so nothing is registered.** The two ideas that could reach the
arithmetic (ROLL, YIELDMAKE) have no data window: 15 events, and 12 days that are the holdout itself. Those two are dated looks, not tries:

- YIELDMAKE: revisit when the four Treasury series have 40 settled days (about 2026-11-30). Needs the public trade tape of ~1,900 markets (a
  fetch, no recorder). The weekly series census below is the reminder mechanism for new listings; the yield dates are in this file.
- ROLL: whether the Pyth commodity feeds roll contracts can be read from the Pyth feed names in the rules text without touching outcomes; if they
  do, November's roll windows are a forward count, not a try.

One look was used (TIEPERSIST, discovery, tie flags). Tries: 0. N unchanged.
