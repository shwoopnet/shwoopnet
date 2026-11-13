# GASCYCLE: the Midwest gasoline price cycle in Kalshi's daily state gas markets (Idea Desk C, Nov 13, 2026)

**Written before any state gas price, quote, candle or result was read.** Only series metadata from the census listing on `kalshi-pull-data` was seen: KXAAAGASDOH (Ohio) and KXAAAGASCDIN (Indiana) are daily, and settle on AAA's state average. Ohio settled 27 markets on Nov 10 with about a thousand contracts in total, so it is thin. This is a card for the Head of R&D's read, not registered. It counts toward the floor only after the Verification Analyst scores it. [research]

`GASCYCLE | family: retail price-cycle phase (Edgeworth restorations) in a state average, against a market that prices the state like the national series; look the evening before, hold to settlement (about a day) | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 2%`

## The published mechanism (read by a worker on Nov 13; papers, no data)

- **Cycling is concentrated in the contiguous upper Midwest:** Indiana, Ohio, Michigan, Illinois and Wisconsin. The FTC's working paper 303 (Zimmerman, Yun and Taylor) covered 355 US cities, 2001 to 2007.
- **The cycle has a recognisable shape.** Retail prices fall slowly for about 1 to 2 weeks as stations undercut each other. Then a "restoration" lifts them by often 10c a gallon or more within 1 to 2 days, and the fall starts again (Lewis and Noel; Noel 2010; Doyle, Muehlegger and Samphantharak, NBER w14162). Restorations come when margins are squeezed, so their timing is partly readable from how far and how long prices have fallen since the last jump.
- **Events:** about 25 to 50 restorations a year in a cycling state.
- **Why a state market could differ:** the national series GAS1, GAS2 and ECONNEW2 tested averages over all states, where cycles in five states are diluted. A state market in a cycling state carries the cycle almost undiluted, but only partly: rural stations in the same state do not cycle.
- **Honest counter:**
  - The jump is visible to anyone watching the same stations, and the market may already price the cycle phase.
  - No paper measures whether these states still cycle after 2020.
  - The exact day of a restoration is not fixed.
  - Tax changes are no help: they are 1c to 3c and public months ahead, too small for a bracket.

## The other side

Traders on a thin state market who price tomorrow's average from today's (persistence) or from the national trend, and who do not track where the state is in its cycle.

## Data source (no new outside source)

The rule reads only the **state average path itself, from Kalshi's own settled markets** (each event's settled value, `expiration_value`), plus Kalshi candles for prices. No outside read is needed:
- AAA's site is not read; its terms are unread;
- no rack (wholesale) price is used, because no terms-permitted source has been checked.

## The rule (proposed, frozen at registration, never before)

- **From the settled path up to and including day D-1:**
  - a restoration is a day-over-day rise of 5c or more in the state average;
  - n is the number of days since the last restoration;
  - F is the fall in cents from the price just after the last restoration to day D-1.
- **Trigger for day D:** n of 6 or more AND F of 8c or more. The numbers come from the published cycle length (1 to 2 weeks) and restoration size (10c or more), fixed now, never fitted.
- **Bet.** At 20:00 US Eastern on day D-1:
  - for the day-D market, buy YES on the lowest strike (or the bracket) whose value is at least the D-1 average plus 4c;
  - ask 20c to 80c, spread 4c or less (YES ask = yes_ask; NO ask = 1 minus yes_bid, as in TEMPBLEND A8), fill at the ask seen plus the rounded fee;
  - 1 contract per state-day, hold to settlement.
- **No bet** when the trigger is off: the rule bets only on predicted restoration days.
- **Voids** are a fee-only loss, counted as a bet.

## Numeric prediction, kill lines, windows

