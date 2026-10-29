# RISK1 registration: day-block bootstrap of the bot's account under the current live rules

Worker RISK1, Strategy Research V2, 2026-10-29. Research only. Written and pushed **before** any simulation was run or any per-window outcome was tallied. Purpose: a risk estimate for the owner's deposit decision ($528 now, or $1,028 after a $500 deposit). **This is not a strategy test: there is no pass bar and no verdict word applies to an edge.** Count: 1 try (running N + 1). Nothing here changes a live rule.

## Ledger check

GROWTH, GROWTH2, GROW1, SIZE_S2 and the gold sizing bootstrap (README lines about 3038, 3545, 5881, 6128, 6911) are earlier day-block bootstraps, all under older or simplified rules (no smooth gate, no quiet hours, Bitcoin and XRP live, flat sizes, no pool or add-on cap, no 25c exit). None models the rules on main at 2026-10-29. RISK1 is a re-estimate under today's code, not a reworded test.

## Live rules modelled (read from `origin/main`, `functions/kalshiLiveLib.js` and `CLAUDE.md`, 2026-10-29)

- **Markets that can trade:** `L1_SERIES` minus `PAUSED_SERIES` (XRP, Bitcoin, AUD/USD, USD/CAD, natural gas are paused) = **gold (`KXGOLD15M`), Dogecoin (`KXDOGE15M`), Ethereum (`KXETH15M`)**, tried in that order within a window. No 10 minute series is left (XRP and natural gas, the `EARLY_PROBE_SERIES`, are paused), so every look is the **6 minute look**: the 1 minute candle ending exactly 360 s before the close (the live window is 330 to 400 s left; the history study convention is 360 s).
- **Band:** `l1Pick`: YES if the candle's closing YES ask is in 0.88 to 0.97, else NO if 1 minus the closing YES bid is in 0.88 to 0.97, else nothing (`lstrats.favorite`).
- **Gold quiet hours:** no gold order when the US Central clock at the look reads 20:00 to 23:59 (`QUIET_HOURS_CT`).
- **Ethereum smooth gate** (`pathShape`, `smoothGate`): the bought side's mid ((bid + ask)/2, or 1 minus it for NO) for every 1 minute candle of that market up to and including the decision candle; at least 4 earlier candles, every minute change >= -0.005 (plain float arithmetic, so exactly -0.005 fails as in live) and last minus first >= 0.10. Otherwise no Ethereum order.
- **One crypto order per window:** Dogecoin and Ethereum are both `CAPPED_SERIES`; the first that orders (Dogecoin, by list order) holds the window. Gold is not part of the rule. Every order is assumed filled, so a Dogecoin order always holds the window.
- **Sizes:** Dogecoin `FIXED_CONTRACTS` 5, Ethereum 1, no add-on for either. Gold, the only ladder market: `l1Count(cash, cost1, cap, addon)`: base = max(1, min(cap, 50, floor(cash x 0.02 / cost1))); count = min(base + min(addon, floor(base x 0.25)), 50), with addon = min(floor(pool / 0.93), floor(cap x 0.25)) (`skimAddon`, `addonCap`); cost1 = worst + fee(worst, 1), worst = the band price rounded up to the cent (the limit). Order size lock (`maxContractsFor`): gold 50, Dogecoin 5, Ethereum 1.
- **Ladder** (`reviewSizing` on cash minus savings, every window): target = max(1, min(40, floor((cash - saved)/43))). Start: the owner restarts after the deposit, so the first state is a **reseed**: cap = target, base = cash. Up: at most +1 per 3 days (when 3 days have passed since the last review, base = cash - saved and the cap steps toward the target). Down: when the target stays below the cap for 2 hours, cap = target and base = cash - saved.
- **Pool and savings** (`foldSkim` with everyWin, in settlement order): cum += pnl; on a new high of cum, savings += 0.5 x the rise; a win adds 0.5 x pnl to the pool; a loss takes pnl from the pool (never below 0). A loss stop empties the pool.
- **Window cap:** account money (cost minus the add-on's share) put into one window is held to 5.5% of the base: allowed = max(1 if the window is empty else 0, floor((0.055 x base - used)/cost1)); a count above allowed + add-on is cut to it, or the order is skipped if that is under 1.
- **Cash:** an order needs cash left (after this window's earlier orders) of at least its cost + $0.50. Kalshi's shards are not modelled (all money is assumed to sit where it is needed).
- **Loss stop:** worst = (settled net of orders sent since max(session start, now - 24 h)) - (cost of open orders, counted as lost); it fires when worst <= -(0.12 x base + allowance), allowance = add-on cost of orders lost at settlement (and the add-on share of an exit loss) in the same span. Checked before each window's orders (all earlier windows have settled by then) and again one minute after them (with this window's orders open and counted as lost). After a stop the open orders run to their end as usual; no new order. Two variants, both reported: **STOP_DAY**: off for the rest of that path's US Central day, restarted (reseed, a new session, so earlier orders no longer count) at the first window of the next day; **STOP_END**: off for the rest of the path. Also **NO_STOP** (the same rules with the stop removed), only to price the stop: cost of the stop = mean net with the stop minus mean net without it.
- **Exit watch:** sell all contracts at the first 1 minute candle after the decision candle and ending at least 60 s before the close whose bought-side bid (YES bid, or 1 minus the YES ask for NO) is <= 0.25, at that bid, with the fee at C contracts. Otherwise hold to settlement (Kalshi's recorded result).
- **Fills:** the decision candle's band price plus the live slippage per market from `workers/DRIFT.md` (30 day mean): gold +0.60c, Ethereum +0.87c, Dogecoin +0.86c. Every order fills in full at that price. Fee 7% x C x p x (1 - p) rounded up to the cent per order, on the price paid. The loss stop and window cap use the simulated cost actually paid.
- **Not modelled (all fail toward no change or are irrelevant at these sizes):** the 200 orders a day limit (at most 192 possible), the $2 per contract `LIVE_CAP`, partial or missed fills, market impact (a 13 to 28 contract gold order is assumed to fill at the touch plus slippage), the probe drop rule (probes are paused), hand trades, Flatten.

## Data

Kalshi public 1 minute candles (closing bid and ask, volume) and recorded results for `KXGOLD15M`, `KXDOGE15M`, `KXETH15M` from `data/` (sources in `hs1.SOURCES` order, then `fresh.sqlite`; first source holding a ticker wins, as in `hs1.load`). Days: every **full US Central day** in the files (expected 2026-08-06 to 2026-10-28, about 84 days; gold has no Saturday markets and a short Sunday, which whole-day resampling keeps). The task text says 69 days; the files now hold more, and all full days are used.

## Step 1: per-window outcome records (1 contract)

For each US Central day, each of its 15 minute windows (by close time), each of the three markets: in band or not, side, band price, limit, smooth gate pass (Ethereum), quiet hour (gold), outcome: settled won or lost, or exited at bid b; zero-volume flag on the decision candle. Reported before the bootstrap: per market entries, loss rate, exits, mean net per contract after fees and slippage, profit factor, by history third.

## Step 2: bootstrap

Resample **whole US Central days** with replacement (uniform), 10,000 paths per configuration, each path 90 days; the 30 and 60 day figures are the first 30 and 60 days of the same paths (each a 30 or 60 day path in its own right). Windows of a day are kept together and in their order. Seed fixed (20261029). Starts $528 and $1,028.

Pools of days: **ALL** (every full day); **T1, T2, T3** (the days split into thirds by date; each third resampled alone). T3, the last third, is what the owner asked for as the weakest-period check; all three are reported so the reader can see which is weakest.

## Outputs (for each start, horizon, day pool and stop variant)

Net at the horizon (final balance including savings minus start): 5th, 25th, 50th, 75th, 95th percentile and mean; probability the 12% stop fires at least once; worst drawdown (peak-to-trough of the balance, in dollars and % of the peak): median and 95th percentile; share of paths ending below the start; expected cost of the stop = mean(STOP_x) - mean(NO_STOP). Also mean number of stops per path and mean gold count at the end.

Information only: the same with zero-volume decision candles treated as no fill.

## Numeric prediction (written before any run)

At $528, ALL days, STOP_DAY, 30 days: median net +$60 (range of my guess +$20 to +$120), 5th percentile below +$0, stop at least once in about 10% of paths, share below start about 10% to 20%; the T3-only pool lower than ALL. The cost of the stop small (a few dollars) and possibly positive.

## Kill criteria

None for a strategy (no strategy is being admitted). The run is void and rerun once (logged) only for a code bug found by its own checks (the Step 1 per-contract tallies must match a direct computation from the same records).

Code: `src/scalper/risk1.py`. Result: `workers/RISK1_RESULT.md`.
