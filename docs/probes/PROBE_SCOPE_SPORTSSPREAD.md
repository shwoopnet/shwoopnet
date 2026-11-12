# Probe scoping: the sports SPREAD cheap cell (design only, Nov 12, 2026)

**Status: scoping only. No code exists and none is to be written in `functions/` unless the Chief of Staff asks. Nothing is live, approved or deployed. It matters only if the research read comes back PASS, which research puts at 3% to 5%.** UNPROVEN: an information purchase, not an edge. Any order needs the owner's own popup with the exact spec.

## 1. The rule being scoped (Refinement's W-SPREAD-CELL1, frozen there, not here)

One of six sports spread series (`KXMLBSPREAD`, `KXNBASPREAD`, `KXNCAAFSPREAD`, `KXNCAAMBSPREAD`, `KXNFLSPREAD`, `KXNHLSPREAD`). One observation per game: about 48 hours before the close, among the game's markets whose YES ask is 5c up to (not including) 15c, the one whose YES mid is nearest 0.5. Buy YES at the ask, 1 contract, hold to settlement. Worst loss about $0.17 an order with the fee.

Classification card: `SPREADCELL | calibration cell, immediate entry on a cheap YES + hold to settlement | low win rate, many losses of 5c to 15c, about $0.17 an order, sports group (no live strategy trades it) | stage Idea`. Not a favourite, not a short round trip, not on the declined list (7e, checked Nov 12). `docs/POLITICS_RULES.md` section 6 allows sports singles as "calibration only, on Kalshi's own settled markets", which is what this is; a LIVE sports single is not covered by any budget in that file, so the popup must name one.

## 2. One thing to settle before the read is trusted: which "close"

