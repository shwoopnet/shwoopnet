# KXINX15M: the search for up to three genuinely different cards (Desk A, Nov 13, 2026; nothing read, nothing registered)
Brief (the Head, 16:58Z): each card needs a NEW field or source that is not an outside fair value, not cheap-side price or time (row 190), and not favourite-late; checked against the declined list and the falsified families first. **Result: NONE passes.** Every candidate I can think of is one of the families below, and I list each with the reason, so the rejection can be audited. I have not read any KXINX15M data, any result file of the cards named (I use the Head's and the declined list's descriptions), or any outside source.

## What fields exist, and the family that already owns each
| Field or source | Family that owns it | Status |
|---|---|---|
| An outside price turned into a probability (ES or MES futures, SPY, VIX or option-implied vol, 0DTE options, any index feed) | quote against an outside fair value, held | DECLINED for good (GOLDFV1, INX1, H7, CMD1; this includes a futures momentum or reversal signal, which is the same fair value in another form) |
| Kalshi price level or time of day, any band, any look (cheap side, favourite, middle, session-open, last window) | cheap-side price, regime and grammar rules without a new data source (row 190); favourite-late | CLOSED by evidence (GEN12, GEN13, REGIME1, SWEEP1, NONCRYPTO1, LEADLAG1, ANGLES1) / banned without an owner exception |
| Taker flow, trade tape, sweep and refill, trade size type | taker order-flow signals; RETAILFRAC1 | CLOSED (FLOW1, TAPEFLOW1, RESIL1; RETAILFRAC1 stage A) |
| Five level book imbalance and depth | DEPTH1 and NC15DEPTH1 (a version on a new market under 7g, never new) | in test, not unique |
| Open interest | OICORE (SPXOI1 is its version) | live probe |
| A scheduled event calendar (FOMC 2:00 PM ET, 10:00 AM ET releases) | EVENT830 (a version on a new market under 7g, never new) | live probe below the bar |
| Other Kalshi markets on the same or a correlated underlying (the hourly and daily index ladders, KXNDQ15M) | lock and parity scans; LEADLAG1 | CLOSED by evidence |
| Resting quotes on both sides for the spread (the quadratic fee schedule changes nothing about the family) | two-sided market making | CLOSED by evidence (H5, MAKER1, MAKER4, MMSIM1 corrected, QUOTE2B) |
| Exact ties (YES wins at or above the strike) | conditional tie premium | CLOSED by census (TIECOND1) |

## Candidates I considered, with the reason each fails
1. **Always buy YES at or under 50c (the equity drift and the "at or above" tie).** The unconditional base rate of an index rising over 15 minutes is a few tenths of a point above 50%. The fee at 50c is 0.07 x 0.5 x 0.5 = 1.75c, so a win-rate edge of at least 3.5 points is needed to break even; the drift supplies a small fraction of that. It also has no field at all (a constant rule): arithmetic kills it, no read needed, not a card.
2. **Momentum or reversal of the index's own prior window return.** Needs an outside index price: that is the fair-value family (above), however it is phrased.
3. **Open-window drift from the strike.** With Kalshi prices only, it is row 190; with futures, it is the fair-value family. (Already rejected in the addendum.)
4. **Settlement-second rule.** Needs a second-level source and a sub-second order; not implementable by our polling (addendum).
5. **Event-window longshot (FOMC, 10:00 AM ET releases).** It is EVENT830's logic on this market: under 7g a VERSION of EVENT830, which takes no slot and counts its tries; it can take a wheel seat under 0.6 if the owner wants every plausible shadow rule on this market, but it is not a different mechanism. I do NOT write it as a card in this answer; if the Head wants it seated as a version, say so and I write its spec line.
6. **Market making on KXINX15M.** Declined family (a new market is a version of a declined idea, not a new one).
7. **Cross-market lead and lag with the daily or hourly index ladder, or Nasdaq 15 minute.** Declined (lock and parity, LEADLAG1).
8. **Volume or open-interest levels as a regime filter on any of the above.** A filter on a declined family or a version under 7g; and regime sweeps without a new source are row 190.
9. **Closing-imbalance publications (SPXCLOSE1).** The only field that is genuinely new and not a Kalshi price or an outside fair value; it fails gate 0 (terms of the exchanges' publications unread) and was never registered. It would be an outside-flow signal, not a fair value; if the owner or the Head clears the terms and a source, it is the one card I would write. It is listed here as the single open lead, not a card.

## Plain statement
I find **no genuinely different KXINX15M card today**. The one open lead (closing-imbalance publications, last window only) needs a terms read and a source before it can be called a card. If the Head can name a new field the project is allowed to read (a published, terms-cleared index-level or flow dataset that is neither a price-derived fair value nor Kalshi's own price, time, flow or open interest), I will write it the same day. Until then I would rather list nothing than pad.

## Dated line (Nov 13, 2026, the Head's ruling at 17:01Z): SPXCLOSE1 CLOSED as a source
Main read the terms: Nasdaq's NOII is subscription only, NYSE's imbalance data is paid, and storage or commercial use needs written consent, so there is no free route to the closing-imbalance publications. Candidate 9 (SPXCLOSE1) is **CLOSED as a source** for that reason; it is no longer an open lead. Reopening it would need a paid vendor quote and the owner's popup. No card exists or is owed for it.
