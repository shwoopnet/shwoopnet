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

## Numeric prediction, kill lines, windows

- **Prediction:** gaps of 0.5F or more with a strike between the two numbers occur in about 5% to 15% of city-hours, and the development cash PF of the bets is 0.9 to 1.2. The market mostly prices the index.
- **Kill (development read):** closed if fewer than 200 bets, or a cash PF under 1.0, or a PF under 1.2 in either half.
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
