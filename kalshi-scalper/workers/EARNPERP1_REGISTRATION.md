# EARNPERP1 registration: does the perp price shortly after the earnings filing already equal the cash opening gap? (written 2026-11-06 about 23:00 UTC, before any earnings outcome; shared rules `EARNPERP_COMMON.md`)

## Mechanism and counterparty
After the 8-K Item 2.02 filing the perp is the only tradable price until 09:30 ET. Holders who cannot trade the cash stock sell or buy the perp at a wide, thin overnight book. Two readings: (H0, the one I expect) the perp is a good forecast of the opening gap by L = 15 minutes after the filing, so continuing in its direction pays only the cost; (H1, the lead) the first 15 minutes under-react (thin book, slow information, size) and the move continues into the open, a drift paid by the late cash holder.

## Rule (fixed, no tuning)
Events, anchor A, look L, exit E, move m, cost screen: `EARNPERP_COMMON.md`. Trigger: |m| at least 150 bps. Trade: the perp IN the direction of m (m > 0 buy at the ask at L, sell at the bid at E; m < 0 the reverse), 1 contract, held L to E. Control: the reversed side (fade) on the same triggers. Information, never scored: the cash gap G = ln(open(next regular session) / close(prior regular session)) from Yahoo DAILY bars; beta = slope of G on m through the origin, the share of events with the same sign, and the mean of G - m (how much of the cash gap the perp had not yet shown at L).

## Numeric prediction
Events in development about 60, with all three candles and the spread screen about 60%, with |m| at least 150 bps about 65%: **about 25 trades (range 12 to 40) on about 20 dates**; mean gross continuation -10 bps (range -80 to +60), mean net about -45 bps (24 bps fee plus about 15 to 25 bps of crossing at L and E); beta 0.8 to 1.1; PF 0.1 to 0.7. P(NOT_ENOUGH_DATA at 2027-03-01) 45% (under 30 trades), P(FALSIFIED) 53%, P(LEAD) 2%.

## Kill, bars and cut
As the common file: NOT_ENOUGH_DATA under 30 trades or 20 dates (the date it would be met at the observed rate is reported; the April to May season gives about 25 more); FALSIFIED on PF under 1.5 in either half, net not above 0 in both halves, PF under 1.2 at fee x1.2, trigger not better than control, or clustered z under about 5.32. Development read date **2027-03-01**; held out releases 2027-03-01 to 2027-05-31, read once on or after 2027-06-01 only after a LEAD.
Scorable today: the only release since the stock perps began quoting is COP (11-05), which predates the perp's first candle; the expected count of events scorable on 2026-11-06 is zero, reported as such.

## Count
N +2 (continuation, control).
