# Kalshi-native fields and uncovered families: answer, Desk B, Nov 13, 2026, written 19:22Z by this desk's clock. NO DATA READ.

**Answer: no card passes. Nothing is written as a registration.** Below, per lane, why, and two time-only counting questions the Head may order if wanted (not cards).

## Lane 1: settlement rule and resolution source quirks
- Rule text edge cases: already a lane of their own (RULESREAD lists, and the politics rule that an edge case is flagged for the owner and never automatic). A card here would be a reading task, not a mechanism with a named counterparty.
- A source that rounds, averages or revises (the 60 second average of CFRTI, a gold fixing, the NY Fed table): the Kalshi price lagging that reference is the declined "quote lags an outside reference" family (GOLDFV1, INX1, H7, CMD1, and today's SPOTFLOW1 ruling). Settlement-source timing with no outside price (a result posted late) cannot be traded, because the market is closed.
- A futures roll inside a 15 minute commodity window (the settlement source switching contract) would need the futures curve, an outside source I have no permitted feed for.

## Lane 2: listing, close-time change, creation timing
- **Late-added strikes** (a strike created after its event opened) do exist: my hourly temperature work found markets whose life is not 60 minutes. I have no mechanism with a named loser: a new strike's first quote is either near its neighbours (nothing to take) or wide (nothing to trade), and a ladder consistency rule is the closed LADDERARB1 and XLADDER1 family.
- **Close-time or expiry changes** (a deadline extended, a market closed early): visible in the politics recorder's close time column, but the directional claim (an extended "by date" market's YES should rise) has no counterparty beyond a stale quote, and the count of such events is unknown and probably a handful, so a card could never reach 150.
- **Determined-but-not-closed markets** (outcome certain, ask still stale): needs an outside observation of the outcome (a weather station, a live score), which is NOWCAST1 for weather and the live data sources that wait on the owner's exception.

## Lane 3: event families in the census that no card covers
Families marked NEVER READ in `FAMILY_TABLE.md` (NHL periods, college football, minor hockey, ITF tennis sets, darts, chess, bowling, volleyball, overseas basketball, NBA quarters, soccer extras): every mechanism I can state for them is either a favourite-late or cheap-tail rule on a price (the USWEEP sweeps' and the declined families' ground), or needs a score or a live feed from a barred source. NHL third period is ENDNET, NHL overtime markets are a SOCDERIV version, and tennis and esports in-play are SC1, MAPBREAK, DBLTB. None passes the check that the SIGNAL is a different data source.

## Two time-only counts, if the Head wants a zero-try answer first (not cards)
1. Late-added strikes: count markets whose open time is later than their event's first open, by series, from the landed lists runs (times only; no price, no result).
2. Close-time drift: count tickers whose close time differs between two polls in `pol-data` (the politics recorder; times only).
Both would only tell whether the event is frequent enough to ever support a card.

## The two time-only counts, run 19:23Z (the Head ordered them at 19:22Z); `time_counts.py` reads tickers, event tickers, open and close times only (no price, size, result or volume), a hash of it is in the commit message
1. **Late-added strikes**, landed run `HOURLYTEMP_LISTS/2026-11-13T0756Z_43389350994` (four hourly city temperature series, seven days, Nov 5 to Nov 11, no held-out listed for this run): 6,720 settled markets in 658 events; **140 markets in 43 events opened more than 60 s after their event's first open** (Chicago 48 in 15 events, Los Angeles 68 in 20, Miami 15 in 5, New York 9 in 3). That is about 600 markets and about 185 events a month, on these four series only. So the event is frequent, and 30 events would come in about five days. Frequency was never the obstacle; the missing mechanism and the closed weather family are.
2. **Close-time drift**, `pol-data` (35 quote files, 277 tickers, server dates Nov 11 19:32 GMT to Nov 13 19:04 GMT, about two days): **0 tickers changed their close time between polls**. Two days is short, but with 277 tickers observed and none moved, the 95% upper bound is about 1% of tickers in two days, and the series list is the politics set under a 14 day cap; this will not reach 30 events for a paper screen in any useful time (it would need more than 3,000 ticker-days of a rate this far below the bound). It stays closed.
