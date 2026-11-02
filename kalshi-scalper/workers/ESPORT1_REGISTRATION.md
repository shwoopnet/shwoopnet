# ESPORT1 registration (Strategy Research V2, written 2026-11-02 BEFORE any candle was downloaded, any price read or any result computed; research only)

Owner decision relayed by the lead: test new non-L1, non-OICORE families in parallel on existing public data; no further approval needed. Family: Kalshi esports map-winner markets priced PRE-GAME. Nothing here means trade; there is no promote verb.

## Ledger check (stop-if-duplicate)
`grep -i -E "esport|cs2|kxcs2|counter-strike|KXLOL|KXVAL|KXDOTA" README.md` finds one line: SP1's fixed universe (Oct 13, a favourite-held bet on 12 sports game-winner series, `KXVALORANTGAME` among them, for the whole match, no ranking model). No CS2, LoL or Dota entry, no map market, no Elo. Not a duplicate. Disclosure: SP1 (favourites) overlaps only in that one Valorant match series, which is NOT in this universe (map series only).

## What was looked at before this registration (disclosure)
Listings only: the series list, the settled market listings (live and `/historical`) of the map series, saved to a scratch file outside the repo. The listing rows carry `result`; I printed only counts by series and source, event counts, open dates, and checked that the scheduled start in the event ticker equals the start stated in `rules_primary`. No bid, ask, price or candle was read, no result was inspected, no model exists. One candle request (the endpoint check) printed only the number of candles returned and the field names.
Findings that shape the design:
1. **Event ticker = scheduled start.** `KXCS2MAP-26NOV020700WINGDNK-2` is map 2, scheduled start 2026-11-02 07:00 US Eastern (ticker and `rules_primary` agree in 99% of rows; the rest are dropped as reschedules). `close_time` is when a winner is DECLARED (early close), so it depends on the outcome and is never used as a clock for entry; it is used only as the time a map's result became known, for the Elo.
2. **Map 2 and later are in play for the match** (they open after map 1 ends). Only MAP 1 (event suffix `-1`) is a pre-game price. Maps 2+ are excluded (no in-play trades).
3. Each event has two markets (one per team); both are listed with `yes_sub_title` = the team name. Team identity is the name string within a series.
4. Settled map-1 events found, by series: KXCS2MAP 6,087 (2025-11 to 2026-11), KXLOLMAP 2,184, KXVALORANTMAP 1,573, KXDOTA2MAP 1,272, KXR6MAP 203, KXCODMAP 159, KXCSGOMAP 2, KXOWGAME and KXRLMAP no map-1 structure. (Counts of events whose ticker parses; some team codes with a dot do not parse in my first pattern and the code must parse them.)

## Counterparty and mechanism
Who loses: retail fans who overpay for popular teams and favourites on a thin, new, fan-heavy market. Honest prior that this is priced in: high. Esports is a heavily bet market (bookmakers, HLTV rankings, public Elo sites) and Kalshi makers can copy those prices; an Elo built only from Kalshi's own settled maps knows far less than they do. Prior of a pass 3%.

## Information source (walk-forward Elo, no outside data)
Per series, an Elo table over team names built ONLY from that series' settled maps (every map, any map number) whose `close_time` (the moment the winner was declared) is at or before the entry time T. Start 1500, K = 24, scale 400, update in order of `close_time` with the two teams of an event updated together (an event's two markets are one result). Both teams need at least 5 earlier maps in that series (else the event is burn-in and is not traded). Fair P(team X wins map 1) = 1 / (1 + 10^((Elo_other - Elo_X)/400)). No parameter is tuned (K, scale, 5 are fixed now); no home advantage, no map-1 effect.

