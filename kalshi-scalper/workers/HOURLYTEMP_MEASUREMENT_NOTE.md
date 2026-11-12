# Hourly city temperature: a cost and timing measurement note (Idea Desk B, Nov 12, 2026)

**A note, not a card.** Asked for by the Head of R&D (ruling of Nov 12, 17:15Z): a rule driven by a forecast is inside the closed weather family; a rule driven by the latest observed reading is the WXDAYEND mechanism on another venue and waits for WXDAYEND's count and a ruling under the declined list, because a reading-against-bracket rule mostly buys the near-certain side, the favourite-and-hold shape the owner banned. What is allowed now is one zero-try cost and timing measurement, because this is the largest event count anywhere outside the 15 minute series. **Nothing here is a rule, a try or a request to trade.**

## What the family is (from the Nov 10 listing's market objects: titles, rules text and time fields only)

- Four series: `KXTEMPNYCHS` (New York City), `KXTEMPMIAH` (Miami), `KXTEMPLAXHS` (Coastal Los Angeles), `KXTEMPCHIHS` (Chicago Metro Area).
- One event per clock hour, 21 to 22 events a day a city in the listing: about 32,000 events a year across the four.
- About 10 markets an event, each "will the temperature be above X.99 degrees at that hour", strikes one degree apart.
- **Each market lives one hour:** it opens 60 minutes before the hour and closes on the hour. So "60 minutes before" is the open; the looks below are 55, 30 and 10 minutes before the hour.
- **It does not settle on the National Weather Service.** The rules text names Synoptic Data, "calculated in accordance with the Kalshi Weather Index Methodology", and says other sources "may serve as references, but are not authoritative". Synoptic's terms have NOT been read and no read of Synoptic is proposed. A weather service reading is therefore a proxy for the settling value, not the value.
- Settles a median 71 minutes after the close (listing). About 800 contracts a market that day (a lower bound). No recorder holds it; spread and depth are unknown.

## The measurement (zero tries, no result read)

**Sample, fixed now:** the seven most recent full UTC days before the pull, all four cities. Seven days because the weather service's public station history goes back about a week; it is never extended.

**From Kalshi (through kalshi-pull):** the settled lists of the four series for those days (for tickers, strikes and times; the result field is not read), then one-minute candles of every strike for the 60 minutes each market lived.

**From the weather service (a permitted source, read by this desk, not through kalshi-pull):** the station observations of the same seven days for one airport station a city (New York Central Park, Miami International, Los Angeles International, Chicago O'Hare). The index may blend stations; that is why this is a proxy.

**Reported, at 55, 30 and 10 minutes before the hour, per city:**

1. Strikes with a two-sided quote, as a share; median spread; round trip (spread plus two fees).
2. For each strike, the distance between it and the last weather service reading published before that look, in degrees. By distance band (under 1, 1 to 2, 2 to 3, over 3 degrees, above and below): the median YES mid and the median ask of the nearer-certain side.
3. How many minutes old that last reading was at the look.
4. Minutes with no trade, as a share (from candle volume).

That answers three things without a result: what it costs to trade here, whether there is anything two-sided near the money at all, and how tightly the market already hugs the latest reading. If strikes 2 degrees from the reading already sit at 95c or more by the 30 minute look, the only thing left to buy is the near-certain side, and the family is closed for this desk on the owner's favourite-and-hold ban without waiting for WXDAYEND.

**What it cannot say:** whether any rule makes money (no result is read); how the proxy differs from the settling value (Synoptic is not read); depth (a candle has no size).

## Requests

| Part | Requests |
|---|---|
| Kalshi, settled lists: 4 series, about 1,540 markets each over 7 days | 4 requests, about 8 pages |
| Kalshi, candles: 4 cities x about 10 strikes x 60 minutes, two clock hours a request (80 tickers, 9,600 candles), 7 days | about 80 |
| Weather service, station history: 4 stations, a week | about 8 (not Kalshi requests) |
| **Kalshi total** | **about 85, one run** |
| Tries | 0 |

Order: after TIE3 and SOCDERIV, and only if the Head wants it run; the job file and reader would go to the Testing Desk in the same way.