The research look is "the last hourly candle at or before close minus 48 hours", and the close times in the committed event list (`SPREAD_CELL1_EVENTS.json` on `claude/refine-live`) are not round times: they look like the moment each market actually closed after its game. That moment is not known 48 hours ahead. It is a timing shift (a game's length varies by an hour or so, so the look can land one hourly candle away), not a leak of the result. But a live rule, and the forward shadow, must use something knowable at the look: the game's scheduled start, which is in the event ticker (date and Eastern start time), plus a fixed offset. **Refinement should state which close its scorer used and fix the live definition (for example "45 to 46 hours before the scheduled start") before a PASS is acted on.** If the edge only exists at the realised-close look, it is not tradable as written.

## 3. Route A: the owner places it by hand

- **Days:** 1 day after a PASS and a popup. With the read landing within a day of the kalshi-pull merge, about Nov 16 to 18 if the owner says yes tonight.
- **What it needs:** research names the exact market and the top price (15c); the owner buys 1 contract in the Kalshi app; money on the exchange shard that sports markets use (not known; the app shows it).
- **What the bot does about it:** nothing. The fill shows on the Bot page as unmatched account activity, it is not in the nightly report or any stop, and it changes the balance the size ladder reads by cents. It needs a manual log line (market, side, price, time, result) kept in a message or the owner's private page, never in this repo.
- **What it cannot do:** repeat. One hand order is one data point; the proven bar is 100 fills.

## 4. Route B: bot code. What is missing today, exactly

Every line was checked against the code on `origin/main` on Nov 12.

| # | Gap | Where | What a build must do |
|---|---|---|---|
| 1 | The slot accepts only 15 minute tickers | `SLOT_TICKER_RE`, `SLOT_SERIES_ALLOWED` in `functions/kalshiSlotLib.js` | Add the six series and a ticker pattern written from REAL market tickers (the market ticker's last part is not in any file this desk holds; do not guess it). Reserve the series to this probe (`SLOT_SERIES_RESERVED`) |
| 2 | The entry window is fixed at 120 to 840 seconds before the close | `SLOT_ENTRY_LEFT_MIN_SEC`, `SLOT_ENTRY_LEFT_MAX_SEC`, the validator, the `jobs` loop in `kalshiSlotRunLib.js` | A second entry mode for a long look: a window in hours before the SCHEDULED start (section 2), with its own validator bounds. The 15 minute mode stays exactly as it is |
| 3 | No quotes for these series reach the engine | `functions/index.js` reads only the L1 series (and a calendar strategy's series when due) | A due-check like `slotCalendarSeriesDue`: read the six series' open markets only in the minutes a game enters its look window (about one paged public read per series, a few times an hour at most). The games and markets per series must be counted first; a busy college Saturday could be hundreds of markets |
| 4 | Choosing the market | nothing | New pure function: among one event's markets with a YES ask of 5c up to 15c, the one with the mid nearest 0.5; one order per EVENT, ever (a fixed client order id per event, not per market) |
| 5 | **An open order older than 24 hours drops out of the shared 12% stop** | `slotRiskForBotRisk` filters orders by time (`inRange`), and `botRisk` passes the last 24 hours | An order still OPEN must count as lost whatever its age; only settled results are windowed. This touches the shared stop, so it is the part that needs the closest review, and it must not change any figure for OICORE or EVENT830 (their orders settle within minutes) |
| 6 | Nothing watches a held order after 25 minutes | `EXIT_LOOKBACK_MS` in `kalshiSlotRunLib.js` | Acceptable for a hold-to-settle order (there is nothing to sell). Stated, not fixed: the hedge sale also stops looking, so the series must be reserved (gap 1) so no other strategy can ever take the other side |
| 7 | The settle sweep reads every open order's market every minute | `runSlotSettle` (no age limit, 12 orders a minute) | Works as it is. For a two day hold it is about 2,900 public reads per order; throttle to every 10th minute for orders more than an hour from their scheduled start |
| 8 | Hold to settlement needs the reviewed list | `SLOT_HOLD_ALLOWED` | Add the id (or use the probe-candidate list on this branch, which carries its own hold permission, switch, 1 contract cap and sticky budget) |
| 9 | Exchange shard | `availableFor` reads the market's own `exchange_index` | Nothing to build; the shard must hold money or the engine logs `shard_short` and sends nothing. The low-money phone alert does not cover slot orders |
| 10 | The page | `KALSHI_EXTRA_SERIES` (gate Y31 wants every slot market on the relay), `kalshiCloseFromTicker` (reads a 15 minute ticker's Eastern time), market names, push alert names | Exempt long-hold probe markets from the relay rule on purpose, show "closes after the game" instead of a parsed time, add names. Display only |
| 11 | Kill rules and budget | the validator; the probe-candidate budget on this branch | Budget $5 (about 30 losing orders), 20 losses in a row is NORMAL at a 10% win rate, so the streak rule is set at the validator's top and the budget is the real brake |
| 12 | A release date | none | Sports seasons end; a stop date in code |

**Build size:** about 4 to 5 build days with tests, 1 to 2 for the security review, then merge and two deploys (`deploy-push.sh`, then `deploy-sizing.sh`). **Days to first order by bot code: 6 to 8 working days after a PASS** (about Nov 24 to 28), or 1 to 2 days after a PASS if it is pre-built off by default, which is a decision for the owner and the Chief of Staff since it spends a week of build on a 3% to 5% chance.

## 5. Caps, kill, return (what a spec would say)

- **Size:** 1 contract, YES only, top price 14c, one order per game. **Budget:** $5 lifetime on its own orders, sticky. **Open at once:** at most 10 (about $1.70), inside the slot's open cap.
- **Kill:** the budget; net below $0 at any point from 100 settled fills; by reviewed edit if the forward shadow reads under 1.0 at 100 shadow fills. **Return:** a 14 day cool-off, a shadow run at cash profit factor 1.3 or better over 100 signals, the owner's approval.
- **Honest limit:** $5 is about 30 tries at a 10% win rate, which is three wins expected. It shows that orders fill at the quoted ask two days out, and at what size the book is real. It cannot show an edge.

## 6. The same path serves a politics single and a $2 parlay

The Head of R&D asked what would place one. The smallest shared build is a "named market, one shot" entry: the registry names the exact ticker, the side, the top price, the count and a date window, and sends one immediate-or-cancel buy, once. It needs gaps 1, 5, 7, 8, 9 and 10 above, not 2 to 4, plus a budget counter replayed from the orders ($200 for politics and parlays, `docs/POLITICS_RULES.md`). About 3 to 4 build days. A $2 parlay adds fractional counts (dollars over price), the combo exchange shard and the $40 parlay stop; whether a combo takes an ordinary order against a posted bid or needs the request-for-quote flow (a 3 second confirm window, which a one minute function cannot serve) is not known. By hand is the only route that works on the day of an approval.

## 7. What to do now (recommendation)

Nothing is built for this before the read. If the read is PASS: one hand-placed order by the owner, then decide on the build with the forward shadow running. If it is LEAD, FAIL or underpowered: nothing.