## Universe (cost, liquidity and metadata only)
- **Try A:** KXCS2MAP.
- **Try B:** KXLOLMAP, KXDOTA2MAP and KXVALORANTMAP pooled (each with its own Elo), the other series with at least 1,000 map-1 events by the listing. KXR6MAP (203), KXCODMAP (159), KXCSGOMAP, KXOWGAME and KXRLMAP are not tried (too few events to reach 150 trades; not a try).
- Map 1 events only (suffix `-1`), ticker start parsed in America/New_York, and equal to the rules_primary start; one market per event, the one whose `yes_sub_title` sorts first alphabetically (metadata only), so one trade at most per event (the NO side of that market is the other team).
- Elo fair between 0.10 and 0.90. A valid two-sided quote (0 < bid < ask < 1) at entry with spread at most 10c, else no trade.

## Entry rule and time
Entry time T = scheduled start minus 10 minutes. The entry price is the first 1 minute candle whose end is at or after T and at or before the scheduled start that has a valid two-sided `yes_bid.close` and `yes_ask.close` (historical `close`, live `close_dollars`; the shared `candlefield` parser reads both). A quote is not a fill; stated. No candle in that interval: no trade. Elo uses only maps with `close_time` <= T.
Buy YES at the ask if fair - ask - 0.07 x ask x (1 - ask) >= 0.08; buy NO at 1 - bid if bid - fair - 0.07 x bid x (1 - bid) >= 0.08. One order of C = 10 contracts, taker, held to settlement. Fee 7% x C x p x (1-p) rounded UP to the cent per order; stress line at fees x1.2. Information only, not tried: gaps of 0.05 and 0.12.

## Windows
Eligible events (past Elo burn-in, a quote at entry, spread <= 10c, fair in 0.10 to 0.90) sorted by scheduled start and cut into three EQUAL thirds by event count: W1 earliest, W2 middle, W3 latest. **W3 is the frozen holdout: it is not scored unless W1 and W2 both pass**, and the rule above is frozen by this file before W1 is scored.

## Numeric prediction (written before scoring)
The registered claim under test (from the brief): the walk-forward Elo beats the market price in Brier on pre-game quotes, and buying the side the model says is under-priced by at least 8 cents after the fee earns profit factor >= 1.5 in each of three windows with n >= 150 trades. **My expectation is the opposite:** market mid Brier better than the Elo's in both tries; profit factor 0.4 to 1.1 in each window; pooled mean -8c to +1c; 300 to 2,500 trades (an Elo with 5 maps of history is noisy, so the 8c gap fires often, and mostly on its own errors).

## Kill criteria
- `FALSIFIED`: profit factor under 1.5 after fees in ANY of the three windows (W3 read only if W1 and W2 pass), or the Elo's Brier no better than the market mid's (same events, same entry quote), or not positive at fees x1.2, or pooled event-clustered z under the deflated bar 5.27 (running N about 728,708), or pooled mean under +2.0c.
- `NOT_ENOUGH_DATA`: fewer than 150 settled trades pooled over the windows (the PFs are reported anyway).
- `NOT_YET_FALSIFIED`: all of the above pass. It would permit only a forward quote re-read, never a trade.
- `NOT_RUNNABLE`: candles unreachable. Windows, thresholds, K, look and universe are not changed after the result; no variant is run.

## Overlap with L1
None. L1 buys 15 minute crypto, gold and similar markets 6 or 10 minutes before the close. These are esports map markets bought about 10 minutes before the match starts and held to the map's end: a different underlying, series, horizon and information source; they cannot share a position or a window. Nothing here touches `functions/`, live code, L1 or OICORE.

## Tries
Two (A: KXCS2MAP; B: the pooled LoL, Dota 2, Valorant map series). Map 2+ markets, other series and gap thresholds other than 0.08 are not tried. N + 2: running count about 728,708 (z bar about 5.27). Every result is quoted with window, n, cost and N.

## Forward read (not built)
Candles of settled markets stay retrievable, so no recorder is needed for a forward read. The date depends on the pace of qualifying trades and is stated in the result.
