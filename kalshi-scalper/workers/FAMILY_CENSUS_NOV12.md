# Untouched-family census (Idea Desk B with the Forensics desk; started Nov 12, 2026)

**Status: plan and listing job only. The table is not written yet.** First cut due 21:00Z on Nov 12 (at risk: the two workers reading the held files were stopped by the account's usage limit at 16:30Z and resume at 18:20Z); full table due 16:00Z on Nov 13. Asked for by the owner through the Head of R&D: "find more", breadth and not depth.

## What the census is

One row per Kalshi FAMILY (a category plus a group of series that work the same way): category, how fast it settles, independent events a year, recent volume and typical spread, fee class, what kind of data it gives (order book, tape, candles, or only a list quote), and TOUCHED or UNTOUCHED. Touched means a registered test exists; it is named with its verdict. Untouched means no registered test of any kind.

**Split with Forensics (agreed Nov 12):** this desk writes the family list, touched or untouched, events a year, fee class and the listing job. Forensics fills volume, settlement speed, spread, depth and data kind for every family we already RECORD, from recorded files only. For a family with no recorder, volume comes from the listing below.

## The fresh listing job

`workers/desk_b_jobs/CENSUS_LISTING.json`, 40 requests, at most 88 pages, about 120 MB (estimated at 1.7 KB a market), one run. It passes the pull script's own check. A listing only: no candle, no test, nothing scored.

| Part | Requests | What it gives |
|---|---|---|
| The whole series list (`/series`, limit 20000) | 1 | every series: ticker, title, category, frequency, fee type and multiplier, settlement source |
| Every non-combo market that settled on Nov 10, 2026 UTC, hour by hour (`/markets`, settled, close-time bounds, combos left out), at most 3 pages of 1,000 an hour | 24 (at most 72 pages) | per family: markets and events settled in a day, final volume, open interest, last price |
| The series list again by single-word category | 15 | a fallback if the whole list is cut at the 5 MB answer cap |

Where the calls come from: the first two are exactly the calls V2's sweep made (`src/scalper/usweep2.py` on `claude/epic-ptolemy-0amjd9`: 330,612 markets crawled in 72 hourly windows, 1,481 series seen). The category parameter on the series list is the one call not seen in that code, so it is placed last, where a refusal cannot stop anything before it.

**Limits, said now.**

1. One day is one day: Nov 10 is a Tuesday. A family that settles weekly or monthly, or only at weekends (NFL Sundays), shows in the series list but not in the settled crawl. Events a year for those come from the series' stated frequency, marked as such.
2. V2 saw about 4,600 settled non-combo markets an hour. At 3 pages an hour, a busy hour is cut at 3,000; the reader flags every cut hour and reports its counts as a lower bound. A full day would not fit under the 200 MB a run cap.
3. Volume in a settled market object is that market's own total; a family's volume is the sum over one day, not a yearly figure.
4. Open markets are not listed by this job (the size cap again). Typical spread therefore comes from Forensics for recorded families and is "not known" for the rest until a second job is asked for.
5. Combos are left out on purpose; the combo recorder covers them.

## What V2's old sweep already says about untouched ground

The universe sweeps (USWEEP1 to 3, Nov 3) stopped at the rate limit: 13,856 in-scope series were never tested by the first, about 14,000 were not reached by the second and about 10,000 custom or one-off series by the third. Their rule was a cheap-tail calibration grid, a crowd-bias rule, and found nothing on what it did read. So a large part of Kalshi has had no registered test of any kind, and the one rule that brushed its edge was of the kind that cannot reach the bar. That is the ground this census maps.

## The reader

To be written before the pull lands: it will count, per series and per family, the markets and events settled on the day, sum the volume, and join the series list's category, frequency and fee fields. It prints counts and sums only.
