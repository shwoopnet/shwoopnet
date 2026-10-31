# LADLONG1 registration (Strategy Research V2 worker, 2026-10-31, research only)

Written and pushed BEFORE any outcome or settled result of this rule was read. Code `src/scalper/ladlong1.py` (committed with this
file); result `workers/LADLONG1_RESULT.md`. Owner's go-ahead (relayed by the main session, Oct 30 evening): reopen the hourly
ladders trade, "the overpriced-longshots finding whose mirror trade was closed earlier". That is a go-ahead to test, NOT a
promotion. Times are UTC in the code and US Central (CDT, UTC-5, the whole sample) in words. Nothing live is touched.

## 1. Genuinely new or a reword (said first)

**Mostly a reword of tested cells; one cell is new. Honest answer: "reword of cell X at another clock, new cell Y".**

- **Mirror of TAIL / NEWH4 H3 (README "Result: NEWH4", `workers/NEWH4_RESULT.md` line 16):** NEWH4's TAIL-BTC BOUGHT the 2c to 6c
  longshot (YES or NO) on the hourly Bitcoin ladder at 30 minutes left: win rate 2.9% and 3.3% against 4.2% paid, PF 0.64 / 0.72
  (z -2.87, -3.03), FALSIFIED. The other side of those very contracts is what this rule buys, but at a **different clock (45
  minutes, not 30)**, on a **different universe rule** and, above all, as a **different trade** (the buyer's loss is not the
  seller's gain: the seller crosses a different spread and pays a different fee, and bears a 90c-plus tail loss). The NEWH4 README
  line (line 7782) records that "the mirror of TAIL (selling the longshot, i.e. buying the 94c to 98c side and holding) was not
  tried: it is a favourite-and-hold entry, closed by the owner on 2026-10-28". This round tests it only because the owner
  reopened it. **Disclosure: that TAIL result already showed the longshot win rate under its price on this same data (Aug 24 to
  Oct 18), so the SIGN of the gross premium on discovery and validation is not blind. The numbers of this rule (mean after fee,
  spread, tail, PF) are new, but the frozen holdout is the only window not touched by TAIL.**
- **TAIL1 (README line 5863, 15 minute gold, 4c to 10c underdog, FALSIFIED -2.77c, "buying cheap sides loses by about spread plus
  fee"):** same economic idea on a different clock and market; the buy side. Its mirror is not a cell anyone ran; the spread plus
  fee it found is the cost this rule also has to beat from the other side.
- **LADL1 (README line 7425 registration, 7628 result):** L1's own rule, side whose ask is 0.88 to 0.97, at 10 and at 6 minutes
  before the close, on KXBTCD and KXETHD with strikes chosen by a 1c to 99c mid 30 to 27 minutes before the close. FALSIFIED for
  Bitcoin: PF at 1 contract 1.20 / 0.87 / 0.69 at 10 minutes and 1.38 / 0.95 / 0.53 at 6. **LADL1 covered the 88c to 97c band on ALL
  strikes (so it already contains the far-wing NO bought at 88c to 97c, and the far-below YES at 88c to 97c) at the 10 and 6 minute
  looks.** So **bands DNnear and UPnear (88c to 94c paid) are a REWORD of a LADL1 cell at a different clock (45 minutes before the
  close, a different and look-ahead-free strike rule, a wing-only subset).** The new cell is the **94c to 98c paid band** (UPfar,
  DNfar: LADL1's band stopped at 0.97 and had no 97c to 98c) **and the 45 minute clock for every band**. Even there, LAD1 and E4 had
  the 45 minute clock for other trades.
- **NEWH14 I2 (`workers/NEWH14_RESULT.md`, "Information looks"):** information only, not a trade. It says the settlement lands
  inside the 25c to 75c range 3 to 9 points more often than priced, so the ladder's wings are rich on average, and that a two-leg
  set's gross premium of about 3 to 5 points is eaten by 4c to 5c of two taker fees and two spreads. This rule is the single-leg
  version at extreme prices, where the fee is small (7% x p x (1-p) is 0.33c at 95c against 1.75c at 50c), so I2 is the reason to
  try, not a result.
- **THETA1 and FLB1 (README lines 7354, 3294):** long-dated markets (days to months), favourite drift sold or held; FALSIFIED. A
  different horizon (45 minutes) and a different mechanism (hourly settlement on a 60 second average of a liquid index, not a
  long-dated opinion market). Not a reword; cited as the general prior.
- **Owner ban of 2026-10-28 (no further buy-the-favourite-and-hold research on the 15 minute L1 markets):** this rule is on the
  HOURLY ladder, a different ticker, and the owner reopened exactly this trade. The DN bands are, in form, "buy a 88c to 98c
  favourite and hold" on an hourly strike; they are in scope only because of the explicit reopening.
- **CORR1 and the G3H1 audit failure (README lines 7416, 7421, 7487):** the lesson applied. `lad1.sqlite` chose strikes from mids
  35 to 25 minutes BEFORE the close, which is after any entry at 45 minutes. This rule does **not** use `lad1.sqlite`. The strike
  universe below is chosen from quotes 52 to 55 minutes before the close, ten minutes before the look, and the files used
  (`conf2_lad.sqlite`, `lad2.sqlite`) store every strike with a mid of 1c to 99c in the candles 55 to 52 minutes before the close
  (the CONF2 and CORR1 fetch rule), a superset of every band below, so no strike is dropped by anything that happens after 52
  minutes.

## 2. Rule and universe (fixed from prices before the entry look; no outcome and no later quote chooses a strike)

- **Market:** KXBTCD, the hourly Bitcoin "above K" ladder, events closing at every top of the hour. Files: `conf2_lad.sqlite`
  first, then `lad2.sqlite` (the first file that holds a close wins it, as NEWH14); 1,544 closes from 2026-08-24 00:00 UTC to
  2026-10-29 23:00 UTC. The longer file (NEWH14's) CAN be used because its strike universe is rebuilt here from the 55 to 52
  minute quotes: the file keeps every strike with a mid of 1c to 99c in that window, so no band is truncated. `lad1.sqlite` is not
  used.
- **Universe candle:** the latest present candle among those ending 52, 53, 54 and 55 minutes before the close. A strike is in the
  universe if on that candle 0 < YES bid < YES ask < 1, the spread is at most **4c**, and its YES mid lies in a band. An event
  with none of those four candles is counted "no universe candle" and dropped.
- **Bands (YES mid at the universe candle; four tries; edges fixed now):**
  - **UPfar:** 0.02 <= mid < 0.06; far-above strike; BUY NO. (2c to 6c is TAIL's longshot band, so the comparison with the buyer's
    PF is like for like. Below 2c a NO costs 98c or more, gains at most 2c and the fee, spread and 1c tick alone use most of it.)
  - **UPnear:** 0.06 <= mid <= 0.12; BUY NO. (Up to 12c: still a wing, 1.5 to 2 sigma out at 45 minutes; above it the strikes are
    the 15c to 40c shoulder NEWH14 already used. Here the NO costs 88c to 94c, LADL1's band.)
  - **DNnear:** 0.88 <= mid <= 0.94; far-below strike; BUY YES at its ask. (Mirror of UPnear.)
  - **DNfar:** 0.94 < mid <= 0.98; BUY YES at its ask. (Mirror of UPfar.)
  The mid edges are mirrored (UP at m is DN at 1 - m) so the two wings are read like for like. 2c and 6c, 6c and 12c are the
  edges because TAIL used 2c to 6c and the next natural bucket doubles it; no edge was tuned on any outcome. A strike belongs to
  exactly one band.
- **Look and fill:** the entry look is the candle ending **45 minutes** before the close. At the look the strike must still be
  quoted two-sided (0 < bid < ask < 1) with a spread of at most 6c, else "no look" (counted). The fill is at the **NEXT candle**
  (ending 44 minutes before the close): UP bands pay the NO ask = 1 - the YES bid of that candle; DN bands pay the YES ask of that
  candle. The fill candle must be two-sided with a spread of at most 6c, and the price paid must be at most 0.99 (a NO ask of 1.00
  is not a trade); otherwise counted "no fill" or "price". Nothing at or after the fill candle chooses or removes a strike.
- **Position:** one contract-leg per strike, each strike one observation, held to settlement. All qualifying strikes of an event are
  taken (no cap); the hourly EVENT is the independent unit for every test and for the bootstrap.
- **Fees:** 7% x C x p x (1 - p) on the price paid, rounded up to the cent per order, **C = 10 headline**, C = 1 and fees x1.2 at
  C = 10 also reported. Note: at p = 0.96 the fee is 0.027 x 10 -> $0.03 a 10-contract order, 0.3c a contract; at p = 0.90 it is
  $0.63, 6.3c / 10. The spread is paid by crossing: UP pays 1 - bid, DN pays the ask.
- **Zero volume both ways:** a trade is "zero-volume" if the look candle or the fill candle has volume 0; every table reports the
  mean and PF with all trades and without them.
- **Sizing note:** the one-minute ladder candles carry no sizes, so a 10 contract fill on a 2c to 12c strike is MODELLED, not
  observed (the 25c to 75c strikes in NEWH14 had 400 to 1,500 contracts at the best price; far strikes are thinner).

## 3. Counterparty

Who sells these wings too cheaply: **retail buyers of lottery tickets on far strikes** (the favourite-longshot bias, found in this
ledger on the buy side of the same strikes by TAIL: win 2.9% against 4.2% paid, and on 15 minute gold by TAIL1), and **makers who
quote the wings rich** as insurance against a fat-tailed Bitcoin hour, collecting a premium for the tail they bear. They persist
because the buyer pays for the payoff shape, not the odds, and because the maker has to carry the tail between hourly fills.
**Honest alternative:** the wings are priced for fat tails and the tail is real. Bitcoin has hours that move 1.5% to 3% in 45
minutes, on which a 95c NO loses 95c and wipes out the premium collected on 20 to 40 winning contracts. The 3 to 9 point I2
premium is an average over the middle strikes; at the far wings, with about 600 events a window, 30 or fewer tail events decide the
mean, so a positive mean could be only a quiet stretch.

## 4. Numeric prediction and kill criteria

**Prediction (before any outcome):** win rate within 1.5 points above the mean price paid; mean net per contract at C = 10 between
-0.8c and +0.8c; **the most likely verdict is FALSIFIED.** Arithmetic behind it: TAIL-BTC's longshot gap (win 1.3 points under its
price) is the gross premium at 2c to 6c, about +1.3c a contract against the YES mid; crossing the spread from the NO side costs
about 0.5c (1c spread) to 1c, and the fee about 0.3c at 96c, leaving about 0c; UPnear and DNnear at 88c to 94c pay 0.4c to 0.6c
in fee plus spread against a smaller gap. Power note: one contract on a 97% winner has an sd of about 17c, with about 1,000
strikes in about 600 correlated events a window the standard error of the mean is about 0.5c to 0.7c, so a **z of 3 needs a mean of
about 1.5c to 2c, larger than the I2 premium**. Most of the outcomes are therefore FALSIFIED (mean under the bar) or
NOT_ENOUGH_DATA (mean over the bar, z under 3).

**Reported for every band and window:** trades, events with a trade, win rate against the mean price paid, mean net cents per
contract at C = 10, at C = 1 and at x1.2, PF at C = 10, 1 and x1.2, net, event-clustered z and day-clustered z (against zero), the
worst single-event loss ($ at C = 10, all strikes of the event together), the worst day ($ at C = 10), a bootstrap (5,000
resamples of 720 hourly events with replacement from ALL the window's events, an event with no trade counting as 0, the strikes
of one event moving together; seed 20261031) 5th percentile and mean of the 30 day net at C = 10, and the funnel (universe,
no look, no fill, price).

**The registered verdict (per band; read in this order):**
1. **NOT_RUNNABLE:** fewer than **300** events with a trade in discovery or fewer than **150** in validation.
2. **FALSIFIED:** in discovery OR validation, the mean net per contract at C = 10 is under **+0.5c**, or the mean net at fees x1.2
   is at or under 0.
3. **NOT_ENOUGH_DATA:** the means pass (>= +0.5c at C = 10 and positive at x1.2 in BOTH windows) but any of these fails in either
   window: event-clustered z >= **3**; PF at C = 10 >= **1.3** (one loss can erase many wins: a positive mean with PF under 1.3 is
   NOT a pass, and the result says so); worst day not worse than **-$125** (25% of a $500 account, at 10 contracts a strike); the
   bootstrap 5th percentile of the 30 day net >= 0.
4. **NOT_YET_FALSIFIED (forward registration only, never "works"):** all of the above in discovery AND validation. The pooled
   event z is also compared with the deflated bar for N = 728,673 + 4 = 728,677 (**z = 5.27**) and reported; a band under 5.27 earns a
   forward registration with the bar written next to it, nothing more.
   The frozen holdout (closes 2026-10-18 00:00 UTC to 2026-10-30 00:00 UTC, i.e. Oct 17 7:00 PM to Oct 29 7:00 PM Central; 257
   closes) is read **only** for a band that reaches this step, once, and the three-window PF >= 1.5 rule of RULES.md applies to the
   forward candidate, not to this try.
A counterparty must be named for any step 4 (section 3 above).

## 5. Windows and data

Discovery: closes from 2026-08-24 00:00 UTC to 2026-09-21 00:00 UTC (656 closes). Validation: to 2026-10-18 00:00 UTC (631
closes). Frozen holdout: to 2026-10-30 00:00 UTC (257 closes). (The staging constants are `newh9.stage`: START Aug 6 is
overridden to Aug 24 here by a floor in `ladlong1.build`, because the ladder files have no earlier close.)
**Counted before this registration, from prices and close times only, no result printed (`python -m scalper.ladlong1 counts`):**
events with a trade per band, discovery / validation / holdout: UPfar 603 / 593 / 248, UPnear 550 / 526 / 213, DNnear 538 / 511 /
222, DNfar 611 / 595 / 248, so every band clears 300 and 150 and nothing is NOT_RUNNABLE on count. Funnel losses are mostly "no
look" (a bid of 0 at the look: 124 and 128 strikes of about 1,200 in discovery, UPfar and DNfar). (The code loads the settled
result into each candidate row, as every ladder loader here does, but the `counts` mode prints and uses none.)
**Gold and Ethereum ladders: NOT_RUNNABLE, not tested, 0 tries.** KXGOLDH candles exist only from 900 seconds before the close
(`newh2_goldh.sqlite`), so no 45 minute look exists, and are mostly zero volume (NEWH4, NEWH14). KXETHD candles in `ladders.sqlite`
(Sep 29 to Oct 13, 328 closes, latest start 420 s before the close) neither reach the 45 minute look nor reach 300 events in
discovery. KXGOLDD and KXGOLDW have 39 and fewer closes in all history (NEWH14 GOLD2 count).

## 6. Tries and count

Four tries (UPfar, UPnear, DNnear, DNfar; one look). Information, not tries, printed with the result: UP and DN wings pooled by
side. Running count before this round **about 728,673**; N after registering **728,677**; deflated one-sided z bar
inv_cdf(1 - 0.05 / 728,677) = **5.27**. Run `python -m scalper.ladlong1 dv` once. Nothing changes after the score; no re-run.

## 7. Overlap with live L1 and OICORE

The hourly KXBTCD strikes are a different ticker from KXBTC15M, but they are the **same underlying (Bitcoin) and the same close**:
a position entered 44 minutes before the top of an hour and held to settlement is open while the live Bitcoin 15 minute windows
inside that hour trade (L1's Bitcoin entries at 10 or 6 minutes before each quarter-hour close, and OICORE exposure on Bitcoin in
the same hour), including the window closing at exactly that top of the hour. So **a LADLONG1 position CAN coexist with live L1 or
OICORE exposure on Bitcoin at the same close**, and a sharp same-direction Bitcoin move would hit both at once (the UP wing loses
on a spike through the strike, the DN wing on a drop; L1's bought favourite can sit on either side). Any candidate is **paper only**
here: nothing live is touched, and the second-slot library (`kalshiSlotLib.js`, inert) would need a separate reviewed phase, its
same-side rule, shared window cap and loss stop before anything sat beside L1.