- **Zero-try count first, before any price:** from the settled values only, the number of trigger days and of restorations in development, per state. Closed if there are fewer than 40 trigger days across Ohio and Indiana, or fewer than 10 restorations a quarter in either state (cycling gone).
- **Prediction:** triggered days are followed by a restoration 30% to 50% of the time. The market already prices much of it. Development cash PF 0.8 to 1.2.
- **Development kill:** fewer than 60 bets, cash PF under 1.0, or a PF under 1.2 in either half. With 30 to 59 bets it is a slow-family paper screen at most.
- **Bar:** cash PF 1.5 in each of three windows after fees, z 5.46, one try.
- **Windows (by settlement date D, date constants):**
  - development = from the first event of each series to before 2026-10-15, halves split at the middle date, fixed by the zero-try count before any price;
  - **held-out = D from 2026-10-15 to before 2026-12-15**, read once on the Head's go.
  - If the series started after 2026-08-15 (under 60 development days), the Head re-rules the cut before any price is read.
- **Held-out line for HELDOUT_REGISTRY.md:** `| GASCYCLE | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/GASCYCLE_CARD.md | KXAAAGASDOH, KXAAAGASCDIN (cycling states only) | Development = D before 2026-10-15; held-out = D 2026-10-15 to before 2026-12-15, read once on the Head's go | 2026-10-15; 2026-12-15 | NOT READ | card text | card only, not registered; zero-try count of trigger days and restorations first |`

## Uniqueness checks (lifecycle 7d), self-scored, and the declined list (7e)

1. **Signal: a different field and logic.**
   - The cycle phase (days and cents since the last restoration) of a state average, in states with a documented retail cycle.
   - GAS1, GAS2 and ECONNEW2 used national (and some state) gas prices against persistence and wholesale futures, buying the cheap side. NEWLIST1 read new listings.
   - None used a cycle-phase signal or a mid-band YES on a predicted jump day.
   - It is in the GAS family by market, but a different signal. The Verification Analyst decides whether that counts as unique.
   - Self-score: unique by signal, low to medium confidence.
2. **Entry and exit:** an evening look and a one-day hold, on markets no live or shadow rule trades.
3. **Correlation:** no shared market with gold L1, OICORE or EVENT830.
4. **Declined list.**
   - Not weather, sports, favourite-late or an official-release calendar: the timing is set by retailers' margins, not by a published schedule.
   - The 20c to 80c band excludes favourite-and-hold and the cheap side.
   - No lock, parity, taker flow or market making.
   - GAS1 and GAS2 are FALSIFIED and NOT_ENOUGH_DATA singly; the gas family is not on the declined list.

## Fields for a zero-try probe (none read yet)

1. **Both series:** first and last event date, events by status, and the strike layout (above-strikes or brackets, step size).
2. **The settled value field** (`expiration_value`) per event, as the state average path, and the AAA timing the rules name: which day's average settles day D, and at what time.
3. **Close time of the day-D market**, and whether it is open at 20:00 ET on D-1.
4. **Candles** at 20:00 ET on D-1, and whether quotes are two-sided.
5. **Other cycling states:** whether Kalshi lists Michigan, Illinois or Wisconsin daily markets (the census listed only Ohio and Indiana).

## Amendment 1 (Nov 13, 2026, before any data): uniqueness score and held-out position

- **Uniqueness:** the Verification Analyst scored GASCYCLE UNIQUE, with low to medium confidence.
- **Closest overlap in market terms:** GAS1-F, V2's forward test of the favourite on the KXAAAGASD* series. GAS1-F buys the favourite on the state and national daily gas markets. GASCYCLE buys mid-band YES only on predicted restoration days in two cycling states, from the cycle phase. They can share a market and a day; the two rules are scored apart and never pooled.
- **Held-out position (to be settled before the zero-try count):**
  - USWEEP1 (frozen at 79724f00) holds state gas windows;
  - W-CAT-ECON1 holds state gas windows (closed unread; its release has been asked of Refinement);
  - GAS1-F's windows are being checked.
  - Under rule (h), GASCYCLE's development and held-out dates may need to move to avoid those windows. Its constants (development D before 2026-10-15; held-out D 2026-10-15 to before 2026-12-15) stand only if the Head confirms no overlap. Otherwise the Head re-rules them before any read.
- **Stage 0** until those are settled and the zero-try count runs. No probe job yet.
