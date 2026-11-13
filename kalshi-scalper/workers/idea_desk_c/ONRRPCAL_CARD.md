# ONRRPCAL: Kalshi's daily overnight reverse repo market against the scheduled Treasury and month-end calendar (Idea Desk C, Nov 13, 2026)

**Written before any KXONRRP price, list, quote or result was read, and before any NY Fed or Treasury value was read.** Only the series metadata of KXONRRP was seen, from the census listing already on `kalshi-pull-data`: title "Overnight Reverse Repo", frequency daily, category World, exchange shard 0, quadratic fee, sources NY Fed and FRED series RRPONTTLD.
- No KXONRRP market settled on Nov 10 in that listing, so **the series may be dormant**. The zero-try count below decides that before anything else.
- This is a card for the Head of R&D's read, not registered. It counts toward the floor only after the Verification Analyst scores it. [research]

`ONRRPCAL | family: official money-market calendar (scheduled Treasury bill settlements and month-end) against a market that anchors on yesterday's print; entry on the morning of the operation, hold to settlement (hours) | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 1%`

## Mechanism, and the other side

- **What is measured.** The NY Fed's overnight reverse repo (ON RRP) facility takes cash from money funds and GSEs each afternoon (results about 13:15 ET). Its daily total moves on a known calendar:
  - **month-end and quarter-end:** banks shrink balance sheets, so cash is pushed into the facility;
  - **the business day after:** the cash comes back out;
  - **Treasury bill settlement days:** money funds take the new bills and pull cash out of the facility, roughly in proportion to net bill supply settling that day.
- **What is known that morning.** Both are known days ahead:
  - the month-end dates are fixed;
  - the bill settlement amounts are in Treasury's own auction results, published days before settlement.
- **The other side.** Traders on a low-volume "World" market who price today from yesterday's figure, the usual anchor in every official-series test here.
- **Honest counter:**
  - Every official-series test so far found the market mid a better forecast than the free outside series (GOVSER1: GAS1, GAS2, MORTGAGE1, ECONNEW1, NOWCAST1, FEDIMPL1).
  - Anyone pricing a repo market seriously knows this calendar.
  - ON RRP balances have been small since 2025, so most days may sit in one bottom bracket. Then only the month-end days carry a gap: about 24 a year, a slow family.

## Sources and terms (named, before any read)

- **NY Fed Markets API** (`markets.newyorkfed.org`, the ON RRP operation results). It is already read keyless by the daily recorder for SOFR (the `daily/ref` rows, approved Nov 6, 2026). It is the settlement source. Its terms of use must be re-read for this endpoint before any automated read; this card does not assume them.
- **US Treasury Fiscal Data API** (`api.fiscaldata.treasury.gov`, the auctions query for issue dates and amounts) and TreasuryDirect auction results. US government works, public domain, no key.
- **FRED RRPONTTLD** is named by Kalshi as a source. FRED's terms bar some redistribution of third-party series, but this one is the NY Fed's own; read only if the NY Fed endpoint is unusable.

## The rule (proposed, frozen at registration, never before)

- **Day type for business day T, from the calendar alone:**
  - ME, the last business day of a month (QE if a quarter end);
  - ME+1, the first business day after;
  - BILL, net bill settlement on T of at least $50 billion, from Treasury's auction results published before T;
  - otherwise PLAIN.
- **Model, from NY Fed history only, before any Kalshi price is read.**
  - For each day type, the empirical distribution of the ratio (ON RRP total on T) / (total on T-1), on business days 2024-01-02 to 2026-07-31 (a fixed span with no Kalshi data in it).
  - The probability that T's total is at or above strike K (or in bracket [a, b]) is the share of those historical ratios that, times the T-1 total, land there.
- **Decision.** At 09:00 ET on T (before the 12:45 ET operation), with the T-1 total published the afternoon before:
  - buy the side whose ask is at least 12c under the model probability;
  - ask 20c to 80c, spread 4c or less, ask plus 1c, 1 contract;
  - at most one market per event (the largest gap), hold to settlement.
  - **PLAIN days are never bet.** The rule bets only where the calendar says the day is different.
- **No parameter is fitted on Kalshi data.** The 12c gap, the 20c to 80c band, the 4c spread, the $50 billion line and the 09:00 ET look are fixed here.

## Numeric prediction, kill lines, windows

- **Zero-try count first (the kill that comes before any price):** closed if KXONRRP has fewer than 60 settled events with any two-sided quote at 09:00 ET on a non-PLAIN day across its whole history. Most likely outcome, about 70%: dormant or too thin.
- **Prediction if it runs:** about 40 to 70 calendar-day bets a year. Development cash PF 0.8 to 1.2; the market prices month-ends.
- **Development kill:** fewer than 60 bets, cash PF under 1.0, or a half under 1.2. If development has 30 to 59 bets it is a slow-family paper screen candidate only (`docs/POLITICS_RULES.md` section 8): "no evidence at n = x" below 30.
- **Bar:** cash PF 1.5 in each of three windows after fees, z 5.46, one try.
- **Windows (date constants, by T):**
  - development = T from the series' first event to before 2026-09-01;
  - **held-out = T from 2026-09-01T00:00:00Z to before 2026-12-01T00:00:00Z**, read once on the Head's go.
  - If the zero-try count shows fewer than 20 development events, the Head re-rules the cut before any price is read.
- **Held-out line for HELDOUT_REGISTRY.md:** `| ONRRPCAL | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/ONRRPCAL_CARD.md | KXONRRP | Development = T from first event to before 2026-09-01; held-out = T 2026-09-01 to before 2026-12-01, read once on the Head's go | 2026-09-01; 2026-12-01 | NOT READ | card text | card only, not registered; zero-try event count first |`

## Uniqueness checks (lifecycle 7d), self-scored, and the declined list (7e)

1. **Signal: a different source and field.**
   - Treasury's scheduled bill settlements and the month-end calendar, against the facility's own history.
   - Closest are SOFR1 (KXSOFRD, a forward cheap-tail rule on last print plus calendar) and GOVSER1 (cheap side against persistence on agency series).
   - This differs in market (ON RRP volume, not a rate), information (named settlement amounts, not persistence), side (mid band 20c to 80c, not the cheap tail) and days (calendar days only).
   - A reviewer could call it a SOFR1 cousin; the Verification Analyst decides.
   - Self-score: unique, medium confidence.
2. **Entry and exit:** a morning look and a hold of a few hours, in a market no live or shadow rule trades.
3. **Correlation:** no shared market with gold L1, OICORE or EVENT830; KXONRRP is on shard 0.
4. **Declined list:**
   - not weather, not sports, not favourite-late;
   - the 20c to 80c band excludes favourite-and-hold, and there is no cheap side;
   - no lock, parity, taker flow or market making.
   - "Official-series against persistence" is not on the list; its tests are NOT_ENOUGH_DATA or FALSIFIED singly, not a closed family.

## Fields for a zero-try probe (none read yet)

1. **KXONRRP events:** count by status, first and last event dates, and markets per event (strike type: above or brackets, step size).
2. **Timing:** the close time against the 13:15 ET results, and whether trading is open at 09:00 ET on T.
3. **Settlement figure:** the rules text, "total accepted" or another figure, and the revision rule.
4. **Candles:** 1 minute or hourly candles for the market at 09:00 ET on calendar days, and whether any quote is two-sided.
5. **Outside sources, NOT Kalshi:** the NY Fed and Fiscal Data terms pages, read by Main before any automated read.
