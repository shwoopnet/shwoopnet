# SPORTCONS1 registration (2026-10-30, written and pushed before any lock was computed)

Owner approved the family by pop-up: "Sports consistency". Research only, nothing live, no recorder.

## What is NOT being repeated (README citations)

- Favourites held (SP1 FALSIFIED -4.19c; F6 tennis favourites -0.22c): no outcome-based favourite bet here.
- Totals ladder locks across strikes (ARB5: zero locks, 691 games; ARB1 and ARB2 live scans of every open event, zero persistent): the within-ladder relation is not retested.
- Maker quotes on sports (MAKER1, 6 of 6 FALSIFIED): every fill here is a taker fill at the ask; no resting order.
- ESPN win-probability lag (ESPN1, 4 of 4 FALSIFIED): no ESPN data used as a signal.
- In-play scalping and footprint (SC1, FP3): no round trips, every position is a two-leg set held to settlement with a payoff that does not depend on the outcome.
New here: R2, a winner-market complement check (the two team markets of one game) and R3, game total against first-half total (KX10 item 9). R2 is close kin of ARB1 (mutually exclusive events) but ARB1 was a live scan of 3.5 hours; this uses minute history of 1,613 games, including in play. R3 is KX10 item 9.

## Relations (from `workers/SPORTCONS1_INVENTORY.md`)

- R2a: buy YES home and YES away at the asks (NO-tie sports only: MLB, NBA, college football). Lock = 1 - ask_h - ask_a - fee(ask_h) - fee(ask_a).
- R2b: buy NO home and NO away at 1 - bid (all four sports incl. NFL). Lock = bid_h + bid_a - 1 - fee(1-bid_h) - fee(1-bid_a). Payoff at least 1 always.
- R3: buy game YES at the ask of strike K_g and 1H NO at 1 - bid of strike K_h with K_g <= K_h. Lock = bid_h - ask_g - fee(ask_g) - fee(1-bid_h).
Fee = 7% x C x p x (1-p), C = 10, rounded UP to the cent per order, per leg. Not on file, so not run: first-half winner, spread ladders, winner vs spread (NOT_RUNNABLE).

## Counterparty
The quoter on the less-liquid leg who has not updated after the other leg moved (in play, a score changes both team markets at once; a bot that moves one and not the other is the payer). The reason it may not exist: both team markets are made by the same market makers whose job is exactly this sum.

## Numeric prediction
Zero locks of at least 1c after fees in every window for R2a, R2b and R3; best lock between -1.5c and -0.2c per contract. Prior that any relation shows 3 or more games with a lock in discovery and validation: 5%.

## Universe and windows (fixed by time only)
R2: all 1,613 `match` games with both team markets' candles. R3: all NFL and NBA games with a game-total and a 1H-total market, pairs with K_g <= K_h. Window by the game's last candle: HOLDOUT = the latest 12 days of the data on file (read only if discovery and validation both pass), DISCOVERY and VALIDATION = the earlier games split at the median date. Fill rule: both legs must have a candle ending in the SAME minute with minute volume of at least 10 contracts each (so C = 10 is plausible); the price is that candle's closing ask or bid (a quote, not a fill; zero-volume minutes are excluded, which is the stricter way, and count would only grow if included).

## Bar and kill criteria
A lock must exist after fees at 10 contracts: NOT_YET_FALSIFIED requires, in EACH of discovery and validation, at least 3 games with a lock of at least 1c per contract (0.01 x 10 = $0.10 a set) in a same-minute pair, and then the holdout is read once with the same test. A lock between 0 and 1c is reported but does not count. Fees x1.2 check: any lock reported must stay positive when both fees are multiplied by 1.2. Otherwise FALSIFIED (zero is a valid answer). Fewer than 100 games with usable same-minute pairs in a relation: NOT_ENOUGH_DATA for that relation (R3 is expected to land here: 16 games have volume on both legs).
T2 (soft consistency, hold to settlement, PF 1.5 in each window with 100/50/30 trades, deflated z 5.27 for N about 728,670 per the owner's brief): runs ONLY if T1 finds at least 3 games with a lock of at least 1c in discovery and validation, because a lock-free consistent book has no gap to trade. No settled result is read by T1 or the inventory. If T2 does not run it costs no try.

## Tries (N)
T1 = 3 tries (R2a, R2b, R3). T2 = 0 unless triggered (then at most 1 more, total at most 4). Running count before: about 592,082 (README), so 592,085 after T1.
