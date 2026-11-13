# TEMPBLEND: the gap between Kalshi's 5-station index and the one station traders watch (Idea Desk C, Nov 13, 2026)

**Written before any index value, station reading, price, list or result was read.** A card for the Head of R&D's read, not registered. It replaces the forecast half of TEMPINDEX: on Nov 13 at 14:51Z the Head ruled that TEMPINDEX as written is in the closed weather family, because projecting a trend with a fitted sigma is a nowcast. This card keeps only the other half of the mechanism: no projection and no fitted sigma. The feed is allowed by the owner as a recorded terms risk. Nothing is read until the Chief of Staff's record is on main and the zero-try probe has run. [research]

`TEMPBLEND | family: settlement-source composition (a 5-station blended index against one station's reading at the same minute); entry 15 minutes before the hour, hold to settlement | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 2%`

## Mechanism, and the other side

- **What settles:** an hourly "at" contract settles on Kalshi's Weather Index. That is a weighted blend of five ASOS stations, each with a weekly offset, one canonical point a minute, published 300 seconds late (CFTC filings MIAWINDEX, Aug 12, and CHIMETROWINDEX, Sep 9, 2026).
- **What traders watch:** most of them see one station, the city's familiar airport or park reading in an app or on weather.com.
- **The gap:** when the blend and that one station disagree by half a degree or more, any strike between the two numbers is priced from the wrong one.
- **Other side:** traders anchored on the single station.
- **Honest counter:**
  - Kalshi's makers can read the index endpoint and very likely do, so the gap may already be priced;
  - the index can still move in the 15 minutes before the hour, and the card makes no attempt to predict that move (that would be a forecast).

## Which station is "the one traders watch" (fixed now, before any data)

For each city, the station named by Kalshi's DAILY high temperature market for that city (the NWS climate station; for example Central Park for New York). It is the reading the most-traded weather contracts point traders at.
- **Source A, preferred (no new source):** the same station's `temp_f` in the index's own `stations[]` (`detailed=true`), if that station is one of the five. Already allowed under the owner's exception.
- **Source B, only if it is not one of the five:** NWS observations at api.weather.gov for that station. US government work, public domain, no key, already read by the wxens recorder and on the signal logger's host list. Its ASOS report is hourly or 5 minute, so "the same minute" becomes "the latest report at or before t", which is coarser.
- If neither source gives a reading within 10 minutes of t, the city-hour is skipped.

## The rule (proposed, frozen at registration, never before)

- **Decision:** the 1 minute candle ending 15 minutes before the settlement minute S.
  - Read the latest canonical index point (v at minute t, about S minus 20 minutes given the 300 second lag) and the station reading s at the same minute t (or the latest at or before t, Source B).
  - Gap: g = v minus s.
- **If |g| is under 0.5F,** no bet.
- **Otherwise:**
  - **g of +0.5F or more:** for a strike K with s < K <= v, buy YES on "K or above".
  - **g of -0.5F or less:** for a strike K with v < K <= s, buy NO on "K or above".
  - Only the strike nearest the midpoint (v + s) / 2, with its ask (for the side bought) at 20c to 80c and a spread of 4c or less. At most one strike per city-hour, ask plus 1c, 1 contract, hold to settlement.
- **No fitted parameter.** The only numbers are the 0.5F gap, the 20c to 80c band, the 4c spread and the 15 minute look, all fixed here.

## When the watched station is one of the five (answered Nov 13, before any data, at the Head's question)

**Rule written now: such cities are KEPT, under the same rule.** The reasons:

