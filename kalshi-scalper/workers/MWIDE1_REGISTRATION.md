# MWIDE1 registration: passive bids on wide-spread daily, weekly and monthly markets (Strategy Research V2, research only)

Written 2026-11-05 BEFORE any trade tape was fetched and before any outcome (`res` table, win or loss) of any MWIDE1 market was read. Code `src/scalper/mwide1.py`.
Nothing here means trade, touches `functions/`, L1 or OICORE, or has a promote verb. Maker design, justified below; N +1.

## Duplicate check (done first)
README and workers grepped for maker, resting, passive, daily, weekly, monthly. MAKER1 to MAKER5, L1Q1, MM1, MM1S, QUOTE2B, MAKERTAIL1, MAKERMID1 are 15 minute or
hourly-Bitcoin/gold. H5 and P2 are 15 minute crypto. QSTALE1, SS2 (wide spread fade) and NEWLIST1 are TAKER rules. No resting-bid test exists on daily, weekly or
monthly series (weather, economics, commodities, financials, entertainment, science).

## What was read before this registration (disclosure)
Quotes only: NEWLIST1's hourly candle table (`data/newlist1.sqlite`, tables `mk`, `cd`: bid, ask close, volume), to count how many orders the rule would create
(759) and to fix the date split (median close). The `res` table and every tape were NOT read. NEWLIST1 (FALSIFIED) scored cheap-side TAKERS on a hash sample drawn
from the same markets at 1, 3 and 6 hour looks, so these markets' taker outcomes were seen by that worker; no maker fill or maker outcome was. Stated, not hidden.

## Counterparty and mechanism
A wide spread on a thin daily market means the resting bid is the only price on that side. A taker who sells into it (or buys the other side at its ask) is
either a hedger, a stale-view trader, or someone informed. The maker earns the spread when the taker is uninformed (counterparty: the impatient, uninformed
seller) and loses it when the taker knows the cheap side just got cheaper (adverse selection: the fill arrives exactly when the cheap side is losing).
Structural claim: on a wide book the bid sits several cents under fair, so a fill at the bid has a positive cushion that a taker never has.
Prior that the pessimistic-fill net is positive after fee and passes: 3%. The pooled cheap-side TAKER baseline is about -5.5c to -6c per contract; the maker
must clear that by at least 6c to matter, and MAKERMID1 (hourly Bitcoin, bids 16c to 40c) already measured -3.8c per resting order.

## Universe (fixed from metadata and quotes, before any outcome)
Every market in `data/newlist1.sqlite` table `cd` (hourly candles already on disk for the NEWLIST1 hash samples of daily, weekly and monthly series in
Economics, Financials, Commodities, Climate and Weather, Crypto (non 15 minute), Entertainment, Science) with: close before **2026-10-03T16:00Z** (the frozen
third: nothing at or after it is fetched or scored), life (close minus open) at least 12 hours, category not Sports. 15 minute series, gold and the hourly
crypto ladders are not in the table. Census: **759 triggered markets, 98 series, 541 YES-side and 218 NO-side orders.** Halves: **D1 = close before
2026-09-19T06:00Z (the median close of the 759), D2 = from then to the cut.** Cluster key: UTC close date.

## The rule (one claim)
For each market, the FIRST hourly candle (end at least open + 2 h and at most close - 2 h) that is priced (bid >= 0.01, ask <= 0.99, ask > bid) with spread
ask - bid >= 0.04 and a CHEAP side whose own best bid is 0.03 to 0.30 (YES side: yes bid; NO side: 1 - yes ask; if both qualify, the lower) triggers one
resting buy of that side at that bid, 1 contract per order (fee evaluated as one order of C = 10), posted at the candle end, back of the queue, never re-priced,
cancelled at the close, held to settlement if filled. Cheap side only: no bid above 0.30, no favourite.
**Fill model (pessimistic, the verdict): filled only if the public trade tape shows, after the post time and before the close, a print STRICTLY BELOW our bid
price by a taker selling into our side** (YES bid: `taker_side` no with yes price below the bid; NO bid: `taker_side` yes with no price below the bid). A print
below our price proves the whole level at our price was consumed whatever the queue, so no queue size is needed. Fill at our bid. Tape not paged back to the post
time (page cap 12 x 1,000 trades) counts as NOT filled and is reported as truncated. **Optimistic readout (information only):** any opposing-side taker print at
or below our bid. Net per filled contract = win - bid - fee. Fee verdict: the taker formula 7% x C x p x (1-p) rounded up per order, C = 10 (a maker rate for
these series is unknown and not assumed); maker fee 0 and fees x1.2 are readouts.
**Readouts, not claims:** fill rate; net per posted order (unfilled = 0); win rate vs price paid on fills; what UNFILLED orders would have earned bought at the
bid (the selection effect, the MAKER2/MAKER3 trap); the cheap-side taker at the ask of the same trigger candle (when ask <= 0.30) as the control; YES vs NO; family
table (picked from many cells, flag only).
Result: `res` table, else the public market object. Unsettled at scoring is excluded and counted.

## Bar and kill rules (decided now)
Day-clustered z (`calibration.cluster_mean_z`) at the running count N = 730,441, deflated z bar **about 5.27**.
1. Pessimistic fills under 150 pooled or under 50 in D1 or D2: **NOT_ENOUGH_DATA**.
2. **FALSIFIED** if profit factor under 1.5 in D1 or in D2, or mean net per fill not positive in both, or net per fill not at least 6c above the taker control's
   mean, or pooled z under 5.27, or PF under 1.0 at fees x1.2.
3. Otherwise **LEAD** only as a flag: the frozen third is read by the coordinator, never by this worker; never "validated".
**Numeric prediction:** pessimistic fill rate 35% (range 20% to 55%, about 265 fills); win rate 2 to 5 points below the price paid; net per fill -3c to -6c, PF
0.3 to 0.8; unfilled orders would have earned MORE than the filled ones; verdict FALSIFIED 52%, NOT_ENOUGH_DATA 45%, LEAD 3%. Run once; no parameter,
band, look, fee or split changes after the first outcome. If the sample is too thin the result says what accrual is needed.

## Forward data note
RECDAILY (`daily/quotes`) holds 7 polls over 2026-11-04 to 11-05, 30 minute to 6 hour gaps, bid/ask/last/volume only, no sizes and no tape: it proves no fill
and cannot test this rule. `sportspre` has bid and ask sizes but is game markets. `book` is hourly Bitcoin (MAKERTAIL1/MAKERMID1). So the forward accrual that
would test the same rule is the public tape for the markets RECDAILY already lists, fetched after their close (this worker's `fetch` can be re-run on closes
after 2026-11-05 as a registered forward read; not scored here).
