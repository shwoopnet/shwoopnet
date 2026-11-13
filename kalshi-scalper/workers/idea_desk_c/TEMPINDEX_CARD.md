# TEMPINDEX: the hourly temperature market against Kalshi's own settling index (Idea Desk C, Nov 13, 2026)

**RULED IN THE CLOSED WEATHER FAMILY AS WRITTEN (Head of R&D, Nov 13, 14:51Z): the trend projection with a fitted sigma is a nowcast. Not counted, not registered. The non-forecast half is `TEMPBLEND_CARD.md`.**

**Written before any index value, price, list or result was read.** A card for the Head of R&D's read, not registered. The feed is allowed by the owner as a recorded terms risk (Head of R&D, 13:55Z Nov 13). Nothing is read until the Chief of Staff's record is on main and the zero-try probe has run. [research]

`TEMPINDEX | family: the settlement index itself (a five-station, offset-adjusted, one-minute mean) against a market whose traders see one station; entry 15 minutes before the hour, hold to settlement (15 minutes) | risk class: mid price (20c to 80c), 1 contract | stage Idea | prior about 3%`

## The facts it rests on (public documents, read by a worker on Nov 13; no API call)

- **The Kalshi Weather Index** (CFTC filings MIAWINDEX, Aug 12, 2026, https://www.cftc.gov/filings/ptc/ptc08122615995.pdf, and CHIMETROWINDEX, Sep 9, 2026, https://www.cftc.gov/filings/ptc/ptc09092624315.pdf):
  - "The Source Agency is Kalshi."
  - The index is "the minute-resolution temperature index ... rounded at final output to the nearest 0.01°F".
  - Chicago blends five ASOS stations at 0.2 weight each, from one-minute high-frequency ASOS through Synoptic Data, each with a station offset recalibrated weekly. It needs at least 4 stations reporting.
  - "exactly one canonical point for t is calculated and published" at t plus 300 seconds, never revised.
  - An "at" contract settles on "the canonical Index observation with the greatest event time t such that t is at or before the settlement time and no more than 60 minutes before".
- **Public endpoints** (docs.kalshi.com, `security: []`): `GET /live_data/weather/{city}` with `from`, `to`, `last_sec`, `detailed`. It returns `timeseries[]` of `t`, `v`, `status`, `contributors`, and with `detailed=true` each station's `temp_f`, `source`, `code` and timing. `GET /live_data/weather/{city}/calibrations` returns weights and `offset_c`.
- **The help center says something else:** hourly markets settle on "The Weather Company" at one station. **Which source settles each hourly series today is not known.** That is question 1 of the probe, and the card dies if a series does not settle on the index.
- **The family** (Desk B's HOURLYTEMP note, from the Nov 10 listing): four cities, one event per clock hour, about 10 strikes one degree apart, each market open 60 minutes before the hour. About 32,000 events a year.

## Mechanism, and the other side

- **The settling number is a blend of five stations with weekly offsets.** Traders mostly see one station: a weather app or weather.com's airport reading. When the stations disagree (a sea breeze, a front, a cold pocket at one airport), the blend sits away from the reading a trader sees by up to a degree or more. Strikes one degree apart are then mispriced near the money.
- **Second part:** the index is a minute series released 5 minutes late. Its last 30 minutes give its own trend, which a single-station hourly reading does not show.
- **Other side:** traders pricing from the one station or app reading they can see.
- **Honest counter:**
  - Kalshi's makers can read the same public endpoint, and very likely do;
  - the blend of five stations moves less than any one station, so most strikes are already near-certain 15 minutes out, and only the one or two strikes nearest the value are mid-priced.

## Uniqueness checks (lifecycle 7d) and the declined list (7e)

1. **Signal: a different data source.** The settlement index's own minute values and station blend. WX1, WX3, WXENS1 and WXLOW1 used NWS or ensemble FORECASTS against DAILY highs and lows. Desk B's HOURLYTEMP measurement uses only Kalshi prices, and its weather-service proxy was not approved.
2. **Entry and exit:** a 15 minute look and hold, on hourly markets no live or shadow rule trades.
3. **Correlation:** no shared market with gold L1, OICORE or EVENT830.
4. **Declined list.**
   - **"Weather forecast against market on daily temperature brackets"** names daily highs, lows and rain. This card is the settling index on HOURLY markets 15 minutes out: a reading and its own minute trend, not a forecast model. **The Head of R&D ruled on Nov 12 that a forecast-driven hourly rule is inside the closed family.** Whether a rule from the settlement index's own trend counts as "forecast-driven" is the Head's call before any registration. The blend-against-single-station part is not a forecast at all.
   - **Favourite-and-hold:** only asks of 20c to 80c are bought, so the near-certain strikes (the WXDAYEND shape) are excluded.
   - **No lock, parity, flow or market making.**

## The rule (proposed, frozen at registration, never before)

- **Decision:** the 1 minute candle ending 15 minutes before the settlement minute S.
  - Index state: the latest canonical point v (t at most S minus 20 minutes, given the 300 second lag) and the least-squares slope b of the canonical points over the 30 minutes before t.
  - Projection: p = v + b x (S minus t).
- **Model:** P(above strike K) = Phi((p minus K) / sigma).
  - Sigma is ONE number per city, fixed from development index history alone before any price is read: the standard deviation of (index at S minus p).
- **Entry:** buy the side whose ask is at least 12c under the model probability for that side. Ask 20c to 80c, spread 4c or less, ask plus 1c, 1 contract. At most one strike per city-hour (the largest gap). Hold to settlement.
- **Signals expected:** 4 cities x about 20 hours x the share of hours with a 12c gap. If 10% qualify, that is about 8 a day, about 250 a month.

## Numeric prediction, kill lines, windows

- **Prediction:** most city-hours show no 12c gap (the market tracks the index). The development cash PF of the bets taken is 0.9 to 1.2.
- **Kill (development read):** closed if fewer than 300 bets, or a cash PF under 1.0, or a PF under 1.2 in either half.
- **Bar:** cash PF 1.5 in each of three windows after fees, z 5.46, one try.
- **Windows (date constants):**
  - development = settlement times 2026-09-13T00:00:00Z to before 2026-10-25T00:00:00Z, split in halves at 2026-10-04T00:00:00Z;
  - **held-out = settlement times 2026-10-25T00:00:00Z to before 2026-11-13T00:00:00Z**, read once on the Head's go.
  - The held-out must not overlap W-CAT-CAL1's released weather window or HOURLYTEMP's measurement days (Nov 5 to 11). **Those days sit inside this held-out, so the Head must rule which governs before registration.**
- **Held-out line for HELDOUT_REGISTRY.md:** `| TEMPINDEX | Idea Desk C | idea-desk-c:kalshi-scalper/workers/idea_desk_c/TEMPINDEX_CARD.md | KXTEMPNYCHS, KXTEMPMIAH, KXTEMPLAXHS, KXTEMPCHIHS (only series that settle on the Kalshi Weather Index) | Development = settlement times 2026-09-13 to before 2026-10-25; held-out = 2026-10-25 to before 2026-11-13, read once on the Head's go | 2026-09-13; 2026-10-25; 2026-11-13 | NOT READ | card text | card only, not registered; overlaps HOURLYTEMP days Nov 5 to 11 (Head to rule) |`

## Fields for the zero-try probe (none read yet)

1. **For each hourly series:** does `rules_primary` or `rules_secondary` name the Kalshi Weather Index, or The Weather Company? Which city key does `/live_data/weather/{city}` use for each? Is S the top of the hour?
2. **`/live_data/weather/{city}`:**
   - how far back `from` and `to` reach (development needs Sep 13 on);
   - `t`, `v`, `status`, `contributors`, and the `stations[]` fields with `detailed=true`;
   - whether points are really 1 minute apart and published 300 seconds late.
3. **`/live_data/weather/{city}/calibrations`:** whether earlier `config_version` values are served, so a past minute can be reproduced with its own offsets.
4. **Hourly market candles:** one-minute candles exist for these series in the development window.

**Requests (estimate, for the job writer):** per city, 42 development days of minute index points (about 60,000 points, the page size to be learned by the probe), plus candles of every strike for the 20 minutes before each hour. Candles are the bulk: about 4 x 20 hours x 42 days x 10 strikes, batched. Exact counts after the probe.