- **What the trader acts on is unchanged.** The trader sees s and the contract pays on v, so the mispricing the card claims is v minus s whatever the index is made of.
- **Membership only shrinks the gap; it does not cancel it.** With five equal weights of 0.2:
  - g = v minus s = 0.8 x (the mean of the other four stations, offset-adjusted, minus s) + 0.2 x (the station's own offset);
  - so the gap is 80% of the difference between the other four stations and the watched one, plus a fifth of its offset.
- **Fewer bets, same threshold.** A city where it is a member will clear the fixed 0.5F threshold less often. That is accepted, and the threshold is not changed for it.
- **The offset part is a constant within a calibration week.** If the gap in a city is mostly that constant, makers can learn it within days, which is the honest counter for those cities.

Two additions, fixed now:

1. **Skip rule.** When the watched station is a member and its own `code` at minute t is anything but `ok`, the city-hour is skipped. In that case the blend is running without it, or on a late value.
2. **Report rule.** The development read reports member cities and non-member cities as two descriptive rows, with the PF and n of each. This is NOT a second try: the verdict is the pooled rule, and no city is dropped after any data is seen.

## Numeric prediction, kill lines, windows

- **Prediction:** gaps of 0.5F or more with a strike between the two numbers occur in about 5% to 15% of city-hours, and the development cash PF of the bets is 0.9 to 1.2. The market mostly prices the index.
- **Kill (development read):** closed if fewer than 200 bets, or a cash PF under 1.0, or a PF under 1.2 in either half.
- **Kill (the makers-learn-the-offset counter, Head of R&D, Nov 13):** in the held-out read, split the bets by time since the latest calibration change (the `effective_at_ms` of the city's `config_version`): days 0 to 1, against day 2 onward. If the day 2 onward bets have a cash PF under 1.0, it is a FAIL, not noise, whatever the pooled PF. The kill test counts only with at least 30 day 2 onward bets in the held-out. Below 30, the result is "no evidence at n = x" and TEMPBLEND cannot pass. The same split is reported, for information only, in the development read.
- **Bar:** cash PF 1.5 in each of three windows after fees, z 5.46, one try.
- **Windows (date constants, per the Head's ruling (b) of Nov 13):**
  - development = settlement times 2026-09-13T00:00:00Z to before 2026-11-05T00:00:00Z, halves split at 2026-10-09T00:00:00Z;
  - Nov 5 to Nov 11 are used by neither held-out (HOURLYTEMP reads prices on those days);
  - **held-out = settlement times 2026-11-12T00:00:00Z to before 2026-12-10T00:00:00Z**, read once on or after 2026-12-10 on the Head's go.
- **Held-out line for HELDOUT_REGISTRY.md:** `| TEMPBLEND | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/TEMPBLEND_CARD.md | hourly temperature series that settle on the Kalshi Weather Index (KXTEMP*H family, per the probe) | Development = S 2026-09-13 to before 2026-11-05; held-out = S 2026-11-12 to before 2026-12-10, read once on or after 2026-12-10 on the Head's go; Nov 5 to 11 unused | 2026-09-13; 2026-11-05; 2026-11-12; 2026-12-10 | NOT READ | card text | card only, not registered |`

## Uniqueness checks (lifecycle 7d) and the declined list (7e)

1. **Signal: a different field.** The settlement index's blend against one constituent or nearby station. It is not a price rule, not a forecast and not an ensemble.
   - Closest: HOURLYTEMP (prices only);
   - WXNEW1 and TEMPINDEX as written (nowcast, closed);
   - WXDAYEND (daily, near-certain strikes from a reading).
   None uses the blend-against-station gap.
2. **Entry and exit:** a 15 minute look and hold, on hourly markets no live or shadow rule trades.
3. **Correlation:** no market shared with gold L1, OICORE or EVENT830.
4. **Declined list.**
   - Weather forecast against market: not a forecast, nothing is projected.
   - Favourite-and-hold: the 20c to 80c band excludes it.
   - No lock, parity, taker flow or market making.

The independent uniqueness score is for the Verification Analyst.

## Delta to Desk B's temperature probe A (zero try, fields only)

1. For each hourly series: the settlement source in the rules (Kalshi Weather Index or The Weather Company), the index city key, and S.
2. With `detailed=true`, for each city: the five `stations[].station_id` values, and whether the daily high market's climate station is among them. Also each station's `source`, `code`, `temp_f`, `obs_time_ms` and `received_at_ms`.
3. How far back `/live_data/weather/{city}` serves `detailed=true` points (development needs 2026-09-13).
4. `/calibrations`: whether earlier `config_version` rows with `effective_at_ms` are served.
5. Only if the climate station is not one of the five: whether api.weather.gov serves that station's observations back to 2026-09-13 (it usually keeps about a week, which would make Source B forward only).

## Amendment 1 (Nov 13, 2026, before any data): readings A1 to A18

The History Miner built a second scorer from this card alone (claude/history-miner, 9c112b9f, `history_miner/tempblend2/`) and listed 18 ambiguities. The Head of R&D ruled A5, A6, A7, A10 and A12 and accepted the readings below for the rest, on Nov 13, 2026. Where this amendment and the text above differ, this amendment is right.

- **A1, the index point:** v is the latest canonical point with t at or before the decision time (S minus 15 minutes) minus 300 s, so the last point published by the decision; normally t = S minus 20 minutes.
- **A2, quotes:** strike quotes are the close of the 1 minute candle ending at S minus 900 s. A strike with no bid or no ask in that candle is not eligible.
- **A3, the station reading:** Source A is the watched station's `temp_f` in the `stations[]` of point t itself. Source B is the latest report with obs_time at or before t. Either is used only if t minus obs_time is 600 s or less (inclusive); otherwise skip.
- **A4, the gap:** bet when |g| is 0.5F or more, with a 1e-9 tolerance.
- **A5, comparison (Head's ruling):** v and s are compared as raw published decimals, with no rounding to whole degrees, in the gap and in the strike conditions. Whether the index is rounded at settlement is a KNOWN GAP in this card. It is not resolved from data.
- **A6, order of filters (Head's ruling):** among the strikes between s and v, keep those whose ask is 20c to 80c and whose spread is 4c or less FIRST. Then take the strike nearest (v + s) / 2.
- **A7, ties (Head's ruling):** two strikes equally near the midpoint (within 1e-9): the lower K.
- **A8, quotes per side:** YES ask = yes_ask; NO ask = 1 minus yes_bid; spread = yes_ask minus yes_bid for both sides. A quote is usable only if 0 < yes_bid < yes_ask < 1.
- **A9, band and spread:** on the ask seen, inclusive at both ends, with a 1e-9 tolerance. There is no slip.
- **A10, fill and fee (Head's ruling):** the fill is at the ask seen, with NO +1c. The fee per contract is 0.07 x p x (1 - p) at that ask, rounded up to the cent. A win pays 1 minus ask minus fee; a loss costs ask plus fee. (The "ask plus 1c" in the rule above is the order's limit, not the booked price.)
- **A11, PF:** gross gain over gross loss, in dollars per contract after the fee; "inf" when there is no loss; n is printed with every PF.
- **A12, void (Head's ruling):** the standing one-void rule. The price is refunded, the fee is kept, it counts as a fee-only loss, and it is counted as a bet.
- **A13, windows:** by S. Development is [2026-09-13, 2026-11-05) with the halves split at 2026-10-09; held-out is [2026-11-12, 2026-12-10). Any other S is ignored and counted.
- **A14, development kill:** a half with no bet fails the 1.2 line; a half with no loss passes it.
- **A15, the calibration split:** measured at the decision time (S minus 15 minutes). Under 2 x 86400 s since the latest `effective_at_ms` is days 0 to 1. A calibration change after the decision but before S is ignored.
- **A16, member skip:** for a member station, a code other than "ok" skips, and so does a missing code. Rows from Source B carry no code and are never skipped on it.
- **A17, no index point:** no canonical point within 10 minutes before the decision time means a skip, counted as "no index point". The index `status` field is NOT filtered (a degraded point still settles contracts).
- **A18, membership:** decided per row, from the `stations[]` of point t at the decision, so it can change with a calibration. The member and non-member rows are descriptive only; the verdict is pooled.
